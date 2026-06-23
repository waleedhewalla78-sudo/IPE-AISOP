# Execution Plan: IPE Platform Production Readiness & BRD/PRD Alignment

**Plan Branch**: `000-project-completion`

**Created**: 2026-06-20

**Status**: Draft

**Inputs**:
- Constitution: `.specify/memory/constitution.md` (6 binding principles)
- Specification: `specs/000-project-completion/spec.md` (48 FRs, 30 SCs)
- Audit: `audit/v2/` (15 deliverable files)
- BRD/PRD: `D:\AISOP\333.txt` (IPE v1.0–v5.0 evolution)
- Sprint Roadmap: `D:\AISOP\Sprints.txt` (16 SCADA-formatted sprints)

---

## Executive Summary

This plan executes the remaining ~45 weeks of the 24-month IPE Master Blueprint. The codebase has completed the equivalent of Months 1-6 (Sprints 1-3 fully, Sprints 4-5 partially, ~65/100 readiness). The plan closes all gaps across 12 phases to reach ≥85/100 readiness and full BRD/PRD v5.0 compliance.

**Total estimated effort**: 45 weeks (11 months)
**Team**: 4-6 engineers (backend, frontend, DevOps, ML)
**Risk-adjusted timeline**: 52 weeks (including 7 weeks buffer)

---

## Phase Overview

| Phase | Focus Area | Sprints | Weeks | Readiness Delta | Cost (est. engineer-weeks) |
|-------|-----------|---------|-------|-----------------|---------------------------|
| **0** | Quick-Win P0 Fixes | — | 1 | 65→70 | 4 |
| **1** | Complete Partial Sprints | S4-S5 | 4 | 70→75 | 16 |
| **2** | Enterprise IAM | S7 | 4 | 75→78 | 20 |
| **3** | Enterprise Solver | S6 | 3 | 78→80 | 14 |
| **4** | ESG Microservices | S11 | 6 | 80→83 | 30 |
| **5** | Strategic & Financial | S9 | 4 | 83→85 | 18 |
| **6** | Digital Twin & War Room | S10 | 4 | 85→87 | 18 |
| **7** | MLOps Pipeline | S8 | 4 | 87→88 | 20 |
| **8** | Multi-ERP & Edge | S12 | 4 | 88→89 | 20 |
| **9** | Chaos & Compliance Testing | S13-S14 | 6 | 89→91 | 24 |
| **10** | UAT & Change Management | S15 | 4 | 91→93 | 16 |
| **11** | Production Go-Live | S16 | 2 | 93→95+ | 10 |
| | **Buffer** | — | 7 | — | — |
| | **Total** | **16** | **52** | **65→95** | **~200** |

---

## Dependency Graph

```
Phase 0 (Quick Fixes)
  │
  ▼
Phase 1 (Complete Partial Sprints) ──────────────────────────┐
  │                                                            │
  ├──► Phase 2 (Enterprise IAM) ──► Phase 3 (Enterprise Solver)│
  │                                                            │
  └──► Phase 4 (ESG Microservices) ────────────────────────────┤
  │                                                            │
  ▼                                                            │
Phase 5 (Strategic & Financial) ────┐                          │
  │                                  │                          │
  ▼                                  ▼                          ▼
Phase 6 (Digital Twin)          Phase 7 (MLOps)
  │                                  │
  └──────────────────┬───────────────┘
                     ▼
              Phase 8 (Multi-ERP & Edge)
                     │
                     ▼
              Phase 9 (Chaos & Compliance)
                     │
                     ▼
              Phase 10 (UAT & Change)
                     │
                     ▼
              Phase 11 (Production Go-Live)
```

**Critical Path**: Phase 0 → 1 → 2 → 3 → 5 → 6 → 8 → 9 → 10 → 11 (35 weeks)
**Parallel Tracks**: Phase 4 (ESG) and Phase 7 (MLOps) can run in parallel with Phase 5-6

---

## Resource Requirements

### Team Composition

| Role | Phase 0-1 | Phase 2-4 | Phase 5-8 | Phase 9-11 |
|------|-----------|-----------|-----------|------------|
| Backend Engineer (Python/FastAPI) | 2 | 2 | 2 | 1 |
| Frontend Engineer (React/TypeScript) | 1 | 1 | 1 | 1 |
| DevOps/Platform Engineer | 1 | 1 | 1 | 1 |
| ML/AI Engineer | — | — | 1 | — |
| **Total** | **4** | **4** | **5** | **3** |

### Infrastructure Requirements

