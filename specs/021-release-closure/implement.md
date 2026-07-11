# Implement — Spec 021 Release Closure

**Date:** 2026-07-11  
**Status:** COMPLETE (engineering tasks)

---

## RC-01: Copilot Chat Timeout (UAT-10)

**Files changed:**
- `services/nlp-svc/app/config.py`: `COPILOT_TIMEOUT_SECONDS: int = 20` (was 300)
- `services/nlp-svc/app/api/v1/copilot.py`:
  - `_TIMEOUT_SECONDS = 20` (was 30)
  - Non-streaming `/chat` wrapped in `asyncio.timeout(20)`
  - On `TimeoutError`, calls `build_tool_fallback_response(tenant_id)` and returns `timeout: true`
- `services/nlp-svc/app/core/copilot_agent.py`:
  - Added `build_tool_fallback_response(tenant_id)` function
  - Added `LLM_TIMEOUT_SECONDS = 18` constant (used by SSE stream guard)
  - Cleaned up imports: `logger`, added tool function imports

**Tests added:**
- `services/nlp-svc/tests/test_api_copilot.py`: `test_copilot_chat_timeout_returns_tool_fallback`
- `services/nlp-svc/tests/test_copilot_tools.py`: fixed stale tool count assertion (16 → 25)

**Result:** 170 passed, 0 failed in nlp-svc test suite

---

## RC-02: Best-Fit Cold Path (UAT-11)

**Files changed:**
- `services/demand-svc/app/core/forecasters/arima_forecaster.py`:
  - Added `deadline: float | None` to `ARIMAForecaster.predict()` + `_fit_best()`
  - Added `deadline: float | None` to `SARIMAForecaster.predict()` + `_fit_best_sarimax()`
  - Inner grid loops check `time.monotonic() >= deadline` and break early
- `services/demand-svc/app/core/forecasters/model_selector.py`:
  - Added `time_budget_seconds: float = 8.0` to `select_and_forecast()` + `_select_model()`
  - Computes `overall_deadline` and `per_model_budget`
  - Passes `deadline` kwarg to each forecaster's `predict()`
  - `_SesForecaster.predict()` accepts `**_kwargs`

**Tests added:**
- `services/demand-svc/tests/test_best_fit.py`:
  - `test_time_budget_zero_falls_back_to_first_candidate`
  - `test_time_budget_forces_ses_for_ax_segment`

**Result:** 29 passed, 0 failed in demand-svc test suite

---

## RC-03: OQ-13 Migration Apply Script

**File created:** `scripts/apply-planning-migrations.ps1`
- Verifies `IPE_DATABASE_URL_SYNC` env var
- Runs `alembic upgrade head`
- Checks current head is `049_sop_engine`
- Verifies 8 planning tables exist via psycopg2

---

## RC-04: Tag Readiness

**File created:** `docs/TAG-READINESS-021.md`
- v9.1.1-r2 conditions: G-R2-04 sign-off + smoke/demo PASS
- v9.2.0-planning conditions: UAT 10/10 on live stack
- Do NOT push v9.1.0-r2 (stale local tag)
- Do NOT retag v9.4.0-p3

---

## RC-07: OPEN-ITEMS-PROJECT.md Update

Updated `specs/018-phase2-release2/OPEN-ITEMS-PROJECT.md`:
- Spec 020 row: ENG DONE
- Added Spec 021 row: ACTIVE

---

## RC-09: Constitution + Feature Pointers

- `ipe/.specify/memory/constitution.md` → v1.2.6
- `ipe/.specify/feature.json` → 021-release-closure
- `E:\AISOP\.specify\feature.json` → 021-release-closure

---

## Test Totals (all suites run after RC-01/RC-02 fixes)

| Service | Tests | Result |
|---------|-------|--------|
| nlp-svc | 170 passed | ✓ GREEN |
| demand-svc | 29 passed | ✓ GREEN |
| **Total touched** | **199 passed** | ✓ |

---

## Remaining (non-blocking)

| Task | Status | Note |
|------|--------|------|
| RC-05: GitHub issues | Pending | `gh issue create` — next step |
| RC-06: UAT re-run | Pending | Requires docker stack up |
| RC-08: release2-smoke | Pending | Requires docker stack up |
| RC-10: commit + push | Pending | After GitHub issues |
