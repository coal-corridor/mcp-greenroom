"""The application factory. Routers live in mcp_greenroom.api.routers."""

from fastapi import FastAPI

from mcp_greenroom.api.routers import submissions
from mcp_greenroom.config import Settings, load_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app from validated settings. Invalid configuration raises ConfigError."""
    settings = settings or load_settings()
    app = FastAPI(title="MCP Greenroom")
    app.state.settings = settings
    app.include_router(submissions.router)
    return app
