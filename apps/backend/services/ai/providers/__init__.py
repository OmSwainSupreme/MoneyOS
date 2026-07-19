"""Provider registry for the AI chat feature.

Selects an :class:`~services.ai.providers.base.LLMProvider` from application
settings. Defaults to the offline :class:`MockProvider`; when a real backend
(e.g. Gemini) is configured it is returned instead. The chat service and
router depend only on the :class:`LLMProvider` contract.
"""

from __future__ import annotations

from core.config import Settings, get_settings
from services.ai.providers.base import LLMProvider
from services.ai.providers.mock import MockProvider

# Imported lazily to avoid hard-dependency churn in the demo image.
try:  # pragma: no cover - gemini provider is optional for the MVP.
    from services.ai.providers.gemini import GeminiProvider
except Exception:  # noqa: BLE001 - provider may be absent.
    GeminiProvider = None  # type: ignore[assignment]


def get_provider(
    settings: Settings | None = None, *, context: dict | None = None
) -> LLMProvider:
    """Return the configured chat provider (mock by default).

    Args:
        settings: Optional settings override.
        context: Dashboard-style aggregation passed to providers that need it
            (e.g. the mock). Ignored by stateless external providers.

    Returns:
        An :class:`LLMProvider` instance.
    """
    resolved = settings or get_settings()
    if (
        GeminiProvider is not None
        and getattr(resolved, "ai_provider", "") == "gemini"
        and getattr(resolved, "ai_api_key", "")
    ):
        return GeminiProvider(api_key=resolved.ai_api_key)
    return MockProvider(context=context)
