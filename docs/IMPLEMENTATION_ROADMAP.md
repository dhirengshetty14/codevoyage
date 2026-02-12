# CodeVoyage Implementation Roadmap

## Goal

Ship a portfolio-grade platform that is demo-ready, technically defensible in SDE interviews, and scalable enough to discuss realistic production tradeoffs.

## Current Baseline (as of 2026-02-12)

- Dockerized stack exists: FastAPI, Celery, Redis, PostgreSQL, Next.js.
- Real-time progress now flows across processes via Redis Pub/Sub -> FastAPI Socket.IO.
- Frontend has both showcase visualizations and a real repository analysis trigger.
- Core analysis pipeline exists but still needs stronger data durability, query optimization, and test coverage.

## Phase 1: Reliability First (Week 1)

1. Stabilize local boot flow and secrets handling.
2. Move all table creation responsibility to Alembic migrations only.
3. Add retry-safe analysis orchestration with explicit stage transitions.
4. Add deterministic failure states and resume behavior.

Deliverables:
- `docker compose up -d --build` works from a fresh clone.
- Failed analysis runs remain inspectable and re-runnable.
- Stage status model documented and enforced.

## Phase 2: Data Model and Scale Path (Week 2)

1. Persist commit/file/contributor entities in batches (not just aggregate JSON).
2. Add indexes for hottest read paths:
   - repository timeline
   - contributor graph queries
   - file hotspot lookups
3. Add ingestion guardrails for very large repos:
   - commit cap by config
   - chunked processing
   - memory-safe iteration

Deliverables:
- Analysis of large repos completes without OOM.
- Query latency for dashboard endpoints is predictable.
- Schema and index strategy can be explained in interviews.

## Phase 3: Visualization From Real Data (Week 3)

1. Replace mock 3D tree/timeline/network datasets with API-backed data adapters.
2. Add timeline snapshot API for git-history scrubbing.
3. Add complexity heatmap overlay toggles and legends.
4. Add language evolution area-chart endpoint and rendering.

Deliverables:
- End-to-end demo uses real repository data.
- Visualizations remain responsive while analysis is running.

## Phase 4: AI Insight Engine (Week 4)

1. Define strict JSON schemas for each insight family.
2. Add prompt templates with token budgeting and truncation strategy.
3. Implement model fallback and malformed-response recovery.
4. Persist AI metadata for replay, cost analysis, and auditability.

Deliverables:
- AI insights are reproducible and parse-safe.
- Clear cost/performance controls are documented.

## Phase 5: Observability and Production Story (Week 5)

1. Add correlation IDs across API -> Celery -> Redis -> DB logs.
2. Expose metrics: queue depth, stage durations, cache hit rate, error rate.
3. Add dashboards/alerts for degraded dependencies and stuck jobs.
4. Add load-test scenario + baseline report.

Deliverables:
- Failure diagnosis is fast and concrete.
- You can discuss SLOs, bottlenecks, and remediation with evidence.

## Phase 6: Interview and LinkedIn Packaging (Week 6)

1. Record architecture walkthrough with one real repository analysis.
2. Publish design tradeoff doc:
   - Redis vs Kafka
   - Celery scaling model
   - Postgres indexing/partitioning plan
3. Add one-click demo scripts and sample repos.
4. Prepare short “systems design deep dive” README section.

Deliverables:
- Recruiter can run demo in under 10 minutes.
- Interviewer can drill into distributed systems decisions with confidence.

## Execution Checklist

- Daily: keep stack green (`api`, `redis`, `postgres`, `worker`, `frontend` healthy).
- Per feature: add one integration test and one failure-path test.
- Weekly: capture one benchmark and one architecture note.
