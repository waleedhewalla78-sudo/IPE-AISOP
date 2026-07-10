# Converge: 019-program-converge

**Date**: 2026-07-10  
**Assessed against**: spec.md, plan.md, tasks.md, constitution v1.2.5  
**Code assessed**: release2 compose, scenario-svc promote, mock-odoo quants, ScenarioWorkbench UI

## Verdict

**Engineering intent for US1–US3 is satisfied.** Commercial/human blockers and deferred Wave 2/3 items remain open — appended below as Convergence tasks (not fake-completed).

| Intent | Gap type | Notes |
|--------|----------|-------|
| FR-019-01 mat-svc compose | none | Present in release2 compose |
| FR-019-02/03 promote | none | API+UI+tests |
| FR-019-04 stock.quant mock | none | Sample quants + tests |
| FR-019-05 blockers OPEN | none | #50 tracks honesty |
| FR-019-07 link open issues | none | Comments posted |
| SC-019-05 Speckit artifacts | none | Full tree under specs/019 |
| Live mat-svc container health | partial | File added; stack not rebuilt this pass (QA port safety) |
| #40 product close | partial | Eng done; issue still OPEN pending human verify |
| PH1-01/02 / Arabic sign-off | missing | External — Convergence tasks |
| #37/#38/#42–#46 | missing | Deferred — Convergence tasks |
| READINESS.md v8 banner stale | unrequested | Optional doc sync — Convergence task |

## Phase Convergence (appended tasks)

> Appended by `/speckit.converge` — do not renumber prior tasks.

### Phase 8: Convergence

- [ ] T060 [Conv] Rebuild/start mat-svc on R2 stack when QA window allows; confirm `:8002/api/v1/health` (no destructive down if other agent active)
- [ ] T061 [Conv] Product-verify scenario promote on live R2 UI; close GitHub #40 if accepted
- [ ] T062 [Conv] BLOCKED PH1-01 — Phase 1 SOW / commercial signature (human) — see #50
- [ ] T063 [Conv] BLOCKED PH1-02 — Provision Odoo staging + wire connector (ops) — see #50
- [ ] T064 [Conv] BLOCKED G-R2-04 — Native Arabic human sign-off (`docs/qa/arabic-qa-r2.md`) — see #50
- [ ] T065 [P] [Conv] Defer/implement #37 tenant provision API (ARB)
- [ ] T066 [P] [Conv] Defer/implement #38 quotas metering E2E (ARB)
- [ ] T067 [P] [Conv] Defer/verify or CUT #42 predictive delay XGBoost+SHAP
- [ ] T068 [P] [Conv] Schedule Wave 3 #43–#46 or ARB CUT from near-term roadmap
- [ ] T069 [P] [Conv] Optional: refresh `READINESS.md` version banner to v9.x / Spec 019 pointer
- [ ] T070 [Conv] After G-R2-04 policy: cut/push `v9.1.1-r2` (do not move old `v9.1.0-r2`)

**Clean for eng MVP of 019**: yes (US1–US3).  
**Clean for customer go-live**: **no**.
