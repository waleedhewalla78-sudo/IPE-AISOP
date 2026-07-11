# Analyze — Spec 021 Release Closure

**Date:** 2026-07-11  
**Scope:** Whole-project status across Specs 000–020 + cross-artifact consistency check

---

## Section 1 — Whole-Project Status (Specs 000–021)

### Spec Map

| Spec | Title | Status | Engineering | Human |
|------|-------|--------|-------------|-------|
| 000 | Foundation / DB scaffold | ARCHIVED | Done | — |
| 001 | RLS + tenant model | ARCHIVED | Done | — |
| 002 | Readiness stabilisation | ARCHIVED | Done | — |
| 003 | API/service stabilisation | ARCHIVED | Done | — |
| 004 | AI-first v6 (REL-DEMO) | SUPERSEDED by v9.x | Done | — |
| 005 | IPE program status rollup | REFERENCE | Updated per 019/020 | — |
| 006 | Hubs / multi-tenant | DELIVERED | Done | — |
| 007 | v8 enterprise upgrades | DELIVERED | Done | — |
| 008 | Keycloak SSO | DELIVERED | Healthy | — |
| 009 | StarTrans MENA config | DELIVERED | Done | — |
| 010 | Release 1 MENA | ENG DONE | Done | PH1-01/02 OPEN |
| 011 | Enterprise SSO/vault | DELIVERED | v9.4.0-p3 tag | — |
| 012 | StarTrans UAT | PARTIAL | ERP-mock done | Live Odoo = PH1-02 |
| 013 | Release 1 Odoo MENA | ENG DONE | All eng done | SOW/staging/Arabic |
| 014 | Release 2 growth | MERGED → 018 | Done | — |
| 015 | Enterprise production | EP3 TAG DONE | v9.4.0-p3 | — |
| 016 | Sprint 7 ecosystem | DONE | Emitters/mig 038 | — |
| 017 | First release plan | WAVE 1 DONE | W1-01–08 eng | C-08 push; PH1 |
| 018 | Phase 2 Release 2 | ENG DONE | G-R2-01/02/03/05 PASS | G-R2-04 OPEN |
| 019 | Program converge | DONE | Scenario promote, stock.quant | Issue triage done |
| 020 | Planning intelligence | **ENG COMPLETE** | 68 tests, mig 044–049, 8/10 UAT | UAT-10/11 code fix → 021 |
| 021 | Release closure | **ACTIVE** | UAT-10/11 fixed, tag readiness | G-R2-04, PH1-01/02 |

### Summary Statistics (as of 2026-07-11)

- **Specs completed (engineering):** 000–019, 020 (pending live test re-run)
- **Active spec:** 021-release-closure
- **Open human blockers:** PH1-01 (SOW), PH1-02 (Odoo staging), G-R2-04 (Arabic sign-off)
- **Tags applied:** `v9.4.0-p3` (Phase 3 gate), `v9.1.0-r2` (local only, not pushed)
- **Tags on HOLD:** `v9.1.1-r2` (G-R2-04), `v9.2.0-planning` (UAT-10/11 code fix pending live re-run)

---

## Section 2 — UAT-10/11 Root Cause Analysis

### UAT-10: Copilot Chat Timeout

**Root cause:** `COPILOT_TIMEOUT_SECONDS` was 300 s. The non-streaming `/chat` endpoint had no wall-clock guard. When the LLM provider (Anthropic/Ollama) was unreachable, `client.messages.create()` hung for 300 s before the httpx client-level timeout triggered.

**Fix applied:**
- `services/nlp-svc/app/config.py`: `COPILOT_TIMEOUT_SECONDS: int = 20`
- `services/nlp-svc/app/api/v1/copilot.py`: `_TIMEOUT_SECONDS = 20`; non-streaming `/chat` wrapped in `asyncio.timeout(20)`; on `TimeoutError`, calls `build_tool_fallback_response(tenant_id)` which invokes 3 planning tools (capacity alerts, S&OP cycle, MO status) and returns a structured snapshot within ≤5 s.
- `services/nlp-svc/app/core/copilot_agent.py`: Added `build_tool_fallback_response()` function; cleaned up imports.

**UAT-10 engineering pass condition:** `/copilot/chat` returns within ≤20 s with either (a) LLM-synthesised answer or (b) structured tool snapshot with `timeout: true` in response body.

### UAT-11: Best-Fit Cold Path

**Root cause:** `BestFitSelector._select_model()` iterated all candidate models (ARIMA 18 orders, SARIMA 18 orders) with no time budget. On cold/first call with a long history, statsmodels ARIMA/SARIMA fitting could exceed 45–180 s.

