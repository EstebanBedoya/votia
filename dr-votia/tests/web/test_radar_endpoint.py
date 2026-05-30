"""The /radar endpoints tested with a fake repository — no Supabase, no LLM."""

from __future__ import annotations

from fastapi.testclient import TestClient

from dr_votia.domain.models import Candidato, EjeMetrics, Scorecard, Tema
from dr_votia.entrypoints.web.app import create_app
from dr_votia.entrypoints.web.deps import get_container


def _scorecard(candidato: Candidato) -> Scorecard:
    return Scorecard(
        candidato=candidato,
        cobertura=1,
        concentracion_hhi=1.0,
        presencia_historica=3,
        computed_at="2026-05-30T00:00:00+00:00",
        ejes=[
            EjeMetrics(
                eje=Tema.SEGURIDAD,
                volumen_propuestas=5,
                solidez=4.0,
                solidez_std=0.82,
                solidez_runs=[5, 3, 4],
                confianza=0.56,
                densidad_evidencia=0.6,
                anclaje_nacional=3,
                coherencia_gestion=None,
                justificacion="Propone metas medibles.",
                fuentes=["fajardo_plan_gobierno_2026.pdf"],
            )
        ],
    )


class FakeRepo:
    def __init__(self, card: Scorecard | None) -> None:
        self._card = card

    def save(self, scorecard: Scorecard) -> None:  # pragma: no cover - unused here
        self._card = scorecard

    def get(self, candidato: Candidato) -> Scorecard | None:
        if self._card is not None and self._card.candidato == candidato:
            return self._card
        return None

    def all(self) -> list[Scorecard]:
        return [self._card] if self._card is not None else []


class FakeContainer:
    def __init__(self, repo: FakeRepo) -> None:
        self.score_repo = repo


def _client(repo: FakeRepo) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_container] = lambda: FakeContainer(repo)
    return TestClient(app)


def test_radar_returns_scorecard() -> None:
    client = _client(FakeRepo(_scorecard(Candidato.FAJARDO)))

    resp = client.get("/radar/fajardo")

    assert resp.status_code == 200
    body = resp.json()
    assert body["candidato"] == "fajardo"
    assert body["ejes"][0]["eje"] == "seguridad"
    assert body["ejes"][0]["solidez"] == 4.0
    assert body["ejes"][0]["solidez_std"] == 0.82


def test_radar_404_when_not_computed() -> None:
    client = _client(FakeRepo(_scorecard(Candidato.FAJARDO)))

    assert client.get("/radar/lopez").status_code == 404


def test_radar_rejects_unknown_candidate() -> None:
    assert _client(FakeRepo(None)).get("/radar/pedro").status_code == 422


def test_radar_all_lists_cards() -> None:
    client = _client(FakeRepo(_scorecard(Candidato.FAJARDO)))

    resp = client.get("/radar")

    assert resp.status_code == 200
    assert [c["candidato"] for c in resp.json()] == ["fajardo"]
