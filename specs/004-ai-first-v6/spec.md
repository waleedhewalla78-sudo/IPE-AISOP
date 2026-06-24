# Feature Specification: IPE V6.0 — AI-First Strategic Reassessment

**Feature Branch**: `004-ai-first-v6`

**Created**: 2026-06-23

**Status**: Implemented — **54/55 tasks complete** (T055 git tag pending). See [tasks.md](./tasks.md), [analyze-v6.md](./analyze-v6.md), [clarify-v6.md](./clarify-v6.md).

**Input**: Enterprise Nexus Platform (ENP) & IPE **V6.0 Unified Master Blueprint** (June 2026), building on delivered **`003-autonomous-planning-v5`** (tag `v1.0.0` / commit `4efb8de`).

**Supersedes (product vision)**: V5.0 PRD gold standard for IPE planning scope; does **not** replace Phoenix commerce PRD.

---

## Executive Summary

IPE v1.0.0 closed the **execution loop**: schedule persistence, demand priority wiring, MDR gate, planner UX, tiered LLM, War Room aggregate, and R4 hardening tooling. The platform is now a credible **demo-to-pilot** APS overlay on Odoo.

The **2026 AI-First Strategic Reassessment** identifies the next competitive gap: IPE still optimizes primarily for **time and feasibility**, not for **margin, tariff resilience, activity-based cost, visual critical-path agility, and quantified chaos cost**. Mid-2026 buyers (CFO + VP Supply Chain) expect Kinaxis/SAP IBP-class **financial translation** and geopolitical **attribute-driven planning** at mid-market TCO.

This feature defines the **minimum IPE-only work** to converge the existing monorepo toward **IPE V6.0** — absorbing five strategic modules into architecture, FRs, and UX without a greenfield rewrite.

### Five Strategic Modules (V6.0)

| # | Module | V6.0 intent | Current IPE baseline (post-003) |
|---|--------|-------------|----------------------------------|
| 1 | **Activity-Based Planning (ABP)** | Prioritize & schedule by **net margin** and activity costs (setup, overtime, expedite) | Priority from `priority_score`; cost-optimized path with energy TOU tariffs + overtime multipliers — **not** full ABC margin objective |
| 2 | **Attribute-Based Planning** | Materials tagged with origin/tariff/carbon; **Total Landed Cost** in pATP | Inventory netting + probabilistic ATP; **no** geopolitical tariff matrix or substitute BOM workflow |
| 3 | **Visual CPM** | Drag-drop Gantt; critical path highlight; **<2s** cascade recalc | Static Gantt + approve; no drag-drop or CPM engine |
| 4 | **Predictive Maintenance** | IoT RUL → maintenance blocks **48h** ahead; re-sequence MOs | `iot_health.py` capacity degradation; **no** RUL ingestion pipeline or proactive blocks |
| 5 | **Cost of Chaos** | Pareto dashboard: $ impact of delays, breakdowns, overrides | Executive delay breakdown; partial resolution `$`; **no** unified CFO dashboard |

### Dual-Engine Scope Boundary

| Engine | In scope for **004** | Notes |
|--------|----------------------|-------|
| **IPE V6.0 (Engine B)** | ✅ Full feature | This spec |
| **Project Phoenix (Engine A)** | ❌ Out of scope | FR-C-01–03 tracked as ENP dependency only; no Next.js/Stripe work here |

**Phase 1 ICP (unchanged)**: Discrete manufacturers, 100–1,000 employees, 1–2 sites, Odoo 16/17 primary ERP.

---

## Problem Statement

Planners using IPE v1.0.0 can **approve a feasible schedule**, but they cannot answer:

1. *Which order should run first to protect **margin**, not just due date?*
2. *What happens to **landed cost and margin** if Region X tariffs rise 25% tomorrow?*
3. *If I drag this MO on the Gantt, what is the new **critical path** and **$ impact** in under 2 seconds?*
4. *Which machine failure will hurt us **before** it happens, and is the schedule already re-sequenced?*
5. *How much money did **chaos** (breakdowns, delays, overrides) cost us this week in activity-based terms?*

Without these capabilities, IPE remains a strong **scheduler** but not the **Financially-Aware, Attribute-Driven Resilience Engine** described in ENP V6.0.

---

## Baseline Delivered (003 — do not re-build)

Treat as **frozen baseline** unless a V6 FR explicitly extends behavior:

