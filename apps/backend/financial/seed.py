"""Seed data for the financial domain.

Provides the baseline set of **system** categories that every user sees
alongside their own. System categories have ``is_system = True`` and
``user_id = NULL`` and are shared across all users (see the
``ck_categories_system_ownership`` CHECK constraint). The seed function is
idempotent: it only inserts rows that are not already present, keyed by
(name, type, is_system), so it is safe to run on every application start or as
a one-off management command.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from financial.models import Category

# Baseline system categories: (name, type, color, icon).
SYSTEM_CATEGORIES: tuple[tuple[str, str, str | None, str | None], ...] = (
    ("Salary", "income", "#2e7d32", "wallet"),
    ("Interest", "income", "#388e3c", "percent"),
    ("Refund", "income", "#43a047", "undo"),
    ("Groceries", "expense", "#1565c0", "cart"),
    ("Dining", "expense", "#ef6c00", "restaurant"),
    ("Transport", "expense", "#00838f", "bus"),
    ("Utilities", "expense", "#5e35b1", "bolt"),
    ("Rent", "expense", "#c62828", "home"),
    ("Shopping", "expense", "#ad1457", "bag"),
    ("Health", "expense", "#00897b", "heart"),
    ("Entertainment", "expense", "#f9a825", "film"),
    ("Transfer", "transfer", "#455a64", "swap"),
)


async def seed_system_categories(session: AsyncSession) -> int:
    """Insert missing baseline system categories.

    Returns the number of categories created (0 if all already exist).
    """
    existing = await session.execute(
        select(Category.name, Category.type).where(
            Category.is_system.is_(True)
        )
    )
    present = {(row.name, row.type) for row in existing.all()}

    created = 0
    for name, type_value, color, icon in SYSTEM_CATEGORIES:
        if (name, type_value) in present:
            continue
        session.add(
            Category(
                name=name,
                type=type_value,
                color=color,
                icon=icon,
                is_system=True,
                user_id=None,
            )
        )
        created += 1
    if created:
        await session.flush()
    return created
