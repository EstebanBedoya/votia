# Dr. votIA

**A RAG agent that answers questions about the 2026 Colombian presidential
candidates — grounded in their actual government plans, management records and
official national datasets, always citing where each claim comes from.**

The goal is civic, not partisan: let a voter ask *"What does Fajardo propose on
security?"* or *"Compare the candidates on health"* and get an answer built only
from verifiable sources, with the sources attached — instead of vibes, headlines
or hallucinations.

```
        ┌─────────────────────────┐         ┌──────────────────────────┐
        │   dr-votia-web (Next 15) │         │   dr-votia (FastAPI)     │
 user → │   pixel-art UI + BFF     │ ──────▶ │   RAG core (hexagonal)   │
        │   /chat  /radar  /gate   │  http   │   /chat  /score  /health │
        └─────────────────────────┘         └────────────┬─────────────┘
                                                          │
                            Voyage (embeddings) ── Supabase pgvector ── OpenRouter (LLM)
```

## What's in here

This is a monorepo with two deployable services plus the source corpus and design docs.

| Path                  | What it is                                                                 |
| --------------------- | ------------------------------------------------------------------------- |
| [`dr-votia/`](./dr-votia)         | **Backend.** Python RAG agent, hexagonal architecture. CLI + FastAPI. |
| [`dr-votia-web/`](./dr-votia-web) | **Frontend.** Next.js 15 pixel-art UI + BFF proxy over the backend.    |
| `dr-contexto-data/`   | The corpus: government plans, management records, national datasets.       |
| `Docs/`               | Design docs — `pipeline.md`, `models.md`, `datos.md`, `plan.md`.           |
| `docker-compose.yml`  | Production wiring (both services on the Dokploy network).                  |

## How it works

1. **Ingestion** — documents in `dr-contexto-data/` (PDF plans, XLSX datasets,
   text analyses) are chunked, embedded with **Voyage** and stored in
   **Supabase pgvector** with topic/author metadata.
2. **Answering** — a **dual-model flow** (see `Docs/models.md`): a cheap model
   (`deepseek-v4-flash`) rewrites the question for retrieval and classifies its
   topic; pgvector retrieves the relevant chunks; then the quality model
   (`claude-sonnet-4.6`) writes the grounded, cited answer.
3. **Radar** — candidates are scored 1–5 on six thematic axes (security,
   economy, health, education, anti-corruption, environment) and rendered as a
   comparison radar in the UI.

## Stack

| Layer       | Tech                                                                   |
| ----------- | --------------------------------------------------------------------- |
| Backend     | Python 3.12 · FastAPI · Typer (CLI) · Pydantic · `uv`                  |
| Retrieval   | Voyage AI embeddings (`voyage-3.5`, 1024-dim) · Supabase pgvector      |
| LLM gateway | OpenRouter (Claude Sonnet 4.6 for answers, DeepSeek for preprocessing) |
| Frontend    | Next.js 15 (App Router) · React 19 · Tailwind v4 · Recharts · `pnpm`   |
| Deploy      | Docker Compose · Dokploy                                               |

## Quick start (Docker)

The fastest path to a running stack. You provide the keys; Compose builds both
services and wires them together.

```bash
cp .env.example .env     # fill in Supabase, Voyage, OpenRouter keys + ACCESS_CODE
docker compose up --build
# frontend → http://localhost:3002   (backend is internal-only on the compose network)
```

> The corpus must already be ingested into Supabase for answers to work — see
> the backend README for `dr-votia ingest`.

## Local development

Run the two services separately. **Start the backend first** — the frontend
proxies every call to it.

```bash
# 1) Backend  (http://127.0.0.1:8000, docs at /docs)
cd dr-votia
uv sync --extra web
cp .env.example .env
uv run dr-votia serve

# 2) Frontend (http://localhost:3000)
cd ../dr-votia-web
pnpm install
cp .env.example .env.local
pnpm dev
```

Full per-service instructions — ingestion, scoring, tests, the BFF proxy and the
design system — live in each subproject's README:

- **[dr-votia/README.md](./dr-votia/README.md)** — RAG core, CLI, FastAPI, config.
- **[dr-votia-web/README.md](./dr-votia-web/README.md)** — UI, BFF, pixel-art design system.

## Configuration

All secrets load from `.env` at the root (Compose) and per service for local
dev. See [`.env.example`](./.env.example) for the full list. The essentials:

| Variable               | What it's for                                          |
| ---------------------- | ------------------------------------------------------ |
| `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` | pgvector store (service_role — RLS is on) |
| `VOYAGE_API_KEY`       | Embeddings                                             |
| `OPENROUTER_API_KEY`   | LLM gateway (answers + preprocessing + scoring)        |
| `ACCESS_CODE`          | Shared access gate for the deployed app                |
| `RATE_LIMIT_*`         | Per-IP / per-session throttling                        |
