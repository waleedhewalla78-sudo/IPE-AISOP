# Plan — Spec 021 Release Closure

**Date:** 2026-07-11  
**Constitution:** v1.2.6

---

## Technical Approach

### RC-01: Copilot Chat Timeout (UAT-10)

**Problem:** Non-streaming `/chat` has no timeout; LLM hang blocks request indefinitely.

**Solution:**
1. Set `_TIMEOUT_SECONDS = 20` in `copilot.py` (shared by SSE and non-streaming).
2. Wrap non-streaming `run_agent_with_tools` loop in `asyncio.timeout(20)`.
3. On `TimeoutError`, call `build_tool_fallback_response(tenant_id)` — invokes 3 tools (capacity alerts, S&OP cycle, MO status) in parallel-ish sequence; each has its own httpx 10 s timeout.
4. Return `APIResponse` with `timeout: true` flag in data.
5. Add `build_tool_fallback_response` to `copilot_agent.py`.

**Files changed:**
- `services/nlp-svc/app/api/v1/copilot.py`
- `services/nlp-svc/app/core/copilot_agent.py`
- `services/nlp-svc/app/config.py`

### RC-02: Best-Fit Cold Path (UAT-11)

**Problem:** ARIMA/SARIMA grid search (up to 36 fitter calls combined) can take 45–180 s on cold path.

**Solution:**
1. Add `deadline: float | None` to `ARIMAForecaster.predict()` and `SARIMAForecaster.predict()`, propagated into `_fit_best()` / `_fit_best_sarimax()` inner loops.
2. Each inner iteration checks `time.monotonic() >= deadline` and breaks early, returning best fit found or raising `ValueError` (→ SES fallback).
3. `BestFitSelector._select_model()` gets `time_budget_seconds=8.0` default; computes per-model deadline and passes to forecaster.
4. `_SesForecaster.predict()` accepts `**_kwargs` to ignore `deadline`.

**Files changed:**
- `services/demand-svc/app/core/forecasters/arima_forecaster.py`
- `services/demand-svc/app/core/forecasters/model_selector.py`

### RC-03: OQ-13 Migration Apply Script

**Solution:** Write `scripts/apply-planning-migrations.ps1` that:
1. Checks compose DB reachability via `pg_isready` or psycopg2 ping
2. Runs `alembic upgrade head` via the shared `IPE_DATABASE_URL_SYNC` env var
3. Queries `alembic_version` table and asserts head is `049_sop_engine`
4. Exits 0 on success, 1 on failure with clear error message

### RC-04: Tag Readiness Document

**Solution:** Write `docs/TAG-READINESS-021.md` documenting conditions for v9.1.1-r2 and v9.2.0-planning. Reference `TAG-DECISION.md` for existing policy.

### RC-05: GitHub Issue Triage

**Solution:** Use `gh issue comment` and `gh issue create` to:
- Create new issues for RC-01–RC-08
- Comment on #50 (commercial blockers) with 021 status
- Do not reopen closed issues

### RC-06: Re-run Planning UAT

**Solution:** Run `scripts/planning-uat.ps1` after code fixes are applied. Update `docs/qa/PLANNING-MASTER-BUILD-UAT-REPORT.md`.

### RC-07: Update OPEN-ITEMS-PROJECT.md

**Solution:** Update Spec 020 row to "ENG DONE"; add Spec 021 row as "ACTIVE".

### RC-08: sop-svc Release2-Smoke Verification

**Solution:** Run `scripts/release2-smoke.ps1`. If compose stack down, note as "stack not running — re-run after docker compose up."

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| LLM keys absent — UAT-10 fallback untested end-to-end | Engineering PASS defined as "returns within 20 s"; tool fallback satisfies this |
| ARIMA deadline breaks loop — `ValueError` path not tested | Existing `test_best_fit.py` mocks statsmodels; add timeout test with `time_budget_seconds=0.001` |
| Docker stack down during UAT re-run | Document "stack not running" as blocker; do not fake scores |
| `asyncio.timeout` not available | Python 3.14 confirmed from .pyc artifacts — available since 3.11 |

---

## Sequencing

```
RC-01 (code) ──┐
RC-02 (code) ──┼── RC-06 (UAT re-run) ── RC-07 (report update) ── RC-08 (smoke check)
                │
RC-03 (script)─┘
RC-04 (docs) ─────── RC-05 (GitHub) ──── commit + push
```
