# Feature Specification: Autonomous Production Planning — IPE V5.0 Convergence

**Feature Branch**: `003-autonomous-planning-v5`

**Created**: 2026-06-22

**Status**: In Progress — R1/R2 core implemented 2026-06-22

**Input**: IPE Platform Status Report (2026-06-22), Expert Assessment vs. V5.0 PRD Gold Standard, AI Auto Scheduling Module proposal, and `IMPLEMENTATION-TASKS.md` Phase R1–R4 roadmap.

---

## Executive Summary

IPE has successfully built a **world-class AI scheduling demo**: OR-Tools CP-SAT optimization, Kafka-driven feasibility pipeline, 15/15 demo checkpoints, and a functional planner UI for Control Tower, Resolution, Schedule, and Copilot. The backend engine is exceptionally strong.

However, the platform is trapped in the **80/20 gap**. It is not yet an **Autonomous Production Planning System** capable of enterprise sales against Kinaxis, o9, or SAP IBP. Critical gaps block production use:

- Solver output is **not persisted** to the CDM; approved work is lost on refresh.
- Demand **priority scoring is not wired** into the CP-SAT objective (feasibility score used instead).
- **Explainability, planner controls, and what-if UI** exist in APIs but not in the Schedule experience.
- **Master Data Readiness (MDR)** engine exists in backend but has no dashboard and does not gate scheduling.
- **Copilot** silently degrades to rule-based responses instead of tiered LLM failover with explicit admin signaling.
- **Financial impact** of resolution choices is not visible to planners or CFO personas.

This feature defines the **minimum product work** to transform IPE from demo-ready (~78%) to **V5.0 enterprise-ready (~100%)** across four remediation phases (R1–R4), aligned with Sprints 11–16 strategy.

**Baseline (already delivered — not in scope to re-build):**

- OR-Tools CP-SAT scheduler (basic, cost, green, network variants)
- Event mesh (dpe → mat → fea → cap pipeline)
- Control Tower, Resolution Center, Schedule Gantt, Copilot, Shop Floor, Executive, War Room
- Project plan Excel upload with version history (migration 022)
- MDR scoring backend (`dpe-svc/mdr_engine.py`), financial projection API (`dpe-svc/financial.py`)
- Tiered LLM router skeleton (`nlp-svc/llm_client.py`, `tiered_router.py`)
- Release stabilization feature (`002-release-stabilization-gates`) — Gate 1–3 passed 2026-06-22

**Out of scope (explicit deferrals):**

- Stripe billing, mobile app (React Native), federated learning production rollout
- Autonomous schedule auto-release without human approval (V5.0 Phase 4 governance — future feature)
- Full SAP/D365 **production** connectors (sandbox validation only in R4)
- WCAG 2.1 AA audit, visual regression testing suite

---

## Problem Statement

An AI scheduler that cannot **persist its output**, **explain its decisions**, or **verify input data quality** is a demo toy—not an enterprise product. Planners cannot trust or adopt AI recommendations they cannot inspect, adjust, or recover after approval. CFOs cannot justify ROI without financial translation. ERP admins cannot safely enable AI on dirty master data.

**Target buyer outcomes after this feature:**

| Outcome | Metric |
|---------|--------|
| Closed-loop planning | Approved schedule visible in CDM, Shop Floor, and ERP within 60s |
| Planner trust | ≥80% of demo users report understanding *why* a slot was chosen (XAI panel) |
| Data safety | AI scheduling blocked when MDR composite score < 70% |
| Disruption response | War Room auto-aggregates impacted MOs and surfaces top 3 mitigations |
| Financial clarity | Resolution choices show dollar impact (expedite cost vs. lost revenue) |

---

## User Scenarios & Testing *(mandatory)*

Stories are grouped by remediation phase. Each story is independently testable and maps to an exit gate.

---

### Phase R1 — Stabilize & Close the Loop (Weeks 1–3)

