# IPE Product Status

**Last Updated:** 2026-07-15  
**Release Tag:** v9.2.0-planning (applied @ b04434d), v9.4.0-p3 (platform)  
**Active Speckit feature:** `specs/024-phase3-ops-intelligence`  
**Constitution:** 1.3.0  
**Workspace:** `E:\AISOP\ipe`

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
| **Excel upload-svc (Ops P3)** | **SCAFFOLD** | upload-svc | **053** | Health + upload API present; compose/Kong wiring residual |
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

## Ops Blueprint Phase 4 / 5 (BACKLOG — do not claim DONE)

| Item | Status | Source |
|------|--------|--------|
| M1–M6 Command modules | BACKLOG | Phase4 Premium Proposal |
| Agents A8–A12 | BACKLOG | Phase4 Premium Proposal |
| Customer portal | BACKLOG | Phase4 |
| Planning Cockpit / MPS / MRP / ATP deep | BACKLOG | Phase5 Planning-Command-Deep |

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
| Spec 024 Ops P3 core | GREEN | 11 | predictive/root-cause/batch/auction/orchestrator |
| Planning module tests | GREEN | 70+ | mat/demand/cap/connector/sop/nlp |
| Planning UAT | GREEN (code) | 10/10 code path | Live LLM optional |
| R2 smoke | GREEN (prior) | 15/15 | Re-verify Spec 022 |
| Playwright | GREEN | 22/22 | Eng Arabic ≠ G-R2-04 COM |
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
| **024 phase3-ops-intelligence** | **ACTIVE** — Ops Blueprint Phase 3 eng + Phase 4/5 backlog; constitution 1.3.0 |
