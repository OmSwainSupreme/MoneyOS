# api/

HTTP layer for the MoneyOS backend.

- `routes/` — FastAPI routers (versioned under `/api/v1`). One module per domain/resource.
- `dependencies/` — Shared FastAPI dependencies: auth, DB sessions, request validation, current-user resolution.

This folder contains **only transport concerns** (request/response wiring). Business logic lives in `services/`, and data access in `repositories/`.
