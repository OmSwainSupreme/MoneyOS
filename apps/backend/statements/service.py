"""Service layer for the Statement Ingestion & Parsing Framework.

This module orchestrates the flow: validation -> extraction -> parsing -> normalization.
It depends on abstractions (extractors, parsers, normalizers) that are injected.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from database.session import get_sessionmaker
from financial.models import Transaction
from financial.models import TransactionSource, TransactionStatus
from financial.repository import AccountRepository, TransactionRepository
from statements import exceptions
from statements.extractors.base import BaseExtractor
from statements.extractors.csv import CSVExtractor
from statements.extractors.excel import ExcelExtractor
from statements.extractors.json import JSONExtractor
from statements.extractors.pdf import PDFExtractor
from statements.normalizers.base import BaseNormalizer
from statements.normalizers.statement import StatementNormalizer
from statements.parsers.base import BaseStatementParser
from statements.parsers.generic import GenericParser
from statements.parsers.json import JSONStatementParser
from statements.parsers.registry import ParserRegistry
from statements.schemas import NormalizedTransaction, UploadResponse, ValidateResponse
from statements.utils.validation import (
    MAX_FILE_SIZE_BYTES,
    SUPPORTED_MIME_TYPES,
    detect_mime_type,
)


class StatementService:
    """Orchestrates the statement ingestion and parsing pipeline."""

    #: Maximum upload size in bytes.
    MAX_FILE_SIZE = MAX_FILE_SIZE_BYTES
    #: Supported MIME types (re-exported for convenience).
    SUPPORTED_MIME_TYPES = SUPPORTED_MIME_TYPES

    def __init__(
        self,
        extractors: dict[str, BaseExtractor] | None = None,
        parsers: ParserRegistry | None = None,
        normalizer: BaseNormalizer | None = None,
    ) -> None:
        self._extractors = extractors or {
            "application/pdf": PDFExtractor(),
            "text/csv": CSVExtractor(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ExcelExtractor(),
            "application/vnd.ms-excel": ExcelExtractor(),
            "application/json": JSONExtractor(),
        }
        self._parsers = parsers or ParserRegistry()
        self._normalizer = normalizer or StatementNormalizer()
        # Register the generic parser as fallback
        self._parsers.register("generic", GenericParser())
        # Register the dedicated JSON parser and route JSON uploads to it.
        self._parsers.register("json", JSONStatementParser())
        self._parsers.register_for_mime("application/json", "json")

    async def _validate_file(self, file: Any) -> tuple[str, str, int]:
        """Validate the uploaded file.

        Returns:
            tuple of (mime_type, filename, size)

        Raises:
            UnsupportedFileType, FileTooLarge, EmptyStatement, CorruptStatement
        """
        # Read file content to check size and content
        contents = await file.read()
        await file.seek(0)  # reset pointer for later use

        size = len(contents)
        if size == 0:
            raise exceptions.EmptyStatement(details={"filename": file.filename})
        if size > self.MAX_FILE_SIZE:
            raise exceptions.FileTooLarge(
                details={
                    "filename": file.filename,
                    "size": size,
                    "max_size": self.MAX_FILE_SIZE,
                }
            )

        mime_type = detect_mime_type(file.filename, contents)
        if mime_type not in self.SUPPORTED_MIME_TYPES:
            raise exceptions.UnsupportedFileType(
                details={
                    "filename": file.filename,
                    "detected_mime": mime_type,
                    "supported": list(self.SUPPORTED_MIME_TYPES),
                }
            )

        return mime_type, file.filename or "unknown", size

    async def process_upload(self, file: Any, user_id: object | None = None) -> dict[str, Any]:
        """Process an uploaded statement file and return normalized transactions.

        Args:
            file: The uploaded statement file.
            user_id: Identifier of the authenticated user who owns the upload.
                Stored on the result so downstream persistence can scope the
                extracted transactions to the caller.

        Steps:
          1. Validate file (size, type, not empty)
          2. Detect format and select extractor
          3. Extract raw rows
          4. Select parser (generic for now) and parse to intermediate format
          5. Normalize parsed rows into canonical transactions
          6. Return normalized statement
        """
        mime_type, filename, size = await self._validate_file(file)

        # Extract raw rows
        extractor = self._extractors.get(mime_type)
        if extractor is None:
            # This should not happen because of validation, but defensive
            raise exceptions.UnsupportedFileType(
                details={"filename": filename, "detected_mime": mime_type}
            )

        try:
            raw_rows = await extractor.extract(file)
        except exceptions.StatementError:
            # Let specific extractor errors (e.g. CorruptStatement for malformed
            # JSON) propagate so the router maps them to the right envelope.
            raise
        except Exception as exc:
            raise exceptions.ExtractionFailed(
                "Failed to extract statement content.",
                details={"filename": filename, "mime_type": mime_type},
            ) from exc

        if not raw_rows:
            raise exceptions.EmptyStatement(details={"filename": filename})

        # Parse raw rows into intermediate format (list of dicts)
        parser = self._parsers.get_parser_for_mime(mime_type)
        try:
            parsed_rows = await parser.parse(raw_rows)
        except Exception as exc:
            raise exceptions.NormalizationFailed(
                "Failed to parse statement rows.",
                details={"filename": filename, "mime_type": mime_type},
            ) from exc

        # Normalize parsed rows into canonical transactions
        try:
            normalized_transactions = await self._normalizer.normalize(parsed_rows)
        except Exception as exc:
            raise exceptions.NormalizationFailed(
                "Failed to normalize statement rows.",
                details={"filename": filename, "mime_type": mime_type},
            ) from exc

        # Detect currency if possible (from first transaction or raw data)
        currency = None
        if normalized_transactions:
            currency = normalized_transactions[0].currency

        return {
            "user_id": user_id,
            "source_format": mime_type,
            "source_name": filename,
            "transaction_count": len(normalized_transactions),
            "transactions": [t.model_dump() for t in normalized_transactions],
        }

    async def store_statement(
        self,
        file: Any,
        *,
        user_id: uuid.UUID,
        account_id: uuid.UUID,
        auto_categorize: bool = True,
    ) -> dict[str, Any]:
        """Extract, parse, normalize, and persist a statement's transactions.

        End-to-end ingestion: the file is validated, extracted, parsed, and
        normalized exactly as in :meth:`process_upload`, then each normalized
        transaction is written to the ``Transaction`` table under the caller's
        chosen ``account_id`` (``source = 'statement'``) and the account
        balance is adjusted atomically for every posted row.

        Ownership is enforced: the account must belong to ``user_id``.

        Args:
            file: The uploaded statement file.
            user_id: Owner of the upload and the target account.
            account_id: Account the statement transactions are booked to.
            auto_categorize: When ``True``, a best-effort category match is
                attempted from the user's visible categories by merchant/name.

        Returns:
            Dictionary with ``account_id``, ``stored_count``, ``skipped_count``,
            and the list of stored transaction ids.
        """
        normalized = await self._normalize_file(file)
        if not normalized:
            return {
                "account_id": account_id,
                "stored_count": 0,
                "skipped_count": 0,
                "transaction_ids": [],
            }

        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            # Enforce ownership inside the persistence transaction.
            accounts = AccountRepository(session)
            await accounts.get_or_raise(account_id, user_id)

            categories = None
            if auto_categorize:
                from financial.repository import CategoryRepository

                cats = await CategoryRepository(session).list_for_user(user_id)
                categories = cats

            txn_repo = TransactionRepository(session)

            # Build a fingerprint set of transactions that already exist on the
            # account so re-uploading the same statement is idempotent. A
            # fingerprint combines the natural key of a statement row:
            # (date, amount, type, reference). This applies uniformly to PDF,
            # CSV and JSON imports.
            seen = await self._existing_fingerprints(txn_repo, account_id)

            stored_ids: list[uuid.UUID] = []
            skipped = 0
            duplicates = 0
            persisted: list[NormalizedTransaction] = []
            for nt in normalized:
                fingerprint = self._fingerprint(nt)
                if fingerprint is not None and fingerprint in seen:
                    duplicates += 1
                    continue
                try:
                    txn = await self._persist_one(
                        txn_repo, nt, account_id, user_id, categories
                    )
                    if txn is not None:
                        stored_ids.append(txn.id)
                        persisted.append(nt)
                        if fingerprint is not None:
                            seen.add(fingerprint)
                    else:
                        skipped += 1
                except Exception:  # noqa: BLE001 - one bad row must not sink the batch
                    skipped += 1

            # Apply the net balance delta atomically for only the rows we
            # actually stored (duplicates and skips must not move the balance).
            net_delta = self._net_statement_delta(persisted)
            if net_delta != 0:
                await accounts.adjust_balance(account_id, net_delta)

            await session.commit()

        return {
            "account_id": account_id,
            "stored_count": len(stored_ids),
            "skipped_count": skipped,
            "duplicate_count": duplicates,
            "transaction_ids": stored_ids,
        }

    @staticmethod
    def _amount_key(amount: object) -> str:
        """Scale-insensitive amount key for de-duplication.

        Normalized rows carry Python ``float`` amounts while the database stores
        them as ``Numeric(18, 2)`` (returned as ``Decimal`` with two decimals).
        Formatting both through ``%.2f`` makes the two representations compare
        equal regardless of trailing zeros.
        """
        return f"{round(float(amount), 2):.2f}"

    @staticmethod
    def _fingerprint(
        nt: NormalizedTransaction,
    ) -> tuple[str, str, str, str] | None:
        """Natural key for de-duplicating a normalized statement row.

        Combines transaction date, absolute amount, direction, and reference
        number. Returns ``None`` for rows that carry no direction (``unknown``)
        because those are never persisted anyway.
        """
        if nt.transaction_type.value == "unknown":
            return None
        date_key = ""
        if nt.date is not None:
            date_key = nt.date.isoformat()[:10]
        amount_key = StatementService._amount_key(nt.amount)
        ref_key = (nt.reference_number or "").strip().lower()
        return (
            date_key,
            amount_key,
            nt.transaction_type.value,
            ref_key,
        )

    async def _existing_fingerprints(
        self,
        txn_repo: TransactionRepository,
        account_id: uuid.UUID,
    ) -> set[tuple[str, str, str, str]]:
        """Load fingerprints of transactions already booked to the account.

        Only statement-sourced rows are considered so a manually entered
        transaction that happens to share a date/amount is not masked.
        """
        from sqlalchemy import select as _select

        result = await txn_repo._session.execute(  # noqa: SLF001
            _select(Transaction).where(
                Transaction.account_id == account_id,
                Transaction.source == TransactionSource.STATEMENT.value,
            )
        )
        seen: set[tuple[str, str, str, str]] = set()
        for txn in result.scalars().all():
            direction = (
                "credit" if txn.transaction_type == "income" else "debit"
            )
            date_key = ""
            if txn.transaction_date is not None:
                date_key = txn.transaction_date.isoformat()[:10]
            fingerprint = (
                date_key,
                StatementService._amount_key(txn.amount),
                direction,
                (txn.reference_number or "").strip().lower(),
            )
            seen.add(fingerprint)
        return seen

    async def _normalize_file(
        self, file: Any
    ) -> list[NormalizedTransaction]:
        """Validate, extract, parse, and normalize a file to canonical rows."""
        mime_type, _filename, _size = await self._validate_file(file)
        extractor = self._extractors.get(mime_type)
        if extractor is None:
            raise exceptions.UnsupportedFileType(
                details={"detected_mime": mime_type}
            )
        raw_rows = await extractor.extract(file)
        if not raw_rows:
            raise exceptions.EmptyStatement(details={})
        parser = self._parsers.get_parser_for_mime(mime_type)
        parsed_rows = await parser.parse(raw_rows)
        return await self._normalizer.normalize(parsed_rows)

    @staticmethod
    def _net_statement_delta(
        normalized: Sequence[NormalizedTransaction],
    ) -> Decimal:
        """Net signed balance delta across all normalized statement rows.

        Income increases balance; expense/transfer decreases it. Only rows with
        a concrete debit/credit classification (not ``unknown``) move the
        balance, matching how manually posted transactions are treated. Uses
        :class:`decimal.Decimal` so currency math stays exact.
        """
        total = Decimal("0")
        for nt in normalized:
            amount = Decimal(str(nt.amount))
            if nt.transaction_type.value == "credit":
                total += amount  # money in
            elif nt.transaction_type.value == "debit":
                total -= amount  # money out
        return total

    async def _persist_one(
        self,
        txn_repo: TransactionRepository,
        nt: NormalizedTransaction,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        categories: Sequence[Any] | None,
    ) -> Transaction | None:
        """Persist a single normalized transaction; return it or ``None``."""
        if nt.transaction_type.value == "unknown":
            return None
        category_id = None
        if categories:
            category_id = self._match_category(nt, categories)
        txn_type = (
            "income" if nt.transaction_type.value == "credit" else "expense"
        )
        return await txn_repo.create(
            account_id=account_id,
            category_id=category_id,
            amount=Decimal(str(nt.amount)),
            transaction_type=txn_type,
            merchant=(nt.merchant or nt.description)[:255],
            description=nt.description,
            transaction_date=_to_datetime(nt.date),
            reference_number=nt.reference_number,
            source=TransactionSource.STATEMENT.value,
            status=TransactionStatus.POSTED.value,
            notes=f"Imported from statement ({nt.currency}).",
        )

    @staticmethod
    def _match_category(
        nt: NormalizedTransaction, categories: Sequence[Any]
    ) -> uuid.UUID | None:
        """Best-effort category match by merchant/description substring."""
        if not categories:
            return None
        text = (nt.merchant or nt.description or "").lower()
        for cat in categories:
            if cat.type != "expense":
                continue
            if text and cat.name.lower() in text:
                return cat.id
        return None

    async def validate_upload(
        self, file: Any, user_id: object | None = None
    ) -> dict[str, Any]:
        """Validate a statement file without extracting or normalizing.

        Args:
            file: The uploaded statement file.
            user_id: Identifier of the authenticated user who owns the upload.

        Returns:
            Dictionary with validation result and basic info.
        """
        mime_type, filename, size = await self._validate_file(file)

        # Attempt to extract a few rows to ensure the file is readable
        extractor = self._extractors.get(mime_type)
        if extractor is None:
            # Should not happen due to validation, but be safe
            raise exceptions.UnsupportedFileType(
                details={"filename": filename, "detected_mime": mime_type}
            )

        try:
            # We only need to know if we can extract at least one row
            raw_rows = await extractor.extract(file)
            if not raw_rows:
                raise exceptions.EmptyStatement(details={"filename": filename})
        except Exception as exc:
            raise exceptions.CorruptStatement(
                details={"filename": filename, "mime_type": mime_type}
            ) from exc

        return {
            "user_id": user_id,
            "source_format": mime_type,
            "source_name": filename,
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "transaction_count": 0,  # Not extracting fully in validation
        }


# Singleton instance for use in the router
sERVICE = StatementService()

# Alias for backward compatibility (if needed)
service = sERVICE


def _to_datetime(value: Any) -> Any:
    """Coerce a date/datetime/string into a timezone-aware datetime.

    Statement dates are date-only; the ``Transaction`` column is a
    timezone-aware ``DateTime``, so we anchor to UTC midnight.
    """
    from datetime import datetime, timezone

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, date):
        return datetime(
            value.year, value.month, value.day, tzinfo=timezone.utc
        )
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)
