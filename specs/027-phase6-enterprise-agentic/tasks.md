# Tasks: Phase 6 Enterprise Agentic Platform

Status legend: [x] done · [ ] pending · [~] deferred

## Gate
- [x] T000 Poll + consume `docs/qa/PHASES3-5-E2E-TEST-REPORT.md`; verify dpe-svc phase4/phase5 foundations green (22/22); document PROCEED

## Phase 6A — Commercial + Analytics
- [x] T001 `app/core/phase6/commercial_intel.py` — A13 pricing / deal / contract
- [x] T002 `app/core/phase6/analytics_intel.py` — A14 insights / trend / anomaly / predictions
- [x] T003 `app/core/phase6/odoo_accounting.py` — scaffold connector (mock, PH1-02 honest)
- [x] T004 `tests/test_phase6_commercial.py` (7)
- [x] T005 `tests/test_phase6_analytics.py` (9)
- [x] T006 Migration `060_cdm_commercial_quote.py` (RLS)
- [x] T007 Migration `061_cdm_analytics_insight.py` (RLS)
- [x] T008 Frontend M7 Analytics Command + M8 Commercial Command pages

## Phase 6B — Procurement + Shop Floor Execution
- [x] T010 `app/core/phase6/procurement_exec.py` — A15 3-way match / receipt
- [x] T011 `app/core/phase6/shop_floor.py` — A16 instructions / time / progress (IoT stub)
- [x] T012 `tests/test_phase6_execution.py` (8, incl. Odoo mock)
- [x] T013 Migration `062_cdm_three_way_match.py` (RLS)
- [x] T014 Frontend M9 Procurement + Shop Floor page

## Phase 6C — Cross-Functional Orchestration
- [x] T020 `app/core/phase6/orchestrator.py` — A17 hierarchy / 6 policies / cascade / cross-functional ATP
- [x] T021 `tests/test_phase6_orchestrator.py` (10, incl. headline ATP)
- [x] T022 Migration `063_cdm_orchestrator_decision.py` (RLS)
- [x] T023 A17 orchestrator actions wired into M8 UI

## Integration + API
- [x] T030 `app/api/v1/phase6_enterprise.py` — `/enterprise/*` routes (A13–A17, M7–M9, integrations status)
- [x] T031 Register router in `app/api/v1/router.py`
- [x] T032 `tests/test_phase6_api.py` — ASGI smoke (6)
- [x] T033 lazyRoutes + router.tsx + IntelligenceHub tabs + constants routes
- [ ] T034 Kong :8000 API smoke against `/api/v1/enterprise/*` (R2 stack)

## Quality + docs
- [x] T040 ruff clean on Phase 6 code
- [x] T041 Full dpe-svc suite regression (280 passed / 2 skipped)
- [x] T042 Frontend typecheck (tsc --noEmit) clean
- [x] T043 `docs/qa/PHASE6-EXECUTION-AND-TEST-REPORT.md`
- [x] T044 Update PRODUCT-STATUS / CHANGELOG / OPEN-ITEMS honesty
- [x] T045 Constitution 1.3.0 → 1.4.0 (Principle X) + root sync
- [x] T046 Commit with env author `IPE Agent <ipe-agent@local>`

## Deferred (Phase 6D)
- [~] T050 Agent tuning / acceptance-rate calibration
- [~] T051 SOC 2 readiness / multi-plant activation
- [~] T052 Live Odoo Accounting / market data / IoT (PH1-02 OPEN)
