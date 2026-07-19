"""Financial-domain data-access layer.

The repositories are the only modules that touch the ORM for the financial
entities. They contain **no business logic** - just persistence operations
(create, fetch, list, update, delete) scoped to a ``user_id`` where ownership
applies. Transaction boundaries are owned by the service layer, which passes in
an already-bound :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from financial.exceptions import (
    AccountNotFound,
    CategoryNotFound,
    TransactionNotFound,
)
from financial.models import Account, Category, Transaction
from financial.schemas import (
    AccountFilter,
    AccountUpdateRequest,
    CategoryFilter,
    CategoryUpdateRequest,
    TransactionFilter,
    TransactionUpdateRequest,
)


class AccountRepository:
    """Async persistence for :class:`Account`."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to an async session."""
        self._session = session

    async def get_by_id(
        self, account_id: uuid.UUID, user_id: uuid.UUID
    ) -> Account | None:
        """Return the user's account or ``None`` if absent/not owned."""
        result = await self._session.execute(
            select(Account).where(
                Account.id == account_id, Account.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_or_raise(
        self, account_id: uuid.UUID, user_id: uuid.UUID
    ) -> Account:
        """Return the user's account or raise :class:`AccountNotFound`."""
        account = await self.get_by_id(account_id, user_id)
        if account is None:
            raise AccountNotFound(
                f"Account {account_id} not found for user {user_id}."
            )
        return account

    async def adjust_balance(
        self, account_id: uuid.UUID, delta: object
    ) -> None:
        """Atomically adjust ``current_balance`` at the database level.

        Issues ``UPDATE accounts SET current_balance = current_balance + :delta``
        so the new balance is computed inside Postgres rather than in Python.
        This removes the read-modify-write race that a fetched-then-mutated
        balance would expose under concurrent transactions, and keeps the value
        exact (the column is ``Numeric(18, 2)``). No row is fetched first, so
        there is no window for a lost update.
        """
        from sqlalchemy import update

        await self._session.execute(
            update(Account)
            .where(Account.id == account_id)
            .values(current_balance=Account.current_balance + delta)
        )

    async def list_for_user(
        self, user_id: uuid.UUID, filters: AccountFilter | None = None
    ) -> list[Account]:
        """List the user's accounts, optionally filtered."""
        stmt = select(Account).where(Account.user_id == user_id)
        if filters is not None:
            if filters.account_type is not None:
                stmt = stmt.where(
                    Account.account_type == filters.account_type.value
                )
            if filters.is_active is not None:
                stmt = stmt.where(Account.is_active == filters.is_active)
            stmt = stmt.limit(filters.limit).offset(filters.offset)
        else:
            stmt = stmt.limit(100)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, user_id: uuid.UUID, **fields: object) -> Account:
        """Persist a new account owned by ``user_id``.

        The caller owns the enclosing transaction; the row is flushed so its
        generated columns are populated without committing.
        """
        account = Account(user_id=user_id, **fields)  # type: ignore[arg-type]
        self._session.add(account)
        await self._session.flush()
        return account

    async def update(
        self, account: Account, payload: AccountUpdateRequest
    ) -> Account:
        """Apply the non-``None`` fields of ``payload`` to ``account``."""
        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(account, field, value)
        await self._session.flush()
        return account

    async def delete(self, account: Account) -> None:
        """Hard-delete the account (cascades to its transactions)."""
        await self._session.delete(account)
        await self._session.flush()

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        """Count accounts owned by the user (for guard checks)."""
        result = await self._session.execute(
            select(func.count()).select_from(Account).where(
                Account.user_id == user_id
            )
        )
        return int(result.scalar_one())


class CategoryRepository:
    """Async persistence for :class:`Category`.

    Categories are visible to a user when they own the category OR it is a
    system category (``is_system`` is true). Mutations are only allowed on
    user-owned categories.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to an async session."""
        self._session = session

    async def get_by_id(
        self, category_id: uuid.UUID, user_id: uuid.UUID
    ) -> Category | None:
        """Return a category if it is owned by the user or system-wide."""
        result = await self._session.execute(
            select(Category).where(
                Category.id == category_id,
                (Category.user_id == user_id) | (Category.is_system.is_(True)),
            )
        )
        return result.scalar_one_or_none()

    async def get_or_raise(
        self, category_id: uuid.UUID, user_id: uuid.UUID
    ) -> Category:
        """Return the category or raise :class:`CategoryNotFound`."""
        category = await self.get_by_id(category_id, user_id)
        if category is None:
            raise CategoryNotFound(
                f"Category {category_id} not found for user {user_id}."
            )
        return category

    async def list_for_user(
        self, user_id: uuid.UUID, filters: CategoryFilter | None = None
    ) -> list[Category]:
        """List categories visible to the user (owned + system).

        By default system categories are included; pass
        ``include_system=False`` to list only the user's own categories.
        """
        stmt = select(Category).where(
            (Category.user_id == user_id) | (Category.is_system.is_(True))
        )
        if filters is not None:
            if filters.type is not None:
                stmt = stmt.where(Category.type == filters.type.value)
            if not filters.include_system:
                stmt = stmt.where(Category.user_id == user_id)
            stmt = stmt.limit(filters.limit).offset(filters.offset)
        else:
            stmt = stmt.limit(100)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, user_id: uuid.UUID, **fields: object) -> Category:
        """Persist a new user-owned category."""
        category = Category(
            user_id=user_id, is_system=False, **fields
        )  # type: ignore[arg-type]
        self._session.add(category)
        await self._session.flush()
        return category

    async def update(
        self, category: Category, payload: CategoryUpdateRequest
    ) -> Category:
        """Apply the non-``None`` fields of ``payload`` to ``category``."""
        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(category, field, value)
        await self._session.flush()
        return category

    async def delete(self, category: Category) -> None:
        """Hard-delete a user-owned category (transactions SET NULL)."""
        await self._session.delete(category)
        await self._session.flush()

    async def get_system_categories(self) -> list[Category]:
        """Return all system categories (shared baseline)."""
        result = await self._session.execute(
            select(Category).where(Category.is_system.is_(True))
        )
        return list(result.scalars().all())