#### User Story R1-1 — Planner Approves a Schedule That Persists (Priority: P0)

As a **production planner**, I need to generate an AI schedule, approve selected manufacturing orders, and see planned start/end times **persist in the system** after page refresh, so my planning work is not lost and Shop Floor operators see the same plan.

**Why this priority**: The #1 critical gap vs. V5.0 PRD. Without CDM persistence, the platform cannot be used in production.

**Independent Test**: Generate schedule → approve 2 MOs → refresh browser → Gantt and Shop Floor still show approved times → database `cdm_work_order` rows updated with `ai_start`/`ai_end` and incremented `version`.

**Acceptance Scenarios**:

1. **Given** a solver-generated schedule on the Schedule page, **When** the planner approves one or more MOs, **Then** `cdm_work_order` records are updated with new planned times using optimistic locking on the `version` field.
2. **Given** a concurrent edit (version mismatch), **When** approve is attempted, **Then** the planner receives a conflict error and is prompted to refresh before re-approving.
3. **Given** a successful approve, **When** the Kafka consumer processes `ipe.schedule.approved`, **Then** the Odoo connector receives an HMAC-signed POST with the approved schedule payload.
4. **Given** Odoo is temporarily unavailable, **When** approve succeeds in CDM, **Then** the outbox event remains in Kafka/DLQ and retries until ERP sync completes—no silent data loss.

---

#### User Story R1-2 — High-Priority Orders Win Schedule Slots (Priority: P0)

As a **supply chain manager**, I need the AI scheduler to sequence jobs according to **business priority** (customer tier, margin, urgency, penalty), not just feasibility score, so Tier-1 customer orders are protected even when capacity is tight.

**Why this priority**: V5.0 mandates dynamic order scoring in the solver objective. Current wiring uses `feasibility_score`, making the scheduler "dumb" to business intent.

**Independent Test**: Two MOs competing for the same work center with identical due dates but different `dpe-svc` priority scores → higher-priority MO receives earlier slot in solver output.

**Acceptance Scenarios**:

1. **Given** MO-A with priority score 92 and MO-B with score 65 sharing a bottleneck WC, **When** schedule is generated, **Then** MO-A operations start before MO-B operations (all else equal).
2. **Given** tenant-configurable priority weights in Admin, **When** weights change and schedule regenerates, **Then** operation ordering reflects the new weights within the same solve run.
3. **Given** the CP-SAT objective, **When** inspecting solver metadata, **Then** tardiness penalty for each MO is multiplied by its normalized priority weight from `dpe-svc`.

---

#### User Story R1-3 — Release Engineering Validates a Trustworthy Baseline (Priority: P1)

As a **technical lead**, I need documentation, tests, and auth health aligned with reality, so Gate 1 stabilization from `002-release-stabilization-gates` is not undermined by new feature drift.

**Why this priority**: Expert assessment and status report both cite doc inconsistency (~29 conflicts) and ~37% API test coverage.

**Independent Test**: Doc sync complete; API test coverage ≥55% on critical endpoints; Keycloak container healthy locally (live IdP test may remain BLOCKED).

**Acceptance Scenarios**:

1. **Given** `IMPLEMENTATION-TASKS.md` Phases 1–2, **When** executed, **Then** cross-artifact CRITICAL/HIGH conflicts are zero and API test count increases per plan.
2. **Given** Keycloak in local Docker stack, **When** health is checked, **Then** container reports healthy (SAML/SCIM live sandbox remains BLOCKED until credentials provided).
3. **Given** cap-svc priority wiring and schedule persistence merged, **When** full demo script runs, **Then** ≥15/15 checkpoints pass including persist-after-approve.

**Phase R1 Exit Gate**: A planner generates a schedule, approves it, sees it persist in CDM, and sees it push to Odoo (or outbox queue if Odoo down).

---

### Phase R2 — Activate the AI Brain & Planner UX (Weeks 4–6)

#### User Story R2-1 — Planner Controls Optimization Strategy (Priority: P0)

