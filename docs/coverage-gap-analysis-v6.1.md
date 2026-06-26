# Test Coverage Gap Analysis — v6.1.0 → 75%+

**Date:** 2026-06-26  
**Command:** `uv run pytest tests/ -m "not integration" --cov=app --cov-report=term`  
**Current gate:** `fail_under=60` (cap, mat, dpe) · `fail_under=80` (nlp, alert, fea — **failing gate, tests pass**)

---

## Service Summary

| Service | Coverage | fail_under | Tests | Gap to 75% |
|---------|----------|------------|-------|------------|
| **cap-svc** | **68.26%** | 60 ✅ | 249 pass | +6.7 pts |
| **mat-svc** | **65.35%** | 60 ✅ | 105 pass | +9.7 pts |
| **dpe-svc** | **65.98%** | 60 ✅ | 147 pass | +9.0 pts |
| **alert-svc** | **67.18%** | 80 ❌ | 17 pass | +7.8 pts |
| **nlp-svc** | **55.69%** | 80 ❌ | 68 pass | +19.3 pts |
| **fea-svc** | **55.45%** | 80 ❌ | 68 pass | +19.6 pts |

**Note:** No standalone `auth-svc` or `mdr-svc` — auth in **dpe-svc** (`app/api/v1/auth.py`), MDR in **dpe-svc** (`app/api/v1/mdr.py`, `app/core/mdr_engine.py`).

---

## Lowest-Coverage Modules (priority)

### cap-svc (68% → target 80%)

| Module | Cover | Untested paths |
|--------|-------|----------------|
| `app/api/v1/scenarios.py` | 26% | Scenario CRUD, simulation endpoints |
| `app/api/v1/capacity.py` | 64% | Green schedule, network optimize, labor sections |
| `app/core/project_plan_service.py` | 17% | Excel upload pipeline |
| `app/core/gurobi_solver.py` | 19% | Gurobi fallback (mock in tests) |

**Tests to add:** API tests for `/scenarios/*`, `/capacity/network-optimize`, project plan upload mock.

### mat-svc (65% → target 80%)

| Module | Cover | Untested paths |
|--------|-------|----------------|
| `app/core/netting.py` | 22% | Priority netting, multi-echelon |
| `app/core/supplier_model.py` | 13% | Supplier predict |
| `app/api/v1/material.py` | 64% | Bulk endpoints, landed cost API |
| `app/events/consumers.py` | 31% | Kafka handlers |

**Tests to add:** `test_netting.py`, supplier predict API, consumer handler mocks.

### dpe-svc (66% → target 80%)

| Module | Cover | Untested paths |
|--------|-------|----------------|
| `app/api/v1/demand.py` | 49% | Classify queue, batch ops |
| `app/api/v1/admin.py` | 30% | Admin config mutations |
| `app/core/chaos_cost.py` | 19% | War room cost rollup |
| `app/api/v1/auth.py` | 95% | ✅ Wave 3 SHA-256 path covered |

**Tests to add:** demand classify integration mocks, chaos_cost unit tests.

### nlp-svc (56% → target 75%)

| Module | Cover | Untested paths |
|--------|-------|----------------|
| `app/core/orchestrator.py` | ~50% | LLM routing, fallback tiers |
| `app/core/copilot_tools.py` | partial | 4-tool registry (war room) |
| `app/api/v1/copilot.py` | low | Streaming, error paths |

**Tests to add:** Extend `test_copilot_tools.py`; mock orchestrator LLM failures.

### alert-svc (67% → target 75%)

| Module | Cover | Untested paths |
|--------|-------|----------------|
| `app/api/v1/war_room.py` | partial | recovery-plan edge cases |
| `app/events/consumers.py` | partial | Event ingestion |

**Tests to add:** war_room API tests with mock DB (CP20 paths).

### fea-svc (55% → target 75%)

| Module | Cover | Untested paths |
|--------|-------|----------------|
| Core feasibility gates | ~55% | 5-gate edge combinations |

**Tests to add:** Parameterized gate failure tests.

---

## P8 Implementation Plan

| Priority | Service | Target module | Est. tests | Est. effort |
|----------|---------|---------------|------------|-------------|
| P8-1 | cap-svc | scenarios.py, capacity gaps | 15 | 1 d |
| P8-2 | mat-svc | netting.py, material bulk | 12 | 1 d |
| P8-3 | dpe-svc | demand.py, chaos_cost.py | 10 | 1 d |
| P8-4 | nlp-svc | orchestrator, copilot | 8 | 0.5 d |
| P8-5 | alert-svc, fea-svc | war_room, gates | 10 | 0.5 d |
| P8-6 | All | Lower fail_under to 75 in pyproject | — | 0.5 d |

**Total effort:** ~4–5 days for 75%+ across six services.

---

## Quick Wins (v7.0.0 minimum)

1. Align `fail_under=75` on cap/mat/dpe (already near threshold)
2. Add 5–10 API tests per service for highest-line-count gaps
3. Save combined report to `docs/coverage-report-v7.md` after P8

---

## References

- `docs/coverage-summary.md` (Wave 2C)
- `services/*/pyproject.toml` `[tool.coverage.report]`
