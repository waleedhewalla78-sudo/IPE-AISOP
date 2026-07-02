# IPE Platform Constitution

## Sync Impact Report (Release 1 — 2026-06-29)

| Change | Version bump | Notes |
|--------|--------------|-------|
| Added Principle VII: Customer-First Release Slicing | **MINOR 1.0.1 → 1.1.0** | Governs 013-release1-odoo-mena |
| Added Release 1 Deployment Doctrine | — | 5–7 service profile; Odoo IS the product |
| Added MENA Market Constraints | — | Arabic MVP, on-prem option, WhatsApp support |
| Clarified Principle IV exception for R1 | — | Kafka optional in release1 compose |
| v8.2.0 platform complete | — | Full 22-service stack remains in monorepo |

**Compliance**: Principles I–III remain NON-NEGOTIABLE in all deployments. Principle VII governs *what ships* to customer #1, not *what exists* in the repo.

---

IPE (Intelligent Planning Engine) is a microservices-based, event-driven platform for **feasibility-first manufacturing planning** in MENA mid-market discrete manufacturing. These principles are binding on all changes.

## Core Principles

### I. Tenant Isolation via Row-Level Security (NON-NEGOTIABLE)

Every database migration MUST enforce Row-Level Security on every table bearing a `tenant_id` column.

- **RLS is not optional.** Any new table with `tenant_id` MUST have RLS enabled in the same migration.
- **Existing gap MUST be closed.** Legacy tables without RLS policies MUST be remediated before production customer go-live.
- **Dynamic RLS loop is the pattern.** Migration 001's procedural loop is canonical.
- **Cross-tenant queries MUST use `app.set_tenant()`.** Application code MUST set `app.current_tenant` before tenant-scoped queries.

**Rationale:** Multi-tenant isolation is the platform's most critical security boundary. A paying factory customer MUST NOT see another tenant's MOs.

---

### II. Service Authentication & Authorization

Every API endpoint MUST be protected by at least one authentication or authorization layer.

- **Zero open endpoints** except `/health`, `/ready`, `/metrics`.
- **RBAC is mandatory for state-changing operations.** POST/PUT/PATCH/DELETE MUST check role permissions.
- **Rate limiting is required** on public endpoints.
- **Release 1 exception:** Demo JWT auth acceptable for PoC; production customer MUST have tenant-scoped credentials and secrets in vault (not hardcoded).

**Rationale:** A factory planner approving a schedule is a state-changing, auditable action.

---

### III. Test-Backed Changes (NON-NEGOTIABLE)

Every behavioral change MUST be accompanied by automated tests.

- **Tests MUST pass before merge.**
- **Odoo connector changes MUST include:** unit tests (mapper), integration tests (mock Odoo XML-RPC), and at least one end-to-end sync test with testcontainers or recorded fixtures.
- **No real network in unit tests.** External services MUST be stubbed.
- **Release 1 gate:** Connector sync + feasibility pipeline MUST have integration test proving MO ingest → Control Tower queue.

**Rationale:** Bad Odoo data in production will be the norm, not the exception. Tests must cover defensive paths.

---

### IV. Event-Driven Architecture Integrity

The event bus is the backbone of inter-service communication in the **full platform**.

- **Full stack (22 services):** Kafka topics, Avro schemas, producer/consumer pairs as documented.
- **Release 1 profile (`docker-compose.release1.yml`):** Kafka MAY be omitted if sync is batch-driven via connector cron. If omitted, MUST document synchronous call paths and MUST NOT silently drop events required for feasibility scoring.
- **Consumer resilience:** Idempotent processing, deserialization error handling, 30s timeout.

**Rationale:** Event mesh is v3.0 architecture. Customer #1 needs reliability over architectural purity.

---

### V. Service Architecture & API Consistency

All services follow a uniform layered architecture.

- **Layered structure:** `app/api/v1/`, `app/models/`, `app/services/`, `app/events/`, `app/deps.py`.
- **`/health`, `/ready`, `/metrics` on every deployed service.**
- **Frontend-backend contract alignment.** Every UI API call MUST have a corresponding backend route.
- **Release 1 deployed services:** `kong`, `dpe-svc`, `cap-svc`, `connector`, `web-ui`, `db`, (`redis` if sessions). All other services remain in monorepo but OFF the customer compose file until requested.

**Rationale:** 22 services in repo; 5–7 in production for customer #1.

---

### VI. Observability & Monitoring

