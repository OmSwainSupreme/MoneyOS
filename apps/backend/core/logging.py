"""Logging configuration.

Provides a centralized logger factory that relies on root-logger
propagation: module loggers propagate to a single root handler instead of
each attaching their own. ``configure_root_logger`` installs the root
handler exactly once, so duplicated or double-emitted records are avoided.

No secrets are logged; sensitive fields must be masked via
:func:`core.security.mask_secret` before reaching a log record.
"""

from __future__ import annotations

import logging

from core.config import Settings, get_settings

_LOG_FORMAT = (
    "%(asctime)s %(levelname)-8s %(name)s "
    "[%(filename)s:%(lineno)d] %(message)s"
)
_ROOT_CONFIGURED = False


def get_logger(name: str = "moneyos") -> logging.Logger:
    """Return a module logger that propagates to the configured root.

    Args:
        name: Logger name, typically the module or service name.

    Returns:
        A :class:`logging.Logger` that emits through the root handler.
    """
    logger = logging.getLogger(name)
    # Propagate to the root logger so a single handler formats all output.
    logger.propagate = True
    return logger


def configure_root_logger(settings: Settings | None = None) -> None:
    """Configure the root logger once from application settings.

    Idempotent: repeated calls leave the existing handler in place.

    Args:
        settings: Optional settings. When omitted, the cached settings
            singleton is used.
    """
    global _ROOT_CONFIGURED
    if _ROOT_CONFIGURED:
        return
    resolved = settings or get_settings()
    root = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(handler)
    root.setLevel(resolved.log_level.upper())
    _ROOT_CONFIGURED = True
