# MCP Greenroom API: the slice's service in one container. Dev identities only (see deploy/README.md).
FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first, so a source change does not reinstall them.
COPY pyproject.toml uv.lock .python-version README.md ./
RUN uv sync --locked --no-dev --no-install-project

# Only what the service reads at runtime: code, pinned contracts, classifier recordings.
COPY src ./src
COPY contracts ./contracts
COPY evals/recordings ./evals/recordings
RUN uv sync --locked --no-dev

RUN useradd --system --create-home --uid 10001 greenroom \
    && mkdir -p /data \
    && chown greenroom /data
USER greenroom

ENV MCP_GREENROOM_DATABASE_URL=sqlite:////data/greenroom.db \
    MCP_GREENROOM_SNAPSHOT_PATH=/data/last-good.json

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD ["uv", "run", "--no-sync", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/livez', timeout=2)"]

CMD ["uv", "run", "--no-sync", "uvicorn", "mcp_greenroom.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
