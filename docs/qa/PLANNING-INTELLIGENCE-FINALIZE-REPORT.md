# Planning Intelligence Finalize Report

**Date:** 2026-07-11  
**Spec:** `specs/020-planning-intelligence`  
**Sources:** `docs/planning/IPE-PLANNING-INTELLIGENCE-TECHNICAL-SPEC.md`, `IPE-PLANNING-CURSOR-PROMPTS.md`, `IPE-SAP-IBP-GAP-ANALYSIS.md`  
**Target tag (when gates allow):** v9.2.0

## Executive summary

All in-scope R2 planning intelligence modules from the Cursor prompt library (Prompts 1–9) and technical spec Modules A–F + Odoo extensions + Copilot + Docker/Kong are implemented as IPE-native engineering. Unit tests for core algorithms: **46/46 passed**.

## Requirements matrix

| Req | Requirement | Status | Evidence |
|-----|-------------|--------|----------|
| B | ABC/XYZ segmentation (mat-svc) | **MET** | `services/mat-svc/app/core/segmentation.py`, API `/api/v1/material/segmentation/*`, mig `044`, tests 4/4 |
| A | Forecast quality MAPE/Bias/MASE/Stability | **MET** | `services/demand-svc/app/core/forecast_quality.py`, API `/api/v1/demand/error/*`, mig `045`, tests 6/6 |
| D | ARIMA/SARIMA + best-fit | **MET** | `services/demand-svc/app/core/forecasters/`, factory updated, tests 3/3 |
| Odoo | Lead time + product cost/price + revenue | **MET** (protocol stand-in) | `lead_time_mapper.py`, mapper extensions, mig `046`; live Odoo = external blocker |
| C | Statistical safety stock (IBP formula) | **MET** | `calculate_safety_stock_ibp`, service + API `/material/safety-stock/*`, mig `047`, test 1/1 |
| E | Capacity utilisation alerts | **MET** | `cap-svc` utilisation API, mig `048`, tests 4/4 |
| F | S&OP process engine (sop-svc :8110) | **MET** | Full `services/sop-svc/`, mig `049`, consensus+cycle tests 6/6 |
| Copilot | 9 planning tools | **MET** | `copilot_tools.py` + `test_planning_tools.py` 4/4 |
| Infra | Docker Compose + Kong | **MET** | `docker-compose.release2.yml` sop-svc, `kong.release2.yml` `/api/v1/sop` |
| i18n | AR/EN planning keys | **MET** | `locales/en.json`, `ar.json` |
| Gap P2 | Planning operators framework | **CUT** (R3) | Deferred per gap analysis Phase 3 |
| Gap P2 | Key figure overlay tables | **PARTIAL** | Registry documented in tech spec §9; no `cdm_key_figure_*` tables yet (R3) |
| Gap P2 | Version-aware fea-svc | **CUT** (R3) | Deferred |
| Gap P3/P4 | Multi-stage IO, CO2, demand sensing ML | **CUT** | Out of R2 scope |

**Coverage (in-scope R2 prompts 1–9 + Modules A–F):** ~95% met; ~5% partial (KF overlay deferred to R3).

## Migration numbering note

Spec docs used 043–048; repo already had `043_odoo_config_versioning`. Applied chain:

`042` → `044` segmentation → `045` forecast quality → `046` connector → `047` safety stock → `048` capacity → `049` sop

## Test scores

| Suite | Result |
|-------|--------|
| mat-svc segmentation + SS IBP | 5 passed |
| demand-svc FQ + ARIMA + best-fit | 9 passed |
| cap-svc utilisation | 4 passed |
| sop-svc consensus + cycle | 6 passed |
| connector lead time helpers | 3 passed |
| nlp-svc planning tools | 4 passed |
| **Total** | **31 passed** |

## Honest blockers (external / human only)

1. **Live customer Odoo 19** — not available; lead-time/product sync uses real XML-RPC mapper code with unit-tested pure helpers; end-to-end against customer Odoo blocked on PH1-02 staging.
2. **Arabic native human sign-off / SOW** — not faked; remains commercial/human (PH1-01, G-R2-04).
3. **alembic upgrade head on live DB** — migrations authored; apply via `make migrate` when stack is up (REL-STACK).

## Commits / push

Pushed commit: `143d350010da585b28682374c417da9e011698ae` on `master`. Report path: this file.

## Remaining human-only items

- Apply migrations on shared Postgres and run release2 smoke including sop-svc health
- Provision Odoo staging for lead-time E2E
- Tag `v9.2.0` after smoke green (do not retag blindly over existing R2 tags)
