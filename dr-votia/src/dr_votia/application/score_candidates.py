"""Use case: score a candidate across the six radar axes.

This is the data-scientist core. For each axis it gathers three evidence sets
(the candidate's proposals, the national reality, the candidate's prior
management), asks the evaluator LLM to grade them, and — crucially — repeats the
grading K times to measure how *stable* the judgment is. A 4 ± 0.0 is a finding;
a 3 ± 1.4 is the model telling us the evidence is ambiguous.

Three tiers, each with a different epistemic weight:
  - deterministic — proposal counts straight from the store (not opinions).
  - semantic — solidez / densidad_evidencia / anclaje / coherencia from the LLM.
  - reliability — mean ± std over K runs, plus a confidence heuristic.

Depends only on ports, so it is unit-tested with fakes — no network.
"""

from __future__ import annotations

import json
import re
import statistics
from dataclasses import dataclass
from datetime import UTC, datetime

from dr_votia.application.prompts import SCORE_SYSTEM, build_score_user_message
from dr_votia.domain.models import (
    RADAR_EJES,
    Candidato,
    EjeMetrics,
    RetrievedChunk,
    Scorecard,
    Tema,
    Tipo,
)
from dr_votia.domain.ports import EmbeddingProvider, LLMProvider, VectorStore

# Per-axis seed queries used to retrieve the relevant proposals/data. Kept here
# (retrieval tuning) rather than in the domain, which stays free of such hints.
EJE_SEED_QUERIES: dict[Tema, str] = {
    Tema.SEGURIDAD: "seguridad orden público homicidios violencia política criminal",
    Tema.ECONOMIA: "economía empleo crecimiento política fiscal impuestos inversión",
    Tema.SALUD: "salud sistema de aseguramiento EPS cobertura sanitaria",
    Tema.EDUCACION: "educación cobertura calidad deserción ciencia tecnología",
    Tema.ANTICORRUPCION: "anticorrupción transparencia contratación pública control fiscal",
    Tema.MEDIOAMBIENTE: "medio ambiente transición energética cambio climático extractivismo",
}

_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)
_CONTEXT_K = 3  # national + historical chunks pulled in as supporting evidence


@dataclass(frozen=True, slots=True)
class _ScoreRun:
    """One parsed LLM verdict. Aggregated across K runs into an EjeMetrics."""

    solidez: int
    densidad_evidencia: float
    anclaje_nacional: int
    coherencia_gestion: int | None
    justificacion: str


class ScoreCandidates:
    def __init__(
        self,
        embeddings: EmbeddingProvider,
        store: VectorStore,
        llm: LLMProvider,
        *,
        runs: int = 3,
        k: int = 8,
    ) -> None:
        self._embeddings = embeddings
        self._store = store
        self._llm = llm
        self._runs = max(1, runs)
        self._k = k

    def __call__(self, candidato: Candidato) -> Scorecard:
        ejes = [self._score_eje(candidato, eje) for eje in RADAR_EJES]
        cobertura = sum(1 for e in ejes if e.volumen_propuestas > 0)
        hhi = _herfindahl([e.volumen_propuestas for e in ejes])
        presencia = self._store.count(candidato=candidato, tipo=Tipo.DATO_HISTORICO)
        return Scorecard(
            candidato=candidato,
            ejes=ejes,
            cobertura=cobertura,
            concentracion_hhi=hhi,
            presencia_historica=presencia,
            computed_at=datetime.now(UTC).isoformat(),
        )

    def _score_eje(self, candidato: Candidato, eje: Tema) -> EjeMetrics:
        volumen = self._store.count(candidato=candidato, tema=eje, tipo=Tipo.PROPUESTA)

        # Absence is deterministic — we KNOW there are zero proposals. Score it a
        # confident 1 (the scale's "ausencia total") without spending LLM calls.
        if volumen == 0:
            return EjeMetrics(
                eje=eje,
                volumen_propuestas=0,
                solidez=1.0,
                solidez_std=0.0,
                solidez_runs=[],
                confianza=1.0,
                densidad_evidencia=0.0,
                anclaje_nacional=1,
                coherencia_gestion=None,
                justificacion="Ausencia total de propuesta en el eje: 0 propuestas indexadas.",
                fuentes=[],
            )

        embedding = self._embeddings.embed_query(EJE_SEED_QUERIES[eje])
        propuestas = self._store.search(
            embedding, k=self._k, candidato=candidato, tema=eje, tipo=Tipo.PROPUESTA
        )
        nacional = self._store.search(
            embedding,
            k=_CONTEXT_K,
            candidato=Candidato.NACIONAL,
            tema=eje,
            tipo=Tipo.ESTADISTICA_NACIONAL,
        )
        historico = self._store.search(
            embedding, k=_CONTEXT_K, candidato=candidato, tema=eje, tipo=Tipo.DATO_HISTORICO
        )

        user = build_score_user_message(
            candidato=candidato.value,
            eje=eje.value,
            propuestas=propuestas,
            nacional=nacional,
            historico=historico,
        )
        runs = [
            run
            for _ in range(self._runs)
            if (run := _parse_run(self._llm.generate(system=SCORE_SYSTEM, user=user))) is not None
        ]
        fuentes = _unique_fuentes([*propuestas, *historico])
        return _aggregate(eje, volumen, runs, fuentes)


