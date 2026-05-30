"""HTTP routes — a driving adapter. Translates request → domain Query, calls the
AnswerQuestion use case, translates Answer → response. No business logic here.

Endpoints are sync ``def``: the use case does blocking I/O (Voyage, OpenRouter),
so FastAPI runs them in a threadpool and the event loop stays free.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from dr_votia.domain.models import Candidato, Query
from dr_votia.entrypoints.container import Container
from dr_votia.entrypoints.web.deps import get_container
from dr_votia.entrypoints.web.schemas import (
    ChatRequest,
    ChatResponse,
    RadarResponse,
)

router = APIRouter()

ContainerDep = Annotated[Container, Depends(get_container)]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, container: ContainerDep) -> ChatResponse:
    answer = container.answer(
        Query(
            text=request.pregunta,
            k=request.k,
            candidato=request.candidato,
            tema=request.tema,
            tipo=request.tipo,
        )
    )
    return ChatResponse.from_answer(answer)


@router.get("/radar", response_model=list[RadarResponse])
def radar_all(container: ContainerDep) -> list[RadarResponse]:
    return [RadarResponse.from_domain(c) for c in container.score_repo.all()]


@router.get("/radar/{candidato}", response_model=RadarResponse)
def radar(candidato: Candidato, container: ContainerDep) -> RadarResponse:
    card = container.score_repo.get(candidato)
    if card is None:
        raise HTTPException(
            status_code=404,
            detail=f"Scorecard de '{candidato.value}' no calculado. Corré: dr-votia score",
        )
    return RadarResponse.from_domain(card)
