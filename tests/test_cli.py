import json
from pathlib import Path

from typer.testing import CliRunner

from infrasentinel.cli import app


def test_cli_returns_json_and_nonzero_for_blocking_plan():
    result = CliRunner().invoke(app, ["scan", "--plan", str(Path("tests/fixtures/plan.json"))])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["counts"]["blocking"] >= 1
