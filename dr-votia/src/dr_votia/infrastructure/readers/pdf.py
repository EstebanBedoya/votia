"""PDF reader adapter (PyMuPDF). Implements the DocumentReader port."""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

from dr_votia.domain.models import Fragment

MIN_PAGE_LEN = 50


class PdfReader:
    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def read(self, path: Path) -> list[Fragment]:
        fragments: list[Fragment] = []
        with fitz.open(str(path)) as doc:
            for index, page in enumerate(doc):
                text = page.get_text("text").strip()
                if len(text) > MIN_PAGE_LEN:
                    fragments.append(Fragment(text=text, page=index + 1))
        return fragments