As a **production planner**, I need sliders and strategy presets on the Schedule page (delivery focus, inventory focus, revenue focus, efficiency, overtime allowance, capacity buffer), so I can regenerate schedules aligned with today's business priorities without calling APIs manually.

**Why this priority**: V5.0 §12 planner refinement mechanism. Backend `alpha`/`beta` exist; UI does not.

**Independent Test**: Move "Delivery Focus" slider to High → regenerate → high-priority/high-urgency MOs show reduced tardiness vs. baseline run.

**Acceptance Scenarios**:

1. **Given** the Schedule Control Panel, **When** planner selects strategy "Earliest Due Date" and clicks Regenerate, **Then** the solver runs with EDD-weighted objective and Gantt updates within 30s (or heuristic fallback—see R2-4).
2. **Given** cost/green trade-off sliders, **When** alpha is set to 0.8 (cost focus), **Then** `/capacity/cost-optimized` path is invoked with visible cost delta in response metadata.
3. **Given** capacity buffer set to 15%, **When** schedule generates, **Then** work center utilization does not exceed 85% of nominal capacity in the plan.
4. **Given** overtime disallowed, **When** schedule generates, **Then** no operation is placed outside defined shift windows.

---

#### User Story R2-2 — Planner Understands Why AI Chose Each Slot (Priority: P0)

As a **production planner**, I need an explainability panel on the Schedule page showing constraints, assumptions, confidence, and contributing factors for the current schedule, so I trust AI recommendations enough to approve them.

**Why this priority**: V5.0 mandates `xai_explanation` on every recommendation. API returns it; UI does not display it.

**Independent Test**: Select an MO on Gantt → XAI panel shows ≥3 contributing factors (e.g., "Customer Priority = High", "Materials Available", "No Setup Change Required") matching API payload.

**Acceptance Scenarios**:

1. **Given** a generated schedule with `xai_explanation` in API response, **When** planner selects an operation bar, **Then** the XAI panel renders constraints, assumptions, confidence score, and contributing factors.
2. **Given** a blocked MO (material shortage), **When** viewed in validation results, **Then** explanation includes explicit reason and expected resolution date.
3. **Given** a schedule regenerated after slider change, **When** comparing explanations, **Then** contributing factor weights reflect the selected strategy.

---

#### User Story R2-3 — Copilot Uses Tiered LLM With Explicit Failover (Priority: P1)

As a **plant manager using Copilot**, I need natural-language answers from a configured LLM tier (SaaS Anthropic or on-prem Ollama/Llama-3), with PII stripped, so I get intelligent responses—not silent rule-based degradation.

**Why this priority**: V5.0 Tiered LLM Deployment mandate. Current behavior falls back to formatter without clear admin signal.

**Independent Test**: With Anthropic key unset but Ollama running in Docker → Copilot returns LLM-generated answer tagged `tier=local`. With both unavailable → HTTP 503 with admin-actionable message (not blank bubble or dumb rules).

**Acceptance Scenarios**:

1. **Given** Tier 1 Anthropic API key configured, **When** planner asks "What is current FG stock?", **Then** response is LLM-generated with PII stripped and tier logged.
2. **Given** Tier 1 unavailable and Tier 2 Ollama healthy, **When** query is sent, **Then** router automatically uses local model without user-visible error.
3. **Given** both Tier 1 and Tier 2 unavailable, **When** query is sent, **Then** API returns 503 with message: "LLM Inference Unavailable. Configure Tier 1 or Tier 2 in Admin."—Admin UI shows configuration status.
4. **Given** any tier, **When** response is generated, **Then** no raw PII (emails, phone numbers) appears in logs or response payload.

---

#### User Story R2-4 — Solver Degrades Gracefully on Timeout (Priority: P1)

As a **planner running a large plant model**, I need the scheduler to produce a **rule-based heuristic schedule** when OR-Tools exceeds the 30s timeout, flagged for manual review, so I always receive a workable proposal—not an empty Gantt.

