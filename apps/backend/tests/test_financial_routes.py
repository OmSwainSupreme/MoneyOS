"""Integration tests for the financial-domain REST endpoints.

Builds an in-process FastAPI app whose ``get_db_session`` dependency is
overridden to reuse a single test session, and whose current-user dependency is
overridden to a real user row. Exercises the full HTTP surface for accounts,
categories, and transactions: CRUD, 201/204 status codes, 422 validation
envelope, 404/403 domain envelopes, and filtering.
"""

from __future__ import annotations

import asyncio
import contextlib
import uuid

import pytest
from auth.dependencies import CurrentUserDep
from auth.models import User as AuthUser
from auth.security import create_access_token
from core.config import get_settings
from database.session import get_db_session
from fastapi import FastAPI
from fastapi.testclient import TestClient
from financial.router import (
    accounts_router,
    categories_router,
    transactions_router,
)

from tests.factories import make_account, make_user

pytestmark = pytest.mark.requires_postgres


def _build_client(db_session, user: AuthUser) -> TestClient:
    app = FastAPI()

    @contextlib.contextmanager
    def _override_session():
        yield db_session

    async def _override_current_user() -> AuthUser:
        return user

    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[CurrentUserDep] = _override_current_user
    app.include_router(accounts_router)
    app.include_router(categories_router)
    app.include_router(transactions_router)

    client = TestClient(app)
    client._user = user  # type: ignore[attr-defined]
    client._session = db_session  # type: ignore[attr-defined]
    return client


def _auth_headers(user_id) -> dict[str, str]:
    token = create_access_token(user_id, get_settings())
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(db_session) -> TestClient:
    """Build a test client bound to a fresh user and shared session."""
    user = asyncio.get_event_loop().run_until_complete(make_user(db_session))
    return _build_client(db_session, user)


