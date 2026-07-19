"""Unit tests for financial-domain schemas, enums, and validation rules.

These tests run WITHOUT a database: they exercise Pydantic validation and the
enum definitions only. They assert that invalid input is rejected before any DB
touch, and that valid input normalizes as expected (currency uppercasing, name
trimming, default current_balance, positive amounts).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from financial.models import (
    AccountType,
    CategoryType,
    TransactionSource,
    TransactionStatus,
    TransactionType,
)
from financial.schemas import (
    AccountCreateRequest,
    AccountUpdateRequest,
    CategoryCreateRequest,
    CategoryUpdateRequest,
    TransactionCreateRequest,
    TransactionUpdateRequest,
)
from pydantic import ValidationError


# --- Enums -------------------------------------------------------------------
def test_account_type_values() -> None:
    """Account type values."""
    assert {t.value for t in AccountType} == {
        "savings",
        "current",
        "credit_card",
        "cash",
        "wallet",
        "investment",
    }


def test_category_type_values() -> None:
    """Category type values."""
    assert {t.value for t in CategoryType} == {
        "income",
        "expense",
        "transfer",
    }


def test_transaction_type_values() -> None:
    """Transaction type values."""
    assert {t.value for t in TransactionType} == {
        "income",
        "expense",
        "transfer",
    }


def test_transaction_status_values() -> None:
    """Transaction status values."""
    assert {t.value for t in TransactionStatus} == {
        "pending",
        "posted",
        "failed",
    }


def test_transaction_source_values() -> None:
    """Transaction source values."""
    assert {t.value for t in TransactionSource} == {
        "manual",
        "statement",
        "import",
    }


# --- Account schema ----------------------------------------------------------
def test_account_create_defaults_currency_and_balance() -> None:
    """Account create defaults currency and balance."""
    req = AccountCreateRequest(name="  Savings  ", account_type="savings")
    assert req.name == "Savings"  # trimmed
    assert req.currency == "INR"  # default
    assert req.opening_balance == 0
    assert req.current_balance == 0  # defaults to opening_balance


def test_account_create_lowercase_currency_normalized() -> None:
    """Account create lowercase currency normalized."""
    req = AccountCreateRequest(
        name="USD Acct", account_type="current", currency="usd"
    )
    assert req.currency == "USD"


def test_account_create_rejects_unsupported_currency() -> None:
    """Account create rejects unsupported currency."""
    with pytest.raises(ValidationError):
        AccountCreateRequest(
            name="X", account_type="cash", currency="JPY"
        )


def test_account_create_rejects_empty_name() -> None:
    """Account create rejects empty name."""
    with pytest.raises(ValidationError):
        AccountCreateRequest(name="   ", account_type="cash")


def test_account_create_rejects_negative_balance() -> None:
    """Account create rejects negative balance."""
    with pytest.raises(ValidationError):
        AccountCreateRequest(
            name="X", account_type="cash", opening_balance=-10
        )


def test_account_create_current_balance_explicit() -> None:
    """Account create current balance explicit."""
    req = AccountCreateRequest(
        name="X",
        account_type="cash",
        opening_balance=100,
        current_balance=50,
    )
    assert req.current_balance == 50


def test_account_update_currency_normalized_and_validated() -> None:
    """Account update currency normalized and validated."""
    req = AccountUpdateRequest(currency="eur")
    assert req.currency == "EUR"
    with pytest.raises(ValidationError):
        AccountUpdateRequest(currency="XYZ")


# --- Category schema ---------------------------------------------------------
def test_category_create_valid() -> None:
    """Category create valid."""
    req = CategoryCreateRequest(name="Food", type="expense", color="#AABBCC")
    assert req.name == "Food"
    assert req.color == "#AABBCC"


def test_category_create_rejects_bad_color() -> None:
    """Category create rejects bad color."""
    with pytest.raises(ValidationError):
        CategoryCreateRequest(name="Food", type="expense", color="red")


def test_category_create_rejects_empty_name() -> None:
    """Category create rejects empty name."""
    with pytest.raises(ValidationError):
        CategoryCreateRequest(name="", type="expense")


def test_category_update_pattern_enforced() -> None:
    """Category update pattern enforced."""
    with pytest.raises(ValidationError):
        CategoryUpdateRequest(color="#fff")


# --- Transaction schema ------------------------------------------------------
def test_transaction_create_valid() -> None:
    """Transaction create valid."""
    now = datetime.now(UTC)
    req = TransactionCreateRequest(
        account_id="11111111-1111-1111-1111-111111111111",
        amount=50.25,
        transaction_type="income",
        transaction_date=now,
    )
    assert req.amount == 50.25
    assert req.source.value == "manual"  # default
    assert req.status.value == "posted"  # default


def test_transaction_create_rejects_zero_amount() -> None:
    """Transaction create rejects zero amount."""
    with pytest.raises(ValidationError):
        TransactionCreateRequest(
            account_id="11111111-1111-1111-1111-111111111111",
            amount=0,
            transaction_type="expense",
            transaction_date=datetime.now(UTC),
        )


def test_transaction_create_rejects_negative_amount() -> None:
    """Transaction create rejects negative amount."""
    with pytest.raises(ValidationError):
        TransactionCreateRequest(
            account_id="11111111-1111-1111-1111-111111111111",
            amount=-1,
            transaction_type="expense",
            transaction_date=datetime.now(UTC),
        )


def test_transaction_create_trims_string_fields() -> None:
    """Transaction create trims string fields."""
    req = TransactionCreateRequest(
        account_id="11111111-1111-1111-1111-111111111111",
        amount=10,
        transaction_type="expense",
        transaction_date=datetime.now(UTC),
        merchant="  Starbucks  ",
        notes="  latte  ",
    )
    assert req.merchant == "Starbucks"
    assert req.notes == "latte"


def test_transaction_update_rejects_zero_amount() -> None:
    """Transaction update rejects zero amount."""
    with pytest.raises(ValidationError):
        TransactionUpdateRequest(amount=0)


def test_transaction_update_accepts_positive_amount() -> None:
    """Transaction update accepts positive amount."""
    req = TransactionUpdateRequest(amount=12.5)
    assert req.amount == 12.5
