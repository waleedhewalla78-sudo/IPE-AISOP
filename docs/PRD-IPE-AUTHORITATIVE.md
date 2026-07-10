# Product Requirements Document (PRD)

## Intelligent Planning Engine (IPE) — Authoritative Specification

| Field | Value |
|-------|-------|
| **Document ID** | PRD-IPE-AUTHORITATIVE-2026 |
| **Product** | **IPE** (Intelligent Planning Engine / AISOP IPE) — **not NEXUS Social** |
| **Document status** | **As-is development reference** — living platform, not idealized future state |
| **Last updated** | **2026-07-10** |
| **Workspace** | `E:\AISOP\ipe` |
| **Constitution** | `ipe/.specify/memory/constitution.md` **v1.2.4** |
| **Supersedes** | Prior draft of this file (2026-07-07); `docs/PRD-IPE-COMPREHENSIVE-AS-IS.md` (historical snapshot) |
| **Primary vertical** | Discrete manufacturing — electrical transformers (Star Trans, Egypt / MENA) |
| **Scope boundary** | **IPE only** — NEXUS Social is out of scope (one-line note in §1.4) |

> **How to read this document:** Capabilities are tagged **SHIPPED** / **PARTIAL** / **PLANNED** / **CUT** / **BLOCKED** / **UNKNOWN**. Items needing stakeholder input are **OQ-*** or listed in §18 / Appendix G. Do not treat inferred competitive claims as validated research.

### Status labeling convention

