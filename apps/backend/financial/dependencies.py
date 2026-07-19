"""FastAPI dependency wiring for the financial module.

Exposes transaction-aware service injection points for accounts, categories,
and transactions. The current user is resolved by the auth layer and reused
directly; HTTP concerns stay in the router.
"""

from __future__ import annotations

from typing import Annotated

from api.dependencies import SettingsDep
from auth.dependencies import CurrentUserDep
from database.session import get_db_session
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from financial.service import (
    AccountService,
    CategoryService,
    TransactionService,
)
from financial.analytics import AnalyticsService


def get_account_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _settings: SettingsDep,
) -> AccountService:
    """Inject a session-bound :class:`AccountService`."""
    return AccountService(session)


def get_category_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _settings: SettingsDep,
) -> CategoryService:
    """Inject a session-bound :class:`CategoryService`."""
    return CategoryService(session)


def get_transaction_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _settings: SettingsDep,
) -> TransactionService:
    """Inject a session-bound :class:`TransactionService`."""
    return TransactionService(session)


AccountServiceDep = Annotated[AccountService, Depends(get_account_service)]
CategoryServiceDep = Annotated[CategoryService, Depends(get_category_service)]
TransactionServiceDep = Annotated[
    TransactionService, Depends(get_transaction_service)
]


def get_analytics_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _settings: SettingsDep,
) -> AnalyticsService:
    """Inject a session-bound :class:`AnalyticsService`."""
    return AnalyticsService(session)


AnalyticsServiceDep = Annotated[
    AnalyticsService, Depends(get_analytics_service)
]

# The current user is resolved by the auth layer; reuse it directly.
CurrentUser = CurrentUserDep