# --- Accounts ----------------------------------------------------------------
def test_create_account_201(client) -> None:
    """Create account 201."""
    resp = client.post(
        "/accounts",
        headers=_auth_headers(client._user.id),
        json={"name": "Savings", "account_type": "savings"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Savings"
    assert body["currency"] == "INR"
    assert body["current_balance"] == 0


def test_create_account_rejects_bad_currency(client) -> None:
    """Create account rejects bad currency."""
    resp = client.post(
        "/accounts",
        headers=_auth_headers(client._user.id),
        json={"name": "X", "account_type": "savings", "currency": "JPY"},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_list_and_get_account(client) -> None:
    """List and get account."""
    created = client.post(
        "/accounts",
        headers=_auth_headers(client._user.id),
        json={"name": "Savings", "account_type": "savings"},
    ).json()
    list_resp = client.get(
        "/accounts", headers=_auth_headers(client._user.id)
    )
    assert list_resp.status_code == 200
    assert any(a["id"] == created["id"] for a in list_resp.json())

    get_resp = client.get(
        f"/accounts/{created['id']}", headers=_auth_headers(client._user.id)
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == created["id"]


def test_get_account_404(client) -> None:
    """Get account 404."""
    resp = client.get(
        f"/accounts/{uuid.uuid4()}", headers=_auth_headers(client._user.id)
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "account_not_found"


def test_update_account(client) -> None:
    """Update account."""
    created = client.post(
        "/accounts",
        headers=_auth_headers(client._user.id),
        json={"name": "Savings", "account_type": "savings"},
    ).json()
    resp = client.patch(
        f"/accounts/{created['id']}",
        headers=_auth_headers(client._user.id),
        json={"name": "Renamed", "is_active": False},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"
    assert resp.json()["is_active"] is False


def test_delete_account_204(client) -> None:
    """Delete account 204."""
    created = client.post(
        "/accounts",
        headers=_auth_headers(client._user.id),
        json={"name": "Temp", "account_type": "cash"},
    ).json()
    del_resp = client.delete(
        f"/accounts/{created['id']}", headers=_auth_headers(client._user.id)
    )
    assert del_resp.status_code == 204
    get_resp = client.get(
        f"/accounts/{created['id']}", headers=_auth_headers(client._user.id)
    )
    assert get_resp.status_code == 404


# --- Categories --------------------------------------------------------------
def test_create_category_includes_system_in_list(client) -> None:
    """Create category includes system in list."""
    created = client.post(
        "/categories",
        headers=_auth_headers(client._user.id),
        json={"name": "Food", "type": "expense", "color": "#AABBCC"},
    )
    assert created.status_code == 201
    lst = client.get(
        "/categories", headers=_auth_headers(client._user.id)
    ).json()
    # System categories are visible alongside the user's own.
    assert any(c["is_system"] for c in lst)
    assert any(c["id"] == created.json()["id"] for c in lst)


def test_create_category_rejects_bad_color(client) -> None:
    """Create category rejects bad color."""
    resp = client.post(
        "/categories",
        headers=_auth_headers(client._user.id),
        json={"name": "Food", "type": "expense", "color": "red"},
    )
    assert resp.status_code == 422


def test_delete_own_category_204(client) -> None:
    """Delete own category 204."""
    created = client.post(
        "/categories",
        headers=_auth_headers(client._user.id),
        json={"name": "Mine", "type": "expense"},
    ).json()
    resp = client.delete(
        f"/categories/{created['id']}",
        headers=_auth_headers(client._user.id),
    )
    assert resp.status_code == 204


# --- Transactions ------------------------------------------------------------
def test_create_transaction_updates_balance(client) -> None:
    """Create transaction updates balance."""
    acc = client.post(
        "/accounts",
        headers=_auth_headers(client._user.id),
        json={
            "name": "Savings",
            "account_type": "savings",
            "opening_balance": 500,
        },
    ).json()
    assert acc["current_balance"] == 500

    txn_resp = client.post(
        "/transactions",
        headers=_auth_headers(client._user.id),
        json={
            "account_id": acc["id"],
            "amount": 100,
            "transaction_type": "expense",
            "transaction_date": "2026-07-19T00:00:00Z",
        },
    )
    assert txn_resp.status_code == 201
    refetched = client.get(
        f"/accounts/{acc['id']}", headers=_auth_headers(client._user.id)
    ).json()
    assert refetched["current_balance"] == 400


def test_create_transaction_rejects_zero_amount(client) -> None:
    """Create transaction rejects zero amount."""
    acc = client.post(
        "/accounts",
        headers=_auth_headers(client._user.id),
        json={"name": "Savings", "account_type": "savings"},
    ).json()
    resp = client.post(
        "/transactions",
        headers=_auth_headers(client._user.id),
        json={
            "account_id": acc["id"],
            "amount": 0,
            "transaction_type": "expense",
            "transaction_date": "2026-07-19T00:00:00Z",
        },
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_create_transaction_rejects_other_users_account(client) -> None:
    """Create transaction rejects other users account."""
    # Create an account owned by a *different* user in the same session.
    other = asyncio.get_event_loop().run_until_complete(
        make_user(client._session, email="other-owner@example.com")
    )
    other_acc = asyncio.get_event_loop().run_until_complete(
        make_account(client._session, user_id=other.id)
    )
    resp = client.post(
        "/transactions",
        headers=_auth_headers(client._user.id),
        json={
            "account_id": str(other_acc.id),
            "amount": 10,
            "transaction_type": "expense",
            "transaction_date": "2026-07-19T00:00:00Z",
        },
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "account_not_found"


def test_list_transactions_with_filter(client) -> None:
    """List transactions with filter."""
    acc = client.post(
        "/accounts",
        headers=_auth_headers(client._user.id),
        json={"name": "Savings", "account_type": "savings"},
    ).json()
    client.post(
        "/transactions",
        headers=_auth_headers(client._user.id),
        json={
            "account_id": acc["id"],
            "amount": 50,
            "transaction_type": "income",
            "transaction_date": "2026-07-19T00:00:00Z",
        },
    )
    filtered = client.get(
        f"/transactions?account_id={acc['id']}&transaction_type=income",
        headers=_auth_headers(client._user.id),
    )
    assert filtered.status_code == 200
    body = filtered.json()
    assert len(body) == 1
    assert body[0]["transaction_type"] == "income"


def test_delete_transaction_204(client) -> None:
    """Delete transaction 204."""
    acc = client.post(
        "/accounts",
        headers=_auth_headers(client._user.id),
        json={
            "name": "Savings",
            "account_type": "savings",
            "opening_balance": 500,
        },
    ).json()
    txn = client.post(
        "/transactions",
        headers=_auth_headers(client._user.id),
        json={
            "account_id": acc["id"],
            "amount": 100,
            "transaction_type": "expense",
            "transaction_date": "2026-07-19T00:00:00Z",
        },
    ).json()
    del_resp = client.delete(
        f"/transactions/{txn['id']}", headers=_auth_headers(client._user.id)
    )
    assert del_resp.status_code == 204
    # Balance rolled back.
    refetched = client.get(
        f"/accounts/{acc['id']}", headers=_auth_headers(client._user.id)
    ).json()
    assert refetched["current_balance"] == 500
