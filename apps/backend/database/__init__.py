"""Database package: async engine, sessions, and declarative base.

Public surface for the isolated database layer. API routes and services
depend on these exports rather than reaching into submodules directly.
"""

from __future__ import annotations

from database.base import Base
from database.session import (
    dispose_engine,
    get_db_session,
    get_engine,
    get_sessionmaker,
    transaction,
    verify_connection,
)

__all__ = [
    "Base",
    "dispose_engine",
    "get_db_session",
    "get_engine",
    "get_sessionmaker",
    "transaction",
    "verify_connection",
]
