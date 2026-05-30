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


# --- Scoring (radar) -------------------------------------------------------

RADAR_EJES: tuple[Tema, ...] = (
    Tema.SEGURIDAD,
    Tema.ECONOMIA,
    Tema.SALUD,
    Tema.EDUCACION,
    Tema.ANTICORRUPCION,
    Tema.MEDIOAMBIENTE,
)
"""The six thematic axes the radar scores. GENERAL is excluded on purpose — it
is a catch-all, not an evaluable policy area."""

EVALUABLE_CANDIDATOS: tuple[Candidato, ...] = (
    Candidato.FAJARDO,
    Candidato.LOPEZ,
    Candidato.CEPEDA,
    Candidato.VALENCIA,
    Candidato.ESPRIELLA,
)
"""Candidates that get a scorecard. NACIONAL is the baseline-data pseudo-author,
not a candidate, so it is never scored."""


@dataclass(frozen=True, slots=True)
class EjeMetrics:
    """Every metric for one candidate on one radar axis, across three tiers of
    trust (see Docs/plan.md §5–6):

    - deterministic — ``volumen_propuestas`` is a raw corpus count, not a judgment.
    - semantic (LLM) — ``solidez`` 1–5, ``densidad_evidencia`` 0–1,
      ``anclaje_nacional`` 1–5, ``coherencia_gestion`` 1–5 (or None when the
      candidate has no prior management to confront the proposal against).
    - reliability — ``solidez`` is the mean of ``solidez_runs`` (K LLM runs);
      ``solidez_std`` and ``confianza`` say how much to trust that mean.
    """

    eje: Tema
    volumen_propuestas: int
    solidez: float
    solidez_std: float
    solidez_runs: list[int]
    confianza: float
    densidad_evidencia: float
    anclaje_nacional: int
    coherencia_gestion: int | None
    justificacion: str
    fuentes: list[str]


@dataclass(frozen=True, slots=True)
class Scorecard:
    """A candidate's full scorecard: per-axis metrics plus corpus-level stats.

    ``cobertura`` (0–6) = axes with at least one proposal. ``concentracion_hhi``
    is the Herfindahl index over proposal volume per axis (1/6 ≈ balanced agenda,
    1.0 = monothematic). ``presencia_historica`` = count of ``dato_historico``
    chunks (0 is itself a finding: no verifiable track record).
    """

    candidato: Candidato
    ejes: list[EjeMetrics]
    cobertura: int
    concentracion_hhi: float
    presencia_historica: int
    computed_at: str
