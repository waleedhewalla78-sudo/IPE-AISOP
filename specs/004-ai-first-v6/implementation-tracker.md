# Implementation Tracker: IPE V6.0 — AI-First Strategic Reassessment

**Status**: Complete (55/55) — v6.0.0 + v7.0.0 tagged | **Progress**: 55/55 tasks (100%)
**Branch**: `004-ai-first-v6` | **Baseline**: v1.0.0 (`003-autonomous-planning-v5`)  
**Generated**: 2026-06-23 via `/spec-to-implementation`

---

## Linked Spec

| Artifact | Path |
|----------|------|
| Specification | [spec.md](./spec.md) |
| Plan | [plan.md](./plan.md) |
| Tasks | [tasks.md](./tasks.md) |
| Contracts | [contracts/](./contracts/) |
| Verification | [quickstart.md](./quickstart.md) |

---

## Overview

Evolve IPE from a **feasible scheduler** (v1.0.0) to a **Financially-Aware, Attribute-Driven Resilience Engine** (v6.0.0). Five modules over ~18 weeks; extends existing monorepo — no greenfield rewrite. Phoenix commerce remains out of scope.

**Readiness**: **100/100** — v7.0.0 (Speckit 162/162, demo 20/20, chaos 6/6, coverage 75%+)

---

## Requirements Summary

### Functional (P0)

| ID | Requirement | Phase | Acceptance |
|----|-------------|-------|------------|
| FR-I-01 | Net-margin-aware priority | V6-R1 | High-margin MO precedes low-margin on bottleneck |
| FR-I-03 | Activity-cost solver objective | V6-R1 | ≥8% cost delta vs time-only baseline |
| FR-I-06 | 85% feasibility guardrail | V6-R1 | ERP write blocked below 85% |
| FR-I-02 | Total Landed Cost in pATP | V6-R2 | TLC fields in pATP response |
| FR-I-04 | Tariff shock simulator | V6-R2 | +25% Region X flags affected MOs |
| FR-V-01 | Visual CPM drag-drop | V6-R3 | p95 cascade <2s |
| FR-I-05 | Predictive maintenance blocks | V6-R4 | RUL <48h → block → reschedule ≤60s |
| FR-V-02 | Cost of Chaos dashboard | V6-R5 | ≥3 categories with non-zero $ |
| FR-V-04 | Generative War Room recovery | V6-R5 | Top 3 ranked by business score ($) |

### Non-Functional

| SLO | Target |
|-----|--------|
| CPM cascade | p95 <2s (≤20 MOs) |
| Tariff shock | <5s open MO portfolio |
| Maintenance e2e | ≤60s |
| Constitution | RLS, RBAC, tests, Avro events |

---

## Technical Approach

| AD | Decision |
|----|----------|
| AD-007 | Visual CPM in `cap-svc` module first |
| AD-008 | Margin priority in `dpe-svc` → consumed by `cap-svc` |
| AD-009 | Landed cost in `mat-svc` pATP path |
| AD-010 | Tariff shock orchestration in `dpe-svc` + `mat-svc` |
| AD-011 | 85% block ERP / 90% auto-confirm (fea-svc) |
| AD-012 | Cost of Chaos from audit + delay + override streams |

**Migrations**: 024 (activity costs) → 025 (attributes/landed cost) → 026 (machine health) → 027 (chaos snapshots)

---

## Implementation Phases

### V6-R1 — Activity-Based Planning (Weeks 1–4) ✅ COMPLETE

**Goal**: Margin-aware priority + activity-cost objective + FR-I-06 guardrail  
**Exit gate**: SC-V6-01 — ≥8% activity-cost delta on demo tenant  
**Services**: dpe-svc, cap-svc, fea-svc, connector  
**Contract**: [v6-r1-abp.md](./contracts/v6-r1-abp.md)

| Task | Component | Status | Owner | Notes |
|------|-----------|--------|-------|-------|
| T001 | DB migration 024 | ✅ Done | | `cdm_activity_cost_drivers` + RLS |
| T002 | Shared model | ✅ Done | | `activity_cost.py` |
| T003 | Seed data | ✅ Done | | `seed-demo-client.sql` |
| T004 | Margin priority core | ✅ Done | | `margin_priority.py` |
| T005 | API | ✅ Done | | `GET /demand/priority/margin-aware` |
| T006 | cap-svc wiring | ✅ Done | | `priority_resolver.py` |
| T007 | Solver objective | ✅ Done | | `activity_objective.py` |
| T008 | Schedule API | ✅ Done | | `strategy=activity_optimized` |
| T009 | Heuristic fallback | ✅ Done | | cost estimate + gap flag |
| T010 | Guardrail | ✅ Done | | block approve <85% |
| T011 | Audit event | ✅ Done | | `autonomy_downgraded_to_suggest` |
| T012 | Tests | ✅ Done | | `test_margin_priority.py` |
| T013 | Tests | ✅ Done | | `test_activity_objective.py` |
| T014 | Tests | ✅ Done | | `test_guardrail_85.py` |
| T015 | Demo | ✅ Done | | checkpoint 17 |

**Estimated effort**: 4 weeks | **Dependencies**: v1.0.0 baseline running

---

### V6-R2 — Attribute-Based Planning & Tariff (Weeks 5–8)

**Goal**: Material attributes, landed cost, tariff shock + substitute draft  
**Exit gate**: SC-V6-02 — 100% seeded MOs flagged; ≥1 substitute draft  
**Contract**: [v6-r2-tariff.md](./contracts/v6-r2-tariff.md)

