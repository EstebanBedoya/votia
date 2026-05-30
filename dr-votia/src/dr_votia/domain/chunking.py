"""Text chunking — a pure business rule, fully unit-testable without I/O.

Splits on blank lines first, but ALWAYS enforces a hard maximum size: an
oversized paragraph (common in serialized spreadsheets or dense PDF pages, which
lack blank-line breaks) is broken down by sentence/line boundaries, and as a last
resort by fixed character windows. Without this, a whole worksheet could become a
single multi-megabyte chunk that the embedding model silently truncates.
"""

from __future__ import annotations

import re

DEFAULT_CHUNK_SIZE = 800
DEFAULT_OVERLAP = 150
MIN_CHUNK_LEN = 100

# Sentence/line boundaries used to break down an oversized paragraph.
_BOUNDARY = re.compile(r"(?<=[.!?;])\s+|\n+")


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks bounded by ``chunk_size``.

    Paragraphs are accumulated up to ``chunk_size``; any paragraph larger than
    that is pre-split so no unit ever exceeds the budget. Overlap carries the
    tail of one chunk into the next. Chunks shorter than :data:`MIN_CHUNK_LEN`
    are dropped as noise.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    units: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= chunk_size:
            units.append(paragraph)
        else:
            units.extend(_split_oversized(paragraph, chunk_size, overlap))

    chunks: list[str] = []
    current = ""
    for unit in units:
        if len(current) + len(unit) <= chunk_size:
            current += ("\n\n" if current else "") + unit
        else:
            if current:
                chunks.append(current)
            tail = current[-overlap:] if len(current) > overlap else ""
            current = f"{tail}\n\n{unit}" if tail else unit

    if current:
        chunks.append(current)

    return [c for c in chunks if len(c) > MIN_CHUNK_LEN]


def _split_oversized(paragraph: str, chunk_size: int, overlap: int) -> list[str]:
    """Break a too-long paragraph into pieces no larger than ``chunk_size``."""
    pieces: list[str] = []
    current = ""
    for part in _BOUNDARY.split(paragraph):
        part = part.strip()
        if not part:
            continue
        if len(part) > chunk_size:
            if current:
                pieces.append(current)
                current = ""
            pieces.extend(_window_split(part, chunk_size, overlap))
        elif len(current) + len(part) + 1 <= chunk_size:
            current = f"{current} {part}" if current else part
        else:
            pieces.append(current)
            current = part
    if current:
        pieces.append(current)
    return pieces


def _window_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Last resort: slice a long, boundary-less string into overlapping windows."""
    step = max(1, chunk_size - overlap)
    return [text[i : i + chunk_size] for i in range(0, len(text), step)]
