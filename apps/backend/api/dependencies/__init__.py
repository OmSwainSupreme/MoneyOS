"""Dependency-injection placeholders for the MoneyOS API.

FastAPI dependencies are declared here as injection points. Concrete
implementations (database sessions, auth context, service factories) are
wired in later phases; the placeholders keep the dependency surface stable.
"""

from __future__ import annotations

from typing import Annotated

from core.config import Settings, get_settings
from fastapi import Depends


def get_app_settings() -> Settings:
    """FastAPI dependency that yields the cached application settings."""
    return get_settings()


# Common dependency aliases used across routes.
SettingsDep = Annotated[Settings, Depends(get_app_settings)]

# TODO(backend): add get_db_session, get_current_user, get_service_factory
# once persistence and authentication phases land.
