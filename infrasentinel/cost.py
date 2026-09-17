from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .models import CostDelta


def _number(value: Any) -> float:
    try:
        if isinstance(value, str):
            value = re.sub(r"[^0-9.+-]", "", value)
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def parse_infracost(data: dict[str, Any]) -> CostDelta:
    projects = data.get("projects")
    if isinstance(projects, list):
        before = after = 0.0
        for project in projects:
            if not isinstance(project, dict):
                continue
            breakdown = project.get("breakdown", project)
            if not isinstance(breakdown, dict):
                continue
            project_after = _number(breakdown.get("totalMonthlyCost", project.get("monthlyCost")))
            after += project_after
            diff = breakdown.get("diff", project.get("diff", {}))
            if isinstance(diff, dict):
                delta = _number(diff.get("totalMonthlyCost", diff.get("monthlyCost")))
                before += project_after - delta
        if before == 0 and after == 0:
            before = _number(data.get("beforeMonthlyCost"))
            after = _number(data.get("afterMonthlyCost"))
        return CostDelta(before, after, after - before, str(data.get("currency", "USD")))
    before = _number(data.get("beforeMonthlyCost", data.get("before_monthly")))
    after = _number(data.get("afterMonthlyCost", data.get("totalMonthlyCost", data.get("after_monthly"))))
    delta = _number(data.get("monthlyCostDelta", data.get("deltaMonthlyCost", data.get("delta_monthly", after - before))))
    return CostDelta(before, after, delta, str(data.get("currency", "USD")))


class InfracostAdapter:
    def __init__(self, executable: str = "infracost", timeout: int = 60):
        self.executable, self.timeout = executable, timeout

    def calculate(self, plan_path: str | Path) -> CostDelta | None:
        try:
            completed = subprocess.run(
                [self.executable, "breakdown", "--path", str(plan_path), "--format", "json"],
                check=True, capture_output=True, text=True, timeout=self.timeout,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        try:
            value = json.loads(completed.stdout)
        except json.JSONDecodeError:
            return None
        return parse_infracost(value) if isinstance(value, dict) else None
