"""Application settings, loaded from environment / .env.

The only place secrets enter the process. Adapters receive plain values from
here; the domain and application layers never read the environment.
"""

from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Supabase (service_role — RLS is enabled)
    supabase_url: str
    supabase_service_key: SecretStr

    # Voyage AI — defaults are the free-tier rate limits (no payment method).
    # Raise these once a payment method unlocks Voyage's standard limits.
    voyage_api_key: SecretStr
    voyage_model: str = "voyage-3.5"
    embedding_dim: int = 1024
    voyage_tokens_per_min: int = 10_000
    voyage_requests_per_min: int = 3

    # OpenRouter (OpenAI-compatible gateway). Three-model setup so each task runs
    # on the cheapest model that still does it well:
    #   answer model — chat response (good value: e.g. google/gemini-2.5-flash)
    #   score model  — radar scorecards; emits structured JSON, so keep it on a
    #                  quality model (Sonnet/Haiku) independent of the chat model
    #   query model  — cheap RAG preprocessing (reformulation + topic classification)
    openrouter_api_key: SecretStr
    openrouter_answer_model: str = "anthropic/claude-sonnet-4.6"
    openrouter_score_model: str = "anthropic/claude-sonnet-4.6"
    openrouter_query_model: str = "deepseek/deepseek-v4-flash"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Output budgets. Chat answers run long (comparisons + justification), so give
    # them room; scoring emits a compact JSON rubric per axis.
    openrouter_answer_max_tokens: int = 1536
    openrouter_score_max_tokens: int = 2048

    # Pipeline knobs
    chunk_size: int = 800
    chunk_overlap: int = 150
    insert_batch: int = 50

    # Scoring (radar). score_runs = how many times each axis is graded to measure
    # judgment stability (mean ± std); score_k = proposals retrieved per axis.
    score_runs: int = 3
    score_k: int = 8

    # Sessions & rate limiting. Set rate_limit_enabled=false to turn limiting off
    # entirely, or send the bypass token (X-Admin-Token) to skip it per request —
    # so the operator never limits themselves. Limits are per trailing window.
    rate_limit_enabled: bool = True
    rate_limit_per_ip: int = 30
    rate_limit_per_session: int = 20
    rate_limit_window_seconds: int = 60
    rate_limit_bypass_token: SecretStr | None = None
    session_history_limit: int = 10
    session_cookie_name: str = "votia_session"

    # Access gate. If set, all non-/health endpoints require an X-Access-Code
    # header matching this value. Leave unset in local dev to disable the gate.
    access_code: SecretStr | None = None
