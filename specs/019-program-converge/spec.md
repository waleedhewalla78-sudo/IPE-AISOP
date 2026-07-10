# Feature Specification: IPE Program Converge (Whole-Project Remaining Work)

**Feature Branch**: `019-program-converge`  
**Created**: 2026-07-10  
**Status**: Active — Speckit full pipeline  
**Product scope**: IPE AISOP only (Nexus Social out of scope)  
**Workspace**: `E:\AISOP\ipe` (canonical)  
**Inputs**: `OPEN-ITEMS-PROJECT.md`, `READINESS.md`, specs 000–018, GitHub #15–#46, constitution v1.2.5

**Purpose**: Program-level Speckit pass that inventories remaining whole-project work without corrupting completed sprint history (017/018). Closes unblocked engineering gaps; keeps commercial/human blockers honest.

---

## What We Build (Already Delivered — Context)

IPE is an ERP-agnostic, feasibility-first manufacturing planning platform (Odoo-first) for MENA mid-market discrete manufacturers.

| Track | Status (2026-07-10) |
|-------|---------------------|
| Specs 000–012 | Historical / absorbed into R1–R2 |
| Spec 013 R1 Odoo MENA | Eng largely done; commercial UAT open |
| Spec 015 Enterprise | Partial; #15–#24 open (triage) |
| Spec 016 Sprint 7 | Emitters/migration done; issues closed where verified |
| Spec 017 First release | Wave 1 eng ✅; PH1-* commercial open |
| Spec 018 Phase 2 R2 | Eng ~90%; G-R2-01/02/03/05 PASS; G-R2-04 human open |
| Platform tag | `v9.4.0-p3` applied; R2 tag HOLD |

---

## What We Want to Build (This Feature)

Close remaining **engineering-unblocked** gaps that block program honesty and R2 compose fidelity:

