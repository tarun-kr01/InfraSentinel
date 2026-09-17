from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_WEIGHTS = {
    "default": 1.0,
    "aws_iam_role": 3.0,
    "aws_iam_policy": 3.0,
    "aws_db_instance": 3.0,
    "aws_s3_bucket": 2.0,
    "aws_security_group": 2.0,
}


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    candidate = Path(path) if path else Path(".infrasentinel.yaml")
    if not candidate.exists():
        return {}
    with candidate.open(encoding="utf-8") as stream:
        value = yaml.safe_load(stream) or {}
    return value if isinstance(value, dict) else {}


def weights(config: dict[str, Any]) -> dict[str, float]:
    result = dict(DEFAULT_WEIGHTS)
    raw = config.get("weights", {})
    if not raw and isinstance(config.get("blast_radius"), dict):
        raw = config["blast_radius"].get("weights", {})
    if isinstance(raw, dict):
        for key, value in raw.items():
            try:
                result[str(key)] = float(value)
            except (TypeError, ValueError):
                continue
    return result
