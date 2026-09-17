from infrasentinel.models import Finding, ResourceChange, ScanResult
from infrasentinel.summarizer import DeterministicSummarizer


def test_summary_has_exact_counts_and_cost():
    result = ScanResult([ResourceChange("x", "aws_instance", "aws", "update")],
                        [Finding("r", "block", "x", "bad")], {"x": 1})
    text = DeterministicSummarizer().summarize(result)
    assert "1 resources changed" in text
    assert "1 findings (1 blocking, 0 warnings)" in text