| Resource | Spec | Qty | When |
|----------|------|-----|------|
| Dev PostgreSQL 16 | 2 vCPU, 4GB RAM | 1 | Phase 0+ |
| Dev Kafka 7.7+ | 3-broker cluster | 1 | Phase 0+ |
| Dev Redis 7 | 2 vCPU, 2GB RAM | 1 | Phase 0+ |
| Keycloak 22+ | 2 vCPU, 4GB RAM | 1 | Phase 2 |
| Gurobi License | Floating | 1 | Phase 3 |
| MLflow + Airflow | 4 vCPU, 8GB RAM | 1 | Phase 7 |
| K3s Edge Cluster | 4 vCPU, 8GB RAM | 1 | Phase 8 |
| K6 + Chaos Mesh | 2 vCPU, 4GB RAM | 1 | Phase 9 |
| Prod EKS Cluster | 8 vCPU, 32GB RAM | 1 | Phase 11 |
| Prod RDS Multi-AZ | 4 vCPU, 16GB RAM | 1 | Phase 11 |
| Prod MSK | 3-broker | 1 | Phase 11 |

---

## Risk Register

| ID | Risk | Probability | Impact | Mitigation | Phase |
|----|------|------------|--------|------------|-------|
| R1 | Gurobi license procurement delays | Medium | High | Start procurement in Phase 1; fallback to OR-Tools heuristic | 3 |
| R2 | SAML/SCIM IdP integration delays (customer-specific) | High | Medium | Document integration steps per IdP; use Auth0 as universal bridge | 2 |
| R3 | K3s edge hardware procurement | Medium | Medium | Use Docker Compose as edge fallback; test on Raspberry Pi class hardware | 8 |
| R4 | Chaos Mesh conflicts with production workloads | Low | High | Run chaos in isolated staging environment; never in prod | 9 |
| R5 | SOC 2 auditor findings requiring rework | Medium | High | Engage auditor early (Phase 4); implement controls per their checklist | 9 |
| R6 | Customer UAT delays (30-day shadow required) | High | Medium | Start shadow mode in Phase 5 (Strategic); collect data for 90+ days | 10 |
| R7 | MLflow/Airflow learning curve | Medium | Low | Allocate 1 week spike in Phase 7 plan | 7 |
| R8 | SAP/D365 API changes during adapter development | Medium | Medium | Use OData/BAPI version pinning; integration tests run against sandbox | 8 |
| R9 | ArgoCD GitOps learning curve | Medium | Low | DevOps engineer ramp-up in Phase 8; use Helm as fallback | 11 |
| R10 | BYOK KMS cross-region latency | Low | Medium | Cache DEK in-memory with 1h TTL; benchmark before production | 9 |

---

## Detailed Phase Plans

### Phase 0: Quick-Win P0 Fixes (Week 1)

**Goal**: Close remaining P0 gaps from the V2 audit that are quick to fix (~1 day each).

| Task | Deliverable | Effort | Dependencies | Constitution Check |
|------|------------|--------|-------------|-------------------|
| Mount /metrics on all 11 services | Prometheus endpoint returning valid metrics on each service | 2 days | None | §VI.1 |
| Add structured JSON logging middleware | All services log JSON with correlation_id, service_name, duration_ms | 1 day | None | §VI.2 |
| Fix cdm_user seed (password_hash column) | Seed runs without error; user created | 0.5 day | None | — |
| Fix cdm_location table reference in seed-data.sh | Seed runs Inventory section without error | 0.5 day | None | — |
| Resolve StrEnum deprecation warnings | Clean `uv run ruff check` | 0.5 day | None | — |

**Verification**: `docker compose up -d` → `curl localhost:800X/metrics` returns Prometheus output on all 11 services. Seed script completes without error.

**Rollback**: Revert commits; previous state was non-functional for metrics anyway.

---

### Phase 1: Complete Partial Sprints (Weeks 2-5)

**Goal**: Complete Sprints 4 and 5 to 100%. These are the closest-to-complete items.

#### Sprint 4 Completion — Copilot, Shop Floor PWA, Shadow Mode (Weeks 2-3)

| Task | Deliverable | Effort | Spec Ref |
|------|------------|--------|----------|
| Complete Shop Floor PWA offline-first (Service Worker + IndexedDB) | Full offline capability: cache work orders, queue delay reports, sync on reconnect | 5 days | FR-501, SC-014 |
| Add Voice-to-Text delay reporting (Web Speech API) | Operator speaks delay details → transcribed → sent as text via PWA | 2 days | US9 |
| Enhance Shadow Mode validation engine | Shadow dashboard compares AI predictions vs human actuals; statistical report | 3 days | US9 (Shadow) |
| Complete nlp-svc SSE streaming edge cases | Copilot handles timeout, cancellation, error recovery | 2 days | — |