- Closed-loop schedule: persist, approve, optimistic lock, `ipe.schedule.approved`, connector sync
- Demand priority → CP-SAT tardiness weight
- MDR composite 70% gate + `/mdr` dashboard
- Schedule control panel, XAI panel, heuristic fallback, tiered LLM + Admin tier health
- Resolution financial columns (MO-level projection via `dpe-svc/financial/project`)
- Digital Twin disrupt simulation (partial); War Room aggregate endpoint
- OR-Tools CP-SAT, Monte Carlo pATP, feasibility pipeline, progressive autonomy (Shadow/Suggest)
- SAP/D365 mapper scripts; Chaos/k6/Airflow tooling

See [../003-autonomous-planning-v5/clarify.md](../003-autonomous-planning-v5/clarify.md) for v1.0.0 caveats.

---

## User Scenarios & Testing

Stories grouped by V6 module. Each maps to a phase exit gate.

### Phase V6-R1 — Activity-Based Planning & Margin Prioritization (Weeks 1–4)

#### User Story V6-1 — CFO-Aligned Order Priority (Priority: P0)

As a **supply chain manager**, I need the scheduler to prioritize MOs by **true net margin** (revenue minus activity-based overhead and setup burden), not raw revenue or feasibility alone, so we protect profit under capacity constraints.

**Independent Test**: Two MOs with equal due dates — high-margin MO receives earlier slot; Admin weight changes reorder output.

**Acceptance Scenarios**:

1. **Given** MO-A net margin $12k and MO-B net margin $3k on a shared bottleneck, **When** schedule runs with margin-aware strategy, **Then** MO-A operations precede MO-B.
2. **Given** `dpe-svc` activity cost drivers (setup mins, overtime rate), **When** priority is recalculated, **Then** `priority_score` reflects margin-adjusted business score documented in audit log.
3. **Given** missing cost data for a product, **When** schedule runs, **Then** system falls back to existing priority with **Warning** status (not silent default).

**Maps to**: FR-I-01, FR-I-03 (partial)

---

#### User Story V6-2 — Activity-Based Financial Scheduling (Priority: P0)

As a **planner**, I need the solver objective to penalize **overtime, setup churn, and expedite activity costs**, not just tardiness, so the approved plan minimizes activity-based waste.

**Independent Test**: Scenario with overtime-eligible WC — solver prefers spread load vs. concentrated overtime when margin weights equal.

**Acceptance Scenarios**:

1. **Given** two feasible schedules with equal OTD, **When** activity-based objective runs, **Then** lower total activity cost schedule is selected.
2. **Given** CP-SAT timeout, **When** heuristic fallback runs, **Then** result includes `activity_cost_estimate` and `optimality_gap` flag if >5%.
3. **Given** cost-optimized endpoint with `alpha`, **When** alpha=0 vs alpha=1, **Then** output shifts measurably between time-first and cost-first.

**Maps to**: FR-I-03, UC-02 fallback rule

**Phase V6-R1 Exit Gate**: Margin-aware priority + activity-cost term in solver; demo shows ≥8% activity-cost delta between strategies on seeded tenant.

---

### Phase V6-R2 — Attribute-Based Planning & Tariff Resilience (Weeks 5–8)

#### User Story V6-3 — Total Landed Cost in ATP (Priority: P0)

As a **procurement manager**, I need probabilistic ATP to evaluate **Total Landed Cost** (base + freight + tariffs + risk premium), so sourcing decisions reflect geopolitical exposure.

**Acceptance Scenarios**:

1. **Given** material attributes (origin, tariff code, carbon), **When** pATP runs, **Then** response includes `landed_cost_per_unit` and attribute snapshot.
2. **Given** tariff matrix update for Region X, **When** pATP recalculates, **Then** affected MO feasibility reflects new cost within same API call chain.

**Maps to**: FR-I-02

---

#### User Story V6-4 — Tariff Shock What-If Simulator (Priority: P1)

As a **planner**, I need to apply “**+25% tariff on Region X**” and instantly see cascading margin impact on open MOs, so I can respond before ERP re-entry.

**Acceptance Scenarios**:

1. **Given** open MO portfolio, **When** planner runs tariff shock scenario, **Then** dashboard lists MOs below margin threshold with $ erosion estimate.
2. **Given** pre-approved substitute material (attribute match), **When** shock breaches threshold, **Then** system drafts BOM substitution proposal for planner approval (Odoo action queue — not autonomous ERP write).

**Maps to**: FR-I-04, UC-03

**Phase V6-R2 Exit Gate**: Landed cost in pATP; tariff shock UI with ≥1 substitute draft flow on demo data.

