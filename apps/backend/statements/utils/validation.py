"""File validation helpers for the Statement Ingestion & Parsing Framework."""

from __future__ import annotations

import mimetypes
from typing import Optional

#: Maximum upload size (10 MB).
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

#: MIME types explicitly supported by the framework.
SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/json",
}


def detect_mime_type(filename: Optional[str], content: bytes = b"") -> str:
    """Best-effort MIME type detection from filename and content sniffing.

    Content sniffing is authoritative for ambiguous cases: some platforms map
    the ``.csv`` extension to ``application/vnd.ms-excel`` via the system
    registry, which would otherwise route a plain CSV to the Excel extractor
    and fail. When the content looks like delimited text, we return
    ``text/csv`` regardless of the filename guess.
    """
    # Authoritative content sniffing first so a real CSV is never misrouted to
    # the Excel extractor just because the OS labelled ``.csv`` as ms-excel.
    if content.startswith(b"%PDF"):
        return "application/pdf"
    if content[:4] == b"PK\x03\x04":
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if content[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return "application/vnd.ms-excel"
    # JSON must be sniffed *before* the CSV comma check, because JSON bodies
    # contain commas too. A JSON document starts with an object/array brace
    # (optionally preceded by whitespace) or carries a ``.json`` extension.
    stripped = content.lstrip()[:1]
    if stripped in (b"{", b"["):
        return "application/json"
    if b"," in content[:256] or b";" in content[:256]:
        return "text/csv"

    guessed, _ = mimetypes.guess_type(filename or "")
    # Guard against the platform quirk where ``.csv`` resolves to ms-excel.
    if guessed and guessed != "application/vnd.ms-excel":
        return guessed
    return "application/octet-stream"


def is_supported_mime_type(mime_type: str) -> bool:
    """Return ``True`` if the MIME type is supported."""
    return mime_type in SUPPORTED_MIME_TYPES
