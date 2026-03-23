"""
Option Oracle — Centralized Exception → HTTP Response Handlers

All three handlers produce an identical JSON shape so clients always parse
the same structure regardless of error type:

    {
        "error":      "Human-readable message",
        "code":       "MACHINE_READABLE_CODE",
        "request_id": "uuid4 from X-Request-ID header",
        "timestamp":  "2025-01-01T00:00:00.000000"
    }

Register all three in create_app() via app.add_exception_handler().
"""
import traceback
from datetime import datetime

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

from src.exceptions import OracleError
from config.logging import get_api_logger

logger = get_api_logger()


def _request_id(request: Request) -> str:
    """Extract request ID set by RequestIDMiddleware, or fall back to 'unknown'."""
    return getattr(getattr(request, "state", None), "request_id", "unknown")


def _error_body(error: str, code: str, request_id: str) -> dict:
    return {
        "error": error,
        "code": code,
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def oracle_error_handler(request: Request, exc: OracleError) -> JSONResponse:
    """Handle all OracleError subclasses with their declared status code."""
    request_id = _request_id(request)
    logger.warning(
        f"[{request_id}] {exc.__class__.__name__} on {request.method} {request.url.path}: "
        f"{exc.message}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.message, exc.code, request_id),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException with the same response shape."""
    request_id = _request_id(request)
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    logger.warning(
        f"[{request_id}] HTTP {exc.status_code} on {request.method} {request.url.path}: "
        f"{detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(detail, code, request_id),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for any exception that slips past the typed handlers.
    Logs the full traceback server-side; returns a generic 500 to the client.
    """
    request_id = _request_id(request)
    logger.error(
        f"[{request_id}] Unhandled {type(exc).__name__} on "
        f"{request.method} {request.url.path}:\n"
        + traceback.format_exc()
    )
    return JSONResponse(
        status_code=500,
        content=_error_body(
            "An unexpected error occurred. Please try again.",
            "INTERNAL_ERROR",
            request_id,
        ),
    )
