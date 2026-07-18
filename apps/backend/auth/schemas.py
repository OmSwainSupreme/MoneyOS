"""Pydantic v2 schemas for the authentication API.

Request and response models live here so the route layer only speaks in typed
contracts. Domain entities (:class:`~auth.models.User`) are never serialized
directly - the service layer maps between ORM models and these schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Password policy (centralized for reuse and frontend parity).
PASSWORD_MIN_LENGTH: int = 8
PASSWORD_MAX_LENGTH: int = 128
PASSWORD_MIN_UPPER: int = 1
PASSWORD_MIN_LOWER: int = 1
PASSWORD_MIN_DIGIT: int = 1
PASSWORD_MIN_SPECIAL: int = 1

_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"


def validate_password_strength(password: str) -> str:
    """Enforce the password policy, returning ``password`` if it passes.

    Args:
        password: The cleartext password to validate.

    Returns:
        The unchanged ``password`` when every rule is satisfied.

    Raises:
        ValueError: With a human-readable message listing the first failing
            requirement(s) when the password is too weak.
    """
    problems: list[str] = []
    if len(password) < PASSWORD_MIN_LENGTH:
        problems.append(f"at least {PASSWORD_MIN_LENGTH} characters")
    if sum(1 for c in password if c.isupper()) < PASSWORD_MIN_UPPER:
        problems.append("an uppercase letter")
    if sum(1 for c in password if c.islower()) < PASSWORD_MIN_LOWER:
        problems.append("a lowercase letter")
    if sum(1 for c in password if c.isdigit()) < PASSWORD_MIN_DIGIT:
        problems.append("a number")
    if sum(1 for c in password if c in _SPECIAL_CHARS) < PASSWORD_MIN_SPECIAL:
        problems.append("a special character")

    if problems:
        raise ValueError("Password must contain " + ", ".join(problems) + ".")
    return password


class RegisterRequest(BaseModel):
    """Payload for ``POST /auth/register``."""

    email: EmailStr = Field(..., max_length=320)
    password: str = Field(
        ...,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
    )
    full_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        return validate_password_strength(value)


class LoginRequest(BaseModel):
    """Payload for ``POST /auth/login``."""

    email: EmailStr = Field(..., max_length=320)
    password: str = Field(..., min_length=1, max_length=PASSWORD_MAX_LENGTH)


class TokenRefreshRequest(BaseModel):
    """Payload for ``POST /auth/refresh``."""

    refresh_token: str = Field(..., min_length=1)


class LogoutRequest(BaseModel):
    """Payload for ``POST /auth/logout``.

    The access token is invalidated by the client discarding it; stateless JWT
    auth has no server-side session to clear, so this confirms the contract.
    """

    refresh_token: str | None = Field(default=None)


class TokenPair(BaseModel):
    """Access + refresh token response returned on login and refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    """Public projection of a user, safe to return to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    """Generic acknowledgement body."""

    message: str