**Why this priority**: V5.0 and TASK-C-002 spec require timeout→heuristic fallback; only skill-relaxation exists today.

**Independent Test**: Trigger 1000+ operation solve with 5s test timeout → heuristic schedule returned with `solver_status=heuristic_fallback` and warning banner in UI.

**Acceptance Scenarios**:

1. **Given** CP-SAT times out at configured limit, **When** solve completes, **Then** ISolver returns heuristic assignments covering ≥90% of MOs.
2. **Given** heuristic fallback used, **When** schedule displays, **Then** UI shows amber banner: "Heuristic schedule—manual review recommended."
3. **Given** heuristic schedule, **When** planner clicks "Re-run with full optimizer", **Then** system retries CP-SAT with extended timeout or reduced horizon option.

**Phase R2 Exit Gate**: Planners interact with AI via sliders, understand decisions via XAI panel, receive Copilot LLM responses (or explicit 503), and never see empty Gantt on timeout.

---

### Phase R3 — Enterprise Governance & V5.0 Differentiators (Weeks 7–9)

#### User Story R3-1 — ERP Admin Passes Master Data Readiness Gate (Priority: P0)

As an **ERP administrator**, I need a Master Data Readiness (MDR) dashboard that scores BOM completeness, routing accuracy, and inventory record quality **before** AI scheduling is enabled, so garbage data cannot silently produce garbage schedules.

**Why this priority**: V5.0 #1 competitive differentiator. MDR backend exists; dashboard and hard-gate do not.

**Independent Test**: Set tenant BOM completeness to 50% → MDR dashboard shows red score → Schedule page blocks "Generate AI Schedule" → remediation checklist lists missing BOMs.

**Acceptance Scenarios**:

1. **Given** MDR composite score ≥ 70%, **When** planner opens Schedule page, **Then** AI scheduling is enabled and score badge shows green.
2. **Given** MDR composite score < 70%, **When** planner attempts to generate schedule, **Then** system hard-blocks with remediation checklist (missing BOMs, routing gaps, inventory anomalies).
3. **Given** MDR recalculation after ERP sync, **When** score crosses 70%, **Then** AI scheduling unlocks without admin manual toggle.
4. **Given** Shadow Mode tenant, **When** onboarding completes, **Then** MDR dashboard is the mandatory step before autonomy progression.

---

#### User Story R3-2 — Supply Chain VP Runs What-If Without Touching Live Plan (Priority: P0)

As a **supply chain VP**, I need a Digital Twin sandbox where I clone the current schedule, apply a disruption (machine down, supplier delay, expedite request), and instantly see **delta in OTD and cost** vs. baseline, so I make risk decisions without corrupting live CDM data.

**Why this priority**: V5.0 Digital Twin mandate. `/simulate` and scenario APIs exist; no Schedule UI.

**Independent Test**: Clone schedule → apply "CNC-04 down 48h" → view side-by-side Gantt + OTD delta + cost delta → live CDM unchanged.

**Acceptance Scenarios**:

1. **Given** an active schedule, **When** planner clicks "Clone to Sandbox", **Then** a versioned scenario snapshot is created without modifying live work orders.
2. **Given** a sandbox scenario, **When** disruption "Machine M-102 breakdown 48h" is applied, **Then** re-solve completes and shows impacted MO count, OTD % change, and estimated cost change.
3. **Given** sandbox results acceptable, **When** planner clicks "Promote to Live", **Then** approval workflow applies changes via R1 outbox pattern.
4. **Given** sandbox discarded, **When** planner closes sandbox, **Then** live schedule is identical to pre-clone state.

---

#### User Story R3-3 — CFO Sees Financial Impact of Resolution Choices (Priority: P1)

As a **CFO or plant controller**, I need the Resolution Center to show **dollar impact** when comparing mitigation options (expedite material vs. delay order vs. overtime), so planning decisions connect to COGM, expedite freight, and lost revenue.

