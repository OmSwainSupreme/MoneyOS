"""Health and liveness monitoring routes."""

from __future__ import annotations

from fastapi import APIRouter, status

from api.dependencies import SettingsDep

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
