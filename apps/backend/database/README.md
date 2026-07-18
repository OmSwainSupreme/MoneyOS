# database/

Database infrastructure for the MoneyOS backend.

- `session.py` — Engine, session factory, and dependency helper (`get_db`).
- `migrations/` — Alembic migration scripts (replaces the legacy top-level `alembic/`).
- `seed/` — Idempotent seed scripts for local/dev data.

Migration workflow is owned by Alembic; no manual schema edits in production.
