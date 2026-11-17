"""GET /v0.1/servers: the published list in the upstream registry format.

When the store fails, the last-good copy is served with a degraded marker in the headers,
so the body stays upstream format. With no last-good copy the list is refused with 503.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from mcp_greenroom.api.dependencies import get_settings, get_store
from mcp_greenroom.api.errors import ApiError
from mcp_greenroom.api.paging import DEFAULT_LIMIT, MAX_LIMIT, decode_cursor, page
from mcp_greenroom.config import Settings
from mcp_greenroom.logging import log_event
from mcp_greenroom.store import SnapshotMissing, SqlStore, StoreUnavailable, read_snapshot

router = APIRouter(prefix="/v0.1/servers", tags=["servers"])

DEGRADED_HEADER = "X-Greenroom-Degraded"
GENERATED_AT_HEADER = "X-Greenroom-Generated-At"


@router.get("")
def list_servers(
    response: Response,
    store: Annotated[SqlStore, Depends(get_store)],
    settings: Annotated[Settings, Depends(get_settings)],
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
) -> dict[str, Any]:
    after = decode_cursor(cursor) if cursor else None
    if cursor and after is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "rule_id": "list.invalid_cursor",
                "message": "List failed: the cursor is not one this registry issued. "
                "Use metadata.nextCursor from the previous page, or omit it to start over.",
            },
        )
    try:
        records = store.published()
    except StoreUnavailable as exc:
        try:
            records, generated_at = read_snapshot(settings.snapshot_path)
        except SnapshotMissing:
            log_event("store.unavailable", logging.ERROR, error=str(exc), snapshot="missing")
            raise ApiError(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "store.unavailable",
                "List failed: the registry store is unavailable and there is no last-good copy "
                "yet to serve. Try again once GET /readyz reports ready.",
            ) from None
        log_event("list.degraded", generated_at=generated_at, error=str(exc))
        response.headers[DEGRADED_HEADER] = "true"
        response.headers[GENERATED_AT_HEADER] = generated_at
    return page(records, after, limit)
