"""Auth business logic and transaction orchestration.

The service owns transaction boundaries (see
:func:`database.session.transaction`) and enforces auth-domain rules:
duplicate-email rejection, credential checks, active-user enforcement, and
token-type validation. It depends on the repository for persistence and on the
security module for crypto. Routes never call the repository or ORM directly.
"""

from __future__ import annotations

import uuid

from core.config import Settings
from database.session import transaction
from sqlalchemy.ext.asyncio import AsyncSession

from auth.exceptions import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenTypeError,
)
from auth.repository import UserRepository
from auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenPair,
    TokenRefreshRequest,
    UserPublic,
)
from auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_against_dummy,
    verify_password,
)


class AuthService:
    """Coordinates identity operations across repository and security."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        """Bind the session, settings, and a user repository."""
        self._session = session
        self._settings = settings
        self._users = UserRepository(session)

    async def register(self, payload: RegisterRequest) -> UserPublic:
        """Register a new user and return its public projection.

        A default :class:`~user.models.UserProfile` is created inside the same
        transaction so the system never holds a user without a profile. The
        user module is imported lazily to keep the auth and user packages
        decoupled (neither imports the other at module load time).

        Raises:
            EmailAlreadyRegisteredError: When the email is already taken.
        """
        if await self._users.email_exists(payload.email):
            raise EmailAlreadyRegisteredError(
                "A user with this email already exists."
            )
        password_hash = hash_password(payload.password)
        from user.service import UserService

        async with transaction(self._session):
            user = await self._users.create(payload, password_hash)
            await UserService(self._session).create_profile(user.id)
        return UserPublic.model_validate(user)

    async def authenticate(self, payload: LoginRequest) -> TokenPair:
        """Validate credentials and mint an access/refresh token pair.

        Raises:
            InvalidCredentialsError: On unknown email or wrong password.
            InactiveUserError: When the matched user is disabled.
        """
        user = await self._users.get_by_email(payload.email)
        if user is None:
            # Constant-cost dummy verification so response latency matches a
            # real credential check; prevents user enumeration via timing.
            verify_against_dummy(payload.password)
            raise InvalidCredentialsError("Invalid email or password.")
        if not verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")
        if not user.is_active:
            raise InactiveUserError("This account is inactive.")
        return self._issue_tokens(user.id)

    async def refresh(self, payload: TokenRefreshRequest) -> TokenPair:
        """Exchange a valid refresh token for a fresh token pair.

        Raises:
            InvalidTokenError: On malformed/expired/untrusted token.
            TokenTypeError: When the presented token is not a refresh token.
        """
        claims = self._decode_and_require(
            payload.refresh_token, expected="refresh"
        )
        user = await self._users.get_by_id(uuid.UUID(claims["sub"]))
        if user is None or not user.is_active:
            raise InvalidTokenError("Token subject is no longer valid.")
        return self._issue_tokens(user.id)

    async def get_current_user(self, token: str) -> UserPublic:
        """Resolve the authenticated user from an access token.

        Raises:
            InvalidTokenError: On malformed/expired/untrusted token.
            TokenTypeError: When the presented token is not an access token.
        """
        claims = self._decode_and_require(token, expected="access")
        user = await self._users.get_by_id(uuid.UUID(claims["sub"]))
        if user is None:
            raise InvalidTokenError("Token subject is no longer valid.")
        return UserPublic.model_validate(user)

    # --- internal helpers -------------------------------------------------

    def _issue_tokens(self, subject: uuid.UUID) -> TokenPair:
        """Build a :class:`TokenPair` for ``subject``."""
        return TokenPair(
            access_token=create_access_token(subject, self._settings),
            refresh_token=create_refresh_token(subject, self._settings),
        )

    def _decode_and_require(self, token: str, *, expected: str) -> dict:
        """Decode ``token`` and assert its ``type`` matches ``expected``."""
        try:
            claims = decode_token(token, self._settings)
        except Exception as exc:  # noqa: BLE001 - normalize to our domain error.
            raise InvalidTokenError("Token is invalid or expired.") from exc
        if claims.get("type") != expected:
            raise TokenTypeError(
                f"Expected a {expected} token, got {claims.get('type')!r}."
            )
        return claims
