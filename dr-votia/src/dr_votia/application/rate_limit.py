"""Rate limiting policy — pure decision logic over the SessionStore.

Two axes, defense in depth:
  - per IP: the hard ceiling against abuse; the client can't forge it.
  - per session: a softer courtesy quota per conversation (a dropped cookie
    resets it, so it is NOT a security control on its own).

A global ``enabled`` switch and a per-call ``bypass`` flag (wired to an admin
token at the edge) make it trivial to turn off — the operator never limits
themselves. The transport concern (429, Retry-After header) stays in the web
adapter; this layer only answers "allowed or not, and why".
"""

from __future__ import annotations

from dataclasses import dataclass

from dr_votia.domain.ports import SessionStore


@dataclass(frozen=True, slots=True)
class RateLimitConfig:
    enabled: bool = True
    per_ip: int = 30
    per_session: int = 20
    window_seconds: int = 60


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    allowed: bool
    scope: str = ""  # "ip" | "session" | "" when allowed
    retry_after: int = 0


class RateLimiter:
    def __init__(self, store: SessionStore, config: RateLimitConfig) -> None:
        self._store = store
        self._config = config

    def check(
        self,
        *,
        ip: str | None = None,
        session_id: str | None = None,
        bypass: bool = False,
    ) -> RateLimitResult:
        cfg = self._config
        if not cfg.enabled or bypass:
            return RateLimitResult(allowed=True)

        if ip is not None:
            ip_count = self._store.recent_request_count(within_seconds=cfg.window_seconds, ip=ip)
            if ip_count >= cfg.per_ip:
                return RateLimitResult(False, scope="ip", retry_after=cfg.window_seconds)

        if session_id is not None:
            session_count = self._store.recent_request_count(
                within_seconds=cfg.window_seconds, session_id=session_id
            )
            if session_count >= cfg.per_session:
                return RateLimitResult(False, scope="session", retry_after=cfg.window_seconds)

        return RateLimitResult(allowed=True)
