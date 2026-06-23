# Task List: IPE Platform Production Readiness

**Task Branch**: `000-project-completion`

**Created**: 2026-06-20

**Status**: Generated from `specs/000-project-completion/plan.md`

**Total Tasks**: ~180 | **Total Effort**: ~200 engineer-weeks

---

## Task Key

| Prefix | Meaning |
|--------|---------|
| TASK-P0-NNN | Phase 0 — Quick-Win P0 Fixes |
| TASK-P1-NNN | Phase 1 — Complete Partial Sprints (S4-S5) |
| TASK-P2-NNN | Phase 2 — Enterprise IAM (S7) |
| TASK-P3-NNN | Phase 3 — Enterprise Solver (S6) |
| TASK-P4-NNN | Phase 4 — ESG Microservices (S11) |
| TASK-P5-NNN | Phase 5 — Strategic & Financial (S9) |
| TASK-P6-NNN | Phase 6 — Digital Twin & War Room (S10) |
| TASK-P7-NNN | Phase 7 — MLOps Pipeline (S8) |
| TASK-P8-NNN | Phase 8 — Multi-ERP & Edge (S12) |
| TASK-P9-NNN | Phase 9 — Chaos & Compliance (S13-S14) |
| TASK-P10-NNN | Phase 10 — UAT & Change (S15) |
| TASK-P11-NNN | Phase 11 — Production Go-Live (S16) |

---

## Phase 0 — Quick-Win P0 Fixes (Week 1)

### TASK-P0-001: Mount /metrics on all services

| Field | Value |
|-------|-------|
| **Description** | Add Prometheus `/metrics` endpoint to all 11 services using `prometheus_fastapi_instrumentator`. Currently zero services expose this. |
| **Effort** | 16 hours (11 services × ~1.5h each) |
| **Dependencies** | None |
| **Priority** | P0 |
| **Spec Ref** | FR-005, SC-005, Constitution §VI.1 |
| **VERIFY Gate** | `curl localhost:800X/metrics` returns HTTP 200 with Prometheus-formatted output on all services |
| **Files affected** | `services/*/app/main.py` (11 files) — add `Instrumentator().instrument(app).expose(app)` |
| **Status** | COMPLETE |

### TASK-P0-002: Add structured JSON logging middleware

| Field | Value |
|-------|-------|
| **Description** | Standardize all services to use JSON-formatted logging with `service_name`, `correlation_id`, `duration_ms`, `severity` fields via `ipe_shared.logging`. |
| **Effort** | 8 hours |
| **Dependencies** | None |
| **Priority** | P0 |
| **Spec Ref** | FR-021, SC-005 (part), Constitution §VI.2 |
| **VERIFY Gate** | Any service log line is valid JSON with required fields |
| **Files affected** | `services/shared/ipe_shared/logging/` (create or update); `services/*/app/main.py` (update logging config) |
| **Status** | COMPLETE |

### TASK-P0-003: Fix cdm_user seed failure

| Field | Value |
|-------|-------|
| **Description** | Seed script fails because `cdm_user` table lacks `password_hash` column. Add column in migration or update seed to skip missing column. |
| **Effort** | 4 hours |
| **Dependencies** | None |
| **Priority** | P0 |
| **Spec Ref** | SC-001 |
| **VERIFY Gate** | `scripts/seed-data.sh` runs without error; user row created |
| **Files affected** | `migrations/versions/` (new migration or seed script fix) |
| **Status** | COMPLETE |

### TASK-P0-004: Fix cdm_location table reference in seed

| Field | Value |
|-------|-------|
| **Description** | `seed-data.sh` references `cdm_location` table that does not exist in migrations. Create the table or remove the reference. |
| **Effort** | 4 hours |
| **Dependencies** | None |
| **Priority** | P0 |
| **Spec Ref** | SC-001 |
| **VERIFY Gate** | Seed script Inventory section completes without error |
| **Files affected** | `migrations/versions/` (new migration for cdm_location if needed) or `scripts/seed-data.sh` |
| **Status** | COMPLETE |

### TASK-P0-005: Resolve StrEnum deprecation warnings

| Field | Value |
|-------|-------|
| **Description** | Replace all `str(Enum)` patterns with `StrEnum` to eliminate deprecation warnings. Run `ruff check --fix` after changes. |
| **Effort** | 4 hours |
| **Dependencies** | None |
| **Priority** | P0 |
| **Spec Ref** | — |
| **VERIFY Gate** | `uv run ruff check` shows 0 StrEnum-related warnings |
| **Files affected** | All service model files using `str(Enum)` pattern (~10-20 files) |
| **Status** | COMPLETE |

---

## Phase 1 — Complete Partial Sprints (Weeks 2-5)

### Sprint 4 Completion — Copilot, Shop Floor PWA, Shadow Mode (Weeks 2-3)

#### TASK-P1-001: Complete Shop Floor PWA offline-first capabilities

| Field | Value |
|-------|-------|
| **Description** | Implement Service Worker caching for work orders and production schedules. Use IndexedDB for offline queue of delay reports. On reconnect, sync via idempotent batch IDs. |
| **Effort** | 40 hours |
| **Dependencies** | None |
| **Priority** | P1 |
| **Spec Ref** | FR-501, SC-014 |
| **VERIFY Gate** | Sever network → delay reports cached locally → syncs via idempotent batch IDs on reconnection |
| **Files affected** | `apps/web/src/features/shop-floor/` (Service Worker, IndexedDB helper, sync logic) |
| **Status** | COMPLETE |

#### TASK-P1-002: Add Voice-to-Text delay reporting

| Field | Value |
|-------|-------|
| **Description** | Integrate Web Speech API for voice transcription of delay reports on Shop Floor PWA. Transcribed text sent as structured delay report via PWA. |
| **Effort** | 16 hours |
| **Dependencies** | TASK-P1-001 (PWA framework) |
| **Priority** | P1 |
| **Spec Ref** | US9 |
| **VERIFY Gate** | Voice input transcribed and submitted as delay report with >90% accuracy on clean audio |
| **Files affected** | `apps/web/src/features/shop-floor/components/DelayReport.tsx` (voice input UI); `apps/web/src/lib/voice.ts` (Web Speech API wrapper) |
| **Status** | COMPLETE |

#### TASK-P1-003: Enhance Shadow Mode validation engine

| Field | Value |
|-------|-------|
| **Description** | Build statistical validation comparing AI predictions (`shadow_planned_end`) vs human actuals (`actual_completion_date`). Track OTD delta, AI accuracy %, and generate per-tenant shadow report. |
| **Effort** | 24 hours |
| **Dependencies** | None |
| **Priority** | P1 |
| **Spec Ref** | US9 (Shadow Mode) |
| **VERIFY Gate** | Shadow compares AI predictions to human actuals (not AI to AI) |
| **Files affected** | `services/fea-svc/app/core/shadow.py` (validation engine); `services/fea-svc/app/api/v1/shadow.py` (API endpoint) |
| **Status** | COMPLETE |

#### TASK-P1-004: Complete nlp-svc SSE streaming edge cases

| Field | Value |
|-------|-------|
| **Description** | Handle SSE streaming edge cases: client disconnect cleanup, 30s timeout with partial response, error recovery mid-stream, backpressure on slow consumers. |
| **Effort** | 16 hours |
| **Dependencies** | None |
| **Priority** | P1 |
| **Spec Ref** | FR-501 (part) |
| **VERIFY Gate** | SSE stream handles disconnect without resource leak; partial response returned on timeout |
| **Files affected** | `services/nlp-svc/app/api/v1/copilot.py` (SSE endpoint) |
| **Status** | COMPLETE |

### Sprint 5 Completion — XAI & Security Core (Weeks 4-5)

#### TASK-P1-005: Standardize XAI payload across all AI APIs

| Field | Value |
|-------|-------|
| **Description** | Add `xai_explanation` JSON field to every AI API response (fea-svc, res-svc, cap-svc, mat-svc, dpe-svc). Field MUST include: `constraints` (list), `assumptions` (list), `confidence_score` (float 0-1), `contributing_factors` (dict). |
| **Effort** | 32 hours |
| **Dependencies** | None |
| **Priority** | P1 |
| **Spec Ref** | US2, FR-012 (part) |
| **VERIFY Gate** | 100% of AI API responses contain valid `xai_explanation` with all required sub-fields |
| **Files affected** | `services/*/app/api/v1/*.py` (response models); `services/*/app/services/*.py` (add explanation generation) |
| **Status** | COMPLETE |

#### TASK-P1-006: Add RBAC to remaining services

| Field | Value |
|-------|-------|
| **Description** | Add `require_roles(...)` decorator to all POST/PUT/PATCH/DELETE endpoints in mat-svc, cap-svc, fea-svc, res-svc, rec-svc. Create role fixtures for testing. |
| **Effort** | 24 hours |
| **Dependencies** | None |
| **Priority** | P1 |
| **Spec Ref** | FR-012, SC-006, Constitution §II.2 |
| **VERIFY Gate** | Unauthorized POST/PUT/PATCH/DELETE returns 403 on all 5 services |
| **Files affected** | `services/mat-svc/app/api/v1/*.py`; `services/cap-svc/app/api/v1/*.py`; `services/fea-svc/app/api/v1/*.py`; `services/res-svc/app/api/v1/*.py`; `services/rec-svc/app/api/v1/*.py` |
| **Status** | COMPLETE |

#### TASK-P1-007: Deploy and configure Kong API Gateway

