# Implementation Plan: Autonomous Production Planning — IPE V5.0 Convergence

**Branch**: `003-autonomous-planning-v5` | **Date**: 2026-06-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-autonomous-planning-v5/spec.md`, IPE Status Report, Expert Assessment vs. V5.0 PRD

**User goal**: Transform IPE from demo-ready AI scheduler (~78%) to enterprise autonomous planning platform (~95%) with closed-loop execution, planner UX, MDR governance, and financial translation.

---

## Summary

**Technical approach**: Four phased remediation (R1–R4) over 10–12 weeks on the existing IPE monorepo. R1 closes the critical loop (CDM persistence, priority wiring, outbox). R2 delivers planner-facing AI (controls, XAI, tiered LLM, heuristic fallback). R3 adds V5.0 differentiators (MDR gate, Digital Twin UI, financial impact, War Room automation). R4 hardens for production (Chaos, multi-ERP sandbox, load cert).

**Baseline readiness**: **78/100** (demo-ready, 15/15 checkpoints)  
**Target after R1**: **85/100** (closed-loop scheduling)  
**Target after R2**: **90/100** (planner adoption)  
**Target after R3**: **95/100** (enterprise governance)  
**Target after R4**: **100/100** (v1.0.0 production release)

---

## Technical Context

**Language/Version**: Python 3.12+ (14 microservices), TypeScript 5.5 / React 18 (SPA)

**Primary Dependencies**: FastAPI, SQLAlchemy async, PostgreSQL 16, Kafka, OR-Tools CP-SAT, openpyxl, Anthropic SDK, Ollama (Tier 2 LLM), Kong 3.x

**Storage**: PostgreSQL CDM with RLS; new tables: `cdm_schedule_version` (R1), MDR composite fields (R3)

**Testing**: pytest (cap/dpe/fea/res/nlp), Vitest (frontend), integration E2E, k6 load

**Target Platform**: Docker Compose (dev); Kubernetes/Helm (R4 production)

**Performance Goals**: Schedule solve ≤30s small factory; heuristic fallback ≤2s; approve→CDM persist ≤60s p95

**Constraints**: Constitution I–III and VI; tenant RLS on all new tables; RBAC on approve/promote endpoints

**Scale/Scope**: 32 FRs across 4 phases; ~120 implementation tasks

---

## Constitution Check

| Principle | Feature Impact | Phase |
|-----------|-----------------|-------|
| **I. Tenant RLS** | Migration 023+ enable RLS on schedule_version | R1 |
| **II. Auth/RBAC** | Approve, promote, MDR admin require planner/admin roles | R1–R3 |
| **III. Test-backed** | Every FR has pytest/Vitest coverage | All |
| **IV. Event mesh** | `ipe.schedule.approved` Avro schema + idempotent consumer | R1 |
| **VI. Observability** | New endpoints expose health; metrics unchanged | All |

---

## Architecture Decisions

### AD-001: Schedule persistence in cap-svc (not connector)

**Decision**: Persist solver proposals and approvals in `cap-svc` via `schedule_persistence.py`; connector consumes Kafka for ERP sync only.

**Rationale**: Single writer to CDM; optimistic locking at source; matches V5.0 transactional outbox pattern.

### AD-002: Priority from demand_line, not feasibility_score

**Decision**: `resolve_mo_priority()` reads `cdm_demand_line.priority_score` (0–100 → 0.01–1.0); fallback to normalized feasibility only when no demand link.

**Rationale**: Implements Expert Assessment Fix 1; CP-SAT already multiplies tardiness by `priority_score`.

### AD-003: Proposal vs. approved state on MO

**Decision**: POST `/schedule` sets `ai_suggested_start/end` + work order `planned_start/end`; POST `/schedule/approve` promotes to `planned_start/end` on MO, clears suggestions, increments `version`.

**Rationale**: Existing connector activate flow already expects `ai_suggested_*`; minimal connector change.

### AD-004: Heuristic fallback = EDD + priority queue

**Decision**: On CP-SAT timeout/UNKNOWN, run greedy EDD scheduler per work center; set `solver_status=heuristic_fallback`.

**Rationale**: TASK-C-002 gap; always return workable proposal.

### AD-005: Tiered LLM: Anthropic → Ollama → 503

**Decision**: Extend `nlp-svc/tiered_router.py`; remove silent rule-based fallback from orchestrator for user-facing errors.

**Rationale**: V5.0 Copilot mandate; Admin UI shows tier health.

### AD-006: MDR composite 70% gate

**Decision**: Extend `dpe-svc/mdr_engine.py` with routing + inventory dimensions; cap-svc checks gate before POST `/schedule`.

**Rationale**: Harmonize backend (80% BOM-only) with V5.0 PRD 70% composite.

---

## Project Structure

```text
specs/003-autonomous-planning-v5/
├── spec.md
├── plan.md                 # This file
├── tasks.md
├── quickstart.md
├── contracts/
│   ├── r1-closed-loop.md
│   ├── r2-planner-ux.md
│   └── r3-enterprise.md
└── checklists/requirements.md

