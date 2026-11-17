"""The application factory and the app `make run` serves. Routers live in api.routers."""

import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from mcp_greenroom.api import errors
from mcp_greenroom.api.routers import audit, health, reviews, servers, submissions
from mcp_greenroom.config import ConfigError, Settings, load_settings
from mcp_greenroom.interfaces import Pipeline
from mcp_greenroom.logging import configure_logging, log_event
from mcp_greenroom.store import SqlStore, StoreUnavailable
from mcp_greenroom.vetting.factory import build_pipeline


async def _log_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """One structured line per request: method, path, status, duration."""
    started = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        log_event(
            "http.request",
            method=request.method,
            path=request.url.path,
            status=status,
            duration_ms=round((time.perf_counter() - started) * 1000, 3),
        )


class StartupError(Exception):
    """The service cannot start. The message says what failed, what was received, what to do."""


def _build_pipeline_or_fail(settings: Settings) -> Pipeline:
    try:
        return build_pipeline(settings)
    except Exception as exc:
        detail = ascii(str(exc)[:300])[1:-1]
        log_event("startup.pipeline_failed", logging.ERROR, error=type(exc).__name__)
        raise StartupError(
            "Startup failed: the vetting pipeline could not be built. "
            f"Received: {type(exc).__name__}: {detail} (risk provider {settings.risk_provider}, "
            f"recordings {settings.recordings_dir}). Next: run 'uv sync' to install the scanner, "
            "check MCP_GREENROOM_RECORDINGS_DIR, then start again. Nothing is served meanwhile."
        ) from None


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app from validated settings.

    Invalid configuration raises ConfigError; a pipeline that cannot be built raises
    StartupError. The pipeline is built once, here, and reused (the scanner takes ~2.5 s).
    """
    settings = settings or load_settings()
    configure_logging(settings.log_level)
    pipeline = _build_pipeline_or_fail(settings)

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
    app.state.pipeline = pipeline
    errors.install(app)
    app.middleware("http")(errors.catch_unexpected)  # inner: errors become 500 here
    app.middleware("http")(_log_request)  # outer: sees the final status
    app.include_router(submissions.router)
    app.include_router(reviews.router)
    app.include_router(audit.router)
    app.include_router(servers.router)
    app.include_router(health.router)
    return app


def _app_or_exit() -> FastAPI:
    """Invalid configuration stops startup with the message alone, no stack trace."""
    try:
        return create_app()
    except (ConfigError, StartupError) as exc:
        raise SystemExit(str(exc)) from None


app = _app_or_exit()
