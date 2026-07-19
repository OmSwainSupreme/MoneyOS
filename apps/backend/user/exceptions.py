"""User-domain (profile/preferences) exceptions.

Plain domain errors raised by the user service/repository. The router maps
them to HTTP responses; the exceptions themselves carry no status codes so
business logic stays transport-agnostic.
"""

from __future__ import annotations


class UserError(Exception):
    """Base class for all user-module failures."""


class ProfileNotFound(UserError):
    """Raised when a profile is missing for an otherwise-valid user."""


class UnsupportedCurrency(UserError):
    """Raised when a requested currency code is not supported."""


class InvalidPreference(UserError):
    """Raised when a preference value fails validation.

    Covers theme, language, date format, timezone, etc.
    """