---

### Phase V6-R3 — Visual CPM Agility (Weeks 9–11)

#### User Story V6-5 — Drag-Drop Gantt with Critical Path (Priority: P0)

As a **planner**, I need to drag an MO on the Gantt and see the **critical path** redraw in red with financial/temporal cascade impact in **<2 seconds**, so I can negotiate changes without leaving the Resolution Center.

**Acceptance Scenarios**:

1. **Given** active schedule loaded, **When** planner drags MO start by +2 days, **Then** dependency arrows and critical path update within 2s (p95).
2. **Given** drag creates infeasibility, **When** cascade completes, **Then** conflicting operations highlighted with human-readable reason.
3. **Given** drag accepted, **When** planner confirms, **Then** change flows through existing approve/outbox workflow (no silent CDM write).

**Maps to**: FR-V-01, SLO Visual CPM <2s

**Phase V6-R3 Exit Gate**: Interactive Gantt on Schedule or Resolution page; CPM recalc p95 <2s on demo tenant (≤20 MOs).

---

### Phase V6-R4 — Predictive Maintenance & MDR Auto-Correction (Weeks 12–14)

#### User Story V6-6 — Predictive Maintenance Blocks (Priority: P1)

As a **maintenance manager**, I need IoT **RUL <48h** signals to inject maintenance blocks and trigger automatic re-sequencing, so production plans reflect imminent failures.

**Acceptance Scenarios**:

1. **Given** CNC-04 RUL <48h telemetry event, **When** ingested, **Then** `cap-svc` adds maintenance block and re-solves affected MOs to alternate WCs.
2. **Given** no alternate WC, **When** block applied, **Then** feasibility queue shows capacity constraint with predicted failure window.

**Maps to**: FR-I-05, UC-04 (partial)

---

#### User Story V6-7 — MDR Auto-Correction Draft (Priority: P2)

As an **engineering manager**, I need the Edge/quality module to draft **routing standard time updates** when actual cycle times deviate >15% from ERP, requiring one-click approve to Odoo.

**Acceptance Scenarios**:

1. **Given** 15% cycle time deviation on WC, **When** MDR auto-correction runs, **Then** draft routing update appears in connector queue with before/after times.
2. **Given** planner rejects draft, **When** rejected, **Then** MDR score unchanged and audit log records decision.

**Maps to**: UC-04 MDR Auto-Correction (Phase 3 ENP roadmap — pilot in V6-R4)

**Phase V6-R4 Exit Gate**: End-to-end telemetry → block → reschedule on demo; ≥1 routing draft generated from seeded deviation.

---

### Phase V6-R5 — Cost of Chaos & Generative War Room (Weeks 15–18)

#### User Story V6-8 — Cost of Chaos Dashboard (Priority: P0)

As a **CFO**, I need a Pareto dashboard translating delays, breakdowns, and manual overrides into **$ activity-based drain**, so I can quantify firefighting cost weekly.

**Acceptance Scenarios**:

1. **Given** delay events and override audit entries, **When** CFO opens Cost of Chaos, **Then** top categories show $ impact (idle time, rework, expedite).
2. **Given** supplier delay disruption, **When** aggregated, **Then** line item links to War Room impacted MO list.

**Maps to**: FR-V-02

---

#### User Story V6-9 — Generative AI War Room Recovery Plan (Priority: P1)

As a **VP Supply Chain**, when a massive disruption occurs, I need AI to **auto-aggregate impacted MOs** and present a **ranked, costed recovery plan** (not just raw scenarios).

**Acceptance Scenarios**:

1. **Given** Tier-1 supplier delay event, **When** War Room opens within 60s, **Then** top 3 recovery options show business score ($), delivery impact, and activity cost.
2. **Given** Copilot tier available, **When** planner asks for recovery narrative, **Then** response cites scenario IDs and financial lines (no silent rule fallback when routing enabled).

**Maps to**: FR-V-04, FR-023–025 (extends 003 partial)

**Phase V6-R5 Exit Gate**: `/cost-of-chaos` route live; War Room shows ranked recovery plan with $ columns on demo disruption.

---

### Cross-Cutting: Autonomous Safety (Priority: P0)

#### User Story V6-10 — Synchronous Safety Guardrail

**Maps to**: FR-I-06

**Acceptance**: When `feasibility_score < 85%`, ERP write-back blocked; autonomy downgrades to **Suggest** with audit event.

*(Validate against existing `fea-svc` dual-gate; extend if threshold differs today.)*

---

## Functional Requirements

