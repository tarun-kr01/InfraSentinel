from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .config import load_config
from .cost import InfracostAdapter
from .graph import build_dependency_graph, downstream_scores
from .models import ScanResult
from .parser import parse_plan_file
from .policy import evaluate
from .summarizer import DeterministicSummarizer

app = typer.Typer(add_completion=False, help="Scan Terraform plans for infrastructure risk.")


@app.callback()
def main() -> None:
    """InfraSentinel commands."""


@app.command()
def scan(
    plan: Path = typer.Option(..., "--plan", exists=True, readable=True, help="terraform show -json output"),
    config: Optional[Path] = typer.Option(None, "--config", help="Policy and blast-radius YAML"),
) -> None:
    plan_data, changes = parse_plan_file(plan)
    settings = load_config(config)
    graph = build_dependency_graph(plan_data, changes)
    cost = InfracostAdapter().calculate(plan)
    result = ScanResult(changes, evaluate(changes), downstream_scores(graph, changes, settings), cost)
    result.summary = DeterministicSummarizer().summarize(result)
    typer.echo(json.dumps(result.as_dict(), sort_keys=True, indent=2))
    raise typer.Exit(code=1 if any(f.blocking for f in result.findings) else 0)


if __name__ == "__main__":
    app()
