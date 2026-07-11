# Feature Specification: Sprint 4 Wave 1 — Odoo Config v2 + OTD Analytics

**Feature Branch**: `023-sprint4-wave1`

**Created**: 2026-07-11

**Status**: Active

**Input**: Sprint 4 Wave 1 delivery after Spec 022 go-live eng closure. Complete Spec 017 Wave 1 items W1-03..W1-08: Admin Odoo Config v2 (encrypted ERP connections) and OTD Analytics dashboard polish. Source checklist: `ipe/tasks/sprint4-todo.md`. Commercial blockers remain OPEN (do not fake).

**Prior features**: 017 (Wave 1 partial) → 020/021/022 ENG COMPLETE. Constitution **1.2.8**.

**Depends on**: Migration head ≥049; connector + dpe-svc + web-ui R1/R2 profiles; `IPE_ENCRYPTION_KEY` for Fernet.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Admin configures Odoo without SQL (Priority: P1)

As a tenant admin, I can create, edit, test, activate, and soft-delete an Odoo ERP connection from the Platform/Admin UI, with passwords encrypted at rest and never returned in API responses.

**Why this priority**: Spec 017 FR-017-PH1-04 / W1-03..W1-05 — self-service Odoo config is required for partner-ready installs and Star Trans staging (when PH1-02 exists).

**Independent Test**: With connector up and `IPE_ENCRYPTION_KEY` set, `pytest services/connector/tests/test_erp_connections.py` PASS; UI route renders connection list/form in R1+R2.

**Acceptance Scenarios**:

1. **Given** an admin JWT + tenant context, **When** POST `/api/v1/erp/connections` with host/db/user/password, **Then** 201 with connection metadata and **no** plaintext password field.
2. **Given** a stored connection, **When** POST `.../test`, **Then** result records success/failure within ~5s (mock XML-RPC in unit tests; live Odoo SKIP if PH1-02 OPEN).
3. **Given** multiple connections of type odoo, **When** one is activated, **Then** only one active Odoo connection per tenant (partial unique index).
4. **Given** migration 050, **When** applied, **Then** `cdm_erp_connection` and `cdm_erp_connection_log` have RLS enabled.

---

### User Story 2 — Manager views OTD KPIs and trends (Priority: P1)

As an operations manager, I open the OTD Analytics dashboard (R1 and R2 nav) and see KPIs, trend, root-cause, baseline comparison, and cost-of-chaos backed by `cdm_otd_snapshot` / aggregator APIs in dpe-svc.

**Why this priority**: Spec 017 W1-06..W1-08 — OTD story is the customer ROI narrative.

**Independent Test**: `pytest services/dpe-svc/tests/test_otd_analytics.py` PASS; OTDDashboardPage loads with i18n keys EN+AR.

**Acceptance Scenarios**:

1. **Given** tenant MO history, **When** GET OTD analytics endpoints, **Then** KPI/trend/root-cause payloads return 200 with tenant isolation.
2. **Given** aggregator capture, **When** daily snapshot is requested, **Then** upsert into `cdm_otd_snapshot` succeeds (migration 039 already exists).
3. **Given** R1 and R2 profiles, **When** nav is inspected, **Then** OTD Dashboard is reachable from Command Center (and related hubs).

---

### User Story 3 — Wave 1 program status is accurate (Priority: P2)

As the program owner, PRODUCT-STATUS, CHANGELOG, Spec 017, and Spec 023 docs show W1-03..W1-08 engineering status honestly, with commercial items still OPEN.

**Why this priority**: Constitution VII honesty.

**Independent Test**: Diff docs — no invented Arabic COM sign-off, pricing, or live Odoo PASS.

**Acceptance Scenarios**:

1. **Given** Wave 1 eng tasks done, **When** PRODUCT-STATUS is read, **Then** Odoo Config v2 and OTD rows reflect BUILT/eng-complete.
2. **Given** OQ-7 / G-R2-04 / PH1-02 / OQ-1, **When** any Spec 023 artifact is read, **Then** they remain explicitly OPEN.

---

### User Story 4 — Spec 022 converge residuals addressed or carried (Priority: P2)

As an engineering lead, #70–#72 (seed feasibility queue, write-back activate 404, re-validate) are either closed with evidence in this sprint or left OPEN with an honest note — never silently marked done.

