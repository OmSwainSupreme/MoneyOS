# Financial Domain — Deferred Items & Architecture Decisions

This document records the non-obvious decisions made while building Phase 3
(Financial Domain) and explicitly defers work that is out of scope for this
phase.

## Decisions made in this phase

### Account deletion strategy: hard-delete with `ON DELETE CASCADE`
Deleting an account **hard-deletes** the row; its transactions are removed
atomically via `ON DELETE CASCADE` on `transactions.account_id`. We do **not**
soft-delete accounts. Rationale: a soft-deleted account would leave a dangling
balance with no UI surface, and a cascade keeps referential integrity simple
and provable. The cascade is enforced at the database level, so it holds
regardless of which code path issues the delete.

### Transfer representation: type-tagged only
A transfer is modelled as a transaction with `transaction_type = "transfer"`.
`current_balance` is decreased by the transfer amount (same as an expense),
mirroring the "money left this account" view. There is **no** balancing logic
that creates a paired counter-transaction in a destination account — that would
imply multi-account orchestration (and charge/credit ordering) that belongs to a
future transfers/ledger feature. Consumers that need a two-sided transfer should
derive it from the `transfer` type tag.

### System categories: shared, read-only baseline
`SYSTEM_CATEGORIES` (seeded via `financial.seed.seed_system_categories`) are
inserted with `user_id = NULL` and `is_system = True`. They are visible to every
user (the repository's visibility predicate is `user_id == me OR is_system`).
The service **blocks mutation and deletion** of system categories
(`CategoryOwnershipError` → 403). This keeps the baseline stable and lets users
layer their own categories on top.

### Account balance is a stored, derived value
`current_balance` is not computed on read; it is adjusted in the **same
committed transaction** as the transaction row write (`_balance_delta` in
`financial.service`). Non-posted (pending/failed) transactions do not move the
balance. Reversing/rolling back a posted transaction updates the balance by the
matching signed delta so the two can never diverge. This is the core balance-
safety guarantee: a malformed request cannot leave a balance inconsistent with
the ledger.

### Ownership scoping
Every read in the repositories is scoped to the requesting `user_id`:
- Accounts: `Account.user_id == user_id`.
- Categories: `(user_id == me) OR is_system` (visibility only).
- Transactions: joined through `accounts` so only the user's own accounts' rows
  are reachable.

A user can never read, mutate, or attach a transaction to another user's
account; the service raises `AccountNotFound` (404, not 403) to avoid leaking
existence.

## Deferred (explicitly NOT implemented this phase)
The following are out of scope per the Phase 3 brief and are intentionally
absent:

- **Statement parsing / import pipeline** — transactions support a `source`
  enum (`manual`/`statement`/`import`) but no ingestion logic exists yet.
- **Analytics / aggregation / dashboards** — no balances-over-time, category
  rollups, or reporting endpoints.
- **Budgets** — no budget model, enforcement, or overrun alerts.
- **AI / Decision Engine** — no model calls or recommendations.
- **OCR** — not applicable to this phase.
- **Queue workers / background jobs** — no async workers; all writes are
  synchronous within the request transaction.
- **Investments / Loans / Tax** — the `investment` account type is accepted as
  a value but carries no special behavior.
- **Recurring transactions / forecasting** — no scheduling or projections.
- **Notifications** — none.
- **Soft-delete for accounts** — see decision above; not implemented.

## Verification notes
- The Alembic migration (`add_financial_domain`) is design-verified (SQL
  reviewed) but is **not** executed in CI here without a Postgres target. The
  schema shape is exercised end-to-end via `Base.metadata.create_all` in the
  test fixtures; CHECK constraints and `pgcrypto`/`gen_random_uuid()` defaults
  are installed by the real migration and gated behind `requires_postgres` when
  a live DB is provided.
