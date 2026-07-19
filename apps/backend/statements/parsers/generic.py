"""Generic statement parser for the Statement Ingestion & Parsing Framework."""

from __future__ import annotations

from typing import Any, List

from apps.backend.statements.exceptions import NormalizationFailed
from apps.backend.statements.parsers.base import BaseStatementParser


class GenericParser(BaseStatementParser):
    """Format-agnostic parser that maps raw rows into an intermediate shape.

    This parser does not assume any particular bank layout. It performs
    light, defensive normalization of common field names so the downstream
    normalizer can rely on a stable intermediate contract. Bank-specific
    parsers can subclass this and override :meth:`_coerce_row`.
    """

    _FIELD_ALIASES = {
        "date": {"date", "transaction_date", "txn_date", "posting_date", "value_date"},
        "description": {"description", "narration", "particulars", "details", "remarks"},
        "amount": {"amount", "txn_amount", "transaction_amount"},
        "currency": {"currency", "ccy", "cur"},
        "balance": {"balance", "running_balance", "closing_balance"},
        "reference_number": {"reference", "ref", "ref_no", "cheque_no", "cheque_number", "utr"},
    }

    async def parse(self, raw_rows: List[dict[str, Any]]) -> List[dict[str, Any]]:
        """Parse raw rows into a normalized intermediate structure.

        Args:
            raw_rows: Raw rows produced by an extractor.

        Returns:
            List of intermediate dict rows with canonical keys.

        Raises:
            NormalizationFailed: if a row cannot be parsed.
        """
        parsed: List[dict[str, Any]] = []
        for index, row in enumerate(raw_rows):
            try:
                mapped = self._map_fields(row)
                parsed.append(mapped)
            except Exception as exc:
                raise NormalizationFailed(
                    "Failed to parse a raw row.",
                    details={"row_index": index},
                ) from exc
        return parsed

    def _map_fields(self, row: dict[str, Any]) -> dict[str, Any]:
        """Map a raw row's keys to canonical intermediate keys."""
        lowered = {str(k).strip().lower(): v for k, v in row.items()}
        mapped: dict[str, Any] = {}
        for canonical, aliases in self._FIELD_ALIASES.items():
            for alias in aliases:
                if alias in lowered and lowered[alias] not in (None, ""):
                    mapped[canonical] = lowered[alias]
                    break
        # Preserve the raw row for traceability.
        mapped["_raw"] = row
        return mapped
