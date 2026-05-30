"""QueryRefiner tested with a fake LLM — no network, no DeepSeek."""

from __future__ import annotations

from dr_votia.application.refine_query import QueryRefiner
from dr_votia.domain.models import Tema


class StubLLM:
    def __init__(self, reply: str) -> None:
        self._reply = reply

    def generate(self, *, system: str, user: str) -> str:
        return self._reply


def test_parses_clean_json() -> None:
    llm = StubLLM('{"search_text": "tasa de homicidios seguridad", "tema": "seguridad"}')
    refined = QueryRefiner(llm)("homicidios?")

    assert refined.search_text == "tasa de homicidios seguridad"
    assert refined.tema == Tema.SEGURIDAD


def test_extracts_json_wrapped_in_prose() -> None:
    llm = StubLLM('Claro:\n{"search_text": "pobreza monetaria", "tema": "economia"}\nListo.')
    refined = QueryRefiner(llm)("pobreza?")

    assert refined.search_text == "pobreza monetaria"
    assert refined.tema == Tema.ECONOMIA


def test_unknown_tema_becomes_none() -> None:
    llm = StubLLM('{"search_text": "algo", "tema": "deportes"}')
    assert QueryRefiner(llm)("x").tema is None


def test_garbage_falls_back_to_original_question() -> None:
    refined = QueryRefiner(StubLLM("no soy json"))("¿pregunta original?")

    assert refined.search_text == "¿pregunta original?"
    assert refined.tema is None
