"""Repository-layer tests for the financial domain.

Exercises the three repositories directly against a real Postgres schema built
by ``create_all``. Asserts ownership scoping (a user never sees another user's
rows), category visibility (owned + system), and the basic CRUD lifecycle.

Skipped automatically when ``TEST_DATABASE_URL`` is not configured.
"""

from __future__ import annotations

import pytest
from financial.exceptions import (
    AccountNotFound,
    CategoryNotFound,
    TransactionNotFound,
)
from financial.models import Category
from financial.repository import (
    AccountRepository,
    CategoryRepository,
    TransactionRepository,
)
from financial.schemas import AccountFilter, CategoryFilter, TransactionFilter

from tests.factories import (
    make_user,
)

pytestmark = pytest.mark.requires_postgres


async def test_account_create_and_get_scoped(db_session) -> None:
    """Account create and get scoped."""
    user = await make_user(db_session)
    other = await make_user(db_session, email="other@example.com")
    repo = AccountRepository(db_session)

    acc = await repo.create(
        user.id, name="Savings", account_type="savings", currency="INR"
    )
    assert acc.id is not None
    assert acc.user_id == user.id

    # Owner can fetch it.
    fetched = await repo.get_or_raise(acc.id, user.id)
    assert fetched.id == acc.id

    # Another user cannot see it.
    assert await repo.get_by_id(acc.id, other.id) is None
    with pytest.raises(AccountNotFound):
        await repo.get_or_raise(acc.id, other.id)


async def test_account_list_filter_by_type(db_session) -> None:
    """Account list filter by type."""
    user = await make_user(db_session)
    repo = AccountRepository(db_session)
    await repo.create(
        user.id, name="A", account_type="savings", currency="INR"
    )
    await repo.create(
        user.id,
        name="B",
        account_type="cash",
        currency="INR",
        is_active=False,
    )
    inactive = await repo.list_for_user(
        user.id, AccountFilter(account_type="cash", is_active=False)
    )
    assert len(inactive) == 1
    assert inactive[0].account_type == "cash"


async def test_account_update_partial(db_session) -> None:
    """Account update partial."""
    user = await make_user(db_session)
    repo = AccountRepository(db_session)
    acc = await repo.create(
        user.id, name="A", account_type="savings", currency="INR"
    )
    from financial.schemas import AccountUpdateRequest

    updated = await repo.update(
        acc, AccountUpdateRequest(name="Renamed", is_active=False)
    )
    assert updated.name == "Renamed"
    assert updated.is_active is False


async def test_account_delete(db_session) -> None:
    """Account delete."""
    user = await make_user(db_session)
    repo = AccountRepository(db_session)
    acc = await repo.create(
        user.id, name="A", account_type="savings", currency="INR"
    )
    await repo.delete(acc)
    assert await repo.get_by_id(acc.id, user.id) is None


async def test_category_visibility_owned_and_system(db_session) -> None:
    """Category visibility owned and system."""
    user = await make_user(db_session)
    repo = CategoryRepository(db_session)

    # System category shared across users.
    system = Category(
        user_id=None, name="System Cat", type="expense", is_system=True
    )
    db_session.add(system)
    await db_session.flush()

    # User-owned category.
    owned = await repo.create(user.id, name="Mine", type="expense")

    visible = await repo.list_for_user(user.id)
    ids = {c.id for c in visible}
    assert owned.id in ids
    assert system.id in ids

    # Excluding system returns only owned.
    owned_only = await repo.list_for_user(
        user.id, CategoryFilter(include_system=False)
    )
    assert all(c.user_id == user.id for c in owned_only)
    assert system.id not in {c.id for c in owned_only}


async def test_category_get_raises_when_unowned(db_session) -> None:
    """Category get raises when unowned."""
    user = await make_user(db_session)
    other = await make_user(db_session, email="o2@example.com")
    repo = CategoryRepository(db_session)
    cat = await repo.create(other.id, name="Theirs", type="expense")

    # `get_by_id` allows system but not another user's category.
    assert await repo.get_by_id(cat.id, user.id) is None
    with pytest.raises(CategoryNotFound):
        await repo.get_or_raise(cat.id, user.id)


async def test_transaction_create_and_scope(db_session) -> None:
    """Transaction create and scope."""
    user = await make_user(db_session)
    other = await make_user(db_session, email="o3@example.com")
    repo = AccountRepository(db_session)
    txn_repo = TransactionRepository(db_session)

    acc = await repo.create(
        user.id, name="A", account_type="savings", currency="INR"
    )
    txn = await txn_repo.create(
        account_id=acc.id,
        amount=50,
        transaction_type="income",
        status="posted",
        source="manual",
    )
    assert txn.id is not None

    # Owner can fetch, another user cannot.
    assert await txn_repo.get_by_id(txn.id, user.id) is not None
    assert await txn_repo.get_by_id(txn.id, other.id) is None
    with pytest.raises(TransactionNotFound):
        await txn_repo.get_or_raise(txn.id, other.id)


async def test_transaction_filter_by_account(db_session) -> None:
    """Transaction filter by account."""
    user = await make_user(db_session)
    repo = AccountRepository(db_session)
    txn_repo = TransactionRepository(db_session)

    acc1 = await repo.create(
        user.id, name="A1", account_type="savings", currency="INR"
    )
    acc2 = await repo.create(
        user.id, name="A2", account_type="cash", currency="INR"
    )
    await txn_repo.create(
        account_id=acc1.id,
        amount=10,
        transaction_type="expense",
        status="posted",
        source="manual",
    )
    await txn_repo.create(
        account_id=acc2.id,
        amount=20,
        transaction_type="income",
        status="posted",
        source="manual",
    )
    filtered = await txn_repo.list_for_user(
        user.id, TransactionFilter(account_id=acc1.id)
    )
    assert len(filtered) == 1
    assert filtered[0].account_id == acc1.id
