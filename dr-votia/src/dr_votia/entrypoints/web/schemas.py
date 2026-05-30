"""HTTP DTOs for the web layer. These translate between the JSON API and the
domain models — the domain never depends on them."""

from __future__ import annotations

from pydantic import BaseModel, Field

from dr_votia.domain.models import Answer, Candidato, RetrievedChunk, Tema, Tipo


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
