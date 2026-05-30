"""Keyword-based topic inference — pure, deterministic, unit-testable.

A lightweight heuristic to tag a chunk with a :class:`Tema` when the source does
not declare one. Not a classifier; just a transparent, debuggable baseline.
"""

from __future__ import annotations

from dr_votia.domain.models import Tema

TEMA_KEYWORDS: dict[Tema, tuple[str, ...]] = {
    Tema.SEGURIDAD: (
        "seguridad",
        "homicidio",
        "crimen",
        "policía",
        "fuerza pública",
        "masacre",
        "líder",
        "extorsión",
        "narcotráfico",
        "coca",
        "eln",
        "farc",
        "disidencias",
        "orden público",
        "delito",
    ),
    Tema.ECONOMIA: (
        "economía",
        "empleo",
        "desempleo",
        "pib",
        "fiscal",
        "impuesto",
        "tributari",
        "deuda",
        "inversión",
        "crecimiento",
        "inflación",
        "pobreza",
        "empresa",
        "pyme",
        "trabajo",
        "salario",
    ),
    Tema.SALUD: (
        "salud",
        "eps",
        "hospital",
        "médico",
        "enfermedad",
        "covid",
        "afiliación",
        "minsalud",
        "cobertura",
        "paciente",
        "clínica",
    ),
    Tema.EDUCACION: (
        "educación",
        "escuela",
        "colegio",
        "universidad",
        "matrícula",
        "deserción",
        "docente",
        "maestro",
        "ciencia",
        "tecnología",
        "investigación",
        "cti",
        "mineduc",
    ),
    Tema.ANTICORRUPCION: (
        "corrupción",
        "transparencia",
        "contratación",
        "fiscal",
        "procuraduría",
        "anticorrupción",
        "soborno",
        "peculado",
        "contraloría",
        "rendición de cuentas",
    ),
    Tema.MEDIOAMBIENTE: (
        "ambiente",
        "clima",
        "carbono",
        "energía",
        "petróleo",
        "transición",
        "deforestación",
        "biodiversidad",
        "agua",
        "renovable",
        "solar",
        "eólica",
        "extractiv",
    ),
}


def infer_tema(text: str) -> Tema:
    """Return the best-matching :class:`Tema`, or ``Tema.GENERAL`` if none match."""
    lowered = text.lower()
    scores = {
        tema: sum(1 for kw in keywords if kw in lowered) for tema, keywords in TEMA_KEYWORDS.items()
    }
    best = max(scores, key=lambda t: scores[t])
    return best if scores[best] > 0 else Tema.GENERAL
