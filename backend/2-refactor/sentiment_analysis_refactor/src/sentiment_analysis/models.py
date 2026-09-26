from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class SentimentResult:
    negative: float
    neutral: float
    positive: float


@runtime_checkable
class SentimentProvider(Protocol):
    def analyze(self, text: str) -> SentimentResult:
        ...
