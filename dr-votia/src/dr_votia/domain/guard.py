"""Guardrail value objects.

The verdict the guardrail produces before any retrieval happens. Pure data —
the *decision* lives in the application layer (it needs an LLM); this is only
the vocabulary used to express that decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from dr_votia.domain.models import TokenUsage


class GuardCategory(StrEnum):
    """Why a question was allowed or rejected."""

    ALLOWED = "allowed"
    OFF_TOPIC = "off_topic"  # not about the Colombian electoral context
    INJECTION = "injection"  # attempt to override the system's instructions


@dataclass(frozen=True, slots=True)
class GuardVerdict:
    """The outcome of inspecting a user question before answering."""

    allowed: bool
    category: GuardCategory
    reason: str = ""
    # Cost of the topical-scope LLM call (empty when the verdict was reached by
    # the deterministic injection regex, or when the call failed open).
    usage: TokenUsage = field(default_factory=TokenUsage.empty)

    @classmethod
    def ok(cls, *, usage: TokenUsage | None = None) -> GuardVerdict:
        return cls(
            allowed=True,
            category=GuardCategory.ALLOWED,
            usage=usage or TokenUsage.empty(),
        )

    @classmethod
    def blocked(
        cls, category: GuardCategory, reason: str = "", *, usage: TokenUsage | None = None
    ) -> GuardVerdict:
        return cls(
            allowed=False,
            category=category,
            reason=reason,
            usage=usage or TokenUsage.empty(),
        )
