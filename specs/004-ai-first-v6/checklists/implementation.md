# Implementation Checklist: IPE V6.0 (004)

**Purpose**: Exit gate verification before `v6.0.0` tag  
**Updated**: 2026-06-23 | **Progress**: 54/55 tasks

---

## V6-R1 — Activity-Based Planning ✅

- [x] Migration 024 + RLS on `cdm_activity_cost_drivers`
- [x] `GET /demand/priority/margin-aware`
- [x] `strategy=activity_optimized` + activity cost breakdown
- [x] 85% feasibility guardrail on approve
- [x] Tests: margin, activity objective, guardrail
- [x] Demo checkpoint 17

## V6-R2 — Tariff & Landed Cost ✅

- [x] Migration 025 + material attributes + landed cost profiles
- [x] pATP TLC fields
- [x] `POST /demand/tariff/shock`, exposure, substitute draft
- [x] Avro `ipe_tariff_shock` + connector handler
- [x] TariffShockPanel + `/tariff` route
- [x] Tests: landed_cost, tariff_shock
- [x] Demo checkpoint 18

## V6-R3 — Visual CPM ✅

- [x] `visual_cpm.py` — critical path, slack, cascade
- [x] `POST /capacity/cpm/cascade`, `/cpm/apply`
- [x] Gantt drag-drop + critical path styling
- [x] `cap_svc_cpm_cascade_duration_seconds` metric
- [x] Tests: visual_cpm, api_cpm_cascade, perf test
- [x] Demo checkpoint 19

## V6-R4 — Predictive Maintenance ✅

- [x] Migration 026 + machine health telemetry
- [x] RUL ingest on `/iot/telemetry`
- [x] Avro `ipe_maintenance_block_required`
- [x] Maintenance block injection + partial re-solve
- [x] MDR routing deviation + connector stub
- [x] Tests: maintenance_block
- [x] Demo checkpoint 20 (telemetry portion)

## V6-R5 — Cost of Chaos & War Room ✅

- [x] Migration 027 + chaos_cost aggregation
- [x] `GET /analytics/cost-of-chaos`
- [x] `/cost-of-chaos` page (executive RBAC)
- [x] `GET /war-room/recovery-plan` top 3
- [x] WarRoomPage $ columns + Copilot tool
- [x] MS Project XML export
- [x] READINESS 96/100 + RELEASE_NOTES v6.0.0
- [ ] T055: Git tag `v6.0.0` — **pending approval**

---

## Constitution Compliance (I–VI)

- [x] **I RLS**: Migrations 024–027 enable tenant isolation
- [x] **II Auth**: RBAC on all new endpoints; JWT demo
- [x] **III Tests**: pytest for each phase; launch-verify
- [x] **IV Events**: tariff.shock, maintenance.block_required Avro
- [x] **V API**: Frontend routes match backend contracts
- [x] **VI Observability**: CPM histogram + existing /metrics

---

## Residual (96 → 100)

- [ ] k6 200 VU executed with evidence attached
- [ ] Chaos Mesh evidence attached
- [ ] Keycloak live IdP (BLOCKED C-007)
