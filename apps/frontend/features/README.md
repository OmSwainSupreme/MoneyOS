# features/

Feature-scoped modules. Each feature owns its components, hooks, and services,
keeping related code colocated and imports scalable.

- `auth/` — Authentication & session UI.
- `dashboard/` — Financial overview dashboard.
- `upload/` — Statement / data upload flows.
- `chat/` — Conversational financial assistant UI.
- `analysis/` — Spending & financial analysis views.
- `decision/` — Decision engine results ("Can I buy this?", loans, etc.).
- `profile/` — User profile & settings.

Cross-feature primitives belong in `components/`, not here.
