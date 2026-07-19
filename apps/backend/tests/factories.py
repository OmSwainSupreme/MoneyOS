"""Test factories for inserting minimal domain rows.

Provides a helper to create a bare ``auth.User`` row directly via the ORM so
tests can reference a real FK parent without going through the auth service
(password hashing, tokens). This is intentionally lightweight - it exists only
to satisfy the ``user_profiles.user_id`` foreign key in tests.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import User
from auth.security import hash_password
from financial.models import Account, Category, Transaction


async def make_user(
    session: AsyncSession, *, email: str | None = None, full_name: str = "Test User"
) -> User:
    """Insert and flush a User row, returning the persisted instance.

    Args:
        session: An active async session.
        email: Optional email; a unique one is generated when omitted.
        full_name: Display name stored on the user.

    Returns:
        The flushed :class:`~auth.models.User` (id populated).
    """
    if email is None:
        email = f"user-{uuid.uuid4().hex[:12]}@example.com"
    user = User(
        email=email,
        password_hash=hash_password("Sup3rSecret!Pass"),
        full_name=full_name,
    )
    session.add(user)
    await session.flush()
    return user


async def make_account(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    name: str = "Test Account",
    account_type: str = "savings",
    currency: str = "INR",
    opening_balance: float = 0,
    current_balance: float = 0,
) -> Account:
    """Insert and flush an Account row owned by ``user_id``."""
    account = Account(
        user_id=user_id,
        name=name,
        account_type=account_type,
        currency=currency,
        opening_balance=opening_balance,
        current_balance=current_balance,
        is_active=True,
    )
    session.add(account)
    await session.flush()
    return account


async def make_category(
    session: AsyncSession,
    *,
    user_id: uuid.UUID | None = None,
    name: str = "Test Category",
    type: str = "expense",
    is_system: bool = False,
) -> Category:
    """Insert and flush a Category (user-owned by default)."""
    category = Category(
        user_id=user_id,
        name=name,
        type=type,
        is_system=is_system,
    )
    session.add(category)
    await session.flush()
    return category


async def make_transaction(
    session: AsyncSession,
    *,
    account_id: uuid.UUID,
    category_id: uuid.UUID | None = None,
    amount: float = 100,
    transaction_type: str = "expense",
    status: str = "posted",
    source: str = "manual",
) -> Transaction:
    """Insert and flush a Transaction row for ``account_id``."""
    txn = Transaction(
        account_id=account_id,
        category_id=category_id,
        amount=amount,
        transaction_type=transaction_type,
        status=status,
        source=source,
        transaction_date=datetime.now(timezone.utc),
    )
    session.add(txn)
    await session.flush()
    return txn
