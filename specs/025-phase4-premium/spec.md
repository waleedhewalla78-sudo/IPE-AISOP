# Feature Specification: Phase 4 Premium — Manufacturing Intelligence Platform

**Feature Branch**: `025-phase4-premium`

**Created**: 2026-07-15

**Status**: Active — Wave 1 eng (MVP)

**Input**: `IPE-Phase4-Premium-Proposal.md`. Transform IPE from planning tool into manufacturing intelligence platform: 6 Command modules, agents A8–A12, autonomous guardrails, Command pulse hub, customer portal (read-only). Depends on Spec 024 Ops Phase 3 eng complete. Commercial blockers remain OPEN (do not fake).

**Prior features**: 020/021/022/023 ENG COMPLETE · 024 Phase 3 Wave 1 COMPLETE · Constitution **1.2.8** / 1.3.0 absorb.

**Depends on**: Spec 024 predictive/root-cause/batch/auction/orchestrator; quality-svc, procurement-svc, sustain-svc, order-svc, dpe financial.

**Out of scope**: Live Odoo PH1-02, G-R2-04 Arabic COM, OQ-7 pricing, inventing signatures, pushing `v9.1.0-r2`. Phase 5 Planning Cockpit / MPS deep.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Planner opens Intelligence Pulse with 6 modules (Priority: P1)

As a planner/executive at 07:00, I open Manufacturing Intelligence and see Today's Pulse plus six module cards (Demand, Production, Supply, Quality, Finance, Customer) with key KPIs and links.

**Independent Test**: GET `/api/v1/intelligence/pulse` returns 200 with `modules` length 6; UI route `/intelligence` renders.

**Acceptance Scenarios**:

1. **Given** tenant context, **When** pulse is requested, **Then** module cards include M1–M6 with status and KPI fields.
2. **Given** R2 UI, **When** nav opens Intelligence, **Then** page loads without inventing COM sign-off.

### User Story 2 — Agents A8–A12 produce actionable intel (Priority: P1)

As a planner, I can request customer health (A8), PO recommendations (A9), quality CAPA (A10), MO margin/cash impact (A11), and product carbon/ESG (A12).

**Independent Test**: Unit tests for each core; APIs return structured payloads.

**Acceptance Scenarios**:

1. **Given** customer metrics, **When** A8 health scores, **Then** overall/risk/recommended_action present.
2. **Given** materials below reorder, **When** A9 recommends POs, **Then** priorities and dual-source risk notes appear.
3. **Given** defect event, **When** A10 creates CAPA, **Then** CAPA id + 30/60/90 verify windows set.
4. **Given** MO cost inputs, **When** A11 margins, **Then** gross_margin_pct and variance vs target returned.
5. **Given** BOM + process + transport, **When** A12 footprints, **Then** total kg CO₂e and reduction options returned.

### User Story 3 — Autonomous overnight actions with guardrails (Priority: P2)

As a planner, I see autonomous actions taken overnight that respect guardrails (no A-customer auto-approve; PO value caps; quality inspection add-only).

**Independent Test**: Unit-test `AutonomousRuleEngine` with synthetic overnight context.

**Acceptance Scenarios**:

1. **Given** B-customer reschedule ≤2 days zero cost, **When** rules run, **Then** auto-approve logged and reversible.
2. **Given** A-customer, **When** same rule evaluated, **Then** blocked by guardrail.
3. **Given** PO value > cap or unreliable supplier, **When** auto-PO rule runs, **Then** skipped.

### User Story 4 — Customer portal read-only order tracking (Priority: P2)

As a customer user (or demo role), I view active orders, delivery confidence, and invoice status without write APIs.

**Independent Test**: GET `/api/v1/orders/portal/summary` returns orders with status + confidence; UI `/customer-portal` is read-only.

### User Story 5 — Program honesty (Priority: P2)

PRODUCT-STATUS / CHANGELOG / OPEN-ITEMS / PHASE4 report state Wave 1 eng honestly; COM remains OPEN; Phase 3 not redone.

---

## Requirements

### Functional

- **FR-001** Register agents A8–A12 in status + orchestrator chain (extend, do not replace A1–A7).
- **FR-002** Intelligence pulse API aggregating M1–M6 shells.
- **FR-003** A8 customer health + delay notification draft.
- **FR-004** A9 weekly PO recommendation engine (extend procurement-svc).
- **FR-005** A10 CAPA create/list (extend quality-svc); reuse existing predict/SPC.
- **FR-006** A11 MO margin + decision P&L + 4-week cash sketch (dpe phase4 finance_intel).
- **FR-007** A12 carbon per product + supplier ESG (extend sustain-svc).
- **FR-008** Autonomous rule engine with 4 proposal rules and audit log shape.
- **FR-009** UI: Intelligence hub + customer portal pages; wire routes.
- **FR-010** Docs: Spec 025 + PHASE4 report + PRODUCT-STATUS/CHANGELOG honest update.

### Non-functional

- Auth + tenant on new routes; no secrets in commits.
- Unit tests GREEN for new cores (no Docker required for Wave 1 unit).
- Do not claim live Odoo / Arabic COM / OQ-7 closed.

---

## Success Criteria

- SC-001 A8–A12 unit tests pass
- SC-002 Pulse returns 6 modules
- SC-003 Autonomous guardrails block A-customer auto-approve
- SC-004 PHASE4 report written with honest residuals
- SC-005 Phase 3 cores unchanged (no regression redo)
