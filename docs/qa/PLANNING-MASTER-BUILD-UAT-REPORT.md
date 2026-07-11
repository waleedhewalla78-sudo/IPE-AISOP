# Planning Intelligence — Master Build & UAT Report

**Date:** 2026-07-11  
**Prompt:** `IPE-MASTER-BUILD-UAT-PROMPT.md`  
**Workspace:** `E:\AISOP\ipe`  
**HEAD (pre-UAT commit):** `32a7b5b` (+ local UAT fixes)

## Build status (Modules 1–9)

Already implemented under Spec 020 (migrations **044–049**, not prompt’s 043–048 numbering — `043` was reserved for Odoo config versioning).

| Module | Status | Evidence |
|--------|--------|----------|
| 1 ABC/XYZ | **BUILT** | mat-svc + mig 044 |
| 2 Forecast quality | **BUILT** | demand-svc + mig 045 |
| 3 ARIMA/best-fit | **BUILT** | demand-svc forecasters |
| 4 Odoo lead-time/cost | **BUILT** | connector + mig 046 |
| 5 Safety stock | **BUILT** | mat-svc + mig 047 |
| 6 Capacity utilisation | **BUILT** | cap-svc + mig 048 |
| 7 S&OP engine | **BUILT** | sop-svc :8110 + mig 049 |
| 8 Copilot tools | **BUILT** | nlp-svc (≥9 tools) |
| 9 Infra Kong/compose | **BUILT** | release2 compose + kong |

## UAT results

| Step | Status | Detail |
|------|--------|--------|
| UAT-1 Migration integrity | **PASS** | `alembic upgrade head` → **049**; 14 planning tables created |
| UAT-2 RLS | **PASS** | All 14 new tables `rowsecurity=t` |
| UAT-3 Unit tests | **PASS** | mat 24 + demand 9 + cap 4 + connector 3 + sop 6 + nlp 22 = **68 passed** |
| UAT-4 Service health | **PASS** | mat/demand/cap/connector/sop/nlp/dpe/kong 200 |
| UAT-5 API contracts | **PASS** | Kong login + segmentation/mape/ss/cap/sop + create cycle |
| UAT-6 Segmentation E2E | **PASS** | `products_classified=7` after demand seed (89 lines) |
| UAT-7 Safety stock E2E | **PASS** | calculate accepted |
| UAT-8 S&OP FSM | **PASS** | advance + approve + invalid future stage rejected (HTTP 400) |
| UAT-9 Consensus | **PASS** | baseline version auto-created; calculate OK |
| UAT-10 Copilot chat | **PARTIAL → ENG FIXED** | Live `/copilot/chat` now enforces 20s timeout + tool fallback (Spec 021 RC-01); unit tests **22/22**; re-run on live stack pending |
| UAT-11 Best-fit | **PARTIAL → ENG FIXED** | best-fit now has 8s time budget + SES fallback (Spec 021 RC-02); unit tests **29/29**; re-run on live stack pending |
| UAT-12 Cross-module | **PASS** | A-class product SL=97 linked to safety-stock results |

**Pre-fix script score:** PASS=8 PARTIAL=2 FAIL=0 (`scripts/planning-uat.ps1` 2026-07-11)  
**Post-fix score (live re-run pending):** Expected PASS=10 PARTIAL=0 after Spec 021 RC-01/RC-02 code fixes  
**Evidence:** `docs/qa/PLANNING-UAT-RESULTS-2026-07-11.md`

## Fixes applied during UAT

1. Applied migrations 044→049 on compose DB (`IPE_DATABASE_URL_SYNC` @ `:5433`)
2. Seeded 84 demand lines for ABC/XYZ
3. sop-svc: auto-create baseline `SopVersion` on cycle create; reject non-current stage approve with HTTP 400; include `versions` on get cycle
4. Added `scripts/planning-uat.ps1` for repeatable UAT-4..12

## Tag decision

Prompt: tag `v9.2.0-planning` **only if all UAT steps PASS**.

**Not tagged yet** — UAT-10 and UAT-11 code fixes committed (Spec 021 2026-07-11); live re-run on stack pending before tag.  
After live re-run confirms 10/10 PASS:

Recommended after LLM keys + warm best_fit path:
```powershell
git tag -a v9.2.0-planning -m "Planning intelligence UAT green"
git push origin v9.2.0-planning
```

## Fixes applied in Spec 021 (2026-07-11)

5. UAT-10 fix: `asyncio.timeout(20)` in non-streaming /chat + `build_tool_fallback_response()` in nlp-svc (PR: issue #52)
6. UAT-11 fix: `time_budget_seconds=8.0` in BestFitSelector + `deadline` param in ARIMA/SARIMA fitters (PR: issue #53)
7. Stale test count fixed: `TOOL_DEFINITIONS` count assertion updated from 16 → 25

## Honest blockers (remaining after Spec 021)

- Live Copilot chat LLM synthesis needs working LLM provider (tool fallback satisfies engineering gate)
- Live customer Odoo still PH1-02 (mapper unit-tested)
- Arabic native sign-off (G-R2-04) blocks v9.1.1-r2 tag
