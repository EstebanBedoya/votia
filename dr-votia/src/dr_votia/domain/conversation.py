"""Conversation entities — the aggregate a session owns.

A distinct bounded context from the RAG ingestion entities in ``models.py``:
these describe *who is talking and what was said*, not the documents votIA
reasons over. Pure data — persistence lives behind the SessionStore port.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True, slots=True)
class Message:
    """One turn in a conversation. ``created_at`` is an ISO-8601 string set by
    the store on insert; ``None`` for messages not yet persisted."""

    role: Role
    content: str
    created_at: str | None = None


@dataclass(frozen=True, slots=True)
class Session:
    """An anonymous conversation thread. ``id`` is a server-issued UUID — the
    seam a future login attaches a real user to."""

    id: str
    created_at: str | None = None
