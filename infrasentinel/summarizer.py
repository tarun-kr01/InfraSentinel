from __future__ import annotations

import json
from typing import Protocol

from .models import ScanResult


class Summarizer(Protocol):
    def summarize(self, result: ScanResult) -> str: ...


class DeterministicSummarizer:
    def summarize(self, result: ScanResult) -> str:
        counts = result.as_dict()["counts"]
        cost = "unavailable"
        if result.cost:
            cost = f"{result.cost.delta_monthly:+.2f} {result.cost.currency}/month"
        return (
            f"{counts['resources']} resources changed; {counts['findings']} findings "
            f"({counts['blocking']} blocking, {counts['warnings']} warnings); "
            f"cost delta {cost}."
        )


class OpenAISummarizer(DeterministicSummarizer):
    """Optional client adapter; without a client it remains deterministic."""

    def __init__(self, client: object | None = None, model: str = "gpt-4o-mini"):
        self.client, self.model = client, model

    def summarize(self, result: ScanResult) -> str:
        if self.client is None:
            return super().summarize(result)
        try:
            prompt = json.dumps(result.as_dict(), sort_keys=True)
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                messages=[{"role": "user", "content": f"Summarize this structured scan only:\n{prompt}"}],
            )
            return response.choices[0].message.content
        except Exception:
            return super().summarize(result)


class AnthropicSummarizer(DeterministicSummarizer):
    """Optional client adapter; without a client it remains deterministic."""

    def __init__(self, client: object | None = None, model: str = "claude-3-5-haiku-latest"):
        self.client, self.model = client, model

    def summarize(self, result: ScanResult) -> str:
        if self.client is None:
            return super().summarize(result)
        try:
            prompt = json.dumps(result.as_dict(), sort_keys=True)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                temperature=0,
                messages=[{"role": "user", "content": f"Summarize this structured scan only:\n{prompt}"}],
            )
            return response.content[0].text
        except Exception:
            return super().summarize(result)
