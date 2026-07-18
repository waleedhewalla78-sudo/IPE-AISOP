# IPE Platform Constitution

<!--
Sync Impact Report (Speckit - 2026-07-18 phase8-r1-production)
Version: 1.4.1 -> 1.4.2 (PATCH)
Updated: Development Workflow — Spec 030-phase8-r1-production ACTIVE; Spec 029 ENG COMPLETE Wave 1
Updated: Phase Naming Map — Productionization COMPLETE Wave 1; Phase 8 Wave 1 (8A) active
Clarified: Migrations continue from head 069 (070 write-back log); Ollama degrade + role thresholds binding for Wave 1
Reaffirmed: COM blockers (OQ-7, PH1-02, G-R2-04, OQ-1) remain OPEN — never fake; no live write-back without PH1-02
Templates: no structural change (PATCH pointer/workflow only)
Root .specify/memory/constitution.md MUST stay synced to this canonical ipe copy

Prior (2026-07-18 productionization): 1.4.0 -> 1.4.1 (PATCH) — Spec 029 active
Prior (2026-07-16 phase6-enterprise-agentic): 1.3.0 -> 1.4.0 (MINOR) — Principle X
Prior (2026-07-15 phase3-ops-intelligence): 1.2.8 -> 1.3.0 (MINOR) — Principle IX
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
- **Phase 3 ops agents MUST include:** unit tests for scorers/analyzers/batchers with stubbed DB; no live Odoo or external LLM required for merge.
- **No real network in unit tests.** External services MUST be stubbed.
- **Release 1 gate:** Connector sync + feasibility pipeline MUST have integration test proving MO ingest → Control Tower queue.

**Rationale:** Bad Odoo data in production will be the norm, not the exception. Tests must cover defensive paths.

---

### IV. Event-Driven Architecture Integrity

The event bus is the backbone of inter-service communication in the **full platform**.

- **Full stack (22 services):** Kafka topics, Avro schemas, producer/consumer pairs as documented.
- **Release 1 profile (`docker-compose.release1.yml` and Helm `values-dev.yaml`):** Kafka MAY be omitted. Set `IPE_KAFKA_BOOTSTRAP_SERVERS=""` so health probes return `not_configured` instead of probing `localhost:9092`.
- **Consumer resilience:** Idempotent processing, deserialization error handling, 30s timeout.
- **Agent orchestrator:** Chain steps MAY call HTTP endpoints when Kafka is not configured; MUST still log activity to `cdm_agent_activity_log`.

**Rationale:** Event mesh is v3.0 architecture. Customer #1 needs reliability over architectural purity.

---

### V. Service Architecture & API Consistency

All services follow a uniform layered architecture.

- **Layered structure:** `app/api/v1/`, `app/models/`, `app/services/`, `app/events/`, `app/deps.py`.
- **`/health`, `/ready`, `/metrics` on every deployed service.**
- **Frontend-backend contract alignment.** Every UI API call MUST have a corresponding backend route.
- **Port scheme:** Dockerfile ports are canonical; docker-compose, Kong, and Helm values MUST stay reconciled.
- **Release 1 deployed services:** `kong`, `dpe-svc`, `fea-svc`, `cap-svc`, `mat-svc`, `connector`, `res-svc`, `web-ui`, `db`, (`redis` if sessions). All other services remain in monorepo but OFF the customer compose file until requested.
- **New services (e.g. upload-svc:8120):** MUST land in compose/Kong before customer enablement; MAY ship behind feature flag until Wave complete.

**Rationale:** 22 services in repo; 8 in production for customer #1 (Release 1 profile).

---

### VI. Observability & Monitoring

Every **deployed** service MUST be observable.