| Field | Value |
|-------|-------|
| **Description** | Configure Kong in docker-compose with: rate limiting plugin (100 req/min per tenant), JWT auth plugin (JWKS validation), CORS plugin. Add Lua plugin to strip spoofed `X-Tenant-ID` header and inject JWT-verified tenant ID. |
| **Effort** | 24 hours |
| **Dependencies** | None |
| **Priority** | P1 |
| **Spec Ref** | FR-301, SC-011 |
| **VERIFY Gate** | Rate limiting returns 429 at 101st request/min; spoofed X-Tenant-ID is replaced with JWT tenant |
| **Files affected** | `infrastructure/docker/docker-compose.yml` (Kong service); `infrastructure/kong/` (plugins, config) |
| **Status** | COMPLETE |

#### TASK-P1-008: Run full RLS audit and close remaining gaps

| Field | Value |
|-------|-------|
| **Description** | Write automated audit script that checks every table with `tenant_id` column for RLS policies. Add missing RLS policies via new migration. Verify in tests. |
| **Effort** | 16 hours |
| **Dependencies** | None |
| **Priority** | P1 |
| **Spec Ref** | FR-002, SC-002, Constitution §I |
| **VERIFY Gate** | 0 database tables with `tenant_id` lack RLS; automated audit passes |
| **Files affected** | `migrations/versions/` (new RLS-audit migration); `scripts/audit-rls.sh` (audit script) |
| **Status** | COMPLETE |

#### TASK-P1-009: Verify 100% endpoints return 401 without JWT

| Field | Value |
|-------|-------|
| **Description** | Write automated endpoint scanner that hits every non-health route on every service without a JWT. Verify 401 response. Exclude `/health`, `/ready`, `/metrics`. |
| **Effort** | 16 hours |
| **Dependencies** | None |
| **Priority** | P1 |
| **Spec Ref** | FR-003, SC-003, Constitution §II.1 |
| **VERIFY Gate** | 100% of non-health endpoints return 401 without valid JWT |
| **Files affected** | `scripts/scan-endpoints.py` (new automation script) |
| **Status** | COMPLETE |

#### TASK-P1-010: Implement optimistic locking concurrency tests

| Field | Value |
|-------|-------|
| **Description** | Write integration tests proving `version` field-based optimistic locking works: concurrent updates return 409, stale updates rejected, version auto-increments on success. |
| **Effort** | 12 hours |
| **Dependencies** | None |
| **Priority** | P1 |
| **Spec Ref** | US2 (Concurrency), Constitution §II |
| **VERIFY Gate** | res-svc approve endpoint returns 409 when version is stale |
| **Files affected** | `tests/integration/test_optimistic_locking.py` (new); `services/res-svc/tests/test_api_resolution.py` (add concurrency tests) |
| **Status** | COMPLETE |

---

## Phase 2 — Enterprise IAM (Weeks 6-9)

#### TASK-P2-001: Deploy Keycloak as OAuth 2.1/OIDC provider

| Field | Value |
|-------|-------|
| **Description** | Deploy Keycloak 22+ container in docker-compose. Configure realm, client (public for SPA, confidential for backend), users, roles. Export realm config as JSON for reproducibility. |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P1-007 (Kong configured) |
| **Priority** | P1 |
| **Spec Ref** | FR-008, SC-007 |
| **VERIFY Gate** | OAuth 2.1 authorization code flow with PKCE returns valid JWT |
| **Files affected** | `infrastructure/docker/docker-compose.yml` (Keycloak service); `infrastructure/keycloak/` (realm import, Dockerfile) |
| **Status** | COMPLETE |

#### TASK-P2-002: Migrate JWT validation from HS256 to JWKS

| Field | Value |
|-------|-------|
| **Description** | Update all 11 services' JWT validation to use Keycloak's JWKS endpoint instead of symmetric HS256 secret. Add JWKS caching with 1h TTL. Add JWKS endpoint health check in `/ready`. |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P2-001 (Keycloak deployed with JWKS endpoint) |
| **Priority** | P1 |
| **Spec Ref** | FR-002 (updated), SC-002 |
| **VERIFY Gate** | JWT signed by Keycloak validated via JWKS; old HS256 tokens rejected |
| **Files affected** | `services/shared/ipe_shared/auth/jwt.py` (JWKS validation); `services/*/app/deps.py` (update dependency) |
| **Status** | COMPLETE |

#### TASK-P2-003: Configure SAML 2.0 SSO for Azure AD / Okta

| Field | Value |
|-------|-------|
| **Description** | Configure Keycloak SAML 2.0 identity provider brokering for Azure AD and Okta. Support IdP-initiated and SP-initiated SSO. Map SAML assertions to IPE user attributes (email, roles, tenant_id). |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P2-001 (Keycloak deployed) |
| **Priority** | P1 |
| **Spec Ref** | FR-009, SC-008 |
| **VERIFY Gate** | SAML SSO login from Azure AD provisions user and redirects to IPE Control Tower |
| **Files affected** | `infrastructure/keycloak/` (SAML IDP config); `infrastructure/docker/docker-compose.yml` (Keycloak env vars) |
| **Status** | COMPLETE |

#### TASK-P2-004: Implement SCIM 2.0 endpoints

| Field | Value |
|-------|-------|
| **Description** | Implement SCIM 2.0 standard endpoints: `/Users` (GET, POST, PUT, PATCH, DELETE), `/Groups` (GET, POST, PUT, DELETE), `/Schemas`, `/Bulk`. Map SCIM User → IPE user with role assignment. Support pagination (`startIndex`, `count`), filtering (`filter`), and attribute selection (`attributes`). |
| **Effort** | 40 hours |
| **Dependencies** | TASK-P2-001 (Keycloak as identity store) |
| **Priority** | P1 |
| **Spec Ref** | FR-010, SC-009 |
| **VERIFY Gate** | `POST /Users` creates user in DB with correct role mapping within 5s; `DELETE /Users/{id}` revokes active sessions |
| **Files affected** | `services/scim-svc/` (new service or add to existing); or `services/ipe-identity/` (new dedicated identity service) |
| **Status** | COMPLETE |

#### TASK-P2-005: Configure mTLS via Istio

| Field | Value |
|-------|-------|
| **Description** | Deploy Istio service mesh. Configure `PeerAuthentication` to `STRICT` mode for pod-to-pod mTLS. Use cert-manager for automatic certificate rotation. Phased rollout: PERMISSIVE → STRICT over 2 weeks. |
| **Effort** | 24 hours |
| **Dependencies** | None |
| **Priority** | P1 |
| **Spec Ref** | FR-011, SC-010 |
| **VERIFY Gate** | `tcpdump` on any pod shows TLS handshake with client certificate; service without sidecar cannot connect |
| **Files affected** | `infrastructure/k8s/istio/` (PeerAuthentication, DestinationRule); `infrastructure/k8s/cert-manager/` (ClusterIssuer, Certificate) |
| **Status** | COMPLETE |

#### TASK-P2-006: Implement tiered LLM routing

| Field | Value |
|-------|-------|
| **Description** | Update nlp-svc to route LLM queries based on tenant tier: Tier 1 (SaaS) → Anthropic Claude (with PII stripping), Tier 2 (Private VPC) → AWS SageMaker Llama-3, Tier 3 (On-Prem) → local vLLM. Configurable via tenant config. Graceful fallback between tiers. |
| **Effort** | 32 hours |
| **Dependencies** | None |
| **Priority** | P2 |
| **Spec Ref** | FR-008 (part) |
| **VERIFY Gate** | Tier 3 routes to local vLLM with zero external network calls |
| **Files affected** | `services/nlp-svc/app/core/llm_client.py` (routing logic); `services/nlp-svc/app/core/tier_config.py` (tenant tier mapping) |
| **Status** | COMPLETE |

#### TASK-P2-007: Build PII stripping middleware

| Field | Value |
|-------|-------|
| **Description** | Build middleware using Microsoft Presidio for PII detection and anonymization. Strip: names (NER), emails (regex), SSNs (regex), phone numbers (regex), addresses (NER). Configurable per tenant tier. Log PII stripping events for audit. |
| **Effort** | 24 hours |
| **Dependencies** | None |
| **Priority** | P2 |
| **Spec Ref** | FR-008 (part) |
| **VERIFY Gate** | Prompt with "Contact John at john@test.com, SSN 123-45-6789" → LLM receives "[REDACTED]" |
| **Files affected** | `services/shared/ipe_shared/security/pii.py` (Presidio wrapper); `services/nlp-svc/app/middleware/pii.py` (FastAPI middleware) |
| **Status** | COMPLETE |

---

## Phase 3 — Enterprise Solver (Weeks 10-12)

#### TASK-P3-001: Define and implement ISolver interface

| Field | Value |
|-------|-------|
| **Description** | Define `ISolver` abstract base class with method `solve(context: SolverContext, constraints: list[Constraint]) -> ScheduleResult`. Context includes MOs, work centers, operators, shifts. Result includes assignments, tardiness, solver_status. |
| **Effort** | 16 hours |
| **Dependencies** | None |
| **Priority** | P2 |
| **Spec Ref** | US1 (Solver abstraction) |
| **VERIFY Gate** | Both OR-Tools and Gurobi implementations pass the same `ISolver` contract tests |
| **Files affected** | `services/shared/ipe_shared/solver/interface.py` (ISolver base); `services/shared/ipe_shared/solver/` (types, context, result models) |
| **Status** | COMPLETE |

#### TASK-P3-002: Refactor cap-svc to use ORToolsSolver via ISolver

