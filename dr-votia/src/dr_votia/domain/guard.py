"""Guardrail value objects.

The verdict the guardrail produces before any retrieval happens. Pure data —
the *decision* lives in the application layer (it needs an LLM); this is only
the vocabulary used to express that decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


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

    @classmethod
    def ok(cls) -> GuardVerdict:
        return cls(allowed=True, category=GuardCategory.ALLOWED)

    @classmethod
    def blocked(cls, category: GuardCategory, reason: str = "") -> GuardVerdict:
        return cls(allowed=False, category=category, reason=reason)
