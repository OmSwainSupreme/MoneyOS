"""initial database foundation.

Revision ID: 2a8ca911e7f1
Revises:
Create Date: 2026-07-18 20:39:36.911000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2a8ca911e7f1"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the schema changes for this revision."""
    pass


def downgrade() -> None:
    """Revert the schema changes for this revision."""
    pass
