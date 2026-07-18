"""Health and liveness monitoring routes."""

from __future__ import annotations

from core.logging import get_logger
from database.session import verify_connection
from fastapi import APIRouter, HTTPException, status

from api.dependencies import SettingsDep

logger = get_logger(__name__)

router = APIRouter(tags=["monitoring"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(settings: SettingsDep) -> dict[str, str]:
    """Return the service health status for orchestration and probes.

    Args:
        settings: Injected application settings (FastAPI dependency).

    Returns:
        A mapping with ``status``, ``service``, and ``version`` keys.
    """
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.version,
    }


@router.get("/health/db", status_code=status.HTTP_200_OK)
async def health_check_db() -> dict[str, str]:
    """Verify database connectivity by executing ``SELECT 1``.

    The query runs through the isolated database layer so no ORM logic
    leaks into the route.

    Returns:
        A mapping confirming the database is connected.

    Raises:
        HTTPException: ``503 Service Unavailable`` if the database is
            unreachable or the probe query fails.
    """
    try:
        await verify_connection()
    except Exception as exc:  # noqa: BLE001 - surfaced as a 503 below.
        logger.error("Database health check failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "database": "disconnected"},
        ) from exc
    return {"status": "healthy", "database": "connected"}
