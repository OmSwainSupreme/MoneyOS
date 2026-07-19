"""Financial-domain exceptions.

Plain domain errors raised by the financial service/repository layers. They
carry no HTTP status codes so business logic stays transport-agnostic; the
global exception handler in :mod:`core.errors` maps each to a unified error
envelope (see :func:`core.app._register_exception_handlers`).
"""

from __future__ import annotations


class FinancialError(Exception):
    """Base class for all financial-domain failures."""


class AccountNotFound(FinancialError):
    """Raised when an account id does not resolve for the requesting user."""


class CategoryNotFound(FinancialError):
    """Raised when a category id does not exist (or is not visible to user)."""


class TransactionNotFound(FinancialError):
    """Raised when a transaction id does not resolve for the user."""


class AccountOwnershipError(FinancialError):
    """Raised when a user attempts to access an account they do not own."""


class CategoryOwnershipError(FinancialError):
    """Raised when a user attempts to mutate a system category."""


class InvalidCurrencyError(FinancialError):
    """Raised when a currency code is not in the supported set."""


class InvalidEnumValueError(FinancialError):
    """Raised when an enum-backed field receives an unsupported value."""


class InvalidAmountError(FinancialError):
    """Raised when an amount violates a business rule (e.g. non-positive)."""
