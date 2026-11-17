"""GET /v0.1/servers: the published list in the upstream registry format."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from mcp_greenroom.api.dependencies import get_store
from mcp_greenroom.api.paging import DEFAULT_LIMIT, MAX_LIMIT, decode_cursor, page
from mcp_greenroom.store import SqlStore

router = APIRouter(prefix="/v0.1/servers", tags=["servers"])


@router.get("")
def list_servers(
    store: Annotated[SqlStore, Depends(get_store)],
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
    return page(store.published(), after, limit)