**VERIFY Gate** (Sprints.txt S4-V1): Sever network to PWA tablet → delay reports cache locally and sync via idempotent batch IDs on reconnection.

#### Sprint 5 Completion — XAI & Security Core (Weeks 4-5)

| Task | Deliverable | Effort | Spec Ref |
|------|------------|--------|----------|
| Standardize XAI payload across all AI APIs | Every AI response (fea-svc, res-svc, cap-svc, mat-svc, dpe-svc) includes `xai_explanation` with constraints, assumptions, confidence | 4 days | FR-012 (part), US2 |
| Add RBAC to remaining services | mat-svc, cap-svc, fea-svc, res-svc, rec-svc enforce `require_roles` on POST/PUT/PATCH/DELETE | 3 days | FR-012, SC-006 |
| Deploy & configure Kong API Gateway | Kong routes traffic; rate limiting (100 req/min per tenant); Lua plugin strips spoofed X-Tenant-ID | 3 days | FR-301 |
| Run full RLS audit + close gaps | Verify all 46+ tables have RLS; add where missing | 2 days | FR-002, SC-002 |
| Verify 100% endpoints return 401 without JWT | Automated endpoint scan across all services | 2 days | FR-003, SC-003 |

**VERIFY Gate** (Sprints.txt S5-V1): Approve MO with outdated `version` → API returns `409 Conflict`.

**VERIFY Gate** (Sprints.txt S5-V2): Query Tenant B data with Tenant A JWT → 0 rows returned.

---

### Phase 2: Enterprise IAM (Weeks 6-9)

**Goal**: Complete Sprint 7 — OAuth 2.1, SAML 2.0 SSO, SCIM 2.0 provisioning, tiered LLM, PII stripping.

| Task | Deliverable | Effort | Spec Ref | Dependencies |
|------|------------|--------|----------|-------------|
| Deploy Keycloak 22+ as OAuth 2.1/OIDC provider | Keycloak container; realm, clients, users configured | 3 days | FR-008 | Phase 1 Kong |
| Migrate JWT validation from HS256 to JWKS | All services validate via Keycloak JWKS endpoint | 3 days | FR-002 | Keycloak deployed |
| Configure SAML 2.0 SSO for Azure AD / Okta | Users can log in via corporate IdP; IdP-initiated and SP-initiated flows | 4 days | FR-009 | Keycloak deployed |
| Implement SCIM 2.0 endpoints (Users, Groups, Schemas) | SCIM provisioning: create/update/delete users and groups; map to IPE RBAC roles | 5 days | FR-010 | Keycloak deployed |
| Configure mTLS between all services (Istio) | PeerAuthentication STRICT; cert-manager for auto-rotation | 3 days | FR-011 | — |
| Implement tiered LLM routing (Anthropic / SageMaker / vLLM) | nlp-svc routes based on tenant tier: Tier 1 → Anthropic (PII-stripped), Tier 2 → SageMaker, Tier 3 → local vLLM | 4 days | FR-008 (part) | — |
| Build PII stripping middleware (Presidio) | Regex + NER anonymization for names, emails, SSNs before LLM prompts | 3 days | — | — |

**VERIFY Gate** (Sprints.txt S7-V1): Send prompt with fake SSN to Tier 1 → LLM receives `[REDACTED]`.

**VERIFY Gate** (Sprints.txt S7-V2): Trigger SCIM delete event → user's active JWT invalidated within 5s.

---

### Phase 3: Enterprise Solver (Weeks 10-12)

**Goal**: Complete Sprint 6 — ISolver abstraction, Gurobi/CPLEX, k6 SLO enforcement.

| Task | Deliverable | Effort | Spec Ref | Dependencies |
|------|------------|--------|----------|-------------|
| Define and implement `ISolver` interface | `solve(context, constraints) -> ScheduleResult` base class | 2 days | — | Phase 1 |
| Implement `ORToolsSolver` wrapping existing CP-SAT | Existing scheduler refactored to implement ISolver | 2 days | — | — |
| Implement `GurobiSolver` adapter | Gurobi Python API integration with license check; graceful fallback on missing license | 4 days | — | Gurobi license |
| Implement `CPLEXSolver` adapter (optional) | CPLEX Python API integration | 2 days | — | CPLEX license |
| Write k6 load test suite for CI | 200 concurrent Monte Carlo runs; p95 < 5s threshold | 3 days | — | — |
| Configure HPA based on load test results | Autoscaling thresholds tuned for mat-svc, cap-svc, fea-svc | 2 days | — | k6 results |

**VERIFY Gate** (Sprints.txt S6-V1): Mock Gurobi license failure → system falls back to OR-Tools/Heuristic.

