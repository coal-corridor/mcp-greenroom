"""The application factory. Routers live in mcp_greenroom.api.routers."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from mcp_greenroom.api import errors
from mcp_greenroom.api.routers import servers, submissions
from mcp_greenroom.config import Settings, load_settings
from mcp_greenroom.store import SqlStore


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app from validated settings. Invalid configuration raises ConfigError."""
    settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        store = SqlStore(settings.database_url, settings.snapshot_path)
        store.ensure_schema()
        app.state.store = store
        yield

    app = FastAPI(title="MCP Greenroom", lifespan=lifespan)
    app.state.settings = settings
    errors.install(app)
    app.include_router(submissions.router)
    app.include_router(servers.router)
    return app
