"""Excel extractor for the Statement Ingestion & Parsing Framework."""

from __future__ import annotations

from typing import Any, List

from statements.exceptions import CorruptStatement, ExtractionFailed
from statements.extractors.base import BaseExtractor


class ExcelExtractor(BaseExtractor):
    """Extract raw rows from Excel (.xlsx / .xls) files.

    Reads the first worksheet of the workbook and returns one dict row per
    data row, using the first row as headers. No bank-specific logic here.
    """

    async def extract(self, file: Any) -> List[dict[str, Any]]:
        """Extract raw rows from an Excel workbook.

        Args:
            file: Object exposing ``read()``/``seek()`` (e.g. ``UploadFile``).

        Returns:
            List of dict rows.

        Raises:
            CorruptStatement: if the workbook cannot be opened.
            ExtractionFailed: if rows cannot be read.
        """
        try:
            import openpyxl  # lazy import to avoid hard dependency
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise ExtractionFailed(
                "Excel support requires the 'openpyxl' package.",
                details={"filename": getattr(file, "filename", "unknown")},
            ) from exc

        contents = await file.read()
        await file.seek(0)

        try:
            workbook = openpyxl.load_workbook(
                io.BytesIO(contents), read_only=True, data_only=True
            )
        except Exception as exc:
            raise CorruptStatement(
                "The provided Excel file appears to be corrupt or unreadable.",
                details={"filename": getattr(file, "filename", "unknown")},
            ) from exc

        try:
            sheet = workbook[workbook.sheetnames[0]]
            rows_iter = sheet.iter_rows(values_only=True)
            header = [str(cell).strip() if cell is not None else "" for cell in next(rows_iter, [])]
            records: List[dict[str, Any]] = []
            for row in rows_iter:
                if all(cell is None for cell in row):
                    continue
                records.append(
                    {
                        header[i]: (row[i] if i < len(row) else None)
                        for i in range(len(header))
                    }
                )
        except Exception as exc:
            raise ExtractionFailed(
                "Failed to read rows from the Excel workbook.",
                details={"filename": getattr(file, "filename", "unknown")},
            ) from exc
        finally:
            workbook.close()

        return records


import io  # noqa: E402  (placed after class for readability of imports above)