**VERIFY Gate** (Sprints.txt S6-V2): k6 p95 latency < 5s; HPA scales mat-svc pods automatically.

---

### Phase 4: ESG Microservices (Weeks 13-18)

**Goal**: Complete Sprint 11 — sustain-svc, quality-svc, scn-svc. These are the 3 microservices missing from the BRD/PRD's 13-service architecture.

#### Sustain-svc (Weeks 13-14)

| Task | Deliverable | Effort | Spec Ref |
|------|------------|--------|----------|
| Create sustain-svc FastAPI service | Scaffold with shared library, health/ready/metrics, Dockerfile, tests | 1 day | FR-101 |
| Implement circular supply chain models | Recycling rates, take-back programs, material recovery models | 4 days | FR-101 |
| Implement end-of-life planning | EOL date prediction, obsolescence scoring per product/BOM | 3 days | FR-102 |
| Implement recyclability scoring | Per-product/BOM recyclability percentage, disassembly cost | 3 days | FR-103 |
| Kafka events | `ipe.sustainability.circularity_scored`, `ipe.sustainability.eol_planned` | 2 days | FR-104 |
| Frontend: Sustainability dashboard | Carbon footprint, circularity score, EOL timeline | 4 days | US4 |

**VERIFY Gate** (extended from Sprints.txt S11): POST /sustainability/circularity-score returns valid recyclability % + disassembly cost.

#### Quality-svc (Weeks 15-16)

| Task | Deliverable | Effort | Spec Ref |
|------|------------|--------|----------|
| Create quality-svc FastAPI service | Scaffold with shared library, health/ready/metrics, Dockerfile, tests | 1 day | FR-109 |
| Implement SPC charts & control limits | X-bar, R, p-charts with configurable control limits (±3σ) | 4 days | FR-109 |
| Implement defect prediction | From quality event feed; predict defect probability per operation/MO | 4 days | FR-110 |
| Kafka events | `ipe.quality.spc_alert`, `ipe.quality.defect_predicted` | 2 days | — |
| Frontend: Quality dashboard | SPC charts, defect heat map, CP/CPK metrics | 4 days | US4 |

**VERIFY Gate**: Feed 100 quality events → SPC chart detects out-of-control condition triggers alert.

#### Scn-svc (Weeks 17-18)

| Task | Deliverable | Effort | Spec Ref |
|------|------------|--------|----------|
| Create scn-svc FastAPI service | Scaffold with shared library, health/ready/metrics, Dockerfile, tests | 1 day | FR-105 |
| Implement supplier scorecards | OTIF, quality (defect rate), cost (price competitiveness), sustainability score | 4 days | FR-105 |
| Implement RFQ/RFP workflow | Create → publish → respond → award lifecycle with status machine | 5 days | FR-106 |
| Implement multi-tier visibility | Supplier risk propagation (tier-2 → tier-1 impact) | 4 days | FR-107 |
| Kafka events | `ipe.scn.supplier_scored`, `ipe.scn.rfq_created`, `ipe.scn.risk_detected` | 2 days | FR-108 |
| Frontend: SCN Portal | Supplier list with scorecards, RFQ management, risk flags | 5 days | US5, SC-015 |

**VERIFY Gate** (Sprints.txt S11-V2): Log in as Supplier A → query Supplier B data → 403 Forbidden (RLS enforced).

---

### Phase 5: Strategic Planning & Financials (Weeks 19-22)

**Goal**: Complete Sprint 9 — S&OP module, Financial Translation Engine, Executive Dashboard.

| Task | Deliverable | Effort | Spec Ref | Dependencies |
|------|------------|--------|----------|-------------|
| Build S&OP ingestion API | Unconstrained sales pipeline ingestion; weekly bucket aggregation | 4 days | US10 (part) | Phase 1 |
| Implement macro-level OR-Tools S&OP solver | Weekly capacity constraints; solve < 10s for 52-week horizon | 5 days | — | — |
| Complete Financial Translation Engine | Map MO operations → GL cost centers; COGM, labor, energy, overhead, COPQ | 5 days | US10 (part) | Existing dpe-svc financial projection |
| Build Executive Dashboard | Strategic KPIs, P&L view, AI vs Manual OTD, what-if simulation | 6 days | FR-503, SC-016 | Financial engine complete |
| Build AI Trust Dashboard (preview) | Adoption, Accuracy, Impact scores; Override Nudge Modal | 4 days | FR-503 (part) | — |

**VERIFY Gate** (Sprints.txt S9-V1): S&OP simulation identifies capacity bottlenecks at monthly bucket level without timing out.

**VERIFY Gate** (Sprints.txt S9-V2): COGM calculation matches manual accounting spreadsheet within 0.01% tolerance.

