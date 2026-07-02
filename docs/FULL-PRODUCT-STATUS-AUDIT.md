# IPE Full Product Status Audit

**Audit date:** 2026-06-30  
**Auditors:** Cross-functional product audit team (BA, Solution Architect, Integration, QA, DevOps, UX, Data)  
**Repository:** `E:\AISOP\ipe`  
**Evidence basis:** Live file inspection, `scripts/audit-metrics.py` (2026-06-30), demo run outputs, CI config, migrations — not memory.

---

## Executive Summary

IPE is a **mature demo platform (v8.2.0)** with **274 FastAPI endpoints** across **22 application microservices**, **206 Python test files**, documented **1110 passing backend tests** (2026-06-28), and **32/32 demo checkpoints** when the **full Docker stack** is running. **Release 1 (Odoo customer profile)** is **engineering-complete at 94/100** with live Odoo 19 sync validated, but **production SaaS is blocked** on Keycloak, live Stripe, SAP/D365 connectors, and enterprise hardening.

**Critical finding:** Documentation and Speckit pointers **conflict** on version (v6.0.0 vs v8.2.0 vs v9.0.0-r1) and demo score (20/20 vs 32/32). **Kong release1** misroutes `/api/v1/resolution` to `dpe-svc` (404) instead of `res-svc`.

---

# PART A — PRODUCT IDENTITY & BUSINESS STATUS

## A1. Product Identity Card

| Source | Path | Version | Readiness / Status | License |
|--------|------|---------|-------------------|---------|
| README | `README.md` L5–6 | **v8.2.0** (full) · **v9.0.0-r1** (Release 1 target) | 32/32 demo · 870+ tests · Star Trans UAT in progress | *(not stated in README)* |
| Product status | `docs/PRODUCT-STATUS.md` L1–6 | **v8.2.0** · 2026-06-28 | Speckit **100/100** · Demo **32/32** · 22 Kong backends · Production **POST-B** | — |
| Readiness | `READINESS.md` L10–16 | **v8.2.0** · 2026-06-27 | **100/100** Speckit · **~92/100** audit · **32/32** demo · **6/6** chaos · tags v1.0.0–v6.1.0; **v8.2.0 ready to tag** | — |
| IPE feature pointer | `ipe/.specify/feature.json` | **platform_release: v8.2.0** · **release_target: v9.0.0-r1** | **readiness_score: 94** · speckit converge complete · pending UAT/tag | — |
| Root feature pointer | `.specify/feature.json` (workspace root) | **release_target: v6.0.0** | **readiness_score: 97** · **live_demo_score: 20/20** · active: **005/004** | — |
| Git tags | `git describe --tags` | **BLOCKED** — dubious ownership on `E:/AISOP/ipe` | Cannot verify tagged version in this environment | — |

### Agreement matrix

| Field | README | PRODUCT-STATUS | READINESS | ipe/feature.json | Root feature.json |
|-------|--------|----------------|-----------|------------------|-------------------|
| Platform version | v8.2.0 | v8.2.0 | v8.2.0 | v8.2.0 | — |
| Release target | v9.0.0-r1 | — | v8.2.0 ready to tag | v9.0.0-r1 | v6.0.0 |
| Demo checkpoints | 32/32 | 32/32 | 32/32 | — | 20/20 |
| Readiness score | — | 100/100 | 100 / ~92 audit | 94 | 97 |
| Active feature | 013 (README link) | — | 010 closure | **013** | **005/004** |

**Verdict:** **CONFLICT** — operational truth is **v8.2.0 platform + 013 Release 1**; root `.specify/feature.json` and `AGENTS.md` are **stale (v6 era)**.

---

## A2. Feature Inventory (Speckit Traceability)

### `.specify/` inventory (28 files)

