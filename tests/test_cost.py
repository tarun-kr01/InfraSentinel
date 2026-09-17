import json
from pathlib import Path

from infrasentinel.cost import parse_infracost


def test_parse_cost_delta():
    data = json.loads(Path("tests/fixtures/infracost.json").read_text())
    cost = parse_infracost(data)
    assert cost.delta_monthly == 2.5
