# Tasks — Spec 023 Sprint 4 Wave 1

**Feature**: `023-sprint4-wave1`  
**Date**: 2026-07-11  
**Plan**: `plan.md`  
**Constitution**: 1.2.8  
**Checklist mirror**: `ipe/tasks/sprint4-todo.md`

---

## Phase 1: Odoo Config v2 — schema & crypto (US1)

- [x] T001 Create/verify Alembic migration 050 for `cdm_erp_connection` + `cdm_erp_connection_log` with RLS and partial unique active index
- [x] T002 [P] Add SQLAlchemy models in `ipe_shared` (+ export `__init__`)
- [x] T003 [P] Implement Fernet `password_crypto` module; document `IPE_ENCRYPTION_KEY` in env templates
- [x] T004 Implement `erp_connections_service` (CRUD, soft-delete, activate, test, sync-now, logs)

## Phase 2: Odoo Config v2 — API & tests (US1)

- [x] T005 Expose FastAPI router `/api/v1/erp/connections` (CRUD/test/activate/sync-now/logs); register in connector router
- [x] T006 [P] Add Pydantic schemas (no password on read responses)
- [x] T007 Write `tests/test_erp_connections.py` (encrypt roundtrip, CRUD/test mocks); ensure cryptography dep in pyproject
- [x] T008 Run connector ERP connection tests green

## Phase 3: Odoo Config v2 — UI & i18n (US1)

- [x] T009 [P] Build `OdooConnectionsPage` + `erpConnectionsApi` client
- [x] T010 Wire lazyRoutes/router + Platform/Admin hub nav (R1+R2)
- [x] T011 [P] Add EN/AR i18n keys for Odoo Config connections UI

## Phase 4: OTD Analytics polish (US2)

- [x] T012 Confirm `cdm_otd_snapshot` (039); implement/finish `OTDAggregator` in dpe-svc
- [x] T013 Extend `otd_analytics` API endpoints + schemas as needed
- [x] T014 Write/extend `tests/test_otd_analytics.py`; run green
- [x] T015 Polish `OTDDashboardPage`; ensure R1+R2 nav; EN/AR keys

## Phase 5: Closure docs & Spec 017 sync (US3)

- [x] T016 Update CHANGELOG.md Wave 1 entries
- [x] T017 Update PRODUCT-STATUS.md — Odoo Config v2 + OTD Dashboard rows; Spec 023 active; COM OPEN
- [x] T018 Mark Spec 017 W1-03..W1-08 DONE (eng); refresh `tasks/sprint4-todo.md` checkboxes
- [x] T019 Update root + ipe feature.json / AGENTS.md pointers to Spec 023 / constitution 1.2.8
- [x] T020 Commit Speckit 023 + Wave 1 eng with author `IPE Agent <ipe-agent@local>` (no secrets); push per sprint4 C5

## Phase 6: Spec 022 residuals best-effort (US4)

- [ ] T021 [P] Attempt seed/sync so validate feasibility queue improves (#70) or comment residual — **OPEN**: IPE R2/star-trans Docker not running this session (only nexus containers present)
- [x] T022 [P] Fix or ARB-document write-back activate 404 (#71) — validate script + `docs/qa/ARB-WRITEBACK-ACTIVATE-ROUTE.md`
- [ ] T023 Re-run validate if Docker allows (#72); record evidence or leave OPEN honestly — **OPEN**: blocked on stack-up after T022

## Phase 7: Human / commercial (DOCUMENT ONLY)

- [ ] T024 [HUMAN] OQ-7 pricing — blocks SOW send
- [ ] T025 [HUMAN] OQ-1 Odoo 17 vs 19 confirmation
- [ ] T026 [HUMAN] PH1-02 live Odoo staging
- [ ] T027 [HUMAN] G-R2-04 Arabic native QA → then `v9.1.1-r2` (never push `v9.1.0-r2`)

## Phase 8: Convergence (appended 2026-07-11)

- [ ] T028 [P] With R2/star-trans stack up, run demo seed / sync so feasibility queue validate PASSes (#70/#93)
- [ ] T029 Re-run `star-trans-validate.ps1` after write-back path fix; attach evidence under `docs/qa/` (#72/#95)
- [ ] T030 Close or comment Spec 017 GH issues #31–#36 superseded by Spec 023 delivery

---

## Dependency notes

- T001 → T002 → T004 → T005 → T007 → T008
- T003 || T002; T006 || T005
- T009 → T010; T011 || T009
- T012 → T013 → T014; T015 || T014
- T008 + T014 before claiming Wave 1 eng complete
- T016–T019 after eng green
- T021 || T022 → T023
- T024–T027 never auto-complete
- T028 → T029

## Parallel opportunities

- T002 || T003
- T009 || T012
- T016 || T018 after tests
- T021 || T022
- T028 || T030
