# services/

Business logic layer. Orchestrates use-cases across repositories, AI, and external systems.

- `ai/` — AI/LLM integration (see `ai/README.md`).
- `financial/` — Financial decision logic: affordability, loan analysis, overspending, health scoring.

Services must be framework-agnostic (no FastAPI imports) so they stay unit-testable.