---

### Phase 6: Digital Twin & War Room (Weeks 23-26)

**Goal**: Complete Sprint 10 — Recursive CTE digital twin, network-svc enhancements, War Room UX.

| Task | Deliverable | Effort | Spec Ref | Dependencies |
|------|------------|--------|----------|-------------|
| Design recursive CTE queries for multi-level BOM explosion | CTE queries that trace tier-2 supplier → MO delay in <2s | 3 days | — | Phase 1 DB |
| Build Digital Twin API | `GET /digital-twin/bom/{mo_id}` explodes BOM; `GET /digital-twin/supplier/{id}` traces downstream MOs | 4 days | — | CTE queries |
| Enhance network-svc for multi-echelon optimization | Transfer order optimization across regional capacity constraints | 4 days | — | Sprint 9 existing |
| Build War Room UX | Auto-aggregate impacted MOs during disruption event; Slack/Teams task assignment | 6 days | — | Digital Twin API |
| WebSocket-based disruption broadcast | Real-time updates to War Room dashboard on risk events | 3 days | — | Kafka events |

**VERIFY Gate** (Sprints.txt S10-V1): Simulate Tier-2 supplier delay → CTE identifies all downstream MOs in <2s.

**VERIFY Gate** (Sprints.txt S10-V2): Trigger simulated port strike → War Room aggregates impacted MOs + sends Slack alerts in <60s.

---

### Phase 7: MLOps Pipeline (Weeks 23-26, parallel with Phase 5-6)

**Goal**: Complete Sprint 8 — MLflow, Airflow, drift detection, model governance.

| Task | Deliverable | Effort | Spec Ref | Dependencies |
|------|------------|--------|----------|-------------|
| Deploy MLflow tracking server | S3-compatible artifact store; experiment tracking enabled | 2 days | FR-401 | — |
| Implement Airflow DAG: pATP retraining | Daily retrain Monte Carlo parameters from historical actuals | 3 days | FR-402 | MLflow deployed |
| Implement Airflow DAG: feasibility weight tuning | Weekly tune G1-G5 gate weights based on prediction accuracy | 3 days | FR-402 | MLflow deployed |
| Implement Airflow DAG: supplier scoring update | Monthly update supplier scorecards from recent performance | 3 days | FR-402 | scn-svc data |
| Implement drift detection | Monitor: NLP classifier accuracy, pATP reliability, feasibility score distribution; alert on >5% drift | 5 days | FR-403 | MLflow deployed |
| Build Model Registry + Approval Gate UI | Promote staging → production with Data Steward approval | 4 days | FR-404 | Drift detection |
| Build MLOps Dashboard | Experiment list, model registry, drift metrics | 3 days | — | All above |

**VERIFY Gate** (Sprints.txt S8-V1): Inject synthetic data drift → model flagged, blocked from auto-promotion, requires manual UI approval.

**VERIFY Gate** (Sprints.txt S8-V2): One-click rollback → inference endpoint switches to previous model version in <10s.

---

### Phase 8: Multi-ERP & Edge (Weeks 27-30)

**Goal**: Complete Sprint 12 — SAP/D365 adapters, K3s Edge Gateway, Federated Learning.

| Task | Deliverable | Effort | Spec Ref | Dependencies |
|------|------------|--------|----------|-------------|
| Build SAP S/4HANA adapter | BAPI/OData integration; map SAP tables → CDM; full load + delta sync | 5 days | — | Phase 1 connector pattern |
| Build D365 Business Central adapter | Dataverse/OData with ETag retry; map D365 → CDM | 5 days | — | Phase 1 connector pattern |
| Build K3s Edge Gateway | SQLite local cache; store-and-forward sync; idempotency keys; <2s reconnection sync | 5 days | — | Kafka idempotency pattern |
| Implement Federated Learning DAG | Extract supplier metrics → SHA-256 hash → aggregate → share opt-in | 4 days | — | Airflow (Phase 7) |
| Edge health monitoring dashboard | K3s node status, sync lag, conflict rate | 3 days | — | Edge Gateway |

**VERIFY Gate** (Sprints.txt S12-V1): Simulate D365 409 ETag conflict → auto-retry merges without overwriting human changes.

**VERIFY Gate** (Sprints.txt S12-V2): Simulate network flap → Edge sync creates zero duplicate CDM records.

---

### Phase 9: Chaos & Compliance Testing (Weeks 31-36)

**Goal**: Complete Sprints 13-14 — Schemathesis, RLS bypass tests, k6 load, Chaos Mesh, SOC 2 evidence, BYOK, pen-test.

#### Sprint 13 — Chaos Engineering (Weeks 31-33)

