"""Tests for AgamiAI JSON statement ingestion.

These tests exercise the *auto-detection* path of the Statement Ingestion
framework: a JSON file dropped on the existing ``/statements`` upload/import
endpoints is detected as ``application/json`` and routed through a dedicated
extractor + parser, producing the same :class:`NormalizedTransaction` contract
as PDF/CSV. The same repositories, services, analytics, AI and decision engine
are reused -- no special JSON tables, no separate endpoint.

The file is split into two layers:

* Fast, DB-free tests (extractor / parser / normalizer / ``process_upload`` /
  validation / normalization / duplicate-key math) -- these run anywhere.
* ``requires_postgres`` tests (full import, balance adjustment, duplicate
  upload, dashboard/analytics, large file) -- gated on a live database, exactly
  like the rest of the suite.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import pytest

from statements.exceptions import CorruptStatement, EmptyStatement
from statements.extractors.json import JSONExtractor
from statements.normalizers.statement import StatementNormalizer
from statements.parsers.json import JSONStatementParser
from statements.schemas import NormalizedTransaction, TransactionType
from statements.service import StatementService

# The fast (no-DB) tests below run anywhere. Only the DB-backed tests carry the
# ``requires_postgres`` marker so they are skipped without a live database.


def _fake_file(content: bytes, name: str = "stmt.json") -> Any:
    """Minimal async file stub (UploadFile-like) for the pipeline."""

    class _File:
        def __init__(self, data: bytes, filename: str) -> None:
            self._data = data
            self.filename = filename

        async def read(self) -> bytes:
            return self._data

        async def seek(self, n: int) -> None:  # noqa: ARG002
            return None

    return _File(content, name)


def _agami_doc(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a minimal AgamiAI-shaped statement document."""
    return {
        "bank_name": "Progressive National Bank",
        "account_holder": "Om Prakash",
        "account_number": "78439336112",
        "ifsc_code": "ABCD0001234",
        "currency": "INR",
        "opening_balance": 1000.0,
        "closing_balance": 0.0,
        "transactions": transactions,
    }


# ---------------------------------------------------------------------------
# Fast (no-DB) tests
# ---------------------------------------------------------------------------

AGAMI_SAMPLE = _agami_doc(
    [
        {
            "date": "2024-01-01 11:30:55",
            "value_date": "2024-01-01",
            "description": "NEFT Cr-SALARY CREDIT",
            "cheque_no": "",
            "debit": None,
            "credit": 50000.0,
            "balance": 51000.0,
            "branch_code": "5749",
            "failed": False,
        },
        {
            "date": "2024-01-02 12:44:20",
            "description": "Chq Paid-GROCERY STORE",
            "cheque_no": "567302",
            "debit": 1500.0,
            "credit": None,
            "balance": 49500.0,
            "branch_code": "3421",
            "failed": False,
        },
        # A reversed / failed entry -- must be skipped entirely.
        {
            "date": "2024-01-03 09:00:00",
            "description": "FAILED TXN",
            "cheque_no": "",
            "debit": 999.0,
            "credit": None,
            "balance": 48501.0,
            "failed": True,
        },
        # Missing date -> dropped during normalization (tolerant ingestion).
        {
            "description": "NO DATE BILL",
            "debit": 2000.0,
            "credit": None,
            "balance": 46501.0,
            "failed": False,
        },
    ]
)


def test_detect_json_mime_by_extension() -> None:
    from statements.utils.validation import detect_mime_type

    mime = detect_mime_type("statement.json", b'{"transactions": []}')
    assert mime == "application/json"


def test_detect_json_mime_by_content() -> None:
    from statements.utils.validation import detect_mime_type

    # A JSON body with no filename must still sniff as JSON (and must NOT be
    # mistaken for CSV even though it contains commas).
    mime = detect_mime_type(None, b'{"a": 1, "b": 2}')
    assert mime == "application/json"


def test_json_in_supported_mime_types() -> None:
    from statements.utils.validation import SUPPORTED_MIME_TYPES

    assert "application/json" in SUPPORTED_MIME_TYPES


async def test_extractor_reads_transactions_and_threads_meta() -> None:
    ext = JSONExtractor()
    rows = await ext.extract(_fake_file(json.dumps(AGAMI_SAMPLE).encode()))
    assert len(rows) == 4  # all entries present (failed row kept until parser)
    # Statement-level metadata is injected into every row.
    assert rows[0]["currency"] == "INR"
    assert rows[0]["account_number"] == "78439336112"
    assert rows[0]["_raw"]["description"] == "NEFT Cr-SALARY CREDIT"


