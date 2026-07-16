# Feature Specification: Phase 6 Enterprise Agentic Platform

**Feature Branch**: `027-phase6-enterprise-agentic`

**Created**: 2026-07-16

**Status**: Active — Wave 1 (6A/6B/6C) eng COMPLETE

**Input**: `IPE-Phase6-Enterprise-Agentic-Platform.md`. Extend the 12-agent platform (A1–A12) to 17 agents by adding A13 Commercial Intelligence (SD), A14 Analytics Intelligence (SAC), A15 Procurement Execution (MM), A16 Shop Floor Intelligence (PP), and A17 Cross-Functional Orchestrator (meta-agent). Add Modules M7 Analytics Command, M8 Commercial Command, M9 Procurement Command. Build on Phase 3/4/5 (dpe-svc `phase4`/`phase5` cores, ATP/CTP promise, finance margin) — do NOT wipe.

**Gate**: Started only after consuming `docs/qa/PHASES3-5-E2E-TEST-REPORT.md`. Verdict was nominally **FAIL**, but every failure is a strategy-harness `ModuleNotFoundError` referencing module paths absent from this layout (features live in owning services fea-svc/cap-svc/upload-svc whose baseline suites PASS); all 10 baseline unit suites — including `dpe-svc phase4` and `dpe-svc phase5` that Phase 6 depends on — PASS. Foundations verified green (22/22 locally) → PROCEED.

**Out of scope (honest MOCK/SCAFFOLD or deferred)**:
- Live Odoo Accounting / Sales / Purchases write-back — **PH1-02 OPEN** (scaffold `OdooAccountingConnector`, mock only)
- Market/commodity/FX data feed — PH1-02 OPEN (optional injected input)
- IoT / shop-floor machine telemetry — STUB (no live MQTT/REST)
- OQ-7 pricing, SOW send, Odoo 17/19 confirmation, G-R2-04 Arabic native QA → v9.1.1-r2 — **COM OPEN**
- Phase 6D (tuning / SOC 2 readiness / multi-plant) — **DEFERRED**
- Operator tablet UI — minimal (Wave 1)

---

## User Scenarios

### US1 — Commercial Intelligence (A13, M8) (P1)
Sales/planner requests a quote; A13 returns an optimized price (tier + volume + competitive discount, margin-floor protected, discount-authority flag), a full-cost deal-profitability P&L, and contract-compliance alerts (OTD/price/quality/payment SLAs).

### US2 — Analytics Intelligence (A14, M7) (P1)
A14 auto-generates weekly insights (demand pattern, cost trend, operational benchmark, anomaly, financial pattern) with confidence + suggested action, plus trend/anomaly/predictive tools — zero analyst setup.

### US3 — Cross-Functional Orchestration (A17) (P1)
A17 runs the headline cross-functional ATP/CTP: coordinates A1 (demand) + A3 (capacity) + A11 (finance) + A13 (commercial), applies the 6 enterprise policies + resolution hierarchy, and returns an accept / negotiate / reject decision with a governance level.

### US4 — Procurement + Shop-Floor Execution (A15/A16, M9) (P2)
A15 runs 3-way match (PO ↔ receipt ↔ invoice) with routing (auto_approve / route_for_approval / block_and_investigate); A16 serves digital work instructions, operator time tracking, and live production progress.

---

## Requirements

- **FR-001** A13 pricing optimization (tier/volume/competitive discount, margin floor, discount authority)
- **FR-002** A13 deal-profitability full cost-stack P&L with monthly contribution + target gap
- **FR-003** A13 contract-compliance monitoring with SLA-breach alerts + penalty exposure
- **FR-004** A14 automated insight generation (5 categories) with confidence + action
- **FR-005** A14 trend detection, anomaly alerting (z-score), predictive analytics
- **FR-006** A15 3-way match + receipt confirmation with routing decision
- **FR-007** A16 work instructions, time tracking (efficiency + deviation), production progress
- **FR-008** A17 resolution hierarchy, 6 enterprise policies, cascading events, cross-functional ATP/CTP
- **FR-009** Odoo Accounting scaffold (mock, PH1-02-honest) + integration status endpoint
- **FR-010** APIs under `/api/v1/enterprise/*`; router registered; Kong :8000 reachable
- **FR-011** Migrations 060–063 (commercial quote, analytics insight, 3-way match, orchestrator decision) with RLS
- **FR-012** Frontend M7 Analytics + M8 Commercial + M9 Procurement pages, Intelligence hub nav, routes
- **FR-013** PHASE6 execution+test report; PRODUCT-STATUS / CHANGELOG / OPEN-ITEMS honesty
- **FR-014** Unit tests per new agent (pytest) + API smoke + cross-functional orchestration test

## Success Criteria

- **SC-001** Phase 6 unit + API suites GREEN (`test_phase6_commercial/analytics/orchestrator/execution/api`)
- **SC-002** No regression in existing dpe-svc suite
- **SC-003** APIs under `/api/v1/enterprise/*`; frontend typechecks
- **SC-004** Migrations continue head numbering (059 → 060–063) with RLS on every tenant table
- **SC-005** COM blockers (OQ-7, PH1-02, G-R2-04) remain OPEN; mock/stub capabilities flagged honestly
- **SC-006** Headline cross-functional ATP/CTP (A17 coordinating A1/A3/A11/A13) demonstrated + tested
