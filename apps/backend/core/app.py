"""Production-grade FastAPI application factory.

This module owns the construction of the :class:`fastapi.FastAPI` instance.
It wires together configuration, structured logging, CORS, global exception
handling, lifespan events, and the API router so the application can be
assembled consistently across development, test, and production entrypoints.

Importing this module performs no side effects; all environment access,
logging setup, and middleware registration happen inside :func:`create_app`.
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator, Callable

from api.router import api_router
from database.session import dispose_engine, get_engine
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth.exceptions import (
    AuthError,
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenTypeError,
)
from core.config import Settings, get_settings
from core.errors import register_domain_exception, register_exception_handlers
from core.logging import configure_root_logger, get_logger
from user.exceptions import ProfileNotFound, UserError

from user.exceptions import (
    InvalidPreference,
    UnsupportedCurrency,
)

logger = get_logger(__name__)

API_DESCRIPTION: str = (
    "MoneyOS backend API. Phase 2.1 - backend bootstrap. "
    "Authentication, persistence, and AI services are not yet enabled."
)


def _build_lifespan(settings: Settings) -> Callable[[FastAPI], object]:
    """Construct the ASGI lifespan context manager for the application.

    Centralizes startup and shutdown hooks. Later phases can register
    connection pools, caches, and background workers here without changing
    the factory signature.

    Args:
        settings: Resolved application settings.

    Returns:
        An async context manager yielding the application state dict.
    """

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[dict[str, object]]:
        """Manage application startup and shutdown resources."""
        logger.info(
            "Starting %s v%s (env=%s, debug=%s)",
            settings.service_name,
            settings.version,
            settings.environment,
            settings.debug,
        )
        # Initialize the async engine/connection pool at startup.
        get_engine(settings)
        try:
            yield {"settings": settings}
        finally:
            logger.info("Shutting down %s", settings.service_name)
            # Release pooled database connections on shutdown.
            await dispose_engine()

    return lifespan


def _register_exception_handlers(app: FastAPI) -> None:
    """Register domain-to-envelope mappings and install global handlers.

    Domain exceptions are mapped to a stable (status, code) pair here so the
    routers can simply raise them and the unified envelope is produced in one
    place. Unexpected exceptions are logged and returned as a generic 500.
    """
    register_domain_exception(EmailAlreadyRegisteredError, 409, "email_taken")
    register_domain_exception(InvalidCredentialsError, 401, "invalid_credentials")
    register_domain_exception(InactiveUserError, 401, "account_inactive")
    register_domain_exception(InvalidTokenError, 401, "invalid_token")
    register_domain_exception(TokenTypeError, 401, "invalid_token_type")
    register_domain_exception(ProfileNotFound, 404, "profile_not_found")
    register_domain_exception(UnsupportedCurrency, 422, "unsupported_currency")
    register_domain_exception(InvalidPreference, 422, "invalid_preference")
    # AuthError / UserError are bases; they still resolve to a generic mapping.
    register_domain_exception(AuthError, 401, "auth_error")
    register_domain_exception(UserError, 400, "user_error")
    register_exception_handlers(app)


def _register_middleware(app: FastAPI, settings: Settings) -> None:
    """Register ASGI middleware, including configurable CORS."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the MoneyOS FastAPI application.

    Args:
        settings: Optional pre-built settings. When omitted, the cached
            settings singleton is resolved inside the factory (no import-time
            side effects).

    Returns:
        A fully configured :class:`fastapi.FastAPI` instance.
    """
    configure_root_logger()
    resolved = settings or get_settings()
    # Fail fast in production on insecure defaults (e.g. default DB URL).
    resolved.validate_production()

    app = FastAPI(
        title=resolved.project_name,
        description=API_DESCRIPTION,
        version=resolved.version,
        debug=resolved.debug,
        lifespan=_build_lifespan(resolved),
    )

    # Attach resolved settings for downstream access (e.g. DI, middleware).
    app.state.settings = resolved

    _register_middleware(app, resolved)
    _register_exception_handlers(app)

    # Mount all routes under the configured API version prefix.
    app.include_router(api_router, prefix=resolved.api_v1_prefix)

    logger.debug("FastAPI application constructed: %s", resolved.service_name)
    return app