| Field | Value |
|-------|-------|
| **Description** | Refactor `cap-svc/app/core/scheduler.py` to implement `ISolver` interface as `ORToolsSolver`. Keep existing CP-SAT logic but wrap it in the interface. Add factory function for solver instantiation. |
| **Effort** | 16 hours |
| **Dependencies** | TASK-P3-001 (ISolver interface) |
| **Priority** | P2 |
| **Spec Ref** | US1 |
| **VERIFY Gate** | Existing cap-svc tests pass without modification |
| **Files affected** | `services/cap-svc/app/core/scheduler.py` (refactor to implement ISolver); `services/cap-svc/app/core/solver_factory.py` (new) |
| **Status** | COMPLETE |

#### TASK-P3-003: Implement GurobiSolver adapter

| Field | Value |
|-------|-------|
| **Description** | Implement `GurobiSolver` implementing `ISolver`. Use Gurobi Python API to model: tardiness variables, no-overlap constraints, precedence constraints, priority-weighted objective. Handle license check; graceful fallback to OR-Tools if license not available. |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P3-001 (ISolver interface); Gurobi license |
| **Priority** | P2 |
| **Spec Ref** | US1 (Enterprise solver) |
| **VERIFY Gate** | Mock Gurobi license failure → system falls back to OR-Tools/Heuristic |
| **Files affected** | `services/cap-svc/app/core/solvers/gurobi_solver.py` (new); `services/cap-svc/app/core/solver_factory.py` (register Gurobi) |
| **Status** | COMPLETE |

#### TASK-P3-004: Write k6 load test suite for CI

| Field | Value |
|-------|-------|
| **Description** | Create k6 test scripts for 200 concurrent Monte Carlo ATP evaluations. Measure p95 latency, error rate, throughput. Add CI job to run k6 tests on merge to master. Set pass threshold: p95 < 5s, error rate < 1%. |
| **Effort** | 24 hours |
| **Dependencies** | None |
| **Priority** | P2 |
| **Spec Ref** | SC-010 (k6) |
| **VERIFY Gate** | k6 run shows p95 < 5s at 200 concurrent VUs |
| **Files affected** | `tests/performance/k6/load-test.js` (update); `.github/workflows/ci.yml` (add k6 job); `infrastructure/docker/docker-compose.test.yml` (k6 container) |
| **Status** | COMPLETE |

#### TASK-P3-005: Configure HPA based on load test results

| Field | Value |
|-------|-------|
| **Description** | Configure HorizontalPodAutoscaler for mat-svc and cap-svc based on CPU (target: 70%) and custom metric for Monte Carlo queue depth. Tune min/max replicas based on k6 results. |
| **Effort** | 16 hours |
| **Dependencies** | TASK-P3-004 (k6 results) |
| **Priority** | P2 |
| **Spec Ref** | FR-306 |
| **VERIFY Gate** | k6 load test triggers HPA scale-up; replicas return to min after load subsides |
| **Files affected** | `infrastructure/k8s/helm/ipe-platform/templates/hpa.yaml` (new); `infrastructure/k8s/helm/ipe-platform/values.yaml` (hpa settings) |
| **Status** | COMPLETE |

---

## Phase 4 — ESG Microservices (Weeks 13-18)

### Sustain-svc (Weeks 13-14)

#### TASK-P4-001: Scaffold sustain-svc service

| Field | Value |
|-------|-------|
| **Description** | Create new `services/sustain-svc/` with: FastAPI scaffold, `app/main.py`, `app/api/v1/`, `app/models/`, `app/core/`, `app/events/`, Dockerfile, pyproject.toml (workspace member), tests directory. Follow existing service conventions (layered architecture, /health/ready/metrics, shared library import). |
| **Effort** | 8 hours |
| **Dependencies** | None |
| **Priority** | P2 |
| **Spec Ref** | FR-101 (scaffold) |
| **VERIFY Gate** | `docker compose up` includes sustain-svc; `/health` returns 200 |
| **Files affected** | `services/sustain-svc/` (new directory); `infrastructure/docker/docker-compose.yml` (add sustain-svc); `pyproject.toml` (add workspace member) |
| **Status** | COMPLETE |

#### TASK-P4-002: Implement circular supply chain models

| Field | Value |
|-------|-------|
| **Description** | Implement data models and scoring for: recycling rates per material, take-back program eligibility, material recovery percentage, disassembly cost estimation. |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P4-001 (sustain-svc scaffold) |
| **Priority** | P2 |
| **Spec Ref** | FR-101 |
| **VERIFY Gate** | POST /sustainability/circularity-score returns valid material recovery % + disassembly cost for any BOM |
| **Files affected** | `services/sustain-svc/app/models/circularity.py`; `services/sustain-svc/app/core/scorer.py`; `services/sustain-svc/app/api/v1/circularity.py` |
| **Status** | COMPLETE |

#### TASK-P4-003: Implement end-of-life planning

| Field | Value |
|-------|-------|
| **Description** | Implement EOL date prediction based on product lifecycle data, component obsolescence scores, and regulatory phase-out schedules. Generate phase-out timelines with alternative sourcing recommendations. |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P4-001 (sustain-svc scaffold) |
| **Priority** | P2 |
| **Spec Ref** | FR-102 |
| **VERIFY Gate** | GET /sustainability/eol-plan returns phase-out schedule for product with EOL date and alternative sourcing |
| **Files affected** | `services/sustain-svc/app/models/eol.py`; `services/sustain-svc/app/core/eol_planner.py`; `services/sustain-svc/app/api/v1/eol.py` |
| **Status** | COMPLETE |

#### TASK-P4-004: Implement recyclability scoring

| Field | Value |
|-------|-------|
| **Description** | Score each product/BOM for recyclability based on: material composition, disassembly complexity, recycling infrastructure availability, hazardous material content. Return score (0-100) and improvement recommendations. |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P4-001 (sustain-svc scaffold) |
| **Priority** | P2 |
| **Spec Ref** | FR-103 |
| **VERIFY Gate** | POST /sustainability/recyclability-score returns score with breakdown and recommendations |
| **Files affected** | `services/sustain-svc/app/core/recyclability.py`; `services/sustain-svc/app/api/v1/recyclability.py` |
| **Status** | COMPLETE |

#### TASK-P4-005: Implement sustain-svc Kafka events

| Field | Value |
|-------|-------|
| **Description** | Register Avro schemas for `ipe.sustainability.circularity_scored` and `ipe.sustainability.eol_planned`. Implement producers in scoring endpoints. Add topics to setup script. Register in Schema Registry. |
| **Effort** | 16 hours |
| **Dependencies** | TASK-P4-002, TASK-P4-003, TASK-P4-004 |
| **Priority** | P2 |
| **Spec Ref** | FR-104 |
| **VERIFY Gate** | Event published on scoring → consumer can deserialize by registered Avro schema |
| **Files affected** | `services/sustain-svc/app/events/producers.py`; `infrastructure/kafka/setup-topics.sh`; `services/shared/ipe_shared/events/schemas/` |
| **Status** | COMPLETE |

#### TASK-P4-006: Build sustainability frontend dashboard

| Field | Value |
|-------|-------|
| **Description** | Create React dashboard under `apps/web/src/features/sustainability/`: carbon footprint over time (line chart), circularity score per product (bar chart), EOL timeline (gantt), recyclability scorecards. Fetch from sustain-svc API. |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P4-002, TASK-P4-003, TASK-P4-004 (APIs available) |
| **Priority** | P2 |
| **Spec Ref** | US4 |
| **VERIFY Gate** | Dashboard renders all three data views with real API data (not mock) |
| **Files affected** | `apps/web/src/features/sustainability/` (new feature directory); `apps/web/src/app/router.tsx` (add route) |
| **Status** | COMPLETE |

### Quality-svc (Weeks 15-16)

#### TASK-P4-007: Scaffold quality-svc service

| Field | Value |
|-------|-------|
| **Description** | Create `services/quality-svc/` following same pattern as TASK-P4-001. Include quality event models, SPC models, defect prediction models. |
| **Effort** | 8 hours |
| **Dependencies** | None |
| **Priority** | P2 |
| **Spec Ref** | FR-109 (scaffold) |
| **VERIFY Gate** | `docker compose up` includes quality-svc; `/health` returns 200 |
| **Files affected** | `services/quality-svc/` (new directory); `infrastructure/docker/docker-compose.yml`; `pyproject.toml` |
| **Status** | COMPLETE |

#### TASK-P4-008: Implement SPC charts and control limits

| Field | Value |
|-------|-------|
| **Description** | Implement Statistical Process Control: X-bar and R charts for continuous measurements, p-charts for defect rates. Configurable control limits (±3σ default). Auto-detect out-of-control conditions (points beyond limits, runs >7, trending). |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P4-007 (quality-svc scaffold) |
| **Priority** | P2 |
| **Spec Ref** | FR-109 |
| **VERIFY Gate** | Feed 100 quality measurements → SPC chart correctly identifies out-of-control condition |
| **Files affected** | `services/quality-svc/app/core/spc.py`; `services/quality-svc/app/models/spc.py`; `services/quality-svc/app/api/v1/spc.py` |
| **Status** | COMPLETE |

#### TASK-P4-009: Implement defect prediction

| Field | Value |
|-------|-------|
| **Description** | Build defect prediction model from quality event feed: features = operation type, work center, shift, operator, material batch, time since last maintenance. Predict defect probability per MO. Rule-based initially, ML-powered after Phase 7 (MLOps). |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P4-007 (quality-svc scaffold) |
| **Priority** | P2 |
| **Spec Ref** | FR-110 |
| **VERIFY Gate** | POST /quality/predict returns defect probability > 80% for known-defective MOs from historical data |
| **Files affected** | `services/quality-svc/app/core/predictor.py`; `services/quality-svc/app/api/v1/predict.py` |
| **Status** | COMPLETE |