**Why this priority**: V5.0 Financial Translation Engine. Backend COGM APIs exist; Resolution UI shows business scores only.

**Independent Test**: Open resolution scenario for material shortage → Option A shows "+$4,500 expedite freight" vs. Option B shows "-$12,000 lost revenue" sourced from `dpe-svc/financial/project`.

**Acceptance Scenarios**:

1. **Given** a resolution scenario with ≥2 options, **When** displayed in Resolution Center, **Then** each option shows COGM impact, expedite cost, and revenue-at-risk columns.
2. **Given** planner selects an option, **When** approval is recorded, **Then** financial projection is persisted to `cdm_financial_projection` for audit.
3. **Given** Executive dashboard, **When** viewing period summary, **Then** aggregate cost-of-poor-planning metric is available.

---

#### User Story R3-4 — Compliance Officer Accesses Governance Modules (Priority: P2)

As a **compliance officer**, I need Quality, Sustainability, and Compliance dashboards accessible from the main navigation, so governance modules are discoverable during enterprise security review.

**Independent Test**: Main nav includes Quality, Sustainability, Compliance routes → each page loads with tenant-scoped data.

**Acceptance Scenarios**:

1. **Given** authenticated admin/planner role, **When** main navigation renders, **Then** Quality, Sustainability, and Compliance links are visible and routed.
2. **Given** Compliance dashboard, **When** loaded, **Then** SOC2 evidence summary displays without 404.

**Phase R3 Exit Gate**: Platform passes enterprise data-governance review—MDR gates AI, Digital Twin enables VP decisions, Resolution shows financial impact, compliance modules are navigable.

---

### Phase R4 — Production Hardening & Multi-ERP (Weeks 10–12)

#### User Story R4-1 — SRE Validates Production Resilience (Priority: P1)

As an **SRE**, I need Chaos Mesh experiments executed in staging (Kafka broker kill, Postgres failover) with documented recovery times, so we certify v1.0.0 production release with evidence.

**Acceptance Scenarios**:

1. **Given** staging cluster with Chaos Mesh, **When** Postgres primary is killed, **Then** failover completes in <15s and schedule outbox resumes without duplicate ERP posts.
2. **Given** Kafka broker killed, **When** consumers reconnect, **Then** rebalancing completes in <30s with no lost `ipe.schedule.approved` events.

---

#### User Story R4-2 — Integration Engineer Validates Tier-1 ERP Sandboxes (Priority: P1)

As an **integration engineer**, I need SAP S/4HANA and D365 BC connectors validated against live sandbox environments, so enterprise sales can cite multi-ERP readiness.

**Acceptance Scenarios**:

1. **Given** SAP sandbox credentials, **When** connector sync runs, **Then** MOs and BOMs appear in CDM with tenant isolation verified.
2. **Given** D365 sandbox credentials, **When** schedule approve fires, **Then** planned dates appear in D365 test environment via HMAC-signed API.

---

#### User Story R4-3 — ML Ops Validates Drift Pipeline (Priority: P2)

As a **data scientist**, I need Airflow in the default local stack running drift detection DAGs, so MLOps claims are verifiable in demo and staging.

**Acceptance Scenarios**:

1. **Given** local Docker stack with Airflow scheduler+worker, **When** `ipe_hourly_schedule_pipeline` triggers, **Then** DAG completes without error.
2. **Given** injected NLP accuracy drift, **When** drift DAG runs, **Then** alert is emitted to War Room feed.

**Phase R4 Exit Gate**: System certified for v1.0.0 production release—Chaos evidence attached, multi-ERP sandbox validated, k6 200 VU p95 <5s SLO confirmed.

---

### Edge Cases

