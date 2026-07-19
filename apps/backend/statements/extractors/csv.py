"""CSV extractor for the Statement Ingestion & Parsing Framework."""

from __future__ import annotations

import csv
import io
from typing import Any, List

from apps.backend.statements.exceptions import ExtractionFailed
from apps.backend.statements.extractors.base import BaseExtractor


class CSVExtractor(BaseExtractor):
    """Extract raw rows from CSV files.

    Uses Python's built-in ``csv`` module and assumes the first row is a
    header row. No bank-specific logic is applied here.
    """

    async def extract(self, file: Any) -> List[dict[str, Any]]:
        """Extract raw rows from a CSV file.

        Args:
            file: Object exposing ``read()``/``seek()`` (e.g. ``UploadFile``).

        Returns:
            List of dict rows.

        Raises:
            ExtractionFailed: if the file cannot be read as CSV.
        """
        contents = await file.read()
        await file.seek(0)

        try:
            decoded = contents.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ExtractionFailed(
                "Failed to decode CSV file as UTF-8.",
                details={"filename": getattr(file, "filename", "unknown")},
            ) from exc

        buffer = io.StringIO(decoded)
        try:
            reader = csv.DictReader(buffer)
            rows = [dict(row) for row in reader]
        except Exception as exc:
            raise ExtractionFailed(
                "Failed to parse CSV content.",
                details={"filename": getattr(file, "filename", "unknown")},
            ) from exc

        return rows
