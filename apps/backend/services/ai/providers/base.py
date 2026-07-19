"""Provider abstraction for the AI chat feature.

Defines the :class:`LLMProvider` interface the chat service depends on. The
concrete implementation is selected at runtime (mock by default; a Gemini
provider can be dropped in later without touching the service or router), so
the demo works fully offline and stays provider-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatMessage:
    """A single chat turn."""

    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class ChatRequest:
    """A chat request with optional prior history."""

    message: str
    history: list[ChatMessage] = field(default_factory=list)
    user_id: Any | None = None


@dataclass
class ChatResponse:
    """A provider's reply."""

    reply: str
    provider: str
    data: dict = field(default_factory=dict)


class LLMProvider(ABC):
    """Contract every chat backend must satisfy."""

    name: str = "base"

    @abstractmethod
    async def complete(self, request: ChatRequest) -> ChatResponse:
        """Produce a reply for ``request``."""
        raise NotImplementedError

    async def health(self) -> bool:
        """Return ``True`` when the provider is usable."""
        return True
