# IPE Product Status

**Last Updated:** 2026-07-16  
**Release Tag:** v9.2.0-planning (applied @ b04434d), v9.4.0-p3 (platform)  
**Active Speckit feature:** `specs/027-phase6-enterprise-agentic` (prior: `026-phase5-planning-command`, `025-phase4-premium`, `024-phase3-*`)  
**Agents:** 17 (A1–A17) · **Modules:** 9 (M1–M9)  
**Constitution:** 1.4.0  
**Workspace:** `E:\AISOP\ipe`  
**Phase 3 report:** `docs/qa/PHASE3-EXECUTION-AND-TEST-REPORT.md`  
**Phase 4 report:** `docs/qa/PHASE4-EXECUTION-AND-TEST-REPORT.md`  
**Phase 5 report:** `docs/qa/PHASE5-EXECUTION-AND-TEST-REPORT.md`  
**Phase 6 report:** `docs/qa/PHASE6-EXECUTION-AND-TEST-REPORT.md`  
**Phase 3-5 E2E gate:** `docs/qa/PHASES3-5-E2E-TEST-REPORT.md` (verdict FAIL = strategy-harness path mismatch; dpe-svc phase4/phase5 foundations verified green → Phase 6 PROCEED)

---

## Release 1 Core Modules

| Module | Status | Service | Migration | Notes |
|--------|--------|---------|-----------|-------|
| Production Planning (MRP) | BUILT | dpe-svc | 001–038 | Control Tower, MO management |
| Feasibility Engine | BUILT | fea-svc | — | Auto-propose, rescore |
| **Predictive risk (Ops P3)** | **BUILT (eng)** | fea-svc | **057** | `PredictiveRiskScorer` + GET `/feasibility/predict/{mo_id}`; unit tests GREEN |
| **Root-cause chain (Ops P3)** | **BUILT (eng)** | fea-svc | **056** | `RootCauseAnalyzer` + GET `/feasibility/root-cause/{mo_id}`; unit tests GREEN |
| Resource Management | BUILT | res-svc | — | Machines, WC utilisation |
| Capacity Planning | BUILT | cap-svc | 048 | Alerts, utilisation |
| **Smart batch / auction (Ops P3)** | **BUILT (eng)** | cap-svc | **058–059** | `SmartBatcher` + `CapacityAuction`; unit tests GREEN |
| Material Management | BUILT | mat-svc | 044, 047 | ABC/XYZ, safety stock |
| Odoo Connector | BUILT | connector | 046, **050** | XML-RPC sync; Odoo Config v2; Odoo 17+19 aliases |
| OTD Analytics | BUILT | dpe-svc | 039 | KPI/trend/root-cause/baseline/snapshot + dashboard |
| **Agent orchestrator / exceptions (Ops P3)** | **BUILT (eng)** | dpe-svc | **051–052** | `AgentOrchestrator` dry-run + exception ack/resolve API; tests GREEN |
| **Excel upload-svc (Ops P3)** | **BUILT** | upload-svc :8120 | **053** | Wizard + multi-stage validation; R2 compose + Kong `/api/v1/upload` |
| API Gateway | BUILT | Kong | — | R1 + R2 + star-trans profiles |
| Web UI (R1) | BUILT | web-ui | — | `VITE_RELEASE_PROFILE=release1` |

## Release 2 Additions

| Module | Status | Service | Migration | Notes |
|--------|--------|---------|-----------|-------|
| AI Copilot (Planner Assistant) | BUILT | nlp-svc | — | 9+ tools; UAT-10 timeout fix in Spec 021 |
| Demand Sensing & Forecasting | BUILT | demand-svc | 045, **054** | SES/ARIMA/SARIMA; demand signal table for fusion |
| Scenario Workbench | BUILT | scenario-svc | — | What-if simulations |
| Web UI (R2) | BUILT | web-ui | — | `VITE_RELEASE_PROFILE=release2`, Arabic eng keys |

## Planning Intelligence Modules (v9.2.0-planning)

| Module | Status | Service | Migration | Notes |
|--------|--------|---------|-----------|-------|
| ABC/XYZ Segmentation | BUILT | mat-svc | 044 | Configurable thresholds |
| Forecast Quality (MAPE/Bias/MASE) | BUILT | demand-svc | 045 | Stability, value-add by lag |
| ARIMA/SARIMA Best-Fit | BUILT | demand-svc | — | 8s budget, SES fallback |
| Safety Stock Calculator | BUILT | mat-svc | 047 | Segment-driven Z-score |
| Capacity Utilisation Alerts | BUILT | cap-svc | 048 | Overload thresholds |
| S&OP Process Engine | BUILT | sop-svc | 049 | 4-stage cycle |