**Fix applied:**
- `services/demand-svc/app/core/forecasters/arima_forecaster.py`: Added `deadline: float | None` parameter to `predict()`, `_fit_best()`, and `_fit_best_sarimax()`. Inner grid loop checks `time.monotonic() >= deadline` and breaks early, returning best fit found so far. If no order converged, raises `ValueError` → caller falls back to SES.
- `services/demand-svc/app/core/forecasters/model_selector.py`: Added `time_budget_seconds: float = 8.0` parameter to `select_and_forecast()` and `_select_model()`. Computes `overall_deadline` and `per_model_budget`, passes `deadline` to each forecaster's `predict()`. `_SesForecaster.predict()` accepts `**_kwargs` to ignore unknown args. Budget exhaustion causes loop to break early with best model found.

**UAT-11 engineering pass condition:** `POST /api/v1/demand/forecast/best-fit` returns within ≤15 s for history length ≤100. With `time_budget_seconds=8`, ARIMA/SARIMA each get ~2.7 s; SES is always sub-second fallback.

---

## Section 3 — Cross-Artifact Consistency Check

| Artifact | Expected | Actual | Status |
|----------|----------|--------|--------|
| constitution.md version | 1.2.6 | 1.2.6 | ✓ |
| ipe/.specify/feature.json active | 021-release-closure | 021-release-closure | ✓ |
| E:\AISOP\.specify\feature.json active | ipe/specs/021-release-closure | ipe/specs/021-release-closure | ✓ |
| Migration head on compose DB | 049 | 049 (applied Spec 020) | ✓ |
| nlp-svc COPILOT_TIMEOUT_SECONDS | ≤20 | 20 | ✓ |
| demand-svc best-fit budget | ≤8 s default | 8.0 s | ✓ |
| OPEN-ITEMS-PROJECT.md Spec 020 | ENG DONE | To be updated → RC-07 | Pending |
| planning-uat.ps1 score | 10/10 | 8/10 (PARTIAL=2, pre-fix) | Pending re-run |
| release2-smoke.ps1 | 15/15 | 15/15 (last run 2026-07-10) | ✓ (needs re-verify) |
| GitHub issue #50 | OPEN human blockers | OPEN | ✓ |
| GitHub issue #51 | CLOSED defer tracker | CLOSED | ✓ |

---

## Section 4 — Migration Apply Path (OQ-13)

Migrations 044–049 were applied to the compose DB during Spec 020 UAT (2026-07-11) via:

```powershell
# From ipe/ with compose stack up
$env:IPE_DATABASE_URL_SYNC = "postgresql+psycopg2://ipe:ipe_dev_pass@localhost:5433/ipe_dev"
cd services/sop-svc  # or any service with alembic.ini pointing to root migrations/
python -m alembic -c alembic.ini upgrade head
```

The apply path is scripted in `scripts/apply-planning-migrations.ps1` (RC-03 deliverable).

Migration details:
| Migration | Table | Purpose |
|-----------|-------|---------|
| 044 | `product_segments` | ABC/XYZ product segmentation |
| 045 | `forecast_quality_metrics` | MAPE/bias tracking |
| 046 | `connector_lead_times` | Odoo lead-time + cost sync |
| 047 | `safety_stock_targets` | Safety stock calc results |
| 048 | `capacity_alerts` | Work center utilisation alerts |
| 049 | `sop_cycles`, `sop_versions`, `consensus_items` | S&OP engine |

All 14 new tables have RLS enabled (Principle I verified in UAT-2).

---

## Section 5 — Tag Decision

| Tag | Condition | Current State |
|-----|-----------|---------------|
| `v9.1.1-r2` | G-R2-04 Arabic native sign-off | **HOLD** — human blocker |
| `v9.2.0-planning` | UAT-10/11 PASS on live stack + 10/10 score | **HOLD** — code fix committed; pending live re-run |
| Do NOT push `v9.1.0-r2` | Already local-only; old tag | Leave untouched |

---

## Section 6 — Constitution Compliance (Spec 021)

| Principle | Check | Status |
|-----------|-------|--------|
| I. RLS | No new tables in 021 (fixes only) | ✓ |
| II. Auth | No endpoint auth changes | ✓ |
| III. Tests | Fixes covered by existing test suite + new timeout tests | ✓ (pending) |
| IV. Event bus | Kafka not touched | ✓ |
| V. API consistency | No new routes; fallback response uses existing APIResponse schema | ✓ |
| VI. Observability | `logger.warning` added for timeout path | ✓ |
| VII. Customer-first | UAT-10/11 fix directly enables planning demo | ✓ |
| VIII. Gate scripts | planning-uat.ps1 is the gate script; update report after re-run | Pending |
