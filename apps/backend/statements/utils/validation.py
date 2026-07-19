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
}


def detect_mime_type(filename: Optional[str], content: bytes = b"") -> str:
    """Best-effort MIME type detection from filename and content sniffing."""
    guessed, _ = mimetypes.guess_type(filename or "")
    if guessed:
        return guessed
    if content.startswith(b"%PDF"):
        return "application/pdf"
    if content[:4] == b"PK\x03\x04":
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if content[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return "application/vnd.ms-excel"
    if b"," in content[:256] or b";" in content[:256]:
        return "text/csv"
    return "application/octet-stream"


def is_supported_mime_type(mime_type: str) -> bool:
    """Return ``True`` if the MIME type is supported."""
    return mime_type in SUPPORTED_MIME_TYPES
