"""Base extractor interface and shared abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

from statements.exceptions import ExtractionFailed


class BaseExtractor(ABC):
    """Abstract base class for all extractors.

    An extractor's sole responsibility is to pull raw structured rows from a
    source file. It must not perform parsing logic that maps rows to a
    particular bank schema, and it must not know anything about databases or AI.
    """

    @abstractmethod
    async def extract(self, file: Any) -> list[dict[str, Any]]:
        """Extract raw rows from the given uploaded file.

        Args:
            file: An object exposing ``read()``/``seek()`` (e.g. ``UploadFile``).

        Returns:
            A list of dictionaries, each representing one raw row.

        Raises:
            ExtractionFailed: if rows cannot be extracted.
        """
        raise NotImplementedError

    @staticmethod
    def _to_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Helper to normalize arbitrary record lists into plain dict rows."""
        return [dict(row) for row in records]

    async def extract_stream(self, file: Any) -> AsyncIterator[dict[str, Any]]:
        """Optional streaming extraction for very large files.

        Default implementation simply yields from :meth:`extract`.
        """
        for row in await self.extract(file):
            yield row
