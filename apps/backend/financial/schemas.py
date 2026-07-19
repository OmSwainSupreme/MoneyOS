"""Pydantic v2 schemas for the financial domain API.

Request and response models are kept separate. Request models validate input on
the way in (enum values, positive amounts, currency whitelist, string lengths,
date sanity); response models project the stored entities back to the client.

Currency is mirrored from :mod:`user.models` (the single source of truth for
the supported set) so the financial surface cannot drift from the rest of the
app.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from user.models import CURRENCIES

from financial.models import (
    AccountType,
    CategoryType,
    TransactionSource,
    TransactionStatus,
    TransactionType,
)

# Reusable currency validator -------------------------------------------------
_CURRENCY_SET = frozenset(CURRENCIES)


def _validate_currency(value: str | None) -> str | None:
    """Normalize and whitelist a currency code (uppercase ISO-ish code)."""
    if value is None:
        return None
    code = value.strip().upper()
    if code not in _CURRENCY_SET:
        raise ValueError(
            f"Unsupported currency {value!r}. Supported: "
            + ", ".join(CURRENCIES)
            + "."
        )
    return code


def _validate_amount(
    value: Decimal | float | int | None,
) -> Decimal | float | int | None:
    """Reject non-positive transaction amounts (magnitude must be > 0)."""
    if value is None:
        return value
    if value <= 0:
        raise ValueError("amount must be a positive number greater than zero.")
    return value


# ---------------------------------------------------------------------------
# Account schemas
# ---------------------------------------------------------------------------
class AccountResponse(BaseModel):
    """Read projection of an account."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    account_type: str
    institution_name: str | None
    currency: str
    opening_balance: float
    current_balance: float
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AccountCreateRequest(BaseModel):
    """Create a new account (all user-supplied fields required where noted)."""

    name: str = Field(min_length=1, max_length=255)
    account_type: AccountType
    institution_name: str | None = Field(default=None, max_length=255)
    currency: str = Field(default="INR", max_length=8)
    opening_balance: float = Field(default=0, ge=0)
    current_balance: float | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def _trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be empty or whitespace only.")
        return value

    @field_validator("currency")
    @classmethod
    def _validate_currency(cls, value: str) -> str:
        return _validate_currency(value)  # type: ignore[return-value]

    @model_validator(mode="after")
    def _default_current_balance(self) -> AccountCreateRequest:
        # When omitted, current_balance starts equal to opening_balance.
        if self.current_balance is None:
            self.current_balance = self.opening_balance
        return self


class AccountUpdateRequest(BaseModel):
    """Partial account update. ``None`` means unchanged."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    account_type: AccountType | None = None
    institution_name: str | None = Field(default=None, max_length=255)
    currency: str | None = Field(default=None, max_length=8)
    opening_balance: float | None = Field(default=None, ge=0)
    current_balance: float | None = Field(default=None, ge=0)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def _trim_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("name must not be empty or whitespace only.")
        return value

    @field_validator("currency")
    @classmethod
    def _validate_currency(cls, value: str | None) -> str | None:
        return _validate_currency(value)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Category schemas
# ---------------------------------------------------------------------------
class CategoryResponse(BaseModel):
    """Read projection of a category."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None
    name: str
    type: str
    color: str | None
    icon: str | None
    is_system: bool
    created_at: datetime


class CategoryCreateRequest(BaseModel):
    """Create a user-owned category."""

    name: str = Field(min_length=1, max_length=255)
    type: CategoryType
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str | None = Field(default=None, max_length=64)

    @field_validator("name")
    @classmethod
    def _trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be empty or whitespace only.")
        return value