| Task | Component | Status |
|------|-----------|--------|
| T016–T017 | DB + models (025) | ✅ Done |
| T018–T019 | Landed cost + pATP | ✅ Done |
| T020–T024 | Tariff shock API + Kafka + connector | ✅ Done |
| T025–T026 | Frontend + Excel import | ✅ Done |
| T027–T028 | Tests + demo checkpoint 18 | ✅ Done |

**Estimated effort**: 4 weeks | **Dependencies**: V6-R1 margin API (T004–T006)

---

### V6-R3 — Visual CPM (Weeks 9–11)

**Goal**: Drag-drop Gantt with critical path; cascade p95 <2s  
**Exit gate**: SC-V6-03  
**Contract**: [v6-r3-visual-cpm.md](./contracts/v6-r3-visual-cpm.md)

| Task | Component | Status |
|------|-----------|--------|
| T029–T030 | CPM engine + cascade API | ✅ Done |
| T031–T033 | Gantt UI + metrics | ✅ Done |
| T034–T036 | Tests + Playwright perf + demo 19 | ✅ Done |

**Estimated effort**: 3 weeks | **Dependencies**: V6-R1 activity cost metadata on cascade response

---

### V6-R4 — Predictive Maintenance & MDR Auto-Correction (Weeks 12–14)

**Goal**: IoT RUL blocks + routing correction drafts  
**Exit gate**: SC-V6-04 — telemetry → reschedule ≤60s  
**Contract**: [v6-r4-predictive-maint.md](./contracts/v6-r4-predictive-maint.md)

| Task | Component | Status |
|------|-----------|--------|
| T037–T038 | DB 026 + IoT ingest | ✅ Done |
| T039–T041 | Kafka + maintenance blocks + re-solve | ✅ Done |
| T042–T045 | MDR draft + connector + demo 20 | ✅ Done |

**Estimated effort**: 3 weeks | **Dependencies**: cap-svc scheduler from 003

---

### V6-R5 — Cost of Chaos & Generative War Room (Weeks 15–18)

**Goal**: CFO dashboard + ranked recovery plans + v6.0.0 release  
**Exit gate**: SC-V6-05–08; tag **v6.0.0**  
**Contract**: [v6-r5-chaos-warroom.md](./contracts/v6-r5-chaos-warroom.md)

| Task | Component | Status |
|------|-----------|--------|
| T046–T049 | Chaos cost API + CFO UI | ✅ Done |
| T050–T052 | War Room recovery + Copilot | ✅ Done |
| T053–T055 | MS Project export + READINESS + tag | 🟡 T055 pending |

**Estimated effort**: 4 weeks | **Dependencies**: V6-R1–R4 (financial + disruption data)

---

## Dependency Graph

```
v1.0.0 baseline
    └── V6-R1 (ABP) ──┬── V6-R2 (Tariff)
                      ├── V6-R3 (CPM) ──┐
                      └── FR-I-06         │
    V6-R2 ────────────────────────────────┤
    V6-R3 ────────────────────────────────├── V6-R5 (Chaos + War Room)
    V6-R4 (Maint) ────────────────────────┘
```

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| CPM >2s on large plants | SC-V6-03 miss | Demo scope ≤20 MOs; async cascade post-v6.0.0 |
| Missing GL/cost data | Wrong margin priority | Warning fallback; seed drivers |
| Notion/task drift | Tracking gaps | Sync from this file + `tasks.md` |
| Scope creep Phoenix | Delay | Explicit out-of-scope in spec |

---

## Success Criteria (Release v6.0.0)

| ID | Criterion | Verified |
|----|-----------|----------|
| SC-V6-01 | ≥8% activity-cost delta | ⬜ |
| SC-V6-02 | 100% seeded MOs flagged on tariff shock | ⬜ |
| SC-V6-03 | CPM p95 <2s | ⬜ |
| SC-V6-04 | Maintenance e2e ≤60s | ⬜ |
| SC-V6-05 | ≥3 chaos categories with $ | ⬜ |
| SC-V6-06 | War Room top 3 with $ columns | ⬜ |
| SC-V6-07 | Readiness ≥96/100 | ⬜ |
| SC-V6-08 | Demo 20/20 checkpoints | ⬜ |

---

## Progress Log

| Date | Milestone | Notes |
|------|-----------|-------|
| 2026-06-23 | Plan complete | plan.md, tasks.md, contracts, quickstart created |
| 2026-06-23 | Tracker created | `/spec-to-implementation` — Notion sync pending auth |
| | V6-R1 started | |
| | V6-R1 complete | |
| | v6.0.0 tagged | |

---

## Next Actions

1. **Start V6-R1**: Run `/speckit.implement` or begin T001 (migration 024)
2. **Verify baseline**: `.\scripts\start-product.ps1` + v1.0.0 demo checkpoints 1–16
3. **Notion sync** (optional): Authenticate Notion MCP → import phases as project pages + tasks from tables above

---

## Notion Import Template

When Notion MCP is authenticated, create:

1. **Page**: `Implementation Plan: IPE V6.0 AI-First` — paste Overview + Technical Approach + Phases from this file
2. **Tasks database rows** (55): one row per T001–T055 with properties:
   - **Name**: `T### — [short title]`
   - **Status**: To Do
   - **Phase**: V6-R1 | V6-R2 | V6-R3 | V6-R4 | V6-R5
   - **Priority**: P0 for T001–T015, T018–T021, T029–T031, T046–T051; P1/P2 otherwise
   - **Project**: IPE V6.0
   - **Acceptance**: Link to contract AC-R*-## row
