from infrasentinel.graph import build_dependency_graph, downstream_scores
from infrasentinel.parser import parse_plan


def test_graph_explicit_dependency_and_weight_override():
    plan = {
        "resource_changes": [{"address": "aws_iam_policy.p", "type": "aws_iam_policy", "change": {"actions": ["create"]}},
                             {"address": "aws_instance.i", "type": "aws_instance", "change": {"actions": ["update"]}}],
        "configuration": {"root_module": {"resources": [
            {"address": "aws_iam_policy.p", "type": "aws_iam_policy", "expressions": {}},
            {"address": "aws_instance.i", "type": "aws_instance", "depends_on": ["aws_iam_policy.p"], "expressions": {}},
        ]}},
    }
    changes = parse_plan(plan)
    graph = build_dependency_graph(plan, changes)
    assert list(graph.successors("aws_iam_policy.p")) == ["aws_instance.i"]
    assert downstream_scores(graph, changes, {"weights": {"default": 2}})["aws_iam_policy.p"] == 5
