# Tasks: Autonomous Production Planning — IPE V5.0 Convergence

**Input**: [plan.md](./plan.md), [spec.md](./spec.md)

**Branch**: `003-autonomous-planning-v5`

**Format**: `- [ ] T### [P?] [R?] Description with file path`

---

## Phase R1: Close the Loop (Weeks 1–3) 🎯 MVP

### R1.1 Database & Models

- [x] T001 [R1] Create migration `migrations/versions/023_add_schedule_persistence_columns.py` — `cdm_work_order.version`, RLS if new table
- [x] T002 [R1] Add `version` column to `WorkOrder` model in `services/shared/ipe_shared/models/work_order.py`

### R1.2 Core Services

- [x] T003 [R1] Implement `resolve_mo_priority()` in `services/cap-svc/app/core/priority_resolver.py`
- [x] T004 [R1] Implement `persist_schedule_proposal()`, `approve_schedule_mos()`, `load_active_schedule()` in `services/cap-svc/app/core/schedule_persistence.py`
- [x] T005 [R1] Wire demand priority into `schedule_production()` in `services/cap-svc/app/api/v1/capacity.py` (replace feasibility-only priority)
- [x] T006 [R1] Call `persist_schedule_proposal()` after successful solve in `capacity.py`
- [x] T007 [R1] Add `GET /capacity/schedule/active` endpoint in `capacity.py`
- [x] T008 [R1] Add `POST /capacity/schedule/approve` with optimistic locking in `capacity.py`
- [x] T009 [R1] Create Avro schema `services/shared/ipe_shared/events/schemas/ipe_schedule_approved.avsc`
- [x] T010 [R1] Publish `ipe.schedule.approved` on approve in `schedule_persistence.py`

### R1.3 Connector & Frontend

- [x] T011 [R1] Add Kafka consumer for schedule.approved in `services/connector/app/events/handlers.py` (or extend activate flow)
- [x] T012 [R1] Update `apps/web/src/features/schedule/api.ts` — approve → `/capacity/schedule/approve`, fetch → GET active first
- [x] T013 [R1] Update `SchedulePage.tsx` to handle version conflict (409) and refresh prompt

### R1.4 Tests & Demo

- [x] T014 [P] [R1] Unit tests `services/cap-svc/tests/test_priority_resolver.py`
- [x] T015 [P] [R1] Unit tests `services/cap-svc/tests/test_schedule_persistence.py`
- [x] T016 [R1] API tests `services/cap-svc/tests/test_api_schedule_approve.py`
- [x] T017 [R1] Add demo checkpoint 16 to `scripts/run-full-demo.ps1` (persist-after-approve)

**R1 Exit Gate**: Approve → CDM persist → Kafka event → demo 16/16

---

## Phase R2: Planner UX & AI Brain (Weeks 4–6)

### R2.1 Heuristic Fallback

- [x] T018 [R2] Implement `heuristic_schedule()` in `services/cap-svc/app/core/heuristic_scheduler.py`
- [x] T019 [R2] Hook heuristic on CP-SAT timeout in `services/cap-svc/app/core/scheduler.py`

### R2.2 Validation & Controls

- [x] T020 [R2] Add `POST /capacity/validate` pre-solve endpoint in `capacity.py`
- [x] T021 [R2] Extend `ScheduleRequest` with strategy, alpha, beta, capacity_buffer, overtime_allowed
- [x] T022 [R2] Create `ScheduleControlPanel.tsx` in `apps/web/src/features/schedule/components/`
- [x] T023 [R2] Integrate control panel into `SchedulePage.tsx`

### R2.3 Explainability

- [x] T024 [R2] Create `ScheduleExplainPanel.tsx` rendering `xai_explanation` + selected op metadata
- [x] T025 [R2] Wire explain panel to Gantt selection in `GanttChart.tsx` / `SchedulePage.tsx`

### R2.4 Tiered LLM

- [x] T026 [R2] Add Ollama service to `infrastructure/docker/docker-compose.yml`
- [x] T027 [R2] Implement Tier 1→2→503 in `services/nlp-svc/app/core/tiered_router.py`
- [x] T028 [R2] Remove silent rule fallback from `services/nlp-svc/app/core/orchestrator.py` for LLM-unavailable case
- [x] T029 [R2] Add LLM tier status to `apps/web/src/features/admin/components/AdminPage.tsx`

### R2.5 Tests

- [x] T030 [P] [R2] Tests `services/cap-svc/tests/test_heuristic_scheduler.py`
- [x] T031 [P] [R2] Tests `services/nlp-svc/tests/test_tiered_router.py`

**R2 Exit Gate**: Sliders work, XAI visible, Copilot Tier 2 or 503, heuristic on timeout

---

## Phase R3: Enterprise Governance (Weeks 7–9)

- [x] T032 [R3] Extend MDR composite score in `services/dpe-svc/app/core/mdr_engine.py`
- [x] T033 [R3] Add `GET /demand/mdr/dashboard` in `services/dpe-svc/app/api/v1/mdr.py`
- [x] T034 [R3] MDR gate check before schedule in `capacity.py`
- [x] T035 [R3] Create `MdrDashboardPage.tsx` + route
- [x] T036 [R3] Create `DigitalTwinPanel.tsx` using scenario APIs
- [x] T037 [R3] Financial columns in `ResolutionCenterPage.tsx` via `dpe-svc/financial/project`
- [x] T038 [R3] Add Quality/Sustainability/Compliance routes to `apps/web/src/app/router.tsx`
- [x] T039 [R3] War Room auto-aggregate in `services/alert-svc/` or `del-svc/` on supplier delay

**R3 Exit Gate**: MDR blocks <70%, Twin delta UI, Resolution shows $

---

## Phase R4: Production Hardening (Weeks 10–12)

- [x] T040 [R4] Execute Chaos Mesh in staging — `infrastructure/chaos/`
- [x] T041 [R4] SAP sandbox integration test script
- [x] T042 [R4] D365 sandbox integration test script
- [x] T043 [R4] Airflow in default docker-compose
- [x] T044 [R4] k6 200 VU re-cert — `tests/performance/k6/load-test-200vu.js`
- [x] T045 [R4] Tag `v1.0.0` + update `RELEASE_NOTES.md`

**R4 Exit Gate**: Production release certified

---

## Summary

| Phase | Tasks | Effort |
|-------|-------|--------|
| R1 | T001–T017 | 2–3 weeks |
| R2 | T018–T031 | 2–3 weeks |
| R3 | T032–T039 | 2–3 weeks |
| R4 | T040–T045 | 2–3 weeks |
| **Total** | **45 tasks** | **10–12 weeks** |

**Implementation order**: R1 (T001–T017) → R2 (T018–T031) → R3 → R4
