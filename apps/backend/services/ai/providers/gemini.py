"""Gemini provider (optional, swap-ready).

This is a thin, ready-to-wire implementation of the :class:`LLMProvider`
contract for Google's Gemini models. It is NOT imported at startup (the
registry only loads it when ``AI_PROVIDER=gemini`` and ``AI_API_KEY`` is set),
so the demo image does not need the ``google-generativeai`` SDK installed.

To enable: set ``AI_PROVIDER=gemini`` and ``AI_API_KEY=...`` in the
environment, and ``uv pip install google-generativeai``. The chat service and
router require no changes.
"""

from __future__ import annotations

from typing import Any

from services.ai.providers.base import ChatRequest, ChatResponse, LLMProvider


class GeminiProvider(LLMProvider):
    """LLMProvider backed by Google Gemini."""

    name = "gemini"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._model = "gemini-1.5-flash"
        self._client = None  # Initialized lazily on first use.

    async def complete(self, request: ChatRequest) -> ChatResponse:
        client = self._get_client()
        history = [
            {"role": m.role, "parts": [m.content]} for m in request.history
        ]
        history.append({"role": "user", "parts": [request.message]})
        try:
            response = await client.generate_content_async(
                model=self._model, contents=history
            )
            reply = response.text
        except Exception as exc:  # noqa: BLE001 - surface as a clean reply.
            reply = f"AI provider error: {exc}"
        return ChatResponse(reply=reply, provider=self.name, data={})

    async def health(self) -> bool:
        return bool(self._api_key)

    def _get_client(self):
        if self._client is None:
            import google.generativeai as genai

            genai.configure(api_key=self._api_key)
            self._client = genai.GenerativeModel(self._model)
        return self._client