| Task | Deliverable | Effort | Spec Ref |
|------|------------|--------|----------|
| Implement Schemathesis for all FastAPI endpoints | Fuzz testing; 0 unhandled 5xx errors; contract compliance | 4 days | — |
| Write 20-scenario parameterized cap-svc tests | Multi-level BOM, skill constraints, heuristic fallback validation | 3 days | — |
| Run k6 load test suite in CI | 200 concurrent Monte Carlo; p95 < 5s; auto-PR gate | 3 days | — |
| Deploy Chaos Mesh + write manifests | Kill Kafka leader, kill Postgres primary, kill Redis; validate Outbox+Edge recovery | 5 days | — |
| Validate <60s recovery from Postgres/Kafka kills | Transactional Outbox replay verified; zero data loss | 2 days | — |

**VERIFY Gate** (Sprints.txt S13-V1): Kill Postgres primary → auto-failover in <15s with zero data loss via Outbox.

**VERIFY Gate** (Sprints.txt S13-V2): Run Schemathesis → 0 unhandled 5xx errors on public endpoints.

#### Sprint 14 — Compliance (Weeks 34-36)

| Task | Deliverable | Effort | Spec Ref |
|------|------------|--------|----------|
| Implement append-only `cdm_audit_log` | `REVOKE UPDATE, DELETE` on audit table; all state changes logged | 3 days | FR-201 |
| Implement SOC 2 evidence collector | Automated collection: policies, implementation verification, monitoring output — all 6 trust principles | 5 days | FR-201, SC-012 |
| Implement GDPR DSAR API | Data subject access request; async export to S3 with signed URL | 4 days | FR-202, SC-013 |
| Implement data retention policies | Configurable per-entity TTL; auto-archive/delete | 3 days | FR-203 |
| Implement FDA 21 CFR Part 11 e-signature | User ID, NIST timestamp, signature meaning, full record; N-attempt lockout | 4 days | FR-204, FR-205 |
| Deploy BYOK KMS (AWS KMS) | Terraform; IAM policy denying root `kms:Decrypt` | 3 days | FR-301 (part) |
| Harden Kong API Gateway | Rate limiting, auth plugins, X-Tenant-ID spoof prevention | 2 days | FR-301 |
| Third-party penetration test | 0 Critical/High findings | 5 days | — |

**VERIFY Gate** (Sprints.txt S14-V1): Access Enterprise tenant DB using SaaS root AWS credentials → KMS policy returns `AccessDenied`.

**VERIFY Gate** (Sprints.txt S14-V2): Send request with fake `X-Tenant-ID` → Kong strips it and enforces JWT tenant ID.

---

### Phase 10: UAT & Change Management (Weeks 37-40)

**Goal**: Complete Sprint 15 — 30-day Shadow Mode validation, AI Trust Dashboard, Progressive Autonomy state machine, UAT sign-off.

| Task | Deliverable | Effort | Spec Ref | Dependencies |
|------|------------|--------|----------|-------------|
| Build `shadow_roi_validator.py` | `scipy.stats` OTD delta calculation; 95% CI; filters cancelled/scrapped MOs | 3 days | — | Historical data (30+ days) |
| Build AI Trust Dashboard | Adoption rate, accuracy per model, impact (OTD delta), Override Nudge Modal | 5 days | — | Shadow validator |
| Implement Progressive Autonomy state machine | States: Shadow → Suggest → Autonomous; per-tenant via LaunchDarkly | 4 days | — | Phase 1 RBAC |
| Implement synchronous safety guardrail | Feasibility < 85% → blocks ERP write-back synchronously | 3 days | — | fea-svc |
| Implement asynchronous Slack alert | Feasibility < 85% → Kafka event → Slack notification < 2s | 2 days | — | Guardrail |
| Conduct 30-day Shadow Mode validation with customer | Statistical report; UAT sign-off criteria: >10% OTD improvement at 95% CI | 30 days* | SC-012 | All above |

*\*30-day shadow runs concurrently with other phases; only the analysis and sign-off are in this phase's critical path.*

**VERIFY Gate** (Sprints.txt S15-V1): Set tenant to Autonomous, create MO with 82% feasibility → ERP write-back blocked synchronously, Slack alert arrives <2s.

**VERIFY Gate** (Sprints.txt S15-V2): Shadow validation script filters out cancelled/scrapped MOs to maintain statistical purity.

---

### Phase 11: Production Go-Live (Weeks 41-42)

**Goal**: Complete Sprint 16 — Terraform/ArgoCD provisioning, canary deployment, first autonomous MO, rollback validated.

