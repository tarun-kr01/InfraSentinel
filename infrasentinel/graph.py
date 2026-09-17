from __future__ import annotations

import re
from typing import Any, Iterable

import networkx as nx

from .config import weights
from .models import ResourceChange

_REFERENCE = re.compile(r"(?:[A-Za-z_][\w-]*\.)+[A-Za-z_][\w-]*(?:\.[A-Za-z_][\w-]*)?")


def _walk_resources(module: dict[str, Any]) -> Iterable[dict[str, Any]]:
    yield from (r for r in module.get("resources", []) or [] if isinstance(r, dict))
    for child in module.get("child_modules", []) or []:
        if isinstance(child, dict):
            yield from _walk_resources(child)


def _references(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        refs = value.get("references")
        if isinstance(refs, list):
            found.update(str(r) for r in refs)
        for child in value.values():
            found.update(_references(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_references(child))
    elif isinstance(value, str):
        found.update(_REFERENCE.findall(value))
    return found


def build_dependency_graph(
    plan: dict[str, Any], changes: Iterable[ResourceChange] | None = None
) -> nx.DiGraph:
    """Build a dependency -> dependent graph from Terraform configuration JSON."""
    graph = nx.DiGraph()
    resources = list(_walk_resources((plan.get("configuration") or {}).get("root_module") or {}))
    if changes:
        for change in changes:
            graph.add_node(change.address, type=change.type, action=change.action)
    for resource in resources:
        address = str(resource.get("address", ""))
        if address:
            graph.add_node(address, type=resource.get("type", ""))
    for resource in resources:
        address = str(resource.get("address", ""))
        if not address:
            continue
        refs = _references(resource.get("expressions", {}))
        explicit = resource.get("depends_on", [])
        if isinstance(explicit, list):
            refs.update(str(ref) for ref in explicit)
        for ref in refs:
            # A reference may include an attribute or index; map it to the
            # longest known resource address.
            candidates = [node for node in graph.nodes if ref == node or ref.startswith(f"{node}.")]
            if candidates:
                graph.add_edge(max(candidates, key=len), address)
    return graph


def downstream_scores(
    graph: nx.DiGraph, changed: Iterable[ResourceChange], config: dict[str, Any] | None = None
) -> dict[str, float]:
    weight_map = weights(config or {})
    scores: dict[str, float] = {}
    for change in changed:
        if change.address not in graph:
            graph.add_node(change.address, type=change.type)
        affected = nx.descendants(graph, change.address)
        # Include the changed resource itself so a standalone change has a
        # useful, non-zero score.
        affected.add(change.address)
        score = 0.0
        for address in affected:
            node_type = str(graph.nodes[address].get("type", ""))
            score += weight_map.get(address, weight_map.get(node_type, weight_map["default"]))
        scores[change.address] = round(score, 3)
    return scores


def calculate_blast_radius(
    graph: nx.DiGraph, changed: Iterable[ResourceChange], config: dict[str, Any] | None = None
) -> dict[str, float]:
    """Public descriptive alias for callers that use the specification's terminology."""
    return downstream_scores(graph, changed, config)
