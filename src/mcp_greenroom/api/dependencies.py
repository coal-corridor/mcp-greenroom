"""Injection points. Tests swap each one through app.dependency_overrides.

Frozen names. get_store returns SqlStore, not interfaces.Store (user decision at integration).
Example in a test:

    app.dependency_overrides[get_pipeline] = lambda: FakePipeline()
"""

from typing import Annotated

from fastapi import Header, HTTPException, Request, status

from mcp_greenroom.config import DEV_IDENTITIES, Settings
from mcp_greenroom.interfaces import Pipeline
from mcp_greenroom.models import Identity
from mcp_greenroom.store import SqlStore


def get_pipeline(request: Request) -> Pipeline:
    """The vetting pipeline, with its classifier provider and scanner already inside.

    Built once at startup by build_pipeline(settings) (api.main lifespan) and reused.
    """
    pipeline: Pipeline = request.app.state.pipeline
    return pipeline


def get_store(request: Request) -> SqlStore:
    """The store the lifespan opened. Routes use SqlStore's methods directly."""
    store: SqlStore = request.app.state.store
    return store


def get_settings(request: Request) -> Settings:
    """The validated settings the app was built with."""
    settings: Settings = request.app.state.settings
    return settings


def get_identity(
    request: Request, authorization: Annotated[str | None, Header()] = None
) -> Identity:
    """The caller, from the credential (bearer token), never from the request body.

    Unknown or missing token: 401. Dev stub tokens are in mcp_greenroom.config.DEV_IDENTITIES.
    """
    scheme, _, token = (authorization or "").partition(" ")
    dev = get_settings(request).env == "dev"  # stub identities exist only in dev
    identity = DEV_IDENTITIES.get(token.strip()) if dev and scheme.lower() == "bearer" else None
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "rule_id": "auth.unknown_credential",
                "message": "Authentication failed: missing or unknown bearer token. "
                "Send 'Authorization: Bearer <token>' with a known token.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    return identity
