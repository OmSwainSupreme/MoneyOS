"""AI chat REST route.

Exposes ``POST /ai/chat`` (mounted under the API prefix). The route is
authenticated and delegates to :class:`~services.ai.chat.ChatService`, which
selects a provider (mock by default, Gemini when configured). No LLM/HTTP
logic lives here.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, status

from auth.dependencies import CurrentUserDep
from database.session import get_db_session
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.ai.chat import ChatService, build_chat_service
from services.ai.providers.base import ChatMessage, ChatResponse
from pydantic import BaseModel, Field

chat_router = APIRouter(prefix="/ai", tags=["ai"])


class ChatTurn(BaseModel):
    """A prior chat turn."""

    role: str = Field(..., description="One of user/assistant/system.")
    content: str = Field(..., description="Turn text.")


class ChatRequestPayload(BaseModel):
    """Inbound chat payload."""

    message: str = Field(..., min_length=1, max_length=2048)
    history: list[ChatTurn] = Field(default_factory=list)


class ChatResponsePayload(BaseModel):
    """Outbound chat payload."""

    reply: str
    provider: str
    data: dict = Field(default_factory=dict)


@chat_router.post("/chat", response_model=ChatResponsePayload)
async def chat(
    payload: ChatRequestPayload,
    current_user: CurrentUserDep,
    session: AsyncSession = Depends(get_db_session),
) -> ChatResponsePayload:
    """Answer a financial question using the user's stored data."""
    service = build_chat_service(session)
    response: ChatResponse = await service.ask(
        current_user.id,
        payload.message,
        history=[t.model_dump() for t in payload.history],
    )
    return ChatResponsePayload(
        reply=response.reply,
        provider=response.provider,
        data=response.data,
    )
