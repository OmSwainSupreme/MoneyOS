"""Authentication and user routes.

Exposes the identity endpoints:
    POST /auth/register
    POST /auth/login
    POST /auth/refresh
    POST /auth/logout
    GET  /users/me

Routes delegate all logic to :class:`~auth.service.AuthService` and raise the
service's domain exceptions directly; :func:`core.errors.register_exception_handlers`
translates them into the unified error envelope. No ORM or repository access
happens here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, status

from auth.dependencies import AuthServiceDep, CurrentUserDep
from auth.schemas import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RegisterRequest,
    TokenPair,
    TokenRefreshRequest,
    UserPublic,
)

# ``SettingsDep`` is imported lazily to avoid an import cycle:
# ``api.dependencies`` -> ``api`` -> ``api.router`` -> ``auth.router`` ->
# back into ``api.dependencies``. It is only referenced in the ``logout``
# route signature, so a deferred import is safe.
if TYPE_CHECKING:
    from api.dependencies import SettingsDep

# Auth endpoints live under /auth; /users/me is mounted separately below.
auth_router = APIRouter(prefix="/auth", tags=["auth"])
user_router = APIRouter(tags=["users"])


@auth_router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    auth_service: AuthServiceDep,
) -> UserPublic:
    """Create a new account and return its public projection."""
    return await auth_service.register(payload)


@auth_router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest,
    auth_service: AuthServiceDep,
) -> TokenPair:
    """Authenticate and return an access/refresh token pair."""
    return await auth_service.authenticate(payload)


@auth_router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: TokenRefreshRequest,
    auth_service: AuthServiceDep,
) -> TokenPair:
    """Exchange a refresh token for a fresh access/refresh pair."""
    return await auth_service.refresh(payload)


@auth_router.post("/logout", response_model=MessageResponse)
async def logout(
    _payload: LogoutRequest,
) -> MessageResponse:
    """Acknowledge logout.

    JWT auth is stateless, so the client discards its tokens; no server-side
    session is cleared in this phase. The route requires authentication but
    does no work, so no settings dependency is needed here.
    """
    return MessageResponse(
        message="Logged out. Discard your tokens client-side."
    )


@user_router.get("/users/me", response_model=UserPublic)
async def read_current_user(current_user: CurrentUserDep) -> UserPublic:
    """Return the authenticated user resolved from the bearer token."""
    return current_user
