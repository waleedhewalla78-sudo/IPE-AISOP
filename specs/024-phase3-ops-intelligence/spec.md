# Feature Specification: Ops Phase 3 — Operations Intelligence (Blueprint 3→5 Program)

**Feature Branch**: `024-phase3-ops-intelligence`

**Created**: 2026-07-15

**Status**: Active — Speckit pipeline run 2026-07-15

**Input**: Full Speckit pipeline for IPE after Spec 023 Wave 1 ENG COMPLETE. Govern Ops Blueprint Phase 3 (7 AI agents, predictive risk, exception lifecycle, Excel onboarding) as the next coherent engineering slice; track Blueprint Phase 4 (Premium modules/agents A8–A12) and Phase 5 (Planning/Command deep build) as program backlog. Absorb concurrent Phase-agent deltas (migrations 051–059). Sources: `IPE-Phase3-Blueprint-v2.0.md`, `IPE-Phase3-Technical-Spec-v2.0.md`, `IPE-Phase4-Premium-Proposal.md`, `IPE-Phase5-Planning-Command-Deep.md`. Commercial blockers remain OPEN (do not fake).

**Prior features**: 020/021/022/023 ENG COMPLETE. Constitution **1.3.0**.

**Depends on**: Migration head ≥050 (`cdm_erp_connection`); fea/cap/mat/demand/dpe/nlp services; R1/R2 profiles. Peer agents may land 051–059 — Speckit MUST NOT recreate.

**Out of scope products**: `nexus-social/` (authoritative PRD is a separate product).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Planner sees 3/7/14-day predictive risk (Priority: P1)

As a production planner at 07:00, I open Control Tower / feasibility and see not only today's score but predicted scores at T+3, T+7, T+14 with trend (`stable` / `deteriorating` / `crisis_approaching`) and a recommended action window — without running Excel cross-checks.

**Why this priority**: Blueprint A4 predictive risk is the core "fire before it burns" value of Ops Phase 3.

**Independent Test**: Unit-test `PredictiveRiskScorer` with stubbed projections; GET `/api/v1/feasibility/predict/{mo_id}` returns 200 with horizons and RLS-scoped tenant.

**Acceptance Scenarios**:

1. **Given** an MO with gate scores, **When** predictive score runs, **Then** horizons 3/7/14 are returned with `predicted_score`, `primary_risk`, `trend`.
2. **Given** migration 057, **When** predict persists, **Then** rows land in `cdm_prediction_log` with RLS.
3. **Given** missing capacity/material projection inputs, **When** scorer runs, **Then** conservative defaults apply — never silent NaN or 500.

---

### User Story 2 — Planner gets 5-why root cause + priced options (Priority: P1)

As a planner investigating a late/at-risk MO, I see an automatic root-cause chain (up to 5 levels) stored in `cdm_root_cause_chain`, with immediate/short/long recommendations — and an exception in `cdm_agent_exception` with SLA clocks.

**Why this priority**: Exception lifecycle (Blueprint §3.4) replaces WhatsApp firefighting.

**Independent Test**: Unit-test `RootCauseAnalyzer` with synthetic gate failures; exception create/ack endpoints enforce auth + tenant.

**Acceptance Scenarios**:

1. **Given** weakest gate = material/capacity, **When** analyze runs, **Then** chain depth ≥1 and `root_cause_type` set.
2. **Given** an open exception, **When** planner acknowledges, **Then** `acknowledged_at` set and SLA timer starts.
3. **Given** SLA breach, **When** orchestrator checks, **Then** severity escalation fields/status update (no auto-close).

---

### User Story 3 — Capacity conflict resolved by auction + smart batching (Priority: P2)

As a planner facing two MOs competing for the same WC slot, I see a capacity-auction decision with priority scores (margin/penalty/due) and optional smart-batching savings vs FIFO — audited in `cdm_capacity_auction_log` / `cdm_batch_group`.

**Why this priority**: Blueprint A3 magic features; valuable but secondary to risk visibility.

**Independent Test**: Unit-test `SmartBatcher` and `CapacityAuction` with in-memory MO lists; no Docker required.

**Acceptance Scenarios**:

1. **Given** two competing MOs, **When** auction runs, **Then** winner/loser and scores are deterministic given inputs.
2. **Given** same-product sequence, **When** batcher runs, **Then** changeover minutes ≤ FIFO baseline when delivery dates maintained.

---

### User Story 4 — Excel onboarding upload with validation (Priority: P2)

As a tenant admin without live Odoo (PH1-02 OPEN), I upload the 14 Excel templates via onboarding wizard tracked in `cdm_upload_history` / `cdm_upload_error`, with stage validation and error Excel download path scaffolded.

**Why this priority**: Unlocks value when staging Odoo is unavailable; Blueprint §4.

**Independent Test**: Migration 053 applied; upload-svc health + dry validation unit test; COM honesty: live PH1-02 still OPEN.

**Acceptance Scenarios**:

1. **Given** valid Product Master sheet, **When** upload processes, **Then** history row status=`accepted`/`partial`.
2. **Given** unknown customer_code, **When** validation runs, **Then** reject row + error detail; no silent accept.
3. **Given** upload-svc not on R1 compose yet, **When** docs/status read, **Then** status shows scaffold/partial — never fake production-ready.

---

### User Story 5 — Morning brief synthesises agent chain (Priority: P3)

As a planner, Copilot/nlp morning brief section summarises demand/inventory/feasibility flags after agent orchestrator chain runs; activity written to `cdm_agent_activity_log`.

