# IPE Platform Constitution

<!--
Sync Impact Report (Speckit — 2026-07-10 program converge)
Version: 1.2.4 → 1.2.5 (PATCH)
Updated: Development Workflow — Spec 019-program-converge is active Speckit feature for remaining whole-project work
Updated: Principle VIII — R2 eng gates PASS; G-R2-04 Arabic human sign-off and PH1 commercial remain open (not faked)
Clarified: Do not dilute Principle VII three-screen minimum; Wave 2/3 features stay POST-R1 unless contracted
Templates: no structural change (PATCH only)
-->

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
- **Rate limiting is required** on public endpoints (Kong + service-level where applicable).
- **Enterprise profile:** Keycloak OIDC + RS256 JWT MUST be verified by Gate 2 and Option B scripts before enterprise tag promotion.
- **Release 1 profile:** Local/demo JWT acceptable for PoC; production customer MUST use tenant-scoped credentials and secrets in vault (not hardcoded).

**Rationale:** A factory planner approving a schedule is a state-changing, auditable action. Enterprise gates proved SSO, Vault, TLS, and audit in `v9.3.0-p2`.

---

### III. Test-Backed Changes (NON-NEGOTIABLE)

Every behavioral change MUST be accompanied by automated tests.

- **Tests MUST pass before merge.**
- **Odoo connector changes MUST include:** unit tests (mapper), integration tests (mock Odoo XML-RPC), and at least one end-to-end sync test with testcontainers or recorded fixtures.
- **ERP scaffold changes (SAP/D365) MUST include:** import/unit tests proving registry factory and no-op sync paths do not raise.
- **No real network in unit tests.** External services MUST be stubbed.
- **Release 1 gate:** Connector sync + feasibility pipeline MUST have integration test proving MO ingest → Control Tower queue.

**Rationale:** Bad Odoo data in production will be the norm, not the exception. Tests must cover defensive paths.

---

### IV. Event-Driven Architecture Integrity

The event bus is the backbone of inter-service communication in the **full platform**.

- **Full stack (22 services):** Kafka topics, Avro schemas, producer/consumer pairs as documented.
- **Release 1 profile (`docker-compose.release1.yml` and Helm `values-dev.yaml`):** Kafka MAY be omitted. Set `IPE_KAFKA_BOOTSTRAP_SERVERS=""` so health probes return `not_configured` instead of probing `localhost:9092`.
- **Consumer resilience:** Idempotent processing, deserialization error handling, 30s timeout.

**Rationale:** Event mesh is v3.0 architecture. Customer #1 needs reliability over architectural purity.

---

### V. Service Architecture & API Consistency

All services follow a uniform layered architecture.

- **Layered structure:** `app/api/v1/`, `app/models/`, `app/services/`, `app/events/`, `app/deps.py`.
- **`/health`, `/ready`, `/metrics` on every deployed service.**
- **Frontend-backend contract alignment.** Every UI API call MUST have a corresponding backend route.
- **Port scheme:** Dockerfile ports are canonical; docker-compose, Kong, and Helm values MUST stay reconciled.
- **Release 1 deployed services:** `kong`, `dpe-svc`, `fea-svc`, `cap-svc`, `mat-svc`, `connector`, `res-svc`, `web-ui`, `db`, (`redis` if sessions). All other services remain in monorepo but OFF the customer compose file until requested.

**Rationale:** 22 services in repo; 8 in production for customer #1 (Release 1 profile).

---

### VI. Observability & Monitoring

Every **deployed** service MUST be observable.

- **`/metrics` mandatory** on release1 and enterprise services (Gate 1: 9/9 Prometheus targets).
- **Structured JSON logging** with correlation IDs.
- **Performance baselines:** k6 SLO profile (normal load) and stress profile (rate limiter) MUST both pass before enterprise phase tags; they measure different things and MUST NOT be combined into one script.
- **Sync observability (Release 1):** Every Odoo sync run MUST log and persist: start time, end time, records synced, records skipped, errors, data quality flags. UI MUST show "Last synced at" timestamp.
- **Graceful degradation:** `/ready` surfaces DB/Odoo connectivity; planner sees actionable message, not 500 stack trace.

**Rationale:** Phase 2 closed with Grafana dashboards, Alertmanager rules, and documented SLO baselines (`docs/qa/PERFORMANCE-BASELINE-v9.1.0.md`).

---

### VII. Customer-First Release Slicing

**The Odoo connector IS the product for customer #1.** Platform breadth serves demos; release depth serves revenue.

- **One ERP first:** Odoo (XML-RPC + optional `ipe_connector` module). SAP/D365 scaffolds MUST NOT block Odoo production path until customer #2 is contracted.
- **One value proposition:** Planners see at-risk MOs from **live Odoo data** before the shift starts, with structured resolution options.
- **Three screens minimum:** Control Tower, Resolution Center, Executive OTD. Copilot, Scenarios, Supply Network, Quality, Sustainability are **POST-R1** unless customer contract explicitly includes them.
- **Data quality before planning:** MOs missing BOM, routing, or work center capacity MUST be flagged as "unscorable" — never silent misleading feasibility scores.
- **Conflict policy:** Odoo wins on master data; IPE wins on approved schedule until next sync flags conflict (Gate 4 verified).
- **Arabic MVP:** Control Tower, Resolution Center, navigation, and alerts MUST support Arabic before customer go-live.
- **Deployment options:** MUST support (a) Diligent-managed cloud VM and (b) customer on-prem single-VM compose. Full K8s is Phase 3 enterprise track, NOT required for Star Trans R1 go-live.
- **Customer readiness package:** Deployment guide, SOW input, UAT plan, field mapping worksheet, and training curriculum MUST exist before SOW signature (`docs/customer/star-trans/`).

