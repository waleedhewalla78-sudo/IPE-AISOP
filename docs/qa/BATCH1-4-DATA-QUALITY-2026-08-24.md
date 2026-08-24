# BATCH1-4 — Data quality dashboard

**Date:** 2026-08-24  
**Alembic:** **086** `cdm_data_quality_report` FORCE RLS  
**Catalog:** 45 checks across ingest entities + one operational MO check. Every check has `fix_guidance`. Engine does **not** auto-fix.

## Surfaces

- `dpe-svc` `app/data_quality/{catalog,engine}.py`
- API module `app/api/v1/data_quality.py` (admin `/run`, `/catalog`) — **not** included in dirty `dpe-svc` router.py
- UI `apps/web/src/features/admin/DataQualityPage.tsx` (route wiring not committed from dirty web router)
- Seed helper `scripts/seed-dq-test-data.ps1`

## Tests

`pytest services/tests/data_quality/test_dq_engine.py -v` → **8/8 PASS**

## VERDICT

**YELLOW** — catalog+engine+migration+tests; API/UI not mounted in dirty routers; no overnight cron in cluster.
