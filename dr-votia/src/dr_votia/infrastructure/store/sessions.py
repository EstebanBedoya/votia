"""Supabase adapter for conversation sessions. Implements the SessionStore port.

Two tables (see scripts/migrations/0001_sessions.sql):
  - ``sessions``: one row per anonymous thread, server-issued UUID.
  - ``messages``: one row per turn, with the requester IP for IP-based rate
    limiting. ``role`` distinguishes user turns (the ones we count) from
    assistant replies.

Requires the service_role key — RLS is enabled and the anon role cannot read or
write these tables directly; everything goes through this server.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from postgrest.types import CountMethod
from supabase import Client, create_client

from dr_votia.domain.conversation import Message, Role, Session

SESSIONS = "sessions"
MESSAGES = "messages"


class SupabaseSessionStore:
    def __init__(self, url: str, service_key: str) -> None:
        self._client: Client = create_client(url, service_key)

    def create(self) -> Session:
        # UUID minted client-side: deterministic and independent of PostgREST's
        # return representation. created_at is filled by the column default.
        session_id = str(uuid.uuid4())
        self._client.table(SESSIONS).insert({"id": session_id}).execute()
        return Session(id=session_id)

    def exists(self, session_id: str) -> bool:
        response = self._client.table(SESSIONS).select("id").eq("id", session_id).limit(1).execute()
        return bool(response.data)

    def append(self, session_id: str, message: Message, *, ip: str | None = None) -> None:
        self._client.table(MESSAGES).insert(
            {
                "session_id": session_id,
                "role": message.role.value,
                "content": message.content,
                "ip": ip,
            }
        ).execute()

    def add_cost(self, session_id: str, cost_usd: float) -> float:
        # Atomic increment via a Postgres function (see migration 0002): a
        # read-modify-write in Python would race between concurrent turns of the
        # same session. The RPC adds and returns the new total in one round-trip.
        response = self._client.rpc(
            "increment_session_cost",
            {"p_session_id": session_id, "p_delta": cost_usd},
        ).execute()
        return float(cast("Any", response.data) or 0.0)

    def session_cost(self, session_id: str) -> float:
        response = (
            self._client.table(SESSIONS)
            .select("total_cost_usd")
            .eq("id", session_id)
            .limit(1)
            .execute()
        )
        rows = cast("list[dict[str, Any]]", response.data or [])
        return float(rows[0]["total_cost_usd"]) if rows else 0.0

    def history(self, session_id: str, *, limit: int = 10) -> list[Message]:
        response = (
            self._client.table(MESSAGES)
            .select("role, content, created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = cast("list[dict[str, Any]]", response.data or [])
        # Fetched newest-first to honour the limit; return chronological.
        return [
            Message(role=Role(r["role"]), content=r["content"], created_at=r.get("created_at"))
            for r in reversed(rows)
        ]

    def recent_request_count(
        self,
        *,
        within_seconds: int,
        ip: str | None = None,
        session_id: str | None = None,
    ) -> int:
        cutoff = (datetime.now(UTC) - timedelta(seconds=within_seconds)).isoformat()
        query = (
            self._client.table(MESSAGES)
            .select("id", count=CountMethod.exact)
            .eq("role", Role.USER.value)
            .gte("created_at", cutoff)
            .limit(1)
        )
        if ip is not None:
            query = query.eq("ip", ip)
        if session_id is not None:
            query = query.eq("session_id", session_id)
        response = query.execute()
        return response.count or 0
