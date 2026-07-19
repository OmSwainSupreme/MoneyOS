"""Dedicated exceptions for the Statement Ingestion & Parsing Framework.

These exceptions are intentionally decoupled from database, auth, and
financial domains. They describe failures that can occur while ingesting,
parsing, and normalizing uploaded bank statements.
"""

from __future__ import annotations


class StatementError(Exception):
    """Base class for all statement framework errors."""

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        return self.message


class UnsupportedFileType(StatementError):
    """Raised when the uploaded file format is not supported."""


class FileTooLarge(StatementError):
    """Raised when the uploaded file exceeds the maximum allowed size."""


class EmptyStatement(StatementError):
    """Raised when the supplied file contains no usable data."""


class CorruptStatement(StatementError):
    """Raised when the file is structurally invalid or unreadable."""


class ExtractionFailed(StatementError):
    """Raised when an extractor cannot pull rows from the source file."""


class NormalizationFailed(StatementError):
    """Raised when extracted rows cannot be normalized into canonical form."""


class ValidationFailed(StatementError):
    """Raised when a statement fails structural or semantic validation."""
