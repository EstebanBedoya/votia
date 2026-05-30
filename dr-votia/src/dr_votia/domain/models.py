"""Domain entities. Pure data — no I/O, no third-party SDK imports.

These types are the language the whole application speaks. Adapters translate
external representations (PDF pages, Supabase rows, Voyage vectors) into these.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Candidato(StrEnum):
    FAJARDO = "fajardo"
    LOPEZ = "lopez"
    CEPEDA = "cepeda"
    VALENCIA = "valencia"
    ESPRIELLA = "espriella"
    NACIONAL = "nacional"


class Tema(StrEnum):
    SEGURIDAD = "seguridad"
    ECONOMIA = "economia"
    SALUD = "salud"
    EDUCACION = "educacion"
    ANTICORRUPCION = "anticorrupcion"
    MEDIOAMBIENTE = "medioambiente"
    GENERAL = "general"


class Tipo(StrEnum):
    PROPUESTA = "propuesta"
    DATO_HISTORICO = "dato_historico"
    ESTADISTICA_NACIONAL = "estadistica_nacional"


@dataclass(frozen=True, slots=True)
class Fragment:
    """A unit of text extracted from a source, before chunking.

    ``page`` is set for paginated sources (PDFs) and ``None`` otherwise.
    """

    text: str
    page: int | None = None


@dataclass(frozen=True, slots=True)
class Chunk:
    """A retrieval-ready piece of text plus its metadata.

    Mirrors a row of the ``documents`` table, minus the generated ``id`` and the
    ``embedding`` (which is attached later as an :class:`EmbeddedChunk`).
    """

    content: str
    tipo: Tipo
    fuente: str
    candidato: Candidato | None = None
    tema: Tema | None = None
    subtema: str | None = None
    pagina: int | None = None
    año: int | None = None
    verificable: bool = True


@dataclass(frozen=True, slots=True)
class EmbeddedChunk:
    chunk: Chunk
    embedding: list[float]


@dataclass(frozen=True, slots=True)
class Query:
    """A user question plus optional metadata filters for retrieval."""

    text: str
    k: int = 5
    candidato: Candidato | None = None
    tema: Tema | None = None
    tipo: Tipo | None = None


@dataclass(frozen=True, slots=True)
class RefinedQuery:
    """Output of the cheap preprocessing model: a retrieval-optimized search
    string plus an optional classified topic."""

    search_text: str
    tema: Tema | None = None


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """A chunk returned by the vector store, with its similarity score."""

    id: int
    content: str
    tipo: Tipo
    fuente: str
    similarity: float
    candidato: Candidato | None = None
    tema: Tema | None = None
    subtema: str | None = None
    pagina: int | None = None
    año: int | None = None


@dataclass(frozen=True, slots=True)
class Answer:
    """The result of the RAG use case: generated text plus its sources."""

    text: str
    sources: list[RetrievedChunk] = field(default_factory=list)
