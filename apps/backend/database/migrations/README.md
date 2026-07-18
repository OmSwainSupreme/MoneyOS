# migrations/

Alembic database migrations for MoneyOS.

This folder holds versioned migration scripts. The Alembic environment is
initialized in Phase 1. Conventions:

- One migration per logical schema change.
- Always provide both `upgrade()` and `downgrade()`.
- Never edit a committed migration — add a new one instead.

Seed data belongs in `../seed/`, not here.
