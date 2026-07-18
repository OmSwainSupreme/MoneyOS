# models/

SQLAlchemy ORM models (database tables). One class per table.

- Map 1:1 to database tables via SQLAlchemy declarative base.
- Keep columns, relationships, and constraints here.
- No business logic — use `services/` and `repositories/`.
