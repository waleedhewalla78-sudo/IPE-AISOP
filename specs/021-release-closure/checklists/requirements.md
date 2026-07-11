# Requirements Checklist — Spec 021 Release Closure

**Date:** 2026-07-11

---

## Functional Requirements

| ID | Requirement | Test | Status |
|----|-------------|------|--------|
| FR-021-01 | `POST /copilot/chat` returns within ≤20 s when LLM unavailable | `test_copilot_chat_timeout_returns_fallback` | Pending |
| FR-021-02 | Fallback response body contains tool-backed planning data | Unit test mock | Pending |
| FR-021-03 | Fallback response has `timeout: true` in `data` | Unit test | Pending |
| FR-021-04 | SSE stream enforces 20 s timeout (unchanged from existing 30→20) | Existing SSE tests | ✓ (code updated) |
| FR-021-05 | `POST /demand/forecast/best-fit` returns within ≤15 s for history ≤100 | `test_best_fit_time_budget_falls_back_to_ses` | Pending |
| FR-021-06 | Best-fit returns `selected_model: "ses"` when budget exhausted | Unit test mock | Pending |
| FR-021-07 | Migration 049 is head after `alembic upgrade head` | `apply-planning-migrations.ps1` | ✓ (applied Spec 020) |
| FR-021-08 | All 14 planning tables have `rowsecurity=t` | UAT-2 | ✓ PASS |

## Non-Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| NFR-021-01 | No secrets committed | ✓ (`.kms_keys`, `.env` excluded) |
| NFR-021-02 | Ruff/mypy clean on touched files | Pending |
| NFR-021-03 | All existing tests still pass (no regression) | Pending re-run |
| NFR-021-04 | `release2-smoke.ps1` still 15/15 | Pending stack re-verify |

## Principle Compliance

| Principle | Requirement | Status |
|-----------|-------------|--------|
| I (RLS) | No new tables → no RLS check needed | ✓ |
| II (Auth) | No endpoint auth changes | ✓ |
| III (Tests) | New tests for timeout/budget paths | Pending |
| IV (Events) | Kafka not touched | ✓ |
| V (API) | Fallback uses existing `APIResponse` schema | ✓ |
| VI (Observability) | `logger.warning` on timeout | ✓ |
| VII (Customer-first) | Fixes enable planning demo UAT | ✓ |
| VIII (Gates) | planning-uat.ps1 re-run after fix | Pending |

## Open Items After 021

| ID | Item | Owner |
|----|------|-------|
| OI-021-01 | PH1-01 SOW commercial | Executive |
| OI-021-02 | PH1-02 Odoo staging | Ops |
| OI-021-03 | G-R2-04 Arabic native sign-off | QA |
| OI-021-04 | Tag v9.1.1-r2 cut | After G-R2-04 |
| OI-021-05 | Tag v9.2.0-planning cut | After UAT 10/10 live |
