"""Financial-domain REST routes.

Exposes the accounts, categories, and transactions endpoints under
``/accounts``, ``/categories``, and ``/transactions``. All routes require
authentication (the current user is injected) and delegate business logic to
the service layer, raising domain exceptions directly;
:func:`core.errors.register_exception_handlers` translates them into the
unified error envelope. No ORM, repository, or SQL access happens here.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status

from financial.dependencies import (
    AccountServiceDep,
    AnalyticsServiceDep,
    CategoryServiceDep,
    CurrentUser,
    TransactionServiceDep,
)
from financial.schemas import (
    AccountCreateRequest,
    AccountFilter,
    AccountResponse,
    AccountUpdateRequest,
    CashFlowResponse,
    CategoryCreateRequest,
    CategoryFilter,
    CategoryResponse,
    CategoryUpdateRequest,
    DashboardResponse,
    DecisionRequest,
    DecisionResponse,
    MonthlySummaryRow,
    SpendingByCategoryRow,
    TransactionCreateRequest,
    TransactionFilter,
    TransactionResponse,
    TransactionUpdateRequest,
)

# Decision engine lives in its own module; import the strategy.
from financial.decision import FinancialDecisionEngine

accounts_router = APIRouter(prefix="/accounts", tags=["accounts"])
categories_router = APIRouter(prefix="/categories", tags=["categories"])
transactions_router = APIRouter(prefix="/transactions", tags=["transactions"])
dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])
analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])
decision_router = APIRouter(prefix="/decision", tags=["decision"])


# --- Accounts ---------------------------------------------------------------
@accounts_router.get("", response_model=list[AccountResponse])
async def list_accounts(
    current_user: CurrentUser,
    account_service: AccountServiceDep,
    account_type: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
) -> list[AccountResponse]:
    """List the authenticated user's accounts, optionally filtered."""
    filters = None
    if account_type is not None or is_active is not None:
        filters = AccountFilter(account_type=account_type, is_active=is_active)
    return await account_service.list_accounts(current_user.id, filters)


@accounts_router.post(
    "", response_model=AccountResponse, status_code=status.HTTP_201_CREATED
)
async def create_account(
    payload: AccountCreateRequest,
    current_user: CurrentUser,
    account_service: AccountServiceDep,
) -> AccountResponse:
    """Create a new account for the authenticated user."""
    return await account_service.create_account(current_user.id, payload)


@accounts_router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    account_service: AccountServiceDep,
) -> AccountResponse:
    """Fetch a single account by id (must be owned by the user)."""
    return await account_service.get_account(current_user.id, account_id)


@accounts_router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: uuid.UUID,
    payload: AccountUpdateRequest,
    current_user: CurrentUser,
    account_service: AccountServiceDep,
) -> AccountResponse:
    """Partially update an account (must be owned by the user)."""
    return await account_service.update_account(
        current_user.id, account_id, payload
    )


@accounts_router.delete(
    "/{account_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    account_service: AccountServiceDep,
) -> None:
    """Delete an account and its transactions (cascade)."""
    await account_service.delete_account(current_user.id, account_id)


# --- Categories -------------------------------------------------------------
@categories_router.get("", response_model=list[CategoryResponse])
async def list_categories(
    current_user: CurrentUser,
    category_service: CategoryServiceDep,
    type: str | None = Query(default=None),
    include_system: bool = Query(default=True),
) -> list[CategoryResponse]:
    """List the user's categories plus system categories."""
    filters = None
    if type is not None or not include_system:
        filters = CategoryFilter(type=type, include_system=include_system)
    return await category_service.list_categories(current_user.id, filters)


@categories_router.post(
    "", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED
)
async def create_category(
    payload: CategoryCreateRequest,
    current_user: CurrentUser,
    category_service: CategoryServiceDep,
) -> CategoryResponse:
    """Create a new user-owned category."""
    return await category_service.create_category(current_user.id, payload)


@categories_router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: uuid.UUID,
    current_user: CurrentUser,
    category_service: CategoryServiceDep,
) -> CategoryResponse:
    """Fetch a single category (owned or system)."""
    return await category_service.get_category(current_user.id, category_id)


@categories_router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdateRequest,
    current_user: CurrentUser,
    category_service: CategoryServiceDep,
) -> CategoryResponse:
    """Partially update a user-owned category."""
    return await category_service.update_category(
        current_user.id, category_id, payload
    )


@categories_router.delete(
    "/{category_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_category(
    category_id: uuid.UUID,
    current_user: CurrentUser,
    category_service: CategoryServiceDep,
) -> None:
    """Delete a user-owned category (system categories are protected)."""
    await category_service.delete_category(current_user.id, category_id)


