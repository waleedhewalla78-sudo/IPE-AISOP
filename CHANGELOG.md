# Changelog

All notable changes to the IPE platform are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

**Authoritative product spec:** [docs/PRD-IPE-AUTHORITATIVE.md](docs/PRD-IPE-AUTHORITATIVE.md)

---

## [Unreleased] — Spec 026 Phase 5 Planning-Command (Wave 1)

### Added
- Planning Cockpit, MPS, MRP explode, ATP/CTP/PTP promise, production leveling, RCCP/CRP, scenario cascade
- Command Center ops live, war room, shift handover, action tracker, performance cockpit, predictive 3/7/14d
- UI: `/planning/cockpit`, `/command-center/ops-live` with tool actions
- Kong R2: `/api/v1/planning-command`, `/api/v1/intelligence`
- Spec `026-phase5-planning-command`; report `docs/qa/PHASE5-EXECUTION-AND-TEST-REPORT.md`

### Tests
- Phase 5: **13/13 PASS** (`test_phase5_planning.py`)

### Honesty
- COM OPEN unchanged; collaborative UI / WhatsApp hub deferred; no live Odoo write-back claim

---

## [Unreleased] — Spec 025 Phase 4 Premium (Wave 1)

### Added
- Manufacturing Intelligence pulse (`GET /api/v1/intelligence/pulse`) with M1–M6 Command module shells
- Agents **A8–A12**: customer health/delay drafts, PO recommendations, CAPA, MO margin/decision P&L/cash sketch, carbon + supplier ESG
- Autonomous overnight rule engine with guardrails (A-customer block, PO caps, quality inspection add-only)
- Customer portal read-only page + `GET /api/v1/orders/portal/summary`
- UI routes `/intelligence/*` and `/customer-portal` (R2 sidebar)
- Speckit feature `specs/025-phase4-premium` + `docs/qa/PHASE4-EXECUTION-AND-TEST-REPORT.md`

### Tests
- Phase 4: **21 PASS** (dpe/order/quality/sustain/procurement); Phase 3 orchestrator regression 7 passed

### Honesty
- COM blockers remain OPEN; no live Odoo PH1-02 claim; Digital Factory polish deferred

---

## [Unreleased] — Spec 024 Phase 3 Ops Intelligence (Wave 1)

### Added
- Migrations **051–059** (agent activity, exceptions/SLA, upload history, demand signals, supplier_score Phase 3 ALTER, root-cause, predictions, auction log, batch groups)
- **upload-svc** (:8120): 5-phase onboarding wizard + multi-stage Excel/CSV validation + Kong R2 route
- Predictive risk scoring (fea-svc T+3/7/14) and 5-why root-cause analyzer
- Smart batching + capacity auction (cap-svc)
- Demand signal fusion (demand-svc); predictive stockout + supplier scorecard (mat-svc)
- Agent orchestrator + exception lifecycle + financial optioning (dpe-svc)
- Contextual Copilot morning brief / meeting prep (nlp-svc); S&OP executive brief (sop-svc)
- Frontend: Data Upload, Agents, Exceptions, Predictions, Root Cause, Supplier Scorecard, Meeting Prep (+ EN/AR i18n)

### Conflicts documented
- Migration 055 ALTERs existing `cdm_supplier_score` (041) instead of CREATE
- A5 generate-resolutions lives under `/api/v1/agents/*` (res-svc owns `/api/v1/resolution`)

### Tests
- Phase 3 new suites: **18/18 PASS** (fea/cap/demand/mat/dpe/nlp/sop/upload)
- Report: `docs/qa/PHASE3-EXECUTION-AND-TEST-REPORT.md`

### Deferred / OPEN (COM unchanged)
- Full CDM persist for every upload row; WhatsApp exception push; full S&OP 4-week UI
- OQ-7 / SOW / Odoo staging / G-R2-04 Arabic COM — **OPEN**

---

## [Unreleased] — Sprint 4 Wave 1 (Spec 023)

### Added
- Admin Odoo Config v2: `cdm_erp_connection` + audit log (migration 050, RLS), Fernet password encryption (`IPE_ENCRYPTION_KEY`), connector REST `/api/v1/erp/connections` (CRUD/test/activate/sync-now/logs)
- React `OdooConnectionsPage` + EN/AR i18n; Platform hub route `/platform/odoo-config`
- OTD Analytics polish: `OTDAggregator` (daily snapshot + historical backfill), extended `/api/v1/analytics/otd/*` endpoints, dashboard/nav for R1+R2