| Task | Deliverable | Effort | Spec Ref | Dependencies |
|------|------------|--------|----------|-------------|
| Finalize Terraform for Prod EKS | Multi-AZ RDS, MSK, ElastiCache Redis, S3 for artifacts | 4 days | FR-301-FR-306 | All phases |
| Bootstrap ArgoCD `app-of-apps` | Dev/Staging/Prod environments; sync policies; auto-heal | 3 days | FR-301 | Terraform |
| Configure OpenTelemetry + Prometheus SLOs | RED metrics for all services; PagerDuty routing; SLO burn-rate alerts | 3 days | FR-003-FR-005 | Phase 0 |
| Design + test Argo Rollouts canary strategy | 5% → 25% → 100% based on error rate + latency | 4 days | — | ArgoCD |
| Execute "First Autonomous MO" synthetic test | MO flows ERP → dpe-svc → mat-svc → cap-svc → fea-svc → res-svc → connector → ERP; zero human clicks | 2 days | — | All services |
| Draft + test Rollback Runbook | Kong traffic shifting; bypass DNS TTLs; <15 min rollback | 2 days | — | — |
| Production readiness review | Dashboards live, alerts active, runbooks documented, team briefed | 1 day | SC-028 | All above |

**VERIFY Gate** (Sprints.txt S16-V1): Inject 5% error rate into canary → Argo Rollouts automatically halts and shifts 100% traffic back to stable in <2 minutes.

**VERIFY Gate** (Sprints.txt S16-V2): Verify `cdm_audit_log` captures `autonomous_confirmation` with exact AI rationale for the first autonomous MO.

---

## Constitution Compliance Matrix

Every phase MUST comply with the 6 binding principles from `.specify/memory/constitution.md`.

| Principle | Phase 0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | P11 |
|-----------|---------|----|----|----|----|----|----|----|----|----|-----|-----|
| **I. RLS** | ✓ Verify | ✓ Audit | ✓ SCIM-created tables | — | ✓ scn-svc RLS | — | ✓ CTE scoped | — | ✓ Edge RLS | ✓ Audit table RLS | — | ✓ Prod verify |
| **II. Auth** | ✓ /metrics fix | ✓ RBAC on 5 svcs | ✓ OAuth 2.1 JWKS | ✓ mTLS | ✓ scn-svc auth | ✓ Guardrail auth | — | ✓ Model API auth | ✓ Edge auth | ✓ E-sign auth | ✓ Autonomy auth | ✓ Prod verify |
| **III. Tests** | ✓ Quick tests | ✓ XAI + RBAC tests | ✓ Keycloak tests | ✓ k6 tests | ✓ 3 svc test suites | ✓ S&OP tests | ✓ CTE tests | ✓ Airflow tests | ✓ Edge tests | ✓ Chaos tests | ✓ Shadow tests | ✓ Canary tests |
| **IV. Events** | — | — | — | — | ✓ 6 new topics | ✓ S&OP events | ✓ Disruption events | ✓ Model events | ✓ Edge events | ✓ Outbox replay | ✓ Guardrail events | ✓ First MO audit |
| **V. Arch** | ✓ /metrics mount | ✓ Kong config | ✓ JWKS validation | ✓ ISolver interface | ✓ 3 svc scaffolding | ✓ S&OP API | ✓ Digital Twin API | ✓ MLflow API | ✓ SAP/D365 adapter | ✓ Append-only audit | ✓ Autonomy API | ✓ Prod infra |
| **VI. Observability** | ✓ /metrics + JSON logs | ✓ Kong metrics | ✓ Keycloak metrics | ✓ k6 dashboards | ✓ 3 svc dashboards | ✓ Exec dashboard | ✓ War Room | ✓ MLflow dashboards | ✓ Edge health | ✓ Chaos dashboards | ✓ Trust Dashboard | ✓ SLO alerts |

---

## Verification Strategy

### Per-Sprint VERIFY Gates

Each sprint has 2 VERIFY gates from `D:\AISOP\Sprints.txt`. These are MANDATORY — the sprint is not complete until both pass.

| Sprint | V1 | V2 |
|--------|----|----|
| 1 | Tenant isolation via raw SQL | MDR blocks at 50% BOM completeness |
| 2 | DLQ routes malformed message | Control Tower <2s update |
| 3 | 30s OR-Tools timeout fallback | PII stripped before LLM |
| 4 | Offline PWA sync via idempotent batch IDs | Shadow compares AI vs human (not AI vs AI) |
| 5 | 409 Conflict on stale version | 0 rows cross-tenant via spoof JWT |
| 6 | Graceful Gurobi license fallback | k6 p95 <5s + HPA scales |
| 7 | PII `[REDACTED]` before LLM | SCIM delete invalides JWT in 5s |
| 8 | Drift blocks auto-promotion | MLflow rollback in <10s |
| 9 | S&OP <10s solve | COGM within 0.01% tolerance |
| 10 | CTE identifies downstream MOs in <2s | War Room Slack alert in <60s |
| 11 | Outbox survives Kafka kill | SCN RLS blocks cross-supplier |
| 12 | D365 ETag conflict resolves | Edge sync zero duplicates |
| 13 | Postgres failover <15s, zero data loss | Schemathesis 0 unhandled 5xx |
| 14 | BYOK denies root kms:Decrypt | Kong strips spoofed X-Tenant-ID |
| 15 | Guardrail blocks <85% synchronously | Shadow filters cancelled MOs |
| 16 | Canary auto-rollback in <2min | Audit log captures autonomous_confirmation |

