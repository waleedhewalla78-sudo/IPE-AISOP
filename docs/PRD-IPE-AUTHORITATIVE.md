# Product Requirements Document (PRD)

## Intelligent Planning Engine (IPE) — Authoritative Specification

| Field | Value |
|-------|-------|
| **Document ID** | PRD-IPE-AUTHORITATIVE-2026 |
| **Product** | **IPE** (Intelligent Planning Engine) — **not NEXUS** |
| **Product version (full stack)** | **v8.2.0** (code complete; git tag pending — see OQ-4) |
| **Customer release profiles** | Release 1 (`v9.0.0-r1`) · Release 2 (`v9.1.0-r2`) · Enterprise P2 (`v9.3.0-p2` ✅) · Enterprise P3 (`v9.4.0-p3` blocked) · Sprint 7 (`v9.5.0-s7` in progress) |
| **Status** | **As-is development reference** — documents what exists, what is scaffolded, what is validated, and what is blocked |
| **Last updated** | **2026-07-07** |
| **Workspace** | `E:\AISOP\ipe` |
| **Supersedes** | `docs/PRD-IPE-COMPREHENSIVE-AS-IS.md` (retained as historical snapshot through 2026-07-04) |
| **Primary vertical** | Discrete manufacturing — electrical transformers (Star Trans, Egypt/MENA) |
| **Scope boundary** | **IPE AISOP only** — NEXUS Social / external marketing products are **out of scope** |

> **How to read this document:** Sections describe IPE **as it currently exists in development**, not an idealized future state. Items marked **POST-B** require business activation (credentials, contracts). Items marked **⬜** or **🟡** are gaps or partial implementations. **Stakeholder decisions** are flagged as **OQ-*** rather than assumed.

---

## Table of Contents