- **Optimistic locking conflict**: Two planners approve different versions of the same MO simultaneously → second approver gets 409 with refresh prompt; no partial ERP sync.
- **MDR score flapping around 70%**: Hysteresis band (e.g., unlock at 72%, block at 68%) prevents UI thrashing.
- **Heuristic + full optimizer disagree**: UI shows both with diff summary; planner chooses which to promote.
- **Digital Twin promote while live schedule changed**: Promote requires re-validation against current CDM state.
- **LLM PII leak attempt**: Prompt injection with customer email → stripped before any tier; audit log records redaction count.
- **Odoo down during approve**: CDM is source of truth; ERP sync is eventually consistent via outbox—planner sees "ERP sync pending" badge.
- **Keycloak sandbox still unavailable in R4**: SAML/SCIM remains BLOCKED; spec does not claim enterprise SSO is production-certified until VERIFY gate passes.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Closed-Loop Execution (R1)

- **FR-001**: System MUST persist approved schedule times to `cdm_work_order` with `ai_start`, `ai_end`, and optimistic locking via `version`.
- **FR-002**: System MUST publish `ipe.schedule.approved` (or equivalent) to Kafka on successful CDM write.
- **FR-003**: ERP connector MUST consume approval events and POST HMAC-signed payloads to configured ERP endpoint.
- **FR-004**: System MUST implement transactional outbox pattern—ERP failure MUST NOT roll back CDM approval; event MUST retry from DLQ.

#### Priority & Optimization (R1–R2)

- **FR-005**: System MUST map `dpe-svc` priority score to CP-SAT tardiness penalty weight: `Minimize(Σ tardiness[mo] × priority_weight[mo])`.
- **FR-006**: System MUST NOT use `feasibility_score` as the sole scheduler priority input when `dpe-svc` priority is available.
- **FR-007**: Schedule page MUST expose strategy presets: EDD, Throughput, Revenue, Inventory, Hybrid (maps to existing solver endpoints).
- **FR-008**: Schedule page MUST expose planner sliders: delivery focus, inventory focus, revenue focus, efficiency focus, overtime allowance, capacity buffer (5–20%).
- **FR-009**: ISolver MUST implement heuristic fallback on CP-SAT timeout, flag result as `heuristic_fallback`, and MUST NOT return empty assignments for solvable inputs.

#### Explainability & Copilot (R2)

- **FR-010**: Schedule page MUST render `xai_explanation` (constraints, assumptions, confidence, contributing factors) for selected operations.
- **FR-011**: System MUST provide pre-solve validation API returning per-MO status: Valid, Warning, or Blocked with human-readable reasons.
- **FR-012**: Copilot MUST implement Tier 1 (Anthropic SaaS) → Tier 2 (Ollama/Llama-3 local) → Tier 3 (503 error) routing with PII stripping on all tiers.
- **FR-013**: System MUST NOT silently degrade Copilot to rule-based formatter when LLM tiers are misconfigured—Admin UI MUST show tier health.

#### MDR & Governance (R3)

- **FR-014**: System MUST expose MDR dashboard scoring BOM completeness, routing accuracy, and inventory record quality with composite score 0–100%.
- **FR-015**: System MUST hard-block AI schedule generation when MDR composite score < 70% and generate remediation checklist.
- **FR-016**: MDR recalculation MUST run after ERP sync and before autonomy mode progression.
- **FR-017**: Quality, Sustainability, and Compliance pages MUST be registered in main application router and navigation.

#### Digital Twin & Financial (R3)

- **FR-018**: System MUST support clone-current-schedule to sandbox scenario without modifying live CDM.
- **FR-019**: Sandbox MUST display delta metrics: impacted MO count, OTD % change, estimated cost change vs. baseline.
- **FR-020**: Sandbox promotion MUST require explicit planner approval via R1 outbox workflow.
- **FR-021**: Resolution Center MUST display financial impact (COGM, expedite cost, revenue-at-risk) per scenario option using financial projection service.
- **FR-022**: Approved resolution choices MUST persist financial projection records for audit.

#### War Room Automation (R3)

