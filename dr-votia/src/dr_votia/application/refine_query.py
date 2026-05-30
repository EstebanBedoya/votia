"""Query preprocessing — the cheap half of the dual-model architecture.

Uses an inexpensive LLM (DeepSeek V4 Flash) to rewrite the user question for
better semantic retrieval and to classify its topic, before pgvector search.
Depends only on the :class:`LLMProvider` port, so it is fed whichever model the
container wires in — and tested with a fake.

Failures are non-fatal: if the model returns unparseable output, we fall back to
the original question with no topic. Retrieval still works.
"""

from __future__ import annotations

import json
import re

from dr_votia.application.prompts import REFINE_SYSTEM, build_refine_user_message
from dr_votia.domain.conversation import Message
from dr_votia.domain.models import RefinedQuery, Tema
from dr_votia.domain.ports import LLMProvider

_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


class QueryRefiner:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    def __call__(self, question: str, history: list[Message] | None = None) -> RefinedQuery:
        raw = self._llm.generate(
            system=REFINE_SYSTEM, user=build_refine_user_message(question, history)
        )
        return _parse(raw, fallback=question)


def _parse(raw: str, *, fallback: str) -> RefinedQuery:
    match = _JSON_OBJECT.search(raw)
    if match is None:
        return RefinedQuery(search_text=fallback)
    try:
        data = json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return RefinedQuery(search_text=fallback)
    if not isinstance(data, dict):
        return RefinedQuery(search_text=fallback)

    search_text = str(data.get("search_text") or "").strip() or fallback
    return RefinedQuery(search_text=search_text, tema=_coerce_tema(data.get("tema")))


def _coerce_tema(value: object) -> Tema | None:
    if not isinstance(value, str):
        return None
    try:
        tema = Tema(value.strip().lower())
    except ValueError:
        return None
    # GENERAL is not a useful retrieval filter — treat it as "no topic".
    return None if tema is Tema.GENERAL else tema
