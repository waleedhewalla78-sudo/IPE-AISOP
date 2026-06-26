# Coverage Report — v7.0.0 (P8 Final)

**Date:** 2026-06-24  
**Command:** `uv run pytest tests/ -m "not integration" --cov=app --cov-fail-under=75 --cov-report=term-missing`

---

## Service Results

| Service | Before (v6.1) | After (v7) | Gate | Tests | Status |
|---------|---------------|------------|------|-------|--------|
| nlp-svc | 57% | **77.94%** | 75% ✅ | 134 | ✅ |
| fea-svc | 55% | **75.25%** | 75% ✅ | 91 | ✅ |
| cap-svc | 68% | **75.48%** | 75% ✅ | 275 | ✅ |
| mat-svc | 68% | **75.77%** | 75% ✅ | 121 | ✅ |
| dpe-svc | 67% | **75.77%** | 75% ✅ | 178 | ✅ |
| alert-svc | 69% | **88.54%** | 75% ✅ | 25 | ✅ |

**Average:** ~78.1% · **Target:** ≥75% per service · **Status:** ✅ **P8 COMPLETE**

> **Note:** `auth-svc` and `mdr-svc` live inside `dpe-svc` (`app/api/v1/auth.py`, `app/core/mdr_engine.py`). Auth and MDR coverage is included in dpe-svc totals.

---

## Round 1 — Biggest gaps (nlp + fea)

### nlp-svc (57% → 78%)
- `test_orchestrator_fetchers.py`, `test_llm_client_extended.py`, `test_copilot_agent.py`
- `test_response_formatter_extended.py`, `test_consumers_lifecycle.py`

### fea-svc (55% → 75%)
- `test_labor_autonomy.py`, `test_scorer_gates_mock.py`, `test_auto_confirm.py`
- `test_disruption_ws.py`, `test_event_handlers.py`, `test_ws_manager.py`

---

## Round 2 — Remaining services

### cap-svc (68% → 75%)
- `test_project_plan_service_extended.py`, `test_scenarios_disruption.py`, `test_scenarios_solve.py`
- `test_scenarios_diff.py`, `test_labor_unit.py`, `test_priority_resolver_extended.py`
- `test_event_handlers_unit.py`

### mat-svc (68% → 76%)
- `test_netting_mock.py`, `test_netting_extended.py`, `test_event_handlers_unit.py`

### dpe-svc (67% → 76%)
- `test_mdr_engine.py`, `test_mdr_remediation.py`, `test_mdr_api.py`
- `test_auth_verify.py`, `test_classifier.py`, `test_stripe_billing.py`
- `test_dpe_handlers.py`, `test_dpe_handlers_success.py`, `test_dpe_handlers_inventory.py`
- `test_chaos_cost_aggregate.py`, `test_margin_priority.py` (extended)

### alert-svc (69% → 89%)
- `test_war_room_recovery.py`, `test_war_room_extended.py`

---

## pyproject.toml gates updated

All six services now use `fail_under = 75` in `[tool.coverage.report]`.

---

## Next: P11 Regression

```powershell
.\scripts\rel-demo-stack.ps1
.\scripts\run-full-demo.ps1 -ReportPath docs\final-regression-demo.txt
.\scripts\run-chaos-scenarios.ps1
```

Then tag `v7.0.0` after P11 green.