- **`/metrics` mandatory** on release1 and enterprise services (Gate 1: 9/9 Prometheus targets).
- **Structured JSON logging** with correlation IDs.
- **Performance baselines:** k6 SLO profile (normal load) and stress profile (rate limiter) MUST both pass before enterprise phase tags; they measure different things and MUST NOT be combined into one script.
- **Sync observability (Release 1):** Every Odoo sync run MUST log and persist: start time, end time, records synced, records skipped, errors, data quality flags. UI MUST show "Last synced at" timestamp.
- **Agent observability (Phase 3):** Every agent chain run MUST persist activity log + exceptions with SLA timestamps; UI MUST surface open exceptions.
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
- **Arabic MVP:** Control Tower, Resolution Center, navigation, and alerts MUST support Arabic before customer go-live. **Human native QA sign-off (G-R2-04) remains OPEN** — engineering Arabic keys MUST NOT be treated as commercial sign-off.
- **Deployment options:** MUST support (a) Diligent-managed cloud VM and (b) customer on-prem single-VM compose. Full K8s is enterprise track (platform Phase 3 DONE @ `v9.4.0-p3`), NOT required for Star Trans R1 go-live.
- **Customer readiness package:** Deployment guide, SOW v1, UAT plan, field mapping worksheet, training curriculum, sales one-pagers, support guide, release notes, and `scripts/star-trans-validate.ps1` MUST exist before SOW signature. Artifacts EXIST under `docs/customer/star-trans/`, `docs/sales/`, `docs/runbooks/`, and `deploy/star-trans/`. **SOW send remains blocked by OQ-7 pricing** until commercial owner fills amounts.
- **Honesty rule:** Agents and engineers MUST NOT invent Arabic sign-off, live Odoo staging proof, Odoo version confirmation, or pricing. Document COM blockers; implement only engineering-feasible work.

**Rationale:** Engineering and GTM packages are ready; remaining blockers are commercial and customer-IT — not code gaps.

---

### VIII. Enterprise Gate Verification

**No enterprise phase tag without scripted gate evidence.**

- **Gates 1–5 are mandatory** before `v9.3.0-p2`-class tags: observability, security, multi-tenant, Odoo sync, full E2E (R1+R2+audit).
- **Option B (Phase 0 combined)** MUST pass when enterprise flags are ON: Keycloak, Vault, TLS, Audit, Combined demo.
- **Platform Phase 3 gates (6–11)** MUST pass before `v9.4.0-p3`: Helm lint/render, kind deploy health, compose–K8s parity, HPA smoke, ERP scaffold imports, R1 demo on K8s ingress. **DONE** with OQ-9 waiver for Gate 11 partials.
- **Platform Phase 4 gates** (GTM SaaS): Stripe sandbox billing, tenant self-service API, developer portal — tracked as backlog; MUST NOT invent PASS.
- **Platform Phase 5** (SOC 2 Type II, live SAP/D365): post-GTM backlog; MUST NOT block Star Trans R1 compose go-live.
- **Gate scripts are the source of truth.** Markdown status tables MUST reference script paths and last PASS output; manual claims without script evidence do not satisfy this principle.
- **Regression:** R1 14/14 HTTPS and R2 5/5 MUST re-run after each phase gate that touches auth, networking, or connector paths.
- **Planning intelligence tag:** `v9.2.0-planning` applied at `b04434d` (Sprint 1 engineering closure).

**Rationale:** Phase 2 closure required reproducible verification, not checklist theater.

---

### IX. Operations Intelligence Program (Blueprint Phases 3→5) — NEW

**Ops Blueprint Phases 3–5 are a product program distinct from platform K8s/GTM phase numbers.**

- **Spec 024** governs Blueprint Phase 3 (7 AI agents, predictive risk, exceptions, Excel upload wizard) as the **active engineering slice**. Migrations **051–059** (or ALTER equivalents where tables already exist) are the schema spine.
- **Blueprint Phase 4** (6 Command modules, agents A8–A12) and **Phase 5** (Planning Cockpit / MPS / MRP / ATP deep UI) are **program backlog** under the same Speckit analyze surface until their own feature numbers are cut — tracked, not silently claimed DONE.
- **Concurrent Phase agents:** Speckit MUST absorb peer agent deltas (migrations, models, UI) and implement **remaining gaps** only — never recreate tables or force-fight peer edits.
- **COM blockers remain OPEN** and MUST never be auto-closed by Speckit or Phase agents.
- **Tag discipline:** Never push stale `v9.1.0-r2`. Cut `v9.1.1-r2` only after G-R2-04. Ops Phase 3 eng completion MAY use a separate tag (e.g. `v9.5.0-ops3`) only with test evidence — never invent tag application.

**Rationale:** Without a binding Ops-vs-Platform map, agents collide on phase numbers and duplicate schema work.

---

### X. Agentic Autonomy Governance (Blueprint Phase 6) — NEW

**Phase 6 expands the platform to 17 agents (A1–A17) and 9 modules (M1–M9); autonomy MUST be governed and auditable.**

