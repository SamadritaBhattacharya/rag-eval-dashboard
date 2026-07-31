# Engineering Rules

## Cardinal Rules (Never Break These)

1. Free tier only. No suggestion, no experiment, no exception.
2. Secrets never in Git, never in code, never in logs.
3. Golden dataset changes require a commit message explaining WHY.
4. `main` is always deployable. If a commit breaks main, revert first, fix second.
5. No feature without a phase in GOALS.md that calls for it.

## Definition of Done — For Every Feature

A feature is DONE when:
- Code is written and formatted (ruff + black backend, prettier frontend).
- Tests exist and pass locally.
- Types check clean (mypy backend, tsc frontend).
- The feature is used somewhere (dead code fails review).
- Docs updated if the change is user-facing or architectural.
- Commits are clean (squashed if messy, each commit tells a story).
- Manual smoke test performed and described in the PR.

## Backend Standards

### Structure
- FastAPI route handlers are thin. They validate input, call a service, return a response.
- All business logic in `services/`. Services are pure Python classes, testable
  without spinning up FastAPI.
- Pipeline components (retrieval, generation, judging) are in `pipeline/`,
  fully decoupled from FastAPI.

### Errors
- Custom exception classes in `core/errors.py`: `RetrievalError`, `GenerationError`,
  `JudgeError`, `GoldenDatasetError`, `ConfigError`.
- Route handlers translate exceptions to HTTP responses in a single
  exception handler middleware.
- Never catch bare `Exception`. Catch specific classes. Let unexpected errors bubble up
  to be logged and surface as 500.

### Configuration
- All config via a Pydantic Settings class, loaded from env at startup.
- No `os.getenv` scattered through code.
- Config class validated on startup — missing required vars fail fast.

### Logging
- structlog with JSON output.
- Every log line has: level, timestamp, event, and context fields.
- Trace IDs propagate through the eval run so a single run's logs are filterable.

### LLM Calls
- All Groq calls go through a single `GroqClient` wrapper.
- Wrapper handles: retry with backoff, rate-limit awareness, cost estimation,
  Langfuse tracing, error normalization.
- No direct `groq.Groq(...)` calls anywhere else in the codebase.

### Rate Limits
- Verify Groq's current published free-tier limits at signup (they change over time).
- The `GroqClient` wrapper enforces a client-side rate limiter (aiolimiter) at 80%
  of the published limit to leave headroom.
- Eval runs that would exceed the daily quota are refused at start with a
  clear message.

## Frontend Standards

### Components
- Server Components for anything that doesn't need interaction.
- Client Components ('use client') only when necessary: state, event handlers,
  browser APIs.
- Every Client Component under 200 lines. Break up earlier.

### Styling
- Tailwind utility classes directly in JSX. No `@apply` in CSS files (Tailwind's
  own recommendation).
- Design tokens via Tailwind config extend, not hardcoded hex values.
- shadcn/ui for primitives (Button, Card, Table, Dialog). Copy-paste the source
  into `components/ui/` per shadcn convention.

### Data Fetching
- Server Components use `fetch()` with Next.js caching directives.
- Client Components use SWR with a shared `swrConfig` (dedup interval, revalidate
  on focus).
- All API responses typed in `lib/api-types.ts`. Never `any`.

### Charts
- Recharts for standard charts (bar, line, area).
- One chart, one component. No god-charts with 10 responsibilities.

## Testing

### Backend
- pytest with pytest-asyncio.
- Fixtures in `tests/conftest.py`. Shared: test client, mock Groq client,
  temp ChromaDB.
- Unit tests: service methods, pipeline components in isolation.
- Integration tests: full API route → service → mocked pipeline.
- Golden dataset validation: one test loads and validates every row.
- Snapshot tests for chunking: given a known corpus, chunks must be stable.
  Snapshot updates require explicit review.

### Frontend
- Vitest + React Testing Library.
- Test the interactive behavior, not the markup.
- No snapshot tests for JSX — brittle, low value.

### CI
- GitHub Actions.
- On PR: lint, type-check, unit tests, build.
- On merge to main (Phase 3 onward): full eval run against golden dataset.
  Regression > 5% blocks.

## Git Discipline

### Branches
- `main` — always deployable.
- `feat/<slug>` — one feature per branch.
- `fix/<slug>` — bug fixes.
- `chore/<slug>` — non-functional (deps, config, docs).

### Commits
- Conventional format: `<type>(<scope>): <subject>`.
- Scopes: `backend`, `frontend`, `pipeline`, `eval`, `golden`, `infra`, `docs`.
- Subject: imperative mood, no period. "add hybrid retriever" not "added hybrid retriever."
- Body (if needed): explain WHY.
- Footer (if needed): "Closes #12" for linked issues.

### PR Rules
- One PR = one logical change.
- Description explains: what, why, how to verify, screenshots for UI.
- Self-review the diff before requesting review.
- Never merge your own PR without another set of eyes — except for docs and
  chore commits.

## Documentation

- README.md — user-facing: what the project is, how to run it, live demo link,
  key results with numbers.
- CLAUDE.md — for Claude Code sessions.
- ARCHITECTURE.md — system design.
- ENGINEERING_RULES.md — this doc.
- GOALS.md — phase deliverables.
- Any non-obvious code deserves a docstring. "Why" > "what."

## Naming

- Files: `snake_case.py`, `kebab-case.tsx`.
- Python: `snake_case` for functions/vars, `PascalCase` for classes, `SCREAMING_SNAKE`
  for module-level constants.
- TypeScript: `camelCase` for functions/vars, `PascalCase` for types and components.
- Config keys: `snake_case` in YAML, `SCREAMING_SNAKE` in env vars.

## What NOT to Add

- Auth / user accounts — not in scope.
- Database beyond ChromaDB — not in scope.
- Real-time chat UI — not in scope. This is an eval dashboard, not a product.
- Fine-tuning, RLHF, custom model training — not in scope.
- Kubernetes, Terraform, complex infra — deploy to Vercel + Railway/Fly free tiers.
- Multiple languages/i18n — English only.
- Dark mode — nice-to-have but only if capacity allows late in the plan.
