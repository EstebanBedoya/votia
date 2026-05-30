"""OpenRouter adapter. Implements the LLMProvider port.

OpenRouter exposes an OpenAI-compatible API, so we reuse the ``openai`` SDK with
a custom ``base_url``. The model is a fully-qualified OpenRouter slug, e.g.
``anthropic/claude-sonnet-4.6`` or ``openai/gpt-4o`` — swap it via settings
without touching this code.
"""

from __future__ import annotations

import httpx
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


class OpenRouterBilling:
    """Reads account credit usage from OpenRouter's billing endpoint.

    Powers the "ENERGÍA" gauge: how much of the purchased credit budget is left.
    Distinct from the chat client — it talks to the REST billing API, not the
    OpenAI-compatible completions surface.
    """

    def __init__(self, api_key: str, *, base_url: str = DEFAULT_BASE_URL) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    def credits(self) -> dict[str, float | None]:
        """Return total/used/remaining credits and the remaining percentage.

        ``pct`` is ``None`` when the account has no purchased credit cap (so the
        UI can show "N/D" instead of a misleading empty bar).
        """
        resp = httpx.get(
            f"{self._base_url}/credits",
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        total = float(data.get("total_credits") or 0.0)
        used = float(data.get("total_usage") or 0.0)
        remaining = max(0.0, total - used)
        pct = round(remaining / total * 100.0, 1) if total > 0 else None
        return {"total": total, "used": used, "remaining": remaining, "pct": pct}
