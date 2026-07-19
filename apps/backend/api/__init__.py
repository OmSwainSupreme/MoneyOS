"""API package for the MoneyOS backend.

Exposes the dependency-injection helpers so the application factory and tests
can import them from a single location. ``api_router`` is composed in
:mod:`api.router` and re-exported lazily from here to avoid a circular import
chain (``financial.router`` -> ``api.dependencies`` -> ``api`` ->
``api.router`` -> ``financial.router``). Import ``api_router`` directly from
:mod:`api.router` when needed.
"""

from __future__ import annotations

from api.dependencies import get_app_settings

__all__ = ["get_app_settings"]
