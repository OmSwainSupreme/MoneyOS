"""Read-optimized financial analytics.

Pure query/aggregation layer for the dashboard and analytics endpoints. It
reads through the ORM and computes summaries, monthly rollups, and
category breakdowns entirely in SQL (``func.sum``, ``group_by``) so the
service never loads a user's full transaction history into Python. Every
query is scoped to accounts owned by the requesting user, so cross-user
leakage is impossible by construction.

Currency is assumed single-tenant per request (the first account's currency
wins); multi-currency aggregation is out of scope for the MVP.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from financial.models import Account, Category, Transaction


class AnalyticsService:
    """Aggregates the user's financial data for dashboards/analytics."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _user_account_ids(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        """Return the ids of every account owned by ``user_id``."""
        result = await self._session.execute(
            select(Account.id).where(Account.user_id == user_id)
        )
        return list(result.scalars().all())

    async def _user_currency(self, user_id: uuid.UUID) -> str:
        """Best-effort currency: first non-null account currency."""
        result = await self._session.execute(
            select(Account.currency)
            .where(Account.user_id == user_id)
            .limit(1)
        )
        currency = result.scalar_one_or_none()
        return currency or "INR"

    async def dashboard(
        self, user_id: uuid.UUID, *, limit_recent: int = 10
    ) -> dict:
        """Headline dashboard figures for ``user_id``.

        Returns totals (income/expenses/savings across all months), the current
        total balance across the user's accounts, and the most recent
        transactions.
        """
        account_ids = await self._user_account_ids(user_id)
        currency = await self._user_currency(user_id)

        total_balance = await self._sum_balance(account_ids)
        income = await self._sum_amount(account_ids, "income")
        expenses = await self._sum_amount(account_ids, "expense")
        savings = income - expenses
        recent = await self._recent(account_ids, limit_recent)

        return {
            "currency": currency,
            "total_balance": total_balance,
            "total_income": income,
            "total_expenses": expenses,
            "total_savings": savings,
            "recent_transactions": recent,
        }

    async def monthly_summary(
        self, user_id: uuid.UUID, *, months: int = 12
    ) -> list[dict]:
        """Per-month income, expenses, savings, and net for the user.

        Returns up to ``months`` trailing calendar months, ordered oldest
        first. Months with no activity still appear so the chart is contiguous.
        """
        account_ids = await self._user_account_ids(user_id)
        if not account_ids:
            return []
        rows = await self._monthly_rollup(account_ids, months)
        by_month: dict[str, dict] = {r["month"]: r for r in rows}
        return self._fill_month_gaps(by_month, months)

    async def spending_by_category(
        self, user_id: uuid.UUID, *, months: int = 12
    ) -> list[dict]:
        """Expense totals grouped by category for the trailing window.

        Each entry carries the category id, name, color, and total spent.
        Transactions with no category are bucketed under ``Uncategorized``.
        """
        account_ids = await self._user_account_ids(user_id)
        if not account_ids:
            return []
        cutoff = self._months_ago(months)
        stmt = (
            select(
                Category.id,
                Category.name,
                Category.color,
                func.coalesce(func.sum(Transaction.amount), 0).label("total"),
            )
            .select_from(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .join(
                Category,
                Category.id == Transaction.category_id,
                isouter=True,
            )
            .where(Account.user_id == user_id)
            .where(Transaction.transaction_type == "expense")
            .where(Transaction.status == "posted")
            .where(Transaction.transaction_date >= cutoff)
            .group_by(Category.id, Category.name, Category.color)
            .order_by(func.sum(Transaction.amount).desc())
        )
        result = await self._session.execute(stmt)
        out: list[dict] = []
        for row in result.all():
            name = row.name if row.name is not None else "Uncategorized"
            out.append(
                {
                    "category_id": row.id,
                    "category_name": name,
                    "color": row.color,
                    "total": float(row.total),
                }
            )
        return out

    async def income_vs_expense(
        self, user_id: uuid.UUID, *, months: int = 12
    ) -> list[dict]:
        """Monthly income vs expense pairings (sparse months omitted)."""
        summary = await self.monthly_summary(user_id, months=months)
        return [
            {
                "month": m["month"],
                "income": m["income"],
                "expense": m["expense"],
            }
            for m in summary
        ]

    async def cash_flow(
        self, user_id: uuid.UUID, *, months: int = 12
    ) -> dict:
        """Cash-flow summary over the trailing window.

        Returns per-month ``inflow``/``outflow``/``net`` plus the window
        totals and the resulting balance delta.
        """
        summary = await self.monthly_summary(user_id, months=months)
        total_in = sum(m["income"] for m in summary)
        total_out = sum(m["expense"] for m in summary)
        return {
            "months": [
                {
                    "month": m["month"],
                    "inflow": m["income"],
                    "outflow": m["expense"],
                    "net": m["net"],
                }
                for m in summary
            ],
            "total_inflow": total_in,
            "total_outflow": total_out,
            "total_net": total_in - total_out,
        }

    # --- internals --------------------------------------------------------
    @staticmethod
    def _months_ago(months: int) -> datetime:
        """First moment of the month ``months - 1`` back from now (UTC)."""
        now = datetime.now(timezone.utc)
        year, month = now.year, now.month
        for _ in range(months - 1):
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        return datetime(year, month, 1, tzinfo=timezone.utc)

    @staticmethod
    def _month_key(value: datetime) -> str:
        return f"{value.year:04d}-{value.month:02d}"

    def _fill_month_gaps(
        self, by_month: dict[str, dict], months: int
    ) -> list[dict]:
        """Emit ``months`` contiguous entries, oldest first, filling gaps."""
        now = datetime.now(timezone.utc)
        year, month = now.year, now.month
        keys: list[str] = []
        for _ in range(months):
            keys.append(f"{year:04d}-{month:02d}")
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        keys.reverse()
        out: list[dict] = []
        for key in keys:
            base = by_month.get(
                key,
                {"month": key, "income": 0.0, "expense": 0.0, "savings": 0.0, "net": 0.0},
            )
            entry = dict(base)
            entry["net"] = round(entry.get("income", 0.0) - entry.get("expense", 0.0), 2)
            out.append(entry)
        return out

    async def _sum_balance(self, account_ids: list[uuid.UUID]) -> float:
        if not account_ids:
            return 0.0
        result = await self._session.execute(
            select(func.coalesce(func.sum(Account.current_balance), 0)).where(
                Account.id.in_(account_ids)
            )
        )
        return round(float(result.scalar_one()), 2)

    async def _sum_amount(
        self, account_ids: list[uuid.UUID], txn_type: str
    ) -> float:
        if not account_ids:
            return 0.0
        result = await self._session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .join(Account, Transaction.account_id == Account.id)
            .where(Account.id.in_(account_ids))
            .where(Transaction.transaction_type == txn_type)
            .where(Transaction.status == "posted")
        )
        return round(float(result.scalar_one()), 2)

    async def _recent(
        self, account_ids: list[uuid.UUID], limit: int
    ) -> list[dict]:
        if not account_ids:
            return []
        result = await self._session.execute(
            select(Transaction)
            .join(Account, Transaction.account_id == Account.id)
            .where(Account.id.in_(account_ids))
            .order_by(Transaction.transaction_date.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        out = []
        for t in rows:
            out.append(
                {
                    "id": t.id,
                    "account_id": t.account_id,
                    "category_id": t.category_id,
                    "amount": float(t.amount),
                    "transaction_type": t.transaction_type,
                    "merchant": t.merchant,
                    "description": t.description,
                    "transaction_date": t.transaction_date,
                    "status": t.status,
                    "source": t.source,
                }
            )
        return out

    async def _monthly_rollup(
        self, account_ids: list[uuid.UUID], months: int
    ) -> list[dict]:
        cutoff = self._months_ago(months)
        # Truncate timestamp to month using date_trunc for cross-dialect safety.
        month_col = func.date_trunc("month", Transaction.transaction_date)
        stmt = (
            select(
                func.to_char(month_col, "YYYY-MM").label("month"),
                Transaction.transaction_type,
                func.coalesce(func.sum(Transaction.amount), 0).label("total"),
            )
            .join(Account, Transaction.account_id == Account.id)
            .where(Account.id.in_(account_ids))
            .where(Transaction.status == "posted")
            .where(Transaction.transaction_date >= cutoff)
            .group_by(month_col, Transaction.transaction_type)
        )
        result = await self._session.execute(stmt)
        # Pivot type rows into per-month {income, expense}.
        pivoted: dict[str, dict] = defaultdict(
            lambda: {"month": "", "income": 0.0, "expense": 0.0}
        )
        for row in result.all():
            key = row.month
            pivoted[key]["month"] = key
            if row.transaction_type == "income":
                pivoted[key]["income"] = round(float(row.total), 2)
            elif row.transaction_type == "expense":
                pivoted[key]["expense"] = round(float(row.total), 2)
        return list(pivoted.values())
