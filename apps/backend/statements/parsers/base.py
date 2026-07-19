"""Base parser interface and shared abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List

from apps.backend.statements.schemas import NormalizedTransaction


class BaseStatementParser(ABC):
    """Abstract base class for all statement parsers.
    
    A parser takes the raw rows produced by an :class:`BaseExtractor` and converts
    them into a canonical intermediate representation. Parsers are
    intentionally decoupled from file formats, extraction logic, and
    persistence concerns.
    """

    @abstractmethod
    async def parse(self, raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Parse raw rows into an intermediate structure.
        
        This method should be pure (no side effects) and return a list of
        dictionaries that represent the structured transaction data, ready
        for normalization.
        
        Args:
            raw_rows: List of raw rows extracted from a file.
            
        Returns:
            List of intermediate rows.
            
        Raises:
            ParsingFailed: if rows cannot be parsed.
        """
        raise NotImplementedError
