# Tasks: IPE V6.0 — AI-First Strategic Reassessment

**Input**: [plan.md](./plan.md), [spec.md](./spec.md)

**Branch**: `004-ai-first-v6`

**Baseline**: `003-autonomous-planning-v5` @ v1.0.0 (`4efb8de`)

**Format**: `- [ ] T### [P?] [V6-R?] Description with file path`

---

## Phase V6-R1: Activity-Based Planning (Weeks 1–4) 🎯

### V6-R1.1 Database & Models

- [x] T001 [V6-R1] Create migration `migrations/versions/024_add_activity_cost_drivers.py` — `cdm_activity_cost_drivers` + RLS
- [x] T002 [V6-R1] Add SQLAlchemy model `ActivityCostDriver` in `services/shared/ipe_shared/models/activity_cost.py`
- [x] T003 [V6-R1] Seed demo activity cost drivers in `scripts/seed-demo-client.sql`

### V6-R1.2 Margin Priority

- [x] T004 [V6-R1] Implement `compute_margin_adjusted_priority()` in `services/dpe-svc/app/core/margin_priority.py`
- [x] T005 [V6-R1] Add `GET /demand/priority/margin-aware` in `services/dpe-svc/app/api/v1/demand.py`
- [x] T006 [V6-R1] Wire margin weight into `services/cap-svc/app/core/priority_resolver.py`

### V6-R1.3 Activity-Based Solver

- [x] T007 [V6-R1] Implement `activity_objective.py` extending `services/cap-svc/app/core/scheduler_cost.py` / OR-Tools objective
- [x] T008 [V6-R1] Add `strategy=activity_optimized` + `activity_cost_breakdown` to `services/cap-svc/app/api/v1/capacity.py`
- [x] T009 [V6-R1] Extend `heuristic_scheduler.py` with `activity_cost_estimate` and `optimality_gap`

### V6-R1.4 Safety Guardrail (FR-I-06)

- [x] T010 [V6-R1] Block approve when `feasibility_score < 85` in `schedule_persistence.py` + `connector/handlers.py`
- [x] T011 [V6-R1] Emit audit `autonomy_downgraded_to_suggest` in `ipe_shared/audit/service.py` usage

### V6-R1.5 Tests & Demo

- [x] T012 [P] [V6-R1] Unit tests `services/dpe-svc/tests/test_margin_priority.py`
- [x] T013 [P] [V6-R1] Unit tests `services/cap-svc/tests/test_activity_objective.py`
- [x] T014 [P] [V6-R1] Integration test `services/cap-svc/tests/test_guardrail_85.py`
- [x] T015 [V6-R1] Demo checkpoint 17 in `scripts/run-full-demo.ps1` (margin-aware ordering)

**V6-R1 Exit Gate**: SC-V6-01 ≥8% activity-cost delta on demo tenant

---

## Phase V6-R2: Attribute-Based Planning & Tariff (Weeks 5–8)

### V6-R2.1 Database & Models

- [x] T016 [V6-R2] Create migration `migrations/versions/025_add_material_attributes_landed_cost.py` + RLS
- [x] T017 [V6-R2] Add models `MaterialAttribute`, `LandedCostProfile` in `services/shared/ipe_shared/models/`

### V6-R2.2 Landed Cost in pATP

- [x] T018 [V6-R2] Implement `landed_cost.py` in `services/mat-svc/app/core/landed_cost.py`
- [x] T019 [V6-R2] Extend `POST /material/probabilistic-atp` response with TLC fields in `material.py`

### V6-R2.3 Tariff Shock

- [x] T020 [V6-R2] Implement `tariff_shock.py` in `services/dpe-svc/app/core/tariff_shock.py`
- [x] T021 [V6-R2] Add `POST /demand/tariff/shock` and `GET /demand/tariff/exposure` in `dpe-svc`
- [x] T022 [V6-R2] Add `POST /demand/tariff/substitute-draft` → connector queue
- [x] T023 [V6-R2] Avro schema `ipe_tariff_shock.avsc` + publish on shock run
- [x] T024 [V6-R2] Connector handler `handle_tariff_shock` in `connector/app/events/handlers.py`

### V6-R2.4 Frontend & Import

- [x] T025 [V6-R2] Create `TariffShockPanel.tsx` on Control Tower or `/tariff` route
- [x] T026 [V6-R2] Excel tariff matrix import in `services/cap-svc/app/core/` or extend project plan parser
- [x] T027 [P] [V6-R2] Tests `services/mat-svc/tests/test_landed_cost.py`, `services/dpe-svc/tests/test_tariff_shock.py`
- [x] T028 [V6-R2] Demo checkpoint 18 in `scripts/run-full-demo.ps1`

**V6-R2 Exit Gate**: SC-V6-02 100% seeded MOs flagged; ≥1 substitute draft

---

## Phase V6-R3: Visual CPM (Weeks 9–11)

### V6-R3.1 CPM Engine

- [x] T029 [V6-R3] Implement `visual_cpm.py` — critical path, slack, cascade in `services/cap-svc/app/core/`
- [x] T030 [V6-R3] Add `POST /capacity/cpm/cascade` in `capacity.py` with financial_delta + conflicts