### Activity-Based & Financial (V6-R1)

| ID | Requirement | Validation Rule |
|----|-------------|-----------------|
| **FR-I-01** | `dpe-svc` MUST compute **net-margin-aware priority** using revenue minus activity-based overhead/setup costs | Unit tests with known COGM; audit log on weight change |
| **FR-I-03** | `cap-svc` objective MUST penalize overtime, setup churn, expedite activity costs alongside tardiness | A/B solve shows lower activity cost when feasible; metadata exposes cost breakdown |
| **FR-I-06** | If `feasibility_score < 85%`, block ERP write-back; downgrade autonomy to Suggest | Integration test on approve + connector queue |

### Attribute-Based & Tariff (V6-R2)

| ID | Requirement | Validation Rule |
|----|-------------|-----------------|
| **FR-I-02** | `mat-svc` MUST support material **attributes** (origin, tariff code, carbon) and pATP **Total Landed Cost** | pATP response fields; migration for `cdm_material_attributes` |
| **FR-I-04** | Tariff shock simulator MUST apply region/% tariff and list MOs below margin threshold | API + UI; optional substitute draft to connector |

### Predictive Maintenance (V6-R4)

| ID | Requirement | Validation Rule |
|----|-------------|-----------------|
| **FR-I-05** | Ingest IoT RUL; inject maintenance blocks **≥48h** before predicted failure; re-sequence MOs | Event → cap-svc block → solve; demo CNC scenario |

### Visual & Financial UX (V6-R3, V6-R5)

| ID | Requirement | Validation Rule |
|----|-------------|-----------------|
| **FR-V-01** | Visual CPM: drag-drop Gantt, critical path highlight, cascade **p95 <2s** | k6 or Playwright timing on demo tenant |
| **FR-V-02** | Cost of Chaos dashboard: Pareto $ by delay/breakdown/override | CFO role read; ties to audit + delay APIs |
| **FR-V-03** | Bi-directional Excel: import tariff matrix + activity cost drivers; export Gantt/MS Project XML | Extends migration 022 pattern |
| **FR-V-04** | Generative War Room: auto workspace, aggregated MOs, **top 3 costed recovery plans** | Extends 003 aggregate + res-svc |

### CDM Extensions (V6-R2 / V6-R4)

| Entity | Purpose |
|--------|---------|
| `cdm_material_attributes` | JSONB: origin, tariff_code, carbon_intensity |
| `cdm_landed_cost_profiles` | Supplier/region tariff linkage |
| `cdm_activity_cost_drivers` | Setup mins, overtime rates, expedite freight |
| `cdm_machine_health_telemetry` | IoT RUL, vibration, last_seen |

All new tenant-scoped tables: **RLS in same migration** (Constitution I).

### Cross-Cutting (all phases)

| ID | Requirement |
|----|-------------|
| **FR-X-01** | Every V6 behavior change includes pytest and/or Vitest coverage |
| **FR-X-02** | State-changing V6 endpoints enforce RBAC (planner/admin/CFO read scopes) |
| **FR-X-03** | New Kafka events (tariff shock, maintenance block, chaos metric) use Avro + idempotent consumers |

---

## Success Criteria

| ID | Criterion | Target |
|----|-----------|--------|
| **SC-V6-01** | Activity-based scheduling reduces seeded overtime cost vs. time-only baseline | ≥8% on demo tenant |
| **SC-V6-02** | Tariff shock identifies MOs below margin threshold | 100% of seeded affected MOs |
| **SC-V6-03** | Visual CPM drag cascade latency | p95 **<2s** (≤20 MO demo) |
| **SC-V6-04** | Predictive maintenance block → reschedule | ≤60s end-to-end on demo |
| **SC-V6-05** | Cost of Chaos dashboard categories populated | ≥3 categories with non-zero $ |
| **SC-V6-06** | War Room recovery plan ranked by business score ($) | Top 3 scenarios with $ columns |
| **SC-V6-07** | Deployment readiness (IPE V6.0) | **≥96/100** with ≤3 residual risks documented |
| **SC-V6-08** | Demo script extended | ≥20/20 checkpoints including tariff + chaos |

---

## Gap Traceability — V6.0 Blueprint → This Feature