def _aggregate(eje: Tema, volumen: int, runs: list[_ScoreRun], fuentes: list[str]) -> EjeMetrics:
    if not runs:
        # Every run was unparseable — report it honestly with zero confidence.
        return EjeMetrics(
            eje=eje,
            volumen_propuestas=volumen,
            solidez=0.0,
            solidez_std=0.0,
            solidez_runs=[],
            confianza=0.0,
            densidad_evidencia=0.0,
            anclaje_nacional=1,
            coherencia_gestion=None,
            justificacion="No fue posible evaluar: el modelo no devolvió un veredicto válido.",
            fuentes=fuentes,
        )

    solideces = [r.solidez for r in runs]
    mean = round(statistics.fmean(solideces), 2)
    std = round(statistics.pstdev(solideces), 2) if len(solideces) > 1 else 0.0
    coherencias = [r.coherencia_gestion for r in runs if r.coherencia_gestion is not None]
    # The justification from the run closest to the mean is the most representative.
    representative = min(runs, key=lambda r: abs(r.solidez - mean))
    return EjeMetrics(
        eje=eje,
        volumen_propuestas=volumen,
        solidez=mean,
        solidez_std=std,
        solidez_runs=solideces,
        confianza=_confidence(std, volumen),
        densidad_evidencia=round(statistics.fmean([r.densidad_evidencia for r in runs]), 2),
        anclaje_nacional=round(statistics.fmean([r.anclaje_nacional for r in runs])),
        coherencia_gestion=round(statistics.fmean(coherencias)) if coherencias else None,
        justificacion=representative.justificacion,
        fuentes=fuentes,
    )


def _confidence(std: float, volumen: int) -> float:
    """How much to trust the solidez mean. Two factors, weighted 70/30:

    - stability: a low std across runs means the model is sure (std 0 → 1.0;
      std ≥ 2 on a 1–5 scale → 0.0).
    - evidence: more indexed proposals = more to judge on (caps at 10).
    """
    stability = max(0.0, 1.0 - std / 2.0)
    evidence = min(volumen / 10.0, 1.0)
    return round(0.7 * stability + 0.3 * evidence, 2)


def _herfindahl(volumes: list[int]) -> float:
    """Herfindahl–Hirschman index over proposal volume per axis. ~1/6 means a
    balanced agenda across the six axes; 1.0 means everything in one axis."""
    total = sum(volumes)
    if total == 0:
        return 0.0
    return round(sum((v / total) ** 2 for v in volumes), 3)


def _unique_fuentes(chunks: list[RetrievedChunk]) -> list[str]:
    seen: dict[str, None] = {}
    for c in chunks:
        seen.setdefault(c.fuente, None)
    return list(seen)


def _parse_run(raw: str) -> _ScoreRun | None:
    match = _JSON_OBJECT.search(raw)
    if match is None:
        return None
    try:
        data = json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None

    solidez = _clamp_int(data.get("solidez"), low=1, high=5)
    if solidez is None:
        return None  # no usable score → drop this run
    return _ScoreRun(
        solidez=solidez,
        densidad_evidencia=_clamp_float(data.get("densidad_evidencia"), low=0.0, high=1.0),
        anclaje_nacional=_clamp_int(data.get("anclaje_nacional"), low=1, high=5) or 1,
        coherencia_gestion=_clamp_int(data.get("coherencia_gestion"), low=1, high=5),
        justificacion=str(data.get("justificacion") or "").strip(),
    )


def _clamp_int(value: object, *, low: int, high: int) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return max(low, min(high, round(value)))


def _clamp_float(value: object, *, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return max(low, min(high, float(value)))
