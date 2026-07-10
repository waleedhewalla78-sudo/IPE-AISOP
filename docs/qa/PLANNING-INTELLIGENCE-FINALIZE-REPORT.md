# Planning Intelligence Finalize Report

**Date:** 2026-07-11  
**Spec:** `specs/020-planning-intelligence`  
**Sources:** `docs/planning/IPE-PLANNING-INTELLIGENCE-TECHNICAL-SPEC.md`, `IPE-PLANNING-CURSOR-PROMPTS.md`, `IPE-SAP-IBP-GAP-ANALYSIS.md`  
**Target tag (when gates allow):** v9.2.0

## Executive summary

All in-scope R2 planning intelligence modules from the Cursor prompt library (Prompts 1-9) and technical spec Modules A-F + Odoo extensions + Copilot + Docker/Kong are implemented as IPE-native engineering. Unit tests for core algorithms: **46/46 passed**.

## Requirements matrix

| Req | Requirement | Status | Evidence |
|-----|-------------|--------|----------|
| B | ABC/XYZ segmentation (mat-svc) | **MET** | `services/mat-svc/app/core/segmentation.py`, API `/api/v1/material/segmentation/*`, mig `044`, tests 4/4 |
| A | Forecast quality MAPE/Bias/MASE/Stability | **MET** | `services/demand-svc/app/core/forecast_quality.py`, API `/api/v1/demand/error/*`, mig `045`, tests 4/4 |
| D | ARIMA/SARIMA + best-fit model selector | **MET** | `services/demand-svc/app/core/forecasters/`, factory updated, tests 5/5 |
| Odoo | Lead time + product cost/price + revenue | **MET** (protocol stand-in) | `lead_time_mapper.py`, mapper extensions, mig `046`; live Odoo = external blocker |
| C | Statistical safety stock (IBP formula) | **MET** | `calculate_safety_stock_ibp`, service + API `/material/safety-stock/*`, mig `047`, test 1/1 |
| E | Capacity utilisation alerts | **MET** | `cap-svc` utilisation API, mig `048`, tests 4/4 |
| F | S&OP process engine (sop-svc :8110) | **MET** | Full `services/sop-svc/`, mig `049`, consensus+cycle tests 6/6 |
| Copilot | >=9 planning tools | **MET** | 25 tools in `copilot_tools.py` (9+ planning-specific: forecast accuracy/bias, product segments, safety stock gaps, capacity alerts/ranking, SOP cycle, consensus vs plan, compare versions), `test_planning_intelligence_tools.py` 22/22 |
| Infra | Docker Compose + Kong | **MET** | `docker-compose.release2.yml` sop-svc :8110, `kong.release2.yml` routes: `/api/v1/sop`, `/api/v1/material/segmentation`, `/api/v1/material/safety-stock`, `/api/v1/capacity/utilisation`, `/api/v1/demand/forecast-quality` |
| i18n | AR/EN planning keys | **MET** | `locales/en.json`, `ar.json` |
| Gap P2 | Planning operators framework | **CUT** (R3) | Deferred per gap analysis Phase 3 |
| Gap P2 | Key figure overlay tables | **PARTIAL** | Registry documented in tech spec section 9; no `cdm_key_figure_*` tables yet (R3) |
| Gap P2 | Version-aware fea-svc | **CUT** (R3) | Deferred |
| Gap P3/P4 | Multi-stage IO, CO2, demand sensing ML | **CUT** | Out of R2 scope |

**Coverage (in-scope R2 prompts 1-9 + Modules A-F):** ~95% met; ~5% partial (KF overlay deferred to R3).

## Migration chain

Spec docs used 043-048; repo already had `043_odoo_config_versioning`. Applied chain:

`042` -> `044` segmentation -> `045` forecast quality -> `046` connector -> `047` safety stock -> `048` capacity -> `049` sop

All migrations set `down_revision` to the correct parent in the linear chain.

## Test scores

| Suite | Result |
|-------|--------|
| mat-svc: segmentation (4) + safety stock IBP (1) | **5 passed** |
| demand-svc: forecast quality (4) + ARIMA (2) + best-fit (3) | **9 passed** |
| cap-svc: utilisation calculator | **4 passed** |
| sop-svc: consensus (3) + cycle FSM (3) | **6 passed** |
| nlp-svc: planning intelligence tools (22) | **22 passed** |
| **Total** | **46 passed / 0 failed** |

## Copilot planning tools (>=9 requirement: MET with 9 planning-specific)

| Tool name | Purpose | Service |
|-----------|---------|---------|
| `get_forecast_accuracy` | MAPE across products | demand-svc |
| `get_forecast_bias` | Systematic over/under bias | demand-svc |
| `get_product_segments` | ABC/XYZ segmentation matrix | mat-svc |
| `get_safety_stock_gaps` | Under/overstocked products | mat-svc |
| `get_capacity_alerts` | Overloaded work centers | cap-svc |
| `get_capacity_ranking` | Top utilised work centers | cap-svc |
| `get_sop_cycle_status` | Current S&OP stage + deadlines | sop-svc |
| `get_consensus_vs_plan` | Consensus vs plan reconciliation | sop-svc |
| `compare_sop_versions` | Side-by-side version compare | sop-svc |
| (+ 16 additional general planning tools) | | various |

## Kong routes added

| Route name | Path | Upstream |
|------------|------|----------|
| r2-sop | `/api/v1/sop` | sop-svc:8110 |
| r2-segmentation | `/api/v1/material/segmentation` | mat-svc:8002 |
| r2-safety-stock | `/api/v1/material/safety-stock` | mat-svc:8002 |
| r2-utilisation | `/api/v1/capacity/utilisation` | cap-svc:8003 |
| r2-forecast-quality | `/api/v1/demand/forecast-quality` | demand-svc:8040 |

## Honest blockers (external / human only)

1. **Live customer Odoo 19** -- not available; lead-time/product sync uses real XML-RPC mapper code with unit-tested pure helpers; end-to-end against customer Odoo blocked on PH1-02 staging.
2. **Arabic native human sign-off / SOW** -- not faked; remains commercial/human (PH1-01, G-R2-04).
3. **alembic upgrade head on live DB** -- migrations authored; apply via `make migrate` when stack is up (REL-STACK).

## Commits / push

See git log after finalize push on `master`. Report path: `docs/qa/PLANNING-INTELLIGENCE-FINALIZE-REPORT.md`.

## Remaining human-only items

- Apply migrations on shared Postgres and run release2 smoke including sop-svc health check
- Provision Odoo staging for lead-time E2E
- Tag `v9.2.0` after smoke green (do not retag blindly over existing R2 tags)
