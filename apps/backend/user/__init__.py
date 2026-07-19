"""User module: profile and preferences for MoneyOS.

This package owns a user's profile/preference data, kept strictly separate
from authentication (which lives in the ``auth`` module) and from future
financial domains.

NOTE: the composed route object (:data:`user_router`) is exported from
:mod:`user.router`, **not** re-exported here. Keeping this package init
router-free avoids a circular import chain through the FastAPI app graph
(``models`` -> ``user`` -> ``user.router`` -> ``api``). Import the router
directly from :mod:`user.router`.
"""

from __future__ import annotations

from user.models import UserProfile

__all__ = ["UserProfile"]
