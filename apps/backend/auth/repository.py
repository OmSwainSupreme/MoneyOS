"""Auth data-access layer.

The repository is the only module that touches the ORM for the user entity. It
contains **no business logic** - just persistence operations (create, fetch,
existence checks). Transaction boundaries are owned by the service layer, which
passes in an already-bound :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import User
from auth.schemas import RegisterRequest


class UserRepository:
    """Async persistence for :class:`~auth.models.User`."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to a request-scoped session."""
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Return the user with ``user_id`` or ``None`` if absent."""
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        """Return the user with the given ``email`` or ``None`` if absent.

        The email is normalized to lowercase so lookups are case-insensitive.
        """
        result = await self._session.execute(
            select(User).where(User.email == email.strip().lower())
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Return ``True`` when any user already owns ``email``.

        Matching is case-insensitive (see :meth:`get_by_email`).
        """
        return await self.get_by_email(email) is not None

    async def create(
        self, payload: RegisterRequest, password_hash: str
    ) -> User:
        """Persist a new user from a registration payload.

        The email is normalized to lowercase before storage so the unique
        constraint is effectively case-insensitive. The caller is responsible
        for hashing the password and for committing the enclosing transaction.

        Args:
            payload: Validated registration input.
            password_hash: Argon2id digest produced by the security layer.

        Returns:
            The newly created (not yet committed) :class:`User`.
        """
        user = User(
            email=payload.email.strip().lower(),
            password_hash=password_hash,
            full_name=payload.full_name,
        )
        self._session.add(user)
        # Flush so the generated id/columns are populated for the caller
        # without committing the enclosing transaction.
        await self._session.flush()
        return user