Root: `E:\AISOP\.specify\` — feature.json, extensions.yml, constitution, workflows, templates, agent-context extension.  
IPE-local: `E:\AISOP\ipe\.specify\` — feature.json, memory/constitution.md v1.1.0.

### `specs/` inventory

**128 files** under `E:\AISOP\ipe\specs\` across **14 numbered feature directories** (000–013, plus 011 analyze-only).

| Spec ID | Title | Status (from spec/analyze) | Key deliverables | Gaps |
|---------|-------|---------------------------|------------------|------|
| 000 | Project Completion / BRD alignment | 85/100 reconciled | Platform baseline | Historical |
| 001 | Production Readiness Convergence | Superseded | plan.md only | No spec.md |
| 002 | Release Stabilization Gates | Approved; gates passed | CI, chaos, k6 evidence | T049–T053 hygiene open per gap analysis |
| 003 | Autonomous Planning V5 | Complete (v1.0.0) | 45/45 tasks | — |
| 004 | AI-First V6 | Implemented 54/55 | V6-R1–R5 features | T055 tag checkbox drift |
| 005 | Program Status | Active | Whole-program rollup | Demo score 20 vs 32 in analyze |
| 006 | Module Hub Consolidation | Implemented | Hub UI refactor | — |
| 007 | v8 Phase 1 Foundation | Implemented MVP | Copilot sessions, demand, scenario | — |
| 008 | v8 Phase 2 Expansion | Implemented MVP | Supply, order, equipment | — |
| 009 | v8 Phase 3 Design & Procurement | Implemented MVP | Design AI, procurement APIs | — |
| 010 | v8 Validation Convergence | Active complete | 98/100 speckit · 30/30 demo in analyze | Score drift vs 32/32 |
| 011 | Keycloak SSO | POST-B analyze only | Scaffold docs | Not activated |
| 012 | Star Trans Client Demo | Implementing | Seed overlay, hybrid runbook | — |
| 013 | Release 1 Odoo + MENA | **94/100** converge · UAT blocked | Odoo sync, release1 compose, Arabic MVP, vault creds | T002 SOW, T071 UAT, T073 tag |

**Specs without full implementation evidence:** 001 (plan only), 011 (POST-B scaffold), commercial items in 013 (T002, T086, T071).

---

## A3. Business Capability Map

| Business Capability | Speckit Spec(s) | Service(s) | Demo CP | Maturity |
|---------------------|-----------------|------------|---------|----------|
| Demand Planning & Forecasting | 004, 007, 008 | demand-svc, dpe-svc | CP21–22 | **Functional** (API + tests; needs full stack) |
| Supply Network Planning | 008 | supply-svc, network-svc | CP25 | **Functional** |
| Scenario Planning & What-If | 007, 004 | scenario-svc, cap-svc/scenarios | CP23–24 | **Functional** |
| Order Management (ATP/CTP) | 008 | order-svc, fea-svc | CP26 | **Foundation→Functional** |
| Production Capacity Planning | 003, 004 | cap-svc (OR-Tools) | CP4, CP15 | **Enterprise-Ready** (demo); **Production-Blocked** (MDR gate) |
| Material Requirements Planning | 003 | mat-svc, dpe-svc | CP14 | **Functional** |
| Procurement & Sourcing | 009 | procurement-svc, scn-svc | CP29, CP6 | **Functional** |
| Predictive Maintenance / Equipment | 008, 004 V6-R4 | equipment-svc, cap-svc/iot | CP27, CP20 | **Functional** |
| Sustainability Analytics | v7 | sustain-svc | CP31 | **Functional** |
| Quality Management | v7 | quality-svc | CP32 | **Functional** |
| AI Copilot / Role Assistants | 007 | nlp-svc | CP10–11, CP30 | **Functional** (full stack); **Not in release1** |
| NLP / NL Planning | 007 | nlp-svc orchestrator | CP10–11 | **Functional** |
| Alerting & Notifications | 004 | alert-svc | CP9, CP20 | **Functional** |
| ML Model Management | 003 | ml-svc, mlflow compose | CP — partial | **Foundation** (ml-svc **not Kong-routed**) |
| **Odoo ERP Integration (R1)** | **013** | **connector**, cap-svc direct | **Act 0 hybrid** | **Enterprise-Ready** (live sync validated 2026-06-30) |
| Feasibility / Control Tower | 003, 013 | fea-svc | CP1–2 | **Enterprise-Ready** |
| Resolution / Mitigation | 003 | res-svc | CP3 | **Production-Blocked** on release1 Kong route |
| Executive / OTD / ROI | 013 | dpe-svc analytics | CP7–8, CP12–13 | **Functional** |

---

## A4. Competitive Positioning vs SAP IBP / Joule

**Primary sources:** `docs/PRD-IPE-v8.2.0-ENTERPRISE.md` L296–314, `docs/PRD-IPE-COMPREHENSIVE-AS-IS.md` L943–959.

| SAP IBP Area | IPE Status | Evidence | Maturity |
|--------------|------------|----------|----------|
| Demand Planning | ⚠️ Partial | demand-svc, dpe-svc `/demand/*`; CP21–22 | Functional demo |
| Supply Planning | ⚠️ Partial | supply-svc, network-svc; CP25 | Functional |
| S&OP / Executive | ⚠️ Partial | Executive dashboard, SOP APIs in dpe-svc | Functional |
| Inventory Optimization | ⚠️ Partial | mat-svc, inventory APIs | Functional |
| Response & Supply (ATP/CTP) | ⚠️ Partial | fea-svc queue, order-svc | R1: Odoo MO sync |
| Advanced Scheduling | ✅ Parity (niche) | cap-svc OR-Tools, CPM cascade CP19 | Strong vs Excel+Odoo |
| NL Copilot (vs Joule) | ✅ Parity (shadow) | nlp-svc role agents (`role_agents.py`) | Hidden in release1 |
| Live SAP ERP integration | ❌ Gap | `SAPConnector` → `NotImplementedError("POST-B")` in `connector/app/erp/base.py` | Scaffold |
| Multi-echelon network optimization | ❌ Gap | network-svc basic; not IBP-grade | Foundation |

### Top 3 competitive gaps for enterprise deals

1. **Live SAP S/4HANA / IBP connector** — only CDM mappers + sandbox scripts (`services/connectors/sap_adapter/`).
2. **Enterprise IdP (SSO/SAML/SCIM)** — Keycloak scaffold only (`ipe_shared/auth/keycloak.py` POST-B).
3. **Proven multi-site / multi-plant benchmarks** — single-VM release1 profile; no published IBP-scale performance baselines.

---

## A5. Revenue Readiness

| Criterion | Evidence | Status |
|-----------|----------|--------|
| Billing system | `ipe_shared/billing/stripe_adapter.py` — mock default; live `NotImplementedError` POST-B | **Scaffold only** |
| Multi-tenancy + RLS | 36 migrations; RLS in 15 files; `tenant_id` on CDM tables; tests `test_rls_isolation.py` | **Implemented** |
| User management beyond JWT | Local JWT in `dpe-svc/app/api/v1/auth.py`; Keycloak POST-B | **Demo auth only** |
| Tenant provisioning | `scripts/provision-tenant.sh` | **Script exists** |
| Usage metering | `ipe_shared/billing/metering.py` | **Scaffold** |
| Rate limits | Kong `rate-limiting` plugin in `kong.yml` L4–8 | **Full stack only** |
| Odoo customer path | release1 compose, smoke 7/7, live sync | **UAT-ready** |

**Verdict:** **Demo-ready** (full stack) · **UAT-ready** (Release 1 + Odoo) · **Not SaaS-ready** · **On-prem viable** (release1 compose, 8 GB VM notes).

---

# PART B — TECHNICAL ARCHITECTURE STATUS

## B1. Service Inventory (COMPLETE)

**Source:** `infrastructure/docker/docker-compose.yml` (878 lines). **35 compose services**, **22 application microservices** built from `services/`.

| # | Service | Image/Base | Internal Port | Host Port | Health Check | Notes |
|---|---------|------------|---------------|-----------|--------------|-------|
| 1 | db | postgres:16 | 5432 | 5433 | pg_isready | — |
| 2 | redis | redis:7.2-alpine | 6379 | 6380 | redis-cli ping | — |
| 3 | zookeeper | confluent | 2181 | — | none | — |
| 4 | kafka | confluent | 9092 | 9092 | none | — |
| 5 | dpe-svc | python:3.12 build | 8001 | 8020 | /api/v1/health | Core platform |
| 6 | mat-svc | build | 8002 | 8002 | health | — |
| 7 | cap-svc | build | 8003 | 8003 | health | OR-Tools |
| 8 | fea-svc | build | 8004 | 8004 | health | — |
| 9 | res-svc | build | 8005 | 8005 | health | **Not in release1 compose** |
| 10 | del-svc | build | 8006 | 8006 | health | — |
| 11 | nlp-svc | build | 8007 | 8007 | health | Copilot |
| 12 | rec-svc | build | 8008 | 8008 | health | — |
| 13 | connector | build | 8009 | 8011 | health | Odoo |
| 14 | alert-svc | build | 8010 | 8010 | health | — |
| 15 | scn-svc | build | 8014 | 8014 | health | — |
| 16 | network-svc | build | 8015 | 8015 | health | — |
| 17 | ml-svc | build | 8016 | 8016 | health | **Not in kong.yml** |
| 18 | sustain-svc | build | 8012 | 8012 | health | — |
| 19 | quality-svc | build | 8013 | 8013 | health | — |
| 20 | demand-svc | build | 8040 | 8040 | health | — |
| 21 | scenario-svc | build | 8050 | 8050 | health | — |
| 22 | supply-svc | build | 8060 | 8060 | health | — |
| 23 | order-svc | build | 8070 | 8070 | health | — |
| 24 | equipment-svc | build | 8061 | 8061 | health | — |
| 25 | material-svc | build | 8090 | 8090 | health | — |
| 26 | procurement-svc | build | 8100 | 8100 | health | — |
| 27 | kong | kong:3.7 | 8000, 8001 | 8000, 8001 | none | Gateway |
| 28 | keycloak | quay.io/keycloak | 8080 | 8180 | curl ready | POST-B |
| 29 | ollama | ollama | 11434 | 11434 | ollama list | LLM local |
| 30 | airflow + scheduler | apache/airflow | 8080 | 8080 | health | — |
| 31 | otel-collector | otel | 4317–4318 | exposed | none | — |
| 32 | jaeger | jaeger | 16686 | exposed | none | — |
| 33 | mlflow | mlflow | 5000 | 5000 | none | — |
| 34 | migrate | alembic job | — | — | none | — |

**Release 1 profile:** `docker-compose.release1.yml` — **8 services** (db, redis, kong, dpe-svc, fea-svc, cap-svc, connector, web-ui).

### Kong vs Compose mismatches

- **In compose, NOT in kong.yml:** `ml-svc` (8016)
- **In kong.yml, all 21 upstreams** map to compose services except ml-svc gap
- **release1 Kong bug:** `/api/v1/resolution` → `dpe-svc:8001` (`kong.release1.yml` L25–27) but resolution lives on **res-svc:8005** — causes **404** in demo (`docs/demo-data/startrans-full-demo.txt` L17)

---

## B2. Per-Service Deep Dive (Cards)

**Metrics from `scripts/audit-metrics.py` run 2026-06-30.** Endpoint counts = `@router.*` / `@app.*` decorators in `app/`.

```
══ dpe-svc (:8001) ══
Framework: FastAPI | Endpoints: 97 | LOC: 8,664 | Tests: 29 files / 170 funcs
Kafka: producer (demand.classified, tariff.shock) | Redis: yes | Auth: JWT + RBAC
RLS: via tenant middleware | Health: /api/v1/health
Issues: Largest API surface; dev password fallback when ENV != production (auth.py)

══ cap-svc (:8003) ══
Framework: FastAPI | Endpoints: 33 | LOC: 12,501 | Tests: 36 / 270
Kafka In: workcenter.status_changed, disruption.detected, maintenance.block_required
Kafka Out: schedule.approved, schedule.updated | Auth: RBAC
Issues: MDR quality gate blocks schedule when score < 70 (capacity.py L172–209) — 503 in demo

══ connector (:8009) ══
Framework: FastAPI | Endpoints: 9 | LOC: 3,765 | Tests: 9 / 48
Odoo: sync_engine.py (Release 1), odoo_adapter.py (REST), XML-RPC client
Kafka: consumes resolution.approved, schedule.approved, po.suggested, tariff.*
Issues: SAP/D365 stubs POST-B in erp/base.py

══ fea-svc (:8004) ══
Endpoints: 9 | LOC: 2,399 | Tests: 12 / 77
Publishes: ipe.mo.feasibility_scored | Core Release 1 scoring path

══ nlp-svc (:8007) ══
Endpoints: 7 | LOC: 4,587 | Tests: 15 / 137
Copilot role agents: planner, manager, supervisor, executive (role_agents.py)
Issues: Not in release1 compose

══ res-svc (:8005) ══
Endpoints: 5 | LOC: 1,000 | Tests: 4 / 23
Resolution scenarios API — required for CP3; missing from release1 Kong

══ mat-svc (:8002) ══
Endpoints: 14 | LOC: 4,329 | Tests: 15 / 121

══ alert-svc (:8010) ══
Endpoints: 9 | LOC: 1,375 | Tests: 7 / 25

══ demand-svc (:8040) ══
Endpoints: 7 | LOC: 797 | Tests: 4 / 12

══ scenario-svc (:8050) ══
Endpoints: 6 | LOC: 510 | Tests: 2 / 6

══ supply-svc (:8060) ══
Endpoints: 6 | LOC: 475 | Tests: 2 / 5

══ order-svc (:8070) ══
Endpoints: 5 | LOC: 430 | Tests: 2 / 5

══ equipment-svc (:8061) ══
Endpoints: 7 | LOC: 388 | Tests: 2 / 5

══ material-svc (:8090) ══
Endpoints: 6 | LOC: 429 | Tests: 2 / 6

══ procurement-svc (:8100) ══
Endpoints: 5 | LOC: 384 | Tests: 2 / 8

══ sustain-svc (:8012) ══
Endpoints: 6 | LOC: 774 | Tests: 4 / 25

══ quality-svc (:8013) ══
Endpoints: 6 | LOC: 803 | Tests: 3 / 21

══ scn-svc (:8014) ══
Endpoints: 11 | LOC: 1,368 | Tests: 4 / 54

══ network-svc (:8015) ══
Endpoints: 4 | LOC: 1,118 | Tests: 2 / 20

══ ml-svc (:8016) ══
Endpoints: 3 | LOC: 602 | Tests: 2 / 13
Issues: NOT exposed via Kong

══ del-svc (:8006) ══
Endpoints: 10 | LOC: 1,726 | Tests: 5 / 53

══ rec-svc (:8008) ══
Endpoints: 5 | LOC: 879 | Tests: 1 / 14

══ mock-odoo-api ══
Endpoints: 4 | LOC: 124 | Tests: 0 — test fixture service

══ ipe_shared (library, not a service) ══
LOC: part of 69,476 total scoped Python | Tests: 21+ files, 147 collected (135 pass, 12 skip)
Provides: auth, RBAC, KMS, odoo_credentials, billing scaffolds, observability
```

**Aggregate:** **274 endpoints** · **49,427 LOC** (services) · **69,476 LOC** (services+migrations+tests scoped).

---

## B3. API Gateway (Kong)

**Full config:** `infrastructure/kong/kong.yml` (368 lines)

| Plugin | Config |
|--------|--------|
| cors | origins localhost:3000, 5173, 8082 |
| rate-limiting | 300/min, 10000/hr |
| request-size-limiting | 10 MB |

**21 upstream services · 60 named routes.** JWT validation delegated to upstream services (no Kong JWT plugin in declarative file).

**Release 1:** `kong.release1.yml` (58 lines) — **4 upstreams**, **10 routes**, **cors only** (no rate-limit).

**Port drift:** README lists dpe-svc :8001; compose maps **8020:8001**.

---

## B4. Event-Driven Architecture (Kafka)

**Schema registry:** Confluent in compose (port 8083). Avro via `ipe_shared/events/schema_registry.py`.

### Topic catalog (representative — from codebase grep)

| Topic | Producer(s) | Consumer(s) | Notes |
|-------|-------------|-------------|-------|
| ipe.mo.feasibility_scored | fea-svc | res-svc (handler) | — |
| ipe.mo.auto_confirmed | fea-svc | connector | — |
| ipe.mo.capacity_scored | cap-svc | — | producer-only path |
| ipe.schedule.approved | cap-svc | connector | Odoo write-back |
| ipe.schedule.updated | cap-svc | — | — |
| ipe.resolution.approved | res-svc | connector | export queue |
| ipe.resolution.proposed | res-svc | — | — |
| ipe.demand.classified | dpe-svc | mat-svc | — |
| ipe.supply.delay_detected | mat-svc | — | — |
| ipe.supply.adjusted | demand-svc | — | — |
| ipe.supply.network.updated | demand-svc | — | — |
| ipe.po.suggested | mat-svc | connector | Odoo PO draft |
| ipe.tariff.shock | dpe-svc | connector | — |
| ipe.maintenance.block_required | cap-svc/iot | cap-svc consumer | — |
| ipe.disruption.detected | — | cap-svc | — |
| ipe.workcenter.status_changed | — | cap-svc | — |
| ipe.copilot.queried | nlp-svc | — | audit |

**Release 1:** Kafka **omitted by design** (`docker-compose.release1.yml`); synchronous HTTP paths documented in spec 013.

**Dead-letter:** Not uniformly configured per consumer; resilience via idempotent handlers in connector.

---

## B5. Caching Layer (Redis)

**Usage:** `ipe_shared/cache/redis_client.py`; session locks in sync; rate limiting via Kong (not Redis).

**Patterns:** Tenant-scoped keys in fea-svc scoring cache; no comprehensive key catalog in repo. **TTL:** set per call site — audit found no global stale-cache policy document.

---

## B6. Database Architecture

| Metric | Value |
|--------|-------|
| PostgreSQL instances | 1 (db service) |
| Migration files | **36** (`migrations/versions/001`–`036`) |
| Latest | `036_r1_odoo_sync_tables.py` — sync_run, data_quality_flag |
| RLS ENABLE statements | **18 occurrences in 15 migration files** |
| INSERT policy fixes | `033_v8_rls_insert_policies.py`, `035_legacy_rls_insert_policies.py` |
| Merge migration | `032_merge_migration_heads.py` |

**CDM tables:** 19+ core tables per constitution; tenant_id on MO, product, BOM, etc.

**Connection pooling:** SQLAlchemy async via `ipe_shared/database/connection.py`.

**Index coverage:** Partial — performance indexes in later migrations (e.g. chaos cost, telemetry).

---

## B7. Authentication & Authorization

### Auth flow

1. **Obtain token:** `POST /api/v1/auth/login` — `dpe-svc/app/api/v1/auth.py` — email/password → JWT access + refresh.
2. **Validate:** `ipe_shared/auth/dependencies.py` — Bearer token; `AUTH_PROVIDER=local|keycloak`.
3. **Claims:** sub, tenant_id, roles (via RBAC), exp.
4. **X-Tenant-ID:** Middleware `tenant_ctx` — must align with JWT tenant; RLS uses `app.current_tenant_id`.

### RBAC roles (9)

`admin`, `planner`, `supervisor`, `auditor`, `operator`, `manager`, `executive`, `procurement` — `ipe_shared/auth/rbac.py`.

### Keycloak

**Scaffold only** — `keycloak.py` L1: "POST-B activation required". Realm JSON in `infrastructure/keycloak/`.

### Cross-tenant

Tests: `test_rls_isolation.py`, `test_rbac_tenant_isolation.py`, `test_adversarial_rbac.py` (12 skipped without live IdP).

---

# PART C — INTEGRATION STATUS

## C1. ERP Connector Service

**Path:** `services/connector/app/` — 19 Python modules.

| Component | Path | Status |
|-----------|------|--------|
| Odoo XML-RPC sync | `odoo/sync_engine.py` | **Production** — full CDM upsert, DQ flags, rescore |
| Odoo REST adapter | `erp/odoo_adapter.py` | **Production** — `/ipe/api/v1/*` |
| Mock ERP | `erp/base.py` | **Functional** |
| SAP | `erp/base.py` SAPConnector | **Scaffold** — NotImplementedError POST-B |
| D365 | `erp/base.py` D365Connector | **Scaffold** |
| CDM mappers (offline) | `connectors/sap_adapter/`, `d365_adapter/` | **Mapper + tests only** |

**API routes:** `/sync/*`, `/erp/odoo/*`, `/health`, activate, action.

**Odoo addon:** `odoo-addons/ipe_connector/` + `ipe_connector/` for write-back receiver.

---

## C2. External System Integration Matrix

| System | Adapter Status | Data Flow | Auth | Last Tested |
|--------|----------------|-----------|------|-------------|
| **Odoo 17/19** | **Live** | Bi-directional (sync + activate) | XML-RPC + API key (addon) | **2026-06-30** — uid=2, full sync success |
| SAP S/4HANA | Mapper only | — | OData scaffold script | Sandbox report in specs/003 evidence |
| Microsoft D365 | Mapper only | — | OAuth scaffold | Sandbox report |
| Stripe | Mock default | Billing events | API key POST-B | test_stripe_billing.py |
| Keycloak | Scaffold | SSO | OIDC POST-B | test_auth_keycloak.py |
| PagerDuty / Alertmanager | Integrated | Outbound alerts | API keys env | alert-svc |
| Ollama / OpenRouter / Anthropic | LLM routing | Copilot | Env keys | nlp-svc tests |

---

## C3. File/Data Import-Export

| Capability | Status | Evidence |
|------------|--------|----------|
| XLSX import | ✅ | `cap-svc/app/core/project_plan_parser.py`, UI `ProjectPlanUpload.tsx` |
| CSV import | ⚠️ Orphan | `tariff_matrix_import.py` — no API wiring |
| CSV/XLSX export | ❌ | Not found in apps/web or APIs |
| Bulk API | ⚠️ Partial | Batch sync `/sync/run entity=all` |

---

# PART D — FRONTEND / UI/UX STATUS

## D1. Technology Stack

**Source:** `apps/web/package.json`

| Category | Choice | Version |
|----------|--------|---------|
| Framework | React | ^18.3.1 |
| Build | Vite | ^5.4.0 |
| Routing | react-router-dom | ^6.26.0 |
| State | Redux Toolkit + react-redux | ^2.2.7 / ^9.1.2 |
| Charts | recharts | ^3.8.1 |
| Styling | Tailwind CSS | ^3.4.9 |
| HTTP | axios | ^1.7.4 |
| Tests | Vitest + Playwright | ^2.0.5 / ^1.61.0 |

**Frontend LOC:** **9,933** (scoped `apps/web/src`).

---

## D2. Route & Page Inventory

**Router:** `apps/web/src/app/router.tsx` — **29 leaf pages**, 5 hub layouts, 18 legacy redirects, lazy-loaded via `React.lazy`.

Hubs: Planning (7 pages), Command Center (5), Supply Chain (6), AI & Governance (7), Platform (3), plus `/shop-floor`, `/login`.

**Release 1 profile:** `releaseProfile.ts` — hides supply-chain, ai-governance hubs when `VITE_RELEASE_PROFILE=release1`.

---

## D3–D8. UX Summary

| Area | Finding |
|------|---------|
| Components | 65 `.tsx` files; 14 shared in `src/components/`; 47 in `features/` |
| i18n | ✅ `lib/i18n.ts` — en/ar, RTL, localStorage; Release 1 wired on Login, Resolution, Control Tower |
| Design system | Tailwind + custom UI primitives (Button, Card, Badge, Table) — no Storybook |
| Code splitting | ✅ Lazy routes in router.tsx |
| API layer | Feature-scoped `api.ts` modules; axios; Kong proxy in release1 nginx |
| a11y | `@axe-core/playwright` in devDeps; limited aria audit coverage |
| Performance | Lazy loading yes; recharts bundle; no virtual scrolling audit |

**Demo UX evidence (release1 stack, 2026-06-30):** Control Tower **12 MOs** ✅; Resolution API **404** via Kong ❌; Schedule **503** MDR gate ❌.

---

# PART E — QUALITY ASSURANCE STATUS

## E1. Test Inventory

| Metric | Count | Source |
|--------|------:|--------|
| Python `test_*.py` files | **206** | audit-metrics.py |
| Python test functions (services) | **~1,110+** documented pass | docs/qa/full-test-suite-v8.2.0.txt |
| Frontend Vitest files | **14** | apps/web/tests/ |
| Playwright e2e specs | **5** | apps/web/e2e/ |
| Markdown docs | **238** | scoped exclude node_modules |

### Service test matrix (sample — full suite in qa log)

| Service | Unit test funcs | Documented pass (2026-06-28) |
|---------|----------------:|-----------------------------|
| cap-svc | 270 | 275 collected |
| dpe-svc | 170 | 180 |
| nlp-svc | 137 | 114 |
| mat-svc | 121 | 121 |
| fea-svc | 77 | 91 |
| shared | 156+ | 135 pass, 12 skip |
| connector | 48 | not in v8.2.0 suite job |

## E2–E3. Test Quality & Coverage

- **Fixtures:** conftest.py per service; shared `v8_conftest.py`
- **Skipped:** 12 shared integration (Kafka/adversarial without infra)
- **CI gap:** `.github/workflows/ci.yml` unit job runs **only shared, cap-svc, dpe-svc, nlp-svc**
- **Coverage:** Codecov upload for shared; no repo-wide 80% gate

## E4. E2E

5 Playwright specs: login, critical-path, copilot, demand-tab, supply-tab.

## E5. Chaos

**6/6 PASS** — `docs/chaos/chaos-summary.md`, scenarios C1–C6.

## E6. Performance

k6 scripts in `tests/performance/k6/` (8 files); CI job `continue-on-error: true`.

## E7. Demo Evidence

| Run | Date | Result |
|-----|------|--------|
| full-test-suite-v8.2.0.txt | 2026-06-28 | **1110 passed, 0 failed** |
| run-full-demo.ps1 (full stack documented) | — | **32/32** per READINESS |
| startrans-full-demo.txt | 2026-06-30 | **7/32** on release1 Kong (stack subset) |
| release1-integration-demo.txt | 2026-06-30 | **10/13** Odoo integration cycle |
| release1-smoke.ps1 | 2026-06-30 | **7/7 PASS** |

---

# PART F — SECURITY & COMPLIANCE STATUS

| Area | Status | Evidence |
|------|--------|----------|
| JWT signing | HS256 default; JWKS opt-in | jwt.py, JWT_USE_JWKS |
| Token storage (FE) | localStorage (typical SPA) | auth feature |
| Odoo creds | KMS encrypted (T081) | odoo_credentials.py |
| RLS tenant isolation | Implemented + tests | migrations 033, 035, 036 |
| Secrets in code | Dev defaults flagged | odoo_adapter api_key, keycloak CHANGE_ME |
| Vault/AWS SM | POST-B NotImplementedError | secrets_manager.py |
| GDPR DSAR | API scaffold | dpe-svc compliance routes |
| WCAG 2.1 AA | Not audited | — |
| SOC2 evidence | Module exists | compliance/evidence.py |
| Dependabot | CI/docs reference | security/dependabot.py |

---

# PART G — DEVOPS & DEPLOYMENT STATUS

## G1. Infrastructure

- **Compose files:** docker-compose.yml, release1.yml, demo.yml, ollama.yml, secrets.yml
- **Dockerfiles:** Per-service `services/*/Dockerfile`; web `Dockerfile.release1`
- **.dockerignore:** Present at repo root (202 bytes)
- **Non-root USER:** Not consistently set in Dockerfiles (audit spot-check)

## G2. CI/CD

**`.github/workflows/ci.yml`** — 10 jobs: lint, typecheck, test, integration, e2e, integration-e2e, service-dependencies, schemathesis, k6, release1-smoke.

## G3. Environment

- `.env.example`, `config/secrets.env.example`, `config/erp.env.example`, `config/keycloak.env.example`
- IPE_* prefix via pydantic-settings in shared config

## G4. Observability

- OpenTelemetry: otel-collector, jaeger in compose
- Prometheus metrics: `/metrics` on services via ipe_shared observability
- Structured JSON logging: ipe_shared/observability/logging.py
- Grafana dashboards referenced in docs

## G5. Backup / DR

No automated pg_dump in compose; DR runbooks partial in `docs/runbooks/`.

---

# PART H — DOCUMENTATION STATUS

## H1. Documentation Inventory

**238 markdown files** (scoped). Categories include: PRD (3 tiers), implementation playbooks, runbooks, integration Odoo guides, specs 000–013, chaos, qa evidence, ADRs in `docs/decisions/`.

**API reference:** `docs/api-reference.md` — endpoint index (may drift from 274 live routes).

**OpenAPI:** Per-service FastAPI auto-docs at `/docs` when running; no committed openapi.yaml at root.

## H2. Code Documentation

Type hints prevalent in FastAPI services. TODO/FIXME grep in scoped services+web: **0 matches** (audit-metrics.py) — low inline debt markers.

## H3. Onboarding

README quick start + Makefile targets. CONTRIBUTING not verified at root. Star Trans path documented in spec 013.

---

# PART I — CODE HEALTH & TECHNICAL DEBT

## I1. Code Metrics

| Language / Area | LOC |
|---------------|----:|
| Python (services) | 49,427 |
| Python (scoped total) | 69,476 |
| TypeScript/TSX (web src) | 9,933 |
| **Total application** | **~79,400** |

## I2. Shared Library

**`services/shared/ipe_shared/`** — auth, RBAC, KMS, database, events, billing, compliance, observability, odoo_credentials. Reduces duplication; 21 services depend on it.

## I3. Error Handling

Standard `APIResponse` schema in `ipe_shared/schemas/common.py` — `{success, data, error, meta}`.

## I4. Dead Code

- SAP/D365 connector stubs (intentional POST-B)
- `tariff_matrix_import.py` orphaned
- ml-svc not routed

## I5. Dependency Graph

**Hub services:** dpe-svc (97 endpoints), cap-svc (OR-Tools + Kafka hub), connector (ERP). **SPOF risk:** db, kong. Inter-service: primarily HTTP via Kong; Kafka for async mesh.

---

# PART J — CROSS-CUTTING CONCERNS

| Concern | Status |
|---------|--------|
| i18n | ✅ en/ar, RTL, Release 1 pages wired |
| Feature flags | unleash container in full compose; `ipe_shared/feature_flags/` |
| Audit trail | `cdm_sync_run`, audit service, compliance tables |
| Multi-currency | Partial — financial APIs; not full IBP-grade |

---

# PART K — DEFINITIVE STATUS SUMMARY

## K1. Scorecard

| Dimension | Score | Grade | Key Evidence | Critical Gap |
|-----------|------:|-------|--------------|--------------|
| Business Capability | 82 | B | 32/32 demo (full stack); R1 Odoo live | SAP/enterprise IdP |
| Technical Architecture | 85 | B | 22 svc, 274 endpoints, event mesh | release1 Kong resolution route |
| API Completeness | 88 | B | dpe-svc 97 routes; kong 60 routes | ml-svc unrouted |
| Database & Data | 86 | B | 36 migrations, RLS 15 files | MDR gate data quality |
| Integration Maturity | 72 | C | Odoo production; SAP/D365 scaffold | Live SAP connector |
| Frontend / UX | 80 | B | 29 pages, i18n, hubs | release1 subset UX |
| Test Coverage | 84 | B | 1110 pass documented; chaos 6/6 | CI runs 4/22 services |
| Security | 78 | C | RLS+RBAC; Odoo KMS | Keycloak, HS256 default |
| DevOps & Deploy | 81 | B | CI 10 jobs; compose profiles | DR backup automation |
| Documentation | 75 | C | 238 md files; PRD comprehensive | Version drift across artifacts |
| Code Health | 83 | B | 79k LOC; shared lib; low TODO | Port/README drift |
| Production Readiness | 68 | D | POST-B scaffolds | SaaS billing, SSO, SAP |
| **OVERALL** | **80** | **B** | Demo-strong; R1 UAT-ready; not enterprise SaaS |

*Scoring: A=90–100, B=75–89, C=60–74, D=0–59*

---

## K2. Open Issue Register (Top 25)

| # | Sev | Category | Issue | Component | Evidence | Effort |
|---|-----|----------|-------|-----------|----------|--------|
| 1 | P1 | Integration | release1 Kong routes `/resolution` to dpe-svc (404) | kong.release1.yml L25–27 | startrans-full-demo.txt L17 | S |
| 2 | P1 | Scheduling | MDR gate blocks schedule (503) when BOM score low | cap-svc/capacity.py L172 | release1-integration-demo L13 | M |
| 3 | P1 | Gateway | ml-svc not in kong.yml | kong.yml vs compose | PRODUCT-STATUS 22 vs 21 | S |
| 4 | P2 | Docs | Root `.specify/feature.json` stale v6.0.0 / 20/20 | .specify/feature.json | A1 matrix | S |
| 5 | P2 | Docs | README port map drift (8001 vs 8020) | README vs compose | B1 | S |
| 6 | P2 | CI | Unit tests only 4 services in CI | ci.yml test job | E1 | M |
| 7 | P2 | Security | Keycloak SSO not activated | keycloak.py POST-B | F1 | L |
| 8 | P2 | Security | Stripe live billing POST-B | stripe_adapter.py | A5 | L |
| 9 | P2 | Integration | SAP/D365 live connectors POST-B | erp/base.py | C1 | XL |
| 10 | P2 | Gateway | release1 Kong no rate-limit plugin | kong.release1.yml | B3 | S |
| 11 | P3 | DevOps | Git dubious ownership blocks tag verify | git CLI | A1 | S |
| 12 | P3 | DevOps | Kong compose depends_on incomplete | docker-compose.yml L796 | B1 | S |
| 13 | P3 | Data | Only 4 BOMs for tenant (MDR impact) | psql audit 2026-06-30 | C scheduling | M |
| 14 | P3 | UX | Full demo 7/32 on release1 stack expected | startrans-full-demo.txt | E7 | — |
| 15 | P3 | Integration | CSV tariff import orphaned | tariff_matrix_import.py | C3 | S |
| 16 | P3 | Export | No CSV/XLSX export APIs | C3 grep | C3 | M |
| 17 | P3 | Security | HS256 default JWT in dev | jwt.py | F1 | M |
| 18 | P3 | Observability | Kong no healthcheck in compose | B1 | G4 | S |
| 19 | P3 | Kafka | release1 omits Kafka by design | spec 013 | B4 | — |
| 20 | P3 | ML | mlflow in compose but ml-svc unrouted | B1/B3 | I4 | S |
| 21 | P4 | Docs | spec 013 header still 88/100 vs converge 94 | spec.md vs feature.json | A2 | S |
| 22 | P4 | Tests | 12 shared integration tests skipped | full-test-suite | E2 | M |
| 23 | P4 | Docker | cap-svc UV_HTTP_TIMEOUT needed on slow networks | cap-svc Dockerfile | DevOps | S |
| 24 | P4 | Commercial | T002 SOW unsigned | tasks.md 013 | A2 | Business |
| 25 | P4 | Commercial | T071 UAT pending | converge.md | A5 | Business |

---

## K3. Immediate Action Plan (Next Sprint)

### Must-Do (P0/P1)

1. **Fix release1 Kong resolution upstream** → route `/api/v1/resolution` to `res-svc:8005` OR embed proxy in dpe-svc — `infrastructure/kong/kong.release1.yml` — **2h**
2. **Unblock schedule demo: seed MDR-compliant BOM data or document gate bypass for demo tenant** — seed SQL / cap-svc threshold config — **4h**
3. **Sync Speckit pointers** — update root `.specify/feature.json`, `AGENTS.md`, README ports to v8.2.0/013 — **2h**
4. **Add res-svc to release1 compose** (optional service) for Resolution Center — `docker-compose.release1.yml` — **4h**

### Should-Do (P2)

5. Add ml-svc to kong.yml upstream + route — **2h**
6. Extend CI unit test matrix to fea-svc, connector, mat-svc — **1d**
7. Add rate-limiting to kong.release1.yml — **1h**
8. Tag v8.2.0 git release after fixing safe.directory — **1h**

### Nice-to-Do (P3/P4)

9. Wire CSV tariff import to API
10. Add data export endpoints for executive ROI
11. WCAG axe scan in CI

---

## K4. Strategic Recommendations (2–3 Sprints)

1. **Sprint 1 — Release 1 go-live:** Fix Kong routes, complete Star Trans UAT (T071), tag `v9.0.0-r1`. Do not expand platform scope.
2. **Sprint 2 — Production hardening:** Activate Keycloak in staging, HashiCorp Vault for secrets, HS256→RS256 JWT, CI full-service test matrix.
3. **Sprint 3 — Enterprise gap closure:** SAP OData connector MVP (customer #2), Stripe live billing, multi-site benchmark doc for IBP competitive deals.

**Architectural priority:** Maintain **hub-and-spoke Odoo** for R1; defer Kafka-in-R1 permanently per spec 013 `R2-ODOO-KAFKA-BACKLOG.md`.

---

## Appendix A — Audit Commands Run

```powershell
python E:\AISOP\ipe\scripts\audit-metrics.py
.\scripts\run-full-demo.ps1 -Profile startrans
.\scripts\run-release1-integration-demo.ps1
.\scripts\release1-smoke.ps1
.\scripts\seed-startrans-demo.ps1
git describe --tags  # FAILED dubious ownership
```

## Appendix B — Key File Index

| Artifact | Path |
|----------|------|
| Full compose | infrastructure/docker/docker-compose.yml |
| Release 1 compose | infrastructure/docker/docker-compose.release1.yml |
| Kong full | infrastructure/kong/kong.yml |
| Kong R1 | infrastructure/kong/kong.release1.yml |
| Odoo sync engine | services/connector/app/odoo/sync_engine.py |
| Copilot agents | services/nlp-svc/app/core/role_agents.py |
| Migrations | migrations/versions/ |
| Demo runner | scripts/run-full-demo.ps1 |
| QA evidence | docs/qa/full-test-suite-v8.2.0.txt |
| Metrics JSON | docs/demo-data/audit-metrics.json |

---

*End of audit — generated 2026-06-30 by cross-functional product audit team.*
