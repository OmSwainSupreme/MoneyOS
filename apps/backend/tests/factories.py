"""Test factories for inserting minimal domain rows.

Provides a helper to create a bare ``auth.User`` row directly via the ORM so
tests can reference a real FK parent without going through the auth service
(password hashing, tokens). This is intentionally lightweight - it exists only
to satisfy the ``user_profiles.user_id`` foreign key in tests.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import User
from auth.security import hash_password


async def make_user(
    session: AsyncSession, *, email: str | None = None, full_name: str = "Test User"
) -> User:
    """Insert and flush a User row, returning the persisted instance.

    Args:
        session: An active async session.
        email: Optional email; a unique one is generated when omitted.
        full_name: Display name stored on the user.

    Returns:
        The flushed :class:`~auth.models.User` (id populated).
    """
    if email is None:
        email = f"user-{uuid.uuid4().hex[:12]}@example.com"
    user = User(
        email=email,
        password_hash=hash_password("Sup3rSecret!Pass"),
        full_name=full_name,
    )
    session.add(user)
    await session.flush()
    return user
