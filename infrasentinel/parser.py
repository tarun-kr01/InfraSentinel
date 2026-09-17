from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ResourceChange


def normalize_action(actions: list[str] | tuple[str, ...] | str | None) -> str:
    """Turn Terraform's action list into create/update/delete/replace/no-op."""
    if isinstance(actions, str):
        actions = [actions]
    actions = list(actions or [])
    if "create" in actions and "delete" in actions:
        return "replace"
    if "replace" in actions:
        return "replace"
    for action in ("create", "update", "delete", "read", "no-op"):
        if action in actions:
            return action
    return "no-op"


def _tags(values: Any) -> dict[str, Any]:
    if not isinstance(values, dict):
        return {}
    tags = values.get("tags")
    if isinstance(tags, dict):
        return tags
    # Some providers expose tags_all instead of tags.
    tags_all = values.get("tags_all")
    return tags_all if isinstance(tags_all, dict) else {}


def parse_plan(plan: dict[str, Any]) -> list[ResourceChange]:
    changes: list[ResourceChange] = []
    for item in plan.get("resource_changes", []) or []:
        if not isinstance(item, dict) or not item.get("address"):
            continue
        change = item.get("change") or {}
        before, after = change.get("before"), change.get("after")
        provider = item.get("provider_name") or item.get("provider") or ""
        if provider.startswith("provider["):
            provider = provider.split('"', 2)[1] if '"' in provider else provider
        changes.append(
            ResourceChange(
                address=str(item["address"]),
                type=str(item.get("type", "")),
                provider=str(provider),
                action=normalize_action(change.get("actions")),
                before=before,
                after=after,
                tags=_tags(after) or _tags(before),
            )
        )
    return changes


def parse_plan_file(path: str | Path) -> tuple[dict[str, Any], list[ResourceChange]]:
    with Path(path).open(encoding="utf-8") as stream:
        plan = json.load(stream)
    if not isinstance(plan, dict):
        raise ValueError("Terraform plan JSON must be an object")
    return plan, parse_plan(plan)
