# CLAUDE.md — Project Instructions for Claude Code

## Project Identity
Name: RAG Eval Dashboard
Owner: Sam (Samadrita Bhattacharya)
Purpose: Portfolio project demonstrating production-grade RAG evaluation
         over Anthropic + Model Context Protocol documentation.
Target audience: AI engineering hiring managers (Emergent Labs specifically).
Stack: Next.js 14 (App Router) + FastAPI + ChromaDB + Ragas + Groq (free tier).

## What This Project Is (and Is NOT)
This project IS:
- An eval-first system: the RAG pipeline exists to be measured, not to ship as a product.
- A demonstration of reliability engineering practices: golden datasets, regression eval,
  hybrid retrieval with tunable configs, hallucination detection.
- A real deployable full-stack app with observable telemetry (Langfuse).

This project is NOT:
- A production chatbot.
- A general-purpose LLM interface.
- A place to add "cool features" that don't advance the eval story.

Every feature must answer: does this make the eval story stronger, or is it decoration?

## Current Phase
See GOALS.md for the full phase plan. Check which phase is active before
building anything — do not skip ahead.

## Non-Negotiables — Never Violate

### Free-tier only
- No paid APIs. Ever. Groq, Gemini free, HuggingFace local models, ChromaDB local,
  Langfuse free tier only.
- If a suggestion would cost money, refuse it and propose a free alternative.

### Secrets discipline
- Never hardcode API keys in code. All secrets from `.env` via `python-dotenv`
  (backend) or Next.js `process.env` (frontend, server-side only).
- Never log full API keys, even at debug level. Redact to last 4 chars.
- `.env` is in `.gitignore`. Never commit it. Never suggest committing it.

### Reproducibility
- Every ingestion, chunking, embedding, and eval run must be reproducible.
- Store the config used for every run in the run's output directory.
- Never suggest "just run it again" as a fix — if a bug isn't reproducible,
  we haven't understood it.

### Corpus is regenerable, not sacred
- Scraped markdown files (`corpus/`) are gitignored. They can be re-scraped.
- Chunks (`chunks/`) and vector store (`chroma_db/`) are gitignored. They can
  be re-generated. Never commit them.
- The scraper code, chunker code, and ingestion pipeline ARE the artifact.

### Golden dataset is sacred
- `golden_dataset/golden.jsonl` IS committed to Git.
- Every change to golden.jsonl needs a commit message explaining what was added
  and why. This is the answer key. Treat it like production code.

## Code Style — Backend (Python)

- Python 3.11+.
- Type hints on every public function. Use `from __future__ import annotations`.
- `pydantic` v2 for all data models (chunks, golden cases, eval results, API responses).
- `pathlib.Path` never string paths.
- `ruff` for linting, `black` for formatting. Config in `pyproject.toml`.
- Docstrings: Google style, on every module and public function.
- No print statements in library code. Use `structlog` for structured logging.
- FastAPI endpoints return Pydantic models directly, never dicts.
- Async by default for I/O (HTTP scraping, LLM calls). Sync only for pure CPU work
  (chunking, embedding computation locally).

## Code Style — Frontend (Next.js)

- Next.js 14 with App Router. Server Components by default; Client Components only
  when interactivity requires it.
- TypeScript strict mode. No `any`. Use `unknown` and narrow.
- Tailwind for styling. shadcn/ui for base components.
- Data fetching: React Server Components fetch from FastAPI directly.
  Client Components use SWR for polling/revalidation.
- No global state library for MVP. `useState` + URL params + SWR is enough.
  Consider Zustand only if state complexity actually demands it.
- Every component under 200 lines. Extract earlier than you think.

## Folder Conventions

Backend structure:
- `backend/app/` — FastAPI application
  - `api/` — route handlers, one file per resource
  - `core/` — config, logging, security
  - `models/` — Pydantic schemas
  - `services/` — business logic (never in route handlers)
  - `pipeline/` — RAG components (scrape, chunk, embed, retrieve, generate)
  - `eval/` — Ragas wiring, metric computation, golden dataset loader (added Phase 3)
