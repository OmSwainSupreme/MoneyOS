"""Unit tests for the UserProfile model metadata and request schemas.

These tests need no database: they assert the class-level contract (CHECK
constraints registered on the table and the declared server defaults) and the
Pydantic ingress validation that mirrors the database constraints.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from user.models import UserProfile
from user.schemas import PreferencesUpdateRequest, ProfileUpdateRequest

# The MetaData naming_convention (database.base) prefixes CHECK constraints
# with ``ck_<table>_``; the migration DDL uses the identical resolved names so
# create_all and Alembic produce the same schema.
_EXPECTED_CHECKS = {
    "ck_user_profiles_check_user_profiles_currency",
    "ck_user_profiles_check_user_profiles_theme",
    "ck_user_profiles_check_user_profiles_language",
    "ck_user_profiles_check_user_profiles_date_format",
    "ck_user_profiles_check_user_profiles_non_empty_display_name",
    "ck_user_profiles_check_user_profiles_valid_avatar_url",
}


def test_profile_check_constraints_registered() -> None:
    """Every data-integrity CHECK constraint is present on the table."""
    constraint_names = {c.name for c in UserProfile.__table__.constraints}
    assert _EXPECTED_CHECKS.issubset(constraint_names)


def _server_default(column_name: str) -> str:
    """Return the literal server_default for a column (create_all form)."""
    column = UserProfile.__table__.columns[column_name]
    assert column.server_default is not None
    return column.server_default.arg


def test_profile_server_defaults() -> None:
    """Server-side defaults match the expected canonical values."""
    assert _server_default("display_name") == "New User"
    assert _server_default("currency") == "INR"
    assert _server_default("language") == "en"
    assert _server_default("date_format") == "DD/MM/YYYY"
    assert _server_default("theme") == "system"
    assert _server_default("timezone") == "UTC"


def test_profile_not_null_columns() -> None:
    """Required columns are non-nullable."""
    for name in (
        "display_name",
        "timezone",
        "currency",
        "language",
        "date_format",
        "theme",
    ):
        assert UserProfile.__table__.columns[name].nullable is False


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("  Alice  ", "Alice"),  # surrounding whitespace trimmed
        ("Bob", "Bob"),
    ],
)
def test_display_name_trims_whitespace(raw: str, expected: str) -> None:
    """display_name is trimmed on ingress."""
    payload = ProfileUpdateRequest(display_name=raw)
    assert payload.display_name == expected


@pytest.mark.parametrize("bad", ["", "   ", "\t\n"])
def test_display_name_rejects_empty(bad: str) -> None:
    """Whitespace-only display_name is rejected (mirrors DB CHECK)."""
    with pytest.raises(ValidationError):
        ProfileUpdateRequest(display_name=bad)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/avatar.png",
        "http://cdn.local/img.jpg",
        "https://sub.example.com/path/to/a?q=1",
    ],
)
def test_avatar_url_accepts_http_https(url: str) -> None:
    """Valid absolute HTTP/HTTPS avatar URLs are accepted."""
    payload = ProfileUpdateRequest(avatar_url=url)
    assert payload.avatar_url == url


@pytest.mark.parametrize("bad", ["ftp://x", "not-a-url", "javascript:alert(1)"])
def test_avatar_url_rejects_non_http(bad: str) -> None:
    """Non-HTTP/HTTPS avatar URLs are rejected before reaching the DB.

    The empty string is intentionally excluded here: it normalizes to ``None``
    (see ``test_avatar_url_empty_becomes_none``) to support clearing an avatar.
    """
    with pytest.raises(ValidationError):
        ProfileUpdateRequest(avatar_url=bad)


def test_avatar_url_empty_becomes_none() -> None:
    """An empty avatar_url normalizes to None (clears the avatar)."""
    payload = ProfileUpdateRequest(avatar_url="")
    assert payload.avatar_url is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("currency", "JPY"),
        ("language", "fr"),
        ("theme", "neon"),
        ("date_format", "MM-YY-DD"),
    ],
)
def test_preferences_reject_unsupported_values(field: str, value: str) -> None:
    """Unsupported preference values are rejected by the schema."""
    with pytest.raises(ValidationError):
        PreferencesUpdateRequest(**{field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("currency", "USD"),
        ("language", "hi"),
        ("theme", "dark"),
        ("date_format", "MM/DD/YYYY"),
        ("timezone", "Asia/Kolkata"),
    ],
)
def test_preferences_accept_supported_values(field: str, value: str) -> None:
    """Supported preference values pass validation."""
    payload = PreferencesUpdateRequest(**{field: value})
    assert getattr(payload, field) == value