| V6.0 Blueprint item | 003 status | 004 phase |
|---------------------|------------|-----------|
| FR-I-01 Activity-Based Prioritization | Partial (priority_score) | V6-R1 |
| FR-I-02 Attribute-Based / Landed Cost | Not implemented | V6-R2 |
| FR-I-03 Activity-Based Financial Scheduling | Partial (cost-optimized, overtime) | V6-R1 |
| FR-I-04 Tariff Shock Simulator | Not implemented | V6-R2 |
| FR-I-05 Predictive Maintenance Scheduling | Partial (iot_health degrade) | V6-R4 |
| FR-I-06 Safety Guardrail 85% | Partial (dual-gate) | V6-R1 verify/extend |
| FR-V-01 Visual CPM | Not implemented | V6-R3 |
| FR-V-02 Cost of Chaos | Not implemented | V6-R5 |
| FR-V-03 Excel tariff/activity import | Partial (project plan upload) | V6-R2/R5 |
| FR-V-04 Generative War Room | Partial (003 aggregate) | V6-R5 |
| UC-03 Tariff BOM substitution | Not implemented | V6-R2 |
| UC-04 MDR Auto-Correction | Not implemented | V6-R4 |
| Phoenix FR-C-* | N/A (Engine A) | Out of scope |

---

## Out of Scope (004)

- **Project Phoenix** full commerce stack (Next.js ISR, Stripe, OMS, 3PL circuit breaker)
- **M2M Micro-Negotiation** edge mesh (ENP Phase 4)
- **Multi-site network optimization** at enterprise scale (existing network-svc stays demo-grade)
- **Gurobi/CPLEX** production adapters (OR-Tools remains default)
- **Autonomous BOM substitution without human approve** (draft + approve only)
- **Process manufacturing / pharma GxP**
- Re-building 003 closed-loop, MDR gate, or tiered LLM baseline

---

## Assumptions

- Development continues in `ipe/` monorepo; `visual-cpm-svc` MAY start as `cap-svc` module before service split.
- Odoo remains primary demo ERP; tariff/substitution actions use existing connector HMAC pattern.
- Activity cost rates sourced from ERP GL/overhead tables OR seeded demo matrix until GL integration.
- Tariff matrices maintained via Admin UI or Excel import (not live geopolitical API required for MVP).
- IoT telemetry for demo uses synthetic events via `cap-svc/iot` or quality-svc seed — production uses customer MQTT/OPC-UA adapter later.
- ENP pricing/ROI tables are **GTM documentation** only; Stripe billing remains out of scope.
- 003 `clarify.md` deferrals (Twin promote, live SAP/D365) remain unless explicitly pulled into a V6 phase.

---

## Dependencies

| Dependency | Reason |
|------------|--------|
| `003-autonomous-planning-v5` @ v1.0.0 | Closed-loop, MDR, planner UX baseline |
| `002-release-stabilization-gates` | CI, docker, auth, demo scripts |
| `dpe-svc/financial.py` | COGM/margin inputs for ABP |
| `cap-svc` cost-optimized + `scheduler_cost.py` | Extend for FR-I-03 |
| `mat-svc` pATP | Extend for landed cost |
| Constitution I–VI | RLS, RBAC, tests, events, observability |

---

## Phased Delivery Summary

| Phase | Duration | Focus | Exit Gate |
|-------|----------|-------|-----------|
| **V6-R1** | Wks 1–4 | ABP priority + activity-cost objective + FR-I-06 | Margin/cost-aware schedule demo |
| **V6-R2** | Wks 5–8 | Attributes, landed cost, tariff shock | Tariff what-if + substitute draft |
| **V6-R3** | Wks 9–11 | Visual CPM drag-drop | <2s cascade on Gantt |
| **V6-R4** | Wks 12–14 | Predictive maint + MDR auto-correction pilot | Telemetry → block → draft routing |
| **V6-R5** | Wks 15–18 | Cost of Chaos + Generative War Room | CFO dashboard + ranked recovery |

**Estimated effort**: 18 weeks (aligns with ENP Blueprint Phase 2–3 focus for IPE).

**Next command**: Tag `v6.0.0` (T055) after `run-full-demo.ps1` 20/20. Progress: [implementation-tracker.md](./implementation-tracker.md) **54/55**.

---

## Constitution Alignment

- **Principle I**: All CDM extensions enable RLS in migration.
- **Principle II**: CFO read-only on Cost of Chaos; planner-only on CPM drag promote.
- **Principle III**: Each FR-V6-* requires tests before merge.
- **Principle IV**: Tariff/maintenance events use Avro; consumers idempotent.
- **Principle VI**: `visual-cpm-svc` (if split) exposes `/health`, `/metrics`.

Violations MUST be logged in `specs/004-ai-first-v6/analysis.md`, not silently waived.
