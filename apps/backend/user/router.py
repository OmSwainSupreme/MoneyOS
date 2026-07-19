"""User (profile/preferences) routes.

Exposes the profile/preference endpoints:
    GET    /users/me/profile
    PATCH  /users/me/profile
    GET    /users/me/preferences
    PATCH  /users/me/preferences

All routes require authentication (the current user is injected). The router
delegates all logic to :class:`~user.service.UserService` and raises the
service's domain exceptions directly; :func:`core.errors.register_exception_handlers`
translates them into the unified error envelope. No ORM, repository, or
try/except access happens here.
"""

from __future__ import annotations

from fastapi import APIRouter

from user.dependencies import CurrentUser, UserServiceDep
from user.schemas import (
    PreferencesResponse,
    PreferencesUpdateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)

user_router = APIRouter(prefix="/users/me", tags=["user"])


@user_router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: CurrentUser,
    user_service: UserServiceDep,
) -> ProfileResponse:
    """Return the authenticated user's profile."""
    return await user_service.get_profile(current_user.id)


@user_router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user: CurrentUser,
    user_service: UserServiceDep,
) -> ProfileResponse:
    """Update the authenticated user's profile (partial)."""
    return await user_service.update_profile(current_user.id, payload)


@user_router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(
    current_user: CurrentUser,
    user_service: UserServiceDep,
) -> PreferencesResponse:
    """Return the authenticated user's preferences."""
    return await user_service.get_preferences(current_user.id)


@user_router.patch("/preferences", response_model=PreferencesResponse)
async def update_preferences(
    payload: PreferencesUpdateRequest,
    current_user: CurrentUser,
    user_service: UserServiceDep,
) -> PreferencesResponse:
    """Update the authenticated user's preferences (partial)."""
    return await user_service.update_preferences(current_user.id, payload)
