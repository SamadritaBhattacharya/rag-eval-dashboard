# Architecture — RAG Eval Dashboard

## High-Level Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER (Recruiter)                          │
└────────────────────────────┬────────────────────────────────────┘
                              │ HTTPS
┌─────────────────────────────▼────────────────────────────────────┐
│              Next.js Frontend (Vercel, free tier)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  Overview    │  │  Failure     │  │  Config Comparison   │   │
│  │  Dashboard   │  │  Gallery     │  │  (chunk_size × k)    │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│         ▲ SWR polling             ▲ React Server Components      │
└─────────┼─────────────────────────┼──────────────────────────────┘
          │ REST                    │ SSE (eval progress)
┌─────────▼─────────────────────────▼──────────────────────────────┐
│           FastAPI Backend (Railway or Fly.io, free tier)         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  API Layer                                                  │  │
│  │  /health  /eval/run  /eval/runs  /eval/runs/{id}            │  │
│  │  /golden  /query  /retrieval/preview                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Services Layer                                             │  │
│  │  - EvalRunner (orchestrates one eval run end-to-end)        │  │
│  │  - GoldenDatasetService (load, validate, filter)            │  │
│  │  - RAGPipeline (retrieve + generate)                        │  │
│  │  - MetricComputer (Ragas wrapper)                           │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Pipeline Components                                        │  │
│  │  Retrieval:  Chroma + BM25 + RRF fusion + optional reranker │  │
│  │  Generation: Groq Llama 3 (via httpx)                       │  │
│  │  Judge:      Groq Llama 3 (separate client, different rate  │  │
│  │              limit budget)                                   │  │
│  └────────────────────────────────────────────────────────────┘  │
└──┬────────────────┬────────────────┬────────────────┬───────────┘
   │                │                │                │
   ▼                ▼                ▼                ▼
