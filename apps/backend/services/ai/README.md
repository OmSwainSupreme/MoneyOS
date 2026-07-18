# services/ai/

Isolated AI/LLM orchestration layer for MoneyOS.

This folder is a **scaffold for future AI integrations** — no provider or business logic is implemented yet. Each subfolder is reserved for a specific concern:

- `providers/` — Abstractions over LLM vendors (e.g. OpenAI, Anthropic, Gemini). Define a common interface so providers are swappable.
- `prompts/` — Versioned prompt templates and prompt-management artifacts.
- `memory/` — Conversation/history and retrieval memory stores.
- `agents/` — Autonomous or semi-autonomous agent definitions composing tools + prompts + memory.
- `tools/` — Callable tools exposed to agents (e.g. calculators, data fetchers).

**Security boundary:** all user/financial data passed to third-party LLMs MUST be scrubbed of PII first (see `docs/security/`). No secrets or raw credentials are ever sent to external APIs.
