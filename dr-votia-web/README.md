# Dr. votIA — Frontend

Next.js 15 (App Router) frontend for the Dr. votIA RAG backend. This is a
**functional skeleton without styling** — pages work end-to-end (chat + radar),
the UI/UX layer is deliberately left to do.

## How it talks to the backend

The browser never calls FastAPI directly. Next.js **Route Handlers** under
`src/app/api/**` act as a BFF proxy:

```
browser ──same-origin──> Next /api/* ──server-side──> FastAPI (API_BASE_URL)
```

This keeps `API_BASE_URL` server-side and lets the proxy relay the backend's
httponly session cookie (`dr_session`) transparently, so conversation memory
works without the client ever touching the cookie.

## Run

The backend must be running first:

```bash
cd ../dr-votia
uv sync --extra web
uv run dr-votia serve          # http://127.0.0.1:8000
uv run dr-votia score          # optional — needed for /radar to have data
```

Then the frontend:

```bash
pnpm install
cp .env.example .env           # set API_BASE_URL if the backend isn't on :8000
pnpm dev                       # http://localhost:3000
```

## Scripts

```bash
pnpm dev         # dev server
pnpm build       # production build (also validates types end-to-end)
pnpm typecheck   # tsc --noEmit
pnpm lint        # next lint
```

## Layout

```
src/
  lib/         types (API contract), constants (labels), api (server client), radar (recharts transform)
  hooks/       useChat, useRadar
  app/
    api/       BFF route handlers (chat, radar, radar/[candidato], health)
    chat/      chat page
    radar/     radar page
  components/  RadarChart, ChatMessage, Sources
```

## API contract

Mirrors the FastAPI schemas in `../dr-votia/src/dr_votia/entrypoints/web/schemas.py`.
The wire-format types live in `src/lib/types.ts`. Radar plots each axis' `solidez`
(1–5); source weight is `similarity`.
