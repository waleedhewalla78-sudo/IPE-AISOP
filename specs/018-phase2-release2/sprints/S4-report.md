# Sprint S4 Report — Scenario Workbench

**Sprint**: S4  
**Date**: 2026-07-10  
**Authority**: `docs/PHASE2-SPRINT-PLAN.md` · W2-03, W2-04  
**Status**: ✅ Complete

---

## Summary

Delivered scenario simulator with demand %, supplier delay days, and capacity reduction % parameters; REST simulate/list/get APIs; and Scenarios UI with baseline vs scenario KPI comparison (up to 3 saved scenarios).

---

## Deliverables

| Task | Deliverable | Status |
|------|-------------|--------|
| S4-01 | Simulator KPI deltas | ✅ |
| S4-02 | POST simulate, GET list, GET by id | ✅ |
| S4-03 | Scenarios UI compare | ✅ |
| S4-04 | `test_simulator_r2.py` | ✅ |

---

## APIs

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/scenario/simulate` | Ad-hoc or persisted simulation |
| POST | `/api/v1/scenario/{id}/simulate` | Re-run stored scenario |
| GET | `/api/v1/scenario` | List active scenarios (max 3) |
| GET | `/api/v1/scenario/{id}` | Scenario detail + parameters + results |
| GET | `/api/v1/scenario/compare` | Multi-scenario fitness compare |

**Parameters**:

- `demand_change_pct` — e.g. `10%`
- `supplier_delay_days` — integer days
- `capacity_reduction_pct` — e.g. `15%`

---

## UI

| File | Purpose |
|------|---------|
| `apps/web/src/features/hubs/planning/ScenarioWorkbenchPage.tsx` | Create/simulate/compare up to 3 scenarios |

---

## Tests

```
services/scenario-svc/tests/test_simulator_r2.py — 7 passed
services/scenario-svc/tests/ (full suite) — see pytest output
```

---

## KPI baseline (simulator)

| KPI | Baseline |
|-----|----------|
| otd_pct | 87.5 |
| avg_feasibility | 74.9 |
| orders_at_risk | 1.0 |
| total_cost_usd | 125000 |
| capacity_util_pct | 82.0 |

---

*S4 report — Phase 2 Release 2*
