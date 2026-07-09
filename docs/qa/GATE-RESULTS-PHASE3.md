# Gate Results — Phase 3 (2026-07-09)

| Gate | Result | Evidence |
|------|--------|----------|
| Gate 6 — Helm lint/template | **PASS** | `scripts/k8s/verify-gate6.ps1` |
| Gate 7 — kind deploy + health | **PASS** | kind `ipe-dev`; all R1 pods Running; ingress 200 |
| Gate 8 — Compose–K8s parity | **PASS** | `evidence/gate8-parity.txt` |
| Gate 9 — HPA smoke | **PASS** | `evidence/gate9-hpa.txt` |
| Gate 10 — ERP scaffolds | **PASS** | `tests/test_erp_scaffolds.py` |
| Gate 11 — R1 demo on K8s | **12/14 PASS (OQ-9 waiver)** | `docs/demo-data/gate11-k8s-demo.txt` + `docs/demo-data/gate11-oq9-waiver.md` (2026-07-09) |

## Gate 11 notes (2026-07-07, latest)

- **PASS (12):** login, Odoo config/test, full Odoo→CDM sync, sync audit, data quality, feasibility queue/KPIs, resolution scenarios, MDR gate (92%), OTD baseline, ROI metrics
- **FAIL (2):** OR-Tools schedule (cap-svc) — 300s timeout on kind; schedule approve (depends on step 10)
- **Fixes applied:** Odoo creds in sync body (per-pod KMS); `seed-startrans-mdr-boost.sql` via K8s Postgres; full `seed-data.sh` via `seed-k8s-db.ps1`
- **Blocker:** cap-svc OR-Tools solver exceeds ingress timeout under kind CPU load; HPA + repeated rollouts caused transient 503s after long runs

## Gate 11 history

| Run | Score | Notes |
|-----|-------|-------|
| Initial | 7/14 | Minimal seed, cap-svc 503 |
| After seed-data | 10/14 | No sync creds |
| Sync creds + MDR boost | 12/14 | Schedule timeout |

## Fixes applied (2026-07-07)

- Migration 028: `CREATE EXTENSION pgcrypto` before SHA-256 backfill
- `migrate-k8s-db.ps1`: uses `IPE_DATABASE_URL_SYNC` (alembic env.py)
- T169: Kafka-optional health probes; compose `IPE_KAFKA_BOOTSTRAP_SERVERS=""`
- K8s DB: alembic head + `seed_dev_data.py` + Ahmed@nour user for login

## Tag policy

**`v9.4.0-p3`** tagged with **OQ-9 waiver** evidence package (Constitution Principle VIII). Compose path remains **14/14** (`docs/demo-data/release1-integration-demo.txt`). kind steps 10–11 deferred to [#27](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/27).
