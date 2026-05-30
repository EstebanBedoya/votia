"""Supabase adapter for scorecards. Implements the ScoreRepository port.

One row per candidate in ``candidate_scores``, holding the whole scorecard as a
JSONB document. JSONB (rather than a wide column schema) keeps the metric set
free to evolve without migrations — we never query individual metrics in SQL,
we always read the full card for the radar. Requires the service_role key.
"""

from __future__ import annotations

from typing import Any, cast

from supabase import Client, create_client

from dr_votia.domain.models import (
    Candidato,
    EjeMetrics,
    Scorecard,
    Tema,
)

TABLE = "candidate_scores"


class SupabaseScoreStore:
    def __init__(self, url: str, service_key: str) -> None:
        self._client: Client = create_client(url, service_key)

    def save(self, scorecard: Scorecard) -> None:
        self._client.table(TABLE).upsert(
            {
                "candidato": scorecard.candidato.value,
                "scorecard": _dump(scorecard),
                "computed_at": scorecard.computed_at,
            },
            on_conflict="candidato",
        ).execute()

    def get(self, candidato: Candidato) -> Scorecard | None:
        response = (
            self._client.table(TABLE)
            .select("scorecard")
            .eq("candidato", candidato.value)
            .limit(1)
            .execute()
        )
        rows = cast("list[dict[str, Any]]", response.data or [])
        if not rows:
            return None
        return _load(rows[0]["scorecard"])

    def all(self) -> list[Scorecard]:
        response = self._client.table(TABLE).select("scorecard").execute()
        rows = cast("list[dict[str, Any]]", response.data or [])
        return [_load(row["scorecard"]) for row in rows]


def _dump(card: Scorecard) -> dict[str, Any]:
    return {
        "candidato": card.candidato.value,
        "cobertura": card.cobertura,
        "concentracion_hhi": card.concentracion_hhi,
        "presencia_historica": card.presencia_historica,
        "computed_at": card.computed_at,
        "ejes": [
            {
                "eje": e.eje.value,
                "volumen_propuestas": e.volumen_propuestas,
                "solidez": e.solidez,
                "solidez_std": e.solidez_std,
                "solidez_runs": e.solidez_runs,
                "confianza": e.confianza,
                "densidad_evidencia": e.densidad_evidencia,
                "anclaje_nacional": e.anclaje_nacional,
                "coherencia_gestion": e.coherencia_gestion,
                "justificacion": e.justificacion,
                "fuentes": e.fuentes,
            }
            for e in card.ejes
        ],
    }


def _load(data: dict[str, Any]) -> Scorecard:
    return Scorecard(
        candidato=Candidato(data["candidato"]),
        cobertura=data["cobertura"],
        concentracion_hhi=data["concentracion_hhi"],
        presencia_historica=data["presencia_historica"],
        computed_at=data["computed_at"],
        ejes=[
            EjeMetrics(
                eje=Tema(e["eje"]),
                volumen_propuestas=e["volumen_propuestas"],
                solidez=e["solidez"],
                solidez_std=e["solidez_std"],
                solidez_runs=list(e["solidez_runs"]),
                confianza=e["confianza"],
                densidad_evidencia=e["densidad_evidencia"],
                anclaje_nacional=e["anclaje_nacional"],
                coherencia_gestion=e["coherencia_gestion"],
                justificacion=e["justificacion"],
                fuentes=list(e["fuentes"]),
            )
            for e in data["ejes"]
        ],
    )
