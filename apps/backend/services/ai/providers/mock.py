"""Mock LLM provider: deterministic, offline, data-aware.

The mock answers financial questions by combining the user's aggregated data
(``context``) with lightweight keyword heuristics and the same rules engine
the /decision endpoint uses. It returns stable, explainable answers so the
demo never depends on an external LLM, and it is the default provider until a
real Gemini (or other) backend is configured.

It is intentionally a stand-in: swapping in a real provider means implementing
:class:`~services.ai.providers.base.LLMProvider` and registering it in
:func:`services.ai.providers.get_provider`. Nothing else changes.
"""

from __future__ import annotations

from typing import Any

from financial.decision import FinancialDecisionEngine
from services.ai.providers.base import ChatRequest, ChatResponse, LLMProvider


class MockProvider(LLMProvider):
    """Offline heuristic chat provider backed by the user's financial data."""

    name = "mock"

    def __init__(self, context: dict[str, Any] | None = None) -> None:
        # ``context`` is the dashboard-style aggregation for the user.
        self._context = context or {}

    async def complete(self, request: ChatRequest) -> ChatResponse:
        message = request.message or ""
        # Route to the rules engine for intent-rich questions; otherwise give a
        # friendly, data-aware summary.
        engine = FinancialDecisionEngine(self._context)
        decision = engine.answer(message, self._amount_from_request(message))
        return ChatResponse(
            reply=decision["answer"],
            provider=self.name,
            data={
                "verdict": decision["verdict"],
                "safe_to_spend": decision.get("safe_to_spend"),
                "rationale": decision.get("rationale", []),
            },
        )

    @staticmethod
    def _amount_from_request(message: str) -> float | None:
        return FinancialDecisionEngine._extract_amount(message)