- **FR-023**: When Tier-1 supplier delay event is ingested, War Room MUST auto-aggregate impacted MOs within 60 seconds.
- **FR-024**: War Room MUST surface top 3 mitigation scenarios from `res-svc` for the disruption event.
- **FR-025**: War Room MUST support optional task assignment notification (Slack/Teams webhook configurable)—delivery MAY be stubbed in R3 with audit log fallback.

#### Production Hardening (R4)

- **FR-026**: Chaos Mesh experiments MUST be executed in staging with attached recovery time evidence before v1.0.0 tag.
- **FR-027**: SAP and D365 connectors MUST pass sandbox integration tests documented in release evidence.
- **FR-028**: Airflow scheduler+worker MUST be included in default local Docker stack.
- **FR-029**: k6 200 VU load test MUST pass p95 < 5s and error rate < 1% before production promotion.

#### Cross-Cutting

- **FR-030**: Every behavioral change MUST include automated tests per Constitution Principle III.
- **FR-031**: All new tables with `tenant_id` MUST enable RLS in the same migration (Constitution Principle I).
- **FR-032**: All state-changing endpoints MUST enforce RBAC (Constitution Principle II).

### Key Entities

- **Schedule Version**: Immutable snapshot of solver output with metadata (strategy, solver status, xai payload, created_by, created_at).
- **Schedule Approval**: Planner action linking MO IDs to persisted work order times with version increment and outbox event.
- **MDR Assessment**: Composite score with dimension breakdown (BOM, routing, inventory) and remediation tasks.
- **Digital Twin Scenario**: Sandbox clone with disruption overlay, delta metrics, and promotion workflow state.
- **Financial Impact Line**: COGM, expedite cost, revenue-at-risk attached to resolution scenario option.
- **LLM Tier Status**: Health and configuration state for Tier 1/2/3 per tenant.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (R1)**: Planner approve → CDM persist → ERP outbox completes in **≤60 seconds** under normal conditions (p95).
- **SC-002 (R1)**: Priority wiring verified: high-priority MO starts before low-priority MO on shared bottleneck in **100%** of controlled test cases (≥10 scenarios).
- **SC-003 (R1)**: Full demo script passes **≥16/16** checkpoints (existing 15 + persist-after-approve).
- **SC-004 (R2)**: Schedule Control Panel strategies regenerate Gantt in **≤30 seconds** for demo tenant (≤5 seconds for small factory per AI spec §17).
- **SC-005 (R2)**: XAI panel displays **≥3 contributing factors** for selected operations in **100%** of demo schedule runs.
- **SC-006 (R2)**: Copilot Tier 2 (Ollama) responds successfully when Tier 1 disabled; Tier 3 returns explicit 503 (zero silent rule fallback).
- **SC-007 (R2)**: Heuristic fallback produces assignments for **≥90%** of MOs on timeout test suite.
- **SC-008 (R3)**: MDR gate blocks scheduling at <70% and unlocks at ≥70% in **100%** of test tenants.
- **SC-009 (R3)**: Digital Twin clone→disrupt→delta workflow completes in **≤2 minutes** for demo tenant without live CDM mutation.
- **SC-010 (R3)**: Resolution options show financial columns populated for **100%** of demo resolution scenarios.
- **SC-011 (R4)**: Chaos experiments meet recovery SLOs (Postgres <15s, Kafka <30s) with signed evidence.
- **SC-012 (R4)**: k6 200 VU: p95 **<5s**, error rate **<1%**, checks **>95%**.
- **SC-013 (Overall)**: Deployment readiness score increases from **~78%** (demo) to **≥95%** (enterprise) with documented residual risks ≤3 items.

---

## Gap Traceability Matrix

Maps Expert Assessment findings to this feature's stories and requirements.

