# User Module — Deferred Architecture Items

This document records design decisions that are **intentionally out of scope**
for Phase 2.4 but are acknowledged here so future phases can pick them up
without re-litigating the trade-offs. The current implementation is production-
ready for the stated requirements; the items below are scaling/evolution
concerns, not defects.

## 1. Registration coupling (auth → user lazy import)
**Current state:** `AuthService.register` instantiates `UserService` inline
(lazy import) to create the default profile inside the registration
transaction.
**Why deferred:** The existing monolith has no event bus or dispatcher, and a
single atomic transaction across `users` + `user_profiles` is the simplest
correct behavior. A lazy import avoids a circular module dependency today.
**Future:** Introduce a domain-event dispatcher (`UserRegistered` event) so the
auth module publishes and the user module subscribes (sync within the existing
transaction, or async via a worker). This decouples the packages fully.

## 2. Monolithic profile + preferences table
**Current state:** `user_profiles` holds both structural attributes
(`display_name`, `avatar_url`) and operational preferences (`currency`,
`theme`, `language`, `date_format`, `timezone`) in one row.
**Why deferred:** One-to-one, always-present, seldom-updated; a single table is
simpler and avoids join overhead at this scale.
**Future:** Split into `user_profiles` (identity/display) and
`user_preferences` (settings) if write patterns diverge (e.g. high-frequency
preference updates, per-device preferences).

## 3. Static currency / preference whitelists
**Current state:** `CURRENCIES`, `THEMES`, `LANGUAGES`, `DATE_FORMATS` are
hard-coded tuples mirrored in the model, schema, and DB CHECK constraints.
**Why deferred:** The supported set is fixed by product scope for launch.
**Future:** For dynamic multi-currency, move currency to a reference/config
table and source the whitelist at runtime (or drop the CHECK in favor of a FK
to the reference table). Keep the Pydantic whitelist as the ingress fast-path.

## 4. Date-format parsing adapter
**Current state:** Date formats are stored as user-facing strings
(`'DD/MM/YYYY'`).
**Why deferred:** No statement/transaction import exists yet, so no parser
consumer exists.
**Future:** Add an adapter mapping JS/Moment-style tokens to Python `strptime`
(`%d/%m/%Y`) when the transactions/statement-parsing phase lands. Centralize
the mapping in one module to avoid drift.

## 5. Multi-tenancy / organizations
**Current state:** Defaults (currency, timezone, format) live on the individual
`UserProfile`.
**Why deferred:** No organization/workspace concept exists yet.
**Future:** Introduce an `Organization` context that owns baseline currency,
timezone, and format defaults; user preferences become overrides on top of the
org baseline. The `user_id` FK stays; an `org_id` association is added.

## 6. Service→Repository injection
**Status:** Resolved in this phase. `UserService` now accepts an injected
`UserProfileRepository` (falls back to constructing one from the session) —
Dependency Inversion is satisfied for testing and swapping persistence.