### V6-R3.2 Frontend

- [x] T031 [V6-R3] Extend `GanttChart.tsx` — drag-drop, dependency arrows, critical path styling
- [x] T032 [V6-R3] Wire cascade API in `apps/web/src/features/schedule/api.ts` + confirm → approve flow
- [x] T033 [V6-R3] Add CPM latency metric to cap-svc Prometheus middleware

### V6-R3.3 Tests & Demo

- [x] T034 [P] [V6-R3] Tests `services/cap-svc/tests/test_visual_cpm.py`, `test_api_cpm_cascade.py`
- [x] T035 [P] [V6-R3] Playwright perf test cascade p95 <2s in `apps/web/tests/features/schedule/`
- [x] T036 [V6-R3] Demo checkpoint 19 in `scripts/run-full-demo.ps1`

**V6-R3 Exit Gate**: SC-V6-03 p95 <2s on demo tenant

---

## Phase V6-R4: Predictive Maintenance & MDR Auto-Correction (Weeks 12–14)

### V6-R4.1 Telemetry & Database

- [x] T037 [V6-R4] Create migration `026_add_machine_health_telemetry.py` + RLS
- [x] T038 [V6-R4] Extend `services/cap-svc/app/api/v1/iot.py` — ingest RUL, publish Kafka event

### V6-R4.2 Maintenance Blocks

- [x] T039 [V6-R4] Avro `ipe_maintenance_block_required.avsc`
- [x] T040 [V6-R4] Inject maintenance calendar blocks in `scheduler.py` / `ortools_solver.py`
- [x] T041 [V6-R4] Partial re-solve pipeline when block received in `capacity.py`

### V6-R4.3 MDR Auto-Correction

- [x] T042 [V6-R4] Routing deviation detector in `services/dpe-svc/app/core/mdr_engine.py` or `rec-svc`
- [x] T043 [V6-R4] Connector action `sync_routing_correction` + Odoo handler stub
- [x] T044 [P] [V6-R4] Tests `services/cap-svc/tests/test_maintenance_block.py`
- [x] T045 [V6-R4] Demo checkpoint 20 in `scripts/run-full-demo.ps1`

**V6-R4 Exit Gate**: SC-V6-04 telemetry → reschedule ≤60s

---

## Phase V6-R5: Cost of Chaos & Generative War Room (Weeks 15–18)

### V6-R5.1 Cost of Chaos

- [x] T046 [V6-R5] Migration `027_add_chaos_cost_snapshots.py` + RLS
- [x] T047 [V6-R5] Implement `chaos_cost.py` in `services/dpe-svc/app/core/`
- [x] T048 [V6-R5] Add `GET /analytics/cost-of-chaos` in `services/dpe-svc/app/api/v1/analytics.py`
- [x] T049 [V6-R5] Create `CostOfChaosPage.tsx` + route `/cost-of-chaos` + CFO RBAC

### V6-R5.2 Generative War Room

- [x] T050 [V6-R5] Add `GET /war-room/recovery-plan` in `services/alert-svc/app/api/v1/war_room.py`
- [x] T051 [V6-R5] Update `WarRoomPage.tsx` — top 3 ranked recovery cards with $ columns
- [x] T052 [V6-R5] Extend nlp-svc war-room intent in `copilot_tools.py` (scenario ID citations)

### V6-R5.3 Export, Release & Evidence

- [x] T053 [V6-R5] MS Project XML export endpoint or download from Schedule page
- [x] T054 [V6-R5] Update `READINESS.md` to ≥96/100; `RELEASE_NOTES.md` v6.0.0 section
- [ ] T055 [V6-R5] Tag `v6.0.0` after SC-V6-05–08 verified — **see [tasks-release.md](./tasks-release.md) REL-12–REL-14** (requires REL-STACK → REL-DEMO green + approval)

**V6-R5 Exit Gate**: Cost of Chaos live; War Room top-3; demo 20/20; tag v6.0.0

---

## Release Verification (post-build)

**54/55 product tasks complete.** Remaining work is operational — full checklist in [tasks-release.md](./tasks-release.md):

| Phase | Tasks | Blocks T055 |
|-------|-------|-------------|
| P-DOC | P-DOC-01–08 | No |
| REL-STACK | REL-01–05 | Yes |
| REL-TEST | REL-06–08 | Yes |
| REL-DEMO | REL-09–11 | Yes |
| REL-TAG | REL-12–17 | Yes (T055) |
| REL-PROD | REL-18–20 | No (100/100) |

**Critical path**: REL-01 → REL-05 → REL-06 → REL-09 → REL-12 → REL-13 → **T055**

---

## Summary

| Phase | Tasks | Effort |
|-------|-------|--------|
| V6-R1 | T001–T015 | 4 weeks |
| V6-R2 | T016–T028 | 4 weeks |
| V6-R3 | T029–T036 | 3 weeks |
| V6-R4 | T037–T045 | 3 weeks |
| V6-R5 | T046–T055 | 4 weeks |
| **Total** | **55 tasks** | **~18 weeks** |

**Implementation order**: V6-R1 → V6-R2 → V6-R3 → V6-R4 → V6-R5 (R3 may overlap R2 tail after T019)
