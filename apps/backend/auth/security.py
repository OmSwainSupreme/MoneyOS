"""Cryptographic primitives for authentication.

Two concerns live here, kept free of business logic:

* Password hashing with **Argon2id** (via ``argon2-cffi``). Argon2id is the
  OWASP-recommended algorithm for password storage; we chose it over bcrypt
  because the spec prefers it and ``argon2-cffi`` ships a clean, modern API
  with sane defaults - no fragile ``passlib``/bcrypt version coupling.
* JWT issuance and verification for access and refresh tokens (via
  ``PyJWT``). Token *meaning* (claims, lifetimes) is defined here; *policy*
  (when to mint a pair, what to do on refresh) lives in the service layer.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from core.config import Settings, get_settings

# Token types stamped into the JWT ``type`` claim so a refresh token can never
# be replayed against an access-token-protected endpoint.
TokenType = Literal["access", "refresh"]

# Precomputed Argon2id digest used to equalize login latency when the target
# user does not exist. Verifying against this constant-cost hash prevents
# user-enumeration via timing differences (see :func:`verify_password`).
_DUMMY_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$"
    "Z2l2ZW5uYW1lZHVtbXloYXNoZHVtbXloYXNoZA"
    "$kEM5fLUlhZkXS3qNxL8r1hL0wIb9J1Q6JZ6jZ8lJ9wA"
)

# Argon2id hasher. Defaults (memory=2**16 KiB, parallelism=4, time=3) follow
# the argon2-cffi recommended profile and are adequate for interactive logins.
_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    """Return an Argon2id digest for ``plain``.

    Args:
        plain: The cleartext password.

    Returns:
        The encoded Argon2id hash string (includes salt + parameters).
    """
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify ``plain`` against an Argon2id ``hashed`` digest.

    Never raises on a malformed hash - returns ``False`` so the caller can
    translate it into invalid-credentials without leaking hash internals.

    Args:
        plain: The cleartext password to check.
        hashed: The stored Argon2id hash.

    Returns:
        ``True`` when the password matches.
    """
    try:
        return _hasher.verify(hashed, plain)
    except (VerifyMismatchError, InvalidHashError, Exception):  # noqa: BLE001
        return False


def verify_against_dummy(plain: str) -> None:
    """Run a constant-cost Argon2id verification against a dummy hash.

    Called when a login targets an unknown user so the response latency
    matches a real credential check, defeating user-enumeration timing
    attacks. The result is discarded; callers always return invalid
    credentials afterwards.

    Args:
        plain: The cleartext password from the login attempt.
    """
    # The outcome is intentionally unused; we only burn CPU proportional to a
    # real verification so timing does not leak account existence.
    verify_password(plain, _DUMMY_HASH)


def _now() -> datetime:
    """Return the current UTC time (timezone-aware)."""
    return datetime.now(UTC)


def _create_token(
    *,
    subject: uuid.UUID,
    token_type: TokenType,
    settings: Settings,
    expires_delta: timedelta,
) -> str:
    """Build a signed JWT for the given subject and type.

    Args:
        subject: The user id the token is bound to.
        token_type: ``"access"`` or ``"refresh"``.
        settings: Application settings (secret + issuer).
        expires_delta: Token lifetime.

    Returns:
        The encoded JWT string.
    """
    issued_at = _now()
    payload = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + expires_delta).timestamp()),
        "iss": settings.service_name,
    }
    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm="HS256",
    )


def create_access_token(
    subject: uuid.UUID, settings: Settings | None = None
) -> str:
    """Mint a short-lived access token (15 minutes)."""
    resolved = settings or get_settings()
    return _create_token(
        subject=subject,
        token_type="access",
        settings=resolved,
        expires_delta=timedelta(minutes=resolved.access_token_expire_minutes),
    )


def create_refresh_token(
    subject: uuid.UUID, settings: Settings | None = None
) -> str:
    """Mint a long-lived refresh token.

    Lifetime is configurable via ``Settings.refresh_token_expire_days``
    (default 7 days); it is intentionally decoupled from the access lifetime.
    """
    resolved = settings or get_settings()
    return _create_token(
        subject=subject,
        token_type="refresh",
        settings=resolved,
        expires_delta=timedelta(days=resolved.refresh_token_expire_days),
    )


def decode_token(token: str, settings: Settings | None = None) -> dict:
    """Decode and validate a JWT, returning its claims.

    Args:
        token: The encoded JWT.
        settings: Application settings (secret + issuer).

    Returns:
        The decoded claims dict.

    Raises:
        jwt.InvalidTokenError: When the signature, expiry, issuer, or shape is
            invalid. Callers map this to a 401.
    """
    resolved = settings or get_settings()
    return jwt.decode(
        token,
        resolved.secret_key,
        algorithms=["HS256"],
        issuer=resolved.service_name,
        options={"require": ["exp", "sub", "type"]},
    )
