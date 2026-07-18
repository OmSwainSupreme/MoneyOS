"""Alembic migration environment (async).

Runs migrations against the async SQLAlchemy engine using asyncpg. The
database URL and target metadata are resolved from the application code so
there is a single source of truth for both.

The backend directory (the location of ``alembic.ini``) is added to
``sys.path`` so that ``core`` and ``models`` import correctly regardless of
the current working directory. Migration commands therefore work from both
the repository root and the backend directory.
"""

from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.pool import NullPool

# Ensure the backend root is importable (works from repo root or backend dir).
BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Now that the backend root is on the path, import application modules.
from core.config import get_settings  # noqa: E402

# Import metadata target. ``models`` re-exports the declarative Base so all
# models (added in later phases) register with a single metadata object.
from models import Base  # noqa: E402

# Alembic Config object providing access to alembic.ini values.
config = context.config

# Make the migration script location independent of the current working
# directory by resolving it to an absolute path relative to this file.
config.set_main_option(
    "script_location",
    str(Path(__file__).resolve().parent),
)

# Configure Python logging from alembic.ini, if present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Inject the async DSN from application settings (never hardcoded in ini).
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.async_database_url)

# Target metadata for 'autogenerate' support.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL, no DBAPI connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:  # type: ignore[no-untyped-def]
    """Configure the context on a live connection and run migrations."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using the async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
