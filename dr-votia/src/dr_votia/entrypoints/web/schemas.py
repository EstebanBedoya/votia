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

    @classmethod
    def from_answer(cls, answer: Answer) -> ChatResponse:
        return cls(
            respuesta=answer.text,
            fuentes=[SourceDTO.from_chunk(c) for c in answer.sources],
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
