# Gate 2 Evidence

**Date**: 2026-06-22 (baseline) · **Updated**: 2026-06-26 (REL-PROD Wave 2–3)  
**Result**: PASSED

## Original Gate 2 (June 22)

| Artifact | Description |
|----------|-------------|
| `sprint2-e2e.log` | 25 passed, 1 skipped |
| `phase56-e2e.log` | 16 passed |
| `critical-path.log` | 5/5 steps OK |
| `k6-phase56.txt` | 0% http_req_failed, p95 ~1.63s |

**Key fix**: `infrastructure/docker/ipe-common.env` — `IPE_DATABASE_URL`, `IPE_KAFKA_BOOTSTRAP_SERVERS`, `IPE_REDIS_URL`.

## REL-PROD Wave 2–3 Evidence (repo root `docs/`)

| Artifact | Description |
|----------|-------------|
| `docs/k6-summary.md` | k6 smoke / 10 VU / 200 VU load tests (Wave 2A) |
| `docs/k6-smoke-console.txt` | Smoke run console |
| `docs/k6-10vu-console.txt` | 10 VU sustained load |
| `docs/k6-200vu-console.txt` | 200 VU peak load |
| `docs/chaos/chaos-summary.md` | Chaos C1–C6 scenarios (Wave 2B) |
| `docs/demo-run-report-wave3-live.txt` | Live demo 20/20 (Wave 3 W3-04) |
| `docs/wave3-regression.md` | Wave 3 regression checklist |
| `docs/coverage-summary.md` | Coverage 60%+ gate (Wave 2C) |
| `docs/ops-monitoring.md` | Loki + Prometheus + Grafana (Wave 2D) |

See also `contracts/gate-2-operations.md` for acceptance criteria.
