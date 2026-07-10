# R2 Tag Decision — Option B

**Feature**: `018-phase2-release2`  
**Date**: 2026-07-10  
**Decision owner**: Engineering (this finalize) · Release manager (tag cut)

---

## Recommendation: **Option B — `v9.1.1-r2`**

| Option | Tag | When | Verdict |
|--------|-----|------|---------|
| A | Push existing local `v9.1.0-r2` | Now | **Reject** — points at older commit; does not include finalize delta |
| **B** | Cut **`v9.1.1-r2`** on HEAD after Arabic native sign-off | After G-R2-04 human | **Adopt** |
| C | Tag now without Arabic | Now | **Reject** — violates honest G-R2-04 policy |

---

## Gate readiness (engineering)

| Gate | Status |
|------|--------|
| G-R2-01 smoke 15/15 | PASS |
| G-R2-02 Copilot | PASS |
| G-R2-03 Wave 1 eng | PASS (live Odoo = PH1-02 human) |
| G-R2-04 Arabic | PASS eng · **native sign-off OPEN** |
| G-R2-05 demo 7/7 | PASS |
| Backend 860/860 · Vitest 41/41 | PASS |

## Human blockers (do not fake)

1. **G-R2-04** native Arabic reviewer sign-off — `docs/qa/arabic-qa-r2.md` Sign-off table  
2. **PH1-01** Phase 1 SOW / commercial  
3. **PH1-02** Odoo staging environment  
4. **OQ-9 §6.2** named stakeholder signatures — `docs/demo-data/gate11-oq9-waiver.md`

## ARB CUT / DEFER package (R2)

| Item | Decision | Issue |
|------|----------|-------|
| Tenant provision API | DEFER Phase 4 | #37 |
| Quotas metering E2E | DEFER Phase 4 | #38 |
| Predictive delay XGBoost+SHAP | DEFER Wave 2 stretch | #42 |
| NL schedule change | OUT OF SCOPE Wave 3 | #43–#44 |
| Supplier comms | OUT OF SCOPE Wave 3 | #45–#46 |
| Scenario promote | **SHIPPED** (Spec 019) | #40 closed |
| SAP B1 | **CUT** (S12) | — |
| Gate 11 kind 14/14 | **WON'T FIX** infra | #27 |

## Tag cut checklist (when Arabic lands)

```powershell
cd E:\AISOP\ipe
git status   # expect clean (no secrets)
.\scripts\release2-smoke.ps1   # expect 15/15
git tag -a v9.1.1-r2 -m "Phase 2 Release 2 finalize — G-R2-01..05; Arabic native signed"
git push origin master
git push origin v9.1.1-r2
```

**Do not** move or force-push `v9.1.0-r2`.

---

*Option B recorded 2026-07-10 as part of Master Cursor Prompt — Final R2 Closure.*
