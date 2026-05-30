"""Web endpoint tested with a fake container via dependency_overrides — no
network, no Supabase, no LLM. The route is a thin adapter; this proves it."""

from __future__ import annotations

from fastapi.testclient import TestClient

from dr_votia.domain.models import Answer, Candidato, Query, RetrievedChunk, Tipo
from dr_votia.entrypoints.web.app import create_app
from dr_votia.entrypoints.web.deps import get_container


class FakeAnswer:
    def __init__(self) -> None:
        self.last_query: Query | None = None

    def __call__(self, query: Query) -> Answer:
        self.last_query = query
        chunk = RetrievedChunk(
            id=1,
            content="Fajardo propone reforzar la fuerza pública.",
            tipo=Tipo.PROPUESTA,
            fuente="fajardo_plan_gobierno_2026.pdf",
            similarity=0.88,
            candidato=Candidato.FAJARDO,
        )
        return Answer(text="respuesta del Dr. votIA", sources=[chunk])


class FakeContainer:
    def __init__(self, answer: FakeAnswer) -> None:
        self.answer = answer


def _client(answer: FakeAnswer) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_container] = lambda: FakeContainer(answer)
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
