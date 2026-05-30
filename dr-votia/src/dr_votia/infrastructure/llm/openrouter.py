"""OpenRouter adapter. Implements the LLMProvider port.

OpenRouter exposes an OpenAI-compatible API, so we reuse the ``openai`` SDK with
a custom ``base_url``. The model is a fully-qualified OpenRouter slug, e.g.
``anthropic/claude-sonnet-4.6`` or ``openai/gpt-4o`` — swap it via settings
without touching this code.
"""

from __future__ import annotations

from openai import OpenAI

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-sonnet-4.6"
DEFAULT_MAX_TOKENS = 1024

# Optional attribution headers OpenRouter uses for app rankings.
_APP_HEADERS = {"X-Title": "Dr. votIA"}


class OpenRouterLLM:
    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self._client = OpenAI(api_key=api_key, base_url=base_url, default_headers=_APP_HEADERS)
        self._model = model
        self._max_tokens = max_tokens

    def generate(self, *, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""