**Why this priority**: Orchestration glue; depends on US1–US2.

**Independent Test**: `AgentOrchestrator` dry-run with stubbed HTTP returns activity log payload shape.

**Acceptance Scenarios**:

1. **Given** data-change trigger, **When** chain runs, **Then** A4 always attempted; timed-out steps logged as exceptions, chain continues.
2. **Given** Kafka unset (R1), **When** chain runs, **Then** HTTP/direct path still logs activity.

---

### User Story 6 — Program tracks Phase 4/5 backlog honestly (Priority: P2)

As program owner, analyze + PRODUCT-STATUS show Ops Phase 4 (6 modules, A8–A12) and Phase 5 (Planning Cockpit/MPS/MRP/ATP) as BACKLOG; Spec 023 complete; COM OPEN unchanged.

**Why this priority**: Constitution VII/IX honesty.

**Independent Test**: Diff docs — no invented Phase 4/5 DONE, no G-R2-04 PASS, no OQ-7 filled.

**Acceptance Scenarios**:

1. **Given** Spec 024 analyze, **When** Phase map table read, **Then** Platform P3 DONE ≠ Ops P3 ACTIVE; Phase 4/5 BACKLOG.
2. **Given** concurrent Phase-agent commits, **When** Speckit implements, **Then** deltas absorbed; no duplicate CREATE for existing tables.

---

### Edge Cases

- Missing MO / wrong tenant → 404/403, not cross-tenant leak.
- Projection with zero POs/stock → stockout trajectory flagged, not crash.
- `cdm_supplier_score` already exists (041) → migration 055 ALTERs only (peer agent pattern).
- upload-svc port clash → documented in plan; do not break R1 ports.
- Peer Phase agent UI edits in `apps/web` → Speckit does not revert without cause; converge absorbs.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Schema spine migrations **051–059** present with RLS (or ALTER for 055 conflict with 041); Speckit verifies, does not recreate if peer-landed.
- **FR-002**: `PredictiveRiskScorer` in fea-svc + GET predict endpoint + tests.
- **FR-003**: `RootCauseAnalyzer` in fea-svc + persist `cdm_root_cause_chain` + tests.
- **FR-004**: Exception lifecycle APIs (create/list/ack/resolve) for `cdm_agent_exception` + SLA table.
- **FR-005**: Smart batching + capacity auction modules in cap-svc with unit tests and optional persist.
- **FR-006**: Supplier Phase 3 columns used by scoring path (mat-svc/scn) with overall_score/recommendation when available.
- **FR-007**: Demand signal fusion persistence path for `cdm_demand_signal` (demand-svc) — may be stub-wired.
- **FR-008**: upload-svc scaffold (FastAPI app, health, history write) OR documented gap if peer delivers — converge tracks residual.
- **FR-009**: `AgentOrchestrator` in dpe-svc with activity logging; degrade gracefully without Kafka.
- **FR-010**: Docs: PRODUCT-STATUS, AGENTS.md, feature.json → Spec 024 / constitution 1.3.0; COM OPEN listed.
- **FR-011**: Phase 4/5 requirements captured as backlog FR-B* (not implementable this slice unless trivial):

#### Backlog (Phase 4 — Premium)

- **FR-B401**: Modules M1–M6 Command shells (Demand/Production/Supply/Quality/Finance/Customer).
- **FR-B402**: Agents A8 Customer, A9 Procurement, A10 Quality, A11 Finance, A12 Sustainability.
- **FR-B403**: Customer portal read-only order visibility.

#### Backlog (Phase 5 — Planning Command Deep)

- **FR-B501**: Planning Cockpit decision surface (plan health, attention queue, weekly timeline).
- **FR-B502**: MPS grid weekly net requirements.
- **FR-B503**: MRP explosion + RCCP/CRP deep.
- **FR-B504**: ATP/CTP promising API + UI.
- **FR-B505**: Collaborative planning conflict detection.

### Non-Functional

- **NFR-001**: RLS on all new tenant tables (Principle I).
- **NFR-002**: Auth on all new mutating routes (Principle II).
- **NFR-003**: Predict endpoint p95 < 2s for single MO on staging-sized data (best-effort; measure later).
- **NFR-004**: Never commit secrets / `.kms_keys`.

### Key Entities

- `cdm_agent_activity_log`, `cdm_agent_exception`, `cdm_exception_sla`
- `cdm_upload_history`, `cdm_upload_error`
- `cdm_demand_signal`, `cdm_supplier_score` (extended), `cdm_root_cause_chain`
- `cdm_prediction_log`, `cdm_capacity_auction_log`, `cdm_batch_group`

---

## Success Criteria *(mandatory)*

- **SC-001**: Predictive predict endpoint + unit tests GREEN.
- **SC-002**: Root-cause analyzer unit tests GREEN.
- **SC-003**: Migrations 051–059 verified in tree with linear revisions from 050.
- **SC-004**: PRODUCT-STATUS / analyze reflect whole-project honesty (023 done; Ops 3 active; 4/5 backlog; COM OPEN).
- **SC-005**: GitHub issues created for actionable eng tasks; HUMAN tasks labeled, not auto-closed.
- **SC-006**: Converge appends only true residuals (upload-svc compose, Phase 4/5, Docker validate #70/#72, COM).

---

## Assumptions

- Peer Phase agents may continue editing migrations/UI; Speckit re-checks before overwrite.
- Star Trans live Odoo (PH1-02) still unavailable — Excel path is the offline bridge.
- Platform `v9.4.0-p3` is unrelated DONE work; do not reopen Gates 6–11 without evidence request.
