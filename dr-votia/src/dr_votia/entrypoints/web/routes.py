"""HTTP routes — a driving adapter. Translates request → domain Query, calls the
AnswerQuestion use case, translates Answer → response. No business logic here.

Endpoints are sync ``def``: the use case does blocking I/O (Voyage, OpenRouter),
so FastAPI runs them in a threadpool and the event loop stays free.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from dr_votia.domain.conversation import Message, Role
from dr_votia.domain.models import Candidato, Query
from dr_votia.entrypoints.web.deps import (
    ContainerDep,
    RateLimitDep,
    SessionDep,
    client_ip,
    require_access_code,
)
from dr_votia.entrypoints.web.schemas import (
    ChatRequest,
    ChatResponse,
    ConfigResponse,
    KeyResponse,
    RadarResponse,
    SessionUsageResponse,
    UsageResponse,
)

# Public — no gate (liveness probe, uptime monitors).
public_router = APIRouter()

# Protected — require a valid X-Access-Code header on every request.
router = APIRouter(dependencies=[Depends(require_access_code)])


@public_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/auth")
def auth() -> dict[str, bool]:
    """Validate the access code without spending any LLM tokens.

    The router-level dependency already enforced the check; returning here
    means it passed.
    """
    return {"ok": True}


@router.get("/usage", response_model=UsageResponse)
def usage(container: ContainerDep) -> UsageResponse:
    """OpenRouter account credit usage (lifetime). Kept for backward compat."""
    return UsageResponse(**container.billing.credits())


@router.get("/key", response_model=KeyResponse)
def key(container: ContainerDep) -> KeyResponse:
    """OpenRouter key spending limit + burned, for the 'ENERGÍA' gauge."""
    return KeyResponse(**container.billing.key())


@router.get("/config", response_model=ConfigResponse)
def config(container: ContainerDep) -> ConfigResponse:
    """Which models the system runs on — shown in the character panel."""
    settings = container.settings
    return ConfigResponse(
        answer_model=settings.openrouter_answer_model,
        score_model=settings.openrouter_score_model,
        query_model=settings.openrouter_query_model,
    )


@router.get("/session/usage", response_model=SessionUsageResponse)
def session_usage(container: ContainerDep, session_id: SessionDep) -> SessionUsageResponse:
    """Accumulated OpenRouter spend for the current session."""
    return SessionUsageResponse(
        session_id=session_id,
        cost_usd=container.sessions.session_cost(session_id),
    )


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
    # Bill this turn's OpenRouter spend to the session and read back the new total.
    session_cost = container.sessions.add_cost(session_id, answer.cost_usd)
    return ChatResponse.from_answer(
        answer,
        session_id=session_id,
        model=container.settings.openrouter_answer_model,
        session_cost_usd=session_cost,
    )


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
