"""Top-level API router composition.

This module is the single composition point for every versioned and
feature-specific router in the backend. The version prefix (``/api/v1``)
is applied by the application factory when the router is included, so the
prefix is driven by configuration rather than hard-coded here.
"""

from __future__ import annotations

from auth.router import auth_router, user_router
from fastapi import APIRouter

from api.routes.health import router as health_router
from financial.router import (
    accounts_router,
    analytics_router,
    categories_router,
    dashboard_router,
    decision_router,
    transactions_router,
)
from services.ai.router import chat_router
from statements.router import router as statements_router
from user.router import user_router as user_profile_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(user_profile_router)
api_router.include_router(accounts_router)
api_router.include_router(categories_router)
api_router.include_router(transactions_router)
api_router.include_router(dashboard_router)
api_router.include_router(analytics_router)
api_router.include_router(decision_router)
api_router.include_router(statements_router)
api_router.include_router(chat_router)
