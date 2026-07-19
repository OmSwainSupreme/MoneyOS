"""FastAPI dependency wiring for authentication.

Defines the injection points used by protected routes: extracting the bearer
token from the ``Authorization`` header and resolving the current user via the
service layer. HTTP concerns (header parsing, 401 translation) live here so the
service stays transport-agnostic.
"""

from __future__ import annotations

from typing import Annotated

from database.session import get_db_session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from auth.exceptions import AuthError
from auth.schemas import UserPublic
from auth.service import AuthService

# Imported lazily to avoid an import cycle: ``api.dependencies`` -> ``api`` ->
# ``api.router`` -> ``auth.router`` -> ``auth.dependencies``. ``SettingsDep`` is
# only referenced inside function annotations, so a deferred import is safe.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from api.dependencies import SettingsDep

# Reject missing credentials with 401 instead of 403; we want aWWW-Authenticate
# challenge semantics for bearer auth.
_bearer = HTTPBearer(auto_error=True)


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: SettingsDep,
) -> AuthService:
    """Inject a transaction-aware :class:`AuthService`."""
    return AuthService(session, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    auth_service: AuthServiceDep,
) -> UserPublic:
    """Resolve the authenticated user from a bearer access token.

    Raises:
        HTTPException: ``401`` on a missing/invalid/expired token or an
            unresolvable subject.
    """
    try:
        return await auth_service.get_current_user(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token", "message": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


CurrentUserDep = Annotated[UserPublic, Depends(get_current_user)]