### Fixed
- Validate script write-back probe now uses canonical `POST /api/v1/sync/odoo/activate` (was bare `/api/v1/activate` → 404)
- OTD `SnapshotRequest.date` annotation shadowing that broke FastAPI route registration under tests

### Tests
- `services/connector/tests/test_erp_connections.py` — 9 passed
- `services/dpe-svc/tests/test_otd_analytics.py` — 6 passed

---

## [v9.2.0-planning] — 2026-07-11

### Added
- ABC/XYZ product segmentation engine (mat-svc, mig 044)
- Forecast quality tracking: MAPE, bias, MASE, stability, value-add (demand-svc, mig 045)
- ARIMA/SARIMA forecasters with best-fit auto-selection (demand-svc)
- Statistical safety stock calculator with segment-driven service levels (mat-svc, mig 047)
- Capacity utilisation alerts with configurable thresholds (cap-svc, mig 048)
- S&OP process engine with stage workflow and consensus calculation (sop-svc :8110, mig 049)
- Odoo lead time history sync + product cost/price fields (connector, mig 046)
- 9+ Copilot planning intelligence tools (nlp-svc)
- `scripts/planning-uat.ps1` — 12-step automated UAT

### Fixed
- Copilot tool-call chain timeout: concurrent tool execution, per-tool HTTP timeouts, LLM warm-up, 20s chat ceiling with tool-backed fallback
- ARIMA auto-order cold path: reduced grid (18 combos), 8s selection budget, SES-first guaranteed fallback, statsmodels warm-up

### Database
- Migrations 044–049: planning intelligence tables with RLS (043 reserved for Odoo config versioning)

### Tests
- 70+ planning-module unit tests across mat/demand/cap/connector/sop/nlp

---

## [v9.1.1-r2] — 2026-07-XX (PENDING: Arabic native QA sign-off)

### Added
- Release 2 profile: Copilot, Demand Sensing, Scenario Workbench in navigation (`VITE_RELEASE_PROFILE=release2`)
- 299+ Arabic i18n keys across 8+ screens with RTL layout
- Full R2 Kong routes: nlp-svc (read_timeout 300s), demand-svc, scenario-svc, mat-svc

### Validated
- Playwright desktop + R2: 22/22 PASS
- R2 smoke: 15/15 PASS
- R2 demo: 7/7 PASS
- k6 SLO: p95 293ms

### Pending
- G-R2-04 Arabic native speaker QA sign-off (`docs/qa/arabic-qa-r2.md`) — COM task, ENG env ready

---

## [Unreleased] — Release 1 (v9.0.0-r1 target)

### Added

- **Release 1 profile** — 8-service compose (`docker-compose.release1.yml`), Kong `kong.release1.yml`, web `VITE_RELEASE_PROFILE=release1`
- **Odoo sync engine** — XML-RPC full sync: products, work centers, BOMs, BOM lines, routing, MOs, demands, supply (`connector/app/odoo/sync_engine.py`)
- **Odoo 17/19 field mappers** — date_start/finished, scheduled_date, timezone-aware datetimes, BomLine tenant_id
- **Post-sync feasibility rescore** — commit before fea-svc rescore in full sync
- **Sync APIs** — `POST /sync/run`, `GET /sync/status`, `GET /sync/data-quality`
- **Odoo activate write-back** — `POST /sync/odoo/activate` (XML-RPC)
- **Star Trans Odoo seed** — `scripts/seed-odoo-startrans.py` (TR-500/TR-1000 BOMs + MOs)
- **R1 customer docs** — implementation playbook, training curriculum, data quality checklist, support guide
- **Arabic MVP** — Control Tower + nav (`locales/ar.json`)
- **Comprehensive PRD** — `docs/PRD-IPE-COMPREHENSIVE-AS-IS.md`, executive one-pager

### Fixed

- Mapper `default_code=False` → null internal_ref
- MO sync Odoo 19 invalid fields (`date_planned_*`, `__last_update`)
- Supply/demand date parsing (string → timezone-aware datetime)
- `parse_odoo_datetime` definition order in mapper

---

## [v8.2.0] — 2026-06-28

### Added