1. **Compose parity** — `mat-svc` present in `docker-compose.release2.yml` (URL already referenced).
2. **Scenario promotion** — promote API + workbench UI (#40).
3. **stock.quant fidelity** — mock-odoo returns real quants so connector inventory sync is E2E-testable (connector path already exists).
4. **Program artifacts** — refreshed Speckit rollup, issue links, converge honesty.
5. **Explicit deferrals** — tenant provision/quotas (#37/#38), Wave 3 (#43–#46), predictive delay E2E (#42), EP3 stale (#15–#24) with ARB notes — not fake-closed.
6. **Never fake** — PH1-01 SOW, PH1-02 Odoo staging, native Arabic human sign-off.

---

## User Scenarios & Testing

### User Story 1 — R2 compose material service (Priority: P1)

As a **release engineer**, I need `mat-svc` running in the Release 2 compose stack so Copilot/material URLs resolve and smoke does not depend on a missing service.

**Why this priority**: `MAT_SVC_URL` is already set on nlp-svc; missing service causes silent tool failures.

**Independent Test**: `docker compose -f infrastructure/docker/docker-compose.release2.yml config` lists `mat-svc`; health on `:8002` returns ok when stack is up.

**Acceptance Scenarios**:

1. **Given** release2 compose file, **When** config is validated, **Then** `mat-svc` service is defined with AUTH_MODE=local and Kafka disabled.
2. **Given** stack up, **When** health is polled, **Then** mat-svc `/api/v1/health` returns 200.

---

### User Story 2 — Scenario promotion (Priority: P1)

As a **planner**, I need to **promote** a saved what-if scenario so the team can mark a preferred plan without leaving the workbench.

**Why this priority**: GitHub #40 open; CRUD/compare exist; promote is the missing workbench capability.

**Independent Test**: POST promote endpoint sets status `promoted`; UI button visible on active scenarios; unit/API test covers happy path + not-found.

**Acceptance Scenarios**:

1. **Given** an active scenario, **When** planner promotes it, **Then** status becomes `promoted` and list still returns it (or dedicated promoted filter).
2. **Given** wrong tenant/id, **When** promote is called, **Then** NOT_FOUND is returned without leaking cross-tenant data.

---

### User Story 3 — stock.quant mock fidelity (Priority: P1)

As a **connector engineer**, I need mock Odoo to return `stock.quant` rows so inventory sync can be proven without staging Odoo (PH1-02).

**Why this priority**: Connector `sync_inventory()` exists; mock returned `[]`, making FR-R1-05 appear undelivered.

**Independent Test**: mock search_read `stock.quant` returns ≥1 row; sync_inventory updates product safety_stock in unit/integration test with mock.

**Acceptance Scenarios**:

1. **Given** mock-odoo, **When** search_read stock.quant, **Then** non-empty quants with product_id/quantity/reserved_quantity.
2. **Given** connector sync_inventory against mock, **When** sync runs, **Then** updated count ≥ 1 (or products matched).

---

### User Story 4 — Program honesty & issue hygiene (Priority: P2)

As a **PM**, I need open GitHub issues and Speckit artifacts to reflect true status so executives do not see fake completion.

**Why this priority**: Prevents false readiness claims on commercial blockers.

**Independent Test**: Spec/analyze/converge list PH1-01/02 and Arabic sign-off as OPEN; new tasks mapped to issues without duplicating closed #27–#36/#39/#41.

**Acceptance Scenarios**:

1. **Given** commercial blockers, **When** Speckit implement runs, **Then** those tasks are marked blocked, not completed.
2. **Given** closed Wave 1 issues, **When** taskstoissues runs, **Then** no duplicate issues are created.

---

### Edge Cases

- Promote on already-promoted scenario: idempotent success.
- mat-svc added while another QA agent holds ports: prefer config-only change; do not `docker compose down` destructively.
- stock.quant with unknown product_id: skip update, count as unmatched (no crash).
- Keycloak unhealthy: R2 continues on AUTH_MODE=local (existing policy).

---

## Requirements

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-019-01 | release2 compose MUST define `mat-svc` with local auth and no Kafka | P0 |
| FR-019-02 | scenario-svc MUST expose `POST /api/v1/scenario/{id}/promote` | P0 |
| FR-019-03 | Scenario Workbench MUST offer a Promote action with EN+AR strings | P0 |
| FR-019-04 | mock-odoo MUST return sample `stock.quant` records | P0 |
| FR-019-05 | Speckit artifacts MUST document commercial blockers as OPEN | P0 |
| FR-019-06 | New GitHub issues MUST NOT duplicate closed #27–#36/#39/#41 | P0 |
| FR-019-07 | Open #37/#38/#40/#42–#46 MUST be linked or updated, not silently closed | P1 |
| FR-019-08 | Wave 3 NL/supplier (#43–#46) remain scheduled/deferred (not R2 gate) | P2 |

### Non-Functional

| ID | Requirement |
|----|-------------|
| NFR-019-01 | Changes MUST include automated tests (constitution III) |
| NFR-019-02 | Tenant isolation on promote (constitution I) |
| NFR-019-03 | Do not kill shared QA stack ports destructively |

### Out of Scope

- Signing Phase 1 SOW (PH1-01)
- Provisioning customer Odoo staging (PH1-02)
- Native Arabic human linguistic sign-off (G-R2-04)
- Full tenant self-service SaaS (#37/#25) unless timeboxed skeleton
- Wave 3 NL schedule change and supplier comms delivery
- Moving/retagging `v9.1.0-r2` without Arabic policy

---

## Success Criteria

| ID | Criterion | Measurable |
|----|-----------|------------|
| SC-019-01 | mat-svc defined in release2 compose | `docker compose ... config --services` includes mat-svc |
| SC-019-02 | Promote path works | API test green; UI key `scenarios.promote` present EN+AR |
| SC-019-03 | stock.quant mock non-empty | Unit assertion on mock search_read |
| SC-019-04 | Commercial blockers remain OPEN in converge.md | Explicit OPEN rows |
| SC-019-05 | Speckit pipeline artifacts complete | constitution→converge files present under `specs/019-program-converge/` |

---

## Key Entities

- **PlanningScenario** — status: `active` \| `promoted` \| `archived`
- **stock.quant** (Odoo) — product_id, quantity, reserved_quantity, location usage=internal
- **Release2ComposeService** — mat-svc alongside existing R2 services

---

## Assumptions

- Connector `sync_inventory()` implementation is retained; only mock fidelity + tests needed for eng proof.
- AUTH_MODE=local remains the R2 demo path while Keycloak is unhealthy.
- Another agent may run E2E/k6; prefer additive compose/code changes over stack teardown.
- Spec 005 remains historical rollup; 019 is the active program-converge feature pointer.

---

## Dependencies

- Spec 018 gate evidence (`docs/qa/release2-smoke-2026-07-10.txt`, demo G-R2-05)
- Open issues #37–#46, #15–#26
- Constitution v1.2.5