class TransactionRepository:
    """Async persistence for :class:`Transaction`.

    Every read is scoped to accounts owned by the requesting user, so a user
    can never see another user's transactions.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to an async session."""
        self._session = session

    async def get_by_id(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID
    ) -> Transaction | None:
        """Return a transaction if its account belongs to the user."""
        result = await self._session.execute(
            select(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .where(
                Transaction.id == transaction_id,
                Account.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_or_raise(
        self, transaction_id: uuid.UUID, user_id: uuid.UUID
    ) -> Transaction:
        """Return the transaction or raise :class:`TransactionNotFound`."""
        txn = await self.get_by_id(transaction_id, user_id)
        if txn is None:
            raise TransactionNotFound(
                f"Transaction {transaction_id} not found for user {user_id}."
            )
        return txn

    async def list_for_user(
        self, user_id: uuid.UUID, filters: TransactionFilter | None = None
    ) -> list[Transaction]:
        """List the user's transactions, optionally filtered.

        Always joined through ``accounts`` so results are limited to accounts
        the user owns.
        """
        stmt = (
            select(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .where(Account.user_id == user_id)
        )
        if filters is not None:
            if filters.account_id is not None:
                stmt = stmt.where(Transaction.account_id == filters.account_id)
            if filters.category_id is not None:
                stmt = stmt.where(
                    Transaction.category_id == filters.category_id
                )
            if filters.transaction_type is not None:
                stmt = stmt.where(
                    Transaction.transaction_type
                    == filters.transaction_type.value
                )
            if filters.status is not None:
                stmt = stmt.where(Transaction.status == filters.status.value)
            if filters.source is not None:
                stmt = stmt.where(Transaction.source == filters.source.value)
            if filters.merchant is not None:
                pattern = f"%{filters.merchant}%"
                stmt = stmt.where(Transaction.merchant.ilike(pattern))
            if filters.reference_number is not None:
                stmt = stmt.where(
                    Transaction.reference_number == filters.reference_number
                )
            if filters.from_date is not None:
                stmt = stmt.where(
                    Transaction.transaction_date >= filters.from_date
                )
            if filters.to_date is not None:
                stmt = stmt.where(
                    Transaction.transaction_date <= filters.to_date
                )
            stmt = stmt.order_by(Transaction.transaction_date.desc())
            stmt = stmt.limit(filters.limit).offset(filters.offset)
        else:
            stmt = stmt.order_by(
                Transaction.transaction_date.desc()
            ).limit(100)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **fields: object) -> Transaction:
        """Persist a new transaction. The caller validates ownership."""
        txn = Transaction(**fields)  # type: ignore[arg-type]
        self._session.add(txn)
        await self._session.flush()
        return txn

    async def update(
        self, txn: Transaction, payload: TransactionUpdateRequest
    ) -> Transaction:
        """Apply the non-``None`` fields of ``payload`` to ``txn``."""
        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(txn, field, value)
        await self._session.flush()
        return txn

    async def delete(self, txn: Transaction) -> None:
        """Hard-delete the transaction."""
        await self._session.delete(txn)
        await self._session.flush()
