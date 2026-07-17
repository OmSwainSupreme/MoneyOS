# MoneyOS — Development Workflow

> **Audience:** All contributors (human + AI agents)
> **Scope:** How work flows from idea → branch → PR → review → test → release
> **Context:** MoneyOS is built primarily by **AI coding agents** under human oversight. This document defines the guardrails that make multi-agent development safe, reviewable, and reproducible.

---

## 1. Guiding Principles

1. **Every change is traceable.** One issue → one branch → one PR → one reviewer sign-off.
2. **AI agents are contributors, not authorities.** All agent output passes the same gates as human output.
3. **Small, atomic changes.** Prefer many small PRs over one large PR — critical when agents author code, because small diffs are reviewable.
4. **Green main, always.** `main` is always deployable. Nothing merges red.
5. **Determinism over cleverness.** Reproducible builds, pinned dependencies, documented prompts.

---

## 2. Branch Strategy

A trimmed **GitHub Flow + release branch** model — light enough for a hackathon, structured enough to scale.

| Branch | Purpose | Protected | Merges from |
|--------|---------|-----------|-------------|
| `main` | Always-deployable production code | ✅ Yes | `release/*`, `hotfix/*` |
| `develop` | Integration branch for active work | ✅ Yes | `feature/*`, `fix/*`, `chore/*` |
| `feature/<scope>-<short-desc>` | New functionality | No | branched from `develop` |
| `fix/<scope>-<short-desc>` | Non-urgent bug fixes | No | branched from `develop` |
| `chore/<scope>-<short-desc>` | Tooling, docs, deps, CI | No | branched from `develop` |
| `release/<version>` | Release stabilization | ✅ Yes | branched from `develop` |
| `hotfix/<version>` | Urgent production fixes | ✅ Yes | branched from `main` |

**Naming rules**
- Lowercase, kebab-case, scoped: `feature/backend-health-endpoint`, `fix/frontend-auth-redirect`.
- Include the issue number when one exists: `feature/42-ai-context-scrubber`.
- **AI-authored branches** carry an agent tag suffix so provenance is visible in `git log`:
  `feature/42-ai-context-scrubber--claude`, `fix/88-null-budget--qwen`.

**Branch protection (main & develop)**
- Require PR before merge (no direct pushes).
- Require passing CI (`lint`, `test`, `build`).
- Require ≥1 approving review (human for `main`, human-or-designated-reviewer-agent for `develop`).
- Require linear history (squash merge).
- No force-push, no deletion.

---

## 3. Git Workflow

**Commit convention: Conventional Commits.** Machine-parseable, which lets agents and CI generate changelogs automatically.

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **Types:** `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `ci`, `build`.
- **Scope:** `frontend`, `backend`, `shared`, `infra`, `ai`, `db`.
- **Subject:** imperative, ≤72 chars ("add health endpoint", not "added").

**Agent attribution footer (required for AI commits):**
```
feat(backend): add /health endpoint

Adds container liveness probe for docker-compose.

