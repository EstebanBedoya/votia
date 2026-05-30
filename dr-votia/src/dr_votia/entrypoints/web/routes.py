"""HTTP routes — a driving adapter. Translates request → domain Query, calls the
AnswerQuestion use case, translates Answer → response. No business logic here.

Endpoints are sync ``def``: the use case does blocking I/O (Voyage, OpenRouter),
so FastAPI runs them in a threadpool and the event loop stays free.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from dr_votia.domain.conversation import Message, Role
from dr_votia.domain.models import Candidato, Query
from dr_votia.entrypoints.web.deps import (
    ContainerDep,
    RateLimitDep,
    SessionDep,
    client_ip,
)
from dr_votia.entrypoints.web.schemas import (
    ChatRequest,
    ChatResponse,
    RadarResponse,
)

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    container: ContainerDep,
    http: Request,
    session_id: SessionDep,
    _rate_limit: RateLimitDep,
) -> ChatResponse:
    # Read prior turns BEFORE persisting the current one, so the question does
    # not appear in its own history. The refiner uses these to resolve follow-ups
    # ("¿y en educación?") into a standalone search query.
    history = container.sessions.history(session_id, limit=container.settings.session_history_limit)
    # Persist the user turn: it is what the rate limiter counts on the NEXT request.
    container.sessions.append(
        session_id, Message(role=Role.USER, content=request.pregunta), ip=client_ip(http)
    )
    answer = container.answer(
        Query(
            text=request.pregunta,
            k=request.k,
            candidato=request.candidato,
            tema=request.tema,
            tipo=request.tipo,
        ),
        history=history,
    )
    container.sessions.append(session_id, Message(role=Role.ASSISTANT, content=answer.text))
    return ChatResponse.from_answer(answer, session_id=session_id)


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