1. [Product Vision & Scope](#1-product-vision--scope)
2. [Problem Statement & Business Context](#2-problem-statement--business-context)
3. [Goals & Success Metrics](#3-goals--success-metrics)
4. [User Personas & Workflows](#4-user-personas--workflows)
5. [Use Cases](#5-use-cases)
6. [Functional Requirements](#6-functional-requirements)
7. [Feature Specifications](#7-feature-specifications)
8. [Business Scenarios](#8-business-scenarios)
9. [User Interface & Navigation](#9-user-interface--navigation)
10. [Authorization, Roles & Permissions](#10-authorization-roles--permissions)
11. [Reports & Dashboards](#11-reports--dashboards)
12. [Integration Requirements](#12-integration-requirements)
13. [Technical Architecture](#13-technical-architecture)
14. [Competitive Context](#14-competitive-context)
15. [Data & Privacy](#15-data--privacy)
16. [Implementation Roadmap](#16-implementation-roadmap)
17. [Risks & Mitigation](#17-risks--mitigation)
18. [Assumptions & Constraints](#18-assumptions--constraints)
19. [Task Tool & Cursor Integration](#19-task-tool--cursor-integration)
20. [Full Integration Testing Requirements](#20-full-integration-testing-requirements)
21. [Appendices](#21-appendices)

---

## 1. Product Vision & Scope

### 1.1 Vision Statement

> Enable discrete manufacturers to **see which orders are at risk before the shift starts**, **choose among structured resolution options**, and **publish feasible schedules** — grounded in ERP master data, not manually maintained spreadsheets — with AI in **shadow mode** until trust is established.

### 1.2 Product Definition (As-Is)

| Attribute | Definition |
|-----------|------------|
| **Product name** | Intelligent Planning Engine (IPE) |
| **Product type** | AI-assisted Advanced Planning & Scheduling (APS) layer above ERP |
| **Architecture** | Event-driven microservices (22 in full profile; 7–9 in Release 1 compose) + React hub UI + Kong gateway |
| **Primary ERP (live-validated)** | Odoo 17–19 via XML-RPC (`connector`) |
| **Reference customer** | Star Trans — electrical transformers, Egypt/MENA |
| **Constitution** | `ipe/.specify/memory/constitution.md` v1.2.2 — binding principles (RLS, auth, tests, events, service architecture, observability, release gates) |
| **Spec Kit program** | Features `000`–`016` under `ipe/specs/`; active feature `016-sprint7-ecosystem-cohesion` |

### 1.3 In Scope (As-Is — 2026-07-07)

#### Full profile (`VITE_RELEASE_PROFILE=full`)

| Area | Capabilities |
|------|--------------|
| **Unified Workspace** | Cross-tool KPIs + activity feed (`/workspace`) — Sprint 7 Tier 1 |
| **Planning** | Control Tower, Resolution, Schedule (OR-Tools + Excel), Demand, Scenarios |
| **Command** | Executive, War Room, Cost of Chaos, Outcomes (R2), Equipment health |
| **Supply Chain** | Supply network, orders/ATP, procurement, tariff, SCN portal, inventory |
| **AI & Governance** | Copilot, Design AI, AI Trust, MDR, Compliance, Quality, Sustainability |
| **Platform** | Admin, onboarding wizard, MLOps |
| **Shop Floor** | Operator PWA (barcode, work orders) |
| **Integrations** | Kafka event mesh; LLM (Ollama/OpenRouter/Anthropic); Odoo; SAP/D365 scaffolds |
| **Enterprise overlay** | Keycloak, Vault, Kong TLS :8443, Prometheus/Grafana, audit, tenant quotas |

#### Release 1 profile (`VITE_RELEASE_PROFILE=release1`)

| Area | Capabilities |
|------|--------------|
| **Unified Workspace** | Visible; aggregates planning + command KPIs |
| **Planning (trimmed)** | Control Tower, Resolution, Schedule only (hub tabs) |
| **Command (partial)** | Command Center hub; Outcomes tab (R2) |
| **Platform** | Admin (Odoo config, autonomy mode) |
| **Integrations** | Odoo XML-RPC sync + activate write-back; **no Kafka** |
| **Hidden from nav** | Supply Chain, AI & Governance, Shop Floor, Demand, Scenarios |

### 1.4 Explicitly Out of Scope (As-Is)

| Item | Status | Notes |
|------|--------|-------|
| **NEXUS Social** / AI marketing platform | Out | Separate product; not in `ipe/` program |
| Full MES replacement | Out | Shop Floor is monitoring-light |
| Autonomous schedule without human approval | Out | `autonomy_mode=shadow` default |
| Production SAP S/4HANA / D365 connectors | POST-B | Scaffold + registry factory only |
| WCAG 2.1 AA certification | POST-B | Spec 015 Phase 5 |
| SOC 2 Type I/II audit engagement | POST-B | Spec 015 Phase 5 |
| Kafka in Release 1 | Never for R1 | Constitution Principle IV |
| 22-service K8s for first customer | Deferred | R1 = 8 GB VM Docker Compose |
| `stock.quant` live inventory sync | R1.1 | FR-R1-05 not implemented |
| Email ↔ PM bidirectional sync (Microsoft Graph) | Sprint 8+ | Spec 016 Tier 1 stretch deferred |
| Copilot in Release 1 primary nav | Deferred R2 | Hidden by release profile |

### 1.5 Scope Evolution by Version

| Decision | Version / spec | Reasoning |
|----------|----------------|-----------|
| Closed-loop schedule persist | V5 / v1.0.0 (spec 003) | Credibility: approved plans survive refresh |
| Hub consolidation (6 hubs) | v7.0.0 (spec 006) | Reduce 15+ flat routes to 6 hubs |
| U1–U8 v8 streams | v8.0–v8.2 (specs 007–010) | SAP IBP gap closure for enterprise demos |
| Release 1 slice | spec 013 | 8 GB VM; sell vs Excel+Odoo |
| Release 2 growth | spec 014 | Outcomes, Copilot Lite, auto-propose |
| Enterprise gates + K8s | spec 015 | Multi-customer scale path |
| Ecosystem cohesion (EIB) | spec 016 / Sprint 7 | Unified workspace; cross-tool activity |
| Product transition from NEXUS | 2026 program | IPE is canonical manufacturing APS; NEXUS out of repo scope |

### 1.6 Open Scope Decisions (Stakeholder Input Required)

| ID | Question | Impact |
|----|----------|--------|
| **OQ-1** | Canonical Odoo version for R1: **17** (spec 013) vs **19** (local dev validated)? | Field mapping, customer install guide |
| **OQ-2** | Demo SQL overlay vs **Odoo-only** as production source of truth? | Seed scripts vs live sync only |
| **OQ-3** | Enforce **route-level RBAC** in UI? | Any authenticated user reaches all routes today |
| **OQ-4** | When to tag **v8.2.0** in git/CHANGELOG? | READINESS says ready; CHANGELOG stops at v7.0.0 |
| **OQ-5** | Formal MAPE / triage time baseline study? | G-01/G-02 metrics unmeasured in production |
| **OQ-6** | Copilot session retention / GDPR erasure policy? | nlp-svc session storage |
| **OQ-7** | Confirm R1 pricing **$18K–30K/yr** + implementation? | spec 013 commercial model |
| **OQ-8** | R1 compose service count: **mat-svc** in or out? | Constitution lists mat-svc; current `docker-compose.release1.yml` may omit it — **doc drift** |
| **OQ-9** | Accept Gate 11 **12/14** for `v9.4.0-p3` tag or require **14/14**? | Constitution VIII says all Gates 6–11 |

---

## 2. Problem Statement & Business Context

### 2.1 Problems IPE Solves

| Problem | User pain | IPE response (as-is) |
|---------|-----------|---------------------|
| **Invisible infeasibility** | Material/capacity conflicts discovered on shop floor | Feasibility scoring + Control Tower queue |
| **Spreadsheet parallel to ERP** | Dual maintenance; stale MO dates | Odoo sync → CDM; write-back on approve |
| **Unstructured firefighting** | No comparable scenarios | Resolution Center (≥8 scenarios demo tenant) |
| **Capacity blindness** | Overloaded work centers discovered late | Bottleneck map; OR-Tools scheduling |
| **Leadership lag** | OTD seen after month-end | Command Center, Cost of Chaos, Outcomes |
| **Tool fragmentation** | Context-switching across modules | Hub consolidation + Unified Workspace (Sprint 7) |
| **AI distrust** | Black-box recommendations rejected | Shadow autonomy; XAI; AI Trust dashboard |

### 2.2 Target Market

| Segment | Characteristics | IPE fit |
|---------|-----------------|---------|
| **Primary (R1)** | Mid-market discrete on **Odoo** (MENA) | 8-service compose; feasibility-first |
| **Secondary (full)** | $50M–$500M discrete without SAP IBP rollout | 32/32 demo; faster PoC |
| **Not primary** | Fortune 500 multi-site SAP IBP replacement | No live SAP/D365 connector |

### 2.3 Competitive Positioning (Summary)

IPE competes **against Excel + Odoo MRP** for Release 1 and **against Kinaxis / SAP IBP / o9** for full-profile demos. See [Section 14](#14-competitive-context).

---

## 3. Goals & Success Metrics

### 3.1 Platform Success Metrics (Executive)

| Metric | Target | As-is (2026-07-07) | Evidence |
|--------|--------|---------------------|----------|
| Full demo checkpoints | **32/32** | ✅ | `scripts/run-full-demo.ps1` |
| Release 1 HTTPS demo | **14/14** | ✅ Compose; 🟡 **12/14** on K8s | `run-release1-integration-demo.ps1`; `gate11-r1-k8s.txt` |
| Release 2 demo | **5/5** | ✅ | `run-release2-demo.ps1` |
| Backend tests | **870+** pass | ✅ | READINESS.md |
| Enterprise Gates 1–5 | PASS | ✅ | `v9.3.0-p2` |
| Enterprise Gates 6–10 | PASS | ✅ | `GATE-RESULTS-PHASE3.md` |
| Enterprise Gate 11 | PASS | 🟡 **12/14** | OR-Tools timeout on kind |
| k6 SLO P95 | <500ms | ✅ **293ms** | `k6-slo.js` |
| Customer UAT (Star Trans) | Signed | ⬜ | Business-blocked |
| Sprint 7 cohesion | Tier 1 APIs live | ✅ Foundation | spec 016 T701–T714 |

### 3.2 V5 Convergence Goals (Embedded — spec 003)

| ID | Goal | Acceptance | Status |
|----|------|------------|--------|
| V5-G1 | Closed-loop planning | Approve persists to CDM <60s | ✅ |
| V5-G2 | Planner trust (XAI) | Explanation on schedule/rescore | ✅ UI; no formal study |
| V5-G3 | MDR gate | Block schedule if composite <70% | ✅ cap-svc 503 |
| V5-G4 | War Room mitigations | ≥3 recovery options | ✅ |
| V5-G5 | Financial clarity on scenarios | $ impact on cards | ✅ |

### 3.3 Release 1 Metrics (spec 013)

| ID | Metric | Target | As-is |
|----|--------|--------|-------|
| R1-M1 | MOs in Control Tower from Odoo | 100% syncable MOs | ✅ Locally validated |
| R1-M2 | Sync success rate | >95% | ✅ |
| R1-M3 | Post-sync feasibility score | Non-null | ✅ |
| R1-M7 | Write-back to Odoo | Dates match | ✅ Gate 4 |
| R1-M9 | HTTPS + Keycloak demo | 14/14 | ✅ Compose |
| R1-M6 | Customer sign-off | Signed UAT | ⬜ Blocked |

### 3.4 Sprint 7 Cohesion Metrics (spec 016)

| Metric | Target | As-is |
|--------|--------|-------|
| Integration coverage (activity events) | 100% R1 tools emitting | 🟡 EIB consumer + POST ingest; not all services wired |
| Unified dashboard engagement | 60% DAU | ⬜ Post-launch measurement |
| AI recommendation acceptance | 40% | ⬜ Tier 2 not shipped |

---

## 4. User Personas & Workflows

### 4.1 Persona Catalog

| Persona | RBAC role | Primary goals | R1 hub access |
|---------|-----------|---------------|---------------|
| **Production Planner** | `planner` | Triage MOs, resolve, schedule | Workspace, Planning (3 tabs) |
| **Plant Manager** | `manager` | Approve schedules, trade-offs | Same as planner |
| **Shop Supervisor** | `supervisor` | Monitor disruptions | Command Center |
| **Shop Operator** | `operator` | Execute work orders | Shop Floor (hidden R1 nav) |
| **Executive / VP Ops** | `executive` | OTD, margin, chaos cost | Command Center, Workspace KPIs |
| **Procurement Analyst** | `procurement` | Supplier risk, spend | Supply Chain (hidden R1) |
| **System Administrator** | `admin` | Tenant, Odoo, autonomy | Platform → Admin |
| **Auditor** | `auditor` | Read-only compliance | Compliance (limited) |
| **Demo Engineer** | `admin` | 32/32, 14/14 demos | All + scripts |

**Known gap (OQ-3):** UI does not enforce route-level RBAC.

### 4.2 Planner Daily Workflow (Release 1)

```
Login → Unified Workspace (KPIs + activity)
  → Planning → Control Tower (queue sort by score)
       ├─[score < 70]→ Resolution (compare scenarios)
       │                    └─→ Schedule (OR-Tools or Excel)
       │                           └─→ Approve → Odoo activate
       └─[sync stale]→ Admin sync OR wait 15-min scheduler
```

### 4.3 Decision Tree — MO Triage

```
MO in queue?
├─ NO → Run Odoo sync OR seed data
└─ YES → feasibility_score?
    ├─ unscorable (data quality flag) → Fix data / MDR dashboard
    ├─ < 70 → Resolution scenarios → Schedule (if MDR ≥70%)
    └─ ≥ 70 → Schedule directly
         └─ approve → activate Odoo
              ├─ success → done
              └─ MATERIAL_CONFLICT → Resolution / expedite
```

### 4.4 Administrator Workflow — Odoo Setup

```
Platform → Admin → ERP Odoo tab
  → Enter URL, DB, username, password
  → Test connection (POST /admin/erp/odoo/test)
  → Save (encrypted in tenant.config)
  → Manual sync POST /sync/run {"entity":"all", ...creds}
  → Verify /sync/status + Control Tower queue
```

---

## 5. Use Cases

### 5.1 Use Case Index

| ID | Name | Actor | Profile |
|----|------|-------|---------|
| UC-01 | Daily production health triage | Planner | Full + R1 |
| UC-02 | Constraint resolution | Planner, Manager | Full + R1 |
| UC-03 | Finite-capacity scheduling | Planner | Full + R1 |
| UC-04 | Excel project plan import | Planner | Full + R1 |
| UC-05 | Demand sensing / forecast | Planner | Full only |
| UC-06 | What-if scenario | Planner | Full only |
| UC-07 | Supply network visibility | Planner, Executive | Full only |
| UC-08 | Copilot NL query | Planner | Full only |
| UC-09 | Executive disruption review | Executive | Full + R1 partial |
| UC-10 | Shop floor execution | Supervisor, Operator | Full only |
| UC-11 | Star Trans demo load | Demo engineer | Full demo |
| UC-12 | Odoo ERP sync | Admin, System | R1 |
| UC-13 | Schedule write-back | Planner | R1 |
| UC-14 | Post-sync rescore | System | R1 |
| UC-15 | Unified workspace review | All roles | Sprint 7 |
| UC-16 | Cross-tool activity audit | Admin, Auditor | Sprint 7 |

### 5.2 UC-01 — Daily Production Health Triage

| Attribute | Detail |
|-----------|--------|
| **Preconditions** | Authenticated; MOs in CDM; fea-svc healthy |
| **Main flow** | Login → Control Tower → GET `/feasibility/kpis` + `/feasibility/queue` → sort by score → Resolve |
| **Alternatives** | WebSocket refresh; manual sync if stale |
| **Edge cases** | Empty queue; `unscorable=true` |
| **Success criteria** | Top 3 at-risk MOs identified in **≤5 minutes** |

### 5.3 UC-12 — Odoo ERP Sync

| Attribute | Detail |
|-----------|--------|
| **Preconditions** | `erp_type=odoo`; valid creds; Odoo reachable (`host.docker.internal:8069`) |
| **Main flow** | Scheduler 900s OR POST `/sync/run` → upsert products/WC/BOM/MO → commit → rescore → `cdm_sync_run` |
| **Edge cases** | Odoo v17 vs v19 field drift; MO skipped without BOM |
| **Success criteria** | `status=success`; MO count > 0; rescored ≥1 |

### 5.4 UC-13 — Schedule Write-Back

| Attribute | Detail |
|-----------|--------|
| **Main flow** | Approve schedule → POST `/sync/odoo/activate` → XML-RPC updates Odoo dates |
| **Success criteria** | Odoo dates match IPE; no unresolved SYNC_CONFLICT |

### 5.5 UC-15 — Unified Workspace Review (Sprint 7)

| Attribute | Detail |
|-----------|--------|
| **Main flow** | Login → `/workspace` → GET `/dashboard/unified` → review KPIs + activity + pending actions |
| **Success criteria** | Page loads <3s; ≥3 KPI cards; activity feed returns (may be empty pre-EIB wiring) |

---

## 6. Functional Requirements

### 6.1 Authentication & Tenancy

| ID | Requirement | Acceptance | Priority |
|----|-------------|------------|----------|
| FR-AUTH-01 | JWT local or Keycloak OIDC | 401 on bad creds | Must |
| FR-AUTH-02 | Tenant on every API call | JWT claim or `X-Tenant-ID` | Must |
| FR-AUTH-03 | PostgreSQL RLS per tenant | Cross-tenant blocked | Must |
| FR-AUTH-04 | RBAC on state-changing APIs | 403 if role insufficient | Must |
| FR-AUTH-05 | Password hash in `cdm_user` | No plaintext in prod | Must |

### 6.2 Planning Hub

| ID | Requirement | Acceptance | Priority |
|----|-------------|------------|----------|
| FR-PLN-01 | Feasibility queue | ≥1 MO when data present | Must |
| FR-PLN-02 | KPI cards | fea-svc `/kpis` | Must |
| FR-PLN-03 | Resolution scenarios | ≥1 per at-risk MO | Must |
| FR-PLN-04 | OR-Tools schedule | ≤90s (3-MO compose); **300s K8s** | Must |
| FR-PLN-05 | Approve persists CDM | Survives refresh | Must |
| FR-PLN-06 | MDR gate before schedule | composite ≥70% or 503 | Must |
| FR-PLN-07 | Sync status bar (R1) | `/sync/status` | Must |
| FR-PLN-08 | Excel upload | .xlsx validation | Should (R1) |

**Business rules:** BR-PLN-01: autonomy_mode=shadow — no auto-apply. BR-PLN-02: unscorable MOs excluded from auto-confirm.

### 6.3 Odoo Sync (Release 1)

| ID | Requirement | Status |
|----|-------------|--------|
| FR-R1-01 | MO upsert from `mrp.production` | ✅ |
| FR-R1-02 | BOM + routing sync | ✅ |
| FR-R1-03 | 15-min scheduled sync | ✅ |
| FR-R1-04 | Activate write-back | ✅ |
| FR-R1-05 | `stock.quant` inventory | ⬜ R1.1 |
| FR-R1-06 | SYNC_CONFLICT detection | ✅ |
| FR-R1-07 | Post-sync rescore | ✅ |
| FR-R1-08 | Odoo creds in sync body (K8s KMS gap) | ✅ Demo script fix 2026-07-07 |

### 6.4 Sprint 7 — Ecosystem Cohesion (spec 016)

| ID | Requirement | Acceptance | Priority |
|----|-------------|------------|----------|
| FR-S7-01 | Unified dashboard API | `/dashboard/unified` role-aware KPIs | Must ✅ |
| FR-S7-02 | Activity feed | `/activity/feed` paginated | Must ✅ |
| FR-S7-03 | Activity ingest | POST `/activity/events` when Kafka off | Must ✅ |
| FR-S7-04 | EIB normalizer | Kafka topic → `cdm_activity_event` | Must ✅ |
| FR-S7-05 | Pattern discovery | 3 pattern types on activity stream | Should ⬜ |
| FR-S7-06 | Email-PM sync | Microsoft Graph | Deferred Sprint 8 |

### 6.5 Integrations

| ID | Requirement | Status |
|----|-------------|--------|
| FR-INT-01 | Odoo XML-RPC sync + activate | ✅ Live validated |
| FR-INT-02 | SAP/D365 scaffold registry | ✅ Gate 10 |
| FR-INT-03 | Kafka full stack | ✅ Disabled R1 |
| FR-INT-04 | Stripe billing | Mock POST-B |
| FR-INT-05 | LLM tiered routing | ✅ Full stack |

---

## 7. Feature Specifications

| Feature | Purpose | Acceptance criteria | Priority | Introduced |
|---------|---------|---------------------|----------|------------|
| **Unified Workspace** | Single-pane cohesion | `/workspace` + unified API | Must | spec 016 |
| **Cross-tool activity feed** | Audit timeline | GET feed; events persisted | Must | spec 016 |
| **Control Tower** | MO risk queue | Queue + KPIs + Resolve | Must | v1.0.0 |
| **Resolution Center** | Scenario trade-offs | Cost/delivery on cards | Must | v1.0.0 |
| **Schedule + OR-Tools** | Finite capacity Gantt | Approve + persist | Must | v1.0.0 |
| **MDR Gate** | Data readiness | <70% blocks solver | Must | v1.0.0 |
| **Odoo sync engine** | Live ERP ingest | Full sync success | Must R1 | spec 013 |
| **Hub consolidation** | 6 hubs + legacy redirects | 6 sidebar items | Must | v7.0.0 |
| **Outcomes / R2** | OTD baseline, ROI | 5/5 R2 demo | Must R2 | spec 014 |
| **Copilot sessions** | NL planning assist | CP30 pass | Must full | v8.0.0 |
| **Keycloak SSO** | Enterprise IdP | Gate 5 PASS | POST-B | spec 015 |
| **Helm / K8s R1** | Scale path | Gates 6–10 PASS | Must ent | spec 015 |

---

## 8. Business Scenarios

### BS-01 — Star Trans: Copper delay (Full Demo)

| Step | Action | Success metric |
|------|--------|----------------|
| 1 | Planner sees low feasibility MO | <5 min identification |
| 2 | Resolution scenarios compared | Scenario selected |
| 3 | Re-schedule + approve | Gantt + Odoo updated |
| 4 | Executive War Room cost view | $ impact shown |

**Outcome:** 32/32 demo pass.

### BS-02 — Star Trans R1: Morning triage on live Odoo

| Step | Action | Success metric |
|------|--------|----------------|
| 1 | Overnight 15-min sync | `cdm_sync_run.status=success` |
| 2 | Workspace + Control Tower | MOs scored |
| 3 | Resolution + Schedule + activate | Odoo dates updated |

**Outcome:** Locally validated; **customer UAT pending**.

### BS-03 — Sprint 7: Executive cross-tool briefing

| Step | Action | Success metric |
|------|--------|----------------|
| 1 | Executive opens `/workspace` | Unified KPIs load |
| 2 | Reviews activity feed | Events from sync + planning |
| 3 | Drills to War Room | Alert count matches |

**Outcome:** Tier 1 foundation; Tier 2 insights deferred.

---

## 9. User Interface & Navigation

### 9.1 Information Architecture (2026-07-07)

```
App
├── /login (public)
└── Authenticated
    ├── /workspace                    [default landing — Sprint 7]
    ├── Planning Hub      /planning/*
    ├── Command Center    /command-center/*
    ├── Supply Chain      /supply-chain/*    [full nav only]
    ├── AI & Governance   /ai-governance/*   [full nav only]
    ├── Shop Floor        /shop-floor        [full nav only]
    └── Platform          /platform/*
```

### 9.2 Release 1 Visible Routes

| Route | Page | Fields / interactions |
|-------|------|------------------------|
| `/workspace` | Unified Workspace | KPI cards (read-only); activity list; pending actions |
| `/planning/control-tower` | Control Tower | MO table: score, constraint, product, ERP MO ID; KPI cards; sync bar |
| `/planning/resolution` | Resolution | Scenario cards: strategy, cost, delivery impact; approve/reject |
| `/planning/schedule` | Schedule | Gantt; MO multi-select; Approve button; Excel upload (file input) |
| `/command-center/outcomes` | Outcomes | OTD baseline, ROI metrics (R2) |
| `/platform/admin` | Admin | Odoo URL (text), DB (text), username (text), password (password), test/save buttons; autonomy mode (dropdown) |
| `/login` | Login | Email (text), password (password); SSO button (Keycloak) |

### 9.3 Navigation Rules

| Rule | Implementation |
|------|----------------|
| Default route after login | `/workspace` (Sprint 7) |
| R1 nav filter | `IS_RELEASE1` hides Supply, AI, Shop Floor tabs |
| Legacy bookmarks | `/control-tower` → `/planning/control-tower` (etc.) |
| i18n | `en.json` / `ar.json`; Arabic partial (Control Tower + nav) |

---

## 10. Authorization, Roles & Permissions

### 10.1 Role → Permission Matrix

Source: `ipe_shared/auth/rbac.py`

| Role | Permissions |
|------|-------------|
| `admin` | read, write, approve, admin, delete, run_solver, cost_optimize, manage_users |
| `planner` | read, write, approve, run_solver, cost_optimize, view_copilot, run_scenario |
| `manager` | read, write, approve, run_solver, cost_optimize |
| `supervisor` | read, acknowledge_disruption, view_schedule, view_copilot |
| `auditor` | read, view_audit_logs, view_kpis, view_scenarios |
| `operator` | read, write_own |
| `executive` | read, view_kpis |
| `procurement` | read, write, view_kpis |

### 10.2 API Enforcement Examples

| Endpoint | Allowed roles |
|----------|---------------|
| POST `/capacity/schedule` | planner, admin, manager |
| POST `/activity/events` | admin, planner, manager |
| PUT `/admin/erp/odoo` | admin |
| GET `/feasibility/queue` | authenticated + tenant |

### 10.3 Data Visibility

| Rule | Mechanism |
|------|-----------|
| Tenant isolation | PostgreSQL RLS on all `tenant_id` tables |
| Cross-tenant access | **Forbidden** — Gate 3 validates |
| Audit log | Append-only `cdm_audit_log`; auditor read |

**Gap:** UI route guard not implemented (OQ-3).

---

## 11. Reports & Dashboards

### 11.1 Dashboard Catalog

| Dashboard | Route / API | Metrics | Audience | Refresh |
|-----------|-------------|---------|----------|---------|
| **Unified Workspace** | `/workspace`; GET `/dashboard/unified` | MO count, at-risk, alerts, activity | All R1 roles | On load |
| **Planning Dashboard** | `/planning/dashboard` | Queue size, avg feasibility, scenarios, scheduled ops | Planner | On load |
| **Control Tower** | `/planning/control-tower` | Queue, KPIs, bottlenecks | Planner | WebSocket + manual |
| **Command Dashboard** | `/command-center/dashboard` | Alerts, AI OTD, chaos $, recovery | Executive | On load |
| **Outcomes (R2)** | `/command-center/outcomes` | OTD baseline, ROI | Executive | On load |
| **MDR Gate** | `/ai-governance/mdr` | BOM/routing/inventory % | Planner, admin | On load |
| **Executive** | `/command-center/executive` | OTD, delay breakdown | Executive | On load |
| **War Room** | `/command-center/war-room` | Active alerts, recovery plan | Supervisor, Executive | On load |
| **Cost of Chaos** | `/command-center/cost-of-chaos` | 7d Pareto $ | Executive | On load |
| **Activity feed** | GET `/activity/feed` | Cross-tool events | Admin, exec | On load; paginated |

### 11.2 dpe-svc Dashboard APIs

| Endpoint | Payload |
|----------|---------|
| GET `/dashboard/demands` | Demand lines + priority |
| GET `/dashboard/capacity` | WC utilization |
| GET `/dashboard/alerts` | Delay events |
| GET `/dashboard/unified` | KPIs + activity + pending actions |

### 11.3 fea-svc / connector APIs

| Endpoint | Purpose |
|----------|---------|
| GET `/feasibility/queue` | MO risk queue |
| GET `/feasibility/kpis` | at_risk, avg score |
| GET `/feasibility/mdr` | MDR composite |
| GET `/sync/status` | Last sync audit |
| GET `/sync/data-quality` | Flag count |

---

## 12. Integration Requirements

### 12.1 Odoo (Primary — Live)

| Attribute | Specification |
|-----------|---------------|
| Protocol | XML-RPC primary; REST via `ipe_connector` addon optional |
| Versions validated | Odoo 17 (spec 013), Odoo 19 (local dev) — **OQ-1** |
| Auth | Per-tenant `config` JSONB; KMS-encrypted password (`odoo_password_enc`) |
| Sync | POST `/api/v1/sync/run` body: `entity`, optional inline creds (required when connector KMS ≠ dpe KMS) |
| Write-back | POST `/api/v1/sync/odoo/activate` |
| Scheduler | 900s APScheduler in connector |

### 12.2 SAP / D365 (Scaffold)

| Attribute | Specification |
|-----------|---------------|
| Status | Registry factory; no-op sync; Gate 10 unit tests |
| Activation trigger | Customer #2 per spec 015 |
| Constraint | ERP logic MUST NOT leak into CDM core |

### 12.3 Enterprise Services

| Service | Port | Requirement |
|---------|------|-------------|
| Keycloak | 8180 | OIDC; Gate 5 |
| Vault | 8200 | Secrets; `VAULT_ENABLED` |
| Kong | 8000/8443 | TLS, rate limit 300/min |
| Kafka | 9092 | Full stack only; `IPE_KAFKA_BOOTSTRAP_SERVERS=""` for R1 |

### 12.4 EIB — Ecosystem Integration Bus (Sprint 7)

```
Tool → ipe.{tool}.{event} (Kafka) OR POST /activity/events
     → EIB normalizer (eib.py)
     → cdm_activity_event
     → republish ipe.activity.unified (future)
     → Unified dashboard / activity feed
```

**Ingress topics (as-is):** `ipe.demand.created`, `ipe.sync.completed`, `ipe.feasibility.scored`, `ipe.schedule.created`, `ipe.resolution.proposed`, `ipe.alert.raised` (see `EIB_INGRESS_TOPICS`).

### 12.5 API Response Envelope

All public APIs use `APIResponse`: `{ success, data, error, meta }` — `ipe_shared/schemas/common.py`.

---

## 13. Technical Architecture

### 13.1 Release 1 Topology (As-Is)

```
Browser (:8082) → Kong (:8000)
  → dpe-svc | fea-svc | cap-svc | res-svc | connector
  → PostgreSQL (:5433) + Redis (:6380)
  → Odoo (:8069) via host.docker.internal
Optional overlay: Keycloak, Vault, MinIO, Prometheus/Grafana
```

**Note (OQ-8):** Constitution Principle V lists `mat-svc` in R1; verify `docker-compose.release1.yml` for your deployment.

### 13.2 Full Stack (22 services)

See `infrastructure/docker/docker-compose.yml` and PRD §14.1 in comprehensive doc. Ports: dpe 8001, fea 8004, cap 8003, connector 8009, etc.

### 13.3 Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite 5, TypeScript, Tailwind |
| API | FastAPI, Python 3.14+, Pydantic v2 |
| Solver | Google OR-Tools CP-SAT (cap-svc) |
| DB | PostgreSQL 16, RLS, Alembic (migrations through **038**) |
| Gateway | Kong 3.x |
| K8s | Helm chart `helm/ipe/`; kind cluster `ipe-dev` |
| LLM | Ollama, OpenRouter, Anthropic (full) |

### 13.4 Core CDM Entities

| Table | Entity |
|-------|--------|
| `cdm_tenant` | Tenant + Odoo config JSONB |
| `cdm_user` | User + role |
| `cdm_manufacturing_order` | MO + feasibility_score |
| `cdm_bill_of_material` / `cdm_bom_line` | BOM |
| `cdm_routing_operation` | Routing |
| `cdm_resolution_scenario` | Resolution |
| `cdm_sync_run` | Sync audit |
| `cdm_activity_event` | Cross-tool activity (038) |
| `cdm_audit_log` | Append-only audit |

### 13.5 MDR Composite Formula

```
composite = 0.40 × BOM_coverage + 0.35 × routing_coverage + 0.25 × inventory_coverage
Gate threshold = 70% (MDR_QUALITY_GATE_THRESHOLD)
```

### 13.6 Scalability & Performance

| Operation | Target | As-is |
|-----------|--------|-------|
| Full Odoo sync | <60s | ~40–60s local |
| k6 SLO P95 | <500ms | 293ms |
| OR-Tools 3-MO | <90s compose | ✅; **timeout on kind** Gate 11 |
| Ingress proxy timeout | 300s | `values-dev.yaml` |

---

## 14. Competitive Context

### 14.1 Positioning

| Competitor | IPE aligns | IPE differentiates | IPE gaps |
|------------|------------|-------------------|----------|
| **Excel + Odoo MRP** | MO list, basic scheduling | Feasibility queue, resolution, OR-Tools | Change management |
| **Kinaxis RapidResponse** | Control tower concept | Faster deploy; mid-market price | Multi-site proven benchmarks |
| **SAP IBP** | S&OP, scenarios (v8 streams) | Odoo-native; MENA story | Live SAP connector |
| **o9 Solutions** | AI planning narrative | Integrated resolution workflow | Enterprise ML ops maturity |

### 14.2 Feature Comparison Matrix (Abbreviated)

| Capability | IPE | Kinaxis | SAP IBP | Excel+Odoo |
|------------|-----|---------|---------|------------|
| Feasibility pre-schedule scoring | ✅ | ✅ | ✅ | ❌ |
| Finite capacity OR-Tools | ✅ | ✅ | ✅ | Manual |
| Odoo bidirectional sync | ✅ | ❌ | Via integrator | Native ERP only |
| Resolution scenarios | ✅ | Partial | Partial | ❌ |
| Mid-market compose deploy | ✅ | ❌ | ❌ | ✅ |
| Live SAP connector | Scaffold | ✅ | ✅ | N/A |
| Unified cross-tool workspace | ✅ Sprint 7 | ✅ | ✅ | ❌ |

---

## 15. Data & Privacy

### 15.1 Data Collection & Storage

| Data class | Storage | Retention |
|------------|---------|-----------|
| Manufacturing master data | PostgreSQL CDM | Tenant lifetime |
| Odoo credentials | `tenant.config` encrypted | Until rotated |
| Audit events | `cdm_audit_log` | Append-only; export API |
| Activity events | `cdm_activity_event` | No auto-purge policy — **OQ-6** |
| Copilot sessions | nlp-svc / DB | Retention policy TBD — **OQ-6** |

### 15.2 GDPR / Compliance (As-Is)

| Requirement | Status |
|-------------|--------|
| DSAR export API | ✅ scaffold (`/dsar`) |
| Right to erasure | ⬜ Phase 5 (spec 015) |
| Tenant RLS | ✅ Must |
| PII in LLM prompts | PII stripper middleware (Tier 1) — POST-B production hardening |

### 15.3 Security Architecture

| Control | Implementation |
|---------|----------------|
| Auth | JWT HS256 (dev) / RS256 Keycloak (enterprise) |
| Transport | TLS via Kong :8443 (enterprise demo) |
| Secrets | Vault scaffold; env vars dev only |
| Rate limiting | Kong 300/min, 10000/hr |

---

## 16. Implementation Roadmap

### 16.1 Completed Phases

| Phase | Version / spec | Status |
|-------|----------------|--------|
| V5 convergence | v1.0.0 / 003 | ✅ |
| V6 AI-first | v6.0.0 / 004 | ✅ |
| Hub consolidation | v7.0.0 / 006 | ✅ |
| v8 U1–U8 | v8.2.0 / 007–010 | ✅ 32/32 |
| Release 1 | 013 | ✅ 14/14 compose |
| Release 2 | 014 | ✅ 5/5 |
| Enterprise P0–P2 | 015 | ✅ `v9.3.0-p2` |

### 16.2 In Progress

| Phase | Target | Blocker |
|-------|--------|---------|
| Enterprise P3 | `v9.4.0-p3` | Gate 11 **12/14** — OR-Tools on kind |
| Sprint 7 Tier 1 | `v9.5.0-s7` | Tier 2/3 stretch |
| Star Trans UAT | Customer sign-off | SOW + Odoo staging |

### 16.3 Upcoming

| Phase | Scope | Start condition |
|-------|-------|-----------------|
| Enterprise P4 GTM | Stripe live, tenant API, Terraform | After `v9.4.0-p3` |
| Enterprise P5 | SOC2, WCAG, live SAP/D365 | Post-GTM |
| Sprint 7 Tier 2 | Pattern discovery, anomaly alerts | After Tier 1 stable |
| Sprint 8 | Email-PM sync, integration marketplace design | Roadmap doc |

### 16.4 Milestone Dependencies

```
v9.4.0-p3 ──requires──► Gate 11 14/14
v10.0.0-e4 ──requires──► v9.4.0-p3 + Phase 4 tasks T170–T179
Star Trans UAT ──requires──► Customer IT + SOW (business)
```

---

## 17. Risks & Mitigation

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| R-01 | Gate 11 fails on K8s CPU | High | Blocks `v9.4.0-p3` | More cap-svc CPU; direct port-forward; or waiver OQ-9 |
| R-02 | Customer UAT delay | High | Revenue slip | Parallel demo env; SOW escalation |
| R-03 | Odoo version drift 17 vs 19 | Medium | Sync mapper breaks | Version-specific mapper tests; OQ-1 decision |
| R-04 | UI RBAC gap | Medium | Unauthorized actions | OQ-3; route guards Phase 5 |
| R-05 | Per-pod KMS breaks sync creds | Medium | Sync fails on K8s | Inline creds in sync body (implemented demo); shared KMS store |
| R-06 | Kafka-off R1 limits real-time | Low | Stale activity feed | POST `/activity/events` direct ingest |
| R-07 | Doc drift (service count) | Medium | Wrong deploy | OQ-8; reconcile compose + constitution |
| R-08 | Scope creep Sprint 7 | Medium | Tier 1 delay | Committed vs stretch tiers in spec 016 |

---

## 18. Assumptions & Constraints

### 18.1 Assumptions

| ID | Assumption |
|----|------------|
| A-01 | Star Trans runs Odoo on reachable host from Docker/kind |
| A-02 | Demo user `Ahmed@nour` / `admin` acceptable in non-prod only |
| A-03 | 8 GB VM sufficient for R1 compose |
| A-04 | Planners accept shadow-mode AI initially |
| A-05 | English primary; Arabic partial acceptable for R1 |

### 18.2 Technical Constraints

| ID | Constraint |
|----|------------|
| C-01 | RLS mandatory on all tenant tables (Constitution I) |
| C-02 | No Kafka in R1 Helm/compose profiles |
| C-03 | k6 SLO and stress profiles MUST NOT be combined (Constitution VI) |
| C-04 | Tag `v9.4.0-p3` requires Gates 6–11 PASS (Constitution VIII) |
| C-05 | Windows dev host; PowerShell scripts primary operator path |
| C-06 | Canonical codebase: `ipe/` not root `services/` |

### 18.3 Business Constraints

| ID | Constraint |
|----|------------|
| B-01 | First customer deploy = Compose not 22-service K8s |
| B-02 | SAP/D365 live connectors deferred until second customer |
| B-03 | NEXUS product line not funded in IPE program |

---

## 19. Task Tool & Cursor Integration

This section specifies how **Spec Kit task management** integrates with **Cursor IDE** for IPE development workflow.

### 19.1 System Components

| Component | Path | Purpose |
|-----------|------|---------|
| **Spec Kit root** | `E:\AISOP\.specify\` | Workflow registry, templates, feature pointer |
| **Active feature** | `.specify/feature.json` | Points to `ipe/specs/016-sprint7-ecosystem-cohesion` |
| **Constitution** | `ipe/.specify/memory/constitution.md` | Binding gates and principles |
| **Per-feature tasks** | `ipe/specs/{NNN}/tasks.md` | Checklist with IDs (T701, T150, etc.) |
| **Cursor workspace** | `E:\AISOP` (monorepo); canonical code `ipe/` | Agent execution environment |
| **AGENTS.md** | `ipe/AGENTS.md` | Workspace rules for agents |

### 19.2 Task Creation & Assignment Workflow

```
1. /speckit.specify  → creates/updates spec.md
2. /speckit.plan     → plan.md with phases
3. /speckit.tasks    → tasks.md with IDs, priority, status
4. /speckit.implement → agent executes tasks; updates status ✅/🔄/⬜
5. /speckit.converge → analyze gaps; update GATE-RESULTS, converge.md
```

| Step | Owner | Output artifact |
|------|-------|-----------------|
| Specify | PM + agent | `spec.md` with FR-* IDs |
| Tasks | PM + agent | `tasks.md` with traceable IDs |
| Implement | Dev + Cursor agent | Code + evidence files |
| Verify | QA / agent | `evidence/*.txt`, gate scripts |
| Close | PM | Git tag when constitution gates pass |

### 19.3 How Cursor Surfaces Incomplete Work

| Mechanism | Behavior |
|-----------|----------|
| **Active feature pointer** | `feature.json` → agent reads correct `specs/NNN/` |
| **tasks.md status columns** | Agent searches `⬜` and `🔄` rows for backlog |
| **Constitution Principle VIII** | Agent MUST NOT tag release if gates incomplete |
| **GATE-RESULTS-PHASE3.md** | Single source for gate PASS/FAIL |
| **READINESS.md** | Production blocker IDs (C-007, SEC-P0, etc.) |
| **ISSUES.md / GitHub** | `#12–#18` enterprise gate issues |
| **Todo tool (Cursor)** | Session-level task tracking during agent runs |
| **Evidence folder** | `specs/NNN/evidence/` — missing file = incomplete gate |

### 19.4 Integration Points with IPE Modules

| Module | Task traceability |
|--------|-------------------|
| Gate scripts | `tasks.md` T150–T166 map to `verify-gate*.ps1` |
| Demo scripts | T200–T201 regression |
| Migrations | T701 → `038_sprint7_activity_events.py` |
| Helm/K8s | T151–T157 → `helm/ipe/`, `scripts/k8s/` |
| Frontend hubs | T714 → `apps/web/src/features/hubs/` |

### 19.5 Acceptance Criteria — Task Tool + Cursor Integration

| ID | Criterion | Verification |
|----|-----------|--------------|
| TC-TASK-01 | Every implemented feature has task ID in `tasks.md` marked ✅ | Manual audit |
| TC-TASK-02 | `feature.json` active_feature matches current sprint spec | Read file |
| TC-TASK-03 | Gate evidence paths in tasks match files on disk | `audit-event-streams.ps1` pattern |
| TC-TASK-04 | Agent does not tag release when Constitution VIII blocks | Gate 11 partial → no `v9.4.0-p3` |
| TC-TASK-05 | Converge doc updated after phase close | `converge-phase3-close.md` exists |

### 19.6 Gap Resolution Protocol

```
1. Agent or QA identifies gap → document in analyze.md or ISSUES.md
2. Create task row in tasks.md with P0/P1 + owner
3. If gate-related → add to GATE-RESULTS with evidence path
4. Implement fix → run verify script → update evidence
5. Mark task ✅ only with command output or evidence file
6. For stakeholder decisions → add OQ-* to spec §1.6; do NOT assume
```

---

## 20. Full Integration Testing Requirements

### 20.1 Test Pyramid (As-Is)

| Layer | Scope | Command / artifact |
|-------|-------|-------------------|
| Unit | Per-service pytest | `uv run pytest services/*/tests` |
| Integration | v8 E2E | `tests/integration/test_v8_e2e.py` (5/5) |
| Connector | Odoo mapper | 16/16 tests |
| Demo regression | Full product | `run-full-demo.ps1` (32/32) |
| Release regression | R1 + R2 | `run-release1-integration-demo.ps1`, `run-release2-demo.ps1` |
| Enterprise gates | Security + obs | `verify-gate1.sh` … `verify-gate5.ps1` |
| K8s gates | Scale + R1 on K8s | `verify-gate6.ps1` … `verify-gate11.ps1` |
| Load | k6 SLO + stress | `k6-slo.js`, `k6-stress.js` **separate runs** |
| Chaos | Resilience | 6/6 documented `docs/chaos/` |
| E2E UI | Playwright foundation | `apps/web/e2e/` |
| Sprint 7 audit | EIB scaffolding | `scripts/sprint7/audit-event-streams.ps1` |

### 20.2 End-to-End Integration Scenarios (Must Pass for Release)

| ID | Scenario | Steps | Pass criteria |
|----|----------|-------|---------------|
| E2E-01 | Login → Control Tower | Auth → queue | 200; ≥1 MO |
| E2E-02 | Full Odoo sync | sync/run all | status=success |
| E2E-03 | Resolution → Schedule | scenarios → OR-Tools | ops scheduled |
| E2E-04 | Approve → Odoo | activate | Odoo dates updated |
| E2E-05 | MDR gate block | score <70 | cap-svc 503 |
| E2E-06 | R2 Outcomes | OTD + ROI APIs | 200 |
| E2E-07 | Unified workspace | /dashboard/unified | KPIs + activity |
| E2E-08 | Tenant isolation | cross-tenant read | 403 / empty |
| E2E-09 | K8s ingress R1 | 14 demo steps via `localhost` | **12/14** as-is; target 14/14 |
| E2E-10 | Compose–K8s parity | health + feasibility + resolution | Gate 8 3/3 |

### 20.3 Gate Testing Schedule (Enterprise)

| Gate | When | Owner | Evidence path |
|------|------|-------|---------------|
| 1–5 | Pre `v9.3.0-p2` | Platform | scripts/security, monitoring |
| 6–7 | Phase 3 start | Platform | `verify-gate6.ps1`, kind deploy |
| 8 | After DB seed | Platform | `gate8-parity.txt` |
| 9 | HPA overlay | Platform | `gate9-hpa.txt` |
| 10 | CI / local | Backend | `test_erp_scaffolds.py` |
| 11 | Pre `v9.4.0-p3` | Platform | `gate11-r1-k8s.txt` |

### 20.4 Task Tool & Cursor Test Cases

| ID | Test | Steps | Expected |
|----|------|-------|----------|
| TC-CUR-01 | Active feature resolution | Read `feature.json` | Points to 016 |
| TC-CUR-02 | Task completion traceability | T714 ✅ → file exists | `UnifiedWorkspacePage.tsx` |
| TC-CUR-03 | Gate blocked tag | Gate 11 partial | No `v9.4.0-p3` tag |
| TC-CUR-04 | Evidence regeneration | Run `verify-gate11.ps1` | Updates `gate11-r1-k8s.txt` |
| TC-CUR-05 | Sprint 7 audit | Run `audit-event-streams.ps1` | ≥6 checks pass |

### 20.5 Known Testing Gaps (Require Resolution)

| ID | Gap | Dependency | Target phase |
|----|-----|------------|--------------|
| TG-01 | Gate 11 schedule timeout on kind | cap-svc CPU / timeout | P3 close |
| TG-02 | Schemathesis in CI | Pipeline wiring | P5 |
| TG-03 | Chaos Mesh on K8s | Helm addon | P5 |
| TG-04 | Playwright full R1 path | CI stable stack | P4 |
| TG-05 | Formal MAPE baseline | Production data | Post-UAT |
| TG-06 | SCIM live Keycloak test | IdP staging | POST-B |
| TG-07 | Route-level RBAC UI tests | OQ-3 decision | P5 |

### 20.6 Regression Policy

| Trigger | Required runs |
|---------|---------------|
| Any PR touching `connector/` | Odoo tests + Gate 4 subset |
| Any PR touching `cap-svc/` | Schedule tests + demo step 10 |
| Any PR touching RLS migrations | Gate 3 + adversarial RLS tests |
| Pre-release tag | Full gate suite per Constitution VIII |
| Post-Sprint 7 change | `test_activity_eib.py` + unified API smoke |

---

## 21. Appendices

### Appendix A — Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0.0 | 2026 | V5 convergence — MDR, closed-loop schedule |
| v6.0.0 | 2026 | Tariff, CPM, War Room |
| v7.0.0 | 2026 | 6 hub consolidation |
| v8.2.0 | 2026 | U1–U8 streams; 32/32 demo |
| v9.3.0-p2 | 2026-07-04 | Enterprise gates 1–5; k6 |
| v9.4.0-p3 | Target | Phase 3 gates 6–11 — **blocked** |
| v9.5.0-s7 | In progress | Unified workspace, EIB, activity feed |
| PRD authoritative | 2026-07-07 | This document; supersedes comprehensive PRD snapshot |

### Appendix B — Glossary

| Term | Definition |
|------|------------|
| **APS** | Advanced Planning & Scheduling |
| **CDM** | Canonical Data Model (`cdm_*` tables) |
| **Control Tower** | Feasibility queue UI |
| **EIB** | Ecosystem Integration Bus — event normalization layer |
| **MDR** | Master Data Readiness — composite score gating schedule |
| **MO** | Manufacturing Order |
| **OTD** | On-Time Delivery |
| **R1 / R2** | Release 1 (Odoo customer) / Release 2 (growth) |
| **RLS** | Row-Level Security (PostgreSQL) |
| **Spec Kit** | Speckit workflow tooling under `.specify/` |
| **Star Trans** | Reference customer — electrical transformers |

### Appendix C — Key File References

| Artifact | Path |
|----------|------|
| This PRD | `ipe/docs/PRD-IPE-AUTHORITATIVE.md` |
| Readiness | `ipe/READINESS.md` |
| Constitution | `ipe/.specify/memory/constitution.md` |
| Gate results P3 | `ipe/docs/qa/GATE-RESULTS-PHASE3.md` |
| Spec 015 | `ipe/specs/015-enterprise-production-readiness/` |
| Spec 016 | `ipe/specs/016-sprint7-ecosystem-cohesion/` |
| R1 compose | `ipe/infrastructure/docker/docker-compose.release1.yml` |
| Web routes | `ipe/apps/web/src/app/router.tsx` |
| RBAC | `ipe/services/shared/ipe_shared/auth/rbac.py` |

### Appendix D — Entity Relationship (Core Planning)

```
cdm_tenant ─┬─ cdm_user
            ├─ cdm_product ── cdm_bill_of_material ── cdm_routing_operation
            ├─ cdm_manufacturing_order ── cdm_work_order
            ├─ cdm_resolution_scenario
            ├─ cdm_sync_run / cdm_data_quality_flag
            └─ cdm_activity_event (Sprint 7)
```

### Appendix E — Edge Cases & Error Handling

| Condition | System behavior |
|-----------|-----------------|
| Odoo unreachable | `ODOO_CONNECT_FAILED`; sync status failed |
| MDR < 70% | cap-svc 503 `MDR_QUALITY_GATE_FAILED` |
| Missing BOM for MO | MO skipped in sync; unscorable in queue |
| VERSION_CONFLICT on approve | 409; refresh schedule |
| Kafka disabled | Health `not_configured`; direct activity POST |
| Cross-tenant JWT | RLS returns empty / 403 |

### Appendix F — Configuration Options

| Variable | Values | Profile |
|----------|--------|---------|
| `VITE_RELEASE_PROFILE` | `full`, `release1` | Frontend |
| `AUTH_PROVIDER` | `local`, `keycloak` | Auth |
| `IPE_KAFKA_BOOTSTRAP_SERVERS` | `""` = disabled | R1/K8s dev |
| `VAULT_ENABLED` | `true`/`false` | Enterprise |
| `MDR_QUALITY_GATE_THRESHOLD` | default `70` | Scheduling |

### Appendix G — Stakeholder Decision Log

| ID | Decision needed | Status |
|----|-----------------|--------|
| OQ-1 | Odoo 17 vs 19 canonical | Open |
| OQ-3 | UI route RBAC | Open |
| OQ-8 | mat-svc in R1 compose | Open |
| OQ-9 | Gate 11 12/14 vs 14/14 for tag | Open |

---

*End of PRD — IPE Authoritative Specification v2026-07-07*

*Maintainers: Update this document when gates close, specs converge, or scope decisions (OQ-*) are resolved. Historical detail through 2026-07-04 remains in `docs/PRD-IPE-COMPREHENSIVE-AS-IS.md`.*
