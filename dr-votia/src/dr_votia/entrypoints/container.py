"""Composition root — the ONLY place that knows every concrete adapter.

Wires settings + adapters into the use cases. The CLI and the future web layer
both call ``build_container`` (or ``build_readers`` for keyless work) instead of
constructing adapters themselves.
"""

from __future__ import annotations

from dataclasses import dataclass

from dr_votia.application.answer_question import AnswerQuestion
from dr_votia.application.guardrail import Guardrail
from dr_votia.application.ingest_documents import IngestDocuments
from dr_votia.application.rate_limit import RateLimitConfig, RateLimiter
from dr_votia.application.refine_query import QueryRefiner
from dr_votia.application.score_candidates import ScoreCandidates
from dr_votia.config import Settings
from dr_votia.domain.ports import DocumentReader, ScoreRepository, SessionStore
from dr_votia.infrastructure.embeddings.voyage import VoyageEmbeddings
from dr_votia.infrastructure.llm.openrouter import OpenRouterLLM
from dr_votia.infrastructure.readers.pdf import PdfReader
from dr_votia.infrastructure.readers.text import TextReader
from dr_votia.infrastructure.readers.xlsx import XlsxReader
from dr_votia.infrastructure.store.scores import SupabaseScoreStore
from dr_votia.infrastructure.store.sessions import SupabaseSessionStore
from dr_votia.infrastructure.store.supabase import SupabaseVectorStore


def build_readers() -> list[DocumentReader]:
    """Readers need no credentials — usable for dry runs."""
    return [PdfReader(), XlsxReader(), TextReader()]


@dataclass(frozen=True, slots=True)
class Container:
    settings: Settings
    readers: list[DocumentReader]
    ingest: IngestDocuments
    answer: AnswerQuestion
    score: ScoreCandidates
    score_repo: ScoreRepository
    sessions: SessionStore
    rate_limiter: RateLimiter


def build_container(settings: Settings | None = None) -> Container:
    settings = settings or Settings()  # type: ignore[call-arg]  # loaded from env/.env

    embeddings = VoyageEmbeddings(
        settings.voyage_api_key.get_secret_value(),
        model=settings.voyage_model,
        tokens_per_min=settings.voyage_tokens_per_min,
        requests_per_min=settings.voyage_requests_per_min,
    )
    store = SupabaseVectorStore(
        settings.supabase_url,
        settings.supabase_service_key.get_secret_value(),
        insert_batch=settings.insert_batch,
    )
    api_key = settings.openrouter_api_key.get_secret_value()
    answer_llm = OpenRouterLLM(
        api_key,
        model=settings.openrouter_answer_model,
        base_url=settings.openrouter_base_url,
        max_tokens=settings.openrouter_answer_max_tokens,
    )
    # Scoring runs on its own (quality) model — the rubric emits structured JSON,
    # so it stays independent of whatever cheaper model the chat uses.
    score_llm = OpenRouterLLM(
        api_key,
        model=settings.openrouter_score_model,
        base_url=settings.openrouter_base_url,
        max_tokens=settings.openrouter_score_max_tokens,
    )
    # Cheap model for RAG preprocessing; small output budget (it only emits JSON).
    query_llm = OpenRouterLLM(
        api_key,
        model=settings.openrouter_query_model,
        base_url=settings.openrouter_base_url,
        max_tokens=256,
    )
    refiner = QueryRefiner(query_llm)
    # Guardrail rides the same cheap model — its scope check is also light work.
    guardrail = Guardrail(query_llm)
    readers = build_readers()
    score_repo = SupabaseScoreStore(
        settings.supabase_url,
        settings.supabase_service_key.get_secret_value(),
    )
    sessions = SupabaseSessionStore(
        settings.supabase_url,
        settings.supabase_service_key.get_secret_value(),
    )
    rate_limiter = RateLimiter(
        sessions,
        RateLimitConfig(
            enabled=settings.rate_limit_enabled,
            per_ip=settings.rate_limit_per_ip,
            per_session=settings.rate_limit_per_session,
            window_seconds=settings.rate_limit_window_seconds,
        ),
    )

    return Container(
        settings=settings,
        readers=readers,
        ingest=IngestDocuments(readers, embeddings, store, chunk_overlap=settings.chunk_overlap),
        answer=AnswerQuestion(embeddings, store, answer_llm, refiner=refiner, guardrail=guardrail),
        # Scoring is an evaluative judgment on its own quality model, independent
        # of the (cheaper) chat answer model.
        score=ScoreCandidates(
            embeddings, store, score_llm, runs=settings.score_runs, k=settings.score_k
        ),
        score_repo=score_repo,
        sessions=sessions,
        rate_limiter=rate_limiter,
    )
