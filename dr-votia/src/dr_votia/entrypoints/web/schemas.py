"""HTTP DTOs for the web layer. These translate between the JSON API and the
domain models — the domain never depends on them."""

from __future__ import annotations

from pydantic import BaseModel, Field

from dr_votia.domain.models import (
    Answer,
    Candidato,
    EjeMetrics,
    RetrievedChunk,
    Scorecard,
    Tema,
    Tipo,
)


class UsageResponse(BaseModel):
    """OpenRouter account credit usage (lifetime). Kept for backward compat."""

    total: float = Field(description="Total purchased credits.")
    used: float = Field(description="Credits consumed so far.")
    remaining: float = Field(description="Credits left.")
    pct: float | None = Field(
        default=None, description="Remaining as a percentage (None if no credit cap)."
    )


class KeyResponse(BaseModel):
    """OpenRouter API-key spending limit — powers the 'ENERGÍA' gauge."""

    label: str = Field(description="Human-readable key label.")
    usage: float = Field(description="USD spent on this key.")
    limit: float | None = Field(default=None, description="USD spending cap (None if uncapped).")
    limit_remaining: float | None = Field(
        default=None, description="USD left before the cap (None if uncapped)."
    )
    is_free_tier: bool = Field(default=False)
    pct: float | None = Field(
        default=None, description="Remaining as a percentage of the limit (None if no cap)."
    )


class SessionUsageResponse(BaseModel):
    """How many OpenRouter dollars the current session has spent."""

    session_id: str
    cost_usd: float = Field(description="Accumulated USD spend for this session.")


class ConfigResponse(BaseModel):
    """Which models the system runs on — shown in the character panel."""

    answer_model: str = Field(description="Chat answer model slug.")
    score_model: str = Field(description="Radar scoring model slug.")
    query_model: str = Field(description="Cheap RAG preprocessing model slug.")


class ChatRequest(BaseModel):
    pregunta: str = Field(min_length=1, description="La pregunta del usuario.")
    k: int = Field(default=5, ge=1, le=20)
    candidato: Candidato | None = None
    tema: Tema | None = None
    tipo: Tipo | None = None


class SourceDTO(BaseModel):
    fuente: str
    tipo: Tipo
    similarity: float
    content: str
    candidato: Candidato | None = None
    tema: Tema | None = None
    subtema: str | None = None
    pagina: int | None = None
    año: int | None = None

    @classmethod
    def from_chunk(cls, chunk: RetrievedChunk) -> SourceDTO:
        return cls(
            fuente=chunk.fuente,
            tipo=chunk.tipo,
            similarity=chunk.similarity,
            content=chunk.content,
            candidato=chunk.candidato,
            tema=chunk.tema,
            subtema=chunk.subtema,
            pagina=chunk.pagina,
            año=chunk.año,
        )


class ChatResponse(BaseModel):
    respuesta: str
    fuentes: list[SourceDTO]
    session_id: str | None = None
    cost_usd: float = Field(default=0.0, description="USD spent on this turn.")
    model: str | None = Field(default=None, description="Answer model that served this turn.")
    session_cost_usd: float | None = Field(
        default=None, description="Running USD total for the session after this turn."
    )

    @classmethod
    def from_answer(
        cls,
        answer: Answer,
        *,
        session_id: str | None = None,
        model: str | None = None,
        session_cost_usd: float | None = None,
    ) -> ChatResponse:
        return cls(
            respuesta=answer.text,
            fuentes=[SourceDTO.from_chunk(c) for c in answer.sources],
            session_id=session_id,
            cost_usd=answer.cost_usd,
            model=model,
            session_cost_usd=session_cost_usd,
        )


class EjeScoreDTO(BaseModel):
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

    @classmethod
    def from_domain(cls, e: EjeMetrics) -> EjeScoreDTO:
        return cls(
            eje=e.eje,
            volumen_propuestas=e.volumen_propuestas,
            solidez=e.solidez,
            solidez_std=e.solidez_std,
            solidez_runs=e.solidez_runs,
            confianza=e.confianza,
            densidad_evidencia=e.densidad_evidencia,
            anclaje_nacional=e.anclaje_nacional,
            coherencia_gestion=e.coherencia_gestion,
            justificacion=e.justificacion,
            fuentes=e.fuentes,
        )


class RadarResponse(BaseModel):
    candidato: Candidato
    cobertura: int
    concentracion_hhi: float
    presencia_historica: int
    computed_at: str
    ejes: list[EjeScoreDTO]

    @classmethod
    def from_domain(cls, card: Scorecard) -> RadarResponse:
        return cls(
            candidato=card.candidato,
            cobertura=card.cobertura,
            concentracion_hhi=card.concentracion_hhi,
            presencia_historica=card.presencia_historica,
            computed_at=card.computed_at,
            ejes=[EjeScoreDTO.from_domain(e) for e in card.ejes],
        )