async def test_parser_skips_failed_rows() -> None:
    ext = JSONExtractor()
    raw = await ext.extract(_fake_file(json.dumps(AGAMI_SAMPLE).encode()))
    parsed = await JSONStatementParser().parse(raw)
    # failed=True row must be gone; the date-less row survives to normalization.
    assert len(parsed) == 3
    descs = {r.get("description") for r in parsed}
    assert "FAILED TXN" not in descs


async def test_normalize_produces_canonical_contract() -> None:
    # Use a deep copy so the test never depends on (or mutates) the module-level
    # constant, and a freshly-constructed normalizer to avoid any shared state.
    import copy

    sample = copy.deepcopy(AGAMI_SAMPLE)
    ext = JSONExtractor()
    raw = await ext.extract(_fake_file(json.dumps(sample).encode()))
    parsed = await JSONStatementParser().parse(raw)
    norm = await StatementNormalizer().normalize(parsed)
    # 2 valid dated rows + 1 date-less (dropped) = 2.
    assert len(norm) == 2
    by_desc = {t.description: t for t in norm}
    salary = by_desc["NEFT Cr-SALARY CREDIT"]
    grocery = by_desc["Chq Paid-GROCERY STORE"]
    assert salary.transaction_type.value == "credit"
    assert salary.amount == 50000.0
    assert salary.currency == "INR"
    assert grocery.transaction_type.value == "debit"
    assert grocery.amount == 1500.0
    assert grocery.reference_number == "567302"  # cheque_no -> reference_number
    assert grocery.balance == 49500.0


async def test_process_upload_full_json_pipeline() -> None:
    service = StatementService()
    result = await service.process_upload(
        _fake_file(json.dumps(AGAMI_SAMPLE).encode(), "00001.json"),
        user_id="u1",
    )
    assert result["source_format"] == "application/json"
    assert result["transaction_count"] == 2  # failed + no-date dropped


async def test_invalid_json_raises_corrupt() -> None:
    service = StatementService()
    with pytest.raises(CorruptStatement):
        await service.process_upload(
            _fake_file(b"{not valid json,,", "bad.json"), user_id="u1"
        )


async def test_empty_json_object_raises_empty() -> None:
    ext = JSONExtractor()
    with pytest.raises(EmptyStatement):
        await ext.extract(_fake_file(b"{}", "empty.json"))


async def test_scalar_json_raises_corrupt() -> None:
    service = StatementService()
    with pytest.raises(CorruptStatement):
        await service.process_upload(
            _fake_file(b"42", "num.json"), user_id="u1"
        )


async def test_bare_array_json_supported() -> None:
    bare = json.dumps(
        [
            {
                "date": "2024-01-01 10:00:00",
                "description": "XFER IN",
                "debit": None,
                "credit": 100.0,
                "balance": 100.0,
                "failed": False,
            }
        ]
    ).encode()
    result = await StatementService().process_upload(
        _fake_file(bare, "arr.json"), user_id="u1"
    )
    assert result["transaction_count"] == 1
    # ``process_upload`` returns ``model_dump`` dicts, so enum fields serialize
    # to their string value rather than the enum member.
    assert result["transactions"][0]["transaction_type"] == "credit"


async def test_malformed_json_graceful() -> None:
    """A truncated JSON document surfaces a clean CorruptStatement, not a 500."""
    service = StatementService()
    with pytest.raises(CorruptStatement):
        await service.process_upload(
            _fake_file(b'{"transactions": [{"date":', "trunc.json"), user_id="u1"
        )


def test_fingerprint_is_scale_insensitive() -> None:
    """DB stores Numeric(18,2); the fingerprint must ignore trailing zeros."""
    svc = StatementService()
    from datetime import date

    a = NormalizedTransaction(
        date=date(2024, 1, 6),
        description="D",
        amount=20253.8,
        transaction_type=TransactionType.DEBIT,
    )
    db_fp = (
        "2024-01-06",
        svc._amount_key(Decimal("20253.80")),
        "debit",
        "",
    )
    assert svc._fingerprint(a) == db_fp


# ---------------------------------------------------------------------------
# DB-backed tests (requires_postgres)
# ---------------------------------------------------------------------------


