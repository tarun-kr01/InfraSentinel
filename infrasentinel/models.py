from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ResourceChange:
    address: str
    type: str
    provider: str
    action: str
    before: Any = None
    after: Any = None
    tags: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "address": self.address,
            "type": self.type,
            "provider": self.provider,
            "action": self.action,
            "before": self.before,
            "after": self.after,
            "tags": self.tags,
        }


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    address: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def blocking(self) -> bool:
        return self.severity == "block"

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "address": self.address,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class CostDelta:
    before_monthly: float
    after_monthly: float
    delta_monthly: float
    currency: str = "USD"

    def as_dict(self) -> dict[str, Any]:
        return {
            "before_monthly": self.before_monthly,
            "after_monthly": self.after_monthly,
            "delta_monthly": self.delta_monthly,
            "currency": self.currency,
        }


@dataclass
class ScanResult:
    changes: list[ResourceChange]
    findings: list[Finding]
    blast_radius: dict[str, float]
    cost: CostDelta | None = None
    summary: str = ""

    def as_dict(self) -> dict[str, Any]:
        counts = {
            "resources": len(self.changes),
            "findings": len(self.findings),
            "blocking": sum(f.blocking for f in self.findings),
            "warnings": sum(f.severity == "warning" for f in self.findings),
        }
        return {
            "changes": [c.as_dict() for c in self.changes],
            "findings": [f.as_dict() for f in self.findings],
            "blast_radius": self.blast_radius,
            "cost": self.cost.as_dict() if self.cost else None,
            "counts": counts,
            "summary": self.summary,
        }
