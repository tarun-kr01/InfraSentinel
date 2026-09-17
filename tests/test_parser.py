import json
from pathlib import Path

from infrasentinel.parser import parse_plan, parse_plan_file


def test_parser_normalizes_replace_and_tags():
    changes = parse_plan({"resource_changes": [{
        "address": "aws_db_instance.db", "type": "aws_db_instance",
        "provider_name": "hashicorp/aws",
        "change": {"actions": ["delete", "create"], "before": {"x": 1}, "after": {"tags": {"env": "prod"}}},
    }]})
    assert changes[0].action == "replace"
    assert changes[0].tags == {"env": "prod"}


def test_fixture_loads():
    _, changes = parse_plan_file(Path("tests/fixtures/plan.json"))
    assert len(changes) == 2