- **U7 Design AI** — material-svc: engineering materials, design recommendations (CP28)
- **U8 Responsible procurement** — procurement-svc: spend, supplier compliance (CP29)
- **Sustainability demo** — sustain-svc dashboard (CP31)
- **Quality intelligence demo** — quality-svc SPC dashboard (CP32)
- **32/32 demo checkpoints** — Star Trans profile validation
- **Supply network seed** — migration 034 (4 plants, 6 lanes)
- **RLS INSERT policies** — migration 035
- **v8 integration tests** — `tests/integration/test_v8_e2e.py` (5/5)
- `docs/DEPLOYMENT-READINESS-v8.2.0.md`, `docs/PRD-IPE-v8.2.0-ENTERPRISE.md`

### Changed

- Speckit readiness **100/100**; audit ~92/100
- POST-B scaffolds: Keycloak, secrets vault, Stripe, SAP/D365 ERP base

---

## [v8.1.0] — 2026-06-27

### Added

- **U4 Supply orchestration** — supply-svc (CP25)
- **U5 Order management / ATP** — order-svc (CP26)
- **U6 Equipment intelligence** — equipment-svc (CP27)
- Migrations 030 (v8 phase 2 entities)

---

## [v8.0.0] — 2026-06-27

### Added

- **U1 Role-based Copilot sessions** — nlp-svc (CP30)
- **U2 Demand sensing & forecasting** — demand-svc (CP21–22)
- **U3 Scenario workbench** — scenario-svc (CP23–24)
- **Module hub consolidation** — 6 navigation hubs (spec 006)
- Migrations 029 (v8 phase 1 entities)

---

### Added

- **Ollama local LLM backbone** — query orchestrator + tool-calling copilot (`ollama_tool_client.py`)
- Docker overlays: `docker-compose.ollama.yml`, `docker-compose.ollama-host.yml`
- `scripts/start-ollama-stack.ps1` with `-UseHostOllama` flag
- `docs/PRODUCT-STATUS.md`, `docs/PRODUCTION-BLOCKERS.md`, `docs/END-USER-GUIDE.md`
- `docs/AI-AGENTS-ARCHITECTURE.md` — full agent roles + Ollama deployment
- OpenRouter LLM provider for cloud fallback
- Phase 5 gap analysis reports (speckit, audit, coverage, documentation)
- Speckit 162/162 completion (T049–T051 closed; T053 cancelled)
- ADR-001 Keycloak deferral to v8.0.0
- Documentation suite: CONTRIBUTING, runbooks, architecture index, API reference

### Changed

- Kong nlp-svc upstream timeout → 300s (local LLM cold-start)
- `IPE_LLM_PRIMARY_PROVIDER` — auto | ollama | openrouter | anthropic
- Coverage gate ≥75% per service — all six core services pass
- READINESS.md and release checklist updated for v7.0.0 RC

### Fixed

- Copilot 503 — OpenRouter + Ollama integration; `IPE_*` env prefix
- Intent classifier fallback on LLM unavailable
- Tool-calling copilot Anthropic-only gap — Ollama tools supported
- CopilotPanel missing `X-Tenant-ID` header
- del-svc spurious `mock_anthropic_key` env var

---

## [v6.1.0] — 2026-06-26

### Added

- TLS internal services runbook (`docs/runbooks/tls-internal.md`)
- JWT rotation runbook (`docs/runbooks/jwt-rotation.md`)
- Migration 028: SEC-05 password_hash backfill
- Wave 3 live regression evidence (demo 20/20, chaos 6/6)

### Fixed

- Auth password verification for `{SHA-256}` hashed credentials
- MDR fail-closed gate (503) on capacity endpoints
- Optimistic locking on schedule approve (409 conflict)

---

## [v6.0.1] — 2026-06-25

### Fixed

- MDR internal JWT forwarding for cross-service calls
- Audit fixes C-01, BUG-02, BUG-03 live-verified

---

## [v6.0.0] — 2026-06-24

### Added

- V6 features: tariff shock, visual CPM, predictive maintenance, cost of chaos, war room
- Demo 20/20 live gate
- Speckit 004 AI-first V6 complete (55/55 tasks)

---

## [v1.0.0] — 2026-06-22

### Added

- Initial production release
- 14-service microservices architecture
- Kong API gateway with JWT auth
- Demo stack and critical path E2E (Gate 2 passed)
- PostgreSQL CDM with tenant RLS (migrations 024+)