#### TASK-P4-010: Build quality frontend dashboard

| Field | Value |
|-------|-------|
| **Description** | Create React dashboard: SPC control charts (recharts), defect heat map by work center, CP/CPK metrics, recent quality events feed. |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P4-008, TASK-P4-009 (APIs available) |
| **Priority** | P2 |
| **Spec Ref** | US4 |
| **VERIFY Gate** | SPC chart renders with real data; heat map shows correct defect concentration |
| **Files affected** | `apps/web/src/features/quality/` (new); `apps/web/src/app/router.tsx` |
| **Status** | COMPLETE |

### Scn-svc (Weeks 17-18)

#### TASK-P4-011: Scaffold scn-svc service

| Field | Value |
|-------|-------|
| **Description** | Create `services/scn-svc/` following same pattern. Include supplier, scorecard, RFQ models. Enforce strict RLS so suppliers only see their own POs. |
| **Effort** | 8 hours |
| **Dependencies** | None |
| **Priority** | P2 |
| **Spec Ref** | FR-105 (scaffold) |
| **VERIFY Gate** | Supplier A querying supplier B's data returns 403 (RLS enforced) |
| **Files affected** | `services/scn-svc/` (new); `infrastructure/docker/docker-compose.yml`; `pyproject.toml` |
| **Status** | COMPLETE |

#### TASK-P4-012: Implement supplier scorecards

| Field | Value |
|-------|-------|
| **Description** | Compute multi-dimensional supplier score: OTIF (weight 0.35), quality defect rate (0.25), cost competitiveness (0.20), sustainability score (0.10), responsiveness (0.10). Historical trend with 30/90/365-day windows. |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P4-011 (scn-svc scaffold) |
| **Priority** | P2 |
| **Spec Ref** | FR-105 |
| **VERIFY Gate** | POST /scn/supplier/score returns valid multi-dimensional score with historical trend |
| **Files affected** | `services/scn-svc/app/core/scorecard.py`; `services/scn-svc/app/api/v1/suppliers.py` |
| **Status** | COMPLETE |

#### TASK-P4-013: Implement RFQ/RFP management workflow

| Field | Value |
|-------|-------|
| **Description** | Full RFQ lifecycle: Create → Publish → Respond → Evaluate → Award → Order. Status machine with states (draft, published, responding, under_review, awarded, cancelled, expired). Auto-notify suppliers on publish. Support multi-line-item RFQs. |
| **Effort** | 40 hours |
| **Dependencies** | TASK-P4-011 (scn-svc scaffold) |
| **Priority** | P2 |
| **Spec Ref** | FR-106 |
| **VERIFY Gate** | Full RFQ lifecycle end-to-end: create → publish → respond → award → order created |
| **Files affected** | `services/scn-svc/app/models/rfq.py`; `services/scn-svc/app/core/rfq_workflow.py`; `services/scn-svc/app/api/v1/rfq.py` |
| **Status** | COMPLETE |

#### TASK-P4-014: Implement multi-tier visibility

| Field | Value |
|-------|-------|
| **Description** | Build supply chain graph: tier-1 supplier → tier-2 supplier → tier-3. Risk propagation algorithm: if tier-2 supplier has quality issue, propagate impact probability to tier-1 delivery risk. Visualize in supplier portal. |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P4-011 (scn-svc scaffold); TASK-P4-012 (scorecard data) |
| **Priority** | P2 |
| **Spec Ref** | FR-107 |
| **VERIFY Gate** | Mark tier-2 supplier as "at risk" → tier-1 visibility shows propagated risk with impact probability |
| **Files affected** | `services/scn-svc/app/core/supply_graph.py`; `services/scn-svc/app/core/risk_propagation.py`; `services/scn-svc/app/api/v1/visibility.py` |
| **Status** | COMPLETE |

#### TASK-P4-015: Implement scn-svc Kafka events

| Field | Value |
|-------|-------|
| **Description** | Register Avro schemas for `ipe.scn.supplier_scored`, `ipe.scn.rfq_created`, `ipe.scn.risk_detected`. Implement producers. Add topics to setup. |
| **Effort** | 16 hours |
| **Dependencies** | TASK-P4-012, TASK-P4-013, TASK-P4-014 |
| **Priority** | P2 |
| **Spec Ref** | FR-108 |
| **VERIFY Gate** | All 3 events publishable and consumable with registered Avro schemas |
| **Files affected** | `services/scn-svc/app/events/producers.py`; `infrastructure/kafka/setup-topics.sh` |
| **Status** | COMPLETE |

#### TASK-P4-016: Build SCN Portal frontend

| Field | Value |
|-------|-------|
| **Description** | Create supplier-facing React portal: supplier list with scorecards, RFQ list with status/count, create/respond to RFQs, risk alerts panel, performance trends. External Auth0 tenant for supplier authentication. BFF pattern for RLS enforcement. |
| **Effort** | 40 hours |
| **Dependencies** | TASK-P4-012, TASK-P4-013, TASK-P4-014 (APIs available) |
| **Priority** | P2 |
| **Spec Ref** | US5, SC-015 |
| **VERIFY Gate** | Supplier logs in via Auth0, sees only their POs and RFQs, scorecards render with real data |
| **Files affected** | `apps/web/src/features/scn-portal/` (new); `apps/web/src/app/router.tsx`; `apps/web/src/lib/auth-scn.ts` (Auth0 integration) |
| **Status** | COMPLETE |

---

## Phase 5 — Strategic & Financial (Weeks 19-22)

#### TASK-P5-001: Build S&OP ingestion API

| Field | Value |
|-------|-------|
| **Description** | Create API endpoint for unconstrained sales pipeline ingestion: monthly/quarterly demand forecasts, promotion plans, new product introductions. Aggregate into weekly buckets for S&OP solver. Store in new `cdm_sop_forecast` table. |
| **Effort** | 32 hours |
| **Dependencies** | None |
| **Priority** | P2 |
| **Spec Ref** | US10 (S&OP) |
| **VERIFY Gate** | POST /sop/forecast accepts pipeline data, returns aggregated weekly buckets |
| **Files affected** | `migrations/versions/` (cdm_sop_forecast table); `services/dpe-svc/app/api/v1/sop.py` (new); `services/dpe-svc/app/models/sop.py` (new) |
| **Status** | COMPLETE |

#### TASK-P5-002: Implement macro-level S&OP solver

| Field | Value |
|-------|-------|
| **Description** | Implement OR-Tools macro solver for S&OP: weekly time buckets (not discrete ops), capacity constraints by work center group, inventory targets, service level targets. Solve 52-week horizon in <10s. Output: constrained forecast, capacity gaps, inventory plan. |
| **Effort** | 40 hours |
| **Dependencies** | TASK-P5-001 (forecast data available) |
| **Priority** | P2 |
| **Spec Ref** | US10 (S&OP solver) |
| **VERIFY Gate** | S&OP simulation for 52 weeks with 10 product families solves in <10s; identifies capacity bottlenecks |
| **Files affected** | `services/dpe-svc/app/core/sop_solver.py` (new); `services/dpe-svc/app/api/v1/sop.py` (add solver endpoint) |
| **Status** | COMPLETE |

#### TASK-P5-003: Complete Financial Translation Engine

| Field | Value |
|-------|-------|
| **Description** | Extend existing Financial Projection Engine (Sprint 10) to map MO operations → GL cost centers. Compute: COGM (materials + labor + overhead + energy), COPQ (scrap + rework + inspection), variance analysis (planned vs actual). Versioned projections with audit trail. |
| **Effort** | 40 hours |
| **Dependencies** | None (extends existing engine) |
| **Priority** | P2 |
| **Spec Ref** | US10 (Financial) |
| **VERIFY Gate** | COGM for a completed MO matches manual accounting spreadsheet within 0.01% tolerance |
| **Files affected** | `services/dpe-svc/app/core/financial_projection.py` (extend); `services/dpe-svc/app/core/cost_accounting.py` (new); `services/dpe-svc/app/api/v1/financial.py` (extend) |
| **Status** | COMPLETE |

#### TASK-P5-004: Build Executive Dashboard

| Field | Value |
|-------|-------|
| **Description** | Create strategic React dashboard: P&L view (COGM, revenue, margin by product family), AI vs Manual OTD comparison, Capacity utilization heat map (monthly), S&OP gap analysis (forecast vs capacity), What-if simulation controls (adjust demand, add capacity, see financial impact). |
| **Effort** | 48 hours |
| **Dependencies** | TASK-P5-001, TASK-P5-002, TASK-P5-003 (all APIs available) |
| **Priority** | P2 |
| **Spec Ref** | FR-503, SC-016 |
| **VERIFY Gate** | Dashboard renders P&L, OTD comparison, capacity heatmap, and what-if simulation with real data |
| **Files affected** | `apps/web/src/features/executive/` (new/extend); `apps/web/src/app/router.tsx` |
| **Status** | COMPLETE |

#### TASK-P5-005: Build AI Trust Dashboard (preview)

| Field | Value |
|-------|-------|
| **Description** | Create React dashboard for AI Trust metrics: Adoption rate (AI recommendations accepted/total), Accuracy (AI prediction vs actual per model), Impact (OTD delta between AI-assisted and manual decisions), Override Nudge Modal (when AI recommends but planner overrides). |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P1-003 (Shadow validation data) |
| **Priority** | P2 |
| **Spec Ref** | FR-503 (part) |
| **VERIFY Gate** | Trust Dashboard shows Adoption, Accuracy, Impact scores with historical trend |
| **Files affected** | `apps/web/src/features/trust/` (new); `apps/web/src/app/router.tsx` |
| **Status** | COMPLETE |

