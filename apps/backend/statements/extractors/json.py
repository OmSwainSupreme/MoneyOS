"""JSON extractor for the Statement Ingestion & Parsing Framework.

Designed specifically for the AgamiAI *Indian Bank Statements* dataset, where a
single file is a JSON document shaped like::

    {
      "bank_name": "...",
      "account_number": "...",
      "currency": "INR",
      "opening_balance": 1234.56,
      "closing_balance": 7890.12,
      "transactions": [
        {
          "date": "2024-01-01 11:30:55",
          "value_date": "2024-01-01",
          "description": "UPI/...",
          "cheque_no": "",
          "debit": null,
          "credit": 50000.0,
          "balance": 5234.56,
          "branch_code": "...",
          "failed": false
        },
        ...
      ]
    }

The extractor is intentionally tolerant:

* It accepts either a wrapped document (``{"transactions": [...]}``) or a bare
  array of transaction objects (``[ {...}, ... ]``).
* It tolerates minor schema drift: statement-level fields that are missing are
  simply not threaded through, and unknown transaction keys are preserved via
  the ``_raw`` sink so downstream layers can still read them.
* Malformed JSON (or a payload that is neither an object nor an array) raises
  :class:`CorruptStatement` so the router can emit a clean ``corrupt_statement``
  envelope rather than a 500.
"""

from __future__ import annotations

import json
from typing import Any

from statements.exceptions import CorruptStatement, EmptyStatement
from statements.extractors.base import BaseExtractor


class JSONExtractor(BaseExtractor):
    """Extract raw transaction rows from a bank-statement JSON document."""

    #: Keys that the AgamiAI statement wraps around the transaction list. These
    #: are *statement-level* attributes threaded onto every row so the
    #: parser/normalizer can read ``account_number`` and ``currency`` directly.
    STATEMENT_META_KEYS = (
        "bank_name",
        "account_holder",
        "account_number",
        "ifsc_code",
        "micr_code",
        "branch_name",
        "branch_code",
        "account_type",
        "currency",
        "customer_id",
    )

    #: Statement *summary* keys that must NOT be merged onto each transaction
    #: row under their own name. Several of them (``closing_balance``,
    #: ``opening_balance``) alias to the per-transaction ``balance`` field in the
    #: generic parser, which would non-deterministically clobber the real
    #: running balance (hash-randomized set iteration). They are threaded under
    #: ``_stmt_``-namespaced keys instead so downstream code can still reach them
    #: without colliding with transaction fields.
    STATEMENT_SUMMARY_KEYS = (
        "opening_balance",
        "closing_balance",
        "start_date",
        "end_date",
        "statement_date",
        "interest_rate",
    )

    async def extract(self, file: Any) -> list[dict[str, Any]]:
        """Extract raw rows from a JSON statement file.

        Args:
            file: Object exposing ``read()``/``seek()`` (e.g. ``UploadFile``).

        Returns:
            List of dict rows, one per transaction, with statement-level
            metadata (``currency``, ``account_number``) injected so the parser
            and normalizer do not have to re-derive them.

        Raises:
            CorruptStatement: if the payload is not valid JSON or has an
                unsupported top-level shape.
            EmptyStatement: if no transactions are present.
        """
        contents = await file.read()
        await file.seek(0)

        try:
            decoded = contents.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise CorruptStatement(
                "Failed to decode JSON file as UTF-8.",
                details={"filename": getattr(file, "filename", "unknown")},
            ) from exc

        try:
            data = json.loads(decoded)
        except json.JSONDecodeError as exc:
            raise CorruptStatement(
                "The uploaded file is not valid JSON.",
                details={
                    "filename": getattr(file, "filename", "unknown"),
                    "position": exc.pos,
                    "line": exc.lineno,
                    "column": exc.colno,
                },
            ) from exc

        if isinstance(data, list):
            # Bare array of transactions (no statement wrapper).
            transactions = data
            meta: dict[str, Any] = {}
        elif isinstance(data, dict):
            transactions = data.get("transactions")
            meta = {k: data.get(k) for k in self.STATEMENT_META_KEYS}
            # Statement summaries are namespaced so they never collide with a
            # per-transaction ``balance``/``opening_balance`` field.
            meta.update(
                {f"_stmt_{k}": data.get(k) for k in self.STATEMENT_SUMMARY_KEYS}
            )
        else:
            raise CorruptStatement(
                "Unsupported JSON shape: top-level must be an object or array.",
                details={"filename": getattr(file, "filename", "unknown")},
            )

        if transactions is None:
            raise EmptyStatement(
                "The JSON document contains no 'transactions' list.",
                details={
                    "filename": getattr(file, "filename", "unknown"),
                    "reason": "no 'transactions' key in JSON document",
                },
            )

        if not isinstance(transactions, list):
            raise CorruptStatement(
                "The 'transactions' field must be a list of objects.",
                details={"filename": getattr(file, "filename", "unknown")},
            )

        # Inject statement-level context into every row. The parser/normalizer
        # read ``currency`` and ``account_number`` directly, and any unexpected
        # keys survive in ``_raw`` for downstream tolerance.
        rows: list[dict[str, Any]] = []
        for idx, txn in enumerate(transactions):
            if not isinstance(txn, dict):
                # Skip non-object entries but keep going (tolerant ingestion).
                continue
            row = {**meta, **txn}
            row["_raw"] = dict(txn)
            row["_index"] = idx
            rows.append(row)

        return rows
