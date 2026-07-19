"""Dedicated parser for AgamiAI JSON bank statements.

This is a thin specialization of :class:`GenericParser`. The AgamiAI dataset is
already close to the canonical intermediate contract (debit/credit columns,
``date``/``value_date``, ``description``, ``cheque_no`` -> reference,
``balance`` -> running balance), so this parser:

* reuses the generic field-alias mapping (no duplicated logic),
* drops transactions flagged ``failed: true`` (the dataset marks reversed /
  unsuccessful entries with this flag),
* surfaces ``account_number`` and ``currency`` from the statement wrapper so the
  normalizer and persistence layer can record them,
* tolerates missing optional fields (debit/credit may be ``null``; balance may
  be absent for a row) without raising.
"""

from __future__ import annotations

from typing import Any

from statements.exceptions import NormalizationFailed
from statements.parsers.generic import GenericParser


class JSONStatementParser(GenericParser):
    """Parser for the AgamiAI Indian-Bank-Statements JSON layout."""

    #: Transaction keys that signal the row should be skipped entirely.
    _SKIP_FLAGS = ("failed",)

    async def parse(self, raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Parse JSON rows, skipping failed/reversed entries.

        Raises:
            NormalizationFailed: propagated from the generic row mapping if a
                row cannot be parsed.
        """
        parsed: list[dict[str, Any]] = []
        for index, row in enumerate(raw_rows):
            try:
                if self._is_flagged(row):
                    continue
                mapped = self._map_fields(row)
                # Carry the statement-level account number through so it can be
                # stamped on the persisted transaction if desired.
                acc_no = row.get("account_number")
                if acc_no not in (None, ""):
                    mapped["account_number"] = acc_no
                parsed.append(mapped)
            except Exception as exc:
                raise NormalizationFailed(
                    "Failed to parse a JSON transaction row.",
                    details={"row_index": index},
                ) from exc
        return parsed

    @staticmethod
    def _is_flagged(row: dict[str, Any]) -> bool:
        """Return ``True`` if the row is marked failed/reversed."""
        for flag in JSONStatementParser._SKIP_FLAGS:
            value = row.get(flag)
            if value is True or str(value).strip().lower() in ("true", "1", "yes"):
                return True
        return False
