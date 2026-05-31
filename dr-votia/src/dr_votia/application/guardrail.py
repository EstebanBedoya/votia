"""Input guardrail — runs before retrieval to keep votIA on-mission.

Two layers, on purpose:

1. Instruction-override detection is a *security* control, so it is deterministic
   (regex) and fails CLOSED: it cannot be knocked open by an LLM hiccup.
2. Topical scope ("is this about the Colombian electoral context?") needs judgment,
   so it asks the cheap model — and fails OPEN: if that call errors or returns
   garbage we let the question through (a mis-routed cooking question wastes one
   retrieval; blocking a legitimate voter is the worse failure).

This is deliberately NOT folded into :class:`QueryRefiner`, which falls back to the
raw question on any parse error — fail-open semantics that would silently bypass
layer 1. A security gate and a best-effort optimizer don't share a failure mode.
"""

from __future__ import annotations

import json
import re

from dr_votia.application.prompts import GUARD_SYSTEM
from dr_votia.domain.guard import GuardCategory, GuardVerdict
from dr_votia.domain.ports import LLMProvider

# High-precision patterns for blatant instruction-override / prompt-injection.
# Kept tight on purpose: a false positive blocks a real voter, so we only match
# phrasings that have no legitimate use in a question about Colombian politics.
_INJECTION_PATTERNS = (
    r"ignor(a|á|ar|en)\s+(las|tus|todas?\s+las)?\s*instruc",
    r"olvid(a|á|ar|en|ate|áte)\s+(todo|las\s+instruc|tus\s+instruc)",
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"(revel|muestr|mostr|imprim|repet|dame)\w*\s+(el|tu|the|your)?\s*(system\s*)?prompt",
    r"(system|developer)\s*prompt",
    r"act(ú|u)a\s+como\s+si\s+no\s+tuvieras",
    r"a\s+partir\s+de\s+ahora\s+(eres|sos|ser(á|a)s)",
    r"you\s+are\s+now\s+",
)
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


class Guardrail:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    def check(self, question: str) -> GuardVerdict:
        if _INJECTION_RE.search(question):
            return GuardVerdict.blocked(
                GuardCategory.INJECTION,
                "Intento de anular las instrucciones del sistema.",
            )
        return self._check_topic(question)

    def _check_topic(self, question: str) -> GuardVerdict:
        try:
            result = self._llm.generate(system=GUARD_SYSTEM, user=question)
        except Exception:  # noqa: BLE001 — availability over strictness for scope
            return GuardVerdict.ok()

        on_topic, reason = _parse(result.text)
        if on_topic:
            return GuardVerdict.ok(usage=result.usage)
        return GuardVerdict.blocked(GuardCategory.OFF_TOPIC, reason, usage=result.usage)


def _parse(raw: str) -> tuple[bool, str]:
    """Returns (on_topic, reason). Unparseable output fails open (on_topic=True)."""
    match = _JSON_OBJECT.search(raw)
    if match is None:
        return True, ""
    try:
        data = json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return True, ""
    if not isinstance(data, dict):
        return True, ""
    return bool(data.get("on_topic", True)), str(data.get("reason") or "")
