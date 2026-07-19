"""Chat service for the AI financial assistant.

Owns the request lifecycle for a chat turn: it gathers the user's financial
context (via the analytics service), selects a provider through the registry,
and returns the provider's reply. It never touches the ORM directly and stays
provider-agnostic, so the mock and a future Gemini backend are interchangeable.
"""

from __future__ import annotations

import uuid
from typing import Any

from financial.analytics import AnalyticsService
from services.ai.providers import get_provider
from services.ai.providers.base import ChatMessage, ChatRequest, ChatResponse


class ChatService:
    """Answers financial questions using the user's stored data."""

    def __init__(self, analytics: AnalyticsService) -> None:
        self._analytics = analytics

    async def ask(
        self, user_id: uuid.UUID, message: str, history: list[dict] | None = None
    ) -> ChatResponse:
        """Produce a chat reply for ``message`` from ``user_id``'s data."""
        context = await self._analytics.dashboard(user_id, limit_recent=5)
        context["top_categories"] = await self._analytics.spending_by_category(
            user_id, months=3
        )
        provider = get_provider(context=context)
        turns = [ChatMessage(**m) for m in (history or [])]
        request = ChatRequest(
            message=message, history=turns, user_id=user_id
        )
        return await provider.complete(request)


def build_chat_service(session: Any) -> ChatService:
    """Factory: bind a :class:`ChatService` to an active session."""
    return ChatService(AnalyticsService(session))
