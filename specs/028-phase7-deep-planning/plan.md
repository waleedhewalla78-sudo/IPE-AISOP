# Implementation Plan: Phase 7 Deep Planning & Operations Intelligence

**Spec**: `specs/028-phase7-deep-planning/spec.md`
**Constitution**: `ipe/.specify/memory/constitution.md` (v1.4.0 — no bump required; additive feature within existing gates)

## Architecture (build-on, do not wipe)

| Prior phase | How Phase 7 reuses it |
|-------------|-----------------------|
| Phase 5 (026) `planning-command` cores (MPS/MRP/ATP/RCCP/leveling/command-ops) | Phase 7 endpoints extend the same `/planning-command` prefix + Kong route; mirror the `phase5` core+API+test layout |
| Phase 5 `performance_cockpit` (OEE strip) | §5 OEE programme deepens measurement into an improvement programme with payback |
| Phase 6 (027) A13/A14/A17 (finance margin, analytics, orchestration) | §2 financial S&OP + portfolio reuse margin conventions; horizon cascade mirrors A17 governance levels |
| Migrations head 063 | Continue 064 → 067 (RLS on every new tenant table) |
| Hubs (Planning / Command Center / Intelligence) | Add tabs only; existing tabs untouched |

## Backend

- New core package `app/core/phase7/` — one module per capability, pure/deterministic compute over supplied inputs with Star-Trans defaults (no live ERP dependency); `AndonBoard` in-memory tracker mirrors the phase5 `ActionTracker` pattern.
- New API `app/api/v1/phase7_deep.py` — `APIRouter(prefix="/planning-command", tags=["phase7-deep-planning"])`; registered in `router.py` after `phase6_enterprise`.
- All endpoints return the shared `APIResponse(success, data, error)` envelope.

## Data

- Migrations 064-067: `cdm_planning_horizon` + `cdm_horizon_cascade`, `cdm_sop_financial_plan`, `cdm_demand_consensus`, `cdm_andon_alert`. Each: `tenant_id` FK → `cdm_tenant`, JSONB payload columns, tenant-index, RLS `tenant_isolation` policy. Wave 1 compute is stateless/in-memory; tables provide durable persistence when wired to the DB layer.

## Frontend

- `features/deep-planning/ThreeHorizonsPage.tsx` — §1 horizon cards + health bars + cascade actions (offline fallback shell).
- `features/deep-planning/DeepDisciplinePages.tsx` — shared `DeepWorkbench` + named pages `SopDeepPage`/`DemandDeepPage`/`ProductionDeepPage`/`OperationsDeepPage`.
- Routes/constants/lazyRoutes + hub tabs: Planning→Horizons, Command Center→Operations Deep, Intelligence→S&OP/Demand/Production Deep.

## Testing

- `test_phase7_horizons.py`, `test_phase7_sop_financial.py`, `test_phase7_demand_decomp.py`, `test_phase7_scheduling.py`, `test_phase7_operations.py` (core, DB-free) + `test_phase7_api.py` (ASGI in-process smoke).
- Full dpe-svc regression (`uv run pytest -q`) must stay green.
- Kong :8000 live smoke after rebuilding the dpe-svc image (Phase 7 code post-dates the E2E-run image).
- Frontend `tsc --noEmit`.

## Honesty / constraints

- Digital Gemba + real-time WC status = IoT/MES STUB (`iot_live=false`, PH1-02 OPEN). Operator tablet UI minimal.
- COM blockers (OQ-7 / PH1-02 / G-R2-04 / Odoo 17-19) OPEN — not faked, no tag applied.
- Git: env author `IPE Agent <ipe-agent@local>`; fast-forward push only; never push stale `v9.1.0-r2`.
