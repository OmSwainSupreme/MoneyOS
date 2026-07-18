"""Database session management.

Scaffolding — engine + session factory + FastAPI dependency. Concrete
bindings are configured in Phase 1 (PostgreSQL via async or sync driver).
"""
from __future__ import annotations

from typing import Iterator

from core.config import get_settings

settings = get_settings()

# Engine and SessionLocal are initialized in Phase 1 once the DB driver and
# connection URL are finalized. Reserved here for import stability.


def get_db() -> Iterator[object]:
    """FastAPI dependency that yields a database session.

    Implementation provided in Phase 1 (yield session, ensure close).
    """
    raise NotImplementedError("Database session wiring scheduled for Phase 1")
