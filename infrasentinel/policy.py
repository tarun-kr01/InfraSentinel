from __future__ import annotations

import json
from typing import Any, Iterable

from .models import Finding, ResourceChange


def _finding(rule: str, severity: str, change: ResourceChange, message: str, **details: Any) -> Finding:
    return Finding(rule, severity, change.address, message, details)


def _walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _policy_has_wildcard(value: Any) -> bool:
    """Return true when one policy statement grants both wildcard fields."""
    if isinstance(value, str):
        try:
            return _policy_has_wildcard(json.loads(value))
        except (TypeError, ValueError, json.JSONDecodeError):
            return False
    if isinstance(value, dict):
        statements = value.get("Statement")
        if statements is not None:
            statements = statements if isinstance(statements, list) else [statements]
            for statement in statements:
                if isinstance(statement, dict) and _wildcard(statement.get("Action")) and _wildcard(
                    statement.get("Resource")
                ):
                    return True
        return any(_policy_has_wildcard(child) for child in value.values())
    if isinstance(value, list):
        return any(_policy_has_wildcard(child) for child in value)
    return False


def _wildcard(candidate: Any) -> bool:
    return candidate == "*" or (isinstance(candidate, list) and "*" in candidate)


def _is_public_ingress(value: Any) -> bool:
    for rule in value if isinstance(value, list) else []:
        if not isinstance(rule, dict):
            continue
        cidrs = rule.get("cidr_blocks") or rule.get("cidr_ipv4") or []
        if isinstance(cidrs, str):
            cidrs = [cidrs]
        if "0.0.0.0/0" not in cidrs:
            continue
        from_port = rule.get("from_port", rule.get("from"))
        to_port = rule.get("to_port", rule.get("to"))
        if from_port != 80 or to_port != 80:
            if from_port != 443 or to_port != 443:
                return True
    return False


def evaluate(changes: Iterable[ResourceChange]) -> list[Finding]:
    findings: list[Finding] = []
    for change in changes:
        after = change.after if isinstance(change.after, dict) else {}
        if change.type in {"aws_iam_policy", "aws_iam_role_policy", "aws_iam_user_policy"} and _policy_has_wildcard(
            after.get("policy")
        ):
            findings.append(_finding("iam-wildcard", "block", change, "IAM policy grants a wildcard action or resource"))

        ingress = after.get("ingress")
        if change.type in {"aws_security_group", "aws_security_group_rule"} and _is_public_ingress(ingress):
            findings.append(_finding("open-security-group", "block", change, "Security group ingress is open to the internet outside ports 80/443"))

        if change.action == "create":
            tag_keys = {str(key).lower() for key in change.tags}
            for required in ("env", "owner"):
                if required not in tag_keys:
                    findings.append(_finding("required-tags", "block", change, f"Created resource is missing required tag: {required}", tag=required))

        acl = after.get("acl")
        if change.type in {"aws_s3_bucket", "aws_s3_bucket_acl"} and acl in {"public-read", "public-read-write"}:
            findings.append(_finding("public-s3-acl", "block", change, f"S3 ACL is {acl}"))

        if change.type == "aws_db_instance" and after.get("storage_encrypted") is False:
            findings.append(_finding("unencrypted-rds", "block", change, "RDS storage encryption is disabled"))
        if change.type == "aws_ebs_volume" and after.get("encrypted") is False:
            findings.append(_finding("unencrypted-ebs", "block", change, "EBS volume encryption is disabled"))

        env = next((str(v).lower() for k, v in change.tags.items() if str(k).lower() in {"env", "environment"}), "")
        if env == "prod" and change.action in {"delete", "replace"}:
            findings.append(_finding("prod-destructive-change", "warning", change, f"Production resource will be {change.action}d"))
    return findings


class PolicyEngine:
    """Small state-free facade useful for embedding the policy checks."""

    def evaluate(self, changes: Iterable[ResourceChange]) -> list[Finding]:
        return evaluate(changes)
