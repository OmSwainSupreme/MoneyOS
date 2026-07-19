"""Integration tests for the MVP feature set.

Covers the feature areas added in the MVP pass that are not already exercised
by :mod:`tests.test_financial_routes`:

* Statement ingestion — ``POST /statements/import`` extracts, parses,
  normalizes, **persists** transactions to an owned account and adjusts the
  account balance atomically (``source = statement``).
* Dashboard — ``GET /dashboard`` aggregates balances, income, expenses, savings.
* Analytics — monthly summary, spending-by-category, income-vs-expense, cash flow.
* Decision — deterministic rules engine answers affordability / safe-to-spend /
  where-money questions.
* AI chat — ``POST /ai/chat`` answers a financial question using stored data
  (mock provider; Gemini only when configured).

These tests drive the FastAPI app through ``httpx.AsyncClient`` with an
``ASGITransport`` so the request handling runs in the *same* asyncio event loop
as the test's DB session. That avoids the cross-thread async-session reuse that
the synchronous ``TestClient`` triggers under Python 3.14, while still exercising
the full HTTP surface, dependency overrides, and the global error envelope.
"""

from __future__ import annotations

import uuid

import httpx
import pytest
import pytest_asyncio
from auth.dependencies import CurrentUserDep
from auth.models import User as AuthUser
from auth.security import create_access_token
from core.config import get_settings
from database.session import get_db_session, get_sessionmaker
from fastapi import FastAPI
from financial.analytics import AnalyticsService
from financial.decision import FinancialDecisionEngine
from financial.router import (
    accounts_router,
    analytics_router,
    categories_router,
    dashboard_router,
    decision_router,
    transactions_router,
)
from services.ai.router import chat_router
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import make_account, make_user

pytestmark = pytest.mark.requires_postgres


def _build_app(session: AsyncSession, user: AuthUser) -> FastAPI:
    app = FastAPI()

    async def _override_session():
        yield session

    async def _override_current_user() -> AuthUser:
        return user

    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[CurrentUserDep] = _override_current_user
    app.include_router(accounts_router)
    app.include_router(categories_router)
    app.include_router(transactions_router)
    app.include_router(dashboard_router)
    app.include_router(analytics_router)
    app.include_router(decision_router)
    app.include_router(chat_router)
    return app


def _auth_headers(user_id) -> dict[str, str]:
    token = create_access_token(user_id, get_settings())
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def client():
    """Async client bound to its own session and a fresh user.

    The session is created directly from the engine (not borrowed from the
    conftest ``db_session`` fixture) so the request handler and the test run on
    the same session/task without cross-task sharing issues under Python 3.14.
    All tables are truncated after the test for isolation.
    """
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        user = await make_user(session)
        await session.commit()
        app = _build_app(session, user)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as ac:
            ac._user = user  # type: ignore[attr-defined]
            ac._session = session  # type: ignore[attr-defined]
            try:
                yield ac
            finally:
                await session.rollback()
                from database.base import Base

                table_names = ", ".join(
                    f'"{t.name}"' for t in Base.metadata.sorted_tables
                )
                await session.execute(
                    text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE")
                )
                await session.commit()


async def _seed(ac: httpx.AsyncClient, *, balance: float = 0, expenses: int = 0) -> uuid.UUID:
    """Create an account (with opening balance) and seed expense txns.

    Returns the account id. Used to drive dashboard/analytics/decision tests.
    """
    resp = await ac.post(
        "/accounts",
        headers=_auth_headers(ac._user.id),
        json={
            "name": "Savings",
            "account_type": "savings",
            "opening_balance": balance,
        },
    )
    acc = resp.json()
    for _ in range(int(expenses)):
        await ac.post(
            "/transactions",
            headers=_auth_headers(ac._user.id),
            json={
                "account_id": acc["id"],
                "amount": 10,
                "transaction_type": "expense",
                "transaction_date": "2026-07-19T00:00:00Z",
            },
        )
    return uuid.UUID(acc["id"])


