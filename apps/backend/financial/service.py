"""Financial-domain business logic and transaction orchestration.

The service owns transaction boundaries (via
:func:`database.session.transaction`), enforces ownership (a user only ever
touches their own data), keeps account balances consistent with accepted
transactions, and validates enum/currency/amount rules. It depends on the
repositories for persistence and never touches the ORM directly.

Account balance safety: ``current_balance`` is treated as a stored, derived
value. On create with ``status = posted`` the balance is adjusted by the
transaction amount in the transaction's direction; non-posted (pending/
failed) transactions do not move the balance. Reversing a posted transaction to
``failed``/``pending`` rolls the balance back. This keeps malformed requests
from corrupting balances: the adjustment is always performed inside the same
committed transaction as the row write, so the two can never diverge.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from database.session import transaction
from sqlalchemy.ext.asyncio import AsyncSession

from financial.exceptions import (
    CategoryOwnershipError,
)
from financial.models import (
    DEFAULT_CURRENCY,
    AccountType,
    CategoryType,
    TransactionSource,
    TransactionStatus,
    TransactionType,
)
from financial.repository import (
    AccountRepository,
    CategoryRepository,
    TransactionRepository,
)
from financial.schemas import (
    AccountCreateRequest,
    AccountFilter,
    AccountResponse,
    AccountUpdateRequest,
    CategoryCreateRequest,
    CategoryFilter,
    CategoryResponse,
    CategoryUpdateRequest,
    TransactionCreateRequest,
    TransactionFilter,
    TransactionResponse,
    TransactionUpdateRequest,
)

_ACCOUNT_TYPE_SET = frozenset(t.value for t in AccountType)
_CATEGORY_TYPE_SET = frozenset(t.value for t in CategoryType)
_TXN_TYPE_SET = frozenset(t.value for t in TransactionType)
_STATUS_SET = frozenset(s.value for s in TransactionStatus)
_SOURCE_SET = frozenset(s.value for s in TransactionSource)


class AccountService:
    """Coordinates account operations across the repository."""

    def __init__(
        self,
        session: AsyncSession,
        repository: AccountRepository | None = None,
    ) -> None:
        """Bind a session and an optional account repository."""
        self._session = session
        self._accounts = repository or AccountRepository(session)

    async def create_account(
        self, user_id: uuid.UUID, payload: AccountCreateRequest
    ) -> AccountResponse:
        """Create a new account owned by ``user_id``."""
        async with transaction(self._session):
            account = await self._accounts.create(
                user_id,
                name=payload.name,
                account_type=payload.account_type.value,
                institution_name=payload.institution_name,
                currency=payload.currency or DEFAULT_CURRENCY,
                opening_balance=payload.opening_balance,
                current_balance=payload.current_balance,
                is_active=True,
            )
        return AccountResponse.model_validate(account)

    async def list_accounts(
        self, user_id: uuid.UUID, filters: AccountFilter | None = None
    ) -> list[AccountResponse]:
        """List ``user_id``'s accounts, optionally filtered."""
        accounts = await self._accounts.list_for_user(user_id, filters)
        return [AccountResponse.model_validate(a) for a in accounts]

    async def get_account(
        self, user_id: uuid.UUID, account_id: uuid.UUID
    ) -> AccountResponse:
        """Fetch a single account owned by ``user_id``."""
        account = await self._accounts.get_or_raise(account_id, user_id)
        return AccountResponse.model_validate(account)

    async def update_account(
        self,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
        payload: AccountUpdateRequest,
    ) -> AccountResponse:
        """Partially update a user-owned account."""
        async with transaction(self._session):
            account = await self._accounts.get_or_raise(account_id, user_id)
            account = await self._accounts.update(account, payload)
        return AccountResponse.model_validate(account)

    async def delete_account(
        self, user_id: uuid.UUID, account_id: uuid.UUID
    ) -> None:
        """Hard-delete the account.

        ON DELETE CASCADE removes its transactions atomically, so no balance is
        left dangling. This is the chosen safe-deletion strategy (documented in
        financial/DEFERRED.md); we do not soft-delete so users get a clear,
        consistent view and the cascade keeps referential integrity.
        """
        async with transaction(self._session):
            account = await self._accounts.get_or_raise(account_id, user_id)
            await self._accounts.delete(account)


class CategoryService:
    """Coordinates category operations across the repository."""

    def __init__(
        self,
        session: AsyncSession,
        repository: CategoryRepository | None = None,
    ) -> None:
        """Bind a session and an optional category repository."""
        self._session = session
        self._categories = repository or CategoryRepository(session)

    async def create_category(
        self, user_id: uuid.UUID, payload: CategoryCreateRequest
    ) -> CategoryResponse:
        """Create a new user-owned category."""
        async with transaction(self._session):
            category = await self._categories.create(
                user_id,
                name=payload.name,
                type=payload.type.value,
                color=payload.color,
                icon=payload.icon,
            )
        return CategoryResponse.model_validate(category)

    async def list_categories(
        self, user_id: uuid.UUID, filters: CategoryFilter | None = None
    ) -> list[CategoryResponse]:
        """List categories visible to ``user_id`` (owned + system)."""
        cats = await self._categories.list_for_user(user_id, filters)
        return [CategoryResponse.model_validate(c) for c in cats]

    async def get_category(
        self, user_id: uuid.UUID, category_id: uuid.UUID
    ) -> CategoryResponse:
        """Fetch a category (owned by the user or a system category)."""
        category = await self._categories.get_or_raise(category_id, user_id)
        return CategoryResponse.model_validate(category)

    async def update_category(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        payload: CategoryUpdateRequest,
    ) -> CategoryResponse:
        """Update a user-owned category (system categories are protected)."""
        async with transaction(self._session):
            category = await self._categories.get_or_raise(
                category_id, user_id
            )
            if category.is_system:
                raise CategoryOwnershipError(
                    "System categories cannot be modified."
                )
            category = await self._categories.update(category, payload)
        return CategoryResponse.model_validate(category)

    async def delete_category(
        self, user_id: uuid.UUID, category_id: uuid.UUID
    ) -> None:
        """Delete a user-owned category (system categories are protected)."""
        async with transaction(self._session):
            category = await self._categories.get_or_raise(
                category_id, user_id
            )
            if category.is_system:
                raise CategoryOwnershipError(
                    "System categories cannot be deleted."
                )
            await self._categories.delete(category)


