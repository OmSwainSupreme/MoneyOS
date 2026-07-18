"""Structured logging configuration.

Scaffolding — configures a basic structured logger. No secrets are logged;
sensitive fields must be masked via core.security.mask_secret.
"""
from __future__ import annotations

import logging
import os


def get_logger(name: str = "moneyos") -> logging.Logger:
    """Return a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    return logger