---

## Phase 6 — Digital Twin & War Room (Weeks 23-26)

#### TASK-P6-001: Design recursive CTE queries for multi-level BOM explosion

| Field | Value |
|-------|-------|
| **Description** | Write PostgreSQL recursive CTE queries: explode multi-level BOMs (parent → child → grandchild), trace supplier dependencies (component → supplier → tier-2 supplier), propagate disruption (supplier delay → component shortage → MO delay). Target <2s for 10-level BOM with 1000+ components. |
| **Effort** | 24 hours |
| **Dependencies** | None (uses existing CDM tables) |
| **Priority** | P3 |
| **Spec Ref** | US10 (Digital Twin) |
| **VERIFY Gate** | Simulate tier-2 supplier delay → CTE identifies all downstream MOs in <2s |
| **Files affected** | `services/network-svc/app/core/digital_twin_queries.py` (new — CTE queries as raw SQL) |
| **Status** | COMPLETE |

#### TASK-P6-002: Build Digital Twin API

| Field | Value |
|-------|-------|
| **Description** | Create API layer over CTE queries: `GET /digital-twin/bom/{mo_id}` (full BOM explosion with lead times), `GET /digital-twin/supplier/{id}` (trace supplier dependencies downstream), `POST /digital-twin/disrupt` (simulate disruption, return impacted MOs). |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P6-001 (CTE queries) |
| **Priority** | P3 |
| **Spec Ref** | US10 |
| **VERIFY Gate** | POST /digital-twin/disrupt with supplier_id + delay_days returns impacted MOs list |
| **Files affected** | `services/network-svc/app/api/v1/digital_twin.py` (new); `services/network-svc/app/core/digital_twin_service.py` (new) |
| **Status** | COMPLETE |

#### TASK-P6-003: Enhance network-svc for multi-echelon optimization

| Field | Value |
|-------|-------|
| **Description** | Extend existing multi-plant optimization (Sprint 9) to full multi-echelon: plant → warehouse → customer, regional capacity constraints, transfer lot sizing, transport lead times, inventory positioning. Use CP-SAT for solver (or Gurobi if Phase 3 complete). |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P3-002 or TASK-P3-003 (ISolver) |
| **Priority** | P3 |
| **Spec Ref** | FR-301 (part) |
| **VERIFY Gate** | Multi-echelon optimization finds valid supply plan across 3 plants + 5 warehouses + 20 customers |
| **Files affected** | `services/network-svc/app/core/optimizer.py` (extend); `services/network-svc/app/api/v1/network.py` (extend) |
| **Status** | COMPLETE |

#### TASK-P6-004: Build War Room UX

| Field | Value |
|-------|-------|
| **Description** | Create React War Room dashboard: auto-aggregates impacted MOs during a disruption event (supplier delay, machine breakdown, port strike). Shows: impacted MO count by severity, timeline view, recommended mitigation actions, "Assign Task" button → creates Slack/Teams message. |
| **Effort** | 48 hours |
| **Dependencies** | TASK-P6-002 (Digital Twin API); TASK-P6-003 (network optimization) |
| **Priority** | P3 |
| **Spec Ref** | US10 (War Room) |
| **VERIFY Gate** | Trigger simulated port strike → War Room aggregates impacted MOs and sends Slack alerts in <60s |
| **Files affected** | `apps/web/src/features/war-room/` (new); `apps/web/src/app/router.tsx`; `services/alert-svc/app/integrations/slack.py` (new) |
| **Status** | COMPLETE |

#### TASK-P6-005: WebSocket disruption broadcast

| Field | Value |
|-------|-------|
| **Description** | Build WebSocket endpoint in fea-svc (or new gateway) that broadcasts disruption events to War Room dashboard in real-time. Subscribes to `ipe.scn.risk_detected`, `ipe.quality.spc_alert`, and new disruption event topics. |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P6-004 (War Room UX); Phase 4 Kafka events |
| **Priority** | P3 |
| **Spec Ref** | FR-501 (part) |
| **VERIFY Gate** | Publish disruption event → War Room dashboard updates in <2s via WebSocket |
| **Files affected** | `services/fea-svc/app/ws/disruption.py` (new broadcaster); `apps/web/src/lib/ws-disruption.ts` (new client) |
| **Status** | COMPLETE |

---

## Phase 7 — MLOps Pipeline (Weeks 23-26, parallel with Phase 5-6)

#### TASK-P7-001: Deploy MLflow tracking server

| Field | Value |
|-------|-------|
| **Description** | Deploy MLflow 2.5+ in docker-compose. Configure: tracking server (PostgreSQL backend store), S3-compatible artifact store (MinIO), model registry. Add to docker-compose with persistent volumes. |
| **Effort** | 16 hours |
| **Dependencies** | None |
| **Priority** | P3 |
| **Spec Ref** | FR-401 |
| **VERIFY Gate** | MLflow UI accessible; experiment logged with metrics + params + artifacts |
| **Files affected** | `infrastructure/docker/docker-compose.yml` (mlflow, minio services); `infrastructure/mlflow/` (config) |
| **Status** | COMPLETE |

#### TASK-P7-002: Implement Airflow DAG: pATP retraining

| Field | Value |
|-------|-------|
| **Description** | Create Airflow DAG `pATP_retraining` that runs daily: extracts historical MO actuals (completion dates vs planned), re-computes Monte Carlo delay distribution parameters, evaluates new params against holdout set, registers metrics in MLflow, promotes to production if MAPE improvement > 2%. |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P7-001 (MLflow deployed); Airflow deployed |
| **Priority** | P3 |
| **Spec Ref** | FR-402 |
| **VERIFY Gate** | DAG runs, extracts data, trains, evaluates MAPE, registers model in MLflow |
| **Files affected** | `airflow/dags/pATP_retraining.py` (new); `services/mat-svc/app/core/atp_trainer.py` (new training module) |
| **Status** | COMPLETE |

#### TASK-P7-003: Implement Airflow DAG: feasibility weight tuning

| Field | Value |
|-------|-------|
| **Description** | Create Airflow DAG `feasibility_tuning` that runs weekly: compares predicted feasibility scores vs actual completed MO outcomes, adjusts G1-G5 gate weights to minimize prediction error, registers tuned weights in MLflow, requires Data Steward approval for production promotion. |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P7-001 (MLflow deployed); Airflow deployed |
| **Priority** | P3 |
| **Spec Ref** | FR-402 |
| **VERIFY Gate** | DAG tunes weights and registers candidate model; auto-promotion blocked without approval |
| **Files affected** | `airflow/dags/feasibility_tuning.py` (new); `services/fea-svc/app/core/weight_tuner.py` (new) |
| **Status** | COMPLETE |

#### TASK-P7-004: Implement drift detection

| Field | Value |
|-------|-------|
| **Description** | Build drift detection module monitoring: NLP classifier accuracy (confidence degradation), pATP reliability (actual vs predicted OTD), feasibility score distribution (PSI — Population Stability Index). Alert via PagerDuty when drift > 5% threshold. Store drift metrics in MLflow. |
| **Effort** | 40 hours |
| **Dependencies** | TASK-P7-001 (MLflow for metrics storage) |
| **Priority** | P3 |
| **Spec Ref** | FR-403 |
| **VERIFY Gate** | Inject synthetic data drift → model flagged, blocked from auto-promotion, requires manual UI approval |
| **Files affected** | `services/shared/ipe_shared/ml/drift.py` (drift detection); `airflow/dags/drift_monitor.py` (new); `services/alert-svc/app/rules/drift.py` (drift alert rules) |
| **Status** | COMPLETE |

#### TASK-P7-005: Build Model Registry + Approval Gate UI

| Field | Value |
|-------|-------|
| **Description** | Build React UI for MLflow Model Registry: view registered models with versions, compare metrics across versions, promote from Staging → Production (Data Steward approval required), one-click rollback, model lineage (training DAG → MLflow run → deployed endpoint). |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P7-004 (drift metrics available) |
| **Priority** | P3 |
| **Spec Ref** | FR-404 |
| **VERIFY Gate** | One-click rollback switches inference endpoint to previous model version in <10s |
| **Files affected** | `apps/web/src/features/model-registry/` (new); `apps/web/src/app/router.tsx`; `services/fea-svc/app/api/v1/models.py` (model deployment endpoint) |
| **Status** | COMPLETE |

#### TASK-P7-006: Build MLOps Dashboard

| Field | Value |
|-------|-------|
| **Description** | Create React dashboard aggregating: experiment list (recent 50 runs with status/metrics), model registry (staging vs production versions), drift metrics (per-model PSI trend, accuracy trend), Data Steward approval queue (pending promotions). |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P7-005 (Model Registry UI) |
| **Priority** | P3 |
| **Spec Ref** | FR-404 (part) |
| **VERIFY Gate** | Dashboard shows experiments, model registry, drift metrics, and approval queue |
| **Files affected** | `apps/web/src/features/mlops/` (new); `apps/web/src/app/router.tsx` |
| **Status** | COMPLETE |

---

## Phase 8 — Multi-ERP & Edge (Weeks 27-30)

#### TASK-P8-001: Build SAP S/4HANA adapter

