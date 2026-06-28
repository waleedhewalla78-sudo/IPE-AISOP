# Feature Specification: IPE v8.0.0 Phase 1 Foundation

**Feature Branch**: `007-v8-phase1-foundation`  
**Created**: 2026-06-27  
**Status**: Implemented (MVP)  
**Input**: SAP Gap Analysis — Tier 1 upgrades U1–U3

---

## What We Build

Phase 1 closes the highest-priority SAP Joule/IBP gaps on top of IPE v7.1 (hub consolidation):

| Stream | Deliverable | Service |
|--------|-------------|---------|
| **U1** | Role-based Copilot with sessions & follow-up suggestions | `nlp-svc` (extended) |
| **U2** | Demand sensing & statistical forecasting | `demand-svc` `:8040` |
| **U3** | Planning scenario workbench (what-if KPI simulation) | `scenario-svc` `:8050` |

### UI (Planning Hub)

- **Demand** tab — forecast table + run sense cycle
- **Scenarios** tab — create/simulate/compare sandbox scenarios
- **Copilot** — role switcher (Planner / Manager / Supervisor / Executive)

---

## What We Want (requirements)

### FR-V8-01 Role-based Copilot
JWT role drives agent persona, intent scope hints, and persisted session context (`cdm_copilot_session`).

### FR-V8-02 Demand forecasting
Generate short/medium horizon forecasts from `cdm_demand_line` history; ingest external signals; MAPE accuracy endpoint.

### FR-V8-03 Scenario workbench
CRUD on `cdm_scenario` sandbox; parameter overlays; KPI simulation; side-by-side compare.

### FR-V8-04 Integration
Kong routes for new APIs; Planning Hub tabs; zero regression on existing `/api/v1/demand/*` dpe-svc routes (classify, tariff).

### FR-V8-05 Tenant isolation
All new tables RLS-scoped via migration 029.

---

## User Stories

| ID | Story | Acceptance |
|----|-------|------------|
| US-V8-1 | Planner selects Planner agent and asks about at-risk MOs | Role suggestions shown; session persisted |
| US-V8-2 | Planner runs demand sense cycle | Forecast rows appear in Demand tab |
| US-V8-3 | Planner creates +10% demand scenario and simulates | KPI results displayed |
| US-V8-4 | Executive uses Executive agent | OTD/chaos-oriented follow-ups |
| US-V8-5 | Legacy dpe `/demand/classify` still works | Demo tariff/MO flows unchanged |

---

## Out of Scope (Phase 2+)

- copilot-svc standalone microservice (8030) — deferred; session in nlp-svc
- Prophet/LSTM ensemble — MVP uses SES v1
- Multi-echelon supply (U4), order mgmt (U5), predictive maint expansion (U6)
- Joule Studio low-code agent builder

---

## Baseline

Built on **v7.1 hub consolidation** (006): 6 sidebar hubs, Planning/Command dashboards, Ollama copilot, 20/20 demo.
