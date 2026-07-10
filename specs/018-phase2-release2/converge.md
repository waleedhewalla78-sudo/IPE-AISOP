# Speckit Converge — Spec 018 Phase 2 Release 2

**Date**: 2026-07-10  
**Constitution**: v1.2.4  
**Authority**: `docs/PHASE2-SPRINT-PLAN.md` · Spec 017 · codebase audit  
**Target tag**: `v9.1.0-r2` · interim platform tag `v9.4.0-p3`

---

## 1. Verdict

| Stream | Plan | Code | Tests | Sprint report |
|--------|------|------|-------|---------------|
| W1 bridge (Odoo + OTD) | ✅ | ✅ ~90% | connector + OTD unit | — |
| S1 R2 infrastructure | ✅ | ✅ | vitest + e2e | `sprints/S1-report.md` |
| S2 Copilot live data | ✅ | ✅ | `test_copilot_tools_r2.py` | — |
| S3 Demand (SES) | ✅ | ✅ | `test_forecaster_r2.py` | `sprints/S3-report.md` |
| S4 Scenarios | ✅ | ✅ | `test_simulator_r2.py` | `sprints/S4-report.md` |
| S5 Arabic 8+ | ✅ | ⬜ | — | — |
| S6 OTD extended | ✅ | ✅ ~85% | analytics + OTD page | — |
| S7 Odoo polish | ✅ | ✅ ~75% | admin panel | — |
| S8 Multi-tenant ops | ✅ | ✅ | `test_ops_dashboard.py` | — |
| S9 Production intel | ✅ | ✅ | `test_analytics_production.py` | — |
| S10 Supply chain intel | ✅ | ✅ | `test_supply_chain_intel.py` | — |
| S11 S&OP synthesis | ✅ | ✅ | `test_sop_reports.py` | — |
| S12 SAP B1 | **CUT** | — | — | — |

**Sprint completion**: 10/12 executable sprints substantially done · **S5 Arabic QA open** · **S12 CUT**  
**Program completion**: **~82%** (engineering) · **~65%** (gates + QA sign-off)  
**Program verdict**: **PROCEED to gate validation** — close S5 Arabic QA, reconcile migrations, run R2 smoke/demo gates

---

## 2. Plan vs actual (reconciliation)

| Dimension | Sprint plan assumption | Actual (2026-07-10) | Delta |
|-----------|------------------------|---------------------|-------|
| Alembic head | Start R2 at 039 | **038** + parallel branches **040–042** + **043** | **039 missing**; **043/040 branch conflict** |
| Copilot R1 nav | Hidden in R1 | Visible (W1-01 done) | S2 focuses on live tools ✅ |
| R2 compose | Not present | **`docker-compose.release2.yml`** | S1 ✅ |
| Odoo Config v2 | Sprint 7 / W1 bridge | **W1-03–06 shipped** | Pulled forward ✅ |
| OTD dashboard | W1-08 / S6 | **`OTDDashboardPage.tsx`** + `/analytics/otd/*` | W1-08 + S6 APIs ✅ |
| Demand ML | Prophet/LSTM | **SES-first** in demand-svc | S3 ✅ per Spec 017 |
| Copilot tools | 7 new R2 tools | **All 7 + S9/S10 tools** in `copilot_tools.py` | S2 ✅ |
| Shadow mode | S2-02 | **`DEFAULT_SHADOW_MODE = True`** in `copilot_agent.py` | S2 ✅ |
| Spec 014 overlap | Separate track | planner-assist, outcomes, OTD baseline **already done** | Dedupe W1/S6 baseline UI |
| SAP B1 | Sprint 12 | **CUT** per Spec 017 | Correct ✅ |

---

## 3. Constitution checklist

| Principle | Status | Evidence |
|-----------|--------|----------|
| I RLS | 🟡 | 040–043 add RLS; **039 pending**; migration branch needs merge |
| II Auth | ✅ | Admin/ops routes use `require_roles` |
| III Tests | ✅ | R2 test files per sprint (S2–S4, S8–S11) |
| IV Events | ✅ | demand/scenario Kafka optional in R2 compose |
| V API | ✅ | Kong R2 routes in `kong.release2.yml` |
| VI Observability | 🟡 | Smoke script exists; **docker gate run TBD** |
| VII Customer-first | 🟡 | **S5 Arabic native QA pending** |
| VIII Gates | 🟡 | G-R2-01/05 not yet executed on live stack |

---

## 4. Sprint gate summary

