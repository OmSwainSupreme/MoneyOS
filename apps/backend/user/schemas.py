"""Pydantic v2 schemas for the user (profile/preferences) API.

Request and response models are kept separate. Request models validate input
on the way in (currency/theme/language/date-format whitelists, IANA timezone
via :mod:`zoneinfo`); response models project the stored profile back to the
client. Preference constants are mirrored from :mod:`user.models` so the API
surface cannot drift from the persistence layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, available_timezones

from pydantic import BaseModel, ConfigDict, Field, field_validator

from user.models import (
    CURRENCIES,
    DATE_FORMATS,
    LANGUAGES,
    THEMES,
)

_VALID_TIMEZONES = available_timezones()


def _validate_avatar_url(value: str | None) -> str | None:
    """Validate avatar URL is a proper HTTP/HTTPS URL.

    Mirrors the database CHECK constraint
    ``check_user_profiles_valid_avatar_url`` so Pydantic rejects bad input
    with a 422 instead of letting it reach the DB and raise a 500.
    An empty string is normalized to ``None`` (clears the avatar).
    """
    if value is None or value.strip() == "":
        return None
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(
            "avatar_url must be a valid absolute HTTP/HTTPS URL "
            "(e.g. 'https://example.com/avatar.png')."
        )
    return value.strip()


class ProfileResponse(BaseModel):
    """Read projection of a user's profile."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str
    avatar_url: str | None
    timezone: str
    created_at: datetime
    updated_at: datetime


class ProfileUpdateRequest(BaseModel):
    """Partial profile update.

    All fields optional; ``None`` means unchanged.
    """

    display_name: str | None = Field(
        default=None, min_length=1, max_length=255
    )
    avatar_url: str | None = Field(default=None, max_length=2048)

    @field_validator("display_name")
    @classmethod
    def _validate_display_name(cls, value: str | None) -> str | None:
        """Trim whitespace and reject empty strings."""
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("display_name cannot be empty or whitespace only")
        return stripped

    @field_validator("avatar_url")
    @classmethod
    def _validate_avatar_url(cls, value: str | None) -> str | None:
        """Validate avatar URL is a valid HTTP/HTTPS URL."""
        return _validate_avatar_url(value)


class PreferencesResponse(BaseModel):
    """Read projection of a user's preferences."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    currency: str
    language: str
    date_format: str
    theme: str
    timezone: str


class PreferencesUpdateRequest(BaseModel):
    """Partial preferences update.

    All fields optional; ``None`` means unchanged.
    """

    currency: str | None = None
    language: str | None = None
    date_format: str | None = None
    theme: str | None = None
    timezone: str | None = None

    @field_validator("currency")
    @classmethod
    def _validate_currency(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in CURRENCIES:
            raise ValueError(
                f"Unsupported currency {value!r}. Supported: "
                + ", ".join(CURRENCIES)
                + "."
            )
        return value

    @field_validator("language")
    @classmethod
    def _validate_language(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in LANGUAGES:
            raise ValueError(
                f"Unsupported language {value!r}. Supported: "
                + ", ".join(LANGUAGES)
                + "."
            )
        return value

    @field_validator("date_format")
    @classmethod
    def _validate_date_format(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in DATE_FORMATS:
            raise ValueError(
                f"Unsupported date format {value!r}. Supported: "
                + ", ".join(DATE_FORMATS)
                + "."
            )
        return value

    @field_validator("theme")
    @classmethod
    def _validate_theme(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in THEMES:
            raise ValueError(
                f"Unsupported theme {value!r}. Supported: "
                + ", ".join(THEMES)
                + "."
            )
        return value

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in _VALID_TIMEZONES:
            raise ValueError(
                f"Unknown timezone {value!r}. Use an IANA timezone name "
                "(e.g. 'Asia/Kolkata')."
            )
        # Return the canonical key; ZoneInfo normalizes aliases.
        return ZoneInfo(value).key
