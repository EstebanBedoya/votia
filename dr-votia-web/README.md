# Dr. votIA — Frontend

Next.js 15 (App Router) frontend for the [Dr. votIA](../README.md) RAG backend.
A retro **16-bit pixel-art** experience ("Tierra Pixelada") that turns dry
electoral data into something a voter actually wants to explore: chat with the
agent, compare candidates on a radar, and watch a playful "energy" budget tick
down as each answer costs real tokens.

## Intent

The backend is correct but austere. This layer exists to make the civic data
**approachable** — a warm, gamified, Colombian pixel palette — without ever
hiding the sources. Every answer still renders its citations; the radar still
plots verifiable 1–5 scores. Style serves trust, it doesn't replace it.

## Features

- **Chat** (`/chat`) — grounded Q&A with the agent, markdown answers and an
  expandable **Sources** panel per message.
- **Radar** (`/radar`, `/eje/[eje]`) — compares candidates across the six
  thematic axes (security, economy, health, education, anti-corruption,
  environment) using Recharts.
- **Access gate** (`/gate`) — a shared `ACCESS_CODE` wall for the deployed app.
- **Session energy & cost** — a pixel energy gauge that reflects per-session
  token usage, so the demo stays within budget.

## How it talks to the backend

The browser **never** calls FastAPI directly. Next.js **Route Handlers** under
`src/app/api/**` act as a BFF (backend-for-frontend) proxy:

```
browser ──same-origin──▶ Next /api/* ──server-side──▶ FastAPI (API_BASE_URL)
```

This keeps `API_BASE_URL` server-side and lets the proxy relay the backend's
httponly session cookie (`dr_session`) transparently — so conversation memory
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
cp .env.example .env.local     # set API_BASE_URL if the backend isn't on :8000
pnpm dev                       # http://localhost:3000
```

## Stack

| Concern    | Tech                                                       |
| ---------- | --------------------------------------------------------- |
| Framework  | Next.js 15 (App Router) · React 19                         |
| Styling    | Tailwind CSS v4 (`@theme` tokens) — "Tierra Pixelada"      |
| Charts     | Recharts                                                   |
| Markdown   | react-markdown + remark-gfm                                |
| Tooling    | TypeScript (strict) · ESLint · pnpm                        |

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
  lib/         types (API contract), constants (labels, axes, icons),
               api (server client), radar (recharts transform), assets (Storage URLs)
  hooks/       useChat, useRadar
  middleware.ts  access-gate redirect
  app/
    api/       BFF route handlers (chat, radar, gate, key, usage, config, health)
    chat/      chat page
    radar/     radar page          eje/[eje]/  single-axis detail
    gate/      access-code page
  components/  Pixel* primitives (Panel, Button, Progress, Icon…),
               ChatWindow, ChatBubble, RadarChart, Sources, StatsPanel…
```

## Design system

The pixel-art tokens live in `src/app/globals.css` under `@theme` (mirrors the
stitch `DESIGN.md`): warm parchment surfaces, "Roasted Coffee" outlines, sunny
gold primary, colonial navy secondary. Pixel-art assets are served from Supabase
Storage — URLs are built in `src/lib/assets.ts` from `NEXT_PUBLIC_SUPABASE_URL`.

## API contract

Mirrors the FastAPI schemas in
[`../dr-votia/src/dr_votia/entrypoints/web/schemas.py`](../dr-votia/src/dr_votia/entrypoints/web/schemas.py).
The wire-format types live in `src/lib/types.ts`. Radar plots each axis'
`solidez` (1–5); source weight is `similarity`.
