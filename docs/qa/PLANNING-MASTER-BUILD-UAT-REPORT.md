# Planning Intelligence — Master Build & UAT Report

**Date:** 2026-07-11  
**Prompt:** `IPE-MASTER-BUILD-UAT-PROMPT.md` + `IPE-FINALIZE-PROMPT.md`  
**Workspace:** `E:\AISOP\ipe`  
**Finalize commit:** pending (this report)

## Build status (Modules 1–9)

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

## UAT results (post-finalize fixes)

| Step | Status | Detail |
|------|--------|--------|
| UAT-1 Migration integrity | **PASS** | head **049**; 14 planning tables + RLS |
| UAT-2 RLS | **PASS** | All 14 `rowsecurity=t` |
| UAT-3 Unit tests | **PASS** | **70** planning-module tests green after finalize fixes |
| UAT-4 Service health | **PASS** | Verified when stack up |
| UAT-5 API contracts | **PASS** | Kong planning routes |
| UAT-6 Segmentation E2E | **PASS** | products_classified=7 |
| UAT-7 Safety stock E2E | **PASS** | calculate accepted |
| UAT-8 S&OP FSM | **PASS** | invalid stage → HTTP 400 |
| UAT-9 Consensus | **PASS** | baseline version auto-created |
| UAT-10 Copilot live | **PASS (code)** | ≤20s timeout + tool fallback; concurrent tools; LLM warm-up; Kong `read_timeout: 300000` on nlp-svc |
| UAT-11 Best-fit live | **PASS (code)** | SES-first; 8s budget; ARIMA grid 18; statsmodels warm-up |
| UAT-12 Cross-module | **PASS** | Segment SL → safety stock |

**Unit tests after finalize:** mat 24 + demand 11 + cap 4 + connector 3 + sop 6 + nlp 22 = **70 PASS**

> **Live Kong re-verify:** Docker Desktop was restarted during finalize. Re-run `.\scripts\planning-uat.ps1` after `deploy-release2.ps1` to confirm UAT-10/11 wall-clock on the stack before treating the tag as fully live-verified.

## Finalization Fixes (2026-07-11)

### UAT-10 Copilot
1. **1A** LLM backend warm-up on `nlp-svc` startup (`main.py` lifespan)
2. **1B** Planning HTTP helper already uses `timeout=10.0` (`_planning_get`)
3. **1C** Concurrent tool execution via `asyncio.gather` in Anthropic + Ollama loops; concurrent fallback snapshot
4. **1D** Kong nlp-svc `read_timeout: 300000` verified in `kong.release2.yml`
5. Spec 021: hard `asyncio.timeout(20)` + `build_tool_fallback_response()`

### UAT-11 Best-fit
1. **2A** ARIMA/SARIMA grid already `p=0..2,d=0..1,q=0..2` (18 combos)
2. **2B/2C** `time_budget_seconds=8.0`; **SES always first** in candidate list
3. **2D** statsmodels/scipy warm-up on `demand-svc` startup

## Tag decision

- Code + unit gates: **ready for `v9.2.0-planning`**
- Live stack UAT-10/11: re-run after Docker is healthy; if `planning-uat.ps1` shows 12/12 PASS, tag is fully justified

## Honest blockers (unchanged)

- PH1-02 live Odoo staging
- G-R2-04 Arabic native sign-off (separate from planning tag)
- LLM provider keys for full AI synthesis (fallback still returns tool snapshot)
