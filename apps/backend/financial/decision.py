"""Deterministic financial decision engine.

A transparent, dependency-free rules engine that answers common personal-
finance questions from the user's aggregated data (supplied as a dashboard
context). It deliberately avoids any LLM call so the demo works offline and
produces explainable, reproducible answers.

Supported intents (matched by keyword + amount):

* affordability  - "Can I buy/afford <thing> [for ₹X]?" -> compares the amount
                   against a safe-to-spend budget.
* safe_to_spend  - "How much can I safely spend?" -> returns the safe budget.
* where_money    - "Where is my money going?" -> surfaces top spending
                   categories (requires the analytics layer for detail; here we
                   summarize from the context when available, else give a
                   directional answer).

The safe-to-spend rule: keep a reserve equal to one month of average expenses
(or a floor of a single month's essentials). Everything above
``total_balance - reserve`` is safe to spend this month.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal

# Fraction of monthly expenses kept as a mandatory reserve.
_RESERVE_RATIO = Decimal("1.0")
# Never let safe-to-spend exceed 70% of current balance (a hard ceiling).
_SAFE_CEILING = Decimal("0.7")


@dataclass
class DecisionContext:
    """Aggregated figures the engine reasons over."""

    currency: str = "INR"
    total_balance: float = 0.0
    total_income: float = 0.0
    total_expenses: float = 0.0
    total_savings: float = 0.0
    top_categories: list[dict] = field(default_factory=list)


class FinancialDecisionEngine:
    """Answers financial questions with hard, explainable rules."""

    def __init__(self, context: dict) -> None:
        self._ctx = DecisionContext(
            currency=context.get("currency", "INR"),
            total_balance=float(context.get("total_balance", 0) or 0),
            total_income=float(context.get("total_income", 0) or 0),
            total_expenses=float(context.get("total_expenses", 0) or 0),
            total_savings=float(context.get("total_savings", 0) or 0),
            top_categories=context.get("top_categories") or [],
        )

    # --- public API --------------------------------------------------------
    def answer(self, question: str, amount: float | None = None) -> dict:
        """Return a structured decision for ``question``."""
        q = (question or "").strip().lower()
        parsed_amount = amount if amount is not None else self._extract_amount(q)
        intent = self._classify(q, parsed_amount)

        if intent == "safe_to_spend":
            return self._safe_to_spend()
        if intent == "where_money":
            return self._where_money()
        if intent == "affordability":
            return self._affordability(parsed_amount, q)
        return self._generic(q)

    # --- intents -----------------------------------------------------------
    def _affordability(self, amount: float | None, question: str) -> dict:
        if amount is None or amount <= 0:
            return {
                "answer": (
                    "I can check if you can afford that once you tell me the "
                    "amount (e.g. add it to the question or the amount field)."
                ),
                "verdict": "info",
                "safe_to_spend": self._safe_budget(),
                "rationale": [],
                "data": {},
            }
        safe = self._safe_budget()
        balance = Decimal(str(self._ctx.total_balance))
        amt = Decimal(str(amount))
        rationale = [
            f"Current balance: {self._ctx.currency} {balance:.2f}.",
            f"Safe-to-spend this month: {self._ctx.currency} {safe:.2f}.",
            f"Purchase amount: {self._ctx.currency} {amt:.2f}.",
        ]
        if amt <= safe:
            verdict = "affordable"
            answer = (
                f"Yes — you can afford "
                f"{self._ctx.currency} {amt:.2f}. It is within your safe-to-spend "
                f"budget of {self._ctx.currency} {safe:.2f}, leaving "
                f"{self._ctx.currency} {(safe - amt):.2f} afterward."
            )
        elif amt <= balance:
            verdict = "caution"
            answer = (
                f"You can technically pay "
                f"{self._ctx.currency} {amt:.2f} (balance "
                f"{self._ctx.currency} {balance:.2f}), but it exceeds your "
                f"safe-to-spend buffer of {self._ctx.currency} {safe:.2f}. "
                f"Only do this if it is important."
            )
        else:
            verdict = "unaffordable"
            answer = (
                f"No — {self._ctx.currency} {amt:.2f} is more than your balance "
                f"of {self._ctx.currency} {balance:.2f}. You would need "
                f"{self._ctx.currency} {(amt - balance):.2f} more."
            )
        return {
            "answer": answer,
            "verdict": verdict,
            "safe_to_spend": float(safe),
            "rationale": rationale,
            "data": {
                "amount": float(amt),
                "balance": float(balance),
                "safe_to_spend": float(safe),
            },
        }

    def _safe_to_spend(self) -> dict:
        safe = self._safe_budget()
        return {
            "answer": (
                f"You can safely spend about {self._ctx.currency} {safe:.2f} "
                f"this month while keeping a one-month expense reserve."
            ),
            "verdict": "info",
            "safe_to_spend": float(safe),
            "rationale": [
                f"Current balance: {self._ctx.currency} "
                f"{Decimal(str(self._ctx.total_balance)):.2f}.",
                "Reserve = one month of average expenses.",
                "Safe-to-spend = balance - reserve (capped at 70% of balance).",
            ],
            "data": {"balance": self._ctx.total_balance},
        }

    def _where_money(self) -> dict:
        cats = self._ctx.top_categories
        if cats:
            top = cats[0]
            lines = [
                f"Your biggest expense category is "
                f"{top.get('category_name', 'Unknown')} at "
                f"{self._ctx.currency} {float(top.get('total', 0)):.2f}."
            ]
            if len(cats) > 1:
                lines.append(
                    "Other significant categories: "
                    + ", ".join(
                        f"{c.get('category_name', '?')} "
                        f"({self._ctx.currency} {float(c.get('total', 0)):.2f})"
                        for c in cats[1:4]
                    )
                    + "."
                )
            answer = " ".join(lines)
            verdict = "info"
        else:
            expenses = Decimal(str(self._ctx.total_expenses))
            answer = (
                f"You have spent {self._ctx.currency} {expenses:.2f} in total. "
                f"Open the Spending-by-Category analytics view for a full "
                f"breakdown."
            )
            verdict = "info"
        return {
            "answer": answer,
            "verdict": verdict,
            "safe_to_spend": self._safe_budget(),
            "rationale": [
                f"Total tracked expenses: {self._ctx.currency} "
                f"{Decimal(str(self._ctx.total_expenses)):.2f}."
            ],
            "data": {"top_categories": self._ctx.top_categories},
        }

    def _generic(self, question: str) -> dict:
        safe = self._safe_budget()
        return {
            "answer": (
                f"I'm a rules-based assistant. Ask things like \"Can I afford "
                f"X?\", \"How much can I safely spend?\", or \"Where is my money "
                f"going?\". Your safe-to-spend budget is "
                f"{self._ctx.currency} {safe:.2f}."
            ),
            "verdict": "info",
            "safe_to_spend": float(safe),
            "rationale": [],
            "data": {},
        }

    # --- helpers -----------------------------------------------------------
    def _safe_budget(self) -> Decimal:
        """Safe-to-spend = max(0, balance - reserve), capped at 70% balance."""
        balance = Decimal(str(self._ctx.total_balance))
        reserve = Decimal(str(self._ctx.total_expenses)) * _RESERVE_RATIO
        raw = balance - reserve
        if raw < 0:
            raw = Decimal("0")
        ceiling = balance * _SAFE_CEILING
        if raw > ceiling:
            raw = ceiling
        return raw.quantize(Decimal("0.01"))

    @staticmethod
    def _extract_amount(text: str) -> float | None:
        """Pull a currency amount out of free text (handles ₹, commas, k)."""
        # Match ₹12,000 or 25000 or 25k or rs 1200.
        match = re.search(
            r"(?:rs\.?|₹|inr)?\s*([\d,]+(?:\.\d+)?)\s*(k|lakh|l)?",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        try:
            value = Decimal(match.group(1).replace(",", ""))
        except Exception:  # noqa: BLE001
            return None
        suffix = (match.group(2) or "").lower()
        if suffix == "k":
            value *= 1000
        elif suffix in ("lakh", "l"):
            value *= 100000
        return float(value)

    @staticmethod
    def _classify(text: str, amount: float | None) -> str:
        if re.search(r"safe(?:ly)?\s*spend|how much.*spend|budget", text):
            return "safe_to_spend"
        if re.search(
            r"where.*money|spending|where.*go|where does", text
        ):
            return "where_money"
        if re.search(r"can i|afford|buy|purchase|enough", text) and amount:
            return "affordability"
        if amount and re.search(r"afford|buy|purchase|can i", text):
            return "affordability"
        if re.search(r"afford|buy|purchase|can i", text):
            return "affordability"
        return "generic"