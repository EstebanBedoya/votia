"""ScoreCandidates tested with in-memory fakes — no Voyage, Supabase or LLM.

These prove the data-science behaviour: mean ± std aggregation over K runs, the
confidence heuristic, the deterministic absence short-circuit (no LLM spend),
clamping of out-of-range model output, and the corpus-level HHI / coverage.
"""

from __future__ import annotations

import json

from dr_votia.application.score_candidates import ScoreCandidates
from dr_votia.domain.models import (
    RADAR_EJES,
    Candidato,
    EjeMetrics,
    RetrievedChunk,
    Scorecard,
    Tema,
    Tipo,
)


class FakeEmbeddings:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [1.0]


class FakeStore:
    """count() answers from a per-axis proposal map; search() returns one chunk
    for proposals and nothing for the supporting context blocks."""

    def __init__(self, propuestas_por_eje: dict[Tema, int], *, historico: int = 0) -> None:
        self._propuestas = propuestas_por_eje
        self._historico = historico

    def count(self, *, candidato=None, tema=None, tipo=None) -> int:  # type: ignore[no-untyped-def]
        if tipo is Tipo.PROPUESTA:
            return self._propuestas.get(tema, 0)
        if tipo is Tipo.DATO_HISTORICO:
            return self._historico
        return 0

    def search(self, query_embedding, *, k=5, candidato=None, tema=None, tipo=None):  # type: ignore[no-untyped-def]
        if tipo is Tipo.PROPUESTA:
            return [
                RetrievedChunk(
                    id=1,
                    content="propuesta con meta a 2030",
                    tipo=Tipo.PROPUESTA,
                    fuente="fajardo_plan_gobierno_2026.pdf",
                    similarity=0.9,
                    candidato=Candidato.FAJARDO,
                    tema=tema,
                )
            ]
        return []


class FakeLLM:
    """Cycles through canned replies so we can simulate run-to-run variance."""

    def __init__(self, replies: list[str]) -> None:
        self._replies = replies
        self.calls = 0

    def generate(self, *, system: str, user: str) -> str:
        reply = self._replies[self.calls % len(self._replies)]
        self.calls += 1
        return reply


def _reply(**fields: object) -> str:
    return json.dumps(fields)


def _only(eje: Tema, volumen: int) -> dict[Tema, int]:
    return {eje: volumen}


def _find(card: Scorecard, eje: Tema) -> EjeMetrics:
    return next(e for e in card.ejes if e.eje is eje)


def test_aggregates_mean_std_and_confidence_over_runs() -> None:
    llm = FakeLLM(
        [
            _reply(solidez=5, densidad_evidencia=0.8, anclaje_nacional=4, justificacion="a"),
            _reply(solidez=3, densidad_evidencia=0.4, anclaje_nacional=2, justificacion="b"),
            _reply(solidez=4, densidad_evidencia=0.6, anclaje_nacional=3, justificacion="c"),
        ]
    )
    score = ScoreCandidates(FakeEmbeddings(), FakeStore(_only(Tema.SEGURIDAD, 5)), llm, runs=3)

    card = score(Candidato.FAJARDO)
    seg = _find(card, Tema.SEGURIDAD)

    assert seg.solidez == 4.0  # mean([5, 3, 4])
    assert seg.solidez_std == 0.82  # pstdev([5, 3, 4]) rounded
    assert seg.solidez_runs == [5, 3, 4]
    assert seg.densidad_evidencia == 0.6
    assert seg.anclaje_nacional == 3
    assert seg.confianza == 0.56  # 0.7*(1-0.82/2) + 0.3*min(5/10,1)
    # Only the one axis with proposals hit the LLM; the other five short-circuited.
    assert llm.calls == 3


def test_absence_is_a_confident_one_without_calling_the_llm() -> None:
    llm = FakeLLM(['{"solidez": 5}'])
    score = ScoreCandidates(FakeEmbeddings(), FakeStore({}), llm, runs=3)

    card = score(Candidato.ESPRIELLA)

    assert llm.calls == 0
    assert card.cobertura == 0
    for eje in RADAR_EJES:
        e = _find(card, eje)
        assert e.solidez == 1.0
        assert e.confianza == 1.0
        assert e.volumen_propuestas == 0


def test_unparseable_output_yields_zero_confidence() -> None:
    llm = FakeLLM(["no soy json"])
    score = ScoreCandidates(FakeEmbeddings(), FakeStore(_only(Tema.SALUD, 4)), llm, runs=3)

    salud = _find(score(Candidato.LOPEZ), Tema.SALUD)

    assert salud.solidez == 0.0
    assert salud.confianza == 0.0
    assert "No fue posible evaluar" in salud.justificacion


def test_coherencia_is_none_when_model_reports_no_track_record() -> None:
    llm = FakeLLM(['{"solidez": 4, "coherencia_gestion": null, "justificacion": "x"}'])
    score = ScoreCandidates(FakeEmbeddings(), FakeStore(_only(Tema.ECONOMIA, 2)), llm, runs=1)

    eco = _find(score(Candidato.CEPEDA), Tema.ECONOMIA)

    assert eco.coherencia_gestion is None


def test_clamps_out_of_range_model_output() -> None:
    llm = FakeLLM(
        [_reply(solidez=9, densidad_evidencia=1.7, anclaje_nacional=0, coherencia_gestion=8)]
    )
    score = ScoreCandidates(FakeEmbeddings(), FakeStore(_only(Tema.SEGURIDAD, 3)), llm, runs=1)

    seg = _find(score(Candidato.FAJARDO), Tema.SEGURIDAD)

    assert seg.solidez == 5.0
    assert seg.densidad_evidencia == 1.0
    assert seg.anclaje_nacional == 1
    assert seg.coherencia_gestion == 5


def test_coverage_and_hhi_reflect_agenda_shape() -> None:
    llm = FakeLLM(['{"solidez": 4, "justificacion": "x"}'])
    # Monothematic: everything in one axis -> HHI 1.0, coverage 1.
    mono = ScoreCandidates(FakeEmbeddings(), FakeStore(_only(Tema.SEGURIDAD, 10)), llm, runs=1)
    card = mono(Candidato.VALENCIA)
    assert card.cobertura == 1
    assert card.concentracion_hhi == 1.0

    # Balanced across all six axes -> HHI ~ 1/6, coverage 6.
    balanced_counts = dict.fromkeys(RADAR_EJES, 5)
    balanced = ScoreCandidates(FakeEmbeddings(), FakeStore(balanced_counts), llm, runs=1)
    card2 = balanced(Candidato.FAJARDO)
    assert card2.cobertura == 6
    assert card2.concentracion_hhi == 0.167


def test_presencia_historica_is_counted() -> None:
    llm = FakeLLM(['{"solidez": 3, "justificacion": "x"}'])
    store = FakeStore(_only(Tema.SEGURIDAD, 2), historico=7)
    card = ScoreCandidates(FakeEmbeddings(), store, llm, runs=1)(Candidato.LOPEZ)

    assert card.presencia_historica == 7
