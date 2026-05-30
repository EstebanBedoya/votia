from __future__ import annotations

from dr_votia.domain.models import Tema
from dr_votia.domain.topic_inference import infer_tema


def test_security_keywords_win() -> None:
    assert infer_tema("El plan reduce el homicidio y refuerza la fuerza pública") == Tema.SEGURIDAD


def test_economy_keywords_win() -> None:
    assert infer_tema("Reducir el desempleo y la pobreza con más empleo") == Tema.ECONOMIA


def test_no_keywords_falls_back_to_general() -> None:
    assert infer_tema("Texto sin términos temáticos reconocibles aquí") == Tema.GENERAL
