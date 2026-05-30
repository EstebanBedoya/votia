"""FastAPI dependencies. The container is built once and reused (it holds the
SDK clients). Tests override ``get_container`` to inject fakes.

Session identity and rate limiting live here as dependencies — they are
transport concerns (cookies, client IP, HTTP 429), kept out of the use cases.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response

from dr_votia.entrypoints.container import Container, build_container


@lru_cache(maxsize=1)
def get_container() -> Container:
    return build_container()


ContainerDep = Annotated[Container, Depends(get_container)]


def client_ip(request: Request) -> str | None:
    """First hop of X-Forwarded-For (set by the proxy) or the direct peer.

    Behind a proxy the direct peer is the proxy itself, so we trust the first
    forwarded address. If you don't run a trusted proxy, prefer request.client."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def get_session_id(request: Request, response: Response, container: ContainerDep) -> str:
    """Read the session cookie, or mint a new session and set it. The UUID is
    the seam a future login attaches a real user to."""
    cookie_name = container.settings.session_cookie_name
    existing = request.cookies.get(cookie_name)
    if existing and container.sessions.exists(existing):
        return existing

    session = container.sessions.create()
    response.set_cookie(
        cookie_name,
        session.id,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return session.id


SessionDep = Annotated[str, Depends(get_session_id)]


def _has_bypass(request: Request, container: Container) -> bool:
    token = container.settings.rate_limit_bypass_token
    if token is None:
        return False
    return request.headers.get("x-admin-token") == token.get_secret_value()


def enforce_rate_limit(request: Request, container: ContainerDep, session_id: SessionDep) -> None:
    result = container.rate_limiter.check(
        ip=client_ip(request),
        session_id=session_id,
        bypass=_has_bypass(request, container),
    )
    if not result.allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Demasiadas solicitudes ({result.scope}). Intentá de nuevo en un momento.",
            headers={"Retry-After": str(result.retry_after)},
        )


RateLimitDep = Annotated[None, Depends(enforce_rate_limit)]
