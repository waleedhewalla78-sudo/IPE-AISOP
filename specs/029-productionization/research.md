# Research — Spec 029

## Kong enterprise gap
Phase 6 handlers live under `phase6_enterprise.router` prefix `/enterprise`. R2 Kong has `r2-planning-command` but no enterprise path → 404 via :8000. Fix: add route sibling to planning-command pointing at same dpe-svc upstream.

## Andon persistence
Migration 067 created `cdm_andon_alert` with RLS; Wave 1 API used module-level `AndonBoard()` only. Dual-write preserves unit determinism while enabling durable storage.

## RLS gaps (from rls-tables.txt)
| Table | Fix |
|-------|-----|
| cdm_location, cdm_project_plan, cdm_project_plan_version, cdm_sop_forecast, cdm_sop_plan | ENABLE RLS + tenant_isolation (016 created POLICY without ENABLE) |
| cdm_scenario_demand/supply/resource | EXISTS join to cdm_scenario.tenant_id |
| cdm_worker_skill_link | EXISTS join to cdm_worker.tenant_id |
| cdm_tenant | self-scope: id = current tenant |

## MPS/MRP
Phase 5 `build_mps` / MRP are pure compute. Durable storage = JSON run snapshots keyed by tenant + product + timestamp.

## Stage-gate
`cdm_sop_stage_gate` model exists. Spec 029 adds interactive scaffold (advance / skip-to management_review) without requiring full UI.