class CategoryUpdateRequest(BaseModel):
    """Partial category update. ``None`` means unchanged."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    type: CategoryType | None = None
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str | None = Field(default=None, max_length=64)

    @field_validator("name")
    @classmethod
    def _trim_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("name must not be empty or whitespace only.")
        return value


# ---------------------------------------------------------------------------
# Transaction schemas
# ---------------------------------------------------------------------------
class TransactionResponse(BaseModel):
    """Read projection of a transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    amount: float
    transaction_type: str
    merchant: str | None
    description: str | None
    transaction_date: datetime
    reference_number: str | None
    source: str
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class TransactionCreateRequest(BaseModel):
    """Create a new transaction."""

    account_id: uuid.UUID
    category_id: uuid.UUID | None = None
    amount: float = Field(gt=0)
    transaction_type: TransactionType
    merchant: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    transaction_date: datetime
    reference_number: str | None = Field(default=None, max_length=128)
    source: TransactionSource = TransactionSource.MANUAL
    status: TransactionStatus = TransactionStatus.POSTED
    notes: str | None = Field(default=None, max_length=2048)

    @field_validator("amount")
    @classmethod
    def _validate_amount(cls, value: float) -> float:
        return _validate_amount(value)  # type: ignore[return-value]

    @field_validator("merchant", "description", "notes", "reference_number")
    @classmethod
    def _strip_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class TransactionUpdateRequest(BaseModel):
    """Partial transaction update. ``None`` means unchanged."""

    category_id: uuid.UUID | None = None
    amount: float | None = Field(default=None, gt=0)
    transaction_type: TransactionType | None = None
    merchant: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1024)
    transaction_date: datetime | None = None
    reference_number: str | None = Field(default=None, max_length=128)
    source: TransactionSource | None = None
    status: TransactionStatus | None = None
    notes: str | None = Field(default=None, max_length=2048)

    @field_validator("amount")
    @classmethod
    def _validate_amount(cls, value: float | None) -> float | None:
        return _validate_amount(value)  # type: ignore[return-value]

    @field_validator("merchant", "description", "notes", "reference_number")
    @classmethod
    def _strip_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


# ---------------------------------------------------------------------------
# Filter query params (used by GET list endpoints)
# ---------------------------------------------------------------------------
class TransactionFilter(BaseModel):
    """Optional filter for listing transactions."""

    account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    transaction_type: TransactionType | None = None
    status: TransactionStatus | None = None
    source: TransactionSource | None = None
    merchant: str | None = None
    reference_number: str | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class AccountFilter(BaseModel):
    """Optional filter for listing accounts."""

    account_type: AccountType | None = None
    is_active: bool | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class CategoryFilter(BaseModel):
    """Optional filter for listing categories."""

    type: CategoryType | None = None
    include_system: bool = True
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


# ---------------------------------------------------------------------------
# Dashboard / analytics / decision response models
# ---------------------------------------------------------------------------
class RecentTransaction(BaseModel):
    """A recent transaction projection (no ORM coupling)."""

    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    amount: float
    transaction_type: str
    merchant: str | None
    description: str | None
    transaction_date: datetime
    status: str
    source: str


class DashboardResponse(BaseModel):
    """Headline dashboard figures for the authenticated user."""

    currency: str
    total_balance: float
    total_income: float
    total_expenses: float
    total_savings: float
    recent_transactions: list[RecentTransaction]


class MonthlySummaryRow(BaseModel):
    """One calendar month of income/expense/savings."""

    month: str
    income: float
    expense: float
    savings: float
    net: float


class SpendingByCategoryRow(BaseModel):
    """Expense total for a single category in the window."""

    category_id: uuid.UUID | None
    category_name: str
    color: str | None
    total: float


class CashFlowMonth(BaseModel):
    """Per-month cash-flow triad."""

    month: str
    inflow: float
    outflow: float
    net: float


class CashFlowResponse(BaseModel):
    """Cash-flow summary over a trailing window."""

    months: list[CashFlowMonth]
    total_inflow: float
    total_outflow: float
    total_net: float


class DecisionRequest(BaseModel):
    """Question for the deterministic financial decision engine."""

    question: str = Field(
        ..., min_length=1, max_length=1024, description="A natural-language question."
    )
    amount: float | None = Field(
        default=None, gt=0, description="Optional amount the question refers to."
    )


class DecisionResponse(BaseModel):
    """Structured answer from the rules engine."""

    answer: str = Field(..., description="Human-readable answer.")
    verdict: str = Field(
        ..., description="One of: affordable, caution, unaffordable, info."
    )
    safe_to_spend: float | None = Field(
        default=None, description="Remaining safe-to-spend budget, if computed."
    )
    rationale: list[str] = Field(default_factory=list)
    data: dict = Field(default_factory=dict)
