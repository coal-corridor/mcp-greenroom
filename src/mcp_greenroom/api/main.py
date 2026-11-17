"""The application factory. Routers live in mcp_greenroom.api.routers."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from mcp_greenroom.api import errors
from mcp_greenroom.api.routers import audit, health, reviews, servers, submissions
from mcp_greenroom.config import Settings, load_settings
from mcp_greenroom.logging import log_event
from mcp_greenroom.store import SqlStore, StoreUnavailable


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app from validated settings. Invalid configuration raises ConfigError."""
    settings = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        store = SqlStore(settings.database_url, settings.snapshot_path)
        try:  # a broken store at startup degrades, it does not stop the service
            store.ensure_schema()
            store.refresh_snapshot()
        except StoreUnavailable as exc:
            log_event("store.unavailable_at_startup", logging.ERROR, error=str(exc))
        app.state.store = store
        yield

    app = FastAPI(title="MCP Greenroom", lifespan=lifespan)
    app.state.settings = settings
    errors.install(app)
    app.include_router(submissions.router)
    app.include_router(reviews.router)
    app.include_router(audit.router)
    app.include_router(servers.router)
    app.include_router(health.router)
    return app
