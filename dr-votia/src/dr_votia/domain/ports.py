"""Ports — the interfaces the domain depends on.

Defined as :class:`typing.Protocol` so adapters satisfy them structurally, with
no inheritance coupling. The application layer programs against these; the
infrastructure layer implements them. This is the seam that lets the web
entrypoint reuse the exact same use cases as the CLI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from dr_votia.domain.conversation import Message, Session
from dr_votia.domain.models import (
    Candidato,
    EmbeddedChunk,
    Fragment,
    LLMResult,
    RetrievedChunk,
    Scorecard,
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

    def count(
        self,
        *,
        candidato: Candidato | None = None,
        tema: Tema | None = None,
        tipo: Tipo | None = None,
    ) -> int:
        """Count stored chunks matching the filters — the deterministic tier of
        the scoring (e.g. how many proposals a candidate has per axis)."""
        ...


@runtime_checkable
class ScoreRepository(Protocol):
    """Persists computed scorecards and reads them back for the radar endpoint.

    Scoring is expensive (K LLM runs × 6 axes × candidate), so it is computed
    offline by the CLI and stored here; the web layer only reads."""

    def save(self, scorecard: Scorecard) -> None: ...

    def get(self, candidato: Candidato) -> Scorecard | None: ...

    def all(self) -> list[Scorecard]: ...


@runtime_checkable
class LLMProvider(Protocol):
    """Generates a grounded answer from a system prompt and a user message.

    Returns an :class:`LLMResult` (text + usage) rather than a bare string, so
    callers can account for per-request cost. Text-only callers read ``.text``.
    """

    def generate(self, *, system: str, user: str) -> LLMResult: ...


@runtime_checkable
class SessionStore(Protocol):
    """Persists conversation sessions and their messages, and answers the
    counting queries the rate limiter needs.

    ``recent_request_count`` counts user turns in a trailing time window, keyed
    by IP or by session — the two axes the edge enforces limits on."""

    def create(self) -> Session: ...

    def exists(self, session_id: str) -> bool: ...

    def append(self, session_id: str, message: Message, *, ip: str | None = None) -> None: ...

    def add_cost(self, session_id: str, cost_usd: float) -> float:
        """Atomically add ``cost_usd`` to the session's running spend and return
        the new total. Used to track per-session OpenRouter dollars."""
        ...

    def session_cost(self, session_id: str) -> float:
        """The session's accumulated OpenRouter spend in USD."""
        ...

    def history(self, session_id: str, *, limit: int = 10) -> list[Message]:
        """The most recent ``limit`` messages, in chronological order."""
        ...

    def recent_request_count(
        self,
        *,
        within_seconds: int,
        ip: str | None = None,
        session_id: str | None = None,
    ) -> int:
        """User turns seen in the last ``within_seconds``, filtered by whichever
        key is provided. Exactly one of ``ip`` / ``session_id`` is expected."""
        ...


@runtime_checkable
class DocumentReader(Protocol):
    """Extracts text fragments from a source file of a given format."""

    def supports(self, path: Path) -> bool: ...

    def read(self, path: Path) -> list[Fragment]: ...
