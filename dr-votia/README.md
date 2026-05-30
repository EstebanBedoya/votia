# Dr. votIA

RAG agent over Colombian electoral data (government plans, management records,
national datasets). Answers questions grounded in verifiable sources, citing
where each claim comes from.

Built with a **hexagonal architecture** (ports & adapters) so the core logic is
independent of Voyage (embeddings), Supabase (pgvector store) and OpenRouter
(LLM gateway) — and so the upcoming web layer plugs in as just another entrypoint.

**Dual-model answering flow** (`Docs/models.md`): a cheap model
(`deepseek/deepseek-v4-flash`) rewrites the question for retrieval and classifies
its topic; pgvector retrieves; then the quality model
(`anthropic/claude-sonnet-4.6`) writes the grounded answer.

## Architecture

```
domain/          Pure business: entities, ports (interfaces), chunking, topic rules.
application/     Use cases: IngestDocuments, AnswerQuestion. Depend only on ports.
infrastructure/  Adapters that implement the ports: Voyage, Supabase, Claude, readers.
entrypoints/     Driving adapters: CLI today, FastAPI later. Wire via container.py.
```

Dependencies point **inward**: `infrastructure` and `entrypoints` know `domain`,
never the reverse. Swapping a provider touches one adapter; the core never moves.

## Setup

```bash
uv sync                 # creates .venv with Python 3.12 and installs deps
cp .env.example .env    # then fill in the keys (service_role for Supabase)
```

## Usage

```bash
# Validate the file→metadata mapping and chunk counts — no API calls, no cost:
uv run dr-votia ingest --dry-run

# Run the real ingestion (embeds with Voyage, inserts into Supabase):
uv run dr-votia ingest

# Ask a question (retrieval + Claude):
uv run dr-votia ask "¿Qué propone Fajardo en seguridad?"
uv run dr-votia ask "¿Cuál es la pobreza monetaria nacional?" --tipo estadistica_nacional
```

### Web API

The web layer is a second driving adapter over the same use cases. Install the
extra and serve:

```bash
uv sync --extra web
uv run dr-votia serve            # http://127.0.0.1:8000  (docs at /docs)
```

```bash
curl -s localhost:8000/chat -H 'content-type: application/json' \
  -d '{"pregunta": "¿Qué propone Fajardo en seguridad?", "candidato": "fajardo"}'
# -> { "respuesta": "...", "fuentes": [ ... ] }
```

## Development

```bash
uv run ruff check .     # lint
uv run ruff format .    # format
uv run mypy             # strict type check
uv run pytest           # tests (domain + application run with fakes, no network)
```

## Configuration

All settings load from `.env` (see `config.py`). Key defaults:

| Setting          | Default            | Notes                                   |
| ---------------- | ------------------ | --------------------------------------- |
| `voyage_model`   | `voyage-3.5`       | 1024 dims — matches the `vector` column |
| `embedding_dim`  | `1024`             | Must match the Supabase schema          |
| `openrouter_answer_model` | `anthropic/claude-sonnet-4.6` | Final response (quality-first) |
| `openrouter_query_model`  | `deepseek/deepseek-v4-flash`  | RAG preprocessing (cheap)       |
| `chunk_size`     | `800`              | Characters per chunk                    |
| `chunk_overlap`  | `150`              | Overlap between chunks                  |

## Data sources

The file → metadata mapping lives in `entrypoints/sources.py`. It points at
`../dr-contexto-data/` by default (override with `--data-root`).
