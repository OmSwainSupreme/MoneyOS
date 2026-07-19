"""Unified API error envelope and global exception handling.

Every error the API emits is wrapped in a single, consistent JSON shape:

    {
        "error": {"code": "profile_not_found", "message": "..."}
    }

This module defines:
- :class:`ErrorDetail` / :class:`ErrorEnvelope`: the response contract.
- :func:`error_response`: a helper that builds a :class:`fastapi.HTTPException`
  carrying an envelope in its ``detail``.
- :func:`register_exception_handlers`: installs a global handler that maps any
  domain exception (auth/user) onto the envelope and logs unexpected errors as
  a generic 500.

Routers raise domain exceptions directly; the global handler translates them,
so the two shapes FastAPI produces (Pydantic ``detail`` list vs. manual
``HTTPException`` dicts) converge on one client-facing format.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.logging import get_logger

logger = get_logger(__name__)


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    """Build a :class:`JSONResponse` using the unified error envelope."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


# Mapping of domain exception types to (HTTP status, error code).
_DOMAIN_HANDLERS: dict[type[Exception], tuple[int, str]] = {}


def register_domain_exception(
    exc_type: type[Exception], status_code: int, code: str
) -> None:
    """Register a domain exception class for automatic envelope translation."""
    _DOMAIN_HANDLERS[exc_type] = (status_code, code)


def register_exception_handlers(app: FastAPI) -> None:
    """Install global handlers that emit the unified error envelope."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        # FastAPI validation errors are re-raised as 422 HTTPExceptions with a
        # ``list[dict]`` detail; normalize them into the envelope.
        detail = exc.detail
        if isinstance(detail, list):
            message = "; ".join(
                _flatten_validation_error(item) for item in detail
            )
            return error_response(exc.status_code, "validation_error", message)
        if isinstance(detail, dict) and "error" in detail and "message" in detail:
            # Already an envelope produced by a router; pass through unchanged.
            return JSONResponse(status_code=exc.status_code, content=detail)
        return error_response(exc.status_code, "http_error", str(detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        message = "; ".join(
            _flatten_validation_error(item) for item in exc.errors()
        )
        return error_response(422, "validation_error", message)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Domain exceptions get a precise code; everything else is generic 500.
        for exc_type, (status_code, code) in _DOMAIN_HANDLERS.items():
            if isinstance(exc, exc_type):
                return error_response(status_code, code, str(exc))
        logger.exception("Unhandled error on %s", request.url.path)
        return error_response(500, "internal_error", "Internal Server Error")


def _flatten_validation_error(item: object) -> str:
    """Render a Pydantic validation error entry into a short string."""
    if not isinstance(item, dict):
        return str(item)
    loc = ".".join(str(p) for p in item.get("loc", []))
    msg = item.get("msg", "invalid value")
    return f"{loc}: {msg}" if loc else msg
