"""Integration tests for the user profile/preferences API endpoints.

These build an in-process FastAPI app whose ``get_db_session`` dependency is
overridden to reuse a single test session (created via ``db_session``). The
current-user dependency is also overridden to a real user row. This exercises
the full HTTP surface: auth-protected access, profile read/update, preference
read/update, input validation (422), and the unified error envelope for domain
errors (404 profile_not_found).
"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.dependencies import CurrentUserDep
from auth.models import User as AuthUser
from auth.security import create_access_token
from core.config import get_settings
from database.session import get_db_session
from user.service import UserService

from tests.factories import make_user

pytestmark = pytest.mark.requires_postgres


def _build_client(db_session, user: AuthUser) -> TestClient:
    """Construct a TestClient bound to ``db_session`` and ``user``."""
    from user.router import user_router

    app = FastAPI()

    def _override_session():
        # Reuse the exact session object the test controls.
        with _reuse(db_session) as s:
            yield s

    async def _override_current_user() -> AuthUser:
        return user

    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[CurrentUserDep] = _override_current_user
    app.include_router(user_router)

    import contextlib

    @contextlib.contextmanager
    def _reuse(session):
        yield session

    # Attach helpers for the test body.
    client = TestClient(app)
    client._user = user  # type: ignore[attr-defined]
    client._session = db_session  # type: ignore[attr-defined]
    return client


def _auth_headers(user_id) -> dict[str, str]:
    token = create_access_token(user_id, get_settings())
    return {"Authorization": f"Bearer {token}"}


def _create_profile(client) -> None:
    """Auto-create the fixture user's profile via the service layer."""
    svc = UserService(client._session)  # type: ignore[attr-defined]
    asyncio.get_event_loop().run_until_complete(svc.create_profile(client._user.id))  # type: ignore[attr-defined]


@pytest.fixture
def client(db_session) -> TestClient:
    """A TestClient bound to a user created for the test."""
    user = asyncio.get_event_loop().run_until_complete(make_user(db_session))
    return _build_client(db_session, user)


def test_get_profile_returns_404_when_no_profile(client) -> None:
    """GET /users/me/profile yields the unified 404 envelope pre-profile."""
    resp = client.get("/users/me/profile")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "profile_not_found"


def test_create_then_get_profile(client) -> None:
    """A profile is auto-created and then readable via GET."""
    _create_profile(client)
    resp = client.get("/users/me/profile")
    assert resp.status_code == 200
    assert "display_name" in resp.json()


def test_update_profile_validation_error(client) -> None:
    """PATCH /users/me/profile with a bad avatar_url -> 422 envelope."""
    _create_profile(client)
    resp = client.patch(
        "/users/me/profile",
        json={"avatar_url": "ftp://not-allowed"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_update_preferences_rejects_bad_currency(client) -> None:
    """PATCH /users/me/preferences with unsupported currency -> 422."""
    _create_profile(client)
    resp = client.patch(
        "/users/me/preferences",
        json={"currency": "JPY"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_update_preferences_success(client) -> None:
    """PATCH /users/me/preferences with valid values persists them."""
    _create_profile(client)
    resp = client.patch(
        "/users/me/preferences",
        json={"currency": "USD", "theme": "dark"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["currency"] == "USD"
    assert body["theme"] == "dark"
