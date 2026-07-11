# Tasks to Issues — Spec 021 Release Closure

**Date:** 2026-07-11  
**Tool:** `gh issue create`

---

## New Issues Created

| Task | Issue | Title |
|------|-------|-------|
| RC-01 | #52 | fix(nlp-svc): Copilot /chat 20s timeout + tool-backed fallback (UAT-10 Spec 021) |
| RC-02 | #53 | fix(demand-svc): best-fit 8s time budget + SES fallback (UAT-11 Spec 021) |
| RC-03 | #54 | chore(ops): apply-planning-migrations.ps1 script (OQ-13 Spec 021) |
| RC-04 | #55 | docs: tag readiness decision v9.1.1-r2 vs v9.2.0-planning (Spec 021) |
| RC-05 | comment on #50 | Spec 021 status update on commercial blockers issue |

## Issues NOT to Create (already tracked)

| Issue | Status | Note |
|-------|--------|------|
| #50 | OPEN | Commercial blockers — do not duplicate |
| #51 | CLOSED | Wave 2/3 defer tracker — closed 2026-07-10 |
| #27–#36 | CLOSED | Already closed in prior sessions |
| #39, #41 | CLOSED | Already closed |
| #47–#49 | CLOSED | Closed in Spec 019 |

## Comment to Add on #50

```
**Spec 021 Release Closure (2026-07-11) status update:**

Engineering gaps UAT-10 and UAT-11 from Spec 020 have been fixed:
- UAT-10 (Copilot chat timeout): non-streaming /chat now enforces 20s wall-clock budget; returns tool-backed structured snapshot when LLM unavailable. Fix in nlp-svc: copilot_agent.py + copilot.py.
- UAT-11 (best-fit cold path): BestFitSelector now has 8s time budget; ARIMA/SARIMA get per-model deadline and fall back to SES when budget exhausted. Fix in demand-svc: arima_forecaster.py + model_selector.py.

Remaining OPEN blockers (not faked, not closed by engineering):
- PH1-01: SOW commercial sign-off — **human/executive**
- PH1-02: Odoo staging environment — **ops**
- G-R2-04: Arabic native QA sign-off — **human reviewer**

Tags on HOLD: v9.1.1-r2 (G-R2-04), v9.2.0-planning (pending live 10/10 UAT re-run after stack up).
See specs/021-release-closure/ and docs/TAG-READINESS-021.md.
```
