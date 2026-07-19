"""UserProfile ORM model for the user (profile/preferences) domain.

This module defines :class:`UserProfile` - the profile/preferences record owned
by the user module. It has a strict one-to-one relationship with the auth
``User`` entity (``user_id`` FK, cascade delete) so a user never exists
without a profile. The model inherits from the shared declarative
:class:`~database.base.Base` so its table registers with the single metadata
object that Alembic targets.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from database.base import Base
from sqlalchemy import DateTime, ForeignKey, String, func, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

# Canonical enum-backed option sets. Kept as module constants so the schema,
# service validation, and repository defaults stay in one place.
CURRENCIES: tuple[str, ...] = ("INR", "USD", "EUR", "GBP")
THEMES: tuple[str, ...] = ("light", "dark", "system")
LANGUAGES: tuple[str, ...] = ("en", "hi")
DATE_FORMATS: tuple[str, ...] = ("DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD")

DEFAULT_CURRENCY = "INR"
DEFAULT_THEME = "system"
DEFAULT_LANGUAGE = "en"
DEFAULT_DATE_FORMAT = "DD/MM/YYYY"
DEFAULT_TIMEZONE = "UTC"


class UserProfile(Base):
    """Profile and preference record for a single authenticated user.

    Exactly one profile exists per user. Deleting the parent ``User`` cascades
    to this row. Preference columns carry sensible defaults so a freshly
    registered user has a complete, valid profile without extra writes.
    """

    __tablename__ = "user_profiles"

    __table_args__ = (
        CheckConstraint(
            "currency IN ('INR', 'USD', 'EUR', 'GBP')",
            name="check_user_profiles_currency"
        ),
        CheckConstraint(
            "theme IN ('light', 'dark', 'system')",
            name="check_user_profiles_theme"
        ),
        CheckConstraint(
            "language IN ('en', 'hi')",
            name="check_user_profiles_language"
        ),
        CheckConstraint(
            "date_format IN ('DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD')",
            name="check_user_profiles_date_format"
        ),
        CheckConstraint(
            "display_name != ''",
            name="check_user_profiles_non_empty_display_name"
        ),
        CheckConstraint(
            "avatar_url IS NULL OR avatar_url LIKE 'http://%' OR avatar_url LIKE 'https://%'",
            name="check_user_profiles_valid_avatar_url"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="New User",
        server_default="New User",
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=DEFAULT_TIMEZONE,
        server_default=DEFAULT_TIMEZONE,
    )
    currency: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default=DEFAULT_CURRENCY,
        server_default=DEFAULT_CURRENCY,
    )
    language: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default=DEFAULT_LANGUAGE,
        server_default=DEFAULT_LANGUAGE,
    )
    date_format: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=DEFAULT_DATE_FORMAT,
        server_default=DEFAULT_DATE_FORMAT,
    )
    theme: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=DEFAULT_THEME,
        server_default=DEFAULT_THEME,
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
