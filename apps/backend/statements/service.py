"""Service layer for the Statement Ingestion & Parsing Framework.

This module orchestrates the flow: validation -> extraction -> parsing -> normalization.
It depends on abstractions (extractors, parsers, normalizers) that are injected.
"""

from __future__ import annotations

from typing import Any

from apps.backend.statements import exceptions
from apps.backend.statements.extractors.base import BaseExtractor
from apps.backend.statements.extractors.csv import CSVExtractor
from apps.backend.statements.extractors.excel import ExcelExtractor
from apps.backend.statements.extractors.pdf import PDFExtractor
from apps.backend.statements.normalizers.base import BaseNormalizer
from apps.backend.statements.normalizers.statement import StatementNormalizer
from apps.backend.statements.parsers.base import BaseStatementParser
from apps.backend.statements.parsers.generic import GenericParser
from apps.backend.statements.parsers.registry import ParserRegistry
from apps.backend.statements.schemas import NormalizedTransaction, UploadResponse, ValidateResponse
from apps.backend.statements.utils.validation import (
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
        }
        self._parsers = parsers or ParserRegistry()
        self._normalizer = normalizer or StatementNormalizer()
        # Register the generic parser as fallback
        self._parsers.register("generic", GenericParser())

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

    async def process_upload(self, file: Any) -> dict[str, Any]:
        """Process an uploaded statement file and return normalized transactions.

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
        except Exception as exc:
            raise exceptions.ExtractionFailed(
                details={"filename": filename, "mime_type": mime_type}
            ) from exc

        if not raw_rows:
            raise exceptions.EmptyStatement(details={"filename": filename})

        # Parse raw rows into intermediate format (list of dicts)
        parser = self._parsers.get_parser_for_mime(mime_type)
        try:
            parsed_rows = await parser.parse(raw_rows)
        except Exception as exc:
            raise exceptions.NormalizationFailed(
                details={"filename": filename, "mime_type": mime_type}
            ) from exc

        # Normalize parsed rows into canonical transactions
        try:
            normalized_transactions = await self._normalizer.normalize(parsed_rows)
        except Exception as exc:
            raise exceptions.NormalizationFailed(
                details={"filename": filename, "mime_type": mime_type}
            ) from exc

        # Detect currency if possible (from first transaction or raw data)
        currency = None
        if normalized_transactions:
            currency = normalized_transactions[0].currency

        return {
            "source_format": mime_type,
            "source_name": filename,
            "transaction_count": len(normalized_transactions),
            "transactions": [t.model_dump() for t in normalized_transactions],
        }

    async def validate_upload(self, file: Any) -> dict[str, Any]:
        """Validate a statement file without extracting or normalizing.

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
