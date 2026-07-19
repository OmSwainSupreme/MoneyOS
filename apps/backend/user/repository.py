"""User (profile/preferences) data-access layer.

The repository is the only module that touches the ORM for the
:class:`UserProfile` entity.
It contains **no business logic** - just persistence operations (create, fetch,
update). Transaction boundaries are owned by the service layer, which passes in
an already-bound :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from user.exceptions import ProfileNotFound
from user.models import UserProfile
from user.schemas import PreferencesUpdateRequest, ProfileUpdateRequest


class UserProfileRepository:
    """Async persistence for :class:`UserProfile`."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to a request-scoped session."""
        self._session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> UserProfile | None:
        """Return the profile for ``user_id`` or ``None`` if absent."""
        result = await self._session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_raise(self, user_id: uuid.UUID) -> UserProfile:
        """Return the profile for ``user_id`` or raise.

        Raises:
            ProfileNotFound: When no profile exists for the user.
        """
        profile = await self.get_by_user_id(user_id)
        if profile is None:
            raise ProfileNotFound(f"No profile found for user {user_id}.")
        return profile

    async def create(self, user_id: uuid.UUID) -> UserProfile:
        """Create a default profile for ``user_id``.

        The caller owns the enclosing transaction. The new row is flushed so
        its generated columns are populated without committing.
        """
        profile = UserProfile(user_id=user_id)
        self._session.add(profile)
        await self._session.flush()
        return profile

    async def update(
        self,
        profile: UserProfile,
        payload: ProfileUpdateRequest | PreferencesUpdateRequest,
    ) -> UserProfile:
        """Apply the non-``None`` fields of ``payload`` to ``profile``.

        Validation of the values has already happened in the schema/serializer;
        this method only assigns. The caller commits the transaction.
        """
        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(profile, field, value)
        await self._session.flush()
        return profile
