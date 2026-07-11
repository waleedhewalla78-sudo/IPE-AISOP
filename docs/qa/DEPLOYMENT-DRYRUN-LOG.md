# Deployment Dry-Run Log

**Date:** 2026-07-11  
**Environment:** Development workstation (Windows 10, Docker Desktop)  
**Compose file:** `deploy/star-trans/docker-compose.yml`  
**Sprint:** Sprint 3 — S3-ENG-01 / Spec 022 T001–T003  
**Mode:** Package self-containment validation (compose config + env coverage + runbook accuracy). Full clean-VM container start deferred to customer image delivery (pre-built `ipe-*:release1` images).

---

## Package Contents Verified

| File | Status |
|------|--------|
| `deploy/star-trans/docker-compose.yml` | OK |
| `deploy/star-trans/.env.template` | OK |
| `deploy/star-trans/kong.star-trans.yml` | OK |
| `deploy/star-trans/DEPLOY-RUNBOOK.md` | OK (Sprint 3 corrections) |
| `deploy/star-trans/SMOKE-TEST.md` | OK |

---

## Verification Results

- [x] `deploy/star-trans/` directory complete (5 files)
- [x] Compose file validates (`docker compose config --quiet`) when `.env` is present — **exit 0** (Spec 022 T002, 2026-07-11)
- [x] All `${VAR}` interpolations in compose covered by `.env.template`
- [x] `DEPLOY-RUNBOOK.md` commands match compose service names and health paths
- [x] `.env.template` has clear instructions for each variable
- [x] Temp `.env` used for config validation was **removed** (not committed)

### Env var coverage (compose → template)

| Variable | Status |
|----------|--------|
| `DATABASE_URL` | OK |
| `POSTGRES_PASSWORD` | OK |
| `ODOO_URL` | OK |
| `ODOO_DB` | OK |
| `ODOO_USER` | OK |
| `ODOO_PASSWORD` | OK |

Additional template vars (defaults / optional): `POSTGRES_USER`, `POSTGRES_DB`, `REDIS_URL`, `IPE_JWT_SECRET_KEY`, `AUTH_MODE`, `ODOO_SYNC_INTERVAL_SEC`, `AUTO_PROPOSE_THRESHOLD`, `IPE_RELEASE_PROFILE`, Kafka/OTEL flags.

### Compose validation notes

1. Without `.env`, `docker compose config` fails with `env file ... .env not found`. **Fix:** always `cp .env.template .env` first.
2. With a filled `.env` (test values), `docker compose -f deploy/star-trans/docker-compose.yml config --quiet` exits **0**.
3. Service names: `db`, `redis`, `dpe-svc`, `fea-svc`, `res-svc`, `cap-svc`, `mat-svc`, `connector`, `kong`, `web-ui`.
4. Healthchecks use `/api/v1/health` (not `/healthz`). Runbook Step 6 includes `res-svc:8005`.
5. Kong admin published on host **8444** (not 8001) to avoid clash with `dpe-svc` host port 8001.

---

## Issues Found and Fixed

| Issue | Fix applied |
|-------|-------------|
| Runbook Step 10 referenced non-existent `scripts/seed-data.py` | Updated to `docs/demo-data/star-trans-seed.sql` via `psql` |
| Runbook omitted `POSTGRES_USER` / `POSTGRES_DB` | Added; noted `.env` is mandatory |
| Health check list omitted `res-svc` | Added port 8005 |
| Validate script PS 5.1 em-dash parse errors | ASCII separators + UTF-8 BOM (Spec 022) |
| Validate wrong host ports on R2 compose | `-DpePort` / `-ConnectorPort` params |
| Validate `ar.json` cwd-relative miss | Resolve via repo root |
| Validate DB name `ipe` vs `ipe_test` | Auto-detect `POSTGRES_DB` |

---

## Assessment

**Deployment package is ready for customer deployment** pending:

1. Delivery of pre-built images **or** source build per runbook Step 3.
2. Customer `.env` values (Odoo host, DB password, JWT secret).
3. Commercial SOW signature before live Odoo staging sync (COM — not engineering).

Estimated time from configured `.env` to healthy stack (excluding image pulls/builds): **&lt; 30 minutes**, matching S3-ENG-01 acceptance.
