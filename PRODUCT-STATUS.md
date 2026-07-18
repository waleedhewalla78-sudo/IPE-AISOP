# IPE Product Status

**Last Updated:** 2026-07-18  
**Release Tag:** v9.2.0-planning (applied @ b04434d), v9.4.0-p3 (platform) — **no v9.1.1-r2** (G-R2-04 HOLD)  
**Active Speckit feature:** `specs/030-phase8-r1-production` (prior: `029`–`024`)  
**Agents:** 17 built (A1–A17) + **A18–A20 stubs** (Phase 8 Wave 1) · **Modules:** 9 (M1–M9) + Phase 7 deep + Phase 8 scaffold  
**Constitution:** 1.4.1  
**Migration head:** **070** (`cdm_write_back_log`)  
**Workspace:** `E:\AISOP\ipe`  
**Phase 3–7 reports:** `docs/qa/PHASE{3,4,5,6,7}-EXECUTION-AND-TEST-REPORT.md`  
**Spec 029 report:** `docs/qa/SPEC029-PRODUCTIONIZATION-REPORT.md`  
**Phase 8 report:** `docs/qa/PHASE8-EXECUTION-AND-TEST-REPORT.md`  
**R1 readiness:** `docs/qa/R1-RELEASE-READINESS.md` — verdict **ENG READY / COM CONDITIONAL**  
**Phase 3-5 E2E gate:** `docs/qa/PHASES3-5-E2E-TEST-REPORT.md` (re-run @ `50c908f` — **CONDITIONAL** 86 PASS / 0 FAIL / 15 SKIP / 1 BLOCKED)

---

## Release 1 Core Modules

| Module | Status | Service | Migration | Notes |
|--------|--------|---------|-----------|-------|
| Production Planning (MRP) | BUILT | dpe-svc | 001–038 | Control Tower, MO management |
| Feasibility Engine | BUILT | fea-svc | — | Auto-propose, rescore |
| **Predictive risk (Ops P3)** | **BUILT (eng)** | fea-svc | **057** | Unit tests GREEN |
| **Root-cause chain (Ops P3)** | **BUILT (eng)** | fea-svc | **056** | Unit tests GREEN |
| Resource Management | BUILT | res-svc | — | Machines, WC utilisation |
| Capacity Planning | BUILT | cap-svc | 048 | Alerts, utilisation |
| **Smart batch / auction (Ops P3)** | **BUILT (eng)** | cap-svc | **058–059** | Unit tests GREEN |
| Material Management | BUILT | mat-svc | 044, 047 | ABC/XYZ, safety stock |
| Odoo Connector | BUILT | connector | 046, **050** | XML-RPC; Odoo 17+19 aliases |
| OTD Analytics | BUILT | dpe-svc | 039 | KPI/trend/root-cause + dashboard |
| **Agent orchestrator / exceptions** | **BUILT (eng)** | dpe-svc | **051–052** | Dry-run + SLA lifecycle |
| **Excel upload-svc** | **BUILT** | upload-svc :8120 | **053** | Wizard + Phase 8 file types |
| API Gateway | BUILT | Kong | — | R1 + R2 + star-trans |
| Web UI (R1) | BUILT | web-ui | — | `VITE_RELEASE_PROFILE=release1` |

## Release 2 Additions

| Module | Status | Service | Migration | Notes |
|--------|--------|---------|-----------|-------|
| AI Copilot | BUILT | nlp-svc | — | Claude-first; Ollama for narratives when up |
| Demand Sensing & Forecasting | BUILT | demand-svc | 045, **054** | SES/ARIMA/SARIMA |
| Scenario Workbench | BUILT | scenario-svc | — | What-if |
| Web UI (R2) | BUILT | web-ui | — | Arabic eng keys |

## Ops Blueprint Phases 3–7

| Phase | Spec | Status |
|-------|------|--------|
| Phase 3 AI Agents + Onboarding | 024 | **ENG COMPLETE Wave 1** (051–059) |
| Phase 4 Premium (A8–A12, M1–M6) | 025 | **ENG COMPLETE Wave 1** |
| Phase 5 Planning Command | 026 | **ENG COMPLETE Wave 1** |
| Phase 6 Enterprise Agentic (A13–A17, M7–M9) | 027 | **ENG COMPLETE Wave 1** — Odoo/IoT MOCK/STUB |
| Phase 7 Deep Planning | 028 | **ENG COMPLETE Wave 1** (064–067) |
| Productionization | 029 | **ENG COMPLETE Wave 1** (068–069, Kong enterprise, stage-gate) |

## Phase 8 — Production Scaffold (Spec 030 — Wave 1 / 8A)

| Item | Status | Notes |
|------|--------|-------|
| Ollama client + degrade + amber banner | **BUILT** | No live 70B / fine-tunes claimed |
| AgentRoleContext $1K/$10K/$50K | **BUILT** | res-svc approve + financial filter |
| Excel forecast/quality/S&OP + CT/MPS export | **BUILT** | upload-svc + `/phase8/export/*` |
| Write-back log dry-run/approve | **MOCK** | migration **070**; PH1-02 OPEN |
| Arabic Phase 8 keys | **ENG** | G-R2-04 **OPEN** |
| A18/A19/A20 | **STUB** | Full → 8B–8D deferred |

## Test Coverage (this run)

| Suite | Status | Count |
|-------|--------|-------|
| Phase 8 new (shared+dpe+upload) | GREEN | **31** |
| dpe Phase 4–8 + Spec 029 bundle | GREEN | **102** |
| Frontend tsc | GREEN | 0 errors |
| Phases 3–5 strategy (prior) | CONDITIONAL | 86/0/15/1 |
| star-trans-validate #70/#72/#110 | OPEN | Stack partial |

## Tags

| Tag | Status |
|-----|--------|
| v9.2.0-planning | **APPLIED** @ b04434d |
| v9.1.1-r2 | **HOLD** (G-R2-04) |
| v9.1.0-r2 | **Do not push** (stale) |
| v9.3.0-r1-eng | **NOT APPLIED** this run |

## COM OPEN (never fake)

OQ-7 · OQ-1 · PH1-01 · PH1-02 · G-R2-04 · OQ-9

## Speckit

| Spec | Status |
|------|--------|
| 022–028 | ENG COMPLETE Wave 1 |
| **029** | ENG COMPLETE Wave 1 |
| **030** | **ENG COMPLETE Wave 1 (8A)** — active |
