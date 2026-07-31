# Goals — Phased Delivery Plan

Total estimated duration: 4-6 weeks part-time (10-15 hrs/week).
Every phase ends with a demoable state and a commit tag.

## Phase 0: Scaffold (Days 1-2)

Goal: repo exists, structure is right, running is possible.

Deliverables:
- Monorepo structure: `backend/`, `frontend/`, `docs/`.
- Backend: FastAPI app running, `/health` endpoint returns ok.
- Frontend: Next.js app running, blank page loads.
- CLAUDE.md, ARCHITECTURE.md, ENGINEERING_RULES.md, GOALS.md committed.
- `.gitignore` correct. `.env.example` in place. Real `.env` NOT committed.
- README.md stub.
- CI: GitHub Actions runs lint + type-check on every PR.

Done when: `docker-compose up` starts both services, `/health` works, PR CI passes.
Tag: `v0.1.0-scaffold`.

## Phase 1: Corpus Ingestion (Days 3-5)

Goal: docs are scraped, cleaned, chunked, embedded, queryable.

Deliverables:
- `scripts/scrape_anthropic.py` — polite scraper for the Anthropic docs site.
- `scripts/scrape_mcp.py` — fetches modelcontextprotocol.io via its llms.txt index.
- Both scripts idempotent (safe to re-run, skip already-scraped).
- `pipeline/chunk.py` — heading-aware markdown chunker.
- `pipeline/embed.py` — sentence-transformers wrapper.
- `pipeline/ingest.py` — CLI: scrape → chunk → embed → store in ChromaDB.
- Chunks include full metadata: source_url, section_path, content_type,
  chunk_index, chunk_length.
- Backend endpoint `POST /retrieval/preview` returns retrieved chunks for a query
  (no generation).

Done when: `python -m scripts.ingest` completes end-to-end and querying
returns sensible chunks for 5 test queries.
Tag: `v0.2.0-ingest`.

Non-goals for Phase 1:
- Generation. No LLM answer generation yet.
- Frontend for querying. CLI/API only.
- Reranking. That comes in Phase 3.

## Phase 2: RAG Pipeline + Basic API (Days 6-9)

Goal: full retrieve-generate pipeline works end-to-end.

Deliverables:
- `pipeline/retrievers/` with `semantic.py`, `keyword.py`, `hybrid.py`.
- `pipeline/rerank.py` (built but toggleable, off by default in Phase 2).
- `pipeline/generate.py` — Groq client wrapper with retries + Langfuse tracing.
- `prompts/qa_v1.yaml` — versioned QA prompt.
- Backend `POST /query` — takes question + config, returns answer + retrieved chunks
  + timing + cost.
- Groq rate limiter in place.
- Backend logs are structured JSON.

Done when: `/query` returns a grounded answer for 10 hand-picked questions from
the corpus, with retrieved chunks visible and Langfuse traces populating.
Tag: `v0.3.0-pipeline`.

## Phase 3: Golden Dataset + Eval Engine (Days 10-14)

Goal: the golden dataset exists and Ragas metrics compute.

Deliverables:
- `golden_dataset/golden.jsonl` — 60 cases across categories:
  - 20 simple factual
  - 15 multi-hop / multi-doc
  - 10 adversarial / out-of-scope (correct answer: "I don't know")
  - 10 numerical / exact-match (rate limits, token counts, prices)
  - 5 code-related (API usage examples)
- `docs/GOLDEN_DATASET_SPEC.md` — schema + category guidelines.
- `services/golden_dataset_service.py` — loader, validator.
- Validation test in CI — fails if golden.jsonl is malformed.
- `services/eval_runner.py` — orchestrates one full run.
- `pipeline/judge.py` — Ragas wired with Groq as judge (separate client).
- `POST /eval/run`, `GET /eval/runs`, `GET /eval/runs/{id}` endpoints.
- Eval runs persisted as JSON files.

Done when: an eval run completes, produces all four Ragas metrics per case,
aggregates cleanly, and results are queryable via API.
Tag: `v0.4.0-eval`.

Non-goals for Phase 3:
- Frontend visualization (Phase 4).
- Config comparison (Phase 5).

## Phase 4: Frontend Dashboard (Days 15-21)

Goal: recruiter can see results in a browser without touching code.

Deliverables:
- Route `/` — Overview: latest run's aggregate metrics as cards, sparklines of
  metrics over last N runs.
- Route `/runs` — Table of all runs, sortable, filterable.
- Route `/runs/[id]` — Single run detail:
  - Aggregate scores at top
  - Per-case table with scores
  - Failure gallery: 10 lowest-scoring cases with question, expected answer,
    actual answer, retrieved chunks, per-metric breakdown
  - Link to Langfuse trace
- Route `/golden` — Read-only view of golden dataset with category filters.
- SSE progress display when a run is in progress.
- Loading states, error states, empty states throughout.
- Tailwind + shadcn/ui consistent styling.

Done when: navigating the site produces a coherent, professional experience
without any dead ends or console errors.
Tag: `v0.5.0-dashboard`.

## Phase 5: Comparison + Advanced Retrieval (Days 22-28)

Goal: the portfolio-defining features — the ones that make a recruiter stop scrolling.

Deliverables:
- Config comparison view (`/compare`):
  - Select 2-4 past runs, see side-by-side aggregate metrics with deltas.
  - Grid view: chunk_size × top_k → faithfulness heatmap.
- Reranker toggle activated. Two comparison runs baked in:
  "hybrid" vs "hybrid + rerank".
- Cost-per-quality-point chart on the compare view.
- Failure category tagging: each low-scoring case auto-classified by the judge into
  a failure category (retrieval miss, generation ignored context, hallucination,
  refusal-should-have-been-answer). Shown in dashboard.

Done when: a viewer can compare two configs, see the delta, and immediately
understand which config is better and why.
Tag: `v0.6.0-compare`.

## Phase 6: Polish + Deploy + Write-Up (Days 29-35)

Goal: it's live, it's documented, it's shareable.

Deliverables:
- Deploy backend to Railway or Fly.io.
- Deploy frontend to Vercel.
- Update `.env` docs with production values.
- README.md rewritten with:
  - What it is (one paragraph)
  - Live demo link
  - Key results with real numbers ("faithfulness 0.72 → 0.89 across configs")
  - Architecture diagram
  - Local development setup
  - Screenshots of dashboard, failure gallery, comparison view
- Loom video walkthrough (2-3 minutes).
- One dev.to or LinkedIn writeup on the retrieval-strategy comparison story.
- Repo tags for each phase for the git-history story.

Done when: URL works, README stands alone, at least one write-up is public.
Tag: `v1.0.0`.

## Explicit Non-Goals (Entire Project)

- Real-time chat interface.
- User accounts, auth, roles.
- Multi-tenant isolation.
- Editing golden dataset via UI. Golden edits happen in Git only.
- Multi-model comparison (Groq vs Gemini vs Claude) — noted as v2 candidate.
- Fine-tuning any model.
- Any paid infrastructure.

## Definition of "Portfolio Ready"

The project is portfolio-ready when a hiring manager can:
- Open the README, understand what it is in 30 seconds.
- Click a live demo link and see it working.
- See real evaluation numbers (not "placeholder").
- Read a coherent story of engineering decisions (commit history should reflect
  this — avoid "wip fix things" as commit messages).
- See the failure gallery and understand why some cases fail.

If any of the above fails, the project is not done, no matter what version tag says.
