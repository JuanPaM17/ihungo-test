from __future__ import annotations

import logging
import os

import paralleldots
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from sentiment_analysis.models import SentimentResult

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 4
_WAIT_MIN = 1
_WAIT_MAX = 30


class ParallelDotsProvider:
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or os.environ.get("PARALLELDOTS_API_KEY")
        if not key:
            raise EnvironmentError(
                "PARALLELDOTS_API_KEY environment variable is not set."
            )
        paralleldots.set_api_key(key)

    def analyze(self, text: str) -> SentimentResult:
        try:
            return self._analyze_with_retry(text)
        except RetryError as exc:
            raise RuntimeError(
                f"ParallelDots failed after {_MAX_ATTEMPTS} attempts."
            ) from exc

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(_MAX_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=_WAIT_MIN, max=_WAIT_MAX),
        reraise=False,
    )
    def _analyze_with_retry(self, text: str) -> SentimentResult:
        response: dict = paralleldots.sentiment(text)  # type: ignore[no-untyped-call]

        if "sentiment" not in response:
            raise ValueError(f"Unexpected ParallelDots response: {response}")

        sentiment = response["sentiment"]
        return SentimentResult(
            negative=round(sentiment["negative"] * 100, 3),
            neutral=round(sentiment["neutral"] * 100, 3),
            positive=round(sentiment["positive"] * 100, 3),
        )
