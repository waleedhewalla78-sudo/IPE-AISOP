# BATCH2-1 — Star Trans tenant provisioning — 2026-08-24

**Branch:** `batch2-startrans-onboarding` (from `batch1-foundation-hardening` @ `59cfd42`, not from merged `033-phase9-wave9a`)  
**Lab DB:** `ipe_test` @ localhost:5433  
**Alembic after apply:** **087**  
**COM:** **OPEN**. PH1-02 / G-R2-04 / OQ-7 / C-01…C-08 unchanged.  
**Production Odoo / Hetzner:** **not used**.

---

## 1. Prerequisite verification

| Check | Result |
|-------|--------|
| Batch 1 PR 164 merged to `033-phase9-wave9a` | **FAIL** — PR 164 still **OPEN**. File-2 would STOP. Operator authorized Batch 2 on YELLOW with a branch cut from Batch 1. |
| Migration head before 087 | **086** on lab (not production) |
| BATCH1-1 RLS against lab | **8/8 PASS** (retest) |
| SOW signed + countersigned in repo | **Not independently verified**. Operator instruction: execute now. |
| Production DB | **Not touched** (constraint) |

Not GREEN. Proceeded as **lab scaffold** only.

---

## 2. Tenant configuration summary

See `deploy/tenants/star-trans/tenant-config.yml`.

- Name Star Trans / slug `star-trans`
- Reference customer + Enterprise license + Phase 1 business-hours support
- Hosting/residency: Hetzner EU-East **intent** (not provisioned)
- Timezone Africa/Cairo; locale en-EG / ar-EG; currency EGP
- Contract dates **null** (SOW scan not in repo)

---

## 3. Migration 087

`migrations/versions/087_provision_startrans_tenant.py`

- Tables: `cdm_tenant_onboarding`, `cdm_tenant_hmac_ref` with FORCE RLS (`app.current_tenant_id`)
- Idempotent `ON CONFLICT` upsert
- `down()` drops registry + placeholder admin; **does not** delete seeded `cdm_tenant` / 28 MOs
- HMAC stored as **secret_ref only** (no production secret in git)

Applied on **lab** `ipe_test` only.

---

## 4. Infrastructure files

Under `deploy/tenants/star-trans/`:

- `tenant-config.yml`, `env.production` (placeholders), `docker-compose.override.yml`
- `kong-routes.yml`, `nginx.conf` (commented), `README.md`, `RUNBOOK.md`, `oncall.md`, `langfuse.md`

Monitoring:

- `infrastructure/monitoring/prometheus/alerts-star-trans.yml`
- `infrastructure/monitoring/dashboards/ipe-star-trans-tenant.json`

---

## 5. Provisioning results (lab)

| Field | Value |
|-------|--------|
| slug | `star-trans` |
| lab tenant_id | `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11` |
| canonical_uuid | `6a7281ee-62cb-5a72-8162-d3c573e54877` |
| hmac_secret_ref | `hetzner-secrets://ipe/tenants/star-trans/copilot-hmac` |
| storage_namespace | `s3://ipe-tenant-star-trans` |
| placeholder user | `admin@startrans.eg` role=admin **is_active=false** no password |
| MO count unchanged | **28** |

Did **not** insert a second `cdm_tenant` (would split seed data).

---

## 6. Monitoring

Alert YAML + Grafana JSON added. Prometheus/Grafana on this lab **not confirmed scraping** the new file. Langfuse project **not created** (no API keys).

---

## 7. Smoke tests

| # | Step | Result |
|---|------|--------|
| 1 | Web :8082 | **PASS** 200 |
| 2 | Kong health | **PASS** 200 |
| 3 | Onboarding row present | **PASS** |
| 4 | RLS: tenant B count=0, tenant A count=1 (`ipe_rls_app`) | **PASS** |
| 5 | Placeholder admin cannot login (no hash, inactive) | **PASS** (by design) |
| 6 | JWT login via Kong with printed private key | **SKIP** (agent policy — do not dump signing key) |
| 7 | Executive Home empty state | **N/A** — lab already has 28 MOs, not an empty tenant |
| 8 | Admin DQ dashboard API | **FAIL** 404 Kong + catalog not on running dpe image |
| 9 | Copilot audit API | **FAIL** 404 (running nlp image / Kong route) |
| 10 | Cross-tenant read | **PASS** at SQL RLS (API 403 not re-proven without JWT mint) |

Must-PASS-all from the prompt: **not met**.

---

## 8. Runbook

`deploy/tenants/star-trans/RUNBOOK.md`

---

## VERDICT

**YELLOW**

Lab registry + 087 + RLS isolation for the onboarding row are real. This is **not** a production Star Trans tenant on Hetzner, **not** a merged Batch 1 base, **not** an empty-tenant UI walkthrough, and Copilot/DQ admin APIs 404 on the warm R2 images. Ready for BATCH2-2 **review file only**, not for user/data load.
