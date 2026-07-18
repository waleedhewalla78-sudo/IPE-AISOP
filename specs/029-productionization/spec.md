# Feature Specification: Productionization & Hardening

**Feature Branch**: `029-productionization`

**Created**: 2026-07-18

**Status**: Active — Wave 1 ENG COMPLETE (this Speckit run)

**Input**: Engineering-actionable backlog from `docs/project/OPEN-TOPICS-REGISTER.md` (Top-10 items 5–9 + related residuals). Specs 022–028 Wave 1 ENG COMPLETE; constitution **1.4.0 → 1.4.1** (PATCH — Spec 029 active pointers).

**Gate**: Started after Spec 028 Phase 7 Deep Planning Wave 1 ENG COMPLETE @ HEAD ~39ad033. Spec 029 does **not** invent new product scope; it closes pure-engineering gaps that block gateway smoke, persistence honesty, RLS completeness, and quality notes.

**Out of scope (honest — COM/HUMAN only; never faked)**:
- OQ-7 pricing / SOW send (C-01/C-02)
- PH1-02 live Odoo staging + live Accounting / market-data / IoT / PO write-back (C-03, INT-02..06)
- G-R2-04 Arabic native QA sign-off → `v9.1.1-r2` tag (C-04, REL-01)
- OQ-1 Odoo 17/19 confirmation (C-05)
- Pushing stale `v9.1.0-r2` (REL-02 — forbidden)

---

## User Scenarios

### US1 — Enterprise APIs reachable via Kong (P0)
A planner/operator hits Phase 6 `/api/v1/enterprise/*` through Kong :8000 and receives the same 200 responses previously only available direct-to-dpe-svc :8020.

### US2 — Andon alerts survive process restart (P1)
A supervisor triggers a red Andon; after dpe-svc restart (or multi-replica), the alert remains queryable from `cdm_andon_alert` (migration 067 already present; Wave 1 board was in-memory only).

### US3 — Tenant isolation on remaining CDM tables (P1)
Security audit TC-RLS-03 moves from PARTIAL toward green: remaining tenant-scoped tables have `rowsecurity=true` + policies; parent-joined child tables use EXISTS policies; `cdm_tenant` self-scope documented.

### US4 — MPS/MRP runs optionally durable (P2)
A planner can persist an MPS/MRP compute result for audit/history when durable plan storage is required (request-driven compute remains the default).

### US5 — S&OP stage-gate scaffolding (P1)
A planner can advance / skip-to `management_review` via an interactive stage-gate API scaffold (closes E2E-SOP-03 BLOCKED path at scaffolding level; full interactive UI may remain Wave 2).

### US6 — Quality evidence honesty (P1/P2)
Engineering captures k6 p95 under-load investigation notes and Playwright flake notes (plus Phase 3+ e2e stubs if feasible) without claiming false green.

### US7 — Validate residuals when stack healthy (P1)
When R2 stack is healthy, seed demo MOs and re-run `star-trans-validate` toward closing GH #70/#72/#110 — do not fake PASS if stack unhealthy.

---

## Requirements

- **FR-001** Kong declarative route `/api/v1/enterprise` → dpe-svc (R2 + deploy package mirrors)
- **FR-002** Wire Andon board trigger/resolve/list to `cdm_andon_alert` (keep in-memory fast path for unit determinism; dual-write + load)
- **FR-003** Migration enabling RLS on remaining gap tables (`cdm_location`, `cdm_project_plan*`, `cdm_sop_forecast/plan`, `cdm_worker_skill_link`, scenario children, `cdm_tenant` self-scope)
- **FR-004** MPS/MRP persistence tables + save helpers (optional; compute APIs unchanged)
- **FR-005** S&OP stage-gate scaffold API under `/planning-command/sop/stage-gate*`
- **FR-006** QA notes: k6 p95 investigation + Playwright flake notes (docs under `docs/qa/`)
- **FR-007** Seed/validate attempt documented; COM blockers remain OPEN
- **FR-008** Pytest coverage for new cores/APIs; no regression to Phase 3–7 suites
- **FR-009** Update `feature.json`, `AGENTS.md`, PRODUCT-STATUS / OPEN-ITEMS honestly

---

## Success Criteria

- Kong enterprise route present in R2 declarative config
- Andon dual-write wired; unit tests green
- RLS remediation migration applied in chain (068+)
- Stage-gate + MPS/MRP persistence scaffolding present with tests
- COM blockers explicitly OPEN in converge
- Speckit pipeline artifacts complete (specify → converge)
