# core/

Application-wide cross-cutting infrastructure.

- `config.py` — Settings loaded from environment (Pydantic-based). Single source of configuration.
- `security.py` — Authentication, authorization, token handling, secret masking, PII helpers.
- `logging.py` — Structured logging configuration (no secrets in logs).

Keep this folder free of domain/business logic.