**Rationale:** Engineering output exceeded go-to-market. Release 1 narrows to provable ROI for one paying factory.

---

### VIII. Enterprise Gate Verification (NEW — Phase 2+)

**No enterprise phase tag without scripted gate evidence.**

- **Gates 1–5 are mandatory** before `v9.3.0-p2`-class tags: observability, security, multi-tenant, Odoo sync, full E2E (R1+R2+audit).
- **Option B (Phase 0 combined)** MUST pass when enterprise flags are ON: Keycloak, Vault, TLS, Audit, Combined demo.
- **Phase 3 gates (6–11)** MUST pass before `v9.4.0-p3`: Helm lint/render, kind deploy health, compose–K8s parity, HPA smoke, ERP scaffold imports, R1 demo on K8s ingress. As of **2026-07-10**: Gates **6–10 PASS**; **Gate 11: 12/14 PASS** with documented **OQ-9 waiver** (`docs/demo-data/gate11-oq9-waiver.md`, `docs/demo-data/gate11-k8s-demo.txt`). Compose validation **14/14** (`docs/demo-data/release1-integration-demo.txt`). Tag **`v9.4.0-p3`** applied at `4629119`; closure commits through `ad494e0` include W1-02 smoke and UAT corrections.
- **Phase 4 gates** (GTM): Stripe sandbox billing, tenant self-service API, developer portal — MUST NOT start until Phase 3 tag `v9.4.0-p3` is applied.
- **Phase 5** (enterprise maturity, SOC 2 Type II, v8 SAP gap features): post-GTM backlog; MUST NOT block Phase 3 close-out or Star Trans R1 compose go-live.
- **Gate scripts are the source of truth.** Markdown status tables MUST reference script paths and last PASS output; manual claims without script evidence do not satisfy this principle.
- **Regression:** R1 14/14 HTTPS and R2 5/5 MUST re-run after each phase gate that touches auth, networking, or connector paths.

**Rationale:** Phase 2 closure required reproducible verification, not checklist theater. Phase 3 inherits the same discipline for K8s and ERP expansion.

---

## MENA Market Constraints (Binding on Release 1)

| Constraint | Requirement |
|------------|-------------|
| **Buyer persona** | CEO / Operations Director — not IT steering committee |
| **Competition** | Excel + Odoo MRP — not Kinaxis/SAP IBP in sales pitch |
| **Pricing fit** | License $18K–30K/yr + implementation $12K–25K one-time (OQ-7 pending commercial sign-off) |
| **Connectivity** | Tolerate intermittent factory internet; batch sync > fragile webhooks |
| **ROI timeline** | Measurable within 90 days: adoption, 2+ MOs saved, OTD trend |
| **Implementation** | Fixed-scope SOW, data migration checklist, training curriculum — not demo script alone |

---

## Security & Cross-Platform Constraints

- **Cross-platform.** PowerShell equivalents for all customer-facing and gate verification scripts.
- **Secret management.** Odoo credentials in tenant config / Vault — never in source or logs.
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
- **Enterprise gate (015):** Gates 1–5 + k6 profiles + Option B before Phase 2 tag; Gates 6–11 before Phase 3 tag.
- **Sprint 7 cohesion (016):** Tier 1 activity emitters (T717–T719) complete; migration 038 (T730) applied compose + K8s.
- **First Release Plan (017):** Phase 0 **closed** (`v9.4.0-p3`); Wave 1 engineering delivered (W1-01–08). Waves 2–3 tracked via open GitHub issues #37–#46.
- **Phase 2 Release 2 (018):** Engineering gates G-R2-01/02/03/05 PASS; G-R2-04 Arabic **human** sign-off OPEN; tag HOLD pending policy.
- **Program Converge (019):** Active Speckit feature for remaining whole-project gaps (compose parity, scenario promote, stock.quant mock fidelity, issue triage). Commercial blockers (PH1-01 SOW, PH1-02 Odoo staging, native Arabic sign-off) MUST remain OPEN until humans close them.
- **Constitution compliance:** Every `/speckit.analyze` or `/speckit.implement` MUST verify compliance. Violations block merge.

---

## Governance

- **Authority.** Principles I–III, VII, and VIII are binding gates. Violations MUST be resolved by changing code, not diluting principles.
- **Amendments.** Changes require PR with rationale and SemVer bump. Update Sync Impact Report (HTML comment at top).
- **Versioning.** MAJOR = principled removal; MINOR = new principle or materially expanded doctrine; PATCH = clarifications.
- **Compliance review.** Every PR MUST verify compliance.

## Phase Naming Map (Roadmap vs Spec 015)

External **Enterprise Deployment Roadmap** (36-week) and internal **Spec 015** use overlapping but not identical phase numbers:

| Roadmap | Spec 015 | Focus |
|---------|----------|-------|
| Phase 0 Security | Phase 0 | Keycloak, Vault, TLS, audit |
| Phase 1 K8s/Obs | Phase 1–2 | CI/CD, metrics, Gates 1–5 |
| Phase 2 ERP | Phase 3 Stream 2 | Odoo live; SAP/D365 scaffold |
| Phase 3 Scale | Phase 3 Streams 1, 3 | Helm, K8s gates, compliance prep |
| Phase 4 GTM | Phase 4 | SaaS, Stripe, SDKs, onboarding |
| — | **Phase 5** (Gap Audit) | SOC 2 II, WCAG, Copilot prod, live SAP/D365 |

All `/speckit.analyze` reports MUST use this map when comparing downloaded roadmap documents to executed program status.

---

**Version**: 1.2.5 | **Ratified**: 2026-06-20 | **Last Amended**: 2026-07-10
