"""Error bodies: a stable rule id and a readable message. Never a stack trace."""

import logging
from collections.abc import Awaitable, Callable
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from mcp_greenroom.logging import log_event
from mcp_greenroom.store import StoreUnavailable


class ApiError(Exception):
    """A refusal with its status code. The message leads with what failed, then what to do."""

    def __init__(self, status_code: int, rule_id: str, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = {"rule_id": rule_id, "message": message, **extra}


def _api_error(_: Request, exc: Exception) -> JSONResponse:
    exc = cast(ApiError, exc)
    return JSONResponse(exc.body, status_code=exc.status_code)


def _http_error(_: Request, exc: Exception) -> JSONResponse:
    exc = cast(HTTPException, exc)
    if isinstance(exc.detail, dict):
        body = exc.detail
    else:
        body = {"rule_id": f"http.{exc.status_code}", "message": str(exc.detail)}
    return JSONResponse(body, status_code=exc.status_code, headers=exc.headers)


def _validation_error(_: Request, exc: Exception) -> JSONResponse:
    exc = cast(RequestValidationError, exc)
    fields = sorted({".".join(str(p) for p in err.get("loc", ())) for err in exc.errors()})
    body = {
        "rule_id": "request.invalid",
        "message": f"Request failed validation at {', '.join(fields) or 'the body'}. "
        "Fix those fields and send it again.",
    }
    return JSONResponse(body, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)


def _store_unavailable(_: Request, exc: Exception) -> JSONResponse:
    log_event("store.unavailable", logging.ERROR, error=str(exc))
    body = {
        "rule_id": "store.unavailable",
        "message": "The registry store is unavailable, so nothing can be submitted or decided. "
        "Try again later; GET /readyz says when the store is back.",
    }
    return JSONResponse(body, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


def internal_error_response() -> JSONResponse:
    body = {
        "rule_id": "internal.error",
        "message": "The request failed inside MCP Greenroom. Nothing was approved. "
        "Try again; if it persists, give the operator the time of the request.",
    }
    return JSONResponse(body, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def catch_unexpected(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Turn any unexpected error into the 500 body here, so nothing re-raises to the server.

    The message may quote untrusted text, so it is logged as a digest ("text").
    """
    try:
        return await call_next(request)
    except Exception as exc:
        log_event(
            "http.unhandled_error",
            logging.ERROR,
            path=request.url.path,
            error=type(exc).__name__,
            text=str(exc),
        )
        return internal_error_response()


def install(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error)
    app.add_exception_handler(HTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StoreUnavailable, _store_unavailable)
