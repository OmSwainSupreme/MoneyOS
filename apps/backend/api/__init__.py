"""API package for the MoneyOS backend.

Exposes the composed ``api_router`` and the dependency-injection helpers so
the application factory and tests can import them from a single location.
"""

from __future__ import annotations

from api.dependencies import get_app_settings
from api.router import api_router

__all__ = ["api_router", "get_app_settings"]
