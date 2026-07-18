# Implement — Spec 029 Productionization

**Date**: 2026-07-18 · **Constitution**: 1.4.1 · **Migration head**: 069

## Delivered (Wave 1)

| Item | Change |
|------|--------|
| Kong enterprise | `r2-enterprise` path `/api/v1/enterprise` in `kong.release2.yml`; deploy `st-enterprise` + `st-planning-command` |
| Andon dual-write | `AndonAlert` model + `andon_persist.py`; phase7 API marks `persisted` |
| RLS 068 | Enable RLS on location/project_plan/sop_forecast/plan; EXISTS policies for scenario children + worker_skill_link; tenant self-scope |
| MPS/MRP 069 | `cdm_mps_run` / `cdm_mrp_run` + `persist=true` on `/mps` and `/mrp/explode` |
| Stage-gate | `SopStageGateMachine` + GET/POST `/planning-command/sop/stage-gate*` |
| QA notes | `SPEC029-K6-P95-NOTES.md`, `SPEC029-PLAYWRIGHT-FLAKE-NOTES.md`, Phase3+ e2e stub (skipped) |
| Pointers | feature.json, AGENTS.md, constitution 1.4.1, PRODUCT-STATUS |

## Tests

```
cd services/dpe-svc
uv run pytest tests/test_spec029_productionization.py tests/test_phase7_operations.py tests/test_phase7_api.py -q
# 27 passed
```

## Stack-dependent (NOT done)

R2 Kong/dpe health timed out — seed MOs + `star-trans-validate` (#70/#72/#110) remain OPEN. Do not fake PASS.

## COM (unchanged OPEN)

OQ-7 (#106), PH1-02 (#108), G-R2-04 (#109), OQ-1 (#107).
