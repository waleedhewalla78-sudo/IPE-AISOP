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
| UAT-10 Copilot chat | **PARTIAL** | Live `/copilot/chat` times out (LLM); tools unit tests **22/22** |
| UAT-11 Best-fit | **PARTIAL** | Endpoint wired; live best_fit can exceed 45–180s on cold path |
| UAT-12 Cross-module | **PASS** | A-class product SL=97 linked to safety-stock results |

**Live script score (latest):** PASS=8 PARTIAL=2 FAIL=0 (`scripts/planning-uat.ps1`)  
**Evidence:** `docs/qa/PLANNING-UAT-RESULTS-2026-07-11.md`

## Fixes applied during UAT

1. Applied migrations 044→049 on compose DB (`IPE_DATABASE_URL_SYNC` @ `:5433`)
2. Seeded 84 demand lines for ABC/XYZ
3. sop-svc: auto-create baseline `SopVersion` on cycle create; reject non-current stage approve with HTTP 400; include `versions` on get cycle
4. Added `scripts/planning-uat.ps1` for repeatable UAT-4..12

## Tag decision

Prompt: tag `v9.2.0-planning` **only if all UAT steps PASS**.

**Not tagged** — UAT-10 (LLM chat latency) and UAT-11 (best_fit runtime) remain PARTIAL.

Recommended after LLM keys + warm best_fit path:
```powershell
git tag -a v9.2.0-planning -m "Planning intelligence UAT green"
git push origin v9.2.0-planning
```

## Honest blockers

- Live Copilot chat needs working LLM provider (timeouts without/slow model)
- best_fit ARIMA/SARIMA search is CPU-heavy on first call
- Live customer Odoo still PH1-02 (mapper unit-tested)