- **Spec 027** governs Blueprint Phase 6 (A13 Commercial, A14 Analytics, A15 Procurement Execution, A16 Shop Floor, A17 Cross-Functional Orchestrator; modules M7 Analytics / M8 Commercial / M9 Procurement). Migrations **060–063** are the schema spine — continue head numbering, never recreate.
- **Four-level governance is binding.** Every autonomous or recommended action MUST declare a governance level: L1 Autonomous (reversible ≤4h, logged), L2 Supervised (notify + override window), L3 Approved (human approval before execution), L4 Escalated (management decision with executive brief). High-impact or below-guardrail actions MUST NOT self-execute.
- **A17 is the only cross-functional arbiter.** Conflicts between domain agents MUST be resolved via the documented resolution hierarchy (safety > customer_sla > revenue_protection > margin_protection > cost_optimization > efficiency > sustainability) and the six enterprise policies. The two hard gates — **Margin Floor (P4)** and **Quality Non-Negotiable (P6)** — MUST be able to BLOCK, not merely warn.
- **Honesty for live integrations (reaffirms VII).** Odoo Accounting/Sales/Purchases write-back, market/FX/commodity feeds, and IoT/shop-floor telemetry are **PH1-02 OPEN**. Phase 6 MUST ship these as MOCK/STUB with an explicit `live:false` + blocker; agents MUST NOT present mock output as live ERP data.
- **Test discipline (reaffirms III).** Each new agent MUST have unit tests with no live network; the headline cross-functional ATP/CTP (A17 coordinating A1/A3/A11/A13) MUST have a test. No COM blocker auto-closed; no tag applied without scripted evidence.

**Rationale:** Autonomous cross-functional decisions are only safe with a bright-line governance ladder, hard safety/quality/margin gates, a single arbiter, and honest boundaries around un-integrated ERP data.

---

## MENA Market Constraints (Binding on Release 1)

| Constraint | Requirement |
|------------|-------------|
| **Buyer persona** | CEO / Operations Director — not IT steering committee |
| **Competition** | Excel + Odoo MRP — not Kinaxis/SAP IBP in sales pitch |
| **Pricing fit** | License $18K–30K/yr + implementation $12K–25K one-time (**OQ-7 OPEN — blocks SOW send**) |
| **Connectivity** | Tolerate intermittent factory internet; batch sync > fragile webhooks |
| **ROI timeline** | Measurable within 90 days: adoption, 2+ MOs saved, OTD trend |
| **Implementation** | Fixed-scope SOW, data migration checklist, training curriculum — not demo script alone |

---

## Security & Cross-Platform Constraints

- **Cross-platform.** PowerShell equivalents for all customer-facing and gate verification scripts.
- **Secret management.** Odoo credentials in tenant config / Vault — never in source or logs. Never commit `.kms_keys/` material.
- **Input validation.** Pydantic models on all API boundaries.
- **Formatting.** `ruff check`, `mypy`, `prettier` MUST pass.

---

## Development Workflow & Quality Gates

- **Branch naming:** `feat/<short-slug>`, `fix/<short-slug>`, `chore/<short-slug>`, `docs/<short-slug>`.
- **PR requirements:** CI green, tests for new behavior, API docs if routes change.
- **Release 1 gate (013):** Before customer go-live:
  1. MO ingest from Odoo → Control Tower queue (live or recorded integration test)
  2. `docker-compose.release1.yml` / `deploy/star-trans/` starts in ≤10 min on 8GB RAM VM
  3. Arabic strings on 3 core screens
  4. Implementation playbook + support runbook published
  5. 90-day ROI metrics instrumented