## Phase 3 AI Agents + Onboarding (Spec 024 — Wave 1)

| Module | Status | Service | Migration | Notes |
|--------|--------|---------|-----------|-------|
| Data Upload / Onboarding Wizard | BUILT | upload-svc :8120 | 053 | 5-phase wizard, multi-stage validation |
| Predictive Risk Scoring | BUILT | fea-svc | 057 | T+3/7/14 predictions |
| Root Cause Chain (5-why) | BUILT | fea-svc | 056 | Recommendations by horizon |
| Smart Batching | BUILT | cap-svc | 059 | Changeover minimisation |
| Capacity Auction | BUILT | cap-svc | 058 | Financial priority resolution |
| Demand Signal Fusion | BUILT | demand-svc | 054 | Multi-source fused demand |
| Predictive Stockout + Supplier Scorecard | BUILT | mat-svc | 055 (ALTER 041) | Phase 3 columns on supplier_score |
| Agent Orchestrator + Exceptions | BUILT | dpe-svc | 051–052 | Dry-run chain + SLA lifecycle |
| Contextual Copilot / Meeting Prep | BUILT | nlp-svc | — | Morning brief + meeting templates |
| S&OP Executive Brief | BUILT | sop-svc | — | Auto-generated brief API |
| Phase 3 Frontend pages | BUILT | web-ui | — | Upload, agents, exceptions, predictions, root-cause, suppliers, meeting-prep |

## Ops Blueprint Phase 4 / 5

| Item | Status | Source |
|------|--------|--------|
| M1–M6 Command modules (pulse + shells) | **BUILT Wave 1** | Spec 025 / Phase4 Premium Proposal |
| Agents A8–A12 | **BUILT Wave 1** | Spec 025 |
| Autonomous overnight rules (guardrailed) | **BUILT Wave 1** | Spec 025 |
| Customer portal (read-only) | **BUILT Wave 1** | Spec 025 |
| Live Odoo quality/finance/PO sync | DEFERRED | Needs PH1-02 |
| Digital Factory animation polish | DEFERRED | Shop-floor linked only |
| Planning Cockpit / MPS / MRP / ATP / Ops Live | **BUILT Wave 1** | Spec 026 / Phase5 Planning-Command-Deep |
| RCCP/CRP + leveling + scenario cascade | **BUILT Wave 1** | Spec 026 |
| Performance + Predictive Command | **BUILT Wave 1** | Spec 026 |
| Collaborative multi-user conflict UI | DEFERRED | Spec 026 residual |
| WhatsApp / Comms Hub | DEFERRED | Spec 026 residual |

## Ops Blueprint Phase 6 — Enterprise Agentic (Spec 027 — Wave 1)

| Item | Status | Service | Migration | Notes |
|------|--------|---------|-----------|-------|
| A13 Commercial Intelligence (M8) | **BUILT Wave 1** | dpe-svc | 060 | Pricing optimization, deal profitability, contract compliance |
| A14 Analytics Intelligence (M7) | **BUILT Wave 1** | dpe-svc | 061 | Auto insights, trend/anomaly (z-score), predictive (linreg) |
| A15 Procurement Execution (M9) | **BUILT Wave 1** | dpe-svc | 062 | 3-way match + routing, receipt confirmation |
| A16 Shop Floor Intelligence (M9) | **BUILT Wave 1** | dpe-svc | — | Work instructions, time tracking, progress (IoT **STUB**) |
| A17 Cross-Functional Orchestrator | **BUILT Wave 1** | dpe-svc | 063 | Resolution hierarchy + 6 policies + cascade + cross-functional ATP/CTP |
| M7 Analytics + M8 Commercial + M9 Procurement UI | **BUILT Wave 1** | web-ui | — | Intelligence hub tabs + `/enterprise/*` |
| Odoo Accounting integration | **SCAFFOLD/MOCK** | dpe-svc | — | `is_live=false` — PH1-02 OPEN |
| Market data / FX feed (A14) | **NOT WIRED** | — | — | PH1-02 OPEN — supplied history only |
| IoT / machine telemetry (A16) | **STUB** | — | — | No live MQTT/REST |
| Odoo PO/invoice write-back (A15) | **NOT executed** | — | — | PH1-02 OPEN |
| Phase 6D (tuning / SOC 2 / multi-plant) | **DEFERRED** | — | — | Not in Wave 1 |
| Live Kong :8000 `/enterprise/*` smoke | **NOT confirmed** | — | — | R2 upload-svc unhealthy residual; ASGI smoke 6/6 covers handlers |

## Customer Enablement (Sprint 2 — COMPLETE)

