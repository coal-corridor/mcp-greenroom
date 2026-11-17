"""Error bodies: a stable rule id and a readable message. Never a stack trace."""

import logging
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request, status
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


def _unexpected(_: Request, exc: Exception) -> JSONResponse:
    log_event("http.unhandled_error", logging.ERROR, error=type(exc).__name__)
    body = {
        "rule_id": "internal.error",
        "message": "The request failed inside MCP Greenroom. Nothing was approved. "
        "Try again; if it persists, give the operator the time of the request.",
    }
    return JSONResponse(body, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def install(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error)
    app.add_exception_handler(HTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StoreUnavailable, _store_unavailable)
    app.add_exception_handler(Exception, _unexpected)
