# Spec 018 — Phase 2 Release 2

**Feature**: `018-phase2-release2`  
**Target tag**: `v9.1.0-r2`  
**Date**: 2026-07-10  
**Status**: **~82% engineering** · gates + Arabic QA pending

---

## Artifacts

| Document | Purpose |
|----------|---------|
| [spec.md](./spec.md) | Vision, scope, sprint summary |
| [tasks.md](./tasks.md) | Sprint backlog (synced to repo) |
| [converge.md](./converge.md) | Plan vs actual, gates, remaining tasks |
| [implement.md](./implement.md) | Executed vs pending per sprint |
| [../docs/PHASE2-SPRINT-PLAN.md](../docs/PHASE2-SPRINT-PLAN.md) | Master sprint calendar |
| [../docs/PHASE2-IMPLEMENTATION-GUIDE.md](../docs/PHASE2-IMPLEMENTATION-GUIDE.md) | Original guide (reconciled) |

**Depends on**: Spec 017 (`017-first-release-plan`) · migration head **038** + R2 migrations **040–043**

---

## Sprint reports

| Sprint | Report | Status | Gate |
|--------|--------|--------|------|
| W1 | — *(see [implement.md](./implement.md))* | ✅ ~90% | Odoo + OTD RLS tests |
| S1 | [sprints/S1-report.md](./sprints/S1-report.md) | ✅ Complete | G-R2-01 smoke TBD |
| S2 | — *(see [implement.md](./implement.md))* | ✅ Complete | G-R2-02 |
| S3 | [sprints/S3-report.md](./sprints/S3-report.md) | ✅ Complete | MAPE + forecast API |
| S4 | [sprints/S4-report.md](./sprints/S4-report.md) | ✅ Complete | simulate + compare UI |
| S5 | — | ⬜ Not started | G-R2-04 Arabic QA |
| S6 | — *(see [implement.md](./implement.md))* | 🟡 ~85% | migration 039 pending |
| S7 | — *(see [implement.md](./implement.md))* | 🟡 ~75% | Odoo polish |
| S8 | — *(see [implement.md](./implement.md))* | ✅ Complete | ops API + dashboard |
| S9 | — *(see [implement.md](./implement.md))* | ✅ Complete | cap analytics |
| S10 | — *(see [implement.md](./implement.md))* | ✅ Complete | supplier risk |
| S11 | — *(see [implement.md](./implement.md))* | ✅ Complete | S&OP report |
| S12 | — | **CUT** | Spec 017 |

> Missing sprint reports (W1, S2, S5–S11) tracked as **C-025** in [converge.md](./converge.md).

---

## Program gates

| Gate | Criteria | Status | Evidence |
|------|----------|--------|----------|
| **G-R2-01** | `release2-smoke.ps1` PASS | 🟡 | `scripts/release2-smoke.ps1` |
| **G-R2-02** | Copilot live data tools | ✅ | `test_copilot_tools_r2.py` |
| **G-R2-03** | Wave 1 W1-03–08 | ✅ ~90% | Odoo v2 + OTD dashboard |
| **G-R2-04** | Arabic 8+ native QA | ⬜ | `docs/qa/arabic-qa-r2.md` missing |
| **G-R2-05** | `run-release2-demo.ps1` PASS | 🟡 | `scripts/run-release2-demo.ps1` |
| **G-R2-TAG** | Tag `v9.1.0-r2` | ⬜ | After gates + S5 |

---

## Master status (quick reference)

| Sprint | Status | Gate | Evidence |
|--------|--------|------|----------|
| W1 | ✅ ~90% | Odoo + OTD RLS | `implement.md` · `test_odoo_config_v2.py` · `OTDDashboardPage.tsx` |
| S1 | ✅ Complete | G-R2-01 | [sprints/S1-report.md](./sprints/S1-report.md) |
| S2 | ✅ Complete | G-R2-02 | `implement.md` · `test_copilot_tools_r2.py` |
| S3 | ✅ Complete | Forecast API | [sprints/S3-report.md](./sprints/S3-report.md) |
| S4 | ✅ Complete | Scenario compare | [sprints/S4-report.md](./sprints/S4-report.md) |
| S5 | ⬜ Open | G-R2-04 | — |
| S6 | 🟡 ~85% | OTD extended | `implement.md` · `otd_analytics.py` |
| S7 | 🟡 ~75% | Odoo polish | `implement.md` · `OdooConfigPanel.tsx` |
| S8 | ✅ Complete | Ops dashboard | `implement.md` · `test_ops_dashboard.py` |
| S9 | ✅ Complete | cap analytics | `implement.md` · `test_analytics_production.py` |
| S10 | ✅ Complete | supplier risk | `implement.md` · `test_supply_chain_intel.py` |
| S11 | ✅ Complete | S&OP report | `implement.md` · `test_sop_reports.py` |
| S12 | **CUT** | — | Spec 017 |

---

## Key scripts

```powershell
cd E:\AISOP\ipe
.\scripts\deploy-release2.ps1      # S1 deploy
.\scripts\release2-smoke.ps1       # G-R2-01
.\scripts\run-release2-demo.ps1    # G-R2-05 (014 + R2)
.\scripts\verify-copilot-r1-smoke.ps1  # W1-02 regression
```

---

*README v1.0 — Phase 2 Release 2 index*