Co-Authored-By: Claude Code <agent@moneyos.dev>
Agent-Model: claude-sonnet
Prompt-Ref: docs/dev/prompts/health-endpoint.md
```

**Rules**
- Rebase feature branches on `develop` before opening a PR (keep history linear).
- One logical change per commit; squash noise before review.
- Never commit secrets, `.env`, `venv/`, or `node_modules/` (enforced by `.gitignore` + CI secret scan).

---

## 4. Feature Workflow

```
Issue ──► Plan ──► Branch ──► Implement ──► Self-check ──► PR
```

1. **Issue first.** Every feature starts as a GitHub issue with acceptance criteria and a chosen owner agent.
2. **Plan before code.** The owning agent writes a short plan (files to touch, approach, risks) as an issue comment. Human approves the plan. This is the single most important gate for AI work — cheaper to correct a plan than a diff.
3. **Branch** from latest `develop`.
4. **Implement** in small commits. Agent stays within the scope declared in the plan; scope creep = new issue.
5. **Self-check** (agent runs locally before PR): `lint`, `test`, `build`, and a self-review pass ("does this match the plan and acceptance criteria?").
6. **Open PR** into `develop` using the PR template.

**Definition of Done**
- Acceptance criteria met · tests added/updated · CI green · docs updated · no TODOs left unexplained.

---

## 5. Pull Request Workflow

- **Target:** feature/fix/chore → `develop`; `release/*` & `hotfix/*` → `main`.
- **Size budget:** aim for **< 400 changed lines**. Larger PRs must be split. (AI can generate huge diffs fast; the review bottleneck is human — keep PRs digestible.)
- **PR description must state:**
  - Linked issue.
  - What changed and why.
  - Which agent authored it + model + prompt reference.
  - Test evidence (CI link / local output).
  - Risk & rollback notes.
- **Labels:** apply `type:*`, `component:*`, `priority:*`, and `ai-authored`.
- **Draft PRs** for in-progress agent work so reviewers can watch direction early.
- **Merge strategy:** squash merge only → one clean commit per PR on `develop`/`main`.

---

## 6. Review Workflow

A **two-tier review** designed for AI-authored code.

### Tier 1 — Automated / Agent review (fast, always)
- CI gates: lint (`ruff`, `eslint`), type checks, tests, build, secret scan.
- A **reviewer agent** (different model from the author — never self-review) checks:
  - Correctness vs. acceptance criteria.
  - Security boundaries (PII scrubbing, no secrets, input validation).
  - Adherence to the approved plan and coding standards.
- Reviewer agent posts findings as PR comments with severity (`blocker` / `major` / `nit`).

### Tier 2 — Human review (required for merge)
- Human confirms the automated findings, resolves blockers, and gives final approval.
- **`main` always requires a human approval.** No exceptions.
- Reviewer checks *intent*, not just syntax: "Is this the right thing to build?"

**Cardinal rule: an agent never approves its own code.** Author agent ≠ reviewer agent.

---

## 7. Testing Workflow

**Test pyramid**
- **Unit** — `pytest` (backend), `vitest`/`jest` (frontend). Fast, run on every commit.
- **Integration** — API + DB (Postgres service), contract tests against `packages/shared` schemas.
- **E2E** — critical user journeys (smoke: health check, one decision flow). Run on PR to `main`.

**Gates**
| Stage | Runs | Blocks merge to |
|-------|------|-----------------|
| Pre-commit (local, agent) | lint + unit | — |
| PR CI | lint + unit + integration + build | `develop` |
| Release CI | full suite + E2E + security scan | `main` |

**Rules for AI-authored tests**
- Agent that writes the feature also writes the tests, **but** the reviewer agent must confirm tests actually assert behavior (guard against tautological / vacuous tests — a common AI failure mode).
- Coverage is a signal, not a target; prioritize meaningful assertions on financial logic and PII handling.

---

## 8. Release Workflow

**Versioning:** Semantic Versioning `MAJOR.MINOR.PATCH`. Changelog auto-generated from Conventional Commits.

```
develop ──► release/x.y.0 ──► stabilize ──► tag vX.Y.0 ──► merge to main ──► deploy
                                                     └──► back-merge to develop
```

1. Cut `release/x.y.0` from `develop` when scope is frozen.
2. Only `fix`/`chore` commits allowed on the release branch (no new features).
3. Run full suite + E2E + security scan.
4. Tag `vX.Y.0`, merge to `main`, deploy, then **back-merge `main` → `develop`** so both stay in sync.

**Hotfixes:** branch `hotfix/x.y.z` from `main`, fix, tag, merge to `main` **and** `develop`.

**Release checklist:** CI green · changelog updated · migrations reviewed · `.env.example` current · rollback plan documented.

---

## 9. Multi-Agent Collaboration Model

MoneyOS uses several AI agents. Efficiency comes from **role specialization + non-overlapping ownership + cross-model review**. Assign by strength, never let one model both author and approve the same change.

### Role assignment

| Agent | Primary Role | Why | Typical outputs |
|-------|-------------|-----|-----------------|
| **Claude Code** | **Lead implementer & orchestrator** | Strong at repo-wide, multi-file changes, tool use, and following structured plans directly in the codebase. | Feature branches, refactors, running tests, wiring services. |
| **Gemini** | **Research & data/AI reasoning** | Strong long-context reasoning and analysis; good for schema design and evaluating AI-pipeline approaches. | Design docs, data-model proposals, LLM-orchestration strategy, alternative-approach analysis. |
| **Qwen** | **Backend & focused code generation** | Efficient at well-scoped Python/API tasks and bulk mechanical edits. | Endpoint scaffolds, migrations, unit tests, utility modules. |
| **Antigravity** | **Agentic execution & environment/automation** | Suited to autonomous multi-step tasks: running builds, wiring CI, environment setup, integration glue. | CI/CD tasks, infra scripts, end-to-end task automation, integration testing. |
| **ChatGPT** | **Reviewer, spec-writer & documentation** | Strong at critique, explanation, and turning requirements into crisp specs; ideal as the independent reviewer voice. | Issue specs, acceptance criteria, PR reviews, docs, changelog polish. |

### Collaboration rules

1. **One owner per issue.** The assigned agent owns the branch end-to-end. No two agents push to the same branch simultaneously.
2. **Cross-model review is mandatory.** The reviewer agent must be a *different* model than the author (e.g., Claude implements → ChatGPT/Gemini reviews). This catches model-specific blind spots.
3. **Plan → hand-off contract.** Gemini/ChatGPT produce the spec + plan; Claude/Qwen/Antigravity implement against it. The plan file is the shared source of truth (`docs/dev/prompts/<feature>.md`).
4. **Provenance is recorded.** Every commit/PR records `Agent-Model` and `Prompt-Ref` so any change can be traced to who/what produced it.
5. **Humans hold the merge key.** Agents can implement, test, and review; a human gives final approval to `main` and owns releases.

### Typical multi-agent feature loop

```
ChatGPT     → writes issue spec + acceptance criteria
Gemini      → proposes design / data model / AI approach  (human approves plan)
Claude Code → implements feature on feature/*--claude branch
Qwen        → generates/extends unit + integration tests
Antigravity → runs CI, integration & E2E, reports results
ChatGPT     → independent PR review (blocker/major/nit)
Human       → resolves blockers, approves, merges (squash)
```

### Anti-patterns to avoid
- ❌ Same model authoring **and** approving a change.
- ❌ Two agents editing one branch concurrently (merge chaos, lost context).
- ❌ Merging agent output without the approved plan on record.
- ❌ Oversized agent-generated PRs that outrun human review capacity.
- ❌ Trusting agent-written tests without confirming they assert real behavior.

---

## 10. Quick Reference

```
Issue (ChatGPT) → Plan (Gemini) → human approves plan
  → Branch from develop  (feature/<n>-<desc>--<agent>)
  → Implement (Claude/Qwen)  → tests (Qwen)  → self-check
  → PR into develop  (template + labels + provenance)
  → Tier1: CI + reviewer agent   → Tier2: human approval
  → Squash merge to develop
  → release/x.y.0 → full suite → tag → main → deploy → back-merge
```
