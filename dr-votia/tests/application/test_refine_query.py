"""QueryRefiner tested with a fake LLM — no network, no DeepSeek."""

from __future__ import annotations

from dr_votia.application.refine_query import QueryRefiner
from dr_votia.domain.conversation import Message, Role
from dr_votia.domain.models import Tema


class StubLLM:
    def __init__(self, reply: str) -> None:
        self._reply = reply
        self.last_user = ""

    def generate(self, *, system: str, user: str) -> str:
        self.last_user = user
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


def test_history_is_fed_to_the_model_for_follow_ups() -> None:
    llm = StubLLM('{"search_text": "x", "tema": null}')
    history = [
        Message(role=Role.USER, content="¿Qué propone Fajardo en seguridad?"),
        Message(role=Role.ASSISTANT, content="Propone reforzar la fuerza pública."),
    ]
    QueryRefiner(llm)("¿y en educación?", history)

    # The prior turns reach the model so it can rewrite the elliptical follow-up.
    assert "Fajardo" in llm.last_user
    assert "¿y en educación?" in llm.last_user


def test_no_history_sends_only_the_bare_question() -> None:
    llm = StubLLM('{"search_text": "x", "tema": null}')
    QueryRefiner(llm)("¿pregunta suelta?")

    assert llm.last_user == "¿pregunta suelta?"
