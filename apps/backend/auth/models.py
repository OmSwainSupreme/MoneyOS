"""User ORM model for the authentication domain.

This module defines the :class:`User` entity - the only identity record owned
by the auth module. It carries no financial or profile data; those concerns
belong to later phases. The model inherits from the shared declarative
:class:`~database.base.Base` so its table registers with the single metadata
object that Alembic targets.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from database.base import Base
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    """Identity record for an authenticated MoneyOS account.

    Columns are limited to identity and account-state fields. Passwords are
    never stored in plaintext - only the Argon2id digest lives in
    ``password_hash``.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
