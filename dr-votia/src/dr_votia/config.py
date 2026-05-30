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

    # OpenRouter (OpenAI-compatible gateway). Dual-model setup:
    #   answer model — final Dr. votIA response (quality-first)
    #   query model  — cheap RAG preprocessing (reformulation + topic classification)
    openrouter_api_key: SecretStr
    openrouter_answer_model: str = "anthropic/claude-sonnet-4.6"
    openrouter_query_model: str = "deepseek/deepseek-v4-flash"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Pipeline knobs
    chunk_size: int = 800
    chunk_overlap: int = 150
    insert_batch: int = 50