### Weekly Health Checks

| Check | Metric | Threshold | Action if Failed |
|-------|--------|-----------|-----------------|
| CI Pipeline | Tests passing | 100% | Block merge; fix or revert |
| SLO: API Latency | p95 response time | < 2000ms | Investigate bottleneck; HPA tuning |
| SLO: Error Rate | 5xx responses | < 0.1% | PagerDuty alert; rollback if >1% |
| Coverage | Unit test coverage | ≥ 40% | Add tests before new features |
| Security | Open vulnerabilities | 0 critical/high | Patch within 24h |
| Kafka Lag | Consumer lag per partition | < 1000 | Scale consumers; investigate consumer health |

### Release Gates

| Gate | Phase | Criteria |
|------|-------|----------|
| **Phase Gate** | End of each phase | All VERIFY gates pass; all FRs for that phase implemented; SCs met |
| **Staging Gate** | Before Phase 11 | Full E2E integration suite passes (15/15); k6 load test passes (p95 < 5s); Chaose experiments <60s recovery |
| **UAT Gate** | Phase 10 complete | 30-day Shadow Mode validation shows >10% OTD improvement (95% CI); customer UAT sign-off |
| **Production Gate** | Phase 11 step 1 | Security pen-test: 0 Critical/High; SOC 2 evidence collector: all 6 trust principles documented; Rollback Runbook tested |
| **Go-Live Gate** | Phase 11 step 5 | Canary passes automated gates; monitoring dashboards green; on-call rotation briefed |

---

## Rollback Strategy

| Phase | Rollback Action | RTO | RPO |
|-------|----------------|-----|-----|
| P0-P1 | Git revert + redeploy | 30 min | 0 (no data changes) |
| P2 (IAM) | Revert to HS256 JWTs; disable Keycloak | 1 hour | 5 min (active sessions lost) |
| P3 (Solver) | Revert to OR-Tools-only; ISolver returns OR-Tools | 30 min | 0 |
| P4 (ESG) | Remove new services from docker-compose/Helm | 15 min | 0 |
| P5 (S&OP) | Remove S&OP endpoints; revert to existing forecasting | 30 min | 1 hour (data in staging) |
| P6 (Digital Twin) | Remove CTE queries; revert to single-site planning | 30 min | 0 |
| P7 (MLOps) | Disable Airflow DAGs; pin model versions in MLflow | 1 hour | 1 DAG run |
| P8 (Multi-ERP) | Disable SAP/D365 adapters; fall back to Odoo-only | 1 hour | 5 min (sync data) |
| P9 (Chaos) | Disable Chaos Mesh; no infra rollback needed | 15 min | 0 |
| P10 (UAT) | Revert Autonomy to Suggest mode; disable guardrail | 15 min | 0 |
| P11 (Prod) | Kong traffic shift to stable; ArgoCD sync revert | 15 min | 5 min (in-flight MOs) |

---

## Appendix: Effort Breakdown by Engineer Type

| Role | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | P11 | **Total** |
|------|----|----|----|----|----|----|----|----|----|----|-----|-----|-----|
| Backend (Python) | 2 | 8 | 10 | 8 | 18 | 10 | 10 | 8 | 12 | 10 | 6 | 2 | **104** |
| Frontend (React) | 1 | 4 | 2 | — | 6 | 6 | 4 | 2 | 2 | — | 4 | — | **31** |
| DevOps/Platform | 1 | 2 | 6 | 4 | 2 | — | 2 | 4 | 4 | 10 | 2 | 6 | **43** |
| ML/AI | — | — | — | — | 2 | — | — | 6 | 2 | 2 | 2 | — | **14** |
| **Total** | **4** | **14** | **18** | **12** | **28** | **16** | **16** | **20** | **20** | **22** | **14** | **8** | **192** |

---

*This plan is a living document. Update VERIFY gate results, effort actuals, and risk status at the end of each phase. Re-baseline if any phase exceeds 120% of estimated effort.*
