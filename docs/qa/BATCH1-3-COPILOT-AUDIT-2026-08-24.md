# BATCH1-3 — Copilot audit trail

**Date:** 2026-08-24  
**Branch:** `batch1-foundation-hardening`  
**Alembic:** **085** applied on `ipe_test`

## Schema

`cdm_copilot_audit`: UUID PK, tenant_id RLS FORCE, query/response/context/sources, HMAC `integrity_hash`, append-only trigger (UPDATE/DELETE raise). No retroactive rows.

## Wiring

- `nlp-svc` `POST /api/v1/copilot/query` writes one audit row best-effort (failure does not block the answer)
- Admin API: `GET /api/v1/governance/copilot-audit`, `/{query_id}`, `/export` (`require_roles(["admin"])`)
- UI component `CopilotAuditPage.tsx` (intended `/ai-governance/copilot-audit`). Router/lazyRoutes **not** committed — those files are mixed with unrelated dirty tree
- `python -m app.verify_audit_integrity` for last-24h HMAC check

## Tests

`pytest services/tests/governance/test_copilot_audit.py -v` → **8/8 PASS**

## VERDICT

**YELLOW** — ENG audit table + API + 8/8 tests; UI route not committed from dirty web router; no retroactive backfill.
