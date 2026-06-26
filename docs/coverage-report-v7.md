# Coverage Report — v7.0.0

**Date:** 2026-06-26  
**Command:** `uv run pytest tests/ -m "not integration" --cov=app --cov-report=term`

---

## Service Results

| Service | Coverage | Gate | Tests | Status |
|---------|----------|------|-------|--------|
| cap-svc | **68.26%** | 60% | 249 pass | ✅ Gate met |
| mat-svc | **65.35%** | 60% | 108 pass | ✅ Gate met |
| dpe-svc | **66.71%** | 60% | 154 pass | ✅ Gate met |
| alert-svc | **67.18%** | 80% | 17 pass | ⚠️ Below 80% gate |
| nlp-svc | **55.69%** | 80% | 68 pass | ⚠️ Below 80% gate |
| fea-svc | **55.45%** | 80% | 68 pass | ⚠️ Below 80% gate |

**Average (6 services): ~63%**  
**Target (v7.0.0): ≥75% per service**

---

## P8 Additions This Release

- `dpe-svc/tests/test_chaos_cost_helpers.py` — 7 tests for chaos cost categorization
- `mat-svc/tests/test_netting_priority.py` — 3 tests for demand priority sorting
- Wave 2C tests: mat check-availability, cap approve 409, dpe tariff exposure

---

## Gap to 75%

| Service | Gap | Priority modules |
|---------|-----|------------------|
| cap-svc | +6.7% | scenarios.py, project_plan_service.py |
| mat-svc | +9.7% | netting.py DB paths, supplier_model.py |
| dpe-svc | +8.3% | demand.py, admin.py |
| nlp-svc | +19.3% | orchestrator.py, copilot API |
| alert-svc | +7.8% | war_room.py, consumers.py |
| fea-svc | +19.6% | gate combinations |

**Estimated effort to 75%:** 3–4 additional days (see `docs/coverage-gap-analysis-v6.1.md`).

---

## Recommendation

v7.0.0 ships with **60% enforced gate** on core services (cap/mat/dpe) and documented path to 75% in v7.1. Alternatively, defer v7.0.0 tag until P8 complete.
