# MoneyOS Frontend

Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui.

## Structure
- `app/` — Next.js App Router routes, layouts, and pages.
- `components/` — Reusable presentational components.
  - `ui/` — shadcn/ui primitives.
  - `layout/` — Shells, headers, sidebars, navigation.
  - `charts/` — Data-visualization components.
  - `common/` — Shared generic components.
- `features/` — Feature-scoped modules (self-contained UI + logic per domain).
- `hooks/` — Reusable React hooks.
- `lib/` — Client-side utilities and configured clients.
- `services/` — API clients / data fetching against the backend.
- `store/` — Global state management.
- `styles/` — Global styles and Tailwind layers.
- `types/` — Shared frontend TypeScript types.
- `public/` — Static assets served as-is.
- `tests/` — Frontend tests.

Business logic and pages are added in Phase 1+; this is structural scaffolding only.
