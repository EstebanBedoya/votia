"""Voyage AI embeddings adapter. Implements the EmbeddingProvider port.

Defaults to ``voyage-3.5`` (1024 dims), matching the ``vector(1024)`` column.
(``voyage-large-2`` produces 1536 dims and is NOT compatible.)

Voyage's free tier (no payment method) caps usage at 3 requests/min and 10K
tokens/min. This adapter respects both with a sliding-window limiter and batches
sized to a token budget, plus exponential backoff on any rate-limit response.
Raise ``tokens_per_min`` / ``requests_per_min`` once a payment method unlocks the
standard limits.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import cast

import voyageai

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "voyage-3.5"
MAX_ITEMS_PER_REQUEST = 128  # Voyage hard limit per request
FREE_TIER_TPM = 10_000
FREE_TIER_RPM = 3
DEFAULT_MAX_TOKENS_PER_REQUEST = 9_000  # safety margin under a 10K/min budget
MAX_RETRIES = 5
INITIAL_BACKOFF = 20.0


def _estimate_tokens(text: str) -> int:
    """Estimate tokens from characters. Spanish averages ~4 chars/token; the +1
    keeps a small safety margin under the per-minute cap without over-throttling.
    """
    return max(1, len(text) // 4 + 1)


def _make_batches(texts: list[str], *, max_tokens: int, max_items: int) -> list[list[str]]:
    """Group texts into batches bounded by both a token budget and an item count."""
    batches: list[list[str]] = []
    current: list[str] = []
    current_tokens = 0
    for text in texts:
        tokens = _estimate_tokens(text)
        too_many_tokens = current_tokens + tokens > max_tokens
        too_many_items = len(current) >= max_items
        if current and (too_many_tokens or too_many_items):
            batches.append(current)
            current, current_tokens = [], 0
        current.append(text)
        current_tokens += tokens
    if current:
        batches.append(current)
    return batches


class _SlidingWindowLimiter:
    """Blocks until sending ``tokens`` keeps us within both per-minute limits."""

    def __init__(self, tokens_per_min: int, requests_per_min: int) -> None:
        self._tpm = tokens_per_min
        self._rpm = requests_per_min
        self._events: deque[tuple[float, int]] = deque()

    def acquire(self, tokens: int) -> None:
        while True:
            now = time.monotonic()
            while self._events and now - self._events[0][0] >= 60:
                self._events.popleft()
            used = sum(t for _, t in self._events)
            if len(self._events) < self._rpm and used + tokens <= self._tpm:
                self._events.append((now, tokens))
                return
            wait = 60 - (now - self._events[0][0]) + 0.5
            logger.info("Límite de tasa Voyage: esperando %.0fs…", wait)
            time.sleep(max(wait, 1.0))


class VoyageEmbeddings:
    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEFAULT_MODEL,
        tokens_per_min: int = FREE_TIER_TPM,
        requests_per_min: int = FREE_TIER_RPM,
        max_tokens_per_request: int = DEFAULT_MAX_TOKENS_PER_REQUEST,
    ) -> None:
        self._client = voyageai.Client(api_key=api_key)  # type: ignore[attr-defined]
        self._model = model
        self._limiter = _SlidingWindowLimiter(tokens_per_min, requests_per_min)
        self._max_tokens = min(max_tokens_per_request, tokens_per_min)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        batches = _make_batches(texts, max_tokens=self._max_tokens, max_items=MAX_ITEMS_PER_REQUEST)
        out: list[list[float]] = []
        for i, batch in enumerate(batches, start=1):
            logger.info("Embeddings: batch %d/%d (%d textos)…", i, len(batches), len(batch))
            self._limiter.acquire(sum(_estimate_tokens(t) for t in batch))
            out.extend(self._embed(batch, input_type="document"))
        return out

    def embed_query(self, text: str) -> list[float]:
        self._limiter.acquire(_estimate_tokens(text))
        return self._embed([text], input_type="query")[0]

    def _embed(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        backoff = INITIAL_BACKOFF
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = self._client.embed(texts, model=self._model, input_type=input_type)
                return cast("list[list[float]]", result.embeddings)
            except Exception as error:
                is_rate_limit = "ratelimit" in type(error).__name__.lower()
                if not is_rate_limit or attempt == MAX_RETRIES:
                    raise
                logger.warning(
                    "RateLimit (intento %d/%d) — backoff %.0fs…", attempt, MAX_RETRIES, backoff
                )
                time.sleep(backoff)
                backoff *= 2
        raise RuntimeError("unreachable")  # pragma: no cover