| Deliverable | Path | Status |
|-------------|------|--------|
| SOW v1 | `docs/customer/star-trans/IPE-Star-Trans-SOW-v1.md` | Artifact ready; **send blocked by OQ-7** |
| Sales one-pagers EN/AR | `docs/sales/` | Done |
| Field mapping | `docs/customer/star-trans/ODOO-FIELD-MAPPING-WORKSHEET.md` | Done |
| Implementation playbook / training / support | `docs/implementation/`, `docs/runbooks/` | Done |
| Release notes R1 | `docs/customer/star-trans/RELEASE-NOTES-R1.md` | Done |
| Validate script | `scripts/star-trans-validate.ps1` | Done |
| Deploy package | `deploy/star-trans/` | Done; Sprint 3 dry-run |

## Test Coverage

| Suite | Status | Count | Notes |
|-------|--------|-------|-------|
| Backend unit tests | GREEN | 199+ | All services |
| Spec 024 Phase 3 Wave 1 | GREEN | **18/18** | fea/cap/demand/mat/dpe/nlp/sop/upload Phase 3 suites |
| Spec 025 Phase 4 Premium Wave 1 | GREEN | **21** | A8–A12 / pulse / autonomy / CAPA / carbon / portal |
| Spec 026 Phase 5 Planning Command | GREEN | **13/13** | Cockpit/MPS/MRP/ATP/RCCP/ops/performance/predictive |
| Spec 027 Phase 6 Enterprise Agentic | GREEN | **40/40** | A13/A14/A15/A16/A17 cores + `/enterprise/*` ASGI smoke |
| dpe-svc full regression (post-Phase 6) | GREEN | **280 passed / 2 skipped** | No regression from Phase 6 router add |
| Planning module tests | GREEN | 70+ | mat/demand/cap/connector/sop/nlp |
| Planning UAT | GREEN (code) | 10/10 code path | Live LLM optional |
| R2 smoke | PRIOR GREEN | 15/15 | Phase 3 services added; re-verify when stack healthy |
| Playwright | GREEN (prior) | 22/22 | Eng Arabic ≠ G-R2-04 COM; Phase 3 pages pending dedicated e2e |
| k6 SLO | GREEN | p95 293ms | Under 300ms target |

## Tags

| Tag | Status | Notes |
|-----|--------|-------|
| v9.2.0-planning | **APPLIED** @ b04434d | Sprint 1 engineering closure |
| v9.1.1-r2 | **HOLD** | Blocked on G-R2-04 Arabic native QA (COM) |
| v9.4.0-p3 | RELEASED | Platform Phase 3 (K8s) — ≠ Ops Blueprint Phase 3 |
| v9.3.0-p2 | RELEASED | Platform Phase 2 |
| v9.1.0-r2 | LOCAL ONLY / STALE | **Do not push** — superseded by v9.1.1-r2 |

## Open Commercial Items (MUST remain OPEN until humans close)

| Item | Owner | Status |
|------|-------|--------|
| OQ-7 licence / implementation price | Waleed | **OPEN — blocks SOW send** |
| OQ-1 Odoo 17 vs 19 confirm | Star Trans IT | **OPEN** (connector supports both) |
| PH1-01 SOW send | COM | **OPEN** (depends OQ-7) |
| PH1-02 Odoo staging | Ops / Customer IT | **OPEN** |
| G-R2-04 Arabic native QA sign-off | Native reviewer | **OPEN** |
| OQ-9 Gate 11 waiver signatures | Waleed | **OPEN** (eng waiver exists) |

## Speckit

| Spec | Status |
|------|--------|
| 020 planning-intelligence | ENG COMPLETE |
| 021 release-closure | ENG COMPLETE |
| 022 sprint3-golive | ENG COMPLETE (residuals #70–#72) |
| 023 sprint4-wave1 | ENG COMPLETE — Odoo Config v2 + OTD; COM OPEN |
| **024 phase3-ops-intelligence** | **ENG COMPLETE (Wave 1 MVP)** — migrations 051–059, upload-svc, UI; COM OPEN |
| 024-phase3-ai-agents | Companion execution pack — see PHASE3 report |
| **025 phase4-premium** | **ENG COMPLETE (Wave 1 MVP)** — M1–M6 pulse, A8–A12, autonomy, portal; COM OPEN |
| **026 phase5-planning-command** | **ENG COMPLETE (Wave 1 MVP)** — Cockpit/MPS/MRP/ATP/RCCP/leveling/scenario + Ops Live/War Room/performance/predictive; COM OPEN |
| **027 phase6-enterprise-agentic** | **ENG COMPLETE (Wave 1: 6A+6B+6C)** — A13–A17, M7–M9, migrations 060–063; Odoo/market/IoT MOCK/STUB; Phase 6D deferred; COM OPEN |
