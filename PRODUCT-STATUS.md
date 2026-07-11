# IPE Product Status

**Last Updated:** 2026-07-11  
**Release Tag:** v9.2.0-planning (planning intelligence), v9.4.0-p3 (platform)  
**Workspace:** `E:\AISOP\ipe`

---

## Release 1 Core Modules

| Module | Status | Service | Migration | Notes |
|--------|--------|---------|-----------|-------|
| Production Planning (MRP) | BUILT | dpe-svc | 001–038 | Control Tower, MO management |
| Feasibility Engine | BUILT | fea-svc | — | Auto-propose, rescore |
| Resource Management | BUILT | res-svc | — | Machines, WC utilisation |
| Capacity Planning | BUILT | cap-svc | 048 | Alerts, utilisation |
| Material Management | BUILT | mat-svc | 044, 047 | ABC/XYZ, safety stock |
| Odoo Connector | BUILT | connector | 046 | XML-RPC sync, lead time history |
| API Gateway | BUILT | Kong | — | R1 + R2 profiles |
| Web UI (R1) | BUILT | web-ui | — | `VITE_RELEASE_PROFILE=release1` |

## Release 2 Additions

| Module | Status | Service | Migration | Notes |
|--------|--------|---------|-----------|-------|
| AI Copilot (Planner Assistant) | BUILT | nlp-svc | — | 9+ tools, concurrent execution, LLM warm-up |
| Demand Sensing & Forecasting | BUILT | demand-svc | 045 | SES, ARIMA, SARIMA, best-fit |
| Scenario Workbench | BUILT | scenario-svc | — | What-if simulations |
| Web UI (R2) | BUILT | web-ui | — | `VITE_RELEASE_PROFILE=release2`, Arabic 299+ keys |

## Planning Intelligence Modules (v9.2.0-planning)

| Module | Status | Service | Migration | Notes |
|--------|--------|---------|-----------|-------|
| ABC/XYZ Segmentation | BUILT | mat-svc | 044 | Configurable thresholds, segment-driven service levels |
| Forecast Quality (MAPE/Bias/MASE) | BUILT | demand-svc | 045 | Stability, value-add by lag |
| ARIMA/SARIMA Best-Fit | BUILT | demand-svc | — | 18-combo grid, 8s budget, SES-first fallback |
| Safety Stock Calculator | BUILT | mat-svc | 047 | Segment-driven service levels, Z-score method |
| Capacity Utilisation Alerts | BUILT | cap-svc | 048 | Configurable overload thresholds, alerting |
| S&OP Process Engine | BUILT | sop-svc | 049 | 4-stage cycle, consensus calculation, version management |

## Test Coverage

| Suite | Status | Count | Notes |
|-------|--------|-------|-------|
| Backend unit tests | GREEN | 199+ | All services |
| Planning module tests | GREEN | 70+ | mat/demand/cap/connector/sop/nlp |
| Planning UAT | GREEN (code) | 10/10 | UAT-10 needs live LLM; UAT-11 SES fallback |
| R2 smoke | GREEN | 15/15 | `scripts/release2-smoke.ps1` |
| Playwright | GREEN | 22/22 | Desktop + Arabic |
| k6 SLO | GREEN | p95 293ms | Under 300ms target |

## Tags

| Tag | Status | Notes |
|-----|--------|-------|
| v9.2.0-planning | TARGET (Sprint 1) | All ENG gates green; tag pending final commit |
| v9.1.1-r2 | PENDING | Blocked on G-R2-04 Arabic native QA sign-off (COM) |
| v9.4.0-p3 | RELEASED | Platform Phase 3 tag |
| v9.3.0-p2 | RELEASED | Platform Phase 2 tag |
| v9.1.0-r2 | LOCAL ONLY | Stale; do not push — superseded by v9.1.1-r2 |

## Open Commercial Items

| Item | Owner | Status |
|------|-------|--------|
| Star Trans SOW | Waleed | Sprint 2 |
| Arabic native QA sign-off | Waleed (find reviewer) | COM dependency |
| Odoo staging environment | Ops | PH1-02 |
| OQ-7 licence price | Waleed | Sprint 2 |
| OQ-1 Star Trans Odoo version | Star Trans IT | Sprint 2 |
