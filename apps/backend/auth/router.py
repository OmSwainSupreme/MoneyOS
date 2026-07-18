"""Authentication and user routes.

Exposes the identity endpoints:
    POST /auth/register
    POST /auth/login
    POST /auth/refresh
    POST /auth/logout
    GET  /users/me

Routes translate service-layer domain errors into HTTP responses and delegate
all logic to :class:`~auth.service.AuthService`. No ORM or repository access
happens here.
"""

from __future__ import annotations

from api.dependencies import SettingsDep
from fastapi import APIRouter, HTTPException, status

from auth.dependencies import AuthServiceDep, CurrentUserDep
from auth.exceptions import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenTypeError,
)
from auth.schemas import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RegisterRequest,
    TokenPair,
    TokenRefreshRequest,
    UserPublic,
)

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
    try:
        return await auth_service.register(payload)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "email_taken", "message": str(exc)},
        ) from exc


@auth_router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest,
    auth_service: AuthServiceDep,
) -> TokenPair:
    """Authenticate and return an access/refresh token pair."""
    try:
        return await auth_service.authenticate(payload)
    except (InvalidCredentialsError, InactiveUserError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "message": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@auth_router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: TokenRefreshRequest,
    auth_service: AuthServiceDep,
) -> TokenPair:
    """Exchange a refresh token for a fresh access/refresh pair."""
    try:
        return await auth_service.refresh(payload)
    except (InvalidTokenError, TokenTypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token", "message": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@auth_router.post("/logout", response_model=MessageResponse)
async def logout(
    _payload: LogoutRequest,
    _settings: SettingsDep,
) -> MessageResponse:
    """Acknowledge logout.

    JWT auth is stateless, so the client discards its tokens; no server-side
    session is cleared in this phase.
    """
    return MessageResponse(
        message="Logged out. Discard your tokens client-side."
    )


@user_router.get("/users/me", response_model=UserPublic)
async def read_current_user(current_user: CurrentUserDep) -> UserPublic:
    """Return the authenticated user resolved from the bearer token."""
    return current_user
