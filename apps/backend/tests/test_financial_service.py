"""Service-layer tests for the financial domain.

Exercises the business logic in isolation from HTTP: ownership enforcement,
system-category protection, currency/amount validation, and (most
importantly) account balance consistency (the stored ``current_balance`` must
always reflect posted transactions, and must be rolled back on delete /
reversed on update).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from financial.exceptions import (
    AccountNotFound,
    CategoryNotFound,
    CategoryOwnershipError,
)
from financial.models import (
    Category,
    TransactionStatus,
    TransactionType,
)
from financial.repository import TransactionRepository
from financial.schemas import (
    AccountCreateRequest,
    CategoryCreateRequest,
    TransactionCreateRequest,
)
from financial.service import (
    AccountService,
    CategoryService,
    TransactionService,
    _balance_delta,
)

from tests.factories import make_account, make_user

pytestmark = pytest.mark.requires_postgres


# --- _balance_delta unit logic -----------------------------------------------
def test_balance_delta_posted_income_increases() -> None:
    """Balance delta posted income increases."""
    assert (
        _balance_delta(
            TransactionType.INCOME.value, TransactionStatus.POSTED.value, 100
        )
        == 100
    )


def test_balance_delta_posted_expense_decreases() -> None:
    """Balance delta posted expense decreases."""
    assert (
        _balance_delta(
            TransactionType.EXPENSE.value, TransactionStatus.POSTED.value, 100
        )
        == -100
    )


def test_balance_delta_transfer_decreases() -> None:
    """Balance delta transfer decreases."""
    assert (
        _balance_delta(
            TransactionType.TRANSFER.value, TransactionStatus.POSTED.value, 40
        )
        == -40
    )


def test_balance_delta_non_posted_is_zero() -> None:
    """Balance delta non posted is zero."""
    for status in ("pending", "failed"):
        assert (
            _balance_delta(TransactionType.INCOME.value, status, 100) == 0
        )


# --- Account service --------------------------------------------------------
async def test_create_account_sets_default_balance(db_session) -> None:
    """Create account sets default balance."""
    user = await make_user(db_session)
    svc = AccountService(db_session)
    acc = await svc.create_account(
        user.id,
        AccountCreateRequest(name="Sav", account_type="savings"),
    )
    assert acc.current_balance == acc.opening_balance == 0


async def test_get_account_enforces_ownership(db_session) -> None:
    """Get account enforces ownership."""
    user = await make_user(db_session)
    other = await make_user(db_session, email="o@example.com")
    acc = await make_account(db_session, user_id=other.id)
    svc = AccountService(db_session)
    with pytest.raises(AccountNotFound):
        await svc.get_account(user.id, acc.id)


async def test_delete_account_cascades_transactions(db_session) -> None:
    """Delete account cascades transactions."""
    user = await make_user(db_session)
    acc = await make_account(db_session, user_id=user.id, current_balance=0)
    repo = TransactionRepository(db_session)
    txn = await repo.create(
        account_id=acc.id,
        amount=10,
        transaction_type="expense",
        status="posted",
        source="manual",
    )
    svc = AccountService(db_session)
    await svc.delete_account(user.id, acc.id)
    # The account and its transaction are gone via ON DELETE CASCADE.
    from financial.exceptions import (
        AccountNotFound,
        TransactionNotFound,
    )

    with pytest.raises(AccountNotFound):
        await svc.get_account(user.id, acc.id)
    with pytest.raises(TransactionNotFound):
        await repo.get_or_raise(txn.id, user.id)


# --- Category service --------------------------------------------------------
async def test_system_category_cannot_be_deleted(db_session) -> None:
    """System category cannot be deleted."""
    user = await make_user(db_session)
    # Create a system category directly.
    system = Category(
        user_id=None, name="Sys", type="expense", is_system=True
    )
    db_session.add(system)
    await db_session.flush()

    # The user can *see* it (get_or_raise) but not delete it.
    svc = CategoryService(db_session)
    fetched = await svc.get_category(user.id, system.id)
    assert fetched.is_system is True
    with pytest.raises(CategoryOwnershipError):
        await svc.delete_category(user.id, system.id)


async def test_system_category_cannot_be_updated(db_session) -> None:
    """System category cannot be updated."""
    user = await make_user(db_session)
    system = Category(
        user_id=None, name="Sys", type="expense", is_system=True
    )
    db_session.add(system)
    await db_session.flush()
    svc = CategoryService(db_session)
    from financial.schemas import CategoryUpdateRequest

    with pytest.raises(CategoryOwnershipError):
        await svc.update_category(
            user.id, system.id, CategoryUpdateRequest(name="Hacked")
        )


async def test_user_category_crud(db_session) -> None:
    """User category crud."""
    user = await make_user(db_session)
    svc = CategoryService(db_session)
    cat = await svc.create_category(
        user.id, CategoryCreateRequest(name="Food", type="expense")
    )
    assert cat.user_id == user.id
    assert cat.is_system is False
    fetched = await svc.get_category(user.id, cat.id)
    assert fetched.name == "Food"
    await svc.delete_category(user.id, cat.id)
    with pytest.raises(CategoryNotFound):
        await svc.get_category(user.id, cat.id)


# --- Transaction service: balance consistency -------------------------------
async def test_create_posted_expense_decreases_balance(db_session) -> None:
    """Create posted expense decreases balance."""
    user = await make_user(db_session)
    acc = await make_account(db_session, user_id=user.id, current_balance=500)
    repo = __import__(
        "financial.repository", fromlist=["TransactionRepository"]
    ).TransactionRepository(db_session)
    svc = TransactionService(db_session, repository=repo)
    await svc.create_transaction(
        user.id,
        TransactionCreateRequest(
            account_id=acc.id,
            amount=100,
            transaction_type="expense",
            transaction_date=datetime.now(UTC),
        ),
    )
    refreshed = await AccountService(db_session).get_account(user.id, acc.id)
    assert refreshed.current_balance == 400


async def test_create_posted_income_increases_balance(db_session) -> None:
    """Create posted income increases balance."""
    user = await make_user(db_session)
    acc = await make_account(db_session, user_id=user.id, current_balance=500)
    repo = __import__(
        "financial.repository", fromlist=["TransactionRepository"]
    ).TransactionRepository(db_session)
    svc = TransactionService(db_session, repository=repo)
    await svc.create_transaction(
        user.id,
        TransactionCreateRequest(
            account_id=acc.id,
            amount=200,
            transaction_type="income",
            transaction_date=datetime.now(UTC),
        ),
    )
    refreshed = await AccountService(db_session).get_account(user.id, acc.id)
    assert refreshed.current_balance == 700


async def test_pending_transaction_does_not_move_balance(db_session) -> None:
    """Pending transaction does not move balance."""
    user = await make_user(db_session)
    acc = await make_account(db_session, user_id=user.id, current_balance=500)
    repo = __import__(
        "financial.repository", fromlist=["TransactionRepository"]
    ).TransactionRepository(db_session)
    svc = TransactionService(db_session, repository=repo)
    await svc.create_transaction(
        user.id,
        TransactionCreateRequest(
            account_id=acc.id,
            amount=999,
            transaction_type="expense",
            transaction_date=datetime.now(UTC),
            status="pending",
        ),
    )
    refreshed = await AccountService(db_session).get_account(user.id, acc.id)
    assert refreshed.current_balance == 500


async def test_delete_transaction_rolls_back_balance(db_session) -> None:
    """Delete transaction rolls back balance."""
    user = await make_user(db_session)
    acc = await make_account(db_session, user_id=user.id, current_balance=500)
    repo = __import__(
        "financial.repository", fromlist=["TransactionRepository"]
    ).TransactionRepository(db_session)
    svc = TransactionService(db_session, repository=repo)
    txn = await svc.create_transaction(
        user.id,
        TransactionCreateRequest(
            account_id=acc.id,
            amount=100,
            transaction_type="expense",
            transaction_date=datetime.now(UTC),
        ),
    )
    assert (
        await AccountService(db_session).get_account(user.id, acc.id)
    ).current_balance == 400
    await svc.delete_transaction(user.id, txn.id)
    assert (
        await AccountService(db_session).get_account(user.id, acc.id)
    ).current_balance == 500


async def test_update_transaction_reverses_and_reapplies(db_session) -> None:
    """Update transaction reverses and reapplies."""
    user = await make_user(db_session)
    acc = await make_account(db_session, user_id=user.id, current_balance=500)
    repo = __import__(
        "financial.repository", fromlist=["TransactionRepository"]
    ).TransactionRepository(db_session)
    svc = TransactionService(db_session, repository=repo)
    txn = await svc.create_transaction(
        user.id,
        TransactionCreateRequest(
            account_id=acc.id,
            amount=100,
            transaction_type="expense",
            transaction_date=datetime.now(UTC),
        ),
    )
    assert (
        await AccountService(db_session).get_account(user.id, acc.id)
    ).current_balance == 400
    # Change expense 100 -> income 250.
    from financial.schemas import TransactionUpdateRequest

    await svc.update_transaction(
        user.id,
        txn.id,
        TransactionUpdateRequest(
            amount=250, transaction_type="income"
        ),
    )
    # 500 - (-100) + 250 = 850
    assert (
        await AccountService(db_session).get_account(user.id, acc.id)
    ).current_balance == 850


async def test_create_transaction_rejects_other_users_account(
    db_session,
) -> None:
    """Create transaction rejects other users account."""
    user = await make_user(db_session)
    other = await make_user(db_session, email="o@example.com")
    acc = await make_account(db_session, user_id=other.id)
    repo = __import__(
        "financial.repository", fromlist=["TransactionRepository"]
    ).TransactionRepository(db_session)
    svc = TransactionService(db_session, repository=repo)
    from financial.exceptions import AccountNotFound

    with pytest.raises(AccountNotFound):
        await svc.create_transaction(
            user.id,
            TransactionCreateRequest(
                account_id=acc.id,
                amount=10,
                transaction_type="expense",
                transaction_date=datetime.now(UTC),
            ),
        )
