# tests/

Backend test suite (pytest).

- Mirror the source layout under `tests/` (e.g. `tests/api/`, `tests/services/`).
- Unit tests for logic, integration tests for API + DB (Postgres service in CI).
- Shared fixtures live in `tests/conftest.py`.