# --- Dashboard ---------------------------------------------------------------
async def test_dashboard_aggregates(client: httpx.AsyncClient) -> None:
    """Dashboard returns balance, income, expenses, savings."""
    account_id = await _seed(client, balance=1000, expenses=5)  # 50 spent
    await client.post(
        "/transactions",
        headers=_auth_headers(client._user.id),
        json={
            "account_id": str(account_id),
            "amount": 200,
            "transaction_type": "income",
            "transaction_date": "2026-07-19T00:00:00Z",
        },
    )
    resp = await client.get("/dashboard", headers=_auth_headers(client._user.id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["currency"] == "INR"
    assert body["total_balance"] == 1000
    assert body["total_expenses"] == 50
    assert body["total_income"] == 200
    assert body["total_savings"] == 150
    assert isinstance(body["recent_transactions"], list)


# --- Analytics ---------------------------------------------------------------
async def test_monthly_summary_contiguous(client: httpx.AsyncClient) -> None:
    """Monthly summary returns one entry per requested month (contiguous)."""
    await _seed(client, balance=500, expenses=2)
    resp = await client.get(
        "/analytics/monthly?months=6", headers=_auth_headers(client._user.id)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 6
    assert all("month" in row for row in body)
    assert all("income" in row and "expense" in row for row in body)


async def test_spending_by_category(client: httpx.AsyncClient) -> None:
    """Spending-by-category returns expense totals grouped by category."""
    await _seed(client, balance=500, expenses=3)
    resp = await client.get(
        "/analytics/spending-by-category?months=12",
        headers=_auth_headers(client._user.id),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert any(row["category_name"] == "Uncategorized" for row in body)


async def test_income_vs_expense(client: httpx.AsyncClient) -> None:
    """Income-vs-expense returns month/income/expense dicts."""
    await _seed(client, balance=500, expenses=2)
    resp = await client.get(
        "/analytics/income-vs-expense?months=12",
        headers=_auth_headers(client._user.id),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert all(set(m.keys()) >= {"month", "income", "expense"} for m in body)


async def test_cash_flow(client: httpx.AsyncClient) -> None:
    """Cash-flow returns per-month triad and window totals."""
    await _seed(client, balance=500, expenses=2)
    resp = await client.get(
        "/analytics/cash-flow?months=12", headers=_auth_headers(client._user.id)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "months" in body and "total_inflow" in body
    assert body["total_net"] == body["total_inflow"] - body["total_outflow"]


# --- Decision ----------------------------------------------------------------
async def test_decision_affordable(client: httpx.AsyncClient) -> None:
    """Decision engine says an in-budget purchase is affordable."""
    await _seed(client, balance=100000, expenses=10)
    resp = await client.post(
        "/decision",
        headers=_auth_headers(client._user.id),
        json={"question": "Can I buy a bike for ₹25,000?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "affordable"
    assert body["safe_to_spend"] is not None


async def test_decision_safe_to_spend(client: httpx.AsyncClient) -> None:
    """'How much can I safely spend?' returns a non-negative budget."""
    await _seed(client, balance=50000, expenses=10)
    resp = await client.post(
        "/decision",
        headers=_auth_headers(client._user.id),
        json={"question": "How much can I safely spend?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "info"
    assert body["safe_to_spend"] >= 0


async def test_decision_where_money(client: httpx.AsyncClient) -> None:
    """'Where is my money going?' returns a category breakdown."""
    await _seed(client, balance=5000, expenses=4)
    resp = await client.post(
        "/decision",
        headers=_auth_headers(client._user.id),
        json={"question": "Where is my money going?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "info"
    assert "answer" in body and body["answer"]


# --- Statement ingestion -----------------------------------------------------
_CSV_STATEMENT = (
    "date,description,debit,credit\n"
    "2026-06-01,Salary,,50000\n"
    "2026-06-02,Grocery Store,1500,\n"
    "2026-06-03,Electricity Bill,2000,\n"
)


async def test_import_statement_persists_and_adjusts_balance(
    client: httpx.AsyncClient,
) -> None:
    """Import extracts rows, persists them, and adjusts balance atomically."""
    acc = (
        await client.post(
            "/accounts",
            headers=_auth_headers(client._user.id),
            json={
                "name": "Stmt Acct",
                "account_type": "savings",
                "opening_balance": 0,
            },
        )
    ).json()
    account_id = uuid.UUID(acc["id"])

    files = {"file": ("statement.csv", _CSV_STATEMENT.encode("utf-8"), "text/csv")}
    resp = await client.post(
        "/statements/import",
        headers=_auth_headers(client._user.id),
        data={"account_id": str(account_id), "auto_categorize": "true"},
        files=files,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # 3 typed rows: 1 credit (income) + 2 debits (expense); none unknown.
    assert body["stored_count"] == 3
    assert body["skipped_count"] == 0
    assert len(body["transaction_ids"]) == 3

    # Net delta = +50000 -1500 -2000 = +46500 -> balance should reflect it.
    refetched = (
        await client.get(
            f"/accounts/{account_id}", headers=_auth_headers(client._user.id)
        )
    ).json()
    assert refetched["current_balance"] == 46500

    # Transactions are stored with source = statement.
    txns = (
        await client.get(
            "/transactions",
            headers=_auth_headers(client._user.id),
            params={"account_id": str(account_id), "source": "statement"},
        )
    ).json()
    assert len(txns) == 3


async def test_import_statement_rejects_other_users_account(
    client: httpx.AsyncClient,
) -> None:
    """Import to a non-owned account is denied (404 envelope)."""
    other = await make_user(client._session, email="other-owner@example.com")
    other_acc = await make_account(client._session, user_id=other.id)
    files = {"file": ("statement.csv", _CSV_STATEMENT.encode("utf-8"), "text/csv")}
    resp = await client.post(
        "/statements/import",
        headers=_auth_headers(client._user.id),
        data={"account_id": str(other_acc.id)},
        files=files,
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "account_not_found"


async def test_import_statement_rejects_bad_account_format(
    client: httpx.AsyncClient,
) -> None:
    """Malformed account_id yields a validation envelope."""
    files = {"file": ("statement.csv", _CSV_STATEMENT.encode("utf-8"), "text/csv")}
    resp = await client.post(
        "/statements/import",
        headers=_auth_headers(client._user.id),
        data={"account_id": "not-a-uuid"},
        files=files,
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


# --- AI chat -----------------------------------------------------------------
async def test_ai_chat_answers(client: httpx.AsyncClient) -> None:
    """Chat endpoint answers using stored data (mock provider)."""
    await _seed(client, balance=100000, expenses=5)
    resp = await client.post(
        "/ai/chat",
        headers=_auth_headers(client._user.id),
        json={"message": "Can I afford a phone for 20000?", "history": []},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "reply" in body and body["reply"]
    assert body["provider"] in ("mock", "gemini")
    assert isinstance(body["data"], dict)


# --- Unit-level decision engine (no HTTP) ------------------------------------
def test_decision_engine_unit() -> None:
    """Decision engine returns deterministic answers from a context dict."""
    ctx = {
        "currency": "INR",
        "total_balance": 100000.0,
        "total_income": 120000.0,
        "total_expenses": 50000.0,
        "total_savings": 70000.0,
        "top_categories": [
            {"category_name": "Food", "total": 12000.0},
            {"category_name": "Travel", "total": 8000.0},
        ],
    }
    engine = FinancialDecisionEngine(ctx)
    affordable = engine.answer("Can I buy a laptop for 25000?")
    assert affordable["verdict"] in ("affordable", "caution")
    safe = engine.answer("How much can I safely spend?")
    assert safe["safe_to_spend"] >= 0
    where = engine.answer("Where is my money going?")
    assert "Food" in where["answer"]


async def test_analytics_service_direct(client: httpx.AsyncClient) -> None:
    """AnalyticsService.dashboard works against the shared session."""
    await _seed(client, balance=2000, expenses=3)
    data = await AnalyticsService(client._session).dashboard(client._user.id)
    assert data["total_balance"] == 2000
    assert data["total_expenses"] == 30
