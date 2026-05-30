"""AnswerQuestion wired with a refiner: the refined text drives retrieval and
the classified topic becomes the filter when the caller gave none."""

from __future__ import annotations

from dr_votia.application.answer_question import AnswerQuestion
from dr_votia.domain.models import Candidato, Query, RefinedQuery, Tema


class RecordingEmbeddings:
    def __init__(self) -> None:
        self.last_query_text = ""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        self.last_query_text = text
        return [1.0]


class RecordingStore:
    def __init__(self) -> None:
        self.last_call: dict[str, object] = {}

    def add(self, chunks: list[object]) -> int:
        return len(chunks)

    def search(self, query_embedding, *, k=5, candidato=None, tema=None, tipo=None):
        self.last_call = {"k": k, "candidato": candidato, "tema": tema, "tipo": tipo}
        return []


class StubLLM:
    def generate(self, *, system: str, user: str) -> str:
        return "respuesta"


class StubRefiner:
    def __init__(self, refined: RefinedQuery) -> None:
        self._refined = refined

    def __call__(self, question: str) -> RefinedQuery:
        return self._refined


def test_refined_text_is_what_gets_embedded() -> None:
    embeddings = RecordingEmbeddings()
    refiner = StubRefiner(RefinedQuery(search_text="consulta reformulada", tema=Tema.SEGURIDAD))
    use_case = AnswerQuestion(embeddings, RecordingStore(), StubLLM(), refiner=refiner)  # type: ignore[arg-type]

    use_case(Query(text="pregunta cruda"))

    assert embeddings.last_query_text == "consulta reformulada"


def test_classified_tema_fills_in_when_caller_gave_none() -> None:
    store = RecordingStore()
    refiner = StubRefiner(RefinedQuery(search_text="x", tema=Tema.SEGURIDAD))
    use_case = AnswerQuestion(RecordingEmbeddings(), store, StubLLM(), refiner=refiner)  # type: ignore[arg-type]

    use_case(Query(text="x"))

    assert store.last_call["tema"] == Tema.SEGURIDAD


def test_explicit_caller_tema_overrides_classification() -> None:
    store = RecordingStore()
    refiner = StubRefiner(RefinedQuery(search_text="x", tema=Tema.SEGURIDAD))
    use_case = AnswerQuestion(RecordingEmbeddings(), store, StubLLM(), refiner=refiner)  # type: ignore[arg-type]

    use_case(Query(text="x", tema=Tema.ECONOMIA, candidato=Candidato.LOPEZ))

    assert store.last_call["tema"] == Tema.ECONOMIA
    assert store.last_call["candidato"] == Candidato.LOPEZ
