"""FastAPI dependency wiring for the user module.

Exposes the injection points used by profile/preferences routes: a
transaction-aware :class:`UserService` and the already-resolved current user
(from the auth dependency). HTTP concerns stay in the router; this module only
composes existing dependencies.
"""

from __future__ import annotations

from typing import Annotated

from api.dependencies import SettingsDep
from auth.dependencies import CurrentUserDep
from database.session import get_db_session
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from user.service import UserService


def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _settings: SettingsDep,
) -> UserService:
    """Inject a session-bound :class:`UserService`."""
    return UserService(session)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]

# The current user is resolved by the auth layer; reuse it directly so the
# user module never re-implements token handling.
CurrentUser = CurrentUserDep
