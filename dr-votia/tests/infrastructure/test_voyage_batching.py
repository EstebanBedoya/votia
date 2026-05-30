"""Token-budget batching for the Voyage adapter — pure, no network."""

from __future__ import annotations

from dr_votia.infrastructure.embeddings.voyage import (
    MAX_ITEMS_PER_REQUEST,
    _estimate_tokens,
    _make_batches,
)


def test_batches_respect_token_budget() -> None:
    texts = ["x" * 300] * 10  # each ~100 estimated tokens
    batches = _make_batches(texts, max_tokens=250, max_items=128)

    # ~100 tokens each → at most 2 per 250-token batch.
    assert all(sum(_estimate_tokens(t) for t in b) <= 250 for b in batches)
    assert sum(len(b) for b in batches) == 10


def test_batches_respect_item_cap() -> None:
    texts = ["x"] * (MAX_ITEMS_PER_REQUEST + 5)  # tiny texts, token budget irrelevant
    batches = _make_batches(texts, max_tokens=10_000, max_items=MAX_ITEMS_PER_REQUEST)

    assert all(len(b) <= MAX_ITEMS_PER_REQUEST for b in batches)
    assert sum(len(b) for b in batches) == MAX_ITEMS_PER_REQUEST + 5


def test_single_oversized_text_still_yields_one_batch() -> None:
    batches = _make_batches(["y" * 9000], max_tokens=1000, max_items=128)
    assert len(batches) == 1
