"""Financial domain (Phase 3).

Canonical financial data model for MoneyOS: accounts, categories, and
transactions. Every future module (statement parsing, analytics, the AI/
decision engine) consumes these models instead of defining its own financial
structures.
"""

from __future__ import annotations

from financial.models import (
    Account,
    AccountType,
    Category,
    CategoryType,
    Transaction,
    TransactionSource,
    TransactionStatus,
    TransactionType,
)
from financial.schemas import (
    AccountCreateRequest,
    AccountResponse,
    AccountUpdateRequest,
    CategoryCreateRequest,
    CategoryResponse,
    CategoryUpdateRequest,
    TransactionCreateRequest,
    TransactionResponse,
    TransactionUpdateRequest,
)
from financial.service import (
    AccountService,
    CategoryService,
    TransactionService,
)
from financial.analytics import AnalyticsService
from financial.decision import FinancialDecisionEngine

__all__ = [
    "Account",
    "AccountType",
    "Category",
    "CategoryType",
    "Transaction",
    "TransactionSource",
    "TransactionStatus",
    "TransactionType",
    "AccountCreateRequest",
    "AccountResponse",
    "AccountUpdateRequest",
    "CategoryCreateRequest",
    "CategoryResponse",
    "CategoryUpdateRequest",
    "TransactionCreateRequest",
    "TransactionResponse",
    "TransactionUpdateRequest",
    "AccountService",
    "CategoryService",
    "TransactionService",
    "AnalyticsService",
    "FinancialDecisionEngine",
]
