"""Web endpoint tested with a fake container via dependency_overrides — no
network, no Supabase, no LLM. The route is a thin adapter; this proves it.

Sessions and rate limiting are exercised here with an in-memory SessionStore and
a real RateLimiter, so the wiring (cookie issuance, turn persistence, 429s,
bypass token) is covered without touching Postgres."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient
from pydantic import SecretStr

from dr_votia.application.rate_limit import RateLimitConfig, RateLimiter
from dr_votia.domain.conversation import Message, Role, Session
from dr_votia.domain.models import Answer, Candidato, Query, RetrievedChunk, Tipo
from dr_votia.entrypoints.web.app import create_app
from dr_votia.entrypoints.web.deps import get_container


class FakeAnswer:
    def __init__(self) -> None:
        self.last_query: Query | None = None
        self.last_history: list[Message] | None = None

    def __call__(self, query: Query, *, history: list[Message] | None = None) -> Answer:
        self.last_query = query
        self.last_history = history
        chunk = RetrievedChunk(
            id=1,
            content="Fajardo propone reforzar la fuerza pública.",
            tipo=Tipo.PROPUESTA,
            fuente="fajardo_plan_gobierno_2026.pdf",
            similarity=0.88,
            candidato=Candidato.FAJARDO,
        )
        return Answer(text="respuesta del Dr. votIA", sources=[chunk])


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: set[str] = set()
        self.turns: list[tuple[str, Message, str | None]] = []
        self.costs: dict[str, float] = {}

    def create(self) -> Session:
        sid = str(uuid.uuid4())
        self._sessions.add(sid)
        return Session(id=sid)

    def exists(self, session_id: str) -> bool:
        return session_id in self._sessions

    def append(self, session_id: str, message: Message, *, ip: str | None = None) -> None:
        self.turns.append((session_id, message, ip))

    def add_cost(self, session_id: str, cost_usd: float) -> float:
        self.costs[session_id] = self.costs.get(session_id, 0.0) + cost_usd
        return self.costs[session_id]

    def session_cost(self, session_id: str) -> float:
        return self.costs.get(session_id, 0.0)

    def history(self, session_id: str, *, limit: int = 10) -> list[Message]:
        msgs = [m for sid, m, _ in self.turns if sid == session_id]
        return msgs[-limit:]

    def recent_request_count(self, *, within_seconds, ip=None, session_id=None) -> int:
        return sum(
            1
            for sid, m, turn_ip in self.turns
            if m.role is Role.USER
            and (
                (ip is not None and turn_ip == ip) or (session_id is not None and sid == session_id)
            )
        )


class FakeContainer:
    def __init__(
        self,
        answer: FakeAnswer,
        *,
        config: RateLimitConfig | None = None,
        bypass_token: SecretStr | None = None,
    ) -> None:
        self.answer = answer
        self.sessions = InMemorySessionStore()
        self.rate_limiter = RateLimiter(self.sessions, config or RateLimitConfig(enabled=False))
        self.settings = SimpleNamespace(
            session_cookie_name="votia_session",
            rate_limit_bypass_token=bypass_token,
            session_history_limit=10,
            access_code=None,
            openrouter_answer_model="test/answer-model",
        )


def _client(answer: FakeAnswer, container: FakeContainer | None = None) -> TestClient:
    app = create_app()
    container = container or FakeContainer(answer)
    app.dependency_overrides[get_container] = lambda: container
    return TestClient(app)


def test_health() -> None:
    assert _client(FakeAnswer()).get("/health").json() == {"status": "ok"}


def test_chat_returns_answer_and_sources() -> None:
    client = _client(FakeAnswer())

    resp = client.post("/chat", json={"pregunta": "¿Qué propone Fajardo en seguridad?"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["respuesta"] == "respuesta del Dr. votIA"
    assert body["fuentes"][0]["candidato"] == "fajardo"
    assert body["fuentes"][0]["fuente"] == "fajardo_plan_gobierno_2026.pdf"


def test_chat_forwards_filters_to_use_case() -> None:
    answer = FakeAnswer()
    client = _client(answer)

    client.post("/chat", json={"pregunta": "x", "candidato": "lopez", "k": 3})

    assert answer.last_query is not None
    assert answer.last_query.candidato == Candidato.LOPEZ
    assert answer.last_query.k == 3


def test_chat_rejects_empty_question() -> None:
    assert _client(FakeAnswer()).post("/chat", json={"pregunta": ""}).status_code == 422


def test_chat_issues_session_cookie_and_persists_both_turns() -> None:
    container = FakeContainer(FakeAnswer())
    client = _client(FakeAnswer(), container)

    resp = client.post("/chat", json={"pregunta": "¿Qué propone López?"})

    assert resp.status_code == 200
    sid = resp.json()["session_id"]
    assert sid and resp.cookies.get("votia_session") == sid
    roles = [m.role for _, m, _ in container.sessions.turns]
    assert roles == [Role.USER, Role.ASSISTANT]  # both turns stored


def test_second_turn_passes_prior_history_to_the_use_case() -> None:
    container = FakeContainer(FakeAnswer())
    client = _client(FakeAnswer(), container)

    first = client.post("/chat", json={"pregunta": "¿Qué propone Fajardo en seguridad?"})
    sid = first.json()["session_id"]
    # Reuse the issued cookie so the second request lands on the same session.
    client.cookies.set("votia_session", sid)
    client.post("/chat", json={"pregunta": "¿y en educación?"})

    # The use case sees the prior turns, NOT the current question (read before append).
    assert container.answer.last_history is not None
    contents = [m.content for m in container.answer.last_history]
    assert "¿Qué propone Fajardo en seguridad?" in contents
    assert "¿y en educación?" not in contents


def test_rate_limit_blocks_after_session_threshold() -> None:
    container = FakeContainer(
        FakeAnswer(),
        config=RateLimitConfig(enabled=True, per_ip=100, per_session=2, window_seconds=60),
    )
    client = _client(FakeAnswer(), container)

    assert client.post("/chat", json={"pregunta": "uno"}).status_code == 200
    assert client.post("/chat", json={"pregunta": "dos"}).status_code == 200
    blocked = client.post("/chat", json={"pregunta": "tres"})
    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"] == "60"


def test_bypass_token_skips_rate_limit() -> None:
    container = FakeContainer(
        FakeAnswer(),
        config=RateLimitConfig(enabled=True, per_ip=1, per_session=1, window_seconds=60),
        bypass_token=SecretStr("s3cr3t"),
    )
    client = _client(FakeAnswer(), container)
    headers = {"X-Admin-Token": "s3cr3t"}

    # Well past both limits, but the admin token waves every request through.
    for _ in range(3):
        assert client.post("/chat", json={"pregunta": "x"}, headers=headers).status_code == 200
