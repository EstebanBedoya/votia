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

from dr_votia.application.prompts import (
    SYSTEM_PROMPT,
    build_context,
    build_user_message,
)
from dr_votia.application.refine_query import QueryRefiner
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
    ) -> None:
        self._embeddings = embeddings
        self._store = store
        self._llm = llm
        self._refiner = refiner

    def __call__(self, query: Query) -> Answer:
        search_text, classified_tema = self._refine(query)
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
        text = self._llm.generate(
            system=SYSTEM_PROMPT,
            user=build_user_message(query.text, context),
        )
        return Answer(text=text, sources=chunks)

    def _refine(self, query: Query) -> tuple[str, Tema | None]:
        if self._refiner is None:
            return query.text, None
        refined = self._refiner(query.text)
        return refined.search_text, refined.tema
