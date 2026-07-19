"""User (profile/preferences) business logic and transaction orchestration.

The service owns transaction boundaries (via
:func:`database.session.transaction`) and enforces user-domain rules:
guaranteeing a profile exists for every user, validating preference values
against the supported whitelists, and merging partial updates without
clobbering unset fields. It depends on the repository for persistence and
never touches the ORM directly.
"""

from __future__ import annotations

import uuid

from database.session import transaction
from sqlalchemy.ext.asyncio import AsyncSession

from user.models import UserProfile
from user.repository import UserProfileRepository
from user.schemas import (
    PreferencesResponse,
    PreferencesUpdateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)


class UserService:
    """Coordinates profile/preference operations across the repository.

    The repository is injected (Dependency Inversion) rather than constructed
    inline, so the persistence layer can be swapped or mocked from the
    composition root without touching business logic.
    """

    def __init__(
        self,
        session: AsyncSession,
        repository: UserProfileRepository | None = None,
    ) -> None:
        """Bind the session and (optionally injected) repository."""
        self._session = session
        self._users = repository or UserProfileRepository(session)

    async def create_profile(self, user_id: uuid.UUID) -> UserProfile:
        """Create a default profile for a freshly registered user.

        Intended to run inside the registration transaction so the profile and
        user are committed atomically; the system never holds a user without a
        profile.
        """
        return await self._users.create(user_id)

    async def get_profile(self, user_id: uuid.UUID) -> ProfileResponse:
        """Return the user's profile, raising if it is missing."""
        profile = await self._users.get_or_raise(user_id)
        return ProfileResponse.model_validate(profile)

    async def update_profile(
        self, user_id: uuid.UUID, payload: ProfileUpdateRequest
    ) -> ProfileResponse:
        """Merge a partial profile update inside a transaction."""
        profile = await self._users.get_or_raise(user_id)
        async with transaction(self._session):
            profile = await self._users.update(profile, payload)
        return ProfileResponse.model_validate(profile)

    async def get_preferences(self, user_id: uuid.UUID) -> PreferencesResponse:
        """Return the user's preferences, raising if the profile is missing."""
        profile = await self._users.get_or_raise(user_id)
        return PreferencesResponse.model_validate(profile)

    async def update_preferences(
        self, user_id: uuid.UUID, payload: PreferencesUpdateRequest
    ) -> PreferencesResponse:
        """Merge a partial preferences update inside a transaction.

        Values were already validated by :class:`PreferencesUpdateRequest`. The
        merge is field-by-field so omitted preferences are preserved.
        """
        profile = await self._users.get_or_raise(user_id)
        async with transaction(self._session):
            profile = await self._users.update(profile, payload)
        return PreferencesResponse.model_validate(profile)
