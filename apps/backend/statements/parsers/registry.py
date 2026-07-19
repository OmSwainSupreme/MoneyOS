"""Parser registry for the Statement Ingestion & Parsing Framework."""

from __future__ import annotations

from typing import Dict, Optional

from apps.backend.statements.exceptions import UnsupportedFileType
from apps.backend.statements.parsers.base import BaseStatementParser


class ParserRegistry:
    """Registry that maps formats/mime-types to statement parsers.

    The registry makes it trivial to plug in future bank-specific or
    format-specific parsers without changing the service layer.
    """

    def __init__(self) -> None:
        self._parsers: Dict[str, BaseStatementParser] = {}
        self._mime_map: Dict[str, str] = {}

    def register(self, key: str, parser: BaseStatementParser) -> None:
        """Register a parser under a key (e.g. 'generic', 'hdfc')."""
        self._parsers[key] = parser

    def register_for_mime(self, mime_type: str, key: str) -> None:
        """Map a MIME type to an already-registered parser key."""
        if key not in self._parsers:
            raise KeyError(f"No parser registered under key '{key}'")
        self._mime_map[mime_type] = key

    def get(self, key: str) -> Optional[BaseStatementParser]:
        """Return a parser by key, or ``None`` if not registered."""
        return self._parsers.get(key)

    def get_parser_for_mime(self, mime_type: str) -> BaseStatementParser:
        """Return the parser registered for a MIME type.

        Falls back to the ``generic`` parser when no specific mapping exists.

        Raises:
            UnsupportedFileType: if no fallback parser is available.
        """
        key = self._mime_map.get(mime_type, "generic")
        parser = self._parsers.get(key)
        if parser is None:
            raise UnsupportedFileType(
                "No parser is available for the provided file type.",
                details={"mime_type": mime_type},
            )
        return parser

    def list_parsers(self) -> Dict[str, str]:
        """Return a mapping of parser keys to their class names."""
        return {key: type(p).__name__ for key, p in self._parsers.items()}