| Field | Value |
|-------|-------|
| **Description** | Build adapter connecting SAP S/4HANA via BAPI/OData. Map: SAP manufacturing orders → CDM manufacturing orders, SAP BOMs → CDM BOMs, SAP material masters → CDM materials, SAP work centers → CDM work centers. Full load + delta sync via change pointers. Strict CDM mapping — no SAP-specific logic leaks into core. |
| **Effort** | 40 hours |
| **Dependencies** | None (parallel with TASK-P8-002) |
| **Priority** | P3 |
| **Spec Ref** | US12 (Multi-ERP) |
| **VERIFY Gate** | SAP manufacturing order syncs to CDM with all fields correctly mapped; delta sync picks up changes within 5 min |
| **Files affected** | `services/connector/app/adapters/sap/` (new); `services/connector/app/adapters/sap/bapi.py`; `services/connector/app/adapters/sap/mapping.py` |
| **Status** | COMPLETE |

#### TASK-P8-002: Build D365 Business Central adapter

| Field | Value |
|-------|-------|
| **Description** | Build adapter for Dynamics 365 Business Central via Dataverse/OData. Map D365 entities → CDM. Handle ETag concurrency conflicts (409 → auto-retry with merge). Use MSAL for OAuth 2.0 client credentials. |
| **Effort** | 40 hours |
| **Dependencies** | None (parallel with TASK-P8-001) |
| **Priority** | P3 |
| **Spec Ref** | US12 (Multi-ERP) |
| **VERIFY Gate** | Simulate D365 409 ETag conflict → auto-retry merges without overwriting human changes |
| **Files affected** | `services/connector/app/adapters/d365/` (new); `services/connector/app/adapters/d365/dataverse.py`; `services/connector/app/adapters/d365/mapping.py` |
| **Status** | COMPLETE |

#### TASK-P8-003: Build K3s Edge Gateway

| Field | Value |
|-------|-------|
| **Description** | Build lightweight Edge Gateway for K3s deployment: SQLite local cache for offline operation, store-and-forward sync pattern, idempotency keys for deduplication, <2s sync when reconnection detected. Target total RAM: 512MB for all services on edge node. Kafka idempotency key pattern for conflict resolution. |
| **Effort** | 40 hours |
| **Dependencies** | None |
| **Priority** | P3 |
| **Spec Ref** | FR-303, SC-020 |
| **VERIFY Gate** | Simulate network flap → Edge sync creates zero duplicate CDM records |
| **Files affected** | `services/edge-gateway/` (new service); `infrastructure/k3s/` (deployment manifests); `infrastructure/docker/docker-compose.yml` (edge profile) |
| **Status** | COMPLETE |

#### TASK-P8-004: Implement Federated Learning DAG

| Field | Value |
|-------|-------|
| **Description** | Create Airflow DAG for opt-in federated learning: extract supplier reliability metrics from participating tenants, hash supplier IDs (SHA-256), compute statistical aggregates (mean OTIF, variance, sample size), share aggregated metrics across opt-in network. Zero raw data shared. Only hashed statistical aggregates leave tenant boundary. |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P7-001 (Airflow); TASK-P4-012 (supplier scorecards as data source) |
| **Priority** | P3 |
| **Spec Ref** | US12 (Federated Learning) |
| **VERIFY Gate** | FL payload contains zero raw PII or supplier-identifiable data; all IDs are SHA-256 hashed |
| **Files affected** | `airflow/dags/federated_learning.py` (new); `services/shared/ipe_shared/ml/federated.py` (aggregation logic) |
| **Status** | COMPLETE |

#### TASK-P8-005: Build Edge health monitoring dashboard

| Field | Value |
|-------|-------|
| **Description** | Create React dashboard for edge fleet monitoring: K3s node status (online/offline), sync lag (seconds since last sync), conflict rate (daily deduplication collisions), queue depth (pending outbound events), per-node resource usage (CPU, RAM, disk). |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P8-003 (Edge Gateway deployed) |
| **Priority** | P3 |
| **Spec Ref** | FR-303 (part) |
| **VERIFY Gate** | Dashboard shows 5+ edge nodes with real-time sync lag and resource metrics |
| **Files affected** | `apps/web/src/features/edge-monitor/` (new); `apps/web/src/app/router.tsx` |
| **Status** | COMPLETE |

---

## Phase 9 — Chaos & Compliance (Weeks 31-36)

### Sprint 13 — Chaos Engineering (Weeks 31-33)

#### TASK-P9-001: Implement Schemathesis for all FastAPI endpoints

| Field | Value |
|-------|-------|
| **Description** | Integrate Schemathesis for all 11 service OpenAPI specs. Run fuzz testing on all endpoints: random inputs, boundary values, invalid types, missing fields, unexpected fields. Verify 0 unhandled 5xx errors. Add as CI gate on merge to master. |
| **Effort** | 32 hours |
| **Dependencies** | None |
| **Priority** | P3 |
| **Spec Ref** | SC-022 (contract) |
| **VERIFY Gate** | Run Schemathesis → 0 unhandled 5xx errors on all public endpoints |
| **Files affected** | `tests/contract/` (new directory); `.github/workflows/ci.yml` (add schemathesis job); `pyproject.toml` (add schemathesis dependency) |
| **Status** | COMPLETE |

#### TASK-P9-002: Write 20-scenario parameterized cap-svc tests

| Field | Value |
|-------|-------|
| **Description** | Write `pytest` parameterized tests for cap-svc covering: 5-level BOM explosion, skill-constrained scheduling, multi-work-center routing, operator absence scenarios, 30s timeout → heuristic fallback validation, zero-MO edge case, single-MO case, 1000-MO scaling, Gurobi fallback (if Phase 3 done). |
| **Effort** | 24 hours |
| **Dependencies** | None |
| **Priority** | P3 |
| **Spec Ref** | SC-022 (solver correctness) |
| **VERIFY Gate** | All 20 scenarios pass; heuristic fallback verified on timeout |
| **Files affected** | `services/cap-svc/tests/test_solver_scenarios.py` (new) |
| **Status** | COMPLETE |

#### TASK-P9-003: Run k6 load test suite in CI

| Field | Value |
|-------|-------|
| **Description** | Add k6 load test as mandatory CI gate: 200 concurrent VUs, 5-min sustained run, thresholds: p95 < 5000ms, error rate < 1%, checks > 95%. Block merge on failure. Historical trend tracking for regression detection. |
| **Effort** | 16 hours |
| **Dependencies** | TASK-P3-004 (k6 scripts) |
| **Priority** | P3 |
| **Spec Ref** | SC-010 |
| **VERIFY Gate** | CI k6 job passes with p95 < 5s, error rate < 1% |
| **Files affected** | `.github/workflows/ci.yml` (update k6 job with thresholds) |
| **Status** | COMPLETE |

#### TASK-P9-004: Deploy Chaos Mesh + write experiment manifests

| Field | Value |
|-------|-------|
| **Description** | Deploy Chaos Mesh in staging Kubernetes cluster. Write experiment manifests for: Kafka leader pod kill (1 of 3 brokers), Postgres primary pod failure (trigger Patroni failover), Redis pod kill, network partition between mat-svc and Kafka, CPU pressure on cap-svc (80% throttle). Each experiment includes automated verification step. |
| **Effort** | 40 hours |
| **Dependencies** | Staging K8s cluster |
| **Priority** | P3 |
| **Spec Ref** | SC-022 (chaos) |
| **VERIFY Gate** | Postgres primary killed → auto-failover in <15s with zero data loss via Outbox; Kafka leader killed → consumer group rebalances in <30s |
| **Files affected** | `tests/chaos/` (new directory with Chaos Mesh YAML manifests); `infrastructure/k8s/chaos-mesh/` (install config) |
| **Status** | COMPLETE |

#### TASK-P9-005: Validate Transactional Outbox post-chaos

| Field | Value |
|-------|-------|
| **Description** | After each chaos experiment, validate: Transactional Outbox has replayed all pending events, no events lost (count matches producer-side counter), no duplicate events in target system (idempotency keys verified), Event sourcing log is consistent. |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P9-004 (Chaos Mesh experiments) |
| **Priority** | P3 |
| **Spec Ref** | SC-022 (data integrity) |
| **VERIFY Gate** | Post-chaos outbox replay shows zero data loss, zero duplicates |
| **Files affected** | `tests/chaos/validate_outbox.py` (new verification script); `.github/workflows/chaos.yml` (new workflow) |
| **Status** | COMPLETE |

### Sprint 14 — Compliance (Weeks 34-36)

#### TASK-P9-006: Implement append-only cdm_audit_log

| Field | Value |
|-------|-------|
| **Description** | Create `cdm_audit_log` table with: event_id (UUID), timestamp (TIMESTAMPTZ, NIST-synced), tenant_id, user_id, action_type, entity_type, entity_id, old_values (JSONB), new_values (JSONB), ip_address, user_agent. `REVOKE UPDATE, DELETE` on table. All state-changing operations write to this log. |
| **Effort** | 24 hours |
| **Dependencies** | None |
| **Priority** | P2 |
| **Spec Ref** | FR-201 |
| **VERIFY Gate** | Attempt to UPDATE or DELETE from cdm_audit_log returns permission denied |
| **Files affected** | `migrations/versions/` (new migration); `services/shared/ipe_shared/audit/service.py` (write audit log); `services/*/app/api/v1/*.py` (add audit calls) |
| **Status** | COMPLETE |

#### TASK-P9-007: Implement SOC 2 evidence collector

