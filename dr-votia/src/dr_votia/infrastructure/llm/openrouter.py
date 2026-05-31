"""OpenRouter adapter. Implements the LLMProvider port.

OpenRouter exposes an OpenAI-compatible API, so we reuse the ``openai`` SDK with
a custom ``base_url``. The model is a fully-qualified OpenRouter slug, e.g.
``anthropic/claude-sonnet-4.6`` or ``openai/gpt-4o`` — swap it via settings
without touching this code.
"""

from __future__ import annotations

from typing import Any

import httpx
from openai import OpenAI

from dr_votia.domain.models import LLMResult, TokenUsage

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

    def generate(self, *, system: str, user: str) -> LLMResult:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        text = response.choices[0].message.content or ""
        return LLMResult(text=text, usage=self._read_usage(response))

    def _read_usage(self, response: Any) -> TokenUsage:
        """Pull cost/tokens out of the response defensively.

        OpenRouter ships ``cost`` (USD) on the ``usage`` object of every response,
        but the OpenAI SDK's typed ``CompletionUsage`` does not declare it, so it
        lands in ``model_extra``. We read that first and fall back to the dumped
        dict, treating any missing piece as zero rather than failing the request.
        """
        served_model = getattr(response, "model", None) or self._model
        usage = getattr(response, "usage", None)
        if usage is None:
            return TokenUsage(model=served_model)

        extra = getattr(usage, "model_extra", None) or {}
        cost = extra.get("cost")
        if cost is None:
            # Robust fallback when the SDK did not retain extras.
            try:
                cost = response.model_dump().get("usage", {}).get("cost")
            except Exception:  # noqa: BLE001 — usage is best-effort, never fatal
                cost = None

        prompt_details = getattr(usage, "prompt_tokens_details", None)
        cached = getattr(prompt_details, "cached_tokens", 0) or 0

        return TokenUsage(
            cost_usd=float(cost) if cost is not None else None,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            total_tokens=getattr(usage, "total_tokens", 0) or 0,
            cached_tokens=int(cached),
            model=served_model,
        )


class OpenRouterBilling:
    """Reads account credit usage from OpenRouter's billing endpoint.

    Powers the "ENERGÍA" gauge: how much of the purchased credit budget is left.
    Distinct from the chat client — it talks to the REST billing API, not the
    OpenAI-compatible completions surface.
    """

    def __init__(self, api_key: str, *, base_url: str = DEFAULT_BASE_URL) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    def credits(self) -> dict[str, Any]:
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

    def key(self) -> dict[str, Any]:
        """Return the API key's spending limit and how much of it is burned.

        ``limit``/``limit_remaining`` are USD (``limit`` is ``None`` for an
        uncapped key). ``pct`` is the percentage of the limit still available, or
        ``None`` when there is no cap — the ENERGÍA gauge reads this.
        """
        resp = httpx.get(
            f"{self._base_url}/key",
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        usage = float(data.get("usage") or 0.0)
        raw_limit = data.get("limit")
        limit = float(raw_limit) if raw_limit is not None else None
        raw_remaining = data.get("limit_remaining")
        if raw_remaining is not None:
            remaining = float(raw_remaining)
        elif limit is not None:
            remaining = max(0.0, limit - usage)
        else:
            remaining = None
        pct = round(remaining / limit * 100.0, 1) if limit and remaining is not None else None
        return {
            "label": data.get("label") or "",
            "usage": usage,
            "limit": limit,
            "limit_remaining": remaining,
            "is_free_tier": bool(data.get("is_free_tier", False)),
            "pct": pct,
        }
