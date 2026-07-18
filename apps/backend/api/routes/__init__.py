"""Route package for the MoneyOS API.

Feature and monitoring routers live in submodules and are composed by
``api.router.api_router``.
"""

from __future__ import annotations

from api.routes.health import router as health_router

__all__ = ["health_router"]
