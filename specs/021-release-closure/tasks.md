# Tasks — Spec 021 Release Closure

**Date:** 2026-07-11  
**Constitution:** v1.2.6

---

## RC-01: Copilot Chat Timeout Fix (UAT-10)

- [x] RC-01-a: Set `_TIMEOUT_SECONDS = 20` in `copilot.py` (was 30)
- [x] RC-01-b: Wrap non-streaming `run_agent_with_tools` loop in `asyncio.timeout(20)`
- [x] RC-01-c: Add `build_tool_fallback_response(tenant_id)` to `copilot_agent.py`
- [x] RC-01-d: On `TimeoutError`, call fallback and return with `timeout: true`
- [x] RC-01-e: Reduce `COPILOT_TIMEOUT_SECONDS` default to 20 in `config.py`
- [ ] RC-01-f: Add unit test `test_copilot_chat_timeout_returns_fallback` in `test_api_copilot.py`

## RC-02: Best-Fit Cold Path Fix (UAT-11)

- [x] RC-02-a: Add `deadline` param to `ARIMAForecaster.predict()` + `_fit_best()`
- [x] RC-02-b: Add `deadline` param to `SARIMAForecaster.predict()` + `_fit_best_sarimax()`
- [x] RC-02-c: Add time-budget logic to `BestFitSelector._select_model()`
- [x] RC-02-d: `_SesForecaster.predict()` accepts `**_kwargs` to ignore `deadline`
- [ ] RC-02-e: Add unit test `test_best_fit_time_budget_falls_back_to_ses`

## RC-03: OQ-13 Migration Apply Script

- [x] RC-03-a: Write `scripts/apply-planning-migrations.ps1`
- [ ] RC-03-b: Test script on compose DB (`IPE_DATABASE_URL_SYNC`)

## RC-04: Tag Readiness Documentation

- [x] RC-04-a: Write `docs/TAG-READINESS-021.md`

## RC-05: GitHub Issue Triage

- [ ] RC-05-a: Create GitHub issues for RC-01–RC-08 via `gh issue create`
- [ ] RC-05-b: Comment on #50 (commercial blockers) with Spec 021 status update

## RC-06: Re-run Planning UAT

- [ ] RC-06-a: Run `scripts/planning-uat.ps1` after code fixes
- [ ] RC-06-b: Record score in `docs/qa/PLANNING-MASTER-BUILD-UAT-REPORT.md`

## RC-07: Update OPEN-ITEMS-PROJECT.md

- [x] RC-07-a: Update Spec 020 row to ENG DONE / 021 ACTIVE in `OPEN-ITEMS-PROJECT.md`

## RC-08: Release2 Smoke Re-verification

- [ ] RC-08-a: Run `scripts/release2-smoke.ps1` if stack is up

## RC-09: Constitution + Feature Pointers

- [x] RC-09-a: Update `ipe/.specify/memory/constitution.md` to v1.2.6
- [x] RC-09-b: Update `ipe/.specify/feature.json` → 021-release-closure
- [x] RC-09-c: Update `E:\AISOP\.specify\feature.json` → 021-release-closure

## RC-10: Commit + Push

- [ ] RC-10-a: Commit all changes with env author `IPE Agent <ipe-agent@local>`
- [ ] RC-10-b: Push to `origin/master` (no force push)