def _balance_delta(
    transaction_type: str, status: str, amount: object
) -> Decimal:
    """Signed balance delta for an account from a transaction.

    Income increases the balance; expense/transfer decrease it. Only posted
    transactions move the balance. Uses :class:`decimal.Decimal` so currency
    arithmetic stays exact (the column is ``Numeric(18, 2)``; binary floats
    would introduce representation drift). Returns ``Decimal(0)`` otherwise.
    """
    amount_d = Decimal(str(amount))
    if status != TransactionStatus.POSTED.value:
        return Decimal("0")
    sign = (
        Decimal("1")
        if transaction_type == TransactionType.INCOME.value
        else Decimal("-1")
    )
    return sign * amount_d


class TransactionService:
    """Coordinates transaction operations across the repositories."""

    def __init__(
        self,
        session: AsyncSession,
        account_repo: AccountRepository | None = None,
        category_repo: CategoryRepository | None = None,
        repository: TransactionRepository | None = None,
    ) -> None:
        """Bind a session and optional account/category/transaction repos."""
        self._session = session
        self._accounts = account_repo or AccountRepository(session)
        self._categories = category_repo or CategoryRepository(session)
        self._txns = repository or TransactionRepository(session)

    async def create_transaction(
        self, user_id: uuid.UUID, payload: TransactionCreateRequest
    ) -> TransactionResponse:
        """Create a transaction and adjust the account balance atomically."""
        async with transaction(self._session):
            # Ownership: the target account must belong to the user.
            await self._accounts.get_or_raise(payload.account_id, user_id)
            # Optional category must be visible to the user (owned or system).
            if payload.category_id is not None:
                await self._categories.get_or_raise(
                    payload.category_id, user_id
                )
            txn = await self._txns.create(
                account_id=payload.account_id,
                category_id=payload.category_id,
                amount=payload.amount,
                transaction_type=payload.transaction_type.value,
                merchant=payload.merchant,
                description=payload.description,
                transaction_date=payload.transaction_date,
                reference_number=payload.reference_number,
                source=payload.source.value,
                status=payload.status.value,
                notes=payload.notes,
            )
            # Keep the stored balance consistent with the new posted txn. The
            # delta is exact (Decimal) and applied in the same committed
            # transaction via an atomic DB-level UPDATE.
            delta = _balance_delta(
                txn.transaction_type, txn.status, txn.amount
            )
            if delta != 0:
                await self._accounts.adjust_balance(payload.account_id, delta)
        return TransactionResponse.model_validate(txn)

    async def list_transactions(
        self, user_id: uuid.UUID, filters: TransactionFilter | None = None
    ) -> list[TransactionResponse]:
        """List ``user_id``'s transactions, optionally filtered."""
        txns = await self._txns.list_for_user(user_id, filters)
        return [TransactionResponse.model_validate(t) for t in txns]

    async def get_transaction(
        self, user_id: uuid.UUID, transaction_id: uuid.UUID
    ) -> TransactionResponse:
        """Fetch a single transaction belonging to the user's account."""
        txn = await self._txns.get_or_raise(transaction_id, user_id)
        return TransactionResponse.model_validate(txn)

    async def update_transaction(
        self,
        user_id: uuid.UUID,
        transaction_id: uuid.UUID,
        payload: TransactionUpdateRequest,
    ) -> TransactionResponse:
        """Update a transaction and keep the account balance consistent."""
        async with transaction(self._session):
            txn = await self._txns.get_or_raise(transaction_id, user_id)
            await self._accounts.get_or_raise(txn.account_id, user_id)
            # Reverse the old balance effect, then re-apply after update. Both
            # deltas are exact Decimal and the net is written atomically.
            old_delta = _balance_delta(
                txn.transaction_type, txn.status, txn.amount
            )
            txn = await self._txns.update(txn, payload)
            new_delta = _balance_delta(
                txn.transaction_type, txn.status, txn.amount
            )
            net = new_delta - old_delta
            if net != 0:
                await self._accounts.adjust_balance(txn.account_id, net)
        return TransactionResponse.model_validate(txn)

    async def delete_transaction(
        self, user_id: uuid.UUID, transaction_id: uuid.UUID
    ) -> None:
        """Delete a transaction and roll back its balance effect."""
        async with transaction(self._session):
            txn = await self._txns.get_or_raise(transaction_id, user_id)
            await self._accounts.get_or_raise(txn.account_id, user_id)
            # Roll back the balance effect of a previously posted txn.
            old_delta = _balance_delta(
                txn.transaction_type, txn.status, txn.amount
            )
            if old_delta != 0:
                await self._accounts.adjust_balance(
                    txn.account_id, -old_delta
                )
            await self._txns.delete(txn)
