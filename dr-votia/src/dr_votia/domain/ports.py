"""Ports — the interfaces the domain depends on.

Defined as :class:`typing.Protocol` so adapters satisfy them structurally, with
no inheritance coupling. The application layer programs against these; the
infrastructure layer implements them. This is the seam that lets the web
entrypoint reuse the exact same use cases as the CLI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from dr_votia.domain.models import (
    Candidato,
    EmbeddedChunk,
    Fragment,
    RetrievedChunk,
    Tema,
    Tipo,
)


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Turns text into vectors.

    Documents and queries are embedded with different intents on purpose —
    Voyage (and most providers) yield better retrieval when the query is
    embedded as a query, not as a document.
    """

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


@runtime_checkable
class VectorStore(Protocol):
    """Persists embedded chunks and runs similarity search over them."""

    def add(self, chunks: list[EmbeddedChunk]) -> int: ...

    def clear(self) -> None:
        """Remove every stored chunk (used to re-ingest from a clean slate)."""
        ...

    def search(
        self,
        query_embedding: list[float],
        *,
        k: int = 5,
        candidato: Candidato | None = None,
        tema: Tema | None = None,
        tipo: Tipo | None = None,
    ) -> list[RetrievedChunk]: ...


@runtime_checkable
class LLMProvider(Protocol):
    """Generates a grounded answer from a system prompt and a user message."""

    def generate(self, *, system: str, user: str) -> str: ...


@runtime_checkable
class DocumentReader(Protocol):
    """Extracts text fragments from a source file of a given format."""

    def supports(self, path: Path) -> bool: ...

    def read(self, path: Path) -> list[Fragment]: ...
