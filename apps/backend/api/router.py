"""Top-level API router composition.

This module is the single composition point for every versioned and
feature-specific router in the backend. The version prefix (``/api/v1``)
is applied by the application factory when the router is included, so the
prefix is driven by configuration rather than hard-coded here.
"""

from __future__ import annotations

from fastapi import APIRouter

from api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)

# TODO(backend): register feature routers (auth, accounts, transactions,
# decisions) as the corresponding phases land.