ipe/
├── migrations/versions/023_add_schedule_persistence_columns.py
├── services/
│   ├── cap-svc/app/core/
│   │   ├── schedule_persistence.py    # NEW
│   │   ├── priority_resolver.py       # NEW
│   │   ├── heuristic_scheduler.py     # NEW (R2)
│   │   └── scheduler.py               # heuristic hook
│   ├── cap-svc/app/api/v1/capacity.py # approve, active, validate
│   ├── dpe-svc/app/core/mdr_engine.py # composite score
│   ├── nlp-svc/app/core/tiered_router.py
│   └── connector/app/events/handlers.py  # schedule.approved consumer
├── services/shared/ipe_shared/events/schemas/
│   └── ipe_schedule_approved.avsc
└── apps/web/src/features/schedule/
    ├── components/ScheduleControlPanel.tsx
    ├── components/ScheduleExplainPanel.tsx
    ├── api.ts
    └── SchedulePage.tsx
```

---

## Phase Overview

| Phase | Duration | Focus | Exit Gate | Key Services |
|-------|----------|-------|-----------|--------------|
| **R1** | Wks 1–3 | Close the loop | Approve→persist→Kafka | cap-svc, connector |
| **R2** | Wks 4–6 | Planner UX + AI brain | Sliders, XAI, LLM, heuristic | cap-svc, nlp-svc, web |
| **R3** | Wks 7–9 | V5.0 differentiators | MDR, Twin, Finance, War Room | dpe-svc, cap-svc, res-svc, web |
| **R4** | Wks 10–12 | Production hardening | v1.0.0 cert | infra, connectors |

---

## Phase R1: Close the Loop (Weeks 1–3)

### R1.1 Database (Day 1–2)

- Migration 023: `cdm_work_order.version` (Integer, default 1)
- Migration 023: `cdm_schedule_version` table (immutable snapshots — optional v1: MO fields only)

### R1.2 Schedule Persistence Service (Days 2–4)

| Module | Responsibility |
|--------|----------------|
| `priority_resolver.py` | Demand priority → normalized weight |
| `schedule_persistence.py` | `persist_proposal()`, `approve_mos()`, `load_active_gantt()` |
| `capacity.py` | Wire persist after solve; new endpoints |

**New API endpoints**:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/capacity/schedule/active` | Load persisted Gantt from CDM |
| POST | `/capacity/schedule/approve` | Optimistic-lock approve + Kafka |
| POST | `/capacity/validate` | Pre-solve Valid/Warning/Blocked (R2 start) |

### R1.3 Priority Wiring (Day 3)

Replace `feasibility_score` priority in `capacity.py` loop with `resolve_mo_priority(session, tid, mo.id)`.

### R1.4 Event Outbox (Days 4–5)

- Avro: `ipe_schedule_approved.avsc`
- Publish on approve; connector consumer triggers Odoo sync

### R1.5 Frontend (Days 5–6)

- `approveSchedule` → `/capacity/schedule/approve`
- `fetchSchedule` → try GET active, else POST schedule
- Pass MO versions for optimistic lock

### R1.6 Tests (Days 6–8)

- `test_schedule_persistence.py`
- `test_priority_resolver.py`
- `test_api_schedule_approve.py`
- Update `run-full-demo.ps1` checkpoint 16

---

## Phase R2: Planner UX (Weeks 4–6)

### R2.1 Heuristic Fallback

- `heuristic_scheduler.py`: greedy EDD
- Hook in `scheduler.py` when status UNKNOWN

### R2.2 Schedule Control Panel

- Strategy selector + sliders → `ScheduleRequest` params / cost-optimized endpoint
- Component: `ScheduleControlPanel.tsx`

### R2.3 XAI Panel

- Component: `ScheduleExplainPanel.tsx` rendering API `xai_explanation` + per-op factors

### R2.4 Tiered LLM Router

- Ollama container in docker-compose
- `tiered_router.py`: Tier 1 → Tier 2 → 503
- Admin tier health in `AdminPage.tsx`

---

## Phase R3: Enterprise Modules (Weeks 7–9)

### R3.1 MDR Dashboard + Gate

- `GET /demand/mdr/dashboard` composite score
- cap-svc pre-schedule gate at 70%

### R3.2 Digital Twin UI

- `DigitalTwinPanel.tsx` wrapping scenario clone/disrupt/solve/diff APIs

### R3.3 Financial Translation

- Resolution Center columns from `dpe-svc/financial/project`

### R3.4 Navigation + War Room

- Router: Quality, Sustainability, Compliance
- War Room auto-aggregate on supplier delay events

---

## Phase R4: Production Hardening (Weeks 10–12)

- Execute Chaos Mesh in staging
- SAP/D365 sandbox connector tests
- Airflow in default compose
- k6 200 VU re-certification
- Tag `v1.0.0`

---

## Risk Register

| Risk | Mitigation |
|------|------------|
| Ollama GPU/memory in Docker | CPU-only Llama-3-8B-q4; document min RAM |
| Optimistic lock UX friction | Auto-refresh on 409 with diff summary |
| MDR false blocks | Hysteresis band 68–72% |
| Scope creep R3–R4 | Strict FR traceability in tasks.md |

---

**Next**: Execute [tasks.md](./tasks.md) starting Phase R1 (T001–T025).