**Why this priority**: Close the go-live validate gap without claiming COM work.

**Independent Test**: `gh issue view 70/71/72` shows closed with SHA or still OPEN with comment linking Spec 023.

**Acceptance Scenarios**:

1. **Given** demo seed available, **When** T022-equivalent work runs, **Then** feasibility queue check improves OR residual remains documented.
2. **Given** write-back route, **When** T023-equivalent investigation finishes, **Then** route fixed or ARB note documents intentional absence for profile.

---

### Edge Cases

- Missing `IPE_ENCRYPTION_KEY` → API returns clear 500/config error; never store plaintext.
- Test-connection against unreachable host → failure recorded in log; no crash.
- Soft-delete active connection → clears active flag; audit log entry.
- Empty MO set for OTD → zero KPIs, not 500.
- Live Odoo unavailable → SKIP/FAIL labeled COM (PH1-02), not fake PASS.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Migration 050 creates `cdm_erp_connection` + `cdm_erp_connection_log` with RLS and partial unique active Odoo per tenant.
- **FR-002**: Fernet encrypt/decrypt for connection passwords via `IPE_ENCRYPTION_KEY`.
- **FR-003**: Connector REST: CRUD, test, activate, sync-now, logs under `/api/v1/erp/connections`.
- **FR-004**: Admin-only for mutating endpoints (RBAC); tenant context mandatory.
- **FR-005**: React `OdooConnectionsPage` + API client; EN/AR i18n; Admin/Platform routes.
- **FR-006**: dpe-svc `OTDAggregator` + analytics API endpoints for KPIs/trend/root-cause/baseline/cost/snapshot.
- **FR-007**: `OTDDashboardPage` polish + R1/R2 nav; EN/AR keys.
- **FR-008**: Unit tests for ERP connections and OTD analytics (no real network in unit tests).
- **FR-009**: Update PRODUCT-STATUS, CHANGELOG, Spec 017 Wave 1 status; commit Wave 1.
- **FR-010**: Do not fake OQ-7, OQ-1, PH1-02, G-R2-04, or invent signatures; never push `v9.1.0-r2`.

### Key Entities

- **ErpConnection**: tenant-scoped Odoo connection metadata + encrypted password + sync settings.
- **ErpConnectionLog**: audit of create/update/test/activate/sync/delete actions.
- **OtdSnapshot**: daily OTD metrics per tenant (existing migration 039).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `test_erp_connections.py` green (≥ encrypt roundtrip, CRUD, test mock).
- **SC-002**: `test_otd_analytics.py` green for aggregator/API paths touched.
- **SC-003**: Migration 050 present with RLS; env templates document `IPE_ENCRYPTION_KEY`.
- **SC-004**: UI routes for Odoo Connections + OTD Dashboard wired in lazyRoutes/router/hubs.
- **SC-005**: Spec 017 marks W1-03..W1-08 DONE (eng); commercial OPEN unchanged.
- **SC-006**: Constitution 1.2.8 + feature.json point at `ipe/specs/023-sprint4-wave1`.
- **SC-007**: GitHub issues for Spec 023 tasks created; mapping in `taskstoissues.md`.

---

## Out of Scope

- Live Odoo staging provision (PH1-02 COM)
- OQ-7 pricing / SOW send
- G-R2-04 native Arabic commercial sign-off / cutting `v9.1.1-r2`
- Wave 2/3 features (#37–#46)
- nexus-social product work
- Root orphan `services/` tree

---

## Clarifications

*(Filled by `/speckit.clarify` — see `clarify.md`)*

| ID | Topic | Decision |
|----|-------|----------|
| Q1 | Scope vs Spec 017 | Spec 023 = deliver W1-03..W1-08 eng; Spec 017 status updated when done |
| Q2 | #70–#72 | Best-effort in implement; leave OPEN if blocked by Docker/COM |
| Q3 | Multi-ERP | Schema allows erp_type; Wave 1 activates Odoo only |
| Q4 | Sync-now | Triggers existing connector sync path for active connection; no new Kafka requirement for R1 |
| Q5 | Analyze order | Project-status analyze runs pre-plan; consistency matrix refreshed post-tasks |