Every **deployed** service MUST be observable.

- **`/metrics` mandatory** on release1 services.
- **Structured JSON logging** with correlation IDs.
- **Sync observability (Release 1):** Every Odoo sync run MUST log and persist: start time, end time, records synced, records skipped, errors, data quality flags. UI MUST show "Last synced at" timestamp.
- **Graceful degradation:** `/ready` surfaces DB/Odoo connectivity; planner sees actionable message, not 500 stack trace.

**Rationale:** When sync fails at 7am before the production meeting, the planner and support contact need immediate visibility.

---

### VII. Customer-First Release Slicing (NEW — Release 1)

**The Odoo connector IS the product for customer #1.** Platform breadth serves demos; release depth serves revenue.

- **One ERP first:** Odoo (XML-RPC + `ipe_connector` module). SAP/D365 scaffolds MUST NOT distract from Odoo production path until customer #2.
- **One value proposition:** Planners see at-risk MOs from **live Odoo data** before the shift starts, with structured resolution options — not seed SQL, not manual spreadsheet maintenance.
- **Three screens minimum:** Control Tower, Resolution Center, Executive OTD. Copilot, Scenarios, Supply Network, Quality, Sustainability are **POST-R1** unless customer contract explicitly includes them.
- **Data quality before planning:** MOs missing BOM, routing, or work center capacity MUST be flagged as "unscorable" — never silent misleading feasibility scores.
- **Conflict policy required:** When Odoo and IPE disagree (e.g., due date changed in Odoo after IPE approval), behavior MUST be documented and implemented (default: Odoo wins on master data; IPE wins on approved schedule until next sync flags conflict).
- **Arabic MVP:** Control Tower, Resolution Center, navigation, and alerts MUST support Arabic before customer go-live (English may remain as secondary).
- **Deployment options:** MUST support (a) Diligent-managed cloud VM and (b) customer on-prem single-VM compose. Full 22-service AWS/EKS is NOT required for R1.
- **Support model:** Same-day response, business hours, WhatsApp/phone channel documented in runbook — not GitHub issues.

**Rationale:** Engineering output exceeded go-to-market. Release 1 narrows to provable ROI for one paying factory.

---

## MENA Market Constraints (Binding on Release 1)

| Constraint | Requirement |
|------------|-------------|
| **Buyer persona** | CEO / Operations Director — not IT steering committee |
| **Competition** | Excel + Odoo MRP — not Kinaxis/SAP IBP in sales pitch |
| **Pricing fit** | License $18K–30K/yr + implementation $12K–25K one-time |
| **Connectivity** | Tolerate intermittent factory internet; batch sync > fragile webhooks |
| **ROI timeline** | Measurable within 90 days: adoption, 2+ MOs saved, OTD trend |
| **Implementation** | Fixed-scope SOW, data migration checklist, training curriculum — not demo script alone |

---

## Security & Cross-Platform Constraints

- **Cross-platform.** PowerShell equivalents for all customer-facing scripts.
- **Secret management.** Odoo credentials in tenant config / vault — never in source or logs.
- **Input validation.** Pydantic models on all API boundaries.
- **Formatting.** `ruff check`, `mypy`, `prettier` MUST pass.

---

## Development Workflow & Quality Gates

- **Branch naming:** `feat/<short-slug>`, `fix/<short-slug>`, `chore/<short-slug>`, `docs/<short-slug>`.
- **PR requirements:** CI green, tests for new behavior, API docs if routes change.
- **Release 1 gate (013):** Before customer go-live:
  1. MO ingest from Odoo → Control Tower queue (live or recorded integration test)
  2. `docker-compose.release1.yml` starts in ≤10 min on 8GB RAM VM
  3. Arabic strings on 3 core screens
  4. Implementation playbook + support runbook published
  5. 90-day ROI metrics instrumented
- **Constitution compliance:** Every `/speckit.analyze` or `/speckit.implement` MUST verify compliance. Violations block merge.

---

## Governance

- **Authority.** Principles I–III and VII are binding gates for Release 1. Violations MUST be resolved by changing code, not diluting principles.
- **Amendments.** Changes require PR with rationale and SemVer bump. Update Sync Impact Report.
- **Versioning.** MAJOR = principled removal; MINOR = new principle; PATCH = clarifications.
- **Compliance review.** Every PR MUST verify compliance.

**Version**: 1.1.0 | **Ratified**: 2026-06-20 | **Last Amended**: 2026-06-29
