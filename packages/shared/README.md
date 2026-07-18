# @moneyos/shared

Code shared between frontend and backend-facing tooling.

- `types/` — Shared TypeScript type definitions (API contracts, domain models).
- `constants/` — Shared constant values (enums, config keys, limits).
- `utils/` — Framework-agnostic utility functions.
- `validation/` — Shared validation schemas (e.g. Zod) kept in sync with backend Pydantic schemas.

Keep this package dependency-light and side-effect free so both apps can import it safely.