| Field | Value |
|-------|-------|
| **Description** | Build automated collector that gathers evidence for all 6 SOC 2 trust principles: Security (access logs, auth config, RLS policies), Availability (uptime reports, incident response docs), Processing Integrity (data quality reports, reconciliation logs), Confidentiality (encryption config, access control lists), Privacy (PII inventory, DSAR responses), + additional principle. Output: downloadable evidence package per principle. |
| **Effort** | 40 hours |
| **Dependencies** | TASK-P9-006 (audit log) |
| **Priority** | P2 |
| **Spec Ref** | FR-201, SC-012 |
| **VERIFY Gate** | Evidence collector returns non-empty report for all 6 trust principles |
| **Files affected** | `services/audit-svc/` (new service or extend existing); `services/audit-svc/app/core/soc2_collector.py`; `services/audit-svc/app/api/v1/evidence.py` |
| **Status** | COMPLETE |

#### TASK-P9-008: Implement GDPR DSAR API

| Field | Value |
|-------|-------|
| **Description** | Implement Data Subject Access Request API: `POST /dsar` (submit request with tenant ID and date range), `GET /dsar/{id}/status` (check progress), `GET /dsar/{id}/download` (download as JSON/CSV). Async processing for large tenants (>1M rows) with S3 staging and signed URL delivery. Respond within 30 calendar days per GDPR. |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P9-006 (audit log for tracking) |
| **Priority** | P2 |
| **Spec Ref** | FR-202, SC-013 |
| **VERIFY Gate** | DSAR for tenant returns all personal data within 30-day window in machine-readable format |
| **Files affected** | `services/audit-svc/app/api/v1/dsar.py`; `services/audit-svc/app/core/dsar_processor.py`; `migrations/versions/` (dsar tracking table) |
| **Status** | COMPLETE |

#### TASK-P9-009: Implement data retention policies

| Field | Value |
|-------|-------|
| **Description** | Implement configurable per-entity data retention policies: TTL-based auto-archiving (move to `_archive` table), TTL-based auto-deletion (GDPR right to erasure), exclusion patterns (financial records retained 7 years, PII anonymized at 30 days). Configurable via tenant config. |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P9-006 (audit log) |
| **Priority** | P2 |
| **Spec Ref** | FR-203 |
| **VERIFY Gate** | Entity exceeding TTL auto-archived; PII anonymized at 30-day threshold |
| **Files affected** | `services/shared/ipe_shared/retention/service.py` (retention engine); `services/shared/ipe_shared/retention/config.py` (config models); `airflow/dags/retention_enforcement.py` (scheduled DAG) |
| **Status** | COMPLETE |

#### TASK-P9-010: Implement FDA 21 CFR Part 11 electronic signature

| Field | Value |
|-------|-------|
| **Description** | Implement Part 11 compliant e-signature: signing ceremony requires username + password re-entry, audit log captures (user_id, NIST-synchronized timestamp, signature meaning, full record signed), N-attempt lockout (configurable, default 5), concurrent e-sign prevention (no interleaving), printed name + date+time on signing UI. |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P9-006 (audit log) |
| **Priority** | P2 |
| **Spec Ref** | FR-204, FR-205 |
| **VERIFY Gate** | E-sign audit log contains user_id, timestamp (NIST), signature meaning, full record; failed attempt #6 locks account |
| **Files affected** | `services/shared/ipe_shared/esign/service.py`; `services/res-svc/app/api/v1/resolution.py` (add e-sign to approve); `apps/web/src/features/resolution-center/` (signing ceremony UI) |
| **Status** | COMPLETE |

#### TASK-P9-011: Deploy BYOK KMS (AWS KMS)

| Field | Value |
|-------|-------|
| **Description** | Terraform AWS KMS customer-managed key (CMK) for Enterprise tenants. IAM policy: deny root AWS account `kms:Decrypt`, allow tenant-specific IAM role with usage quotas. Key rotation: automatic every 365 days. DEK caching in-memory with 1h TTL. Tenant isolation: each Enterprise tenant gets unique KMS key. |
| **Effort** | 24 hours |
| **Dependencies** | AWS account with KMS; Enterprise tenant requirement |
| **Priority** | P2 |
| **Spec Ref** | FR-301 (BYOK) |
| **VERIFY Gate** | Access Enterprise tenant DB using SaaS root AWS credentials → KMS returns `AccessDenied` |
| **Files affected** | `infrastructure/terraform/aws/kms/` (new); `infrastructure/terraform/aws/iam/` (policy updates) |
| **Status** | COMPLETE |

#### TASK-P9-012: Harden Kong API Gateway

| Field | Value |
|-------|-------|
| **Description** | Full Kong hardening: rate limiting plugin (100 req/min per tenant, burst 200), JWT auth plugin (JWKS validation via Keycloak), IP whitelisting for admin API, Lua plugin to strip client `X-Tenant-ID` and inject JWT-verified tenant, CORS restricted to allowed origins, request size limiting (10MB max). |
| **Effort** | 16 hours |
| **Dependencies** | TASK-P2-001 (Keycloak for JWKS) |
| **Priority** | P2 |
| **Spec Ref** | FR-301 (Kong hardening) |
| **VERIFY Gate** | Fake `X-Tenant-ID` header stripped and replaced with JWT-verified tenant ID; rate limiting returns 429 on threshold |
| **Files affected** | `infrastructure/kong/plugins/` (Lua plugin); `infrastructure/kong/kong.yml` (declarative config) |
| **Status** | COMPLETE |

#### TASK-P9-013: Third-party penetration test

| Field | Value |
|-------|-------|
| **Description** | Engage third-party pen-testing firm. Scope: all 11 service APIs, Kong gateway, Keycloak IAM, RLS enforcement, JWT validation, mTLS configuration, Kubernetes RBAC, network policies. Remediate all Critical/High findings before Phase 11. |
| **Effort** | 40 hours (coordination + remediation) |
| **Dependencies** | TASK-P9-012 (Kong hardening); TASK-P2-002 (JWKS validation); TASK-P2-005 (mTLS) |
| **Priority** | P2 |
| **Spec Ref** | SC-022 (security) |
| **VERIFY Gate** | 0 Critical/High pen-test findings after remediation |
| **Files affected** | `docs/security/pen-test-report.md` (findings log); various service files (remediation patches) |
| **Status** | COMPLETE |

---

## Phase 10 — UAT & Change Management (Weeks 37-40)

#### TASK-P10-001: Build shadow_roi_validator.py

| Field | Value |
|-------|-------|
| **Description** | Statistical validator using `scipy.stats`: compute OTD delta between AI-assisted decisions and manual-only decisions, 95% confidence interval via bootstrap resampling, filter out cancelled/scrapped MOs to maintain statistical purity, output: report PDF with executive summary + methodology + raw data. |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P1-003 (Shadow Mode validation data) |
| **Priority** | P2 |
| **Spec Ref** | US6 (ROI validation) |
| **VERIFY Gate** | Script filters out cancelled/scrapped MOs; reports OTD delta with 95% CI; >10% improvement required for sign-off |
| **Files affected** | `scripts/shadow_roi_validator.py` (new); `scripts/shadow_roi_config.yaml` (config) |
| **Status** | COMPLETE |

#### TASK-P10-002: Build AI Trust Dashboard

| Field | Value |
|-------|-------|
| **Description** | Expand Trust Dashboard (TASK-P5-005) with: Adoption rate per team/plant, Accuracy per model with historical trend, Impact (OTD delta in hours/dollars), Override reasons analytics (why planners override AI), Override Nudge Modal (when planner overrides AI recommendation with lower score, show confirmation with projected impact). |
| **Effort** | 40 hours |
| **Dependencies** | TASK-P5-005 (Trust Dashboard preview) |
| **Priority** | P2 |
| **Spec Ref** | US6 (Trust Dashboard) |
| **VERIFY Gate** | Override Nudge Modal shows projected OTD impact before confirmation |
| **Files affected** | `apps/web/src/features/trust/` (extend); `apps/web/src/features/trust/components/OverrideModal.tsx` (nudge modal) |
| **Status** | COMPLETE |

#### TASK-P10-003: Implement Progressive Autonomy state machine

| Field | Value |
|-------|-------|
| **Description** | State machine with 3 states per tenant: Shadow (AI scores but never writes — current state), Suggest (AI writes to staging, planner must confirm → ERP write), Autonomous (AI writes directly to ERP within confidence thresholds). State transitions via LaunchDarkly feature flags. State stored in tenant config. |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P1-007 (Kong for auth boundaries); TASK-P2-002 (Keycloak for tenant identity) |
| **Priority** | P2 |
| **Spec Ref** | US6 (Autonomy) |
| **VERIFY Gate** | Tenant in Shadow mode → AI never writes to ERP; Autonomous mode → AI writes directly within confidence thresholds |
| **Files affected** | `services/shared/ipe_shared/autonomy/state_machine.py`; `services/*/app/middleware/autonomy.py` (new middleware); `apps/web/src/features/admin/autonomy.py` (admin UI) |
| **Status** | COMPLETE |

#### TASK-P10-004: Implement synchronous safety guardrail

| Field | Value |
|-------|-------|
| **Description** | Synchronous guardrail: if AI-computed feasibility < 85%, block write-back to ERP synchronously (return 403 to caller with explanation). Asynchronous Kafka alert → Slack webhook < 2s. Configurable threshold per tenant. Guardrail applies to res-svc (approval), fea-svc (auto-confirm), cap-svc (schedule publish). |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P10-003 (Autonomy state machine) |
| **Priority** | P2 |
| **Spec Ref** | US6 (Guardrail) |
| **VERIFY Gate** | Set tenant to Autonomous, create MO with 82% feasibility → ERP write-back blocked synchronously, Slack alert arrives < 2s |
| **Files affected** | `services/fea-svc/app/core/guardrail.py`; `services/fea-svc/app/api/v1/feasibility.py` (add guardrail check); `services/alert-svc/app/integrations/slack.py` (webhook) |
| **Status** | COMPLETE |

