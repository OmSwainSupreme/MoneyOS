"""Authentication & authorization module.

This package owns identity for MoneyOS. It is intentionally isolated from other
domains (accounts, transactions, decisions) so the auth surface can evolve
independently.

NOTE: the composed route objects (:data:`auth_router`, :data:`user_router`) are
exported from :mod:`auth.router`, **not** re-exported here. Keeping this
package init router-free avoids a circular import chain through the FastAPI app
graph (``models`` -> ``auth`` -> ``auth.router`` -> ``api``). Import routers
directly from :mod:`auth.router`.
"""

from __future__ import annotations

from auth.models import User

__all__ = ["User"]
