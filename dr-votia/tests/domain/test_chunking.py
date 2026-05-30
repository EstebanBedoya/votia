from __future__ import annotations

from dr_votia.domain.chunking import MIN_CHUNK_LEN, chunk_text


def test_short_text_is_discarded() -> None:
    assert chunk_text("hola mundo") == []


def test_long_text_splits_into_multiple_chunks() -> None:
    paragraph = "palabra " * 40  # ~320 chars
    text = "\n\n".join([paragraph] * 6)

    chunks = chunk_text(text, chunk_size=400, overlap=50)

    assert len(chunks) > 1
    assert all(len(c) > MIN_CHUNK_LEN for c in chunks)


def test_overlap_carries_tail_into_next_chunk() -> None:
    first = "A" * 300
    second = "B" * 300
    chunks = chunk_text(f"{first}\n\n{second}", chunk_size=350, overlap=50)

    assert len(chunks) == 2
    # The second chunk should begin with the tail of the first (overlap).
    assert chunks[1].startswith("A" * 50)


def test_oversized_paragraph_without_blank_lines_is_split() -> None:
    # The spreadsheet bug: one giant block with no blank-line breaks must NOT
    # become a single mega-chunk.
    text = "x" * 10_000
    chunks = chunk_text(text, chunk_size=800, overlap=100)

    assert len(chunks) > 1
    assert max(len(c) for c in chunks) <= 800 + 100 + 5


def test_oversized_paragraph_splits_on_line_boundaries() -> None:
    # Serialized rows separated by single newlines (no blank lines), like an XLSX.
    text = "\n".join(f"fila {i}: valor {i}" for i in range(500))
    chunks = chunk_text(text, chunk_size=800, overlap=100)

    assert len(chunks) > 1
    assert max(len(c) for c in chunks) <= 800 + 100 + 5
