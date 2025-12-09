# Stage 1 — Clean Code & Architecture

## Why this matters for you

Ship code today that you’re not embarrassed by tomorrow. Clean Code + Clean Architecture turns spaghetti into systems you can actually extend without fear.

Recruiters and senior engineers instantly spot this—your PRs read like a professional’s, not a student’s. You’ll feel the difference the first time you add a feature in 15 minutes that used to take you all afternoon.

## Career-proof wins you’ll take away

* **Portfolio signal:** “80%+ branch coverage, type-safe modules, ADR-driven design.”
* **Interview weapon:** Walk through a kata refactor and explain your tradeoffs like a pro.
* **Daily payoff:** Fewer bugs, faster reviews, and teammates who want you on their project.

## Focus

* **Code craft:** naming, small functions, cohesion/coupling, docstrings & type hints.
* **Architecture:** module boundaries (api/domain/infra), dependency injection seams.
* **Tooling:** ruff, mypy, pytest, pre-commit.

## Reading & practice (mandatory)

* **Clean Code** — focus on Chapters 1–7 (Meaningful Names, Functions, Formatting, Objects & Data Structures, Error Handling).
* **Clean Architecture** — Parts I–III (Design & Architecture principles; Component Principles).
* Apply with 2–3 code katas (e.g., Tennis, Bowling, or Gilded Rose) showing refactors.

## Outcomes

* Small, testable modules with clear boundaries and types.
* Architecture rationale captured in an ADR.
* You can demonstrate improvements from a “dirty” first commit to a clean final commit.

## Deliverables

* Starter repo with ruff, mypy, pytest, pre-commit.
* ≥ 80% branch coverage.
* ADR-001 Project Structure & Principles.
* CONTRIBUTING.md & RUNBOOK.md (local dev flow).
* CLEAN-CODE-NOTES.md (1–2 pages: key takeaways + examples from your code).
* `kata/` folder with one kata before/after refactor (git history shows it).

### Acceptance tests

* CI runs lint, type checks, and tests on PRs.
* At least one intentional failing test scenario added and fixed (TDD flow).
* Katas demonstrate meaningful names, small functions, and improved complexity.

## Submission checklist

`CODE/` modules • `tests/` + coverage report • config files • ADR-001.md • RUNBOOK.md • CONTRIBUTING.md • CLEAN-CODE-NOTES.md • kata repo history • CI log/screenshot

---

### Production-Readiness Checklist (attach to every PR)

- [ ] **HTTP semantics:** correct verbs; 201 + Location on create; 204 on delete.
- [ ] **Errors:** application/problem+json; precise 4xx/5xx; actionable detail.
- [ ] **Validation:** strict request/response models; size limits; allow-lists.
- [ ] **Security:** authn/z (when in scope), secret handling, CORS, headers.
- [ ] **File safety (if applicable):** magic number, canonical paths, atomic writes, collision-free names.
- [ ] **Observability:** structured logs with correlation IDs; health/readiness.
- [ ] **Docs:** OpenAPI updated; ADRs; RUNBOOK; Postman/contract tests.
- [ ] **Tests:** unit, integration, negative paths; coverage ≥ target.
- [ ] **Ops:** Dockerfile sane (non-root, slim); compose updates; NGINX routes & timeouts.

---

## How to submit each stage

1. Open a PR titled `Stage <N> – <title>`.
2. In the PR description, include links to: repo, CI run, OpenAPI/collection, ADRs, RUNBOOK, test reports, k6 (if any).
3. Add a brief `EVIDENCE.md` with 10–20 short snippets (file paths + line ranges) showing the most relevant parts.
4. Automated checks will run; you’ll receive a stage score with action items.

## Final note

You don’t pass by saying “I finished Stage N.”

You pass by showing running systems, measured results, auditable docs, and tested failure paths. Build like it’s going to production—because it will.

---

# Stage 2 — Python Backend Development (HTTP & API Contracts)

## Focus

* HTTP semantics (POST/GET/PATCH/DELETE).
* Status codes: 201 + Location on create, 204 on delete; precise 4xx vs 5xx.
* Consistent error format: Problem Details (application/problem+json).
* OpenAPI 3.1 with examples for success and errors.

## Outcomes

A coherent, testable API contract with an error catalog.

## Deliverables

* `openapi.yaml` (no code yet).
* Error catalog (`errors.md`): types, titles, status codes.
* Postman collection or contract tests.
* ADR-002 Error Model & HTTP Semantics.

### Acceptance tests

