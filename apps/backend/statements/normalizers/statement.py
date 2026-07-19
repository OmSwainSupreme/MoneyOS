"""Canonical normalizer for the Statement Ingestion & Parsing Framework."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, List, Optional

from apps.backend.statements.exceptions import NormalizationFailed
from apps.backend.statements.normalizers.base import BaseNormalizer
from apps.backend.statements.schemas import NormalizedTransaction, TransactionType


class StatementNormalizer(BaseNormalizer):
    """Transform intermediate parsed rows into canonical transactions.

    This normalizer is intentionally generic. It derives a transaction type
    from sign or explicit debit/credit fields, and leaves ``category`` and
    ``merchant`` as ``None`` (assigned out of scope by downstream systems).
    """

    async def normalize(self, parsed_rows: List[dict[str, Any]]) -> List[NormalizedTransaction]:
        """Normalize parsed rows.

        Args:
            parsed_rows: Intermediate rows (each may contain a ``_raw`` key).

        Returns:
            List of normalized transactions.

        Raises:
            NormalizationFailed: if a row cannot be normalized.
        """
        transactions: List[NormalizedTransaction] = []
        for index, row in enumerate(parsed_rows):
            try:
                transactions.append(self._normalize_row(row))
            except NormalizationFailed:
                raise
            except Exception as exc:
                raise NormalizationFailed(
                    "Failed to normalize a parsed row.",
                    details={"row_index": index},
                ) from exc
        return transactions

    def _normalize_row(self, row: dict[str, Any]) -> NormalizedTransaction:
        raw = row.get("_raw", row)
        parsed_date = self._parse_date(row.get("date"))
        amount = self._parse_amount(row.get("amount"))
        transaction_type = self._derive_type(row, amount)
        balance = self._parse_amount(row.get("balance"))
        currency = self._parse_currency(row.get("currency"))

        description = (row.get("description") or "").strip()
        if not description:
            raise NormalizationFailed(
                "Transaction is missing a description.",
                details={"row": row},
            )
        if parsed_date is None:
            raise NormalizationFailed(
                "Transaction is missing a valid date.",
                details={"row": row},
            )

        reference = row.get("reference_number")
        reference = str(reference).strip() if reference not in (None, "") else None

        return NormalizedTransaction(
            date=parsed_date,
            description=description,
            amount=amount,
            currency=currency,
            transaction_type=transaction_type,
            balance=balance,
            reference_number=reference,
            category=None,
            merchant=None,
            raw_data=raw if isinstance(raw, dict) else dict(row),
        )

    @staticmethod
    def _parse_date(value: Any) -> Optional[date]:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        text = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d %b %Y", "%d-%b-%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_amount(value: Any) -> float:
        if value is None or value == "":
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        text = re.sub(r"[,\s]", "", text)
        text = text.replace("(", "-").replace(")", "")
        if text.startswith("+"):
            text = text[1:]
        try:
            return float(text)
        except ValueError:
            return 0.0

    @staticmethod
    def _parse_currency(value: Any) -> str:
        if value is None or value == "":
            return "INR"
        return str(value).strip().upper()

    @staticmethod
    def _derive_type(row: dict[str, Any], amount: float) -> TransactionType:
        debit = str(row.get("debit", "")).strip()
        credit = str(row.get("credit", "")).strip()
        if debit not in ("", "0", "0.0") and credit in ("", "0", "0.0"):
            return TransactionType.DEBIT
        if credit not in ("", "0", "0.0") and debit in ("", "0", "0.0"):
            return TransactionType.CREDIT
        if amount < 0:
            return TransactionType.DEBIT
        if amount > 0:
            return TransactionType.CREDIT
        return TransactionType.UNKNOWN
