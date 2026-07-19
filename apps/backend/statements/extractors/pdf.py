"""PDF extractor for the Statement Ingestion & Parsing Framework."""

from __future__ import annotations

from typing import Any, List

from apps.backend.statements.exceptions import CorruptStatement, ExtractionFailed
from apps.backend.statements.extractors.base import BaseExtractor


class PDFExtractor(BaseExtractor):
    """Extract raw text lines from PDF files.

    This extractor pulls the raw text content from each page of a PDF and
    returns one row per non-empty line. It does NOT attempt to interpret the
    meaning of the text. Bank-specific layout logic belongs in parsers.
    """

    async def extract(self, file: Any) -> List[dict[str, Any]]:
        """Extract raw line rows from a PDF file.

        Args:
            file: Object exposing ``read()``/``seek()`` (e.g. ``UploadFile``).

        Returns:
            List of dict rows keyed by ``line_number`` and ``raw_text``.

        Raises:
            CorruptStatement: if the PDF cannot be opened.
            ExtractionFailed: if the content cannot be read.
        """
        try:
            import pypdf  # lazy import to avoid hard dependency
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise ExtractionFailed(
                "PDF support requires the 'pypdf' package.",
                details={"filename": getattr(file, "filename", "unknown")},
            ) from exc

        contents = await file.read()
        await file.seek(0)

        try:
            reader = pypdf.PdfReader(io.BytesIO(contents))
        except Exception as exc:
            raise CorruptStatement(
                "The provided PDF file appears to be corrupt or unreadable.",
                details={"filename": getattr(file, "filename", "unknown")},
            ) from exc

        rows: List[dict[str, Any]] = []
        for index, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:
                raise ExtractionFailed(
                    "Failed to extract text from a PDF page.",
                    details={"filename": getattr(file, "filename", "unknown")},
                ) from exc
            for line_number, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                rows.append({"page_number": index, "line_number": line_number, "raw_text": stripped})

        return rows


import io  # noqa: E402  (placed after class for readability of imports above)