| Tag | Meaning |
|-----|---------|
| **SHIPPED** | In codebase and verified by tests, smoke, and/or demo evidence |
| **PARTIAL** | Implemented with named gaps |
| **PLANNED** | In spec/tasks; not built (or not verified) |
| **CUT** | Explicitly removed from scope (e.g. SAP B1 S12) |
| **BLOCKED** | Commercial / human / external dependency |
| **UNKNOWN** | Insufficient repo evidence — needs stakeholder input |

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
19. [Appendices](#19-appendices)

---

## 1. Product Vision & Scope

### 1.1 Vision Statement

> Enable discrete manufacturers to **see which manufacturing orders (MOs) are at risk before the shift starts**, **choose among structured resolution options**, and **publish feasible schedules** — grounded in live ERP master data (Odoo first), not manually maintained spreadsheets — with AI in **shadow mode** until trust is established.

### 1.2 Product Definition (As-Is)

| Attribute | Definition |
|-----------|------------|
| **Product name** | Intelligent Planning Engine (IPE) |
| **Product type** | AI-assisted Advanced Planning & Scheduling (APS) layer above ERP |
| **Architecture** | Microservices + React hub UI + Kong gateway; Kafka event mesh in **full** profile; batch sync in **Release 1/2** profiles |
| **Primary ERP** | Odoo 17–19 via XML-RPC (`connector`); mock-odoo for local E2E |
| **Reference customer** | Star Trans — Electrical Transformer Technology (Egypt / MENA) |
| **Buyer persona (R1)** | CEO / Operations Director — not IT steering committee |
| **Spec Kit program** | Features `000`–`018` under `ipe/specs/`; active rollup `005`; active R2 `018`; first-release plan `017` |

### 1.3 In Scope (As-Is — 2026-07-10)

#### Full profile (`VITE_RELEASE_PROFILE=full`)

| Area | Capabilities | Status |
|------|--------------|--------|
| **Unified Workspace** | Cross-tool KPIs + activity feed (`/workspace`) | **SHIPPED** (Sprint 7 / spec 016) |
| **Planning** | Control Tower, Resolution, Schedule, Demand, Scenarios | **SHIPPED** (depth varies by module) |
| **Command Center** | Executive, War Room, Outcomes, OTD, Cost of Chaos, Equipment, S&OP | **SHIPPED** / **PARTIAL** (some mock-backed UI) |
| **Supply Chain** | Supply planning, orders, procurement, tariff, SCN, inventory | **SHIPPED** (demo/full stack) |
| **AI & Governance** | Copilot, Design AI, AI Trust, MDR, Compliance, Quality, Sustainability | **SHIPPED** / **PARTIAL** |
| **Platform** | Admin, Odoo Config, Onboarding, MLOps, Ops | **SHIPPED** / **PARTIAL** |
| **Shop Floor** | Operator PWA | **SHIPPED** (full profile) |
| **Integrations** | Kafka mesh; LLM tiers; Odoo; SAP/D365 scaffolds | **PARTIAL** (scaffolds not live ERP) |

#### Release 1 profile (`VITE_RELEASE_PROFILE=release1`)

| Area | Capabilities | Status |
|------|--------------|--------|
| **Compose** | `db`, `redis`, `dpe-svc`, `fea-svc`, `res-svc`, `cap-svc`, `connector`, `kong`, `web-ui` (+ Keycloak/Vault/MinIO optional) | **SHIPPED** |
| **Planning** | Control Tower, Resolution, Schedule | **SHIPPED** |
| **Command** | Outcomes, OTD Analytics (Wave 1) | **SHIPPED** |
| **Platform** | Admin / Odoo config | **SHIPPED** |
| **Copilot** | Nav entry permitted (W1-01); live tools deepen in R2 | **PARTIAL** |
| **Integrations** | Odoo XML-RPC sync + activate; **Kafka omitted** | **SHIPPED** (local/mock); **BLOCKED** live staging |
| **Hidden** | Supply Chain hub, most AI Governance, Shop Floor, Demand, Scenarios | By design (Principle VII) |

#### Release 2 profile (`VITE_RELEASE_PROFILE=release2`)

| Area | Capabilities | Status |
|------|--------------|--------|
| **Compose adds** | `nlp-svc`, `demand-svc`, `scenario-svc`, `mock-odoo-api` | **SHIPPED** |
| **Planning adds** | Demand sensing (SES), Scenario workbench | **SHIPPED** |
| **Copilot** | Live planning tools + shadow mode | **SHIPPED** |
| **Arabic** | 8+ screens engineering | **PARTIAL** — native sign-off **BLOCKED** |
| **Ops** | Multi-tenant ops dashboard | **PARTIAL** (provision/quotas incomplete) |
| **SAP B1** | Sprint 12 | **CUT** |

### 1.4 Explicitly Out of Scope

| Item | Notes |
|------|-------|
| **NEXUS Social** / AI marketing platform | Separate product; not in `ipe/` program |
| Full MES replacement | Shop Floor is monitoring-light |
| Autonomous schedule without human approval | Default `autonomy_mode=shadow` |
| Production SAP S/4HANA / D365 connectors | Scaffold only until customer #2 |
| SAP B1 connector | **CUT** (`specs/018-phase2-release2/sprints/S12-CUT.md`) |
| Design AI as R1/R2 paid scope | Strategy cut unless contracted |
| Enterprise K8s as Star Trans R1 go-live requirement | Compose 8GB VM is R1 path |
| Gate 11 14/14 on kind without infra investment | **WON'T FIX** (#27); OQ-9 waiver accepted for `v9.4.0-p3` |

### 1.5 Version Evolution (with reasoning)

| Tag / milestone | Spec | Reasoning | Status |
|-----------------|------|-----------|--------|
| `v1.0.0` → `v6.x` | 000–004 | Foundation → AI-first closed loop | **SHIPPED** (historical) |
| `v7.0.0` | 006 | Hub consolidation (6 hubs) | **SHIPPED** |
| `v8.2.0` | 007–010 | U1–U8 streams + sustain/quality demo (32/32) | **SHIPPED** (code); tag exists |
| `v9.0.0-r1` / R1 | 013 | Customer #1 Odoo MENA slice | **SHIPPED** eng; UAT **BLOCKED** |
| `v9.1.0-r2` | 014 / 018 | R2 growth (Copilot, demand, scenarios, Arabic) | Eng ~92%; **G-R2-TAG HOLD** |
| `v9.2.0-p1` / `v9.3.0-p2` | 015 | Enterprise Gates 1–5 + Option B | **SHIPPED** |
| `v9.4.0-p3` | 015 / 017 | Phase 3 K8s gates 6–10 PASS; Gate 11 12/14 + OQ-9 waiver | **SHIPPED** @ `4629119` |
| Sprint 7 / 016 | 016 | Ecosystem cohesion (activity / workspace) | **SHIPPED** Tier 1 |
| Spec 017 Waves 1–3 | 017 | First release plan post-P3 | Wave 1 eng largely done; PH1 **BLOCKED** |
| Spec 018 | 018 | Phase 2 R2 program gates | In progress finalize |

### 1.6 Open Scope Decisions (Stakeholder Input)

| ID | Question | Impact |
|----|----------|--------|
| **OQ-1** | Canonical Odoo version for R1: **17** vs **19**? | Field mapping, install guide |
| **OQ-2** | Demo SQL overlay vs **Odoo-only** as production SoT? | Seed vs live sync |
| **OQ-3** | Enforce **route-level RBAC** in UI? | Any authenticated user reaches all routes today |
| **OQ-5** | Formal MAPE / triage-time baseline study? | G-01/G-02 unmeasured in production |
| **OQ-6** | Copilot session retention / GDPR erasure policy? | nlp-svc storage |
| **OQ-7** | Confirm R1 pricing **$18K–30K/yr** + **$12K–25K** implementation? | Commercial model |
| **OQ-8** | Include **mat-svc** in R1/R2 compose? | Constitution lists it; compose omits (URL-only in R2) |
| **OQ-9** | Gate 11 waiver — **accepted** (2026-07-10); confirm stakeholder names in waiver §6 | Release governance |
| **OQ-10** | Cut or implement **scenario promotion UI** (#40)? | R2 completeness |
| **OQ-11** | Cut or implement true **`stock.quant`** sync (C-15) vs safety_stock proxy? | Material gate honesty |
| **OQ-12** | Tag policy: push `v9.1.0-r2` vs cut `v9.1.1-r2` after Arabic sign-off? | Release management |

---

## 2. Problem Statement & Business Context

### 2.1 Problems IPE Solves

| Problem | User pain | IPE response (as-is) | Status |
|---------|-----------|----------------------|--------|
| **Invisible infeasibility** | Material/capacity conflicts found on shop floor | Feasibility G1–G5 scoring + Control Tower queue | **SHIPPED** |
| **Spreadsheet parallel to ERP** | Dual maintenance; stale MO dates | Odoo sync → CDM; write-back on approve | **SHIPPED** (local); **BLOCKED** staging |
| **Unstructured firefighting** | No comparable options | Resolution Center scenarios | **SHIPPED** |
| **Capacity blindness** | Overloaded WCs discovered late | Bottleneck map; OR-Tools CP-SAT | **SHIPPED** |
| **Leadership lag** | OTD after month-end | Outcomes, OTD dashboard, Cost of Chaos | **SHIPPED** / **PARTIAL** |
| **Tool fragmentation** | Context switching | Hub IA + Unified Workspace | **SHIPPED** |
| **AI distrust** | Black-box recommendations | Shadow autonomy; XAI; AI Trust | **PARTIAL** |
| **Data quality lies** | Misleading scores on incomplete BOM/routing | Unscorable flags; DQ badges | **SHIPPED** |

### 2.2 Target Market

| Segment | Characteristics | IPE fit |
|---------|-----------------|--------|
| **Primary (R1)** | Mid-market discrete on **Odoo** (MENA) | 8-service compose; feasibility-first |
| **Secondary (R2)** | Same + Copilot / demand / scenarios | `release2` profile |
| **Enterprise demo** | Prospects evaluating vs Kinaxis/SAP IBP | Full 22-service + 32/32 demo |
| **Not primary** | Fortune 500 multi-site SAP IBP replacement | No live SAP/D365 connector |

### 2.3 Business Context (Star Trans)

| Item | Value | Status |
|------|-------|--------|
| Customer | Star Trans (Egypt) | Reference |
| ERP | Odoo 17/19 compatible | **OQ-1** |
| Deployment | Diligent cloud VM **or** customer on-prem 8GB compose | **SHIPPED** docs |
| Commercial | SOW + staging Odoo | **BLOCKED** PH1-01 / PH1-02 |
| ROI window | Measurable within 90 days | Instrumented; not customer-proven |
| Competition in pitch | Excel + Odoo MRP | Constitution MENA constraints |

### 2.4 Competitive Positioning (Summary)

Sell R1 against **Excel + Odoo MRP**. Full-profile demos may reference Kinaxis / SAP IBP / o9 feature breadth — see §14 (**provisional**; no formal competitor research dossier in repo).

---

## 3. Goals & Success Metrics

### 3.1 Platform KPIs (Executive)

| Metric | Target | As-is (2026-07-10) | Evidence | Status |
|--------|--------|---------------------|----------|--------|
| Full demo checkpoints | 32/32 | Documented PASS | `scripts/run-full-demo.ps1`, READINESS | **SHIPPED** |
| R1 compose demo | 14/14 | PASS | `docs/demo-data/release1-integration-demo.txt` | **SHIPPED** |
| R1 K8s Gate 11 | ≥12/14 + waiver | 12/14 + OQ-9 | `gate11-k8s-demo.txt`, waiver | **SHIPPED** (waived) |
| R2 smoke | 15/15 | PASS | `docs/qa/release2-smoke-2026-07-10.txt` | **SHIPPED** |
| R2 demo | 7/7 | PASS | `docs/demo-data/release2-demo-g-r2-05.txt` | **SHIPPED** |
| Backend pytest | Green | **860/860** (018 TEST-RESULTS) | Spec 018 | **SHIPPED** |
| Frontend Vitest | Green | **41/41** | Spec 018 | **SHIPPED** |
| Enterprise Gates 1–5 | PASS | `v9.3.0-p2` | Spec 015 | **SHIPPED** |
| Enterprise Gates 6–10 | PASS | GATE-RESULTS-PHASE3 | Spec 015 | **SHIPPED** |
| k6 SLO P95 | <500ms | **293ms**, 0% err | `PERFORMANCE-BASELINE-v9.1.0.md` | **SHIPPED** |
| Star Trans UAT | Signed | Open | PH1-01/02 | **BLOCKED** |
| Arabic native QA | Signed | Eng done | `docs/qa/arabic-qa-r2.md` | **BLOCKED** |
| G-R2-TAG | `v9.1.0-r2` / `v9.1.1-r2` | HOLD | GATES.md | **BLOCKED** |

### 3.2 Product Outcome Goals

| ID | Goal | Acceptance criteria | Status |
|----|------|---------------------|--------|
| G-01 | Planners triage at-risk MOs before shift | Top 3 at-risk MOs in ≤5 min | **SHIPPED** (demo); **UNKNOWN** production |
| G-02 | Structured resolution | ≥1 comparable scenario per at-risk MO | **SHIPPED** |
| G-03 | Feasible schedule published | Approve persists CDM; Odoo dates match on activate | **SHIPPED** local |
| G-04 | Data quality honesty | Unscorable MOs never silent-scored | **SHIPPED** |
| G-05 | 90-day ROI | Adoption + 2+ MOs saved + OTD trend | **PARTIAL** (instrumented) |
| G-06 | Arabic planner path | CT + Resolution + nav + alerts | **PARTIAL** (sign-off open) |

### 3.3 Spec-Aligned Goal Sets

#### V5 Convergence (spec 003)

| ID | Goal | Status |
|----|------|--------|
| V5-G1 | Closed-loop planning (approve persists <60s) | **SHIPPED** |
| V5-G2 | Planner trust (XAI) | **PARTIAL** (UI; no formal study — OQ-5) |
| V5-G3 | MDR gate (composite <70% blocks) | **SHIPPED** |
| V5-G4 | War Room ≥3 mitigations | **SHIPPED** |
| V5-G5 | Financial clarity on scenarios | **SHIPPED** |

#### Release 1 (spec 013)

| ID | Metric | Status |
|----|--------|--------|
| R1-M1 | MOs from Odoo in Control Tower | **SHIPPED** mock/local; **BLOCKED** staging |
| R1-M2 | Sync success >95% | **SHIPPED** local |
| R1-M3 | Post-sync feasibility non-null | **SHIPPED** |
| R1-M7 | Write-back dates match | **SHIPPED** Gate 4 path |
| R1-M6 | Customer sign-off | **BLOCKED** |

#### Spec 017 / 018 program gates

| Gate | Criteria | Status |
|------|----------|--------|
| **G-R2-01** | `release2-smoke.ps1` 15/15 | **PASS** |
| **G-R2-02** | Copilot live tools | **PASS** |
| **G-R2-03** | Wave 1 W1-03–08 eng | **PASS (eng)**; live Odoo = PH1-02 |
| **G-R2-04** | Arabic 8+ screens | **PARTIAL** — native sign-off open |
| **G-R2-05** | `run-release2-demo.ps1` 7/7 | **PASS** |
| **G-R2-TAG** | Tag on green matrix | **HOLD** |

---

## 4. User Personas & Workflows

### 4.1 Persona Catalog

| Persona | RBAC role | Primary goals | Typical hubs | Status |
|---------|-----------|---------------|--------------|--------|
| **Production Planner** | `planner` | Triage, resolve, schedule | Workspace, Planning, Copilot | Primary |
| **Plant Manager** | `manager` | Approve schedules, trade-offs | Planning, Command | Primary |
| **Shop Supervisor** | `supervisor` | Monitor disruptions | Command, Shop Floor | Full profile |
| **Shop Operator** | `operator` | Execute work orders | Shop Floor | Full profile |
| **Executive / VP Ops** | `executive` | OTD, margin, chaos cost | Command, Workspace | Primary |
| **Procurement Analyst** | `procurement` | Supplier risk, spend | Supply Chain | Full / R2 stretch |
| **System Administrator** | `admin` | Tenant, Odoo, autonomy, ops | Platform | Primary |
| **Auditor** | `auditor` | Read-only compliance | Compliance | Enterprise |
| **Demo Engineer** | `admin` | 32/32, R1/R2 demos | All + scripts | Internal |

**Known gap (OQ-3):** UI does **not** enforce route-level RBAC — API RBAC is the enforcement layer.

### 4.2 Planner Daily Journey (Release 1 / 2)

```
Login (local JWT or Keycloak)
  → /workspace (KPIs + activity)
  → /planning/control-tower (queue by feasibility ASC)
       ├─ unscorable → fix DQ / Admin sync
       ├─ score < 70 → /planning/resolution → compare scenarios
       │                    └─→ /planning/schedule → Approve → Odoo activate
       └─ score ≥ 70 → Schedule directly → Approve
  → [R2] /planning/demand | /planning/scenarios | /ai-governance/copilot
  → [R2] /command-center/otd-analytics | /command-center/outcomes
```

### 4.3 Decision Tree — MO Triage

```
MO in feasibility queue?
├─ NO → Run Odoo sync (Admin / scheduler) OR seed / mock-odoo
└─ YES → data_quality / unscorable?
    ├─ YES → Fix BOM/routing/WC in Odoo → re-sync → rescore
    └─ NO → feasibility_score?
         ├─ < 70 → Resolution scenarios → pick → Schedule (if MDR ≥70%)
         ├─ 70–89 → Schedule with caution / suggest mode
         └─ ≥ 90 (+ autonomous) → auto-confirm path (shadow default: still queue)
              └─ Approve → POST /sync/odoo/activate
                   ├─ success → done
                   └─ SYNC_CONFLICT / MATERIAL_CONFLICT → Resolution
```

### 4.4 Administrator Journey — Odoo Setup

```
/platform/odoo-config (or Admin ERP tab)
  → Enter URL, DB, username, password
  → Test connection (<5s target — W1-04)
  → Save (tenant config / encrypted)
  → POST /api/v1/sync/run
  → Verify /sync/status + Control Tower queue + DQ flags
```

### 4.5 Executive Journey — Morning Brief

```
/workspace → review unified KPIs
  → /command-center/otd-analytics (5 KPIs)
  → /command-center/outcomes (ROI / baseline)
  → Drill to Control Tower if OTD down
```

---

## 5. Use Cases

### 5.1 Use Case Index

| ID | Name | Actor | Profile | Status |
|----|------|-------|---------|--------|
| UC-01 | Daily production health triage | Planner | R1/R2/Full | **SHIPPED** |
| UC-02 | Constraint resolution | Planner, Manager | R1/R2/Full | **SHIPPED** |
| UC-03 | Finite-capacity scheduling | Planner | R1/R2/Full | **SHIPPED** |
| UC-04 | Excel project plan import | Planner | R1/Full | **SHIPPED** |
| UC-05 | Demand sensing (SES) | Planner | R2/Full | **SHIPPED** |
| UC-06 | Scenario simulate/compare | Planner | R2/Full | **SHIPPED** |
| UC-07 | Scenario promotion to live plan | Planner | R2 | **PLANNED** (#40) |
| UC-08 | Supply network visibility | Planner, Exec | Full | **SHIPPED** |
| UC-09 | Copilot NL planning query | Planner | R2/Full | **SHIPPED** |
| UC-10 | Executive disruption review | Executive | Full/R1 partial | **SHIPPED** |
| UC-11 | Shop floor execution | Operator | Full | **SHIPPED** |
| UC-12 | Odoo ERP sync | Admin, System | R1/R2 | **SHIPPED** mock; **BLOCKED** staging |
| UC-13 | Schedule write-back | Planner | R1/R2 | **SHIPPED** |
| UC-14 | Post-sync rescore | System | R1/R2 | **SHIPPED** |
| UC-15 | Unified workspace review | All | Full/R1 | **SHIPPED** |
| UC-16 | OTD baseline & trend | Manager | R1/R2 | **SHIPPED** |
| UC-17 | Tenant provision (self-service) | Admin/Ops | Enterprise/R2 | **PARTIAL** (#37/#25) |
| UC-18 | Predictive delay (XGBoost+SHAP) | Planner | Wave 2 | **PLANNED** / **UNKNOWN** (#42) |
| UC-19 | NL schedule change | Planner | Wave 3 | **PLANNED** (#43–#44) |
| UC-20 | Automated supplier comms | System | Wave 3 | **PLANNED** (#45–#46) |

### 5.2 UC-01 — Daily Production Health Triage

| Attribute | Detail |
|-----------|--------|
| **Actor** | Planner |
| **Preconditions** | Authenticated JWT; tenant set; MOs in CDM; fea-svc healthy |
| **Main flow** | Login → Control Tower → `GET /feasibility/kpis` + `GET /feasibility/queue` → sort by score ASC → open Resolve |
| **Alternatives** | WebSocket refresh; manual sync if stale; Copilot “show at-risk MOs” (R2) |
| **Edge** | Empty queue; `unscorable=true`; Kong 401 if AUTH_MODE mismatch |
| **Success** | Top 3 at-risk MOs identified in **≤5 minutes** |

### 5.3 UC-02 — Constraint Resolution

| Attribute | Detail |
|-----------|--------|
| **Actor** | Planner / Manager |
| **Preconditions** | MO with score <70 or primary_constraint set |
| **Main flow** | Resolution Center → list constraints → generate/compare scenarios → select → navigate Schedule |
| **Alt** | Auto-propose post-sync (FR-R1-14 partial) |
| **Success** | Scenario selected with cost/delivery/risk visible; approval RBAC enforced |

### 5.4 UC-03 — Finite-Capacity Scheduling

| Attribute | Detail |
|-----------|--------|
| **Actor** | Planner |
| **Preconditions** | MDR composite ≥70% (else 503); WC + routing present |
| **Main flow** | `POST /capacity/schedule` (OR-Tools CP-SAT) → review Gantt → Approve → persist CDM |
| **Edge** | Solver timeout (compose ~30–90s; K8s Gate 11 OR-Tools issues waived) |
| **Success** | Assignments with no-overlap; approve survives refresh |

### 5.5 UC-12 — Odoo ERP Sync

| Attribute | Detail |
|-----------|--------|
| **Actor** | Admin / scheduler |
| **Preconditions** | `erp_type=odoo`; creds; Odoo or mock-odoo reachable |
| **Main flow** | 15-min job OR `POST /sync/run` → upsert products/WC/BOM/MO → `cdm_sync_run` → rescore |
| **Edge** | Field drift v17/v19; MO without BOM skipped + DQ flag |
| **Success** | `status=success` or `rescored`; MO count >0; last-synced visible in UI |

### 5.6 UC-13 — Schedule Write-Back

| Attribute | Detail |
|-----------|--------|
| **Main flow** | Approve → `POST /sync/odoo/activate` → XML-RPC update Odoo MO dates |
| **Conflict policy** | Odoo wins master data; IPE wins approved schedule until next sync flags conflict |
| **Success** | Odoo dates match IPE; no unresolved SYNC_CONFLICT |

### 5.7 UC-09 — Copilot Live Query (R2)

| Attribute | Detail |
|-----------|--------|
| **Preconditions** | nlp-svc up; AUTH; optional LLM keys (degrades gracefully) |
| **Main flow** | `/ai-governance/copilot` → query → tools hit live feasibility/schedule APIs → response + sources |
| **Success** | Unauthenticated → 401; authenticated tool path returns structured answer (smoke 12/12 W1-02) |

---

## 6. Functional Requirements

### 6.1 Authentication & Tenancy

| ID | Requirement | Acceptance | Priority | Status |
|----|-------------|------------|----------|--------|
| FR-AUTH-01 | JWT local (`AUTH_MODE=local`) or Keycloak OIDC | 401 on bad/missing token | Must | **SHIPPED** (dual-mode) |
| FR-AUTH-02 | Tenant on every API call | JWT claim; Kong strips client `X-Tenant-ID` | Must | **SHIPPED** |
| FR-AUTH-03 | PostgreSQL RLS per `tenant_id` | Cross-tenant blocked | Must | **SHIPPED** (legacy gaps waived via ADR) |
| FR-AUTH-04 | RBAC on state-changing APIs | 403 if role insufficient | Must | **SHIPPED** |
| FR-AUTH-05 | Zero open endpoints except health/ready/metrics | Scanner / constitution | Must | **SHIPPED** |
| FR-AUTH-06 | Rate limiting (Kong) | 429 under stress profile | Must | **SHIPPED** |

### 6.2 Planning Hub

| ID | Requirement | Acceptance | Priority | Status |
|----|-------------|------------|----------|--------|
| FR-PLN-01 | Feasibility queue | ≥1 MO when data present | Must | **SHIPPED** |
| FR-PLN-02 | KPI cards from fea-svc | `/feasibility/kpis` | Must | **SHIPPED** |
| FR-PLN-03 | Resolution scenarios | ≥1 per at-risk MO | Must | **SHIPPED** |
| FR-PLN-04 | OR-Tools schedule | Valid no-overlap assignments | Must | **SHIPPED** |
| FR-PLN-05 | Approve persists CDM | Survives refresh | Must | **SHIPPED** |
| FR-PLN-06 | MDR gate before schedule | composite ≥70% or 503 | Must | **SHIPPED** |
| FR-PLN-07 | Sync status bar (R1) | `/sync/status` | Must | **SHIPPED** |
| FR-PLN-08 | Excel upload | .xlsx validation | Should | **SHIPPED** |
| FR-PLN-09 | Demand SES forecast (R2) | Forecast + intervals API | Should | **SHIPPED** |
| FR-PLN-10 | Scenario simulate/compare (R2) | scenario-svc | Should | **SHIPPED** |
| FR-PLN-11 | Scenario promotion UI | Promote to live plan | Should | **PLANNED** (#40) |

**Business rules:** BR-PLN-01 shadow autonomy — no silent auto-apply. BR-PLN-02 unscorable MOs excluded from auto-confirm. BR-PLN-03 Odoo wins master data on conflict.

### 6.3 Odoo Sync (Release 1 — FR-R1-*)

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| FR-R1-01 | MO upsert from `mrp.production` | **SHIPPED** | |
| FR-R1-02 | BOM + BOM lines + routing | **SHIPPED** | |
| FR-R1-03 | Work center sync | **SHIPPED** | |
| FR-R1-04 | Product update path | **SHIPPED** | |
| FR-R1-05 | Stock / material availability | **PARTIAL** | Spec 013 claims safety_stock proxy; **C-15** still open for true `stock.quant` — **OQ-11** |
| FR-R1-06 | Scheduled sync 15 min | **SHIPPED** | |
| FR-R1-07 | Sync run log | **SHIPPED** | `cdm_sync_run` |
| FR-R1-08 | Data quality flags | **SHIPPED** | |
| FR-R1-09 | Conflict detection | **SHIPPED** | |
| FR-R1-10 | Activate write-back | **SHIPPED** | |
| FR-R1-11 | Odoo install guide | **SHIPPED** | `docs/integration/` |
| FR-R1-12 | Feasibility skip flagged MOs | **SHIPPED** | |
| FR-R1-13 | Queue with DQ flags | **SHIPPED** | |
| FR-R1-14 | Resolution scenarios | **PARTIAL** | Seed OK; auto-gen post-sync gap |
| FR-R1-15 | Schedule approve → Odoo | **SHIPPED** | |
| FR-R1-16 | OTD baseline capture | **SHIPPED** | Eng; verify via Kong |
| FR-R1-17–19 | Sync widget / DQ / conflict badge | **SHIPPED** | |
| FR-R1-20–21 | i18n ar/en + switcher | **PARTIAL** | Eng; native QA open |
| FR-R1-22 | Hide POST-R1 hubs | **SHIPPED** | `releaseProfile.ts` |
| FR-R1-23–26 | Ops docs + compose | **SHIPPED** | |

### 6.4 Spec 017 Wave Features

| ID | Feature | Status |
|----|---------|--------|
| FR-017-P0-01…06 | Phase 0 stabilization / `v9.4.0-p3` | **SHIPPED** |
| FR-017-PH1-01 | Signed SOW | **BLOCKED** |
| FR-017-PH1-02 | Odoo staging | **BLOCKED** |
| FR-017-W1-01/02 | Copilot R1 nav + smoke | **SHIPPED** |
| FR-017-W1-03…06 | Odoo Config v2 | **SHIPPED** eng (verify E2E) |
| FR-017-W1-07/08 | OTD API + dashboard | **SHIPPED** |
| FR-017-W2-01 | Tenant provision API | **PARTIAL** (#37) |
| FR-017-W2-02 | Quotas/metering | **PARTIAL** (#38) |
| FR-017-W2-03/04 | Scenario + demand | **SHIPPED** (promotion UI open) |
| FR-017-W2-06 | Predictive delay ML | **PLANNED** (#42) |
| FR-017-W3-* | NL schedule + supplier comms | **PLANNED** (#43–#46) |

### 6.5 Sprint 7 Ecosystem Cohesion (spec 016)

| ID | Requirement | Status |
|----|-------------|--------|
| FR-S7-01 | Unified dashboard API | **SHIPPED** |
| FR-S7-02 | Activity feed | **SHIPPED** |
| FR-S7-03 | Activity ingest (Kafka-off path) | **SHIPPED** |
| FR-S7-04 | EIB → `cdm_activity_event` (mig 038) | **SHIPPED** |
| FR-S7-05 | Pattern discovery | **PLANNED** |
| FR-S7-06 | Email↔PM Graph sync | Deferred |

### 6.6 Feasibility Scoring Rules

| Gate | Weight | Input | Rule |
|------|--------|-------|------|
| G1 Demand | 5% | Demand classification | Low weight context |
| G2 BOM | 5% | BOM completeness | Missing → unscorable / low |
| G3 Material | 35% | pATP / inventory | Dominant material risk |
| G4 Capacity | 30% | WC utilization | Real scoring when routing present |
| G5 Labor | 25% | Operator absence | Real scoring when operators present |

| Score band | `action_taken` |
|------------|----------------|
| ≥90 + autonomous | `auto_confirmed` |
| ≥70 | `queued_for_planner` |
| <70 | `routed_to_resolution` |

---

## 7. Feature Specifications

| Feature | Purpose | Benefit | Acceptance criteria | Deps | Priority | Version history | Status |
|---------|---------|---------|---------------------|------|----------|-----------------|--------|
| **Control Tower** | MO risk queue + KPIs | See risk before shift | Queue + KPIs + Resolve; WS optional | fea-svc | P0 | v1→v9 | **SHIPPED** |
| **Resolution Center** | Scenario trade-offs | Structured firefighting | Cost/delivery/risk cards; approve RBAC | res-svc | P0 | v1→v9 | **SHIPPED** |
| **Schedule + OR-Tools** | Finite capacity | Feasible plan | No-overlap; approve persist | cap-svc, MDR | P0 | v1→v9 | **SHIPPED** |
| **MDR Gate** | Data readiness | Block bad solves | <70% → 503 | dpe/cap | P0 | v1 | **SHIPPED** |
| **Odoo sync engine** | Live ERP ingest | SoT from factory | Sync run + rescore | connector | P0 R1 | spec 013 | **SHIPPED** |
| **Activate write-back** | Close loop | ERP dates updated | Activate API success | connector | P0 R1 | spec 013 | **SHIPPED** |
| **Unified Workspace** | Cross-tool briefing | Less context switch | `/workspace` + unified API | dpe | P1 | spec 016 | **SHIPPED** |
| **Hub consolidation** | IA | 6 hubs + redirects | Sidebar matches profile | web | P0 | v7 | **SHIPPED** |
| **Outcomes / OTD** | ROI story | Baseline + trend | 5 KPIs; filters | dpe | P0 R2 | 014/017 | **SHIPPED** |
| **Copilot live tools** | NL assist | Faster triage | Tools + 401 smoke | nlp-svc | P1 R2 | 017/018 | **SHIPPED** |
| **Demand SES** | Sensing | Forecast intervals | MAPE endpoint | demand-svc | P1 R2 | 018 S3 | **SHIPPED** |
| **Scenario workbench** | What-if | Compare plans | Simulate + compare | scenario-svc | P1 R2 | 018 S4 | **SHIPPED** |
| **Scenario promotion** | Commit what-if | Promote to live | UI + API | scenario-svc | P2 | #40 | **PLANNED** |
| **Arabic 8+ screens** | MENA UX | Planner in AR | Native sign-off | i18n | P0 | 018 S5 | **PARTIAL** |
| **Ops dashboard** | Multi-tenant health | Ops visibility | Admin-only APIs | dpe | P2 | 018 S8 | **PARTIAL** |
| **Tenant provision** | Self-service | Scale customers | One-call provision | dpe | P2 | #37/#25 | **PARTIAL** |
| **Keycloak SSO** | Enterprise IdP | SSO | Gate 5 / Option B | keycloak | P1 Ent | 011/015 | **PARTIAL** (R2 container often unhealthy; local JWT path) |
| **Helm / K8s R1** | Scale path | Gates 6–10 | kind deploy | helm | P1 Ent | 015 | **SHIPPED** |
| **SAP/D365 scaffold** | Future ERP | Registry no-op | Gate 10 imports | connector | P3 | 015 | **SHIPPED** scaffold |
| **SAP B1** | ERP #2 | — | — | — | — | S12 | **CUT** |
| **Predictive delay ML** | Delay risk | SHAP explain | AUC>0.80 | ml/del | P2 | #42 | **PLANNED** |
| **NL schedule change** | Voice/text move MO | Preview+execute | >90% intent | nlp | P3 | #43–44 | **PLANNED** |
| **Supplier comms** | Auto email | Audit trail | Rule+template | alert | P3 | #45–46 | **PLANNED** |
| **Design AI** | Design assist | Demo | CP28 | full | Demo | v8 | **SHIPPED** demo; **CUT** paid R1 |
| **Stripe billing** | SaaS | Metered license | Sandbox | billing | P4 | 015 Ph4 | **PLANNED** scaffold |

---

## 8. Business Scenarios

### BS-01 — Star Trans Full Demo (Copper Delay)

| Step | Action | Metric |
|------|--------|--------|
| 1 | Planner sees low-feasibility MO | <5 min ID |
| 2 | Resolution scenarios compared | Scenario selected |
| 3 | Re-schedule + approve | Gantt + CDM persist |
| 4 | Executive War Room / Cost of Chaos | $ impact shown |

**Outcome:** 32/32 demo path — **SHIPPED**.  
**Customer production:** **BLOCKED** on SOW/staging.

### BS-02 — R1 Morning Triage on Odoo

| Step | Action | Metric |
|------|--------|--------|
| 1 | Overnight 15-min sync | `cdm_sync_run` success |
| 2 | Workspace + Control Tower | MOs scored |
| 3 | Resolution + Schedule + activate | Odoo dates updated |

**Outcome:** Local/mock **SHIPPED**; live staging **BLOCKED** (PH1-02).

### BS-03 — R2 Demo (G-R2-05)

| Step | Action | Metric |
|------|--------|--------|
| 1 | Outcomes / OTD | API 200 |
| 2 | mock-odoo sync → rescore | `rescored` |
| 3 | Copilot tool query | Structured response |
| 4 | Kind health | 8/8 pods |

**Evidence:** `docs/demo-data/release2-demo-g-r2-05.txt` — **PASS 7/7**.

### BS-04 — Executive Cross-Tool Briefing (Sprint 7)

| Step | Action | Metric |
|------|--------|--------|
| 1 | Open `/workspace` | Unified KPIs <3s |
| 2 | Activity feed | Events present or empty-OK |
| 3 | Drill to War Room / CT | Counts consistent |

**Status:** Tier 1 **SHIPPED**; Tier 2 insights **PLANNED**.

### BS-05 — Arabic Planner Path

| Step | Action | Metric |
|------|--------|--------|
| 1 | Switch language to AR | RTL layout |
| 2 | Triage → Resolve → Approve | Strings present |
| 3 | Native reviewer sign-off | Signature in `arabic-qa-r2.md` |

**Status:** Eng **PARTIAL**; human **BLOCKED**.

---

## 9. User Interface & Navigation

### 9.1 Information Architecture (actual `apps/web` routes)

Source: `apps/web/src/app/router.tsx`, `apps/web/src/lib/constants.ts`, `releaseProfile.ts`.

```
/login
/workspace                          → UnifiedWorkspacePage
/planning
  /dashboard | /demand | /scenarios | /control-tower | /resolution | /schedule
/command-center
  /dashboard | /war-room | /executive | /outcomes | /equipment
  /cost-of-chaos | /otd-analytics | /sop-report
/supply-chain
  /supply-planning | /orders | /procurement | /tariff | /scn-portal | /inventory
/ai-governance
  /copilot | /design-ai | /ai-trust | /mdr | /compliance | /quality | /sustainability
/platform
  /admin | /odoo-config | /onboarding | /ml-ops | /ops
/shop-floor
+ legacy redirects: /control-tower, /schedule, /resolution[-center], /copilot, …
```

### 9.2 Release Profile Visibility

| Hub / tab | `full` | `release1` | `release2` |
|-----------|--------|------------|------------|
| Workspace | ✅ | ✅ | ✅ |
| Planning: CT / Resolution / Schedule | ✅ | ✅ | ✅ |
| Planning: Demand / Scenarios | ✅ | ❌ | ✅ |
| Planning: Dashboard | ✅ | ❌ | ❌* |
| Command: Outcomes / OTD | ✅ | ✅ | ✅ |
| Command: War Room / Executive / … | ✅ | ❌ | ❌* |
| Supply Chain | ✅ | ❌ | ❌ |
| AI Governance (except Copilot path) | ✅ | ❌ | ❌* |
| Copilot | ✅ | ✅ (W1-01) | ✅ |
| Platform Admin / Odoo | ✅ | ✅ | ✅ |
| Shop Floor | ✅ | ❌ | ❌ |

\*Exact tab filters follow `IS_RELEASE1` / `SHOW_R2_PLANNING_TABS` in hub components — verify before customer demos.

### 9.3 Screen Catalog (field types — representative)

| Screen | Route | Key fields / widgets | Status |
|--------|-------|----------------------|--------|
| Login | `/login` | email/password; language | **SHIPPED** |
| Workspace | `/workspace` | KPI cards, activity feed, pending actions | **SHIPPED** |
| Control Tower | `/planning/control-tower` | KPI cards, MO table (score colors), bottleneck bars, sync bar, Resolve CTA | **SHIPPED** |
| Resolution | `/planning/resolution` | Constraint list, scenario cards (cost/OTD/risk) | **SHIPPED** |
| Schedule | `/planning/schedule` | Gantt, solver status, Approve, Excel upload | **SHIPPED** |
| Demand | `/planning/demand` | Forecast chart, intervals, accuracy | **SHIPPED** R2 |
| Scenarios | `/planning/scenarios` | Simulate, compare; **no promote** | **PARTIAL** |
| OTD | `/command-center/otd-analytics` | 5 KPIs, filters, charts | **SHIPPED** |
| Outcomes | `/command-center/outcomes` | Baseline / ROI widgets | **SHIPPED** |
| Copilot | `/ai-governance/copilot` | Chat, sources, tools | **SHIPPED** |
| Odoo Config | `/platform/odoo-config` | URL/DB/user/pass, test, history | **SHIPPED** |
| Ops | `/platform/ops` | Tenant health | **PARTIAL** |
| Executive | `/command-center/executive` | P&L, S&OP gap, what-if | **SHIPPED** / mock gaps **UNKNOWN** |
| War Room | `/command-center/war-room` | Disruptions, mitigations | **SHIPPED** |

### 9.4 Navigation Rules

| Rule | Detail |
|------|--------|
| Auth gate | `ProtectedRoute` / JWT expiry |
| Default landing | `/` → `/workspace` |
| Unknown routes | Redirect to planning dashboard |
| i18n | `locales/en.json`, `locales/ar.json` |
| Profile | `VITE_RELEASE_PROFILE` |

---

## 10. Authorization, Roles & Permissions

### 10.1 Roles (`ipe_shared.auth.rbac.Role`)

| Role | Permissions (set) |
|------|-------------------|
| `admin` | read, write, approve, admin, delete, run_solver, cost_optimize, manage_users |
| `planner` | read, write, approve, run_solver, cost_optimize, view_copilot, run_scenario |
| `manager` | read, write, approve, run_solver, cost_optimize |
| `supervisor` | read, acknowledge_disruption, view_schedule, view_copilot |
| `auditor` | read, view_audit_logs, view_kpis, view_scenarios |
| `operator` | read, write_own |
| `executive` | read, view_kpis |
| `procurement` | read, write, view_kpis |

### 10.2 Enforcement Matrix

| Layer | Behavior | Status |
|-------|----------|--------|
| Kong JWT | Validates token; injects tenant; strips client tenant header | **SHIPPED** |
| FastAPI `require_roles` | State-changing endpoints | **SHIPPED** |
| FastAPI `require_any_permission` | Fine-grained | **SHIPPED** |
| PostgreSQL RLS | `app.current_tenant` / `set_config` | **SHIPPED** |
| UI route RBAC | Not enforced | **PARTIAL** — **OQ-3** |
| Keycloak realm roles | Mapped when `AUTH_MODE=keycloak` | **PARTIAL** (health issues in R2) |

### 10.3 API Enforcement Examples

| Endpoint | Roles | Action |
|----------|-------|--------|
| `POST /capacity/schedule` | planner, admin, manager | run_solver |
| `POST /resolution/approve` | planner, admin, manager | approve |
| `POST /feasibility/auto-confirm` | planner, admin | write |
| `POST /copilot/query` | planner, admin (+ view_copilot) | read/write |
| Admin / ops APIs | admin | admin |

### 10.4 Data Visibility

| Principle | Rule |
|-----------|------|
| Tenant isolation | All CDM queries under tenant RLS |
| Cross-tenant | Forbidden except platform ops with explicit break-glass (**UNKNOWN** if implemented) |
| Audit | Append-only `cdm_audit_log` (migration 021 immutability) |

---

## 11. Reports & Dashboards

### 11.1 Dashboard Catalog

| Dashboard | Route / API | Audience | Status |
|-----------|-------------|----------|--------|
| Unified Workspace | `/workspace`, `/api/v1/dashboard/unified` | All | **SHIPPED** |
| Control Tower KPIs | fea `/feasibility/kpis` | Planner | **SHIPPED** |
| Executive | `/command-center/executive` | Exec | **SHIPPED** / **PARTIAL** |
| OTD Analytics | `/command-center/otd-analytics` | Manager | **SHIPPED** |
| Outcomes | `/command-center/outcomes` | Exec/Manager | **SHIPPED** |
| Cost of Chaos | `/command-center/cost-of-chaos` | Exec | **SHIPPED** |
| S&OP Report | `/command-center/sop-report` | Manager | **SHIPPED** (mig 042) |
| AI Trust | `/ai-governance/ai-trust` | Exec/Admin | **PARTIAL** (mock risk) |
| MDR | `/ai-governance/mdr` | Planner/Admin | **SHIPPED** |
| Compliance | `/ai-governance/compliance` | Auditor/Admin | **SHIPPED** |
| Quality / Sustain | AI hub tabs | Specialist | **SHIPPED** demo |
| Ops | `/platform/ops` | Admin | **PARTIAL** |
| MLOps | `/platform/ml-ops` | Admin | **PARTIAL** |
| Grafana / Prometheus | infra | SRE | **SHIPPED** enterprise |

### 11.2 Key Analytics APIs (dpe-svc)

| API | Purpose | Status |
|-----|---------|--------|
| `GET /api/v1/analytics/*` | Executive summary, WC, delay, accuracy | **SHIPPED** |
| `GET /api/v1/analytics/otd-baseline` | FR-R1-16 | **SHIPPED** |
| `GET /api/v1/dashboard/unified` | Workspace | **SHIPPED** |
| `GET /api/v1/outcomes/*` | R2 outcomes | **SHIPPED** |
| S&OP / cost-accounting | Forecast, COGM/COPQ | **SHIPPED** full stack |

### 11.3 Feasibility / Sync Observability

| API | Purpose | Status |
|-----|---------|--------|
| `GET /feasibility/queue` | Risk queue | **SHIPPED** |
| `GET /feasibility/compliance-kpis` | Compliance KPIs | **SHIPPED** |
| `GET /sync/status` | Last sync | **SHIPPED** |
| `GET /sync/data-quality` | DQ flags | **SHIPPED** |

---

## 12. Integration Requirements

### 12.1 Odoo (Primary)

| Item | Detail | Status |
|------|--------|--------|
| Protocol | XML-RPC (+ optional `ipe_connector` Odoo module) | **SHIPPED** |
| Entities | product, MO, BOM/lines, WC, routing, inventory proxy | **PARTIAL** (stock.quant — OQ-11) |
| Auth to IPE actions | HMAC `X-IPE-Signature` | **SHIPPED** |
| Sync cadence | 15 min + manual | **SHIPPED** |
| Write-back | `/sync/odoo/activate` | **SHIPPED** |
| Local double | `mock-odoo-api` in R2 compose | **SHIPPED** |
| Staging | Customer Odoo | **BLOCKED** PH1-02 |
| Docs | `docs/integration/ODOO-*.md`, Star Trans worksheets | **SHIPPED** |

### 12.2 SAP / D365 / SAP B1

| ERP | Status |
|-----|--------|
| SAP / D365 | Registry factory + no-op sync — **SHIPPED** scaffold; not production |
| SAP B1 | **CUT** (S12) |

### 12.3 Kong Routes (Release 2 — `kong.release2.yml`)

| Service | Upstream | Paths |
|---------|----------|-------|
| dpe-svc | `:8001` | `/api/v1/auth`, `/dashboard`, `/analytics`, `/demand/classify|queue`, `/planner-assist`, `/admin`, `/compliance`, `/outcomes` |
| fea-svc | `:8004` | `/api/v1/feasibility` |
| res-svc | `:8005` | `/api/v1/resolution` |
| cap-svc | `:8003` | `/api/v1/capacity` |
| connector | `:8009` | `/api/v1/sync`, `/sync/odoo`, `/erp/odoo` |
| nlp-svc | `:8007` | `/api/v1/copilot`, `/nlp` |
| demand-svc | `:8040` | `/api/v1/demand/forecast|sense|accuracy|signal` |
| scenario-svc | `:8050` | `/api/v1/scenario` |

Plugins: CORS, HSTS, rate-limit (Redis), tenant strip.

### 12.4 Event Mesh (Full Profile)

| Topic (examples) | Producers → Consumers | Status |
|------------------|----------------------|--------|
| `ipe.demand.created/classified` | connector/dpe → mat | **SHIPPED** full |
| `ipe.mo.material_scored` | mat → fea | **SHIPPED** full |
| `ipe.mo.feasibility_scored` | fea → UI WS | **SHIPPED** full |
| `ipe.resolution.*` | res | **SHIPPED** full |
| DLQ + Redis idempotency | shared consumer | **SHIPPED** full |
| R1/R2 Kafka | Disabled (`IPE_KAFKA_ENABLED=false` / empty bootstrap) | By design |

### 12.5 Auth Integration

| Mode | When | Status |
|------|------|--------|
| `AUTH_MODE=local` | R1/R2 PoC, smoke/demo | **SHIPPED** (required for R2 smoke 2026-07-10) |
| Keycloak OIDC RS256 | Enterprise / Option B | **PARTIAL** (container health flaky) |
| JWKS opt-in | `JWT_USE_JWKS=true` | **SHIPPED** code |

### 12.6 Performance Requirements

| Profile | Target | Evidence | Status |
|---------|--------|----------|--------|
| k6 SLO | P95 <500ms, err <5% | 293ms / 0% @ v9.3.0-p2 | **SHIPPED** |
| k6 stress | Rate limiter 429 | Separate script | **SHIPPED** |
| R1 compose start | ≤10 min on 8GB VM | Playbook | **PARTIAL** (customer VM unproven — T037) |
| Copilot LLM | Graceful degrade without keys | nlp-svc | **SHIPPED** |

### 12.7 API Envelope

Standard service responses prefer structured JSON; OpenAPI per service under `docs/api/`. Contract fuzz: Schemathesis config in `tests/contract/`.

---

## 13. Technical Architecture

### 13.1 Release 1 Topology

```
[Odoo / mock] --XML-RPC--> [connector]
                              |
[web-ui] --> [Kong] --> [dpe-svc | fea-svc | res-svc | cap-svc | connector]
                              |
                         [PostgreSQL]  [Redis]
                    (Keycloak/Vault/MinIO optional)
```

**No Kafka** in R1 (Constitution IV).

### 13.2 Release 2 Topology

R1 + `nlp-svc` + `demand-svc` + `scenario-svc` + `mock-odoo-api`.

**Gap:** `mat-svc` referenced by URL but **missing** from compose — **OQ-8** / C-14.

### 13.3 Full Stack Services (monorepo `ipe/services/`)

| Service | Role | Typical port | In R1 compose | In R2 compose |
|---------|------|--------------|---------------|---------------|
| dpe-svc | Demand/priority, analytics, auth, admin, outcomes | 8001 | ✅ | ✅ |
| mat-svc | Material, pATP, CTP | 8002 | ❌ (OQ-8) | ❌ |
| cap-svc | OR-Tools scheduling | 8003 | ✅ | ✅ |
| fea-svc | Feasibility + WS | 8004 | ✅ | ✅ |
| res-svc | Resolution scenarios | 8005 | ✅ | ✅ |
| del-svc | Delay NLP | 8006 | Full | — |
| nlp-svc | Copilot | 8007 | — | ✅ |
| rec-svc | Recommendations | 8008 | Full | — |
| connector | ERP sync | 8009 | ✅ | ✅ |
| alert-svc | Alerts | 8010 | Full | — |
| sustain / quality / scn / network | Specialty | 8012–8015 | Full | — |
| ml-svc | ML | 8016 | Full | — |
| demand-svc | SES demand | 8040 | — | ✅ |
| scenario-svc | Scenarios | 8050 | — | ✅ |
| mock-odoo-api | Test ERP | — | — | ✅ |
| order/supply/equipment/procurement/… | v8 streams | varies | Full | — |

Also present: `material-svc`, `gateway`, `connectors/` — treat as legacy/alternate; prefer canonical names above. **Do not use** orphan `services/` at AISOP repo root.

### 13.4 Technology Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Pydantic, uv workspaces |
| Shared | `ipe_shared` (auth, RLS session, events, audit, observability) |
| Frontend | React + TypeScript + Vite; Vitest; Playwright |
| DB | PostgreSQL 16 (+ Timescale patterns for inventory) |
| Cache | Redis 7 (host **6380** in common env) |
| Messaging | Kafka 7.x + Schema Registry (full) |
| Gateway | Kong |
| IdP | Keycloak (enterprise) |
| Secrets | Vault scaffold |
| Orchestration | Docker Compose; Helm/kind (enterprise) |
| Observability | Prometheus, Grafana, OTel, Jaeger |
| Solvers | OR-Tools CP-SAT |
| LLM | Ollama / OpenRouter / Anthropic (tiered) |

### 13.5 Security Architecture

| Control | Status |
|---------|--------|
| RLS on tenant tables | **SHIPPED** (legacy INSERT policies 033/035) |
| JWT + RBAC | **SHIPPED** |
| Audit immutability | **SHIPPED** |
| PII stripping (Copilot SaaS tier) | **SHIPPED** |
| Istio mTLS manifests | **SHIPPED** scaffold |
| SOC 2 control catalog | **SHIPPED** code; audit engagement **PLANNED** Phase 5 |
| Production secrets in vault | **PARTIAL** / POST-B |

### 13.6 Scalability

| Mode | Pattern | Status |
|------|---------|--------|
| R1 single VM | Compose 8GB | **SHIPPED** docs |
| Enterprise | Helm + HPA smoke | **SHIPPED** gates 6–10 |
| Multi-tenant SaaS | Quotas/metering/Stripe | **PARTIAL** / Phase 4 |

---

## 14. Competitive Context

> **Evidence note:** The repository contains **positioning guidance** (Constitution MENA constraints, Spec 013) but **no formal third-party competitive research dossier**. The matrix below is **PROVISIONAL** and requires **PM validation** before customer-facing use.

### 14.1 Positioning (from constitution / specs)

| Axis | IPE stance |
|------|------------|
| R1 competitor | Excel + Odoo MRP |
| Not primary pitch | Kinaxis / SAP IBP feature parity |
| Moat claim | MENA implementation + feasibility-before-shift workflow |
| Buyer | CEO / Ops Director |

### 14.2 Provisional Feature Matrix (needs PM validation)

| Capability | IPE (as-is) | Excel+Odoo MRP | Kinaxis* | SAP IBP* | o9* |
|------------|-------------|----------------|----------|----------|-----|
| Live Odoo MO risk queue | ✅ R1 | Manual | * | * | * |
| Feasibility gates + unscorable | ✅ | ❌ | * | * | * |
| OR-Tools finite schedule | ✅ | Limited MRP | * | * | * |
| Resolution scenarios | ✅ | ❌ | * | * | * |
| Arabic MVP | 🟡 | Varies | * | * | * |
| 8GB VM deploy | ✅ | N/A | ❌ typical | ❌ | ❌ |
| Multi-echelon network | Demo/full | ❌ | * | * | * |
| Enterprise SSO/K8s | 🟡 | N/A | * | * | * |
| Live SAP connector | ❌ scaffold | N/A | * | Native | * |

\*Cells marked `*` = **UNKNOWN** — not evidenced in repo; do not cite as fact.

### 14.3 Pricing Fit (commercial — OQ-7)

| Component | Range (constitution) | Status |
|-----------|----------------------|--------|
| License | $18K–30K / yr | **OQ-7** pending sign-off |
| Implementation | $12K–25K one-time | **OQ-7** |

---

## 15. Data & Privacy

### 15.1 Data Collected / Stored

| Category | Examples | Store |
|----------|----------|-------|
| Master data | Products, BOM, WC, operators | CDM Postgres |
| Transactional | MOs, demand lines, supply orders | CDM |
| Planning | Feasibility scores, schedules, scenarios | CDM |
| Sync audit | `cdm_sync_run`, DQ flags | CDM |
| Activity | `cdm_activity_event` | CDM (038) |
| Auth | `cdm_user` password hashes | CDM |
| Copilot | Session/query logs | nlp-svc — **OQ-6** |
| Telemetry | Metrics, traces | Prometheus/Jaeger |

### 15.2 Privacy & Compliance

| Control | Status |
|---------|--------|
| Tenant RLS | **SHIPPED** |
| GDPR DSAR APIs | **SHIPPED** (dpe) |
| Consent manager | **SHIPPED** code |
| Retention policies + Airflow DAG | **SHIPPED** code |
| PII strip before SaaS LLM | **SHIPPED** |
| SOC 2 Type II | **PLANNED** Phase 5 |
| WCAG 2.1 AA cert | **PLANNED** Phase 5 |

### 15.3 Conflict & Ownership Policy

| Data class | Winner |
|------------|--------|
| Master data (BOM, product, WC) | **Odoo** |
| Approved schedule dates | **IPE** until next sync conflict |
| Inventory on-hand | Odoo (`stock.quant` target) — **PARTIAL** |

---

## 16. Implementation Roadmap

### 16.1 Completed Phases

| Phase | Scope | Tag / evidence | Status |
|-------|-------|----------------|--------|
| Foundation → AI-first | Specs 000–004 | v6.x | **SHIPPED** |
| Hub + v8 streams | 006–010 | v8.2.0 | **SHIPPED** |
| R1 Odoo MENA eng | 013 | R1 compose/demo | **SHIPPED** eng |
| Enterprise P0–P2 | 015 | v9.3.0-p2 | **SHIPPED** |
| Enterprise P3 | 015/017 | v9.4.0-p3 | **SHIPPED** |
| Sprint 7 cohesion | 016 | mig 038 | **SHIPPED** Tier 1 |
| R2 sprints S1–S4, S6–S11 | 018 | smoke/demo | **SHIPPED** eng |

### 16.2 In Progress / Hold

| Item | Owner | Blocker | Status |
|------|-------|---------|--------|
| G-R2-04 Arabic native sign-off | Native reviewer | Human | **BLOCKED** |
| G-R2-TAG / `v9.1.1-r2` | Release manager | G-R2-04 policy | **BLOCKED** |
| Phase 1 UAT Star Trans | Exec + Eng | PH1-01 SOW, PH1-02 staging | **BLOCKED** |
| C-15 stock.quant | Backend / ARB | OQ-11 | **PARTIAL** |
| #40 scenario promotion | Frontend | OQ-10 | **PLANNED** |
| #37/#38 provision/quotas | Backend | Scope | **PARTIAL** |
| mat-svc in R2 compose | Backend | OQ-8 | **PLANNED** |
| Keycloak health in R2 | Ops | Container | **PARTIAL** |

### 16.3 Upcoming (Waves / Phases)

| Horizon | Content | Gate |
|---------|---------|------|
| Wave 2 remainder | Predictive delay (#42); provision/quotas | Spec 017 |
| Wave 3 | NL schedule + supplier comms (#43–46) | Spec 017 |
| Phase 4 GTM | Stripe, tenant self-service, developer portal | After P3 tag ✅ |
| Phase 5 | SOC 2 II, WCAG, live SAP/D365 | Post-GTM |

### 16.4 Resource Notes

| Resource | Note |
|----------|------|
| Engineering | R2 eng ~92% per STATUS-REPORT |
| Commercial | PH1-01/02 required for revenue UAT |
| Native Arabic QA | Cannot be automated |
| Infra | Kind 8/8; compose R2 up with AUTH_MODE=local |

### 16.5 Current Gate Matrix (authoritative snapshot)

| Gate | Status | Evidence |
|------|--------|----------|
| G-R2-01 | **PASS** 15/15 | `docs/qa/release2-smoke-2026-07-10.txt` |
| G-R2-02 | **PASS** | Copilot tools tests / smoke |
| G-R2-03 | **PASS (eng)** | Live Odoo = PH1-02 |
| G-R2-04 | **PARTIAL** | `docs/qa/arabic-qa-r2.md` |
| G-R2-05 | **PASS** 7/7 | `docs/demo-data/release2-demo-g-r2-05.txt` |
| G-R2-TAG | **HOLD** | Prefer `v9.1.1-r2` after Arabic |
| Enterprise 1–10 | **PASS** | Spec 015 / GATE-RESULTS |
| Gate 11 | **12/14 + waiver** | OQ-9 accepted |

Open inventory: `specs/018-phase2-release2/OPEN-ITEMS-PROJECT.md`.

---

## 17. Risks & Mitigation

| ID | Risk | Impact | Likelihood | Mitigation | Status |
|----|------|--------|------------|------------|--------|
| R-01 | No signed SOW / staging Odoo | Cannot prove ROI | High | PH1-01/02 executive track | **BLOCKED** |
| R-02 | Arabic QA unsigned | Tag hold; MENA trust | Medium | Native reviewer checklist | **BLOCKED** |
| R-03 | stock.quant gap | Misleading material scores | Medium | Implement or ARB CUT (OQ-11) | Open |
| R-04 | mat-svc absent from R2 compose | Broken material paths | Medium | Add service (C-14) | Open |
| R-05 | Keycloak unhealthy | SSO demos fail | Medium | AUTH_MODE=local for R2; fix container | Mitigated short-term |
| R-06 | AUTH_MODE mismatch → 401 | Smoke/demo red | Medium | Document local mode; dual JWT | Mitigated 2026-07-10 |
| R-07 | Feature sprawl vs R1 focus | Diluted go-live | Medium | Constitution VII | Ongoing |
| R-08 | LLM key absence | Copilot degrade | Low | Graceful fallback + tools | Mitigated |
| R-09 | Kind OR-Tools timeout | Gate 11 incomplete | Low | OQ-9 waiver | Accepted |
| R-10 | Competitive overclaim | Sales risk | Medium | Label provisional matrix | Process |
| R-11 | UI RBAC gap | Unauthorized screen access | Medium | OQ-3 decision | Open |
| R-12 | Unpushed / dirty git | Traceability | Low | Release hygiene | Process |

---

## 18. Assumptions & Constraints

### 18.1 Assumptions

| ID | Assumption | Validated? |
|----|------------|------------|
| A-01 | Customer #1 is Odoo-based discrete manufacturer | Yes (Star Trans) |
| A-02 | Shadow autonomy acceptable at go-live | Yes (constitution) |
| A-03 | Batch sync sufficient vs webhooks for R1 | Yes (MENA connectivity) |
| A-04 | 8GB VM is acceptable production for R1 | Docs yes; customer VM **UNKNOWN** |
| A-05 | Pricing band $18–30K fits buyer | **OQ-7** |
| A-06 | mock-odoo ≈ staging for eng gates | Accepted for G-R2; not for UAT |

### 18.2 Technical Constraints

| Constraint | Detail |
|------------|--------|
| RLS mandatory | Constitution I |
| Tests for behavioral changes | Constitution III |
| No Kafka in R1 | Constitution IV |
| Port reconciliation | Dockerfile / compose / Kong / Helm |
| Redis host port | **6380** (common env) |
| Python 3.12 + ruff/mypy/prettier | Tooling |
| Cross-platform scripts | PowerShell customer-facing |

### 18.3 Business Constraints

| Constraint | Detail |
|------------|--------|
| One ERP first | Odoo |
| Three screens minimum R1 | CT, Resolution, Executive OTD |
| Arabic before go-live | CT, Resolution, nav, alerts |
| Fixed-scope SOW | Not demo-script-only |
| Phase 4 GTM after `v9.4.0-p3` | Constitution VIII |

### 18.4 Doc Drift / Conflicts (do not invent resolution)

| Conflict | Sources | Action |
|----------|---------|--------|
| FR-R1-05 done vs C-15 open | Spec 013 vs OPEN-ITEMS | **OQ-11** |
| READINESS score 100 vs R2 finalize ~92% eng | READINESS vs 018 STATUS | Treat as different scopes (v8 demo vs R2 program) |
| Root AGENTS.md still cites v6 REL-* | Root AGENTS vs tags v9.x | Update pointer — **UNKNOWN** owner |
| Spec 018 header still “smoke pending” | spec.md vs GATES.md | Prefer **GATES.md** + STATUS-REPORT as live |

---

## 19. Appendices

### Appendix A — Core Data Model (CDM)

| Table | Purpose |
|-------|---------|
| `cdm_tenant` | Tenant config |
| `cdm_product` | Product master |
| `cdm_bill_of_material` / `cdm_bom_line` | BOM |
| `cdm_demand_line` | Demand + priority |
| `cdm_supply_order` | Supply / POs |
| `cdm_manufacturing_order` | MOs + feasibility / material scores |
| `cdm_work_order` / `cdm_work_center` / `cdm_operator` | Capacity / labor |
| `cdm_inventory_position` | Inventory time-series |
| `cdm_delay_event` | Delay causes |
| `cdm_resolution_scenario` | Scenarios |
| `cdm_sync_run` / DQ flags | R1 sync audit (036) |
| `cdm_activity_event` | Sprint 7 activity (038) |
| `cdm_otd_snapshot` | OTD (039) |
| `cdm_tenant_health` | Ops (040) |
| `cdm_supplier_score` | SC intel (041) |
| `cdm_sop_report` | S&OP (042) |
| Odoo config versioning | 043 |
| `cdm_audit_log` | Append-only audit |

ER narrative: ERP → Connector → CDM ←→ AI services; UI reads CDM via Kong.

### Appendix B — Configuration Options (selected)

| Variable | Purpose |
|----------|---------|
| `IPE_DATABASE_URL` | Postgres |
| `IPE_REDIS_URL` | Redis (host 6380) |
| `IPE_KAFKA_BOOTSTRAP_SERVERS` | Empty for R1 |
| `IPE_JWT_SECRET_KEY` | Local JWT |
| `AUTH_MODE` | `local` \| `keycloak` |
| `JWT_USE_JWKS` | JWKS validation |
| `VITE_RELEASE_PROFILE` | `full` \| `release1` \| `release2` |
| `VITE_API_BASE_URL` | Kong/API |
| `ANTHROPIC_API_KEY` / OpenRouter / Ollama | LLM |
| `ODOO_*` / sync body creds | Connector |
| `ERP_SYNC_MODE` | e.g. `direct` |
| `OTEL_*` | Tracing |

### Appendix C — Edge Cases

| Case | Expected behavior |
|------|-------------------|
| MO missing BOM/routing | Unscorable + DQ flag; no silent high score |
| Sync while Odoo down | Failed sync_run; alert webhook if configured; UI last-synced stale |
| MDR <70% | Schedule returns 503 |
| Cross-tenant JWT | RLS + 403/empty |
| Expired JWT | 401; UI redirect login |
| LLM unavailable | Copilot fallback text; tools may still run |
| Solver timeout | Partial/timeout status; no corrupt assignments |
| SYNC_CONFLICT | Badge on CT; planner resolves |

### Appendix D — Technical Decisions (ADR / constitution)

| Decision | Rationale | Ref |
|----------|-----------|-----|
| Odoo first | Customer #1 revenue | Principle VII |
| No Kafka in R1 | Reliability over purity | Principle IV |
| Shadow autonomy default | Trust | Product |
| Gate scripts = SoT | Anti-checklist-theater | Principle VIII |
| OQ-9 Gate 11 waiver | Infra OR-Tools on kind | `gate11-oq9-waiver.md` |
| Keycloak deferral options | ADR-001 | `docs/decisions/` |
| Legacy RLS waiver | ADR-002 | `docs/decisions/` |
| SAP B1 CUT | Strategy / Spec 017 | S12-CUT.md |

### Appendix E — Testing Evidence Paths

| Layer | Path / command | Latest signal |
|-------|----------------|---------------|
| Unit | `uv run pytest` per service | 860/860 (018) |
| Vitest | `apps/web` | 41/41 |
| Playwright | `e2e/arabic-r2.spec.ts`, critical-path | Run for G-R2-04 |
| R2 smoke | `scripts/release2-smoke.ps1` | 15/15 |
| R2 demo | `scripts/run-release2-demo.ps1` | 7/7 |
| R1 demo | `scripts/run-release1-integration-demo.ps1` | 14/14 compose |
| k6 SLO | `docs/qa/PERFORMANCE-BASELINE-v9.1.0.md` | PASS 293ms |
| Chaos | `docs/chaos/` C1–C6 | Documented |
| Integration | `tests/integration/` | Multiple suites |

### Appendix F — Glossary

| Term | Definition |
|------|------------|
| **IPE** | Intelligent Planning Engine |
| **CDM** | Canonical Data Model |
| **MO** | Manufacturing Order |
| **OTD** | On-Time Delivery |
| **MDR** | Master Data Readiness (composite gate) |
| **pATP** | Probabilistic Available-to-Promise |
| **CTP** | Capable-to-Promise |
| **EIB** | Ecosystem Integration Bus (activity normalization) |
| **R1 / R2** | Release 1 / Release 2 compose profiles |
| **Shadow mode** | AI observes/suggests; no auto-apply |
| **Unscorable** | MO lacking data for honest feasibility |
| **Star Trans** | Reference MENA customer |
| **Kong** | API gateway |
| **RLS** | Row-Level Security |
| **OQ** | Open Question (stakeholder) |

### Appendix G — Stakeholder Decision Log (Open)

| ID | Decision needed | Owner | Blocks |
|----|-----------------|-------|--------|
| OQ-1 | Odoo 17 vs 19 canonical | Product + Customer IT | Mapping docs |
| OQ-3 | UI route RBAC | Product + Security | Hardening |
| OQ-5 | Formal KPI baseline study | Product | G-01/G-02 claims |
| OQ-6 | Copilot retention/erasure | Legal + Eng | GDPR |
| OQ-7 | Pricing confirmation | Executive | SOW |
| OQ-8 | mat-svc in compose | Eng lead | C-14 |
| OQ-9 §6 names | Waiver signatories | Program | Governance record |
| OQ-10 | Scenario promotion CUT vs build | PM | #40 |
| OQ-11 | stock.quant true sync vs CUT | ARB | C-15 / material honesty |
| OQ-12 | Tag `v9.1.0-r2` vs `v9.1.1-r2` | Release manager | G-R2-TAG |
| PH1-01 | Sign SOW | Executive | UAT |
| PH1-02 | Provision Odoo staging | Ops + Customer | UAT |
| PH1-05 / G-R2-04 | Arabic native sign-off | Native reviewer | Tag |

### Appendix H — Version History (this PRD)

| Date | Change |
|------|--------|
| 2026-07-07 | Initial authoritative draft (21 sections; pre-R2 finalize) |
| 2026-07-10 | Full rewrite to 19 required sections; aligned to constitution v1.2.4, specs 017/018, GATES, OPEN-ITEMS, live tags `v9.4.0-p3` / `v9.1.0-r2` HOLD |

### Appendix I — Key File References

| Path | Role |
|------|------|
| `ipe/.specify/memory/constitution.md` | Binding principles |
| `ipe/specs/013-release1-odoo-mena/` | R1 FRs |
| `ipe/specs/017-first-release-plan/` | Waves / PH1 |
| `ipe/specs/018-phase2-release2/` | R2 gates, open items |
| `ipe/READINESS.md` | Deployment readiness pointer |
| `ipe/apps/web/src/app/router.tsx` | UI routes |
| `ipe/infrastructure/docker/docker-compose.release{1,2}.yml` | Profiles |
| `ipe/infrastructure/docker/kong.release2.yml` | R2 gateway |
| `ipe/docs/qa/*` / `ipe/docs/demo-data/*` | Gate evidence |

---

*End of PRD-IPE-AUTHORITATIVE — 2026-07-10*
