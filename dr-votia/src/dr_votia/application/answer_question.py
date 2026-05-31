"""Use case: answer a question with retrieval-augmented generation.

Dual-model flow (see Docs/models.md):
    question
      → QueryRefiner (cheap model) rewrites for retrieval + classifies topic
      → embed refined text → VectorStore search
      → answer LLM (quality model) generates the grounded response

Depends only on ports and the QueryRefiner service — never on an SDK — so it is
unit-tested with fakes and reused unchanged by the CLI and the future web layer.
The refiner is optional: without it, the raw question is used directly.
"""

from __future__ import annotations

from dr_votia.application.guardrail import Guardrail
from dr_votia.application.prompts import (
    GUARD_REFUSAL,
    SYSTEM_PROMPT,
    build_context,
    build_user_message,
)
from dr_votia.application.refine_query import QueryRefiner
from dr_votia.domain.conversation import Message
from dr_votia.domain.models import Answer, Query, Tema
from dr_votia.domain.ports import EmbeddingProvider, LLMProvider, VectorStore


class AnswerQuestion:
    def __init__(
        self,
        embeddings: EmbeddingProvider,
        store: VectorStore,
        llm: LLMProvider,
        *,
        refiner: QueryRefiner | None = None,
        guardrail: Guardrail | None = None,
    ) -> None:
        self._embeddings = embeddings
        self._store = store
        self._llm = llm
        self._refiner = refiner
        self._guardrail = guardrail

    def __call__(self, query: Query, *, history: list[Message] | None = None) -> Answer:
        # Guardrail short-circuits BEFORE any embedding, retrieval, or the
        # expensive model: a rejected question costs at most one cheap call.
        # cost_usd accumulates every LLM call this turn made (guardrail + refiner
        # + answer) so the web layer can bill it to the session.
        cost = 0.0
        if self._guardrail is not None:
            verdict = self._guardrail.check(query.text)
            cost += verdict.usage.cost_usd or 0.0
            if not verdict.allowed:
                return Answer(text=GUARD_REFUSAL, sources=[], cost_usd=cost)

        search_text, classified_tema, refine_cost = self._refine(query, history)
        cost += refine_cost
        # An explicit caller filter wins; otherwise fall back to the classified one.
        tema = query.tema or classified_tema

        query_embedding = self._embeddings.embed_query(search_text)
        chunks = self._store.search(
            query_embedding,
            k=query.k,
            candidato=query.candidato,
            tema=tema,
            tipo=query.tipo,
        )
        context = build_context(chunks)
        result = self._llm.generate(
            system=SYSTEM_PROMPT,
            user=build_user_message(query.text, context),
        )
        cost += result.usage.cost_usd or 0.0
        return Answer(text=result.text, sources=chunks, cost_usd=round(cost, 6))

    def _refine(
        self, query: Query, history: list[Message] | None
    ) -> tuple[str, Tema | None, float]:
        if self._refiner is None:
            return query.text, None, 0.0
        refined = self._refiner(query.text, history)
        return refined.search_text, refined.tema, refined.usage.cost_usd or 0.0
