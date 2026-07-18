"""Security helpers: token handling, PII scrubbing, secret masking.

Scaffolding only — concrete algorithms are implemented in Phase 1+.
All PII must be scrubbed before any data leaves the trust boundary to
third-party LLM providers (see docs/security/).
"""

from __future__ import annotations


def mask_secret(value: str | None, visible: int = 4) -> str:
    """Return a masked representation of a secret for safe logging."""
    if not value:
        return "<empty>"
    if len(value) <= visible:
        return "*" * len(value)
    return value[:visible] + "*" * (len(value) - visible)


def scrub_pii(text: str | None) -> str:
    """Placeholder for PII scrubbing before sending to external providers.

    Implemented in Phase 1 with a redaction strategy. Returns input unchanged
    for now so callers can be wired up safely.
    """
    return text or ""
