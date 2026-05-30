"""Plain-text and Markdown reader adapter. Implements the DocumentReader port.

Both .txt and .md are read as a single unpaginated Fragment; the chunker handles
splitting downstream.
"""

from __future__ import annotations

from pathlib import Path

from dr_votia.domain.models import Fragment


class TextReader:
    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in {".txt", ".md", ".markdown"}

    def read(self, path: Path) -> list[Fragment]:
        text = path.read_text(encoding="utf-8").strip()
        return [Fragment(text=text)] if text else []
