# Tasks: Phase 7 Deep Planning & Operations Intelligence

Legend: [x] done · [~] partial/deferred depth · [ ] not started

## Gate
- [x] T000 Wait for Phases 3-5 E2E strategy re-run to close; consume final report (commit `50c908f`, CONDITIONAL 86P/0F, no genuine defects); confirm Phase 6 artifacts exist

## §1 Multi-Horizon Planning
- [x] T101 `horizons.build_horizons` — 3-horizon cards + coverage health + attention
- [x] T102 `horizons.cascade_plan` — decisions down / constraints up (board escalation, governance level 4)
- [x] T103 `GET /planning-command/horizons`, `POST /planning-command/horizons/cascade`
- [x] T104 `ThreeHorizonsPage.tsx` + Planning Hub tab

## §2 S&OP Deep
- [x] T201 `sop_financial.build_financial_sop` — P&L per consensus + margin-floor alerts (A11)
- [x] T202 `sop_rolling.recalc_rolling_sop` — event-driven recalc + 4-stage governance
- [x] T203 `demand_shaping.build_demand_shaping` — mix-shift / pull-forward / outsource
- [x] T204 `portfolio.optimize_portfolio` — margin per constraint hour ranking
- [x] T205 `POST /sop/financial|rolling|demand-shaping|portfolio`
- [~] T206 S&OP formal stage-gate state machine (skip-to-management_review) — DEFERRED (governance modelled as config; was E2E-SOP-03 BLOCKED)

## §3 Demand Deep
- [x] T301 `demand_decomposition.decompose_demand` — 6 components + composite + 95% CI
- [x] T302 `demand_collaboration.build_consensus` — weighted consensus + disagreement + bias decay
- [x] T303 `npi_forecast.forecast_npi` — analogy + cannibalization + market-sizing composite
- [x] T304 `POST /demand/decompose|collaborate|npi`

## §4 Production Deep
- [x] T401 `scheduling.optimize_setup_sequence` — sequence-dependent setup (exact ≤8, greedy else)
- [x] T402 `scheduling.schedule_multi_resource` — binding-constraint surfacing + A10 escalation
- [x] T403 `scheduling.plan_campaign` — setup savings + net benefit
- [x] T404 `labour.plan_labour` — skills matrix + single-point-of-failure flags + cross-train candidate
- [x] T405 `make_or_buy.analyze_make_or_buy` — dynamic rule on bottleneck utilisation
- [x] T406 `POST /production/setup-sequence|multi-resource|campaign|labour|make-or-buy`

## §5 Operations Deep
- [x] T501 `oee_programme.build_oee_programme` — actions/investment/payback
- [x] T502 `gemba.build_gemba` — real-time WC/operator/job view (IoT STUB, `iot_live=false`)
- [x] T503 `andon.AndonBoard` — red/yellow/blue/white trigger→resolve→board lifecycle
- [x] T504 `kpi_tree.build_kpi_tree` — factory→dept→WC→operator drill-down + attention
- [x] T505 `standard_work.build_standard_work` — A16 step tracking + >120% over-standard flags
- [x] T506 `POST /operations/oee-programme|standard-work`, `GET /operations/gemba|andon|kpi-tree`, `POST /operations/andon`, `POST /operations/andon/{id}/resolve`
- [~] T507 Live IoT machine status + operator tablet UI — STUB/minimal (PH1-02 OPEN)

## §6 Integrated Planning Calendar
- [x] T601 `planning_calendar.build_planning_calendar` — daily/weekly/monthly/quarterly/annual + agents
- [x] T602 `GET /planning-command/calendar` (cadence filter)

## Cross-cutting
- [x] T701 Register `phase7_deep.router` in `router.py`
- [x] T702 Migrations 064 `cdm_planning_horizon`+`cdm_horizon_cascade`, 065 `cdm_sop_financial_plan`, 066 `cdm_demand_consensus`, 067 `cdm_andon_alert` (RLS)
- [x] T703 Frontend: routes/constants/lazyRoutes + Planning/Command Center/Intelligence hub tabs
- [x] T704 pytest suites (26 core + 14 API = 40) green
- [x] T705 Full dpe-svc regression green (320 passed / 2 skipped)
- [x] T706 Ruff clean; frontend `tsc --noEmit` clean
- [x] T707 Kong :8000 smoke of new endpoints (rebuild dpe-svc image) — 13/13 + Andon lifecycle
- [x] T708 `PHASE7-EXECUTION-AND-TEST-REPORT.md` + PRODUCT-STATUS / CHANGELOG / OPEN-ITEMS

## Deferred (Wave 2+) / COM (not faked)
- [~] S&OP interactive stage-gate; monetary net-saving in leveling; live IoT/tablet
- [ ] COM: OQ-7, SOW, PH1-02 (live Odoo/Accounting/market-data/IoT), G-R2-04 Arabic → v9.1.1-r2, Odoo 17/19