| Gate | Criteria | Status |
|------|----------|--------|
| G-R2-01 | `release2-smoke.ps1` PASS | 🟡 Script ready; docker run TBD |
| G-R2-02 | Copilot live data tools (S2) | ✅ 7 tools + shadow mode + unit tests |
| G-R2-03 | Wave 1 complete (W1-03–08) | ✅ ~90% — Odoo v2 + OTD API/UI |
| G-R2-04 | Arabic 8+ native QA (S5) | 🔄 eng ✅ · native sign-off ⬜ (`docs/qa/arabic-qa-r2.md`) |
| G-R2-05 | `run-release2-demo.ps1` extended PASS | 🟡 Script exists (014); full R2 extension TBD |
| G-R2-TAG | Tag `v9.1.0-r2` | ⬜ Blocked on G-R2-01, G-R2-04, migration reconcile |

---

## 5. Closed this converge (repo evidence)

| ID | Was | Now | Evidence |
|----|-----|-----|----------|
| S1-ALL | ⬜ | ✅ | `docker-compose.release2.yml`, `kong.release2.yml`, deploy/smoke scripts |
| S2-01–05 | ⬜ | ✅ | `copilot_tools.py` (7 R2 tools), `copilot_agent.py` shadow mode, `test_copilot_tools_r2.py` |
| S3-ALL | ⬜ | ✅ | demand-svc SES, UI overlay, `test_forecaster_r2.py` |
| S4-ALL | ⬜ | ✅ | scenario-svc simulator, workbench UI, `test_simulator_r2.py` |
| W1-03–06 | ⬜ | ✅ | `odoo_config.py`, migration 043, `OdooConfigPage.tsx` |
| W1-07–08 | ⬜ | ✅ | `otd_analytics.py`, `OTDDashboardPage.tsx` |
| S6-01–05 | ⬜ | ✅ | trend/root-cause/cost/baseline APIs + dashboard |
| S8-01–04 | ⬜ | ✅ | `ops.py`, `OpsDashboard.tsx`, `test_ops_dashboard.py` |
| S9-01–03 | ⬜ | ✅ | cap-svc analytics, `analyze_quality_patterns` tool |
| S10-01–04 | ⬜ | ✅ | mat-svc supply-chain intel + copilot SC tools |
| S11-01–04 | ⬜ | ✅ | `sop_report.py`, reports API, `SOPReport.tsx` |

---

## 6. Appended tasks (converge — remaining)

| ID | Task | Priority | Sprint | Blocker |
|----|------|----------|--------|---------|
| C-017 | Reconcile migration branch: **043** and **040–042** both from 038 | P0 | — | ✅ **Fixed** — chain `038→043→039→040→041→042` |
| C-018 | Add migration **039** `cdm_otd_snapshot` | P1 | S6 | ✅ exists |
| C-019 | S5 Arabic R2 QA: `docs/qa/arabic-qa-r2.md` + native sign-off | P0 | S5 | 🔄 checklist ✅ · sign-off ⬜ |
| C-020 | S5 `e2e/arabic-r2.spec.ts` RTL regression | P1 | S5 | ✅ 3/4 (8-screen test needs :8082) |
| C-021 | Execute `release2-smoke.ps1` on live R2 stack (G-R2-01) | P0 | S1 | docker build |
| C-022 | Extend `run-release2-demo.ps1` to full R2 checkpoints (G-R2-05) | P1 | — | G-R2-01 |
| C-023 | S7 Odoo DQ dashboard polish + sync history UX verification | P2 | S7 | — |
| C-024 | S11 PDF export for SOP report (guide optional) | P2 | S11 | — |
| C-025 | Write sprint reports for W1, S2, S6–S11 (audit trail) | P2 | — | ✅ 12 reports in `sprints/` |
| C-026 | Push post-tag commits + restabilize kind (from Spec 017 C-08/C-09) | P0 | — | ops |
| C-027 | Tag readiness checklist `v9.1.0-r2` (014 T163) | P2 | — | G-R2-01–05 |

---

## 7. Next actions

1. **C-021** — `.\scripts\deploy-release2.ps1` then `.\scripts\release2-smoke.ps1`  
2. **C-019** — Arabic R2 QA checklist + native speaker sign-off (blocks G-R2-04)  
3. **C-026** — `git push origin master` + kind restabilize  
4. `alembic upgrade head` (through **042**)

---

*Converge v1.0 — `/speckit.converge` 2026-07-10*
