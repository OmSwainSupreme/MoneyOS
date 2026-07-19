"""Base normalizer interface for the Statement Ingestion & Parsing Framework."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List

from statements.schemas import NormalizedTransaction


class BaseNormalizer(ABC):
    """Abstract base class for normalizers.

    A normalizer converts an intermediate parsed representation into the
    canonical :class:`NormalizedTransaction` contract. It performs no
    financial calculations, categorization, or persistence.
    """

    @abstractmethod
    async def normalize(self, parsed_rows: List[dict[str, Any]]) -> List[NormalizedTransaction]:
        """Normalize parsed rows into canonical transactions.

        Args:
            parsed_rows: Intermediate rows from a parser.

        Returns:
            List of normalized transactions.

        Raises:
            NormalizationFailed: if a row cannot be normalized.
        """
        raise NotImplementedError
