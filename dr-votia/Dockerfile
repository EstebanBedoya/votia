FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency manifests first (better layer caching). README.md is required
# because pyproject declares `readme = "README.md"` and hatchling validates it
# when building the project.
COPY pyproject.toml uv.lock README.md ./

# Install third-party deps only — the project itself needs src/, copied below.
# Splitting keeps this heavy layer cached when only source changes.
RUN uv sync --frozen --extra web --no-dev --no-install-project

# Copy source, then build/install the project itself.
COPY src/ ./src/
RUN uv sync --frozen --extra web --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "dr_votia.entrypoints.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
