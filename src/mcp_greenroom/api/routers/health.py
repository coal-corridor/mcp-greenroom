"""Liveness and readiness. Readiness asks the store and says why it is not ready."""

from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from mcp_greenroom.store import StoreUnavailable

router = APIRouter(tags=["health"])


@router.get("/livez")
def livez() -> dict[str, Any]:
    return {"alive": True}


@router.get("/readyz")
def readyz(request: Request) -> JSONResponse:
    store = getattr(request.app.state, "store", None)
    if store is None:
        reason = "store not started: the app has not finished startup"
    else:
        try:
            store.ping()
        except StoreUnavailable as exc:
            reason = f"store unavailable: {exc}"
        else:
            return JSONResponse({"ready": True})
    return JSONResponse(
        {"ready": False, "reason": reason}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE
    )