- `backend/scripts/` — one-off CLI scripts (initial scrape, initial ingest, eval runs)
- `backend/tests/` — pytest tests, mirroring `app/` structure

Frontend structure:
- `frontend/app/` — Next.js routes
- `frontend/components/` — reusable UI components
- `frontend/lib/` — API client, types, utilities
- `frontend/hooks/` — custom React hooks

## Testing Rules

- Every backend service function has at least one happy-path test and one edge-case test.
- Route handlers have integration tests using `httpx.AsyncClient`.
- Eval metric computations have deterministic tests using fixed judge responses (mocked).
- Never test the LLM's output directly ("assert response == 'expected string'").
  Test the pipeline's *structure*: correct number of chunks retrieved, correct
  score aggregation, correct handling of empty results.
- Aim for 70% coverage on `services/` and `pipeline/`. Route handlers and models
  don't need coverage targets.
- Golden dataset validation: a pytest test loads golden.jsonl and validates schema
  on every CI run. If someone adds a malformed case, CI fails.

## Commit Discipline

- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.
- One logical change per commit.
- Commit messages explain WHY, not what. Diff shows what.
- Never commit commented-out code. Delete it. Git remembers.
- Never commit `TODO` comments without a linked issue.

## Branching

- `main` is always deployable.
- Feature branches: `feat/<short-description>` off main.
- No direct pushes to main after the initial scaffold.
- Every merge to main triggers eval CI (from Phase 3 onward). If the eval regresses
  more than 5% on any metric vs the last main commit, the merge blocks.

## Environment Variables — Required

Backend `.env` (grows across phases — see ARCHITECTURE.md for when each is introduced):
- `LOG_LEVEL` — default `INFO` (Phase 0)
- `GROQ_API_KEY` — from console.groq.com (Phase 2)
- `EMBEDDING_MODEL` — default `sentence-transformers/all-MiniLM-L6-v2` (Phase 1)
- `GENERATOR_MODEL` — default `llama3-70b-8192` (Phase 2)
- `JUDGE_MODEL` — default `llama3-70b-8192` (Phase 3)
- `CHROMA_PATH` — default `./chroma_db` (Phase 1)
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` — from cloud.langfuse.com (Phase 2)

Frontend `.env.local`:
- `NEXT_PUBLIC_API_URL` — default `http://localhost:8000` (Phase 0)
- `NEXT_PUBLIC_LANGFUSE_DASHBOARD_URL` — for linking to traces (Phase 4)

## When Claude Code Is Asked to Add a Feature

Before writing code:
1. Check if the feature aligns with GOALS.md for the current phase.
2. Check if a design decision belongs in ARCHITECTURE.md.
3. Propose the plan in prose first. Wait for approval before implementation.
4. Never scope-creep. If the user asks for X and you notice Y would be nice,
   mention Y in one sentence, do not build it.

Before touching existing code:
1. Read the file fully.
2. Identify the minimal change surface.
3. Preserve existing patterns even if you'd write it differently — consistency > taste.

Prohibited without explicit approval:
- Adding new dependencies.
- Changing folder structure.
- Introducing new environment variables.
- Adding auth/user accounts (out of scope for portfolio).
- Adding a database beyond ChromaDB (Postgres, Redis, etc.).
- Suggesting to "clean up" or "refactor" unrelated code.

## Reference Docs (Read These When Relevant)

- `ARCHITECTURE.md` — system design decisions
- `ENGINEERING_RULES.md` — detailed code standards
- `GOALS.md` — phase deliverables and definition of done
- `docs/RETRIEVAL_STRATEGY.md` — chunking, retrieval, reranking choices (written in Phase 2)
- `docs/GOLDEN_DATASET_SPEC.md` — golden dataset schema and category guidelines (written in Phase 3)
