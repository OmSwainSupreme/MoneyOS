"""Asynchronous database engine, session factory, and FastAPI dependency.

This module is the single owner of the async SQLAlchemy engine and session
lifecycle. It exposes:

* :func:`get_engine` / :func:`get_sessionmaker` - lazily-constructed
  singletons configured from application settings.
* :func:`get_db_session` - the FastAPI dependency that yields a request-scoped
  :class:`~sqlalchemy.ext.asyncio.AsyncSession`. The dependency only manages
  the session lifecycle (create, yield, rollback on error, close); it does
  **not** commit, leaving transaction boundaries to the caller.
* :func:`transaction` - an async context manager that owns commit/rollback for
  the service layer.
* :func:`verify_connection` - a lightweight ``SELECT 1`` liveness probe.
* :func:`dispose_engine` - shutdown hook that releases pooled connections.

No ORM/business logic lives here; the database layer stays isolated from API
routes and services. Everything is async.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from core.config import Settings, get_settings
from core.logging import get_logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = get_logger(__name__)

# Lazily-initialized singletons. Construction is deferred until first use so
# importing this module has no side effects (mirrors the app factory).
_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _create_engine(settings: Settings) -> AsyncEngine:
    """Build the async engine with the configured connection pool."""
    return create_async_engine(
        settings.async_database_url,
        echo=settings.db_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=settings.db_pool_pre_ping,
    )


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Return the process-wide async engine, creating it on first call.

    Args:
        settings: Optional settings override; the cached singleton is used
            when omitted.

    Returns:
        The shared :class:`AsyncEngine`.
    """
    global _engine
    if _engine is None:
        resolved = settings or get_settings()
        _engine = _create_engine(resolved)
        logger.info(
            "Async database engine initialized (pool_size=%s, "
            "max_overflow=%s)",
            resolved.db_pool_size,
            resolved.db_max_overflow,
        )
    return _engine


def get_sessionmaker(
    settings: Settings | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Return the async session factory, creating it on first call.

    ``expire_on_commit`` is disabled so ORM objects remain usable after a
    commit within the same request (SQLAlchemy 2.x async best practice).
    """
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(settings),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a request-scoped async session.

    The dependency only manages the session lifecycle: it creates the
    session, yields it to the route handler, rolls back on any unhandled
    exception, and closes the session. It does **not** commit - transaction
    boundaries are owned by the service layer (see :func:`transaction`).

    Yields:
        A request-scoped :class:`AsyncSession`.
    """
    factory = get_sessionmaker()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncIterator[AsyncSession]:
    """Own commit/rollback for the service layer.

    Wrap a unit of work so it is committed on success and rolled back on any
    exception. The session itself is created and closed by the caller (e.g.
    the :func:`get_db_session` dependency), keeping transaction boundaries
    explicit at the service layer rather than implicit in the API route.

    Example::

        async with transaction(session):
            session.add(entity)

    Args:
        session: An active :class:`AsyncSession`.

    Yields:
        The same ``session``, for use within the ``async with`` block.
    """
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise


async def verify_connection() -> bool:
    """Execute ``SELECT 1`` to confirm the database is reachable.

    Returns:
        ``True`` when the query succeeds.

    Raises:
        Exception: Propagates any driver/connection error to the caller so
            health endpoints can surface an accurate status.
    """
    factory = get_sessionmaker()
    async with factory() as session:
        result = await session.execute(text("SELECT 1"))
        return result.scalar_one() == 1


async def dispose_engine() -> None:
    """Dispose the engine and release all pooled connections (shutdown)."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        logger.info("Async database engine disposed")
    _engine = None
    _sessionmaker = None
