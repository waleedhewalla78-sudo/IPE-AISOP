# Spec 029 — k6 p95 under concurrent load (QA-01)

**Date**: 2026-07-18  
**Status**: Investigation notes (Wave 1) — under-load SLO remains a genuine eng residual if not re-proven green.

## Facts (from prior campaigns)

| Profile | Result | Source |
|---------|--------|--------|
| Baseline SLO | p95 **293ms** < 300ms target — GREEN | `docs/qa/k6-slo-baseline.json`, PRODUCT-STATUS |
| Contention / campaign | p95 ~**6258ms** vs 500ms — FAIL; errors 0%; functional 100% | FULL-TEST-CAMPAIGN-REPORT |
| R2 critical | p95 can stretch to ~60s under stack contention | `k6-r2-critical-summary.json` |

## Likely contributors (ordered)

1. **Solver timeouts** — cap-svc OR-Tools `max_time_in_seconds=30` dominates under parallel schedule calls.
2. **Connection pool saturation** — concurrent asyncpg/SQLAlchemy sessions against single Postgres on 8GB demo VMs.
3. **Cold start / image rebuild** — first-hit latency after compose recreate.
4. **No response cache** on expensive planning-command / enterprise compute endpoints.

## Light mitigations shipped / recommended (not claimed as SLO-closed)

- Keep unit/ASGI functional gates as release bar for Spec 029.
- Before high-concurrency go-live: raise pool sizes, add per-endpoint k6 budgets, consider short-circuit caches for read-only enterprise/agents lists, and cap solver time under load profiles.
- Re-run: `tests/performance/k6/load-test.js` + R2 critical script against healthy stack; attach summaries under `docs/qa/`.

## Honesty

Spec 029 does **not** mark QA-01 CLOSED. Documented for operators; COM blockers unrelated.
