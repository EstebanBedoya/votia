"""FastAPI application factory — the web driving adapter.

Run with: ``uvicorn dr_votia.entrypoints.web.app:app`` or ``dr-votia serve``.
Requires the ``web`` extra: ``uv sync --extra web``.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dr_votia.entrypoints.web.routes import public_router, router


def create_app() -> FastAPI:
    app = FastAPI(title="Dr. votIA", version="0.1.0")
    # Permissive CORS for local development; tighten allow_origins in production.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # /health is always open (liveness probes, uptime monitors).
    app.include_router(public_router)
    # All other routes require a valid X-Access-Code header.
    app.include_router(router)
    return app


app = create_app()
