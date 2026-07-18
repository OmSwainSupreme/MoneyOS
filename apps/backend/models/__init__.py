"""ORM models package.

Phase 2.2 provides database infrastructure only - no entity models are
defined yet. This module re-exports the declarative :class:`Base` so Alembic
can target a single metadata object. As concrete models are added in later
phases, import them here so they register with ``Base.metadata`` and are
discovered by autogenerate.
"""

from __future__ import annotations

from database.base import Base

# Register model modules here in later phases, e.g.:
#   from models.account import Account  # noqa: F401

__all__ = ["Base"]
