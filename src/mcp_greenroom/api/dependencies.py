"""Injection points. Tests swap each one through app.dependency_overrides.

Frozen names and return types. Registry writes the bodies; until then each raises.
Example in a test:

    app.dependency_overrides[get_pipeline] = lambda: FakePipeline()
"""

from typing import Annotated

from fastapi import Header, HTTPException, Request, status

from mcp_greenroom.config import DEV_IDENTITIES, Settings
from mcp_greenroom.interfaces import Pipeline, Store
from mcp_greenroom.models import Identity


def get_pipeline() -> Pipeline:
    """The vetting pipeline, with its classifier provider and scanner already inside."""
    raise NotImplementedError("registry wires the real pipeline here")


def get_store(request: Request) -> Store:
    """The store. Registry defines its methods (mcp_greenroom.store.SqlStore)."""
    store: Store = request.app.state.store
    return store


def get_settings(request: Request) -> Settings:
    """The validated settings the app was built with."""
    settings: Settings = request.app.state.settings
    return settings


def get_identity(authorization: Annotated[str | None, Header()] = None) -> Identity:
    """The caller, from the credential (bearer token), never from the request body.

    Unknown or missing token: 401. Dev stub tokens are in mcp_greenroom.config.DEV_IDENTITIES.
    """
    scheme, _, token = (authorization or "").partition(" ")
    identity = DEV_IDENTITIES.get(token.strip()) if scheme.lower() == "bearer" else None
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
