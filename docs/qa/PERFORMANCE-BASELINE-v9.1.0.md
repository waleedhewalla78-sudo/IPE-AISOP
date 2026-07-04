# Performance Baseline — v9.1.0-r2 → v9.3.0-p2

**Last updated:** 2026-07-03 (Phase 2 close — Task 1C)  
**Target:** Kong gateway `http://localhost:8000` — Release 1 + prod overlay stack  
**Tool:** k6 v2.0.0

---

## Performance Testing Strategy (v9.3.0-p2)

### Two Profiles

| Profile | Script | Purpose | Rate | Expected Result |
|---------|--------|---------|------|-----------------|
| **SLO Baseline** | `k6-slo.js` | Measure real service latency under normal load | ~5–8 VU, throttled to &lt;8 req/s | P95 &lt; 500ms, error &lt; 5% |
| **Stress / Rate Limit** | `k6-stress.js` | Validate Kong rate limiter behavior | Setup burst 700 req + 20–50 VU sustained | 429 after ~500 req/min (**CORRECT**) |

### How to run

```powershell
cd ipe
docker compose -f infrastructure/docker/docker-compose.release1.yml `
               -f infrastructure/docker/docker-compose.prod.yml up -d

# Health
curl.exe -sf http://localhost:8000/api/v1/health

# SLO (MUST pass)
k6 run scripts/perf/k6-slo.js --out json=docs/qa/k6-slo-metrics.ndjson

# Stress (429 expected — validates rate limiter)
k6 run scripts/perf/k6-stress.js --out json=docs/qa/k6-stress-metrics.ndjson
```

Or use runners: `.\scripts\run-k6-slo.ps1` / `.\scripts\run-k6-stress.ps1`.

Summaries: `docs/qa/k6-slo-baseline.json`, `docs/qa/k6-stress-baseline.json`.

### SLO PASS Criteria

| Check | Criteria |
|-------|----------|
| `k6-slo.js` | ALL thresholds green (P95 &lt; 500ms, error rate &lt; 5%) |
| `k6-stress.js` | 429 rate &gt; 1% (confirms rate limiter works) |
| Baseline doc | Updated with new numbers (this file) |

---

## SLO Baseline Results (v9.3.0-p2)

**Captured:** 2026-07-03 22:48 (+03)  
**Script:** `scripts/perf/k6-slo.js`  
**Auth:** Keycloak (`admin@ipe.example.com`)  
**Endpoints:** health, feasibility/queue, feasibility/kpis, analytics/otd-baseline, resolution/scenarios

```
=== k6 SLO Summary (Phase 2) ===
Requests: 594
P95: 292.99ms (target < 500ms)
Error rate: 0.00% (target < 5%)
SLO: PASS
```

| Metric | Target | **Actual** | Pass |
|--------|--------|------------|------|
| P95 latency | &lt; 500 ms | **293 ms** | ✅ |
| Error rate | &lt; 5% | **0.00%** | ✅ |
| Total requests | — | **594** | — |
| Peak VUs | — | **8** | — |
| Duration | — | **3m 20s** (+ setup) | — |

Raw: `docs/qa/k6-slo-baseline.json`, stream: `docs/qa/k6-slo-metrics.ndjson`.

---

## Stress Test Results (v9.3.0-p2)

**Captured:** 2026-07-03 22:50 (+03)  
**Script:** `scripts/perf/k6-stress.js`  
**Kong limit:** 500 req/min per client IP (`kong.release1.yml`)

```
Setup burst: 606 x 200, 94 x 429 (700 total)

=== Stress Test Summary ===
Rate limit (429) hit rate: 73.8%
Rate limit (429) count: 2580
Total requests: 3498
Status: PASS — Rate limiter is working correctly
```

| Metric | Target | **Actual** | Pass |
|--------|--------|------------|------|
| 429 rate | &gt; 1% | **73.8%** | ✅ |
| 429 count | &gt; 0 | **2580** | ✅ |
| Total requests | — | **3498** | — |
| Setup burst | &gt;500 in window | 700 (606×200 + 94×429) | ✅ |

> **Note:** Mass 429 is **expected and correct** — it proves Kong’s global IP rate limiter is enforcing the 500 req/min safety net. Do not treat stress 429s as application errors.

Raw: `docs/qa/k6-stress-baseline.json`, stream: `docs/qa/k6-stress-metrics.ndjson`.

---

## Historical Note

Previous k6 runs (v9.1.0 / early v9.2.0-p1 style load) showed **P95 1,740ms** and **28.6% error rate**.

**Root cause:** a single k6 script generated ~6,000+ req/min against a **500 req/min** Kong rate limit. Most “errors” were rate-limit / overload effects, not true service latency.

**Fix:** split into two profiles — SLO measures latency under normal load; stress deliberately exceeds the limit to confirm 429 behavior.

| Era | Script | P95 | Error / 429 | Verdict |
|-----|--------|-----|-------------|---------|
| v9.1.0 (old single profile) | `k6-load-test.js` @ 100 VU | 1,740 ms | 28.6% errors | ❌ misleading FAIL |
| v9.2.0 (r1-slo subset) | `k6-load-test.js` `K6_PROFILE=r1-slo` | 231 ms | 0% | ✅ interim |
| **v9.3.0-p2 SLO** | `k6-slo.js` | **293 ms** | **0%** | ✅ **PASS** |
| **v9.3.0-p2 Stress** | `k6-stress.js` | n/a | **73.8% 429** | ✅ rate limiter OK |

---

## Archive: v9.1.0 single-profile run (superseded)

**Captured:** 2026-07-02 — `scripts/perf/k6-load-test.js` (do not use for SLO gate)

| Metric | Value |
|--------|-------|
| Total requests | 20,704 |
| P50 | 53.5 ms |
| P95 | **1,740 ms** |
| Error rate | **28.6%** |
| Peak VUs | 100 |
| RPS (avg) | 96.5 |

## Archive: v9.2.0 r1-slo interim

**Date:** 2026-07-03 — outcomes Kong route + health/auth-only mix

| Metric | Target | Actual | Pass |
|--------|--------|--------|------|
| Error rate | &lt; 5% | 0.00% | ✅ |
| P95 | &lt; 500 ms | 231 ms | ✅ |
| Requests | — | 4,826 | — |

Raw: `docs/qa/k6-baseline-v9.2.0.json`

---

## Infrastructure notes (unchanged)

### Database index verification

Migration **037** applied. Hot-table indexes:

```sql
-- ix_bom_tenant_product_active, ix_product_tenant_source_type,
-- ix_inventory_tenant_product, ix_mo_tenant_bom_status, ix_audit_tenant_timestamp
```

### Connection pooling

| Setting | Default | Env override |
|---------|---------|--------------|
| `pool_size` | 20 | `IPE_DB_POOL_SIZE` |
| `max_overflow` | 10 | `IPE_DB_MAX_OVERFLOW` |
| `statement_timeout` | 30s | `IPE_DB_STATEMENT_TIMEOUT_MS` |

### Backup verification

```bash
POSTGRES_CONTAINER=docker-db-1 BACKUP_DIR=./backups/postgres bash scripts/backup/pg-backup.sh
```
