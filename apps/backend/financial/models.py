"""Financial-domain ORM models.

This module is the canonical financial data model for MoneyOS. Every future
module (statement parsing, analytics, the AI/decision engine) MUST consume
these models rather than defining its own financial structures.

Three entities live here:

* :class:`Account` - a user-owned financial account (bank, card, wallet, ...).
* :class:`Category` - a transaction category; ``is_system`` categories are
  shared across all users, while user-created categories are scoped to a user.
* :class:`Transaction` - a single money movement tied to an account and an
  optional category.

All models inherit from the shared declarative :class:`~database.base.Base` so
their tables register with the single metadata object that Alembic targets.

Enum-backed option sets (account types, transaction types, status, source,
category types) are enumerated here as ``str`` enumerations and mirrored as
PostgreSQL ``CHECK`` constraints so the database rejects invalid values
independently of the application.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from database.base import Base
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

# --- Canonical option sets -------------------------------------------------
# Kept as module constants so the schema, service validation, repository
# defaults, and Pydantic schemas stay in one place.

ACCOUNT_TYPES: tuple[str, ...] = (
    "savings",
    "current",
    "credit_card",
    "cash",
    "wallet",
    "investment",
)

DEFAULT_CURRENCY = "INR"

# Category types.
CATEGORY_TYPES: tuple[str, ...] = ("income", "expense", "transfer")

# Transaction classification.
TRANSACTION_TYPES: tuple[str, ...] = ("income", "expense", "transfer")

# Transaction lifecycle status.
TRANSACTION_STATUSES: tuple[str, ...] = ("pending", "posted", "failed")

# Provenance of a transaction row.
TRANSACTION_SOURCES: tuple[str, ...] = ("manual", "statement", "import")


class AccountType(enum.StrEnum):
    """Type of financial account."""

    SAVINGS = "savings"
    CURRENT = "current"
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    WALLET = "wallet"
    INVESTMENT = "investment"


class CategoryType(enum.StrEnum):
    """Direction a category classifies."""

    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class TransactionType(enum.StrEnum):
    """Business classification of a transaction."""

    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class TransactionStatus(enum.StrEnum):
    """Lifecycle status of a transaction."""

    PENDING = "pending"
    POSTED = "posted"
    FAILED = "failed"


class TransactionSource(enum.StrEnum):
    """Provenance of a transaction row."""

    MANUAL = "manual"
    STATEMENT = "statement"
    IMPORT = "import"


class Account(Base):
    """A user-owned financial account.

    One user may own many accounts. Deleting the parent ``User`` cascades to
    the account and (via the account) its transactions, so a user is never left
    with orphaned financial data.
    """

    __tablename__ = "accounts"

    __table_args__ = (
        CheckConstraint(
            "account_type IN ('savings', 'current', 'credit_card', 'cash', "
            "'wallet', 'investment')",
            name="ck_accounts_check_accounts_account_type",
        ),
        CheckConstraint(
            "currency = UPPER(currency)",
            name="ck_accounts_check_accounts_currency_upper",
        ),
        CheckConstraint(
            "length(name) > 0",
            name="ck_accounts_check_accounts_non_empty_name",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    account_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=AccountType.SAVINGS.value,
    )
    institution_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default=DEFAULT_CURRENCY,
    )
    opening_balance: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0,
    )
    current_balance: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=0,
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Category(Base):
    """A transaction category.

    ``is_system`` categories carry a ``NULL`` ``user_id`` and are shared by all
    users; user-created categories are scoped to a single ``user_id``. A
    category is always one of income/expense/transfer.
    """

    __tablename__ = "categories"

    __table_args__ = (
        CheckConstraint(
            "type IN ('income', 'expense', 'transfer')",
            name="ck_categories_check_categories_type",
        ),
        CheckConstraint(
            "length(name) > 0",
            name="ck_categories_check_categories_non_empty_name",
        ),
        # System categories are global (user_id IS NULL); user categories are
        # owned. A user category must have a user_id; a system one must not.
        CheckConstraint(
            "(is_system AND user_id IS NULL) OR "
            "(NOT is_system AND user_id IS NOT NULL)",
            name="ck_categories_check_categories_system_ownership",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=CategoryType.EXPENSE.value,
    )
    color: Mapped[str | None] = mapped_column(
        String(7),
        nullable=True,
    )
    icon: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    is_system: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class Transaction(Base):
    """A single money movement belonging to an account.

    ``amount`` is always stored as a **positive** magnitude; the direction is
    given by ``transaction_type`` (income/expense/transfer). Transfers are
    represented as transactions tagged ``transaction_type = 'transfer'`` on the
    source (and, if desired, a matching one on the destination) account - this
    phase does not implement transfer balancing logic beyond this
    representation.
    """

    __tablename__ = "transactions"

    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('income', 'expense', 'transfer')",
            name="ck_transactions_check_transactions_transaction_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'posted', 'failed')",
            name="ck_transactions_check_transactions_status",
        ),
        CheckConstraint(
            "source IN ('manual', 'statement', 'import')",
            name="ck_transactions_check_transactions_source",
        ),
        CheckConstraint(
            "amount >= 0",
            name="ck_transactions_check_transactions_positive_amount",
        ),
        # A failed transaction may carry any type; only posted/pending need a
        # category, but we keep categories optional to allow drafting rows.
        CheckConstraint(
            "length(coalesce(merchant, '')) >= 0",
            name="ck_transactions_check_transactions_merchant_len",
        ),
        # Composite index to scope a user's transactions by account + date, the
        # most common read pattern (statement views, date-range filters).
        Index(
            "ix_transactions_account_date",
            "account_id",
            "transaction_date",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        default=uuid.uuid4,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    amount: Mapped[float] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=TransactionType.EXPENSE.value,
    )
    merchant: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=func.now(),
    )
    reference_number: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=TransactionSource.MANUAL.value,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=TransactionStatus.POSTED.value,
    )
    notes: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
