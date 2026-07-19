"""Add the financial domain (accounts, categories, transactions).

Revision ID: a1b2c3d4e5f
Revises: d490147de740
Create Date: 2026-07-19 00:00:00.000000

Establishes the canonical financial data model used by every future module.

* ``accounts`` - user-owned financial accounts (FK users ON DELETE CASCADE).
* ``categories`` - transaction categories; system categories have a NULL
  user_id and are shared; user categories are scoped to one user.
* ``transactions`` - money movements tied to an account (FK accounts ON DELETE
  CASCADE) and an optional category (FK categories ON DELETE SET NULL).

Constraint names follow the MetaData naming_convention
(``ck_<table>_<name>``) so they are identical to what ``Base.metadata.create_all``
emits for the ORM models.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f"
down_revision: str | None = "d490147de740"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the financial-domain schema."""
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # --- accounts ----------------------------------------------------------
    op.create_table(
        "accounts",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            index=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "account_type",
            sa.String(length=32),
            server_default="savings",
            nullable=False,
        ),
        sa.Column("institution_name", sa.String(length=255), nullable=True),
        sa.Column(
            "currency", sa.String(length=8), server_default="INR", nullable=False
        ),
        sa.Column(
            "opening_balance",
            sa.Numeric(precision=18, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "current_balance",
            sa.Numeric(precision=18, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accounts")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_accounts_user_id_users"),
            ondelete="CASCADE",
        ),
    )
    op.execute(
        "ALTER TABLE accounts ADD CONSTRAINT "
        "ck_accounts_check_accounts_account_type "
        "CHECK (account_type IN ('savings', 'current', 'credit_card', "
        "'cash', 'wallet', 'investment'))"
    )
    op.execute(
        "ALTER TABLE accounts ADD CONSTRAINT "
        "ck_accounts_check_accounts_currency_upper "
        "CHECK (currency = UPPER(currency))"
    )
    op.execute(
        "ALTER TABLE accounts ADD CONSTRAINT "
        "ck_accounts_check_accounts_non_empty_name "
        "CHECK (length(name) > 0)"
    )

    # --- categories --------------------------------------------------------
    op.create_table(
        "categories",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            index=True,
            nullable=True,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "type",
            sa.String(length=32),
            server_default="expense",
            nullable=False,
        ),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column("icon", sa.String(length=64), nullable=True),
        sa.Column(
            "is_system",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_categories_user_id_users"),
            ondelete="CASCADE",
        ),
    )
    op.execute(
        "ALTER TABLE categories ADD CONSTRAINT "
        "ck_categories_check_categories_type "
        "CHECK (type IN ('income', 'expense', 'transfer'))"
    )
    op.execute(
        "ALTER TABLE categories ADD CONSTRAINT "
        "ck_categories_check_categories_non_empty_name "
        "CHECK (length(name) > 0)"
    )
    op.execute(
        "ALTER TABLE categories ADD CONSTRAINT "
        "ck_categories_check_categories_system_ownership "
        "CHECK ((is_system AND user_id IS NULL) OR "
        "(NOT is_system AND user_id IS NOT NULL))"
    )

    # --- transactions ------------------------------------------------------
    op.create_table(
        "transactions",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "account_id",
            sa.UUID(),
            index=True,
            nullable=False,
        ),
        sa.Column(
            "category_id",
            sa.UUID(),
            index=True,
            nullable=True,
        ),
        sa.Column(
            "amount",
            sa.Numeric(precision=18, scale=2),
            nullable=False,
        ),
        sa.Column(
            "transaction_type",
            sa.String(length=32),
            server_default="expense",
            nullable=False,
        ),
        sa.Column("merchant", sa.String(length=255), nullable=True),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column(
            "transaction_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            index=True,
            nullable=False,
        ),
        sa.Column("reference_number", sa.String(length=128), index=True, nullable=True),
        sa.Column(
            "source",
            sa.String(length=32),
            server_default="manual",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="posted",
            nullable=False,
        ),
        sa.Column("notes", sa.String(length=2048), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_transactions_account_id_accounts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_transactions_category_id_categories"),
            ondelete="SET NULL",
        ),
    )
    op.execute(
        "ALTER TABLE transactions ADD CONSTRAINT "
        "ck_transactions_check_transactions_transaction_type "
        "CHECK (transaction_type IN ('income', 'expense', 'transfer'))"
    )
    op.execute(
        "ALTER TABLE transactions ADD CONSTRAINT "
        "ck_transactions_check_transactions_status "
        "CHECK (status IN ('pending', 'posted', 'failed'))"
    )
    op.execute(
        "ALTER TABLE transactions ADD CONSTRAINT "
        "ck_transactions_check_transactions_source "
        "CHECK (source IN ('manual', 'statement', 'import'))"
    )
    op.execute(
        "ALTER TABLE transactions ADD CONSTRAINT "
        "ck_transactions_check_transactions_positive_amount "
        "CHECK (amount >= 0)"
    )
    op.execute(
        "ALTER TABLE transactions ADD CONSTRAINT "
        "ck_transactions_check_transactions_merchant_len "
        "CHECK (length(coalesce(merchant, '')) >= 0)"
    )
    op.create_index(
        "ix_transactions_account_date",
        "transactions",
        ["account_id", "transaction_date"],
    )


def downgrade() -> None:
    """Revert the financial-domain schema."""
    op.drop_index("ix_transactions_account_date", table_name="transactions")
    op.execute(
        "ALTER TABLE transactions DROP CONSTRAINT "
        "ck_transactions_check_transactions_merchant_len"
    )
    op.execute(
        "ALTER TABLE transactions DROP CONSTRAINT "
        "ck_transactions_check_transactions_positive_amount"
    )
    op.execute(
        "ALTER TABLE transactions DROP CONSTRAINT "
        "ck_transactions_check_transactions_source"
    )
    op.execute(
        "ALTER TABLE transactions DROP CONSTRAINT "
        "ck_transactions_check_transactions_status"
    )
    op.execute(
        "ALTER TABLE transactions DROP CONSTRAINT "
        "ck_transactions_check_transactions_transaction_type"
    )
    op.drop_table("transactions")

    op.execute(
        "ALTER TABLE categories DROP CONSTRAINT "
        "ck_categories_check_categories_system_ownership"
    )
    op.execute(
        "ALTER TABLE categories DROP CONSTRAINT "
        "ck_categories_check_categories_non_empty_name"
    )
    op.execute(
        "ALTER TABLE categories DROP CONSTRAINT "
        "ck_categories_check_categories_type"
    )
    op.drop_table("categories")

    op.execute(
        "ALTER TABLE accounts DROP CONSTRAINT "
        "ck_accounts_check_accounts_non_empty_name"
    )
    op.execute(
        "ALTER TABLE accounts DROP CONSTRAINT "
        "ck_accounts_check_accounts_currency_upper"
    )
    op.execute(
        "ALTER TABLE accounts DROP CONSTRAINT "
        "ck_accounts_check_accounts_account_type"
    )
    op.drop_table("accounts")
