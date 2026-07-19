"""Unit tests for the Statement Ingestion & Parsing Framework."""

from __future__ import annotations

import io
from typing import Any

import pytest

from apps.backend.statements.exceptions import (
    EmptyStatement,
    UnsupportedFileType,
)
from apps.backend.statements.extractors.csv import CSVExtractor
from apps.backend.statements.normalizers.statement import StatementNormalizer
from apps.backend.statements.parsers.generic import GenericParser
from apps.backend.statements.service import StatementService
from apps.backend.statements.utils.validation import (
    SUPPORTED_MIME_TYPES,
    detect_mime_type,
    is_supported_mime_type,
)


class FakeUpload:
    """Minimal in-memory stand-in for ``UploadFile``."""

    def __init__(self, filename: str, content: bytes) -> None:
        self.filename = filename
        self._content = content
        self._cursor = 0

    async def read(self) -> bytes:
        return self._content

    async def seek(self, offset: int) -> int:
        self._cursor = offset
        return self._cursor


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("statement.pdf", "application/pdf"),
        ("statement.csv", "text/csv"),
        ("statement.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ],
)
def test_detect_mime_type(filename: str, expected: str) -> None:
    assert detect_mime_type(filename) == expected


def test_unsupported_mime_type() -> None:
    assert is_supported_mime_type("image/png") is False
    assert is_supported_mime_type("text/csv") is True


@pytest.mark.asyncio
async def test_csv_extract() -> None:
    content = b"date,description,amount\n2026-01-01,Test,100.0\n"
    rows = await CSVExtractor().extract(FakeUpload("s.csv", content))
    assert len(rows) == 1
    assert rows[0]["description"] == "Test"


@pytest.mark.asyncio
async def test_generic_parse_and_normalize() -> None:
    raw = [{"date": "2026-01-01", "description": "Coffee", "amount": "-50.00"}]
    parsed = await GenericParser().parse(raw)
    normalized = await StatementNormalizer().normalize(parsed)
    assert normalized[0].amount == -50.0
    assert normalized[0].transaction_type.value == "debit"


@pytest.mark.asyncio
async def test_empty_file_rejected() -> None:
    service = StatementService()
    with pytest.raises(EmptyStatement):
        await service.process_upload(FakeUpload("s.csv", b""))


@pytest.mark.asyncio
async def test_unsupported_type_rejected() -> None:
    service = StatementService()
    with pytest.raises(UnsupportedFileType):
        await service.process_upload(FakeUpload("s.png", b"data"))
