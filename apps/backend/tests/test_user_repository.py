"""Functional tests for the UserProfileRepository and UserService.

These run against a real PostgreSQL session (see ``conftest.py``) and cover
create, fetch-or-raise, partial merge updates, and the guarantee that every
user gets a profile with valid server defaults.
"""

from __future__ import annotations

import uuid

import pytest

from user.exceptions import ProfileNotFound
from user.models import UserProfile
from user.repository import UserProfileRepository
from user.schemas import PreferencesUpdateRequest, ProfileUpdateRequest
from user.service import UserService

from tests.factories import make_user

pytestmark = pytest.mark.requires_postgres


async def test_create_profile_persists_with_server_defaults(
    db_session,
) -> None:
    """A profile created via the repository inherits server defaults."""
    user = await make_user(db_session)
    repo = UserProfileRepository(db_session)
    profile = await repo.create(user.id)
    await db_session.commit()

    fetched = await repo.get_by_user_id(user.id)
    assert fetched is not None
    assert fetched.id == profile.id
    assert fetched.display_name == "New User"
    assert fetched.currency == "INR"
    assert fetched.language == "en"
    assert fetched.date_format == "DD/MM/YYYY"
    assert fetched.theme == "system"
    assert fetched.timezone == "UTC"


async def test_get_or_raise_raises_when_missing(db_session) -> None:
    """get_or_raise raises ProfileNotFound for an unknown user."""
    repo = UserProfileRepository(db_session)
    with pytest.raises(ProfileNotFound):
        await repo.get_or_raise(uuid.uuid4())


async def test_update_partial_merge_preserves_other_fields(
    db_session,
) -> None:
    """An omitted field is left unchanged by a partial update."""
    user = await make_user(db_session)
    repo = UserProfileRepository(db_session)
    profile = await repo.create(user.id)
    await db_session.commit()

    updated = await repo.update(
        profile, ProfileUpdateRequest(display_name="Renamed")
    )
    assert updated.display_name == "Renamed"
    # currency/theme untouched
    assert updated.currency == "INR"
    assert updated.theme == "system"


async def test_service_create_profile_autocreates(db_session) -> None:
    """UserService.create_profile yields a persisted, defaulted profile."""
    user = await make_user(db_session)
    service = UserService(db_session)
    async with _txn(db_session):
        profile = await service.create_profile(user.id)
    assert isinstance(profile, UserProfile)
    assert profile.user_id == user.id


async def test_service_get_profile_raises_not_found(db_session) -> None:
    """UserService.get_profile surfaces ProfileNotFound as a 404-class error."""
    service = UserService(db_session)
    with pytest.raises(ProfileNotFound):
        await service.get_profile(uuid.uuid4())


async def test_service_update_preferences_partial(db_session) -> None:
    """UserService.update_preferences merges without clobbering others."""
    user = await make_user(db_session)
    service = UserService(db_session)
    async with _txn(db_session):
        await service.create_profile(user.id)

    async with _txn(db_session):
        result = await service.update_preferences(
            user.id, PreferencesUpdateRequest(currency="USD", theme="dark")
        )
    assert result.currency == "USD"
    assert result.theme == "dark"
    # language/day_format left at defaults
    assert result.language == "en"
    assert result.date_format == "DD/MM/YYYY"


async def _txn(session):
    """Lightweight commit-on-exit context manager for tests."""
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _cm():
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    async with _cm() as s:
        yield s
