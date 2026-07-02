# Performance Baseline — v9.1.0-r2

**Captured:** 2026-07-02 (Phase 1 verification)  
**Target:** Kong gateway `http://localhost:8000` — Release 1 + prod overlay stack  
**Tool:** k6 v2.0.0 — `scripts/perf/k6-load-test.js`

## How to run

```bash
docker compose -f infrastructure/docker/docker-compose.release1.yml \
               -f infrastructure/docker/docker-compose.prod.yml up -d

k6 run scripts/perf/k6-load-test.js --out json=docs/qa/k6-baseline.json
```

Login uses `email` + `password` via `setup()` (k6 v2 compatible). Raw JSON export: `docs/qa/k6-baseline.json`.

## SLO thresholds (k6)

| Metric | Target | **Actual** | Pass |
|--------|--------|------------|------|
| P95 latency | < 500 ms | **1,740 ms** | ❌ |
| P99 latency | < 2000 ms | **~1,740 ms** (p99 not emitted) | ⚠️ |
| Error rate | < 5% | **28.6%** | ❌ |

> **Note:** Elevated errors driven by Release 2 outcome routes (`404`) and mixed tenant slug vs UUID on some feasibility paths under load. Re-run after Release 2 Kong routes are wired or restrict k6 to Release 1 endpoints only.

## Aggregate results

| Metric | Value |
|--------|-------|
| Total requests | **20,704** |
| P50 (median) | **53.5 ms** |
| P90 | **1,249 ms** |
| P95 | **1,740 ms** |
| Mean latency | **357 ms** |
| Max latency | **11,013 ms** |
| Error rate | **28.6%** |
| RPS (avg) | **96.5 req/s** |
| Peak VUs | **100** |
| Duration | **3m 30s** (+ ramp) |

## Per-endpoint notes (manual spot-check)

| Endpoint | Expected | Observed |
|----------|----------|----------|
| Feasibility Queue | 200 | 200 |
| MDR Score | 200 | 200 (requires auth) |
| Resolution Scenarios | 200 | 200 |
| OTD Baseline | 200 | **404** (route not on Kong R1) |
| ROI Metrics | 200 | **404** (route not on Kong R1) |
| Auth Info | 200 | 200 |
| Health Check | 200 | 200 |

## Resource usage during test

Captured via `docker stats --no-stream` after sustained load:

| Service | CPU % | Memory |
|---------|-------|--------|
| kong | 1.18% | 647 MiB / 1 GiB |
| dpe-svc | 0.38% | 117 MiB / 512 MiB |
| fea-svc | 1.15% | 127 MiB / 512 MiB |
| cap-svc | 1.36% | 237 MiB / 512 MiB |
| res-svc | 0.56% | 117 MiB / 512 MiB |
| connector | 2.30% | 127 MiB / 512 MiB |
| db | 0.00% | 210 MiB / 4 GiB |
| redis | 0.16% | 15 MiB / 512 MiB |

## Database index verification

Migration **037** applied (`036 → 037`). Verified indexes on hot tables:

```sql
-- ix_bom_tenant_product_active, ix_product_tenant_source_type,
-- ix_inventory_tenant_product, ix_mo_tenant_bom_status, ix_audit_tenant_timestamp
```

## Connection pooling

| Setting | Default | Env override |
|---------|---------|--------------|
| `pool_size` | 20 | `IPE_DB_POOL_SIZE` |
| `max_overflow` | 10 | `IPE_DB_MAX_OVERFLOW` |
| `statement_timeout` | 30s | `IPE_DB_STATEMENT_TIMEOUT_MS` |

## Backup verification

```bash
POSTGRES_CONTAINER=docker-db-1 BACKUP_DIR=./backups/postgres bash scripts/backup/pg-backup.sh
# → backups/postgres/ipe_20260702_234000.sql.gz (104K)
```

## Follow-ups

1. Add Release 2 outcome routes to Kong or remove from k6 mix for R1 baseline.
2. Re-run k6 after P95 tuning (index 037 + query review) to meet SLO.
3. Tag per-endpoint latency using k6 `tags` on each request group.

---

_Raw run log: `docs/qa/k6-run-final.log`_
