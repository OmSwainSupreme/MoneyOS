"""Uvicorn entrypoint for the MoneyOS backend.

This module exposes the ASGI ``app`` object consumed by Uvicorn (directly or
via the Docker ``CMD``) and provides a ``__main__`` block for local
development with hot reload.
"""

from __future__ import annotations

import os

from core.app import create_app

# Module-level application instance used by ASGI servers (e.g. ``uvicorn
# main:app``). The factory keeps construction consistent across environments.
app = create_app()


def _main() -> None:
    """Launch the development server via Uvicorn with hot reload."""
    import uvicorn

    port = int(os.getenv("BACKEND_PORT", os.getenv("PORT", "8000")))
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )


if __name__ == "__main__":
    _main()
