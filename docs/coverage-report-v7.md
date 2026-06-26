# Coverage Report — v7.0.0

**Date:** 2026-06-26 (P8 continuation)  
**Command:** `uv run pytest tests/ -m "not integration" --cov=app --cov-report=term`

---

## Service Results

| Service | Coverage | Gate | Tests | vs 75% target |
|---------|----------|------|-------|---------------|
| cap-svc | **68.26%** | 60% ✅ | 249 | −6.7 pts |
| mat-svc | **68.20%** | 60% ✅ | 114 | −6.8 pts |
| dpe-svc | **66.89%** | 60% ✅ | 156 | −8.1 pts |
| alert-svc | **69.04%** | 80% ❌ | 19 | −5.9 pts |
| nlp-svc | **57.47%** | 80% ❌ | 80 | −17.5 pts |
| fea-svc | **55.45%** | 80% ❌ | 71 | −19.6 pts |

**Average:** ~64.2% · **Target:** ≥75% per service · **Status:** ⚠️ In progress

---

## P8 Additions (this session)

| Service | New tests | Modules targeted (AG-02) |
|---------|-----------|----------------------------|
| mat-svc | `test_supplier_model.py`, `test_netting_priority.py` | supplier_model, netting priority |
| dpe-svc | `test_chaos_cost_helpers.py`, `test_api_demand_no_tenant.py` | chaos_cost, demand API |
| nlp-svc | `test_orchestrator_keywords.py`, war_room in `test_copilot_tools.py` | orchestrator, copilot_tools |
| alert-svc | `test_api_war_room.py` | war_room no-tenant paths |
| fea-svc | `test_labor_autonomy.py` | scorer labor/autonomy |
| shared | `test_healthz.py` | /healthz alias (P7) |

---

## Remaining Gap (per coverage-gap-analysis-v6.1.md)

| Priority | Service | Module | Est. effort |
|----------|---------|--------|-------------|
| 1 | nlp-svc | orchestrator fetchers, copilot API streaming | 1 d |
| 2 | fea-svc | async gate DB paths (`_compute_capacity_gate`) | 1 d |
| 3 | cap-svc | scenarios.py happy path with mocked DB | 0.5 d |
| 4 | mat-svc | netting.py async DB functions | 0.5 d |
| 5 | dpe-svc | demand classify with mocked session | 0.5 d |

**v7.0.0 tag blocked** until all services ≥75% or documented waiver in release checklist.

---

## Per-Service Verify Command

```powershell
cd services\<svc>
uv run pytest tests/ -m "not integration" --cov=app --cov-report=term-missing --cov-fail-under=75 -v
```