| V5.0 Gap | Severity | Addressed By |
|----------|----------|--------------|
| Schedule not persisted to CDM | 🔴 CRITICAL | R1-1, FR-001–004 |
| Priority not wired to CP-SAT | 🔴 CRITICAL | R1-2, FR-005–006 |
| MDR dashboard + gate missing | 🔴 CRITICAL | R3-1, FR-014–016 |
| XAI not on Schedule UI | 🟠 HIGH | R2-2, FR-010–011 |
| Copilot silent rule fallback | 🟠 HIGH | R2-3, FR-012–013 |
| Heuristic timeout fallback missing | 🟠 HIGH | R2-4, FR-009 |
| Digital Twin UI missing | 🟠 HIGH | R3-2, FR-018–020 |
| Financial translation in Resolution | 🟡 MEDIUM | R3-3, FR-021–022 |
| Passive War Room | 🟡 MEDIUM | FR-023–025 |
| SAP/D365 live validation | 🟡 MEDIUM | R4-2, FR-027 |
| API test coverage 37% | 🟠 HIGH | R1-3, IMPLEMENTATION-TASKS Phase 2 |

---

## Assumptions

- Work continues in the existing IPE monorepo under `ipe/`; no greenfield rewrite.
- Odoo remains the primary demo ERP; SAP/D365 validation requires customer-provided sandboxes in R4.
- Ollama/Llama-3 container CAN be added to Docker Compose for Tier 2 local inference.
- MDR composite score formula: weighted average of BOM completeness (40%), routing accuracy (35%), inventory accuracy (25%)—threshold 70% per V5.0 PRD (backend currently uses 80% BOM-only gate; this feature harmonizes to composite 70%).
- Keycloak live IdP (Azure AD/Okta) MAY remain BLOCKED through R4 if sandbox credentials unavailable—documented as residual risk, not a false COMPLETE claim.
- Progressive autonomy (Shadow → Suggest → Autonomous) continues; this feature does NOT enable autonomous auto-release.
- `002-release-stabilization-gates` Gate 1–3 evidence remains valid baseline; this feature extends product capability, not re-stabilization.

---

## Dependencies

- `002-release-stabilization-gates` — green CI, demo scripts, Gate evidence.
- `IMPLEMENTATION-TASKS.md` Phases 1–2 — doc sync and API test coverage.
- `000-project-completion` / V5.0 Master Blueprint — authoritative PRD for MDR, financial, tiered LLM, outbox patterns.
- `.specify/memory/constitution.md` — RLS, RBAC, test-backed changes.
- External: Azure AD/Okta sandbox (R1/R4), SAP/D365 sandbox (R4), Slack/Teams webhook (R3 optional).

---

## Constitution Alignment Notes

This feature MUST NOT weaken:

- **Principle I**: RLS on all new schedule version, outbox, and MDR tables.
- **Principle II**: Approve, promote, and sandbox endpoints require planner/admin RBAC.
- **Principle III**: Every FR above requires corresponding pytest and/or Playwright coverage before merge.
- **Principle IV**: `ipe.schedule.approved` MUST have Avro schema; consumer idempotency tested.
- **Principle VI**: New services/endpoints expose `/health`, `/ready`, `/metrics`.

Violations discovered during implementation MUST be filed as blockers in `specs/003-autonomous-planning-v5/analysis.md`, not silently waived.

---

## Phased Delivery Summary

| Phase | Duration | Focus | Exit Gate |
|-------|----------|-------|-----------|
| **R1** | Weeks 1–3 | Close the loop, priority wiring, test/doc baseline | Approve → persist → ERP outbox |
| **R2** | Weeks 4–6 | Planner UX, XAI, LLM tiers, heuristic fallback | Planners trust and control AI |
| **R3** | Weeks 7–9 | MDR, Digital Twin, Financial, War Room, nav | Enterprise governance pass |
| **R4** | Weeks 10–12 | Chaos, multi-ERP, Airflow, load cert | v1.0.0 production release |

**Total estimated effort**: 10–12 weeks (aligned with Expert Assessment R1–R4 roadmap).

**Next command**: `/speckit.plan` to generate `plan.md`, `tasks.md`, and contracts per phase.