┌────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐
│Chroma  │    │  BM25     │    │  Groq    │    │ Langfuse │
│(local  │    │  index    │    │  API     │    │  Cloud   │
│ disk)  │    │  (rank_bm25)│  │  (free)  │    │  (free)  │
└────────┘    └───────────┘    └──────────┘    └──────────┘
```

## Component Responsibilities

### Frontend (Next.js)
Purpose: display eval results, let user trigger runs, compare configurations.

Pages:
- `/` — Overview dashboard: latest run's metrics, sparklines over time.
- `/runs` — List all eval runs with filters (config, date, status).
- `/runs/[id]` — Single run detail: per-case scores, failure gallery.
- `/compare` — Side-by-side config comparison (chunk_size, top_k, retriever mode).
- `/golden` — Read-only view of the golden dataset.
- `/query` — Ad-hoc query playground (not eval; interactive testing).

Data fetching:
- Server Components fetch initial data from FastAPI at render time.
- Client Components use SWR for polling in-progress eval runs.
- Long-running eval runs stream progress via SSE endpoint.

### Backend (FastAPI)

API surface (thin — most logic in services):
- `GET /health` — liveness probe.
- `POST /eval/run` — trigger a new eval run with a config. Returns run_id.
- `GET /eval/runs?limit&offset` — paginated list of past runs.
- `GET /eval/runs/{id}` — single run's aggregated metrics + per-case details.
- `GET /eval/runs/{id}/stream` — SSE stream of progress during a run.
- `GET /golden` — list all golden cases.
- `GET /golden/{id}` — single golden case.
- `POST /query` — one-off query through the pipeline (for the playground).
- `POST /retrieval/preview` — return retrieved chunks for a query without generating.
                              Useful for debugging retrieval quality.

Services (business logic):
- `EvalRunner` — takes a config, iterates over golden dataset, runs pipeline,
  scores with Ragas, persists results, updates Langfuse.
- `RAGPipeline` — encapsulates retrieval + generation. Config-driven.
- `GoldenDatasetService` — loads and validates golden.jsonl.
- `MetricComputer` — thin wrapper over Ragas with our judge LLM configured.

### Pipeline Components

Retrieval (configurable via EvalConfig):
- `SemanticRetriever` — ChromaDB similarity search.
- `KeywordRetriever` — BM25 over the same chunks (rank_bm25 library, in-memory).
- `HybridRetriever` — runs both, merges with Reciprocal Rank Fusion.
- `Reranker` — optional cross-encoder rerank step (cross-encoder/ms-marco-MiniLM,
  local, CPU). Toggle on/off in config.

Generation:
- `GroqGenerator` — sends prompt + retrieved chunks to Groq, returns answer.
- Prompt template stored in `prompts/qa_v1.yaml`, versioned.

Judge:
- `RagasJudge` — same Groq API, different client instance to isolate rate limits.
  Used only by MetricComputer, never by the main pipeline.

### Storage

ChromaDB:
- Local persistent client. Storage dir: `./chroma_db/`.
- One collection per embedding model. Collection name encodes embedding model + chunk size
  (e.g., `minilm_512_50`).
- Each chunk stores metadata: source_url, section_path, content_type, chunk_index.

BM25 index:
- Built in-memory at startup from chunk metadata JSON file.
- Rebuilt if `chunks.jsonl` mtime is newer than last rebuild timestamp.

Eval runs:
- Stored as JSON files in `eval_runs/{run_id}.json`.
- Each file contains: config used, per-case scores, aggregate metrics, timing, cost estimate.
- Considered committing eval runs; decided against — they're large and regenerable.
- Instead, commit an `EVAL_HISTORY.md` with a table of run_id → key metrics for reference.

Golden dataset:
- `golden_dataset/golden.jsonl` — one JSON object per line.
- Committed to Git. Every change reviewed.
- Schema in `docs/GOLDEN_DATASET_SPEC.md` (written in Phase 3).

## Data Flow — One Eval Run

1. User clicks "Run Eval" in frontend with a selected config.
2. Frontend POSTs to `/eval/run` with `EvalConfig`.
3. FastAPI creates a run_id, spawns a background task, returns 202 with run_id.
4. Background task:
   a. Load golden.jsonl.
   b. For each golden case (~60 cases):
      i.   Retrieve chunks per config.
      ii.  Generate answer via Groq.
      iii. Score with Ragas (faithfulness, answer_relevancy, context_precision,
           context_recall).
      iv.  Log trace to Langfuse with all metadata.
      v.   Append per-case result to run's JSON file.
      vi.  Emit SSE progress event.
   c. Compute aggregate metrics.
   d. Write final run JSON.
5. Frontend polls or subscribes to SSE, updates UI as progress arrives.

Estimated wall-clock per run: 3-8 minutes for 60 cases at Groq's rate limits.
Estimated Groq calls per run: 60 (generation) + 60 * 4 (judge, one per metric) = 300 calls.
Groq free tier limit: generous enough for this workload (verify current limit on signup —
Groq's published limits change over time).

## Deployment Topology

Frontend: Vercel (free hobby tier). Auto-deploys on push to main.
Backend: Railway or Fly.io (both have free tiers). Docker-based.
Vector store: local disk on backend instance. Persistent volume required.
Golden dataset: shipped in the backend Docker image.

CORS: FastAPI CORS middleware allows the Vercel URL only in production.
API secrets: environment variables set in Railway/Fly dashboard.

## Key Design Decisions with Rationale

**DECISION:** ChromaDB local, not managed vector DB (Pinecone, Weaviate Cloud).
**RATIONALE:** Free forever, no rate limits, no vendor lock-in. Adequate for
~5000-chunk corpus. Trade-off: doesn't scale past ~100K chunks — acceptable
for this project's scope.

**DECISION:** Groq for both generation AND judge.
**RATIONALE:** Only free API that supports Llama 3 70B at usable speed. Same model
family for both roles is fine as long as judge uses temperature=0 and a different
prompt. Trade-off: more rigorous to use a different model as judge (e.g. Gemini
Flash) — noted as a Phase 4+ improvement.

**DECISION:** Hybrid retrieval (semantic + BM25 + RRF) as the default.
**RATIONALE:** Anthropic/MCP docs mix conceptual content with exact-match content
(parameter names, error codes). Pure semantic misses exact matches; pure BM25
misses paraphrases. RRF is parameter-free and industry-default.

**DECISION:** SSE for eval progress, not WebSockets.
**RATIONALE:** Server-to-client only, simpler protocol, plays well with FastAPI's
StreamingResponse. WebSockets would be overkill for one-way progress updates.

**DECISION:** Eval runs stored as JSON on disk, not in a database.
**RATIONALE:** Zero-infra, human-readable, git-friendly if we ever want to commit
specific runs. Trade-off: no SQL queries over runs — but we only ever query
"latest N runs" and "specific run by ID" so this is fine.

**DECISION:** Golden dataset in JSONL, committed to Git.
**RATIONALE:** JSONL is line-diffable (great for PR reviews), preserves order,
allows partial reads. Committed because it's the project's crown jewel.

**DECISION:** Reranker as optional, toggled by config, not always-on.
**RATIONALE:** Comparing "with reranker" vs "without reranker" is one of the
best portfolio talking points ("adding reranking improved faithfulness by
X points"). Building it as a toggle enables the comparison story.

**DECISION:** No user authentication.
**RATIONALE:** Out of scope for portfolio. Adds complexity, doesn't advance the
eval story. If a recruiter shares the URL, they see the dashboard read-only.
Ad-hoc query playground rate-limited by IP.

## Observability

Langfuse integration:
- Every LLM call (generator + judge) traced with cost, latency, tokens.
- Every eval run is one trace with per-case spans nested.
- Failed traces tagged for filtering.
- Dashboard shows a link "Open in Langfuse" on every run.

Backend logging:
- structlog for structured JSON logs.
- Log level configurable via env var.
- Never log full LLM outputs (large, may contain PII if corpus expands).
  Log first 200 chars + hash.

Frontend:
- Vercel Analytics free tier.
- No third-party tracking.

## Scaling Boundaries (Explicitly Chosen)

This system is designed for:
- Corpus ≤ 10K chunks (~5 MB text). Anthropic + MCP fits comfortably.
- Golden dataset ≤ 500 cases.
- Concurrent users: 1-5 (portfolio traffic).
- Eval runs: sequential, one at a time.

Explicitly NOT designed for:
- Multi-tenant use.
- High-throughput production RAG serving.
- Real-time streaming responses to end users (the system doesn't run continuously —
  only on eval trigger or ad-hoc query).

If the scope grows, this document gets a new version with the new decisions —
don't silently drift from what's written here.