# --- Transactions -----------------------------------------------------------
@transactions_router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    current_user: CurrentUser,
    transaction_service: TransactionServiceDep,
    account_id: uuid.UUID | None = Query(default=None),  # noqa: B008
    category_id: uuid.UUID | None = Query(default=None),  # noqa: B008
    transaction_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    source: str | None = Query(default=None),
    merchant: str | None = Query(default=None),
    reference_number: str | None = Query(default=None),
) -> list[TransactionResponse]:
    """List the user's transactions, optionally filtered."""
    filters = None
    if any(
        v is not None
        for v in (
            account_id,
            category_id,
            transaction_type,
            status,
            source,
            merchant,
            reference_number,
        )
    ):
        filters = TransactionFilter(
            account_id=account_id,
            category_id=category_id,
            transaction_type=transaction_type,
            status=status,
            source=source,
            merchant=merchant,
            reference_number=reference_number,
        )
    return await transaction_service.list_transactions(
        current_user.id, filters
    )


@transactions_router.post(
    "", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    payload: TransactionCreateRequest,
    current_user: CurrentUser,
    transaction_service: TransactionServiceDep,
) -> TransactionResponse:
    """Create a new transaction in one of the user's accounts."""
    return await transaction_service.create_transaction(
        current_user.id, payload
    )


@transactions_router.get(
    "/{transaction_id}", response_model=TransactionResponse
)
async def get_transaction(
    transaction_id: uuid.UUID,
    current_user: CurrentUser,
    transaction_service: TransactionServiceDep,
) -> TransactionResponse:
    """Fetch a single transaction (must belong to the user's account)."""
    return await transaction_service.get_transaction(
        current_user.id, transaction_id
    )


@transactions_router.patch(
    "/{transaction_id}", response_model=TransactionResponse
)
async def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdateRequest,
    current_user: CurrentUser,
    transaction_service: TransactionServiceDep,
) -> TransactionResponse:
    """Partially update a transaction, keeping balances consistent."""
    return await transaction_service.update_transaction(
        current_user.id, transaction_id, payload
    )


@transactions_router.delete(
    "/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_transaction(
    transaction_id: uuid.UUID,
    current_user: CurrentUser,
    transaction_service: TransactionServiceDep,
) -> None:
    """Delete a transaction and roll back its balance effect."""
    await transaction_service.delete_transaction(
        current_user.id, transaction_id
    )


# --- Dashboard --------------------------------------------------------------
@dashboard_router.get("", response_model=DashboardResponse)
async def get_dashboard(
    current_user: CurrentUser,
    analytics: AnalyticsServiceDep,
    limit_recent: int = Query(default=10, ge=1, le=50),
) -> DashboardResponse:
    """Headline dashboard: balances, income, expenses, savings, recent txns."""
    data = await analytics.dashboard(current_user.id, limit_recent=limit_recent)
    return DashboardResponse(**data)


# --- Analytics ---------------------------------------------------------------
@analytics_router.get("/monthly", response_model=list[MonthlySummaryRow])
async def monthly_summary(
    current_user: CurrentUser,
    analytics: AnalyticsServiceDep,
    months: int = Query(default=12, ge=1, le=60),
) -> list[MonthlySummaryRow]:
    """Month-by-month income, expenses, and savings (contiguous window)."""
    rows = await analytics.monthly_summary(current_user.id, months=months)
    return [MonthlySummaryRow(**r) for r in rows]


@analytics_router.get(
    "/spending-by-category", response_model=list[SpendingByCategoryRow]
)
async def spending_by_category(
    current_user: CurrentUser,
    analytics: AnalyticsServiceDep,
    months: int = Query(default=12, ge=1, le=60),
) -> list[SpendingByCategoryRow]:
    """Expense totals grouped by category over the trailing window."""
    rows = await analytics.spending_by_category(
        current_user.id, months=months
    )
    return [SpendingByCategoryRow(**r) for r in rows]


@analytics_router.get("/income-vs-expense")
async def income_vs_expense(
    current_user: CurrentUser,
    analytics: AnalyticsServiceDep,
    months: int = Query(default=12, ge=1, le=60),
) -> list[dict]:
    """Monthly income vs expense pairings for charting."""
    return await analytics.income_vs_expense(current_user.id, months=months)


@analytics_router.get("/cash-flow", response_model=CashFlowResponse)
async def cash_flow(
    current_user: CurrentUser,
    analytics: AnalyticsServiceDep,
    months: int = Query(default=12, ge=1, le=60),
) -> CashFlowResponse:
    """Cash-flow summary: per-month inflow/outflow/net plus window totals."""
    data = await analytics.cash_flow(current_user.id, months=months)
    return CashFlowResponse(**data)


# --- Decision ----------------------------------------------------------------
@decision_router.post("", response_model=DecisionResponse)
async def decide(
    payload: DecisionRequest,
    current_user: CurrentUser,
    analytics: AnalyticsServiceDep,
) -> DecisionResponse:
    """Answer a financial question via the deterministic rules engine.

    Handles questions such as "Can I afford a bike for ₹25,000?", "How much can
    I safely spend?", and "Where is my money going?".
    """
    context = await analytics.dashboard(current_user.id, limit_recent=5)
    # Enrich the context with top spending categories so "where is my money
    # going?" can answer concretely.
    context["top_categories"] = await analytics.spending_by_category(
        current_user.id, months=3
    )
    engine = FinancialDecisionEngine(context)
    return DecisionResponse(**engine.answer(payload.question, payload.amount))
