"""Auth-domain exceptions.

These are plain domain errors raised by the service/repository layers. The
router translates them into HTTP responses - the exceptions themselves carry
no status codes so business logic stays transport-agnostic.
"""

from __future__ import annotations


class AuthError(Exception):
    """Base class for all authentication/authorization failures."""


class EmailAlreadyRegisteredError(AuthError):
    """Raised when a registration collides with an existing email."""


class InvalidCredentialsError(AuthError):
    """Raised when email/password do not match a known active account."""


class InactiveUserError(AuthError):
    """Raised when an otherwise-valid credential belongs to a disabled user."""


class InvalidTokenError(AuthError):
    """Raised when a JWT is malformed, expired, or fails validation."""


class TokenTypeError(AuthError):
    """Raised when a token of the wrong ``type`` is presented."""
