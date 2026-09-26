from __future__ import annotations

from sentiment_analysis.models import SentimentResult


class FakeSentimentProvider:
    """In-memory fake that never calls ParallelDots."""

    def __init__(self, result: SentimentResult | None = None) -> None:
        self._result = result or SentimentResult(
            negative=10.0, neutral=20.0, positive=70.0
        )
        self.calls: list[str] = []

    def analyze(self, text: str) -> SentimentResult:
        self.calls.append(text)
        return self._result


class FailingSentimentProvider:
    """Always raises, used to test error handling."""

    def __init__(self, exc: Exception | None = None) -> None:
        self._exc = exc or RuntimeError("provider unavailable")

    def analyze(self, text: str) -> SentimentResult:
        raise self._exc