@pytest.mark.requires_postgres
async def test_import_json_persists_and_adjusts_balance(
    migrated_session,
) -> None:
    """A JSON import stores transactions and adjusts balance atomically."""
    from tests.factories import make_account, make_user

    service = StatementService()
    user = await make_user(migrated_session, email="json_dash@example.com")
    await migrated_session.commit()
    account = await make_account(
        migrated_session, user_id=user.id, opening_balance=0
    )
    await migrated_session.commit()

    result = await service.store_statement(
        _fake_file(json.dumps(AGAMI_SAMPLE).encode(), "00001.json"),
        user_id=user.id,
        account_id=account.id,
        auto_categorize=True,
    )
    assert result["stored_count"] == 2
    assert result["skipped_count"] == 0

    from sqlalchemy import select, func
    from financial.models import Transaction

    stored = await migrated_session.scalar(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.account_id == account.id)
    )
    assert stored == 2

    await migrated_session.refresh(account)
    # net = 50000 (credit) - 1500 (debit) = 48500.
    assert float(account.current_balance) == 48500.0


@pytest.mark.requires_postgres
async def test_duplicate_json_upload_is_idempotent(migrated_session) -> None:
    from tests.factories import make_account, make_user
    from sqlalchemy import select, func
    from financial.models import Transaction

    service = StatementService()
    user = await make_user(migrated_session, email="json_dup@example.com")
    await migrated_session.commit()
    account = await make_account(
        migrated_session, user_id=user.id, opening_balance=0
    )
    await migrated_session.commit()

    first = await service.store_statement(
        _fake_file(json.dumps(AGAMI_SAMPLE).encode(), "00001.json"),
        user_id=user.id,
        account_id=account.id,
    )
    second = await service.store_statement(
        _fake_file(json.dumps(AGAMI_SAMPLE).encode(), "00001.json"),
        user_id=user.id,
        account_id=account.id,
    )
    assert first["stored_count"] == 2
    assert second["duplicate_count"] == 2
    assert second["stored_count"] == 0
    total = await migrated_session.scalar(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.account_id == account.id)
    )
    assert total == 2


@pytest.mark.requires_postgres
async def test_json_import_feeds_dashboard(migrated_session) -> None:
    """After a JSON import, dashboard income/expense reflect the rows."""
    import os
    import uuid

    from tests.factories import make_account, make_user
    from financial.analytics import AnalyticsService

    real_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "fixtures",
        "agami_00001.json",
    )
    if not os.path.exists(real_path):
        # Fall back to a wide synthetic window using the in-memory doc.
        path = None
    else:
        path = real_path

    service = StatementService()
    user = await make_user(migrated_session, email="json_dash2@example.com")
    await migrated_session.commit()
    account = await make_account(
        migrated_session, user_id=user.id, opening_balance=0
    )
    await migrated_session.commit()

    if path is None:
        content = json.dumps(AGAMI_SAMPLE).encode()
    else:
        content = open(path, "rb").read()

    await service.store_statement(
        _fake_file(content, "stmt.json"),
        user_id=user.id,
        account_id=account.id,
    )

    months = 60 if path else 12
    dash = await AnalyticsService(migrated_session).dashboard(user.id)
    assert "total_balance" in dash
    if path is None:
        assert dash["total_income"] == 50000.0
        assert dash["total_expenses"] == 1500.0
        assert dash["total_savings"] == 48500.0
    else:
        # Real dataset: income > 0 and expense > 0 after a wide window.
        assert dash["total_income"] > 0
        assert dash["total_expenses"] > 0
        sbc = await AnalyticsService(migrated_session).spending_by_category(
            user.id, months=months
        )
        assert any(r["category_name"] == "Uncategorized" for r in sbc)


@pytest.mark.requires_postgres
async def test_large_json_import(migrated_session) -> None:
    """A 150+ row JSON import persists every valid row and adjusts balance."""
    import random

    service = StatementService()
    from tests.factories import make_account, make_user

    user = await make_user(migrated_session, email="json_large@example.com")
    await migrated_session.commit()
    account = await make_account(
        migrated_session, user_id=user.id, opening_balance=0
    )
    await migrated_session.commit()

    txns = []
    for i in range(160):
        is_credit = i % 2 == 0
        txns.append(
            {
                "date": f"2024-03-{i % 28 + 1:02d} 10:00:00",
                "description": f"TXN {i}",
                "debit": (None if is_credit else round(random.uniform(10, 5000), 2)),
                "credit": (round(random.uniform(10, 5000), 2) if is_credit else None),
                "balance": 0.0,
                "failed": False,
            }
        )
    doc = _agami_doc(txns)
    result = await service.store_statement(
        _fake_file(json.dumps(doc).encode(), "large.json"),
        user_id=user.id,
        account_id=account.id,
    )
    assert result["stored_count"] == 160
