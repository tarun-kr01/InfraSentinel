from infrasentinel.models import ResourceChange
from infrasentinel.policy import evaluate


def change(type_, after, action="create", tags=None):
    return ResourceChange("x", type_, "aws", action, None, after, tags or {})


def test_policy_finds_security_and_missing_tags():
    findings = evaluate([change("aws_security_group", {"ingress": [{"cidr_blocks": ["0.0.0.0/0"], "from_port": 22, "to_port": 22}]})])
    assert {f.rule for f in findings} == {"open-security-group", "required-tags"}


def test_policy_finds_wildcard_and_encryption():
    findings = evaluate([
        change("aws_iam_policy", {"policy": '{"Statement":{"Action":"*","Resource":"*"}}'}, tags={"env": "dev", "owner": "x"}),
        change("aws_ebs_volume", {"encrypted": False}, tags={"env": "dev", "owner": "x"}),
    ])
    assert {"iam-wildcard", "unencrypted-ebs"} <= {f.rule for f in findings}


def test_prod_delete_is_warning():
    findings = evaluate([change("aws_instance", {}, "delete", {"env": "prod", "owner": "x"})])
    assert findings[0].severity == "warning"