- **Enterprise gate (015):** Gates 1–5 + k6 profiles + Option B before Phase 2 tag; Gates 6–11 before platform Phase 3 tag (`v9.4.0-p3` DONE).
- **Planning Intelligence (020):** **ENG COMPLETE** — Modules A–F + Copilot tools + Kong; migrations 044–049; tests green.
- **Release Closure (021):** **ENG COMPLETE** — UAT-10/11 fixed; OQ-13 script; tag `v9.2.0-planning` applied; commercial blockers documented.
- **Sprint 3 Go-Live (022):** **ENG COMPLETE** — deploy dry-run, validate/smoke evidence, status honesty, GH hygiene; residuals #70/#72 may remain OPEN.
- **Sprint 4 Wave 1 (023):** **ENG COMPLETE** @ ~31d4840 — Admin Odoo Config v2 + OTD Analytics; COM blockers remain OPEN.
- **Ops Phase 3 (024):** **ENG COMPLETE Wave 1** — Blueprint Phase 3 agents + predictive risk + exception lifecycle + upload foundation; migrations 051–059.
- **Ops Phase 4 (025) / Phase 5 (026):** **ENG COMPLETE Wave 1** — M1–M6 + A8–A12 + autonomy + portal; Planning/Command deep.
- **Ops Phase 6 (027):** **ENG COMPLETE Wave 1 (6A+6B+6C)** — agents A13–A17, modules M7–M9, migrations 060–063; live Odoo/market/IoT MOCK/STUB (PH1-02 OPEN); Phase 6D deferred.
- **Ops Phase 7 (028):** **ENG COMPLETE Wave 1** — deep planning/ops disciplines; migrations 064–067; Kong planning-command smoke green.
- **Productionization (029):** **ENG COMPLETE Wave 1** — Kong enterprise route, Andon DB wire, RLS 068, MPS/MRP 069, stage-gate scaffold, QA notes; validate #70/#72/#110 OPEN (stack); COM OPEN.
- **Phase 8 R1 Production (030):** **Active Speckit feature** — Wave 1 (8A): Ollama scaffold + rule-based degrade, AgentRoleContext ($1K/$10K/$50K), Excel upload types + CSV export, write-back safety log (migration 070, live flag default false), Arabic Phase 8 keys (G-R2-04 OPEN), A18–A20 stubs; 8B–8D deferred. COM blockers remain OPEN.
- **Constitution compliance:** Every `/speckit.analyze` or `/speckit.implement` MUST verify compliance. Violations block merge.
- **Phase 8 honesty (Wave 1):** Ollama fine-tuned weights are ops Modelfile stubs only; live Odoo write-back MUST remain behind `ipe.odoo.live_writeback=false` until PH1-02; never claim G-R2-04 or marketing tag `v9.1.1-r2`.

---

## Governance

- **Authority.** Principles I–III, VII, VIII, IX, and X are binding gates. Violations MUST be resolved by changing code, not diluting principles.
- **Amendments.** Changes require PR with rationale and SemVer bump. Update Sync Impact Report (HTML comment at top).
- **Versioning.** MAJOR = principled removal; MINOR = new principle or materially expanded doctrine; PATCH = clarifications.
- **Compliance review.** Every PR MUST verify compliance.
- **Canonical constitution path:** `ipe/.specify/memory/constitution.md`. Workspace root `.specify/memory/constitution.md` MUST stay in sync when Speckit runs from AISOP root.

## Phase Naming Map (Roadmap vs Spec 015 vs Ops Blueprint)

External documents use overlapping phase numbers. All Speckit analyze reports MUST use this map:

| Label | Meaning | Status (2026-07-15) |
|-------|---------|---------------------|
| Platform Phase 0–2 | Keycloak/Vault/TLS; Gates 1–5; obs | DONE (`v9.3.0-p2`) |
| Platform Phase 3 | Helm/K8s Gates 6–11; ERP scaffolds | DONE (`v9.4.0-p3`) |
| Platform Phase 4–5 | GTM SaaS / SOC2 / live SAP | BACKLOG (do not fake) |
| **Ops Blueprint Phase 3** | 7 agents, predictive risk, upload wizard | ENG COMPLETE Wave 1 — Spec 024 |
| **Ops Blueprint Phase 4** | 6 Command modules; agents A8–A12 | ENG COMPLETE Wave 1 — Spec 025 |
| **Ops Blueprint Phase 5** | Planning Cockpit / MPS / MRP / ATP deep | ENG COMPLETE Wave 1 — Spec 026 |
| **Ops Blueprint Phase 6** | Enterprise agentic: agents A13–A17, modules M7–M9 | ENG COMPLETE Wave 1 — Spec 027 (Odoo/market/IoT MOCK/STUB) |
| **Ops Blueprint Phase 7** | Deep planning & ops intelligence | ENG COMPLETE Wave 1 — Spec 028 |
| **Productionization** | Kong/Andon/RLS/QA hardening | ENG COMPLETE Wave 1 — Spec 029 |
| **Phase 8 Wave 1 (8A)** | Ollama/roles/Excel/write-back safety | **ACTIVE — Spec 030** |
| Spec 023 Wave 1 | Odoo Config v2 + OTD | ENG COMPLETE |
| Spec 020 Planning Intelligence | Modules A–F | ENG COMPLETE @ `v9.2.0-planning` |

---

**Version**: 1.4.2 | **Ratified**: 2026-06-20 | **Last Amended**: 2026-07-18