#### TASK-P10-005: Conduct 30-day Shadow Mode validation

| Field | Value |
|-------|-------|
| **Description** | Warm up Shadow Mode for 30+ days (may already be running from Phase 1). At end, run `shadow_roi_validator.py` to produce statistical report. Present to customer for UAT sign-off. Sign-off criteria: >10% OTD improvement at 95% CI, < 5% override rate, zero safety incidents. |
| **Effort** | 16 hours (analysis) + 30 days (data collection, can parallel with other phases) |
| **Dependencies** | TASK-P10-001 (ROI validator); 30+ days of shadow data |
| **Priority** | P2 |
| **Spec Ref** | US6 (UAT sign-off) |
| **VERIFY Gate** | Customer signs off on UAT report showing statistically significant OTD improvement |
| **Files affected** | `docs/uat/` (sign-off documentation); `scripts/shadow_roi_validator.py` (final report) |
| **Status** | COMPLETE |

---

## Phase 11 — Production Go-Live (Weeks 41-42)

#### TASK-P11-001: Finalize Terraform for Prod EKS

| Field | Value |
|-------|-------|
| **Description** | Terraform modules for: EKS cluster (multi-AZ, managed node groups), RDS PostgreSQL (Multi-AZ, automated backups, 35-day retention), MSK Kafka (3-broker, multi-AZ), ElastiCache Redis (cluster mode, multi-AZ), S3 buckets (MLflow artifacts, audit logs, DSAR exports), IAM roles for service accounts (IRSA). |
| **Effort** | 32 hours |
| **Dependencies** | None |
| **Priority** | P3 |
| **Spec Ref** | FR-301-FR-306, SC-019 |
| **VERIFY Gate** | `terraform apply` provisions all resources; EKS cluster accessible via kubectl |
| **Files affected** | `infrastructure/terraform/aws/` (new directory — modules for each resource); `infrastructure/terraform/aws/envs/prod/` (prod env config) |
| **Status** | COMPLETE |

#### TASK-P11-002: Bootstrap ArgoCD app-of-apps

| Field | Value |
|-------|-------|
| **Description** | Deploy ArgoCD in EKS cluster. Configure app-of-apps pattern: root app syncs child apps (infra, services, frontend, monitoring). Sync policy: automated pruning, self-heal enabled. Environment overlay: dev/staging/prod branches with kustomize patches. Webhook triggers: push to staging branch → auto-sync staging environment. |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P11-001 (EKS cluster) |
| **Priority** | P3 |
| **Spec Ref** | FR-302, FR-307 |
| **VERIFY Gate** | Git push to staging branch → ArgoCD auto-syncs within 60s |
| **Files affected** | `infrastructure/k8s/argocd/` (app-of-apps config); `infrastructure/k8s/helm/ipe-platform/` (Helm charts); `infrastructure/k8s/kustomize/` (env overlays) |
| **Status** | COMPLETE |

#### TASK-P11-003: Configure OpenTelemetry + SLO alerts

| Field | Value |
|-------|-------|
| **Description** | Deploy OpenTelemetry Collector (DaemonSet) for traces + metrics + logs. Configure Prometheus ServiceMonitor for all services. Set SLO burn-rate alerts: p99 latency < 5s (burn-rate: 1h window), error rate < 0.1% (1h window), availability > 99.9% (30d window). PagerDuty integration for Critical alerts, Slack for Warning. |
| **Effort** | 24 hours |
| **Dependencies** | TASK-P0-001 (/metrics on all services); TASK-P0-002 (structured logging) |
| **Priority** | P3 |
| **Spec Ref** | FR-003-FR-005 (observability) |
| **VERIFY Gate** | OpenTelemetry trace propagates across 3+ services; SLO burn-rate alert fires when error rate exceeds threshold |
| **Files affected** | `infrastructure/k8s/opentelemetry/` (collector config); `infrastructure/k8s/prometheus/` (ServiceMonitor, rules); `infrastructure/k8s/pagerduty/` (integration config) |
| **Status** | COMPLETE |

#### TASK-P11-004: Design and test Argo Rollouts canary strategy

| Field | Value |
|-------|-------|
| **Description** | Argo Rollouts canary strategy: step 1 → 5% traffic for 5 min (analyze: error rate < 1%, latency p95 < 2x baseline), step 2 → 25% for 10 min (same analysis), step 3 → 100% (full promotion). Rollback: if any step fails, traffic shifts back to stable in < 2 min. Analysis queries new ReplicaSet metrics only (not aggregate). |
| **Effort** | 32 hours |
| **Dependencies** | TASK-P11-002 (ArgoCD) |
| **Priority** | P3 |
| **Spec Ref** | SC-028 (canary) |
| **VERIFY Gate** | Inject 5% error rate into canary → Argo Rollouts automatically halts and shifts 100% traffic back to stable in < 2 min |
| **Files affected** | `infrastructure/k8s/rollouts/` (Rollout YAMLs); `infrastructure/k8s/rollouts/analysis-templates/` (analysis templates) |
| **Status** | COMPLETE |

#### TASK-P11-005: Execute First Autonomous MO synthetic test

| Field | Value |
|-------|-------|
| **Description** | Create synthetic Manufacturing Order in Odoo → verify end-to-end flow: Odoo connector → dpe-svc (priority) → mat-svc (pATP) → cap-svc (CP-SAT schedule) → fea-svc (feasibility score, guardrail passes) → res-svc (auto-approve in Autonomous mode) → connector (MO confirmed in Odoo). Verify `cdm_audit_log` captures `autonomous_confirmation` with AI rationale for each step. |
| **Effort** | 16 hours |
| **Dependencies** | TASK-P10-003 (Autonomy); TASK-P10-004 (Guardrail); all service phases |
| **Priority** | P3 |
| **Spec Ref** | SC-028 (first autonomous MO) |
| **VERIFY Gate** | First Autonomous MO flows ERP → IPE → ERP with zero human clicks; audit log captures `autonomous_confirmation` |
| **Files affected** | `scripts/e2e/first_autonomous_mo.py` (new test script); `docs/operations/first-autonomous-mo.md` (runbook) |
| **Status** | COMPLETE |

#### TASK-P11-006: Draft and test Rollback Runbook

| Field | Value |
|-------|-------|
| **Description** | Document and test rollback procedures for: service-level rollback (Helm rollback --revision), full-platform rollback (ArgoCD sync revert + Kong traffic shift), database rollback (RDS point-in-time recovery + Outbox replay), Kafka consumer reset (reset to earliest/latest offset). Target: < 15 min full-rollback. |
| **Effort** | 16 hours |
| **Dependencies** | TASK-P11-001 (Terraform); TASK-P11-002 (ArgoCD) |
| **Priority** | P3 |
| **Spec Ref** | SC-028 (rollback) |
| **VERIFY Gate** | Full rollback executed in < 15 min; traffic shifted via Kong without DNS TTL delay |
| **Files affected** | `docs/operations/rollback-runbook.md` (new); `infrastructure/k8s/scripts/rollback.sh` (automation script) |
| **Status** | COMPLETE |

#### TASK-P11-007: Production readiness review

| Field | Value |
|-------|-------|
| **Description** | Final review checklist: all dashboards green (Prometheus, Grafana), all SLO alerts configured and tested, PagerDuty on-call rotation established, runbooks documented and reviewed, support team briefed, backup/restore tested, penetration test passed (0 Critical/High), SOC 2 evidence collection operational. |
| **Effort** | 8 hours |
| **Dependencies** | All TASK-P11 items |
| **Priority** | P3 |
| **Spec Ref** | SC-028 (production readiness) |
| **VERIFY Gate** | Production readiness checklist 100% complete; team confirms go-live |
| **Files affected** | `docs/operations/production-readiness-checklist.md` (new) |
| **Status** | COMPLETE |

---

## Summary: Task Count and Effort by Phase

| Phase | Tasks | Total Hours | Engineer-Weeks | Critical Path |
|-------|-------|-------------|----------------|---------------|
| P0 — Quick Fixes | 5 | 36 | ~1 | Yes |
| P1 — Complete Partial Sprints | 10 | 224 | ~5.6 | Yes |
| P2 — Enterprise IAM | 7 | 200 | ~5.0 | Yes |
| P3 — Enterprise Solver | 5 | 104 | ~2.6 | Yes |
| P4 — ESG Microservices | 16 | 448 | ~11.2 | No (parallel track) |
| P5 — Strategic & Financial | 5 | 192 | ~4.8 | Yes |
| P6 — Digital Twin & War Room | 5 | 160 | ~4.0 | Yes |
| P7 — MLOps Pipeline | 6 | 160 | ~4.0 | No (parallel track) |
| P8 — Multi-ERP & Edge | 5 | 176 | ~4.4 | Yes (after P5-P6) |
| P9 — Chaos & Compliance | 13 | 376 | ~9.4 | Yes |
| P10 — UAT & Change | 5 | 136 | ~3.4 | Yes |
| P11 — Production Go-Live | 7 | 152 | ~3.8 | Yes |
| **Total** | **89** | **2,364** | **~59** | **~45 weeks** |

*Note: Tasks above represent ~59 engineer-weeks of concrete implementation work. The plan's 200 engineer-week estimate accounts for: testing, debugging, code review, documentation, meetings, and parallel team overhead. Multiply implementation hours by ~3.4x for total effort.*
