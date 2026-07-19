"""Pydantic v2 schemas for the Statement Ingestion & Parsing Framework."""

from __future__ import annotations

from datetime import date as _date
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Canonical transaction classification."""

    DEBIT = "debit"
    CREDIT = "credit"
    UNKNOWN = "unknown"


class NormalizedTransaction(BaseModel):
    """Canonical normalized transaction structure.

    This is the single output contract produced by the normalization
    layer regardless of the originating file format or bank.
    """

    date: _date = Field(..., description="Transaction posting date.")
    description: str = Field(..., description="Human readable description.")
    amount: float = Field(..., description="Signed amount. Negative for debit.")
    currency: str = Field("INR", description="ISO 4217 currency code.")
    transaction_type: TransactionType = Field(
        TransactionType.UNKNOWN, description="Debit or credit classification."
    )
    balance: Optional[float] = Field(None, description="Running balance if present.")
    reference_number: Optional[str] = Field(
        None, description="Bank reference / cheque number if present."
    )
    category: Optional[str] = Field(
        None, description="Nullable; not assigned by this framework."
    )
    merchant: Optional[str] = Field(
        None, description="Nullable; not assigned by this framework."
    )
    raw_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Original unmodified row used to produce this record.",
    )


class NormalizedStatement(BaseModel):
    """Container returned by the framework for a parsed upload."""

    source_format: str = Field(..., description="Detected input format.")
    source_name: str = Field(..., description="Original file name.")
    currency: Optional[str] = Field(None, description="Detected currency if any.")
    transaction_count: int = Field(..., description="Number of normalized rows.")
    transactions: list[NormalizedTransaction] = Field(default_factory=list)


class UploadResponse(BaseModel):
    """Response payload for POST /statements/upload."""

    source_format: str
    source_name: str
    transaction_count: int
    transactions: list[NormalizedTransaction]


class ValidateResponse(BaseModel):
    """Response payload for POST /statements/validate."""

    source_format: str
    source_name: str
    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    transaction_count: int = 0