* OpenAPI validates (use any validator).
* Examples present for happy/edge/error cases.
* Collection/contract tests exercise success and failures.

## Submission checklist

`openapi.yaml` • `errors.md` • ADR-002.md • Postman collection or contract tests + run output

---

# Stage 3 — FastAPI Service Baseline

## Focus

* Implement Stage-2 spec in FastAPI with Pydantic models & DI.
* Health (`/health`) & readiness (`/ready`); structured logs; env-based config.
* Graceful shutdown; client timeouts for upstream calls.

## Outcomes

Contract-adherent service with reliable operational basics.

## Deliverables

* FastAPI app implementing Stage-2 OpenAPI (served at `/docs`).
* Dockerfile + docker-compose.yml.
* ≥ 12 integration tests (happy + failure), 85%+ branch coverage.
* ADR-003 Observability & Config.
* An “incident fix” PR that turns a 500 into a precise 4xx with Problem Details.

### Acceptance tests

* Contract tests pass end-to-end.
* `/health` and `/ready` behave correctly.
* Logs are structured and include correlation/request IDs.

## Submission checklist

`app/` source • `tests/` + coverage report • Dockerfile • docker-compose.yml • ADR-003.md • RUNBOOK.md • brief incident before/after notes

---

# Stage 4 — Databases (Postgres + MongoDB)

## Focus

* Postgres (SQLAlchemy + Alembic migrations).
* MongoDB (Motor) as a read-optimized projection.
* Indices from access patterns, pagination, transactions, connection pooling.

## Outcomes

Sound relational model with a read projection; measured index impact.

## Deliverables

Extend the app with users & tags:

* Write model in Postgres (with fully reversible migrations).
* Read model in MongoDB for tag-based queries.
* Seed & backfill scripts.
* ADR-004 Storage Choices & Indices.
* Tests demonstrating migration safety and index effectiveness.

### Acceptance tests

* Migration up/down works on a clean DB.
* A slow query becomes fast after your index (show numbers).
* Data layer coverage ≥ 85%.

## Submission checklist

`alembic/` migrations • `models.py` • Mongo read code • seed/backfill scripts • tests + coverage • before/after query evidence • ADR-004.md

---

# Stage 5 — Secure File/Asset Service + Docusaurus Integration

## Focus

* File upload security: magic-number validation (don’t trust extensions), size limits.
* Path canonicalization: reject traversal (`../`), confine writes under `/static/img`.
* Collision-free server-side naming (UUID or content hash); atomic writes.
* Correct verbs/status: POST → 201 + Location, DELETE → 204.
* Update a `metadata.json` contract consumed by Docusaurus.

## Outcomes

A production-safe asset pipeline with precise errors.

## Deliverables

* FastAPI Image Asset Service persisting under `/static/img` and updating `metadata.json`.
* OpenAPI + tests for negative paths (traversal, non-image, oversize, overwrite).
* Security checklist with threats and mitigations.
* 100% coverage on the upload module.
* ADR-005 Asset Pipeline & Security.

### Acceptance tests

* Traversal attempts rejected: `../`, `%2e%2e/`, absolute paths.
* Only real images accepted (magic-number).
* Size limit enforced; overwrite prevented; atomic write pattern used.
* Metadata updated correctly; errors use Problem Details.

## Submission checklist

Upload service code • metadata updater • tests • coverage for upload module • `openapi.yaml` • Postman/contract tests • `SECURITY_CHECKLIST.md` • sample `metadata.json`

---

# Stage 6 — Containers & Deployment (Docker) + NGINX – Reverse Proxy & API Gateway

## Focus

* Dockerfile best practices (non-root, slim images, healthcheck).
* Compose up a stack: auth, notes, assets, Postgres, Mongo, NGINX.
* NGINX: routing, timeouts, buffering, rate limits, gzip, basic caching.
* Blue/green or rolling swap locally.

## Outcomes

Services run behind NGINX with health checks; k6 shows SLOs.

## Deliverables

* Dockerfiles + docker-compose.yml.
* `nginx.conf` with upstreams, sensible timeouts, upload rate limit.
* k6 report (p95 latency, error budgets).
* ADR-006 Gateway & Deployment.

### Acceptance tests

* Smoke tests pass through NGINX.
* k6 summary meets your stated SLOs at target RPS.
* Demonstrate a zero-downtime container swap.

## Submission checklist

Dockerfiles • compose • `nginx.conf` • k6 summary/export • deploy steps • ADR-006.md • image sizes/users • healthcheck docs