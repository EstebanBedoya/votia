"""The hexagonal payoff: the RAG use case tested with in-memory fakes.

No Voyage, no Supabase, no Claude, no network. If this is hard to write, the
domain is leaking infrastructure — it isn't.
"""

from __future__ import annotations

from dr_votia.application.answer_question import AnswerQuestion
from dr_votia.domain.models import Candidato, LLMResult, Query, RetrievedChunk, Tipo


class FakeEmbeddings:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0, 0.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [1.0, 0.0, 0.0, 0.0]


class FakeStore:
    def __init__(self, results: list[RetrievedChunk]) -> None:
        self._results = results
        self.last_call: dict[str, object] = {}

    def add(self, chunks: list[object]) -> int:
        return len(chunks)

    def search(self, query_embedding, *, k=5, candidato=None, tema=None, tipo=None):
        self.last_call = {"k": k, "candidato": candidato, "tema": tema, "tipo": tipo}
        return self._results


class FakeLLM:
    def __init__(self) -> None:
        self.system = ""
        self.user = ""

    def generate(self, *, system: str, user: str) -> LLMResult:
        self.system = system
        self.user = user
        return LLMResult(text="respuesta generada")


def _sample_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        id=1,
        content="Fajardo propone fortalecer la fuerza pública.",
        tipo=Tipo.PROPUESTA,
        fuente="fajardo_plan_gobierno_2026.pdf",
        similarity=0.91,
        candidato=Candidato.FAJARDO,
    )


def test_answer_returns_llm_text_and_sources() -> None:
    chunk = _sample_chunk()
    llm = FakeLLM()
    use_case = AnswerQuestion(FakeEmbeddings(), FakeStore([chunk]), llm)

    answer = use_case(Query(text="¿Qué propone Fajardo en seguridad?"))

    assert answer.text == "respuesta generada"
    assert answer.sources == [chunk]
    # The retrieved content must reach the prompt — that's the whole point of RAG.
    assert chunk.content in llm.user


def test_answer_forwards_filters_to_store() -> None:
    store = FakeStore([])
    use_case = AnswerQuestion(FakeEmbeddings(), store, FakeLLM())

    use_case(Query(text="x", k=3, candidato=Candidato.LOPEZ))

    assert store.last_call == {
        "k": 3,
        "candidato": Candidato.LOPEZ,
        "tema": None,
        "tipo": None,
    }
