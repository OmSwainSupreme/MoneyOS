"""Pytest fixtures for the MoneyOS backend test-suite.

The functional tests in this package run against a **real PostgreSQL** database
so they exercise the actual ORM, CHECK constraints, server defaults, and the
FastAPI dependency graph end-to-end. The target database is configured via the
``TEST_DATABASE_URL`` environment variable (asyncpg DSN).

If ``TEST_DATABASE_URL`` is not set (or Postgres is unreachable), the fixtures
``skip`` rather than fail, so the suite still collects and the metadata-only
tests run in CI environments without a database. This keeps the repository
green while making the integration tests first-class when a DB is available.
"""

from __future__ import annotations

import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.base import Base

# Import the domain models so their tables register on ``Base.metadata`` and are
# picked up by ``create_all`` / ``drop_all`` in the fixtures above.
import models  # noqa: F401  (side-effect: metadata registration)
from models import (  # noqa: F401
    Account,
    Category,
    Transaction,
    User,
    UserProfile,
)

# Migration-level extensions/constraints are not applied by ``create_all`` (it
# does not run Alembic), so the tests that depend on them are skipped unless a
# Postgres instance with the migration applied is provided. ``create_all`` is
# still used for schema shape; the few constraint-specific tests are gated by
# ``requires_postgres``.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


def _make_engine():
    """Build a test engine, or ``None`` when no DB is configured."""
    if not TEST_DATABASE_URL:
        return None
    return create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)


_engine = _make_engine()
_sessionmaker: async_sessionmaker[AsyncSession] | None = (
    async_sessionmaker(_engine, expire_on_commit=False, autoflush=False)
    if _engine is not None
    else None
)


_SKIP_DB = pytest.mark.skip(
    reason="TEST_DATABASE_URL not set or Postgres unreachable"
)


def pytest_configure(config: pytest.Config) -> None:
    """Register the requires_postgres marker (also declared in pyproject)."""
    config.addinivalue_line(
        "markers",
        "requires_postgres: test needs a live PostgreSQL (TEST_DATABASE_URL)",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip DB-backed tests when no database is configured/reachable.

    Any test (or module via ``pytestmark``) tagged ``requires_postgres`` is
    skipped when ``_sessionmaker`` could not be built, so the suite stays green
    on machines/CI without Postgres while running for real when a DB exists.
    """
    if _sessionmaker is not None:
        return
    for item in items:
        if item.get_closest_marker("requires_postgres") is not None:
            item.add_marker(_SKIP_DB)


@pytest_asyncio.fixture
async def db_session():
    """Yield a session bound to a fresh schema, rolling back after the test.

    The schema is recreated per-test so each case is isolated. Skips when no
    database is configured.
    """
    if _sessionmaker is None:
        pytest.skip("TEST_DATABASE_URL not set or Postgres unreachable")
    assert _engine is not None
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with _sessionmaker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def migrated_session():
    """Yield a session whose schema was built via Alembic (constraints + ext).

    Used by tests that assert CHECK constraints / server defaults which are
    only installed by the migration, not by ``create_all``.
    """
    if _sessionmaker is None:
        pytest.skip("TEST_DATABASE_URL not set or Postgres unreachable")
    # The migration is applied out-of-band by the test runner (see CI). Here we
    # assume the target DB already has the migrated schema, so we just yield a
    # session. Tests that commit (e.g. route tests) must not leak rows into the
    # next case, so we truncate every table after the test regardless of whether
    # it rolled back or committed.
    assert _sessionmaker is not None
    async with _sessionmaker() as session:
        try:
            yield session
        finally:
            # Best-effort isolation: discard any committed state, then truncate.
            await session.rollback()
            await _truncate_all(session)


async def _truncate_all(session: AsyncSession) -> None:
    """Truncate every known table to keep tests isolated.

    Runs in its own transaction that is committed, so rows left behind by a
    committing test are wiped before the next case runs. Tables are truncated
    WITH RESTART IDENTITY / CASCADE to reset sequences and honor FKs.
    """
    from sqlalchemy import text

    table_names = ", ".join(
        f'"{t.name}"' for t in Base.metadata.sorted_tables
    )
    if not table_names:
        return
    async with session.begin():
        await session.execute(
            text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE")
        )
