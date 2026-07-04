# Product Requirements Document (PRD)

## Intelligent Planning Engine (IPE) — Comprehensive As-Is Specification

| Field | Value |
|-------|-------|
| **Document ID** | PRD-IPE-2026-COMPREHENSIVE |
| **Product version (full stack)** | **v8.2.0** |
| **Customer release profiles** | **Release 1** (`v9.0.0-r1` target) · **Release 2** (`v9.1.0-r2` target) · **Enterprise Phase 2** (`v9.3.0-p2` target) |
| **Status** | As-is development reference — full stack 32/32; R1/R2 HTTPS demos validated locally; enterprise Gates 1–5 pass except k6 SLO + git tag |
| **Author** | Product Management (consolidated from specs, codebase, Speckit 000–015, and gate verification sessions) |
| **Last updated** | **2026-07-03** |
| **Primary vertical** | Discrete manufacturing — electrical transformers (Star Trans, Egypt/MENA) |
| **Product scope boundary** | **IPE AISOP only** — NEXUS Social / external marketing scaffolds are **explicitly out of scope** (spec 005) |
| **Supersedes / extends** | `docs/PRD-IPE-v8.2.0-ENTERPRISE.md` (partial overlap; this document is authoritative for as-is scope) |

> **Scope statement:** This PRD documents IPE **as it currently exists in development**, including what is implemented, what is scaffolded, what is validated in demo vs. live ERP, and what remains blocked. It does **not** describe a future ideal state unless explicitly marked **POST-B** (post–business-blocker) or **Deferred (R2/R3)**.
>
> **Terminology note:** IPE is an **AI-assisted manufacturing planning platform** (APS), not an AI marketing platform. Competitive context in Section 15 compares IPE to **SAP IBP, Kinaxis, o9**, and **Excel + Odoo MRP** — not MarTech vendors.

---

## Table of Contents

0. [Project Definition & Background](#0-project-definition--background)
1. [Executive Summary](#1-executive-summary)
2. [Product Vision & Scope](#2-product-vision--scope)
3. [Problem Statement & Business Context](#3-problem-statement--business-context)
4. [Goals & Success Metrics](#4-goals--success-metrics)
5. [User Personas & Workflows](#5-user-personas--workflows)
6. [Use Cases](#6-use-cases)
7. [Functional Requirements](#7-functional-requirements)
8. [Feature Specifications](#8-feature-specifications)
9. [Business Scenarios](#9-business-scenarios)
10. [User Interface & Navigation](#10-user-interface--navigation)
11. [Authorization, Roles & Permissions](#11-authorization-roles--permissions)
12. [Reports & Dashboards](#12-reports--dashboards)
13. [Integration Requirements](#13-integration-requirements)
14. [Technical Architecture](#14-technical-architecture)
15. [Competitive Context](#15-competitive-context)
16. [Data & Privacy](#16-data--privacy)
17. [Implementation Roadmap](#17-implementation-roadmap)
18. [Risks & Mitigation](#18-risks--mitigation)
19. [Assumptions & Constraints](#19-assumptions--constraints)
20. [Appendices](#20-appendices)
21. [Last 24 Hours — Engineering Activity Log](#21-last-24-hours--engineering-activity-log-2026-07-02--2026-07-03)

---

## 0. Project Definition & Background

### 0.1 Why IPE Exists (Business Purpose)

Discrete manufacturers (100–1,000 employees, 1–2 sites) running **Odoo MRP** or similar ERPs often plan production in **parallel spreadsheets** while ERP holds master data. Planners discover material shortages and capacity overloads **on the shop floor**, not at the start of the shift. Leadership sees OTD and margin impact **after month-end close**. IPE was initiated to provide a **feasibility-first planning layer** that sits above ERP: ingest master data, score manufacturing orders before scheduling, offer structured resolution scenarios, run finite-capacity optimization, and optionally write approved plans back to ERP — with AI in **shadow mode** until trust is established.

### 0.2 Project Definition (As-Is)

| Attribute | Definition |
|-----------|------------|
| **Product name** | Intelligent Planning Engine (IPE) |
| **Workspace** | `E:\AISOP\ipe` (monorepo); Spec Kit at `E:\AISOP\.specify\` |
| **Architecture** | Event-driven microservices (22 in full profile; 8 in Release 1) + React hub UI + Kong gateway |
| **Primary ERP (live-validated)** | Odoo 17–19 via XML-RPC (`connector-svc`) |
| **Reference customer** | Star Trans — electrical transformers, Egypt/MENA |
| **Constitution** | `.specify/memory/constitution.md` v1.0.1 — six binding principles (RLS, auth, tests, events, service architecture, observability) |
| **Speckit program** | Features `000`–`015` under `ipe/specs/`; active rollup `005-ipe-program-status`; enterprise track `015-enterprise-production-readiness` |

### 0.3 Objectives (Measurable, Current Phase)

| ID | Objective | Target | As-is (2026-07-03) |
|----|-----------|--------|---------------------|
| OBJ-01 | Full product demo reliability | 32/32 checkpoints | ✅ Achieved (`run-full-demo.ps1`) |
| OBJ-02 | Release 1 Odoo closed loop | 14/14 integration demo over HTTPS | ✅ Achieved locally (`run-release1-integration-demo.ps1 -BaseUrl https://localhost:8443`) |
| OBJ-03 | Release 2 commercial features | 5/5 R2 demo | ✅ Achieved locally (`run-release2-demo.ps1`) |
| OBJ-04 | Enterprise Phase 2 gates | Gates 1–5 PASS + k6 SLO + tag `v9.3.0-p2` | 🟡 Gates 1–5 pass individually; **k6 FAIL**; **tag pending**; changes **uncommitted** |
| OBJ-05 | Star Trans customer UAT | Signed acceptance on live Odoo | ⬜ Blocked on customer IT / SOW |
| OBJ-06 | Enterprise contract readiness | Phase 0–2 of spec 015 | 🟡 Phase 0 activated in stack; Phase 1 K8s not started |

### 0.4 Scope Summary

**In scope (as deployed in development today):**

- Hub-based web app (Planning, Command Center, Supply Chain, AI & Governance, Platform, Shop Floor)
- Feasibility scoring, Resolution Center, OR-Tools scheduling, Excel plan upload
- Odoo bidirectional sync (ingest + activate write-back) with conflict detection
- v8 streams U1–U8 (copilot sessions, demand, scenario, supply, orders, equipment, design AI, procurement, sustain, quality)
- Release 1 profile (8-service compose, 3 planning tabs)
- Release 2 streams A–D (auto-propose, Outcomes dashboard, Copilot Lite, Odoo resolution write-back — code complete; demo validated)
- Enterprise stack overlay: Keycloak OIDC, HashiCorp Vault, Kong TLS :8443, Prometheus/Grafana (6 dashboards), audit middleware, network isolation, tenant quotas

**Explicitly out of scope:**

- NEXUS Social / AI marketing platform (separate product; not in `ipe/` program scope)
- Full MES replacement; autonomous schedule release without human approval
- Production SAP S/4 or D365 connectors (scaffold only)
- WCAG 2.1 AA certification; SOC 2 Type I audit engagement
- Kafka in Release 1 compose profile
- 22-service Kubernetes production for first customer (Release 1 = 8 GB VM compose)

---

## 1. Executive Summary

### 1.1 What IPE Is

**Intelligent Planning Engine (IPE)** is a multi-tenant, AI-assisted **manufacturing planning and execution platform**. It connects demand sensing, feasibility scoring, constraint resolution, finite-capacity scheduling (OR-Tools), supply network visibility, and shop-floor monitoring in a **hub-based React web application** backed by **22 FastAPI microservices** (full profile) or **8 services** (Release 1 customer profile).

**Core product thesis:** Planners detect infeasibility **before the shift starts**, evaluate structured resolution options, publish optimized schedules, and leadership sees financial impact — with AI in **shadow mode** by default so humans retain control.

### 1.2 Business Drivers

| Driver | Description |
|--------|-------------|
| **Planning cycle compression** | Replace spreadsheet + ERP tab hopping with a prioritized MO risk queue |
| **Feasibility before commitment** | Score MOs on demand, BOM, material, capacity, and labor gates before scheduling |
| **Structured disruption response** | Resolution scenarios with cost/delivery trade-offs vs. ad hoc firefighting |
| **Mid-market accessibility** | Docker-deployable PoC in hours vs. multi-month suite rollouts |
| **MENA go-to-market (Release 1)** | Odoo-native sync for manufacturers using Excel + Odoo MRP |

### 1.3 Current Maturity Snapshot (As-Is)

| Dimension | Full stack (v8.2.0) | Release 1 (Star Trans profile) |
|-----------|---------------------|--------------------------------|
| **Demo validation** | **32/32** automated checkpoints | `release1-smoke.ps1` (compose health + API smoke) |
| **Backend tests** | **870+** (180 in dpe-svc) | Connector Odoo mapper/adapter tests (16/16) |
| **Chaos experiments** | **6/6** (C1–C6 documented) | Not in release1 compose |
| **Microservices** | 22 Kong-routed | **8** (db, redis, kong, dpe-svc, fea-svc, cap-svc, mat-svc, connector) |
| **Live ERP sync** | Odoo XML-RPC validated (Odoo 19 local); bidirectional + conflict resolver | **Odoo path implemented** | Gate 4 PASS; `sync_engine.py` fixes applied |
| **Enterprise overlay** | Keycloak + Vault + TLS + Grafana + audit | Activated in dev stack (Gate 5) | POST-B scaffolds now **live in enterprise compose** |
| **Production deployment** | Gates 1–5 pass; k6 SLO blocked | Enterprise Phase 2 close pending | Tag `v9.3.0-p2` not created |
| **Readiness scores** | Speckit **100/100** (32/32); audit ~92/100 | Spec 013: local integration **14/14 HTTPS** | Customer UAT still blocked |

### 1.4 Product Evolution Summary

| Era | Git / spec tag | Product name | What changed |
|-----|----------------|--------------|--------------|
| **Stabilization** | v1.0.0-rc1 / spec 002 | Release gates | CI green, reproducible stack, doc reconciliation |
| **V5 Convergence** | **v1.0.0** / spec **003** | IPE V5.0 | Closed-loop schedule persist, MDR gate, XAI, chaos/k6 — *note: V5 scope shipped under v1.0.0 tag, not v5.0.0* |
| **V6 AI-First** | v6.0.0 / spec 004 | IPE V6.0 | Tariff shock, visual CPM, cost of chaos, war room, predictive maintenance |
| **v7.x** | v7.0.0 / spec 006 | Hub consolidation | 6 navigation hubs; Ollama/OpenRouter LLM backbone |
| **v8.0–v8.2** | v8.2.0 (tag pending) / specs 007–010 | SAP-gap upgrade | U1–U8 streams: copilot sessions, demand, scenario, supply, orders, equipment, design AI, procurement; 32/32 demo |
| **Release 1** | v9.0.0-r1 (target) / spec 013 | Odoo + MENA customer | 8-service profile; **14/14 HTTPS demo** |
| **Release 2** | v9.1.0-r2 (target) / spec 014 | Commercial growth | Outcomes, Copilot Lite, auto-propose; **5/5 demo** |
| **Enterprise P2** | v9.3.0-p2 (target) / spec 015 | Observability + security gates | Gates 1–5 PASS; k6 + tag pending |

### 1.5 Key Success Metrics (Executive View)

| Metric | Target | As-is status |
|--------|--------|--------------|
| Demo readiness | 32/32 checkpoints | ✅ Achieved (full profile) |
| MO triage time vs spreadsheet | ≥30% faster | 🟡 Qualitative demo feedback; no formal baseline study |
| Feasibility queue operational | ≥1 MO scored and visible | ✅ Release 1 local: 2 Odoo MOs at 82.5 score |
| Closed-loop schedule persist | Approved times survive refresh | ✅ Implemented (V5 R1) |
| Customer Release 1 UAT | Star Trans signed SOW + live Odoo | ⬜ Blocked on customer IT / contract |

---

## 2. Product Vision & Scope

### 2.1 Vision Statement

> Enable discrete manufacturers to **see which orders are at risk before the shift starts**, **choose among structured resolution options**, and **publish feasible schedules** — grounded in ERP master data, not manually maintained spreadsheets.

### 2.2 In Scope (As-Is)

#### Full profile (`VITE_RELEASE_PROFILE=full` or default)

| Area | Capabilities |
|------|--------------|
| **Planning** | Control Tower, Resolution Center, Schedule (OR-Tools + Excel upload), Demand forecasting, Scenario workbench |
| **Command** | Executive dashboard, War Room, Cost of Chaos, Equipment health |
| **Supply Chain** | Supply network, order/ATP, procurement, tariff shock, SCN portal, inventory |
| **AI & Governance** | Copilot (4 agent roles), Design AI, AI Trust, MDR, Compliance, Quality, Sustainability |
| **Platform** | Admin config, onboarding wizard (UI-only), MLOps dashboard |
| **Shop Floor** | Operator PWA (barcode scan, work order list) |
| **Integrations** | Kafka event mesh (full stack); LLM (Ollama/OpenRouter/Anthropic); Odoo connector (XML-RPC + REST adapter + Odoo addon) |
| **Demo / staging** | Star Trans SQL overlay, 32/32 checkpoint scripts, chaos suite |

#### Release 1 profile (`VITE_RELEASE_PROFILE=release1`)

| Area | Capabilities |
|------|--------------|
| **Planning (trimmed)** | Control Tower, Resolution Center, Schedule only |
| **Command (partial)** | Command Center hub visible; sub-pages per full build |
| **Platform** | Admin (config); onboarding/MLOps routes exist but not primary |
| **Integrations** | Odoo XML-RPC sync (15-min scheduler + manual `/sync/run`); activate write-back via XML-RPC |
| **Excluded from nav** | Supply Chain hub, AI & Governance hub, Shop Floor, Copilot, demand/scenario tabs |

### 2.3 Explicitly Out of Scope (As-Is)

| Item | Status | Notes |
|------|--------|-------|
| Full MES replacement | Out | Shop Floor is monitoring-light, not full MES |
| Production SAP/D365 write-back | POST-B | Interface scaffolds only |
| Enterprise SSO in production | POST-B | Keycloak scaffold; local JWT login live |
| WCAG 2.1 AA certification | POST-B | — |
| Autonomous schedule auto-release without human approval | Deferred | Governance requires explicit approve |
| Kafka in Release 1 | Never for R1 | Batch sync sufficient per constitution Principle VII |
| 22-service K8s production for first customer | Deferred R3 | Release 1 uses 8-service compose |
| Copilot in Release 1 nav | Deferred R2 | Hidden by release profile |
| Multi-sheet Excel import on all hubs | POST-B | Schedule upload only |
| `stock.quant` / live inventory sync (Release 1) | R1.1 | FR-R1-05 not implemented |

### 2.4 Scope Evolution & Reasoning

| Decision | Version introduced | Reasoning |
|----------|-------------------|-----------|
| Closed-loop schedule persist | V5 / v1.0.0 | #1 gap blocking production credibility |
| Hub consolidation (6 hubs) | v7.1 | Reduce nav sprawl from 15+ flat routes |
| U1–U8 v8 streams | v8.0–v8.2 | Close SAP IBP feature gaps for enterprise demos |
| Release 1 slice (8 services) | spec 013 | 8GB VM deploy; sell against Excel+Odoo, not Kinaxis |
| Odoo as first live ERP | spec 013 | Star Trans customer; XML-RPC before REST addon install |
| Arabic MVP (Control Tower, nav) | spec 013 | MENA buyer requirement; Resolution/login partial |

### 2.5 Open Scope Decisions (Stakeholder Input Required)

| ID | Question | Impact |
|----|----------|--------|
| **OQ-1** | Canonical Odoo version for Release 1: **17** (spec 013) vs **19** (local dev validated)? | Field mapping docs, customer install guide |
| **OQ-2** | Is demo SQL overlay (`seed-startrans-overlay.sql`) ever used in customer prod, or **Odoo-only** as source of truth? | Spec 013 says Odoo-only for prod; demo scripts differ |
| **OQ-3** | Should UI enforce backend RBAC at route level? | Currently any authenticated user reaches all routes |
| **OQ-4** | When to tag **v8.2.0** in git/CHANGELOG? | READINESS says ready; CHANGELOG stops at v7.0.0 |

---

## 3. Problem Statement & Business Context

### 3.1 Problems IPE Solves

| Problem | User pain | IPE response (as-is) |
|---------|-----------|---------------------|
| **Invisible infeasibility** | Planners discover material/capacity conflicts on the shop floor | Feasibility scoring + Control Tower queue sorted by risk |
| **Spreadsheet planning parallel to ERP** | Dual maintenance; stale MO dates | Odoo sync → CDM; optional write-back on approve |
| **Unstructured firefighting** | No comparable scenarios; decisions not auditable | Resolution Center with ≥8 seeded scenarios (demo tenant) |
| **Capacity blindness** | Overloaded work centers discovered late | Bottleneck map; cap-svc finite scheduling |
| **Leadership lag** | Executives see OTD after month-end | Command Center dashboards, cost of chaos |
| **AI distrust** | Black-box recommendations rejected | Shadow autonomy mode; XAI explanation on rescore; AI Trust dashboard |

### 3.2 Target Market & Opportunity

| Segment | Characteristics | IPE fit |
|---------|-----------------|---------|
| **Primary (Release 1)** | Mid-market discrete manufacturers on **Odoo** (MENA) | 8-service deploy; feasibility-first workflow |
| **Secondary (full demo)** | $50M–$500M discrete mfg pursuing APS without SAP rollout | 32/32 demo; faster PoC than suite vendors |
| **Not primary (as-is GTM)** | Fortune 500 multi-site SAP IBP replacements | Missing live SAP connector, enterprise SSO at scale |

**Release 1 pricing signal (spec 013):** $18K–30K/yr license + $12K–25K implementation — **needs business confirmation**.

### 3.3 Competitive Positioning (Summary)

IPE competes **against Excel + Odoo MRP** for Release 1, and **against Kinaxis / SAP IBP / o9** for full-profile enterprise demos. Differentiators: integrated feasibility queue + resolution + scheduling in one hub UI; faster local demo; MENA implementation story. Gaps vs leaders: production ERP connectors (non-Odoo), proven multi-site benchmarks, enterprise IdP.

*(See [Section 15](#15-competitive-context) for feature matrix.)*

---

## 4. Goals & Success Metrics

> **Note on versioning:** Section 4 layers metrics from **V5 Convergence** (foundational behaviors, spec 003), **v8.2.0** (current full product), and **Release 1** (customer go-live). “IPE V5.0 success” refers to spec 003 outcomes — still embedded in product behavior — not a separate deployed SKU.

### 4.1 V5 Convergence Goals (Spec 003 — Shipped v1.0.0)

| ID | Goal | Metric | Acceptance criteria | As-is |
|----|------|--------|---------------------|-------|
| V5-G1 | Closed-loop planning | Approved schedule in CDM + visible after refresh | Within 60s of approve; `cdm_work_order` updated | ✅ |
| V5-G2 | Planner trust (XAI) | ≥80% demo users understand slot choice | XAI panel on schedule/rescore | ✅ UI present; formal user study not recorded |
| V5-G3 | Data safety (MDR) | Block scheduling when MDR composite < 70% | cap-svc returns 503 / gate | ✅ Backend gate; MDR dashboard exists |
| V5-G4 | Disruption response | War Room top-3 mitigations | ≥3 recovery options on alert aggregate | ✅ Demo seed |
| V5-G5 | Financial clarity | Resolution shows $ impact | COGM, revenue, margin on scenario cards | ✅ Resolution Center |

### 4.2 v8.2.0 Business Goals (PRD §2.1)

| ID | Goal | Metric | As-is |
|----|------|--------|-------|
| G-01 | Reduce planning cycle time | ≥30% faster MO triage vs spreadsheet | 🟡 Not formally measured |
| G-02 | Improve OTD predictability | Feasibility score vs actual delay (MAPE) | 🟡 MAPE tracking scaffold; no production baseline |
| G-03 | Planner productivity | ≥3 scenarios evaluated per at-risk MO | ✅ Demo: ≥8 scenarios per MO |
| G-04 | Executive visibility | Single dashboard: OTD, delay root cause, cost of chaos | ✅ Command Center |
| G-05 | AI adoption with trust | Shadow → suggest → autonomous progression | ✅ `autonomy_mode` tenant setting; default shadow |

### 4.3 v8.2.0 Technical / Quality Gates

| Gate | Target | Evidence (as-is) |
|------|--------|------------------|
| Demo checkpoints | **32/32** | `scripts/run-full-demo.ps1 -Profile startrans` |
| Backend tests | **870+** passing | `docs/qa/full-test-suite-v8.2.0.txt` |
| Chaos | **6/6** | `docs/chaos/` |
| v8 integration | **5/5** | `tests/integration/test_v8_e2e.py` |
| k6 load (V5 R4) | 200 VU, p95 <5s, <2% errors | Documented in RELEASE_NOTES |
| CPM cascade (V6) | p95 <2s demo subset | cap-svc |
| Schedule solver | <90s for 3-MO demo subset | cap-svc OR-Tools |
| Copilot P95 | <180s | nlp-svc; Kong timeout 300s |

### 4.4 Release 1 Success Metrics (Spec 013)

| ID | Metric | Target | As-is (2026-06-30) |
|----|--------|--------|---------------------|
| R1-M1 | MOs visible in Control Tower from Odoo | 100% of active Star Trans MOs with BOM | 🟡 **2/2** Star Trans MOs synced locally; demo furniture MOs skipped (no BOM match) |
| R1-M2 | Sync success rate | >95% scheduled runs | ✅ Last full sync: `success` |
| R1-M3 | Post-sync feasibility score | Non-null for syncable MOs | ✅ Auto-rescore after commit fix: 2/2 at 82.5 |
| R1-M4 | Stack deploy time on 8GB VM | ≤10 minutes | 🟡 Compose documented; T037 manual validation pending |
| R1-M5 | Arabic planner path | Control Tower + nav | 🟡 Keys exist; native speaker QA pending |
| R1-M6 | Customer UAT sign-off | Signed acceptance checklist | ⬜ Pending |
| R1-M7 | Write-back to Odoo | Approved schedule updates MO dates | ✅ Gate 4/5 + activate.py tenant fallback |
| R1-M8 | Zero unresolved P0 data quality flags on go-live MOs | 0 flags | ✅ 0 flags on synced MOs |
| R1-M9 | HTTPS + Keycloak enterprise demo | 14/14 over `https://localhost:8443` | ✅ 2026-07-03 |

### 4.5 Enterprise Phase 2 Gate Metrics (Spec 015 — 2026-07-03)

| Gate | Script | Criterion | Status |
|------|--------|-----------|--------|
| **Gate 1** Observability | `scripts/monitoring/verify-gate1.sh` | 6 Grafana dashboards; 9/9 Prometheus targets UP | ✅ PASS |
| **Gate 2** Security | `scripts/security/verify-gate2.sh` | Network isolation; rate limit; CORS; SAST docs | ✅ PASS (Gate 2 smoke may fail intermittently in Gate 5 bundle) |
| **Gate 3** Multi-tenant quotas | `scripts/security/verify-gate3.sh` | Tenant quotas; Kafka consumer groups scoped | ✅ PASS |
| **Gate 4** Odoo bidirectional sync | `scripts/odoo/verify-gate4.sh` | Inbound sync + activate + conflict resolution | ✅ PASS |
| **Gate 5** Full E2E | `scripts/security/verify-gate5.ps1` | R1 14/14 + R2 5/5 HTTPS; enterprise flags ON; audit ≥3 rows | 🟡 **R1/R2 pass when run standalone**; bundle run had SSL alias bug (fixed); re-verify recommended |
| **k6 SLO** | `scripts/perf/k6-load-test.js` | P95 < 500ms; error rate < 5% | ❌ **FAIL** — Kong global 500 req/min vs high-VU load → mass 429 |
| **Git tag** | `v9.3.0-p2` | All gate fixes committed + tagged | ⬜ Pending (uncommitted changes; git safe.directory blocker) |

### 4.6 Release 2 Success Metrics (Spec 014)

| ID | Metric | Target | As-is (2026-07-03) |
|----|--------|--------|---------------------|
| R2-M1 | Outcomes OTD baseline API | 200 + valid payload | ✅ R2 demo step 1 |
| R2-M2 | ROI metrics API | 200 + valid payload | ✅ R2 demo step 2 |
| R2-M3 | Auto-propose after sync | `scenarios_proposed` in sync response | ✅ R2 demo step 3 |
| R2-M4 | Resolution scenarios available | ≥1 scenario | ✅ R2 demo step 4 |
| R2-M5 | Copilot Lite / planner-assist | Structured response < 3s | ✅ R2 demo step 5 |

---

## 5. User Personas & Workflows

### 5.1 Persona Catalog

| Persona | RBAC role | Primary goals | Pain points | Primary hubs (full) | Release 1 access |
|---------|-----------|---------------|-------------|---------------------|------------------|
| **Production Planner** | `planner` | Triage MOs, resolve constraints, build/approve schedule | Spreadsheet chaos; late material surprises | Planning | Control Tower, Resolution, Schedule |
| **Plant Manager** | `manager` | Approve schedules, authorize overtime/expedite | No single view of trade-offs | Planning, Command | Same as planner (no RBAC UI gate) |
| **Shop Supervisor** | `supervisor` | Monitor floor, acknowledge disruptions | Delay discovery too late | Command, Shop Floor | Command Center only (Shop Floor hidden in R1 nav) |
| **Shop Operator** | `operator` | Execute work orders, scan barcodes | Paper travelers | Shop Floor | Not in R1 nav |
| **Executive / VP Ops** | `executive` | OTD, margin, disruption cost | Delayed reporting | Command Center | Command Center |
| **Procurement Analyst** | `procurement` | Supplier risk, spend | Siloed PO data | Supply Chain | Hidden in R1 |
| **Quality Engineer** | `planner` / read | FPY, SPC | Quality separate from planning | AI & Governance | Hidden in R1 |
| **ESG Lead** | read | Carbon, circularity | Manual ESG spreadsheets | AI & Governance | Hidden in R1 |
| **System Administrator** | `admin` | Tenant config, autonomy mode | Odoo creds in JSONB (R1 gap) | Platform | Platform → Admin |
| **Auditor** | `auditor` | Read-only audit, KPIs | — | AI & Governance (compliance) | Limited |
| **Release 1 Buyer** | CEO / Ops Director | Feasibility before crisis; ROI vs Excel | ERP project fatigue | Planning (3 tabs) | Primary economic buyer (spec 013) |
| **Demo Engineer** | `admin` | 32/32 demo, Star Trans overlay | Wrong DB target for SQL | Platform + scripts | `prepare-startrans-demo.ps1` |

### 5.2 Planner Daily Workflow (Primary)

```
START → Login (/login)
  └─ Planning Hub
       ├─ [Release 1] Control Tower
       │    ├─ Review KPI cards (avg feasibility, orders at risk, OTD)
       │    ├─ Review SyncStatusBar (R1 only) — last Odoo sync
       │    ├─ Sort MO risk queue by feasibility_score ASC
       │    └─ Decision: score ≥ threshold?
       │         ├─ YES → Schedule → Refresh solver → Approve MOs
       │         └─ NO  → Resolution Center → Compare scenarios → Approve
       │                   └─ Schedule → Approve → [R1] Odoo activate write-back
       ├─ [Full only] Demand → Run sense cycle (if forecast stale)
       └─ [Full only] Scenarios → Create sandbox (if major disruption)
END
```

### 5.3 Executive Weekly Workflow

```
Login → Command Center
  ├─ Dashboard (alerts summary)
  ├─ Executive (OTD trend, P&L, S&OP gap)
  ├─ War Room (active disruptions, recovery options)
  └─ Cost of Chaos (7d/30d USD category breakdown)
```

### 5.4 Administrator Onboarding Workflow (Release 1)

```
Deploy release1 compose (deploy-release1.ps1)
  → Configure tenant Odoo creds (SQL or setup-odoo-integration.ps1)
  → Seed Odoo master data (seed-odoo-startrans.py) [customer env]
  → POST /api/v1/sync/run { "entity": "all" }
  → Verify Control Tower queue + data quality flags
  → Set autonomy_mode = shadow in Admin
  → Train planner on Control Tower → Resolution → Schedule path
```

### 5.5 Copilot Workflow (Full Profile Only)

```
AI & Governance → Copilot
  → Select agent role (planner | manager | supervisor | executive)
  → POST /api/v1/copilot/session
  → Natural language query (e.g. "What is blocking MO-ST-001?")
  → Review intent + structured response (180s timeout; fallback to Resolution Center)
```

---

## 6. Use Cases

### 6.1 Use Case Index

| ID | Name | Actor | Profile |
|----|------|-------|---------|
| UC-01 | Daily production health triage | Planner | Full + R1 |
| UC-02 | Constraint resolution | Planner, Manager | Full + R1 |
| UC-03 | Finite-capacity scheduling | Planner | Full + R1 |
| UC-04 | Excel project plan import | Planner | Full + R1 |
| UC-05 | Demand sensing and forecast | Planner | Full only |
| UC-06 | What-if scenario sandbox | Planner | Full only |
| UC-07 | Multi-echelon supply visibility | Planner, Executive | Full only |
| UC-08 | Copilot NL query | Planner | Full only |
| UC-09 | Executive disruption review | Executive | Full + R1 (partial pages) |
| UC-10 | Shop floor execution monitoring | Supervisor, Operator | Full only |
| UC-11 | Star Trans demo data load | Demo engineer | Full demo |
| UC-12 | Odoo ERP sync (Release 1) | Admin, System | R1 |
| UC-13 | Schedule write-back to Odoo | Planner | R1 |
| UC-14 | Post-sync feasibility rescore | System | R1 |

### 6.2 UC-01 — Daily Production Health Triage

| Attribute | Detail |
|-----------|--------|
| **Actors** | Production Planner |
| **Preconditions** | Authenticated; tenant has MOs in `cdm_manufacturing_order`; fea-svc healthy |
| **Main flow** | 1. Login. 2. Navigate to Planning → Control Tower. 3. Load KPIs from `/api/v1/feasibility/kpis`. 4. Load queue from `/api/v1/feasibility/queue`. 5. Sort by lowest `feasibility_score`. 6. Click **Resolve** on MO below threshold (e.g. <70). |
| **Alternative flows** | A1: WebSocket update refreshes queue row. A2: [R1] SyncStatusBar shows stale sync → trigger manual sync. A3: Copilot query (full profile). |
| **Edge cases** | Empty queue → run Odoo sync or demo seed. `unscorable=true` when data quality flag present. |
| **Success criteria** | Planner identifies top 3 at-risk MOs within 5 minutes |
| **Postcondition** | User navigates to Resolution or Schedule with `mo_id` context |

### 6.3 UC-12 — Odoo ERP Sync (Release 1)

| Attribute | Detail |
|-----------|--------|
| **Actors** | System (scheduler), Administrator (manual) |
| **Preconditions** | `cdm_tenant.erp_type='odoo'`; valid creds in `config` JSONB; Odoo reachable from connector container (`host.docker.internal:8069`) |
| **Main flow** | 1. Scheduler fires every 900s OR admin POST `/api/v1/sync/run`. 2. Connector authenticates via XML-RPC. 3. Sync engine upserts: products → work centers → customers → suppliers → BOMs → BOM lines + routing → MOs → demands → supply. 4. Commit CDM. 5. Post-sync rescore via fea-svc. 6. Write `cdm_sync_run` audit row. |
| **Alternative flows** | A1: Partial sync `{ "entity": "manufacturing_orders" }`. A2: REST adapter path via `/api/v1/erp/odoo/sync/all` (requires `ipe_connector` Odoo module). |
| **Edge cases** | Odoo field rename (v17 vs v19) → mapper error; MO skipped if no matching BOM/product. `default_code=False` → mapped to null. |
| **Success criteria** | `cdm_sync_run.status = success`; MO count > 0; rescored ≥1 |
| **Postcondition** | Control Tower reflects Odoo MOs |

### 6.4 UC-13 — Schedule Write-Back to Odoo

| Attribute | Detail |
|-----------|--------|
| **Actors** | Planner (approve), System (connector) |
| **Preconditions** | MO has `erp_mo_id`; AI suggested dates set; Odoo credentials valid |
| **Main flow** | 1. Planner approves schedule in UI. 2. POST `/api/v1/sync/odoo/activate` with MO IDs. 3. Connector writes `date_start`/`date_finished` to Odoo via XML-RPC. 4. Optional: unreserve + replan. 5. Chatter message posted. 6. CDM MO updated; conflict detection if Odoo changed dates after sync. |
| **Alternative flows** | A1: Odoo 17 fallback fields `date_planned_*` on write failure |
| **Edge cases** | Material reservation conflict → `MATERIAL_CONFLICT` reason. Missing `ipe_connector` → XML-RPC path still works for activate. |
| **Success criteria** | Odoo MO dates match IPE approved dates; no unresolved SYNC_CONFLICT flag |
| **Postcondition** | `ai_suggested_start/end` cleared; `ai_schedule_version` incremented |

*(Additional use cases UC-02 through UC-11 follow patterns in `docs/PRD-IPE-v8.2.0-ENTERPRISE.md` §4; unchanged in as-is product.)*

---

## 7. Functional Requirements

### 7.1 Authentication & Tenancy

| ID | Requirement | Business rule | Validation | Priority |
|----|-------------|---------------|------------|----------|
| FR-AUTH-01 | Authenticate via JWT (local) or Keycloak OIDC (POST-B) | Local: email + password → Bearer token | 401 on bad creds | Must |
| FR-AUTH-02 | Every API request carries tenant context | JWT claim or `X-Tenant-ID` header | 403 if missing | Must |
| FR-AUTH-03 | PostgreSQL RLS isolates tenant data | `app.current_tenant_id` session var | Cross-tenant read/write blocked (migration 035) | Must |
| FR-AUTH-04 | Session timeout configurable | Default 8h staging | — | Should |
| FR-AUTH-05 | Password storage | `{SHA-256}` hash in `cdm_user.password_hash` | Dev passwords `admin`/`demo` in non-prod only | Must |

### 7.2 Planning Hub

| ID | Requirement | Module | Acceptance | Priority |
|----|-------------|--------|------------|----------|
| FR-PLN-01 | Display feasibility queue | Control Tower | ≥1 MO when data present | Must |
| FR-PLN-02 | KPI cards: avg feasibility, orders at risk, bottlenecks | Control Tower | Loads from fea-svc | Must |
| FR-PLN-03 | Resolution scenarios per MO | Resolution | ≥8 for demo tenant | Must |
| FR-PLN-04 | OR-Tools schedule ≤90s (3-MO demo) | Schedule | cap-svc | Must |
| FR-PLN-05 | Approve schedule persists to CDM | Schedule | Survives refresh | Must |
| FR-PLN-06 | Excel .xlsx project plan upload | Schedule | Validates MO_ID, WC_CODE | Must (full); Should (R1) |
| FR-PLN-07 | Export MS Project XML | Schedule | Download action | Should |
| FR-PLN-08 | Demand sense cycle | Demand | Creates forecast rows | Must (full); Out (R1 nav) |
| FR-PLN-09 | Scenario create/simulate | Scenarios | KPI delta returned | Must (full); Out (R1 nav) |
| FR-PLN-10 | CPM cascade preview <2s | Schedule | Demo subset | Should |
| FR-PLN-11 | Sync status bar (R1) | Control Tower | Shows last sync from `/sync/status` | Must (R1) |
| FR-PLN-12 | Data quality badges on MOs | Control Tower | From `/sync/data-quality` | Must (R1) |

**Business rules:**

| ID | Rule |
|----|------|
| BR-PLN-01 | MOs with feasibility ≥85% may be approved to active schedule (guardrail; configurable) |
| BR-PLN-02 | `autonomy_mode=shadow` — AI never auto-applies without explicit human approval |
| BR-PLN-03 | Project plan `PLAN_CODE` must be consistent across all upload rows |
| BR-PLN-04 | MO sync skipped if no resolvable BOM for product (Release 1) |
| BR-PLN-05 | Unscorable MOs (data quality flag) excluded from auto-confirm queue |

### 7.3 Odoo Sync (Release 1)

| ID | Requirement | Status (as-is) |
|----|-------------|----------------|
| FR-R1-01 | MO upsert from `mrp.production` | ✅ |
| FR-R1-02 | BOM header + **BOM lines** + **routing operations** | ✅ (implemented; spec 013 doc stale) |
| FR-R1-03 | Work center sync | ✅ |
| FR-R1-04 | Product update path | ✅ |
| FR-R1-05 | Stock/material availability (`stock.quant`) | ⬜ R1.1 |
| FR-R1-06 | Scheduled sync every 15 min | ✅ APScheduler 900s |
| FR-R1-07 | Sync run audit log | ✅ `cdm_sync_run` |
| FR-R1-08 | Data quality flags | ✅ `cdm_data_quality_flag` |
| FR-R1-09 | SYNC_CONFLICT detection | ✅ When Odoo dates change post-sync |
| FR-R1-10 | Activate write-back | ✅ XML-RPC |
| FR-R1-11 | Odoo install guide | ✅ `docs/integration/ODOO-LOCAL-SETUP.md` |
| FR-R1-12 | Post-sync feasibility rescore | ✅ After DB commit |
| FR-R1-13 | Customer/supplier partner sync | ✅ |
| FR-R1-14 | Sale order line → demand | ✅ Odoo 19: `scheduled_date` field |
| FR-R1-15 | Purchase order line → supply | ✅ |
| FR-R1-16 | OTD baseline capture API | ⬜ R1.1 |

### 7.4 Command Center, Supply, AI, Platform

*(Full requirements FR-CC-*, FR-SC-*, FR-AI-*, FR-PLT-* as documented in `docs/PRD-IPE-v8.2.0-ENTERPRISE.md` §5.3–5.6 — all implemented in full profile; subset visible in Release 1 nav.)*

### 7.5 Integrations

| ID | Requirement | Status |
|----|-------------|--------|
| FR-INT-01 | Odoo fetch MO/BOM/material | ✅ XML-RPC (live local); REST with addon |
| FR-INT-02 | Odoo publish approved schedule | ✅ activate.py |
| FR-INT-03 | Kafka `ipe.supply.adjusted` → demand-svc | ✅ Full stack only |
| FR-INT-04 | Stripe billing | Mock / POST-B |
| FR-INT-05 | LLM Ollama → OpenRouter → Anthropic | ✅ Full stack |
| FR-INT-06 | SAP/D365 CDM mappers | Scaffold only |

---

## 8. Feature Specifications

| Feature | Purpose | User benefit | Acceptance criteria | Dependencies | Priority | Introduced |
|---------|---------|--------------|---------------------|--------------|----------|------------|
| **Control Tower** | MO risk visibility | Start day with prioritized queue | Queue loads; KPIs; Resolve links | fea-svc, dpe-svc | Must | v1.0.0 |
| **Resolution Center** | Scenario trade-offs | Data-driven decisions | Scenarios with cost/delivery | dpe-svc, res-svc | Must | v1.0.0 |
| **Schedule + OR-Tools** | Constraint-aware Gantt | Feasible capacity plan | Approve persists; Gantt renders | cap-svc | Must | v1.0.0 |
| **Excel plan upload** | ERP-delay workaround | Planner-native import | .xlsx validates; version history | cap-svc | Must | v1.0.0 |
| **MDR Gate** | Data readiness | Block bad-data scheduling | <70% blocks solver | dpe-svc | Must | v1.0.0 (V5) |
| **Tariff shock** | Landed cost what-if | Supply risk | Affected MOs + substitutes | dpe-svc | Should | v6.0.0 |
| **Visual CPM** | Critical path | Delay impact preview | p95 <2s demo | cap-svc | Should | v6.0.0 |
| **Cost of Chaos** | Financial disruption | Executive $ view | 7d category breakdown | dpe-svc | Should | v6.0.0 |
| **War Room** | Alert aggregation | Mitigation options | ≥8 alerts demo | alert-svc | Should | v6.0.0 |
| **Hub consolidation** | Navigation | Reduced cognitive load | 6 hubs; legacy redirects | web | Must | v7.1 |
| **Copilot sessions** | NL interface | Faster triage | 4 roles; CP30 pass | nlp-svc | Must (full) | v8.0.0 |
| **Demand sensing** | Statistical forecast | Short-term demand | Sense cycle creates rows | demand-svc | Must (full) | v8.0.0 |
| **Scenario workbench** | Sandbox KPIs | Safe what-if | Simulate returns KPIs | scenario-svc | Must (full) | v8.0.0 |
| **Supply network** | Multi-echelon | Network resilience | 4 plants, 6 lanes | supply-svc | Must (full) | v8.1.0 |
| **Order / ATP** | Promise management | Customer commit dates | Order create + ATP | order-svc | Must (full) | v8.1.0 |
| **Equipment health** | RUL / sensors | Maintenance planning | Fleet scores | equipment-svc | Should | v8.1.0 |
| **Design AI** | Material recommend | Engineering assist | CP28 pass | material-svc | Should | v8.2.0 |
| **Procurement ESG** | Supplier compliance | Responsible sourcing | CP29 pass | procurement-svc | Should | v8.2.0 |
| **Quality dashboard** | SPC / FPY | Quality in planning UI | CP32 pass | quality-svc | Should | v8.2.0 |
| **Sustainability** | Carbon / ESG | Board reporting | CP31 pass | sustain-svc | Should | v8.2.0 |
| **Odoo sync engine** | Live ERP ingest | No spreadsheet duplicate | Full sync success | connector | Must (R1) | spec 013 |
| **Sync status bar** | ERP transparency | Trust in data freshness | Shows last sync time | connector, web | Must (R1) | spec 013 |
| **Arabic MVP** | MENA UX | Local planner adoption | ar.json keys for CT + nav | web i18n | Must (R1) | spec 013 |
| **Release 1 profile** | Deploy slice | 8GB VM viable | 3 planning tabs; 3 hubs | compose, web | Must (R1) | spec 013 |
| **Keycloak SSO** | Enterprise auth | IT compliance | AUTH_PROVIDER=keycloak | POST-B | Should | scaffold v8 |
| **Admin Odoo config UI** | Self-service ERP | Ops without SQL | Test + save creds | — | Should (R1.1) | ⬜ Not built |

---

## 9. Business Scenarios

### BS-01 — Star Trans: Copper delay on utility transformer (Full Demo)

| Step | Actor | Action | Success metric |
|------|-------|--------|----------------|
| 1 | Planner | Sees MO at low feasibility, `material` constraint | Identified <5 min |
| 2 | Planner | Evaluates expedite / substitute / split scenarios | Scenario selected |
| 3 | Planner | Re-schedules (solver or Excel upload) | Gantt updated |
| 4 | Executive | War Room cost of delay | $ impact shown |
| 5 | Copilot | Confirms blocker in NL | <180s (full profile) |

**Outcome:** 32/32 demo pass; client confirms weekly-use intent.

### BS-02 — Star Trans Release 1: Live Odoo morning triage

| Step | Actor | Action | Success metric |
|------|-------|--------|----------------|
| 1 | System | 15-min Odoo sync runs overnight | `cdm_sync_run.status=success` |
| 2 | Planner | Opens Control Tower; sees TR-500 / TR-1000 MOs | 2 MOs at 82.5 score |
| 3 | Planner | Reviews material constraint; opens Resolution | Scenario compared |
| 4 | Planner | Approves schedule; activate to Odoo | Odoo MO dates updated |
| 5 | Manager | Executive dashboard OTD trend | Baseline captured (R1.1 gap) |

**Outcome:** Feasibility-first workflow on live ERP — **locally validated**; customer UAT pending.

### BS-03 — Monthly S&OP demand review (Full Profile)

| Step | Actor | Action | Success metric |
|------|-------|--------|----------------|
| 1 | Planner | Demand → Run sense cycle | Forecast +14 days |
| 2 | Planner | Scenarios → "+10% utility demand" | KPI delta visible |
| 3 | Manager | Supply network capacity review | Bottleneck lane ID'd |

**Outcome:** Forecast MAPE <15% on demo history (production target — not formally validated).

### BS-04 — Executive quarterly review (Full Profile)

| Step | Actor | Action | Success metric |
|------|-------|--------|----------------|
| 1 | Executive | OTD trend + delay breakdown | 2+ periods |
| 2 | Executive | Quality FPY + Sustainability ESG | Single session |
| 3 | Executive | AI Trust adoption (shadow mode) | Explained without planner |

**Outcome:** Single-pane review <15 min.

---

## 10. User Interface & Navigation

### 10.1 Information Architecture

```
App
├── /login (public)
└── Authenticated
    ├── Sidebar (hub level)
    │   ├── Planning Hub          [/planning/*]
    │   ├── Command Center        [/command-center/*]
    │   ├── Supply Chain Hub      [/supply-chain/*]     [full only in nav]
    │   ├── AI & Governance       [/ai-governance/*]    [full only in nav]
    │   ├── Shop Floor            [/shop-floor]           [full only in nav]
    │   └── Platform              [/platform/*]
    └── Header (user, sign out)
```

### 10.2 Route Map

#### Planning Hub (`/planning`)

| Route | Page | R1 nav | Data sources |
|-------|------|--------|--------------|
| `/planning/dashboard` | Planning dashboard | Hidden R1 | dashboard APIs |
| `/planning/demand` | Demand forecast | Hidden R1 | demand-svc |
| `/planning/scenarios` | Scenario workbench | Hidden R1 | scenario-svc |
| `/planning/control-tower` | Control Tower | **Visible R1** | fea-svc queue/kpis; WebSocket |
| `/planning/resolution` | Resolution Center | **Visible R1** | res-svc, dpe-svc |
| `/planning/schedule` | Schedule + Gantt | **Visible R1** | cap-svc |

#### Command Center (`/command-center`)

| Route | Page | R1 nav |
|-------|------|--------|
| `/command-center/outcomes` | Outcomes (R2) | Visible R1 | dpe-svc analytics |
| `/command-center/dashboard` | Command dashboard | Visible |
| `/command-center/war-room` | War Room | Visible |
| `/command-center/executive` | Executive | Visible |
| `/command-center/equipment` | Equipment health | Visible |
| `/command-center/cost-of-chaos` | Cost of Chaos | Visible |

#### Supply Chain (`/supply-chain`) — full profile nav only

Supply Planning, Orders, Procurement, Tariff, SCN Portal, Inventory.

#### AI & Governance (`/ai-governance`) — full profile nav only

Copilot, Design AI, AI Trust, MDR, Compliance, Quality, Sustainability.

#### Platform (`/platform`)

| Route | Page | R1 nav |
|-------|------|--------|
| `/platform/admin` | Admin config | Visible |
| `/platform/onboarding` | Onboarding wizard | Visible |
| `/platform/ml-ops` | MLOps | Visible |

**Legacy redirects:** `/control-tower` → `/planning/control-tower`; `/schedule` → `/planning/schedule`; etc.

### 10.3 Key Screen Field Specifications

#### Login (`/login`)

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| email | email input | Yes | Must match `cdm_user.email` |
| password | password input | Yes | Hash verify |

#### Control Tower

| Element | Type | Fields / columns |
|---------|------|------------------|
| KPI: Avg Feasibility | metric tile | number (0–100) |
| KPI: Orders at Risk | metric tile | count |
| KPI: Active Bottlenecks | metric tile | count |
| KPI: OTD | metric tile | % (hidden in shadow mode) |
| SyncStatusBar | status bar (R1) | last sync time, status, entity counts |
| MO Risk Queue | table | mo_id, product_name, customer_name, required_date, feasibility_score, primary_constraint, erp_mo_id |
| Resolve button | link | → `/planning/resolution?mo_id=` |
| Bottleneck map | bar chart | work_center_name, utilization_pct |

#### Schedule

| Element | Type | Options |
|---------|------|---------|
| Strategy | dropdown | hybrid, EDD, throughput, revenue, inventory |
| Delivery focus | range 0–100 | — |
| Efficiency focus | range 0–100 | — |
| Capacity buffer | range 0–20 | — |
| Allow overtime | checkbox | — |
| View source | radio | AI/solver schedule \| Uploaded project plan |
| Plan selector | dropdown | PLAN_CODE list |
| Upload mode | radio | new \| update |
| File | file input | .xlsx only |
| Notes | text | optional |
| Gantt | visual | operations by work center |

#### Admin — Configuration

| Field | Type | Values |
|-------|------|--------|
| Priority weights | number inputs (0–1) | per key from API |
| Auto-confirm threshold | number 0–100 | — |
| Planner threshold | number 0–100 | — |
| autonomy_mode | toggle | shadow \| suggest \| autonomous |

#### Copilot (full profile)

| Field | Type | Values |
|-------|------|--------|
| Agent role | select | planner, manager, supervisor, executive |
| Query | text input | — |

### 10.4 Release Profile Behavior

| Setting | Env var | `full` (default) | `release1` |
|---------|---------|------------------|------------|
| Visible hubs | `VITE_RELEASE_PROFILE` | All 6 | planning, command-center, platform |
| Planning tabs | — | 6 tabs | control-tower, resolution, schedule |
| SyncStatusBar | `IS_RELEASE1` | Hidden | Shown |
| Copilot | — | Available | Hidden from nav |

**⚠️ Ambiguity:** Hidden routes remain in router; direct URL access may still load full pages in Release 1 build.

---

## 11. Authorization, Roles & Permissions

### 11.1 Role Definitions

| Role | Description |
|------|-------------|
| `admin` | Full tenant configuration, user management |
| `planner` | Planning write, approve, solver, scenarios |
| `manager` | Approve schedules, solver, cost optimize |
| `supervisor` | Read, acknowledge disruptions, view schedule |
| `operator` | Read, write own work order progress |
| `executive` | Read KPIs only |
| `auditor` | Read audit logs, KPIs, scenarios |
| `procurement` | Read/write procurement views |

### 11.2 Permission Matrix (Backend — `ipe_shared/auth/rbac.py`)

| Permission | admin | planner | manager | supervisor | operator | executive | auditor | procurement |
|------------|:-----:|:-------:|:-------:|:----------:|:--------:|:---------:|:-------:|:-----------:|
| read | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| write | ✅ | ✅ | ✅ | — | own | — | — | ✅ |
| approve | ✅ | ✅ | ✅ | — | — | — | — | — |
| run_solver | ✅ | ✅ | ✅ | — | — | — | — | — |
| view_copilot | ✅ | ✅ | ✅ | ✅ | — | — | — | — |
| run_scenario | ✅ | ✅ | ✅ | — | — | — | — | — |
| admin / manage_users | ✅ | — | — | — | — | — | — | — |
| view_audit_logs | ✅ | — | — | — | — | — | ✅ | — |
| acknowledge_disruption | ✅ | — | — | ✅ | — | — | — | — |

### 11.3 UI Enforcement (As-Is Gap)

| Layer | Enforcement | Status |
|-------|-------------|--------|
| API | JWT + `require_roles()` / `require_permission()` on selected endpoints | ✅ Partial (not all routes) |
| Web routes | `ProtectedRoute` — authentication only | ⚠️ **No role-based route guards** |
| Copilot | Agent role selector (UX persona, not access control) | ✅ |
| Header | Does not display user role | — |

**Stakeholder decision required (OQ-3):** Implement route-level RBAC in web app to match backend matrix.

### 11.4 Data Visibility Rules

| Rule | Mechanism |
|------|-----------|
| Tenant isolation | PostgreSQL RLS on `tenant_id` tables |
| Executive read-only | Backend permissions; not enforced in UI |
| Audit log immutability | Append-only `cdm_audit_log` |
| Cross-tenant MO access | Blocked by RLS |

### 11.5 Compliance Constraints

| Constraint | Staging (as-is) | Production target |
|------------|-----------------|-------------------|
| JWT secret | Dev placeholder in compose | Vault rotation (POST-B) |
| SSO | Local login | Keycloak / Azure AD (POST-B) |
| Odoo password storage | Plaintext in `cdm_tenant.config` JSONB | Encrypted vault (R1.1 — **security gap**) |
| GDPR DSAR | API scaffold | Legal review (POST-B) |
| FDA 21 CFR Part 11 | E-sign scaffold | Validated deployment (POST-B) |
| SOC2 | Controls scaffold | Assessment (POST-B) |

---

## 12. Reports & Dashboards

| Dashboard / Report | Key metrics | Data sources | Filters | Refresh | Audience |
|--------------------|-------------|--------------|---------|---------|----------|
| **Control Tower KPIs** | avg_feasibility_score, orders_at_risk, active_bottlenecks, OTD | fea-svc `/feasibility/kpis` | tenant | On load + WS | Planner |
| **MO Risk Queue** | feasibility_score, primary_constraint, product_name, erp_mo_id | fea-svc `/feasibility/queue` | constraint, score | Real-time WS | Planner |
| **Sync Status (R1)** | last_sync time, entity_counts, error_summary | connector `/sync/status` | — | On load | Planner, Admin |
| **Data Quality Flags (R1)** | flag_code, message, mo_id | connector `/sync/data-quality` | unresolved | On load | Admin |
| **Executive Summary** | OTD trend, completed MO count | dpe-svc analytics | period | Daily | Executive |
| **Delay Breakdown** | cause category, minutes, $ | cdm_delay_event | category | Daily | Executive, Planner |
| **War Room** | alert count, severity, recovery plans | alert-svc, dashboard | severity | Real-time | Supervisor |
| **Cost of Chaos** | USD by category | analytics | 7d / 30d | Daily | Executive |
| **Demand Forecast** | value, bounds, model_version | demand-svc | product, horizon | On sense cycle | Planner |
| **Scenario KPIs** | simulated metrics | scenario-svc | scenario_id | On simulate | Planner |
| **Supply Network** | facilities, lanes, transit days | supply-svc | — | On load | Planner |
| **SCN Scorecards** | supplier score, lead time | scn-svc / cdm_supplier | tier | Weekly | Procurement |
| **Procurement Spend** | total by category | procurement-svc | period | Monthly | Procurement |
| **Equipment Health** | health_score by asset | equipment-svc | — | Hourly | Maintenance |
| **Quality Dashboard** | defect_rate_pct, FPY | quality-svc | — | Daily | Quality |
| **Sustainability** | esg_score, carbon tCO2e | sustain-svc | — | Monthly | ESG |
| **AI Trust** | adoption, model accuracy | dpe-svc ai-trust | — | Daily | Admin |
| **MDR Gate** | composite score, gate status | dpe-svc MDR | — | On demand | Admin, Planner |
| **Compliance KPIs** | regulatory metrics | fea-svc `/feasibility/compliance-kpis` | — | On load | Auditor |
| **Shop Floor** | WO progress by WC | shop-floor API | WC, status | Real-time | Operator |

---

## 13. Integration Requirements

### 13.1 API Gateway

| Item | Value |
|------|-------|
| Gateway | Kong 3.x @ `:8000` (HTTP) / `:8443` (HTTPS TLS) |
| Auth headers | `Authorization: Bearer <JWT>`, `X-Tenant-ID: <uuid>` |
| Auth modes | `AUTH_MODE=local` (dev) \| `AUTH_MODE=keycloak` (enterprise stack) |
| Rate limit | **500 req/min** global (enterprise); 200 req/min documented in earlier profiles — **⚠️ conflicts with high-VU k6** |
| Max body | 10 MB |
| Release 1 routes | `kong.release1.yml` — subset of services |
| Enterprise CORS | HTTPS origins configured in `ipe-common.env` when audit middleware ON |

### 13.2 Connector API (Odoo)

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/v1/sync/run` | Full/partial sync | JWT + tenant |
| GET | `/api/v1/sync/status` | Last sync run | JWT + tenant |
| GET | `/api/v1/sync/data-quality` | Open DQ flags | JWT + tenant |
| POST | `/api/v1/sync/odoo/activate` | Write-back MO dates | JWT + tenant |
| POST | `/api/v1/ipe/action` | Inbound Odoo webhook | HMAC + tenant |
| GET | `/api/v1/erp/odoo/health` | REST adapter health | JWT |
| GET | `/api/v1/erp/odoo/pull/{domain}` | REST pull preview | JWT |
| POST | `/api/v1/erp/odoo/sync/all` | Sync (`xmlrpc` \| `rest`) | JWT |

**Sync request body (optional overrides):**

```json
{
  "entity": "all | products | work_centers | boms | bom_details | customers | suppliers | manufacturing_orders | demands | supply",
  "odoo_url": "http://host.docker.internal:8069",
  "odoo_db": "starttrans1",
  "odoo_username": "string",
  "odoo_password": "string"
}
```

### 13.3 Odoo Field Mapping (XML-RPC — As-Is)

| Odoo model | CDM entity | Key fields |
|------------|------------|------------|
| `product.product` | `cdm_product` | id→erp_source_id, name, default_code→internal_ref, type→source_type |
| `mrp.workcenter` | `cdm_work_center` | id, name, code, time_efficiency |
| `mrp.bom` | `cdm_bill_of_material` | id, product_id |
| `mrp.bom.line` | `cdm_bom_line` | product_id, product_qty, tenant_id |
| `mrp.routing.workcenter` | `cdm_routing_operation` | sequence, workcenter_id, time_cycle_manual |
| `mrp.production` | `cdm_manufacturing_order` | id→erp_mo_id, date_start/finished, state |
| `sale.order.line` | `cdm_demand_line` | scheduled_date (Odoo 19), product_uom_qty |
| `purchase.order.line` | `cdm_supply_order` | date_planned→expected_date |
| `res.partner` | `cdm_customer` / `cdm_supplier` | customer_rank, supplier_rank |

**⚠️ Odoo 17 vs 19:** Mappers include fallbacks (`date_planned_start`/`date_finished` vs `date_start`/`date_finished`). MO sync fields exclude Odoo 17-only names when targeting v19.

### 13.4 Feasibility API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/feasibility/queue` | Control Tower MO list |
| GET | `/api/v1/feasibility/kpis` | KPI tiles |
| POST | `/api/v1/feasibility/rescore/{mo_id}` | Recompute score; persist to MO |
| GET | `/api/v1/feasibility/compliance-kpis` | Compliance dashboard |

**Gate weights (default):** demand 5%, BOM 5%, material 35%, capacity 30%, labor 25%.

### 13.5 Conceptual Data Flow

```
Odoo ERP
  │ XML-RPC (primary R1) / REST (optional ipe_connector addon)
  ▼
connector (OdooSyncEngine)
  │ upsert + data quality validation
  ▼
PostgreSQL CDM (cdm_*)
  │ post-commit rescore
  ▼
fea-svc (feasibility_score, primary_constraint)
  │
  ▼
Web Control Tower ← WebSocket (fea-svc /ws)
  │
  ├─► Resolution Center (scenarios)
  └─► Schedule (cap-svc OR-Tools) ──► activate ──► Odoo write-back
```

### 13.6 Performance Considerations

| Integration | Target | As-is |
|-------------|--------|-------|
| Full Odoo sync | <60s typical | ~40–60s locally (70 products, 10 MOs) |
| fea-svc rescore | <5s per MO | ✅ ~instant locally |
| Kong → connector | Must not timeout on sync | Client timeout 300s recommended |
| Kafka consumers | Full stack only | Not in release1 compose |

---

## 14. Technical Architecture

### 14.1 Full Stack Topology

```
Browser (React/Vite :8082)
        │
        ▼
Kong API Gateway (:8000)
        │
        ├── dpe-svc (:8001) — auth, dashboard, resolution, analytics, admin
        ├── mat-svc (:8002) — material ATP, netting
        ├── cap-svc (:8003) — scheduling, CPM, project plans
        ├── fea-svc (:8004) — feasibility, WebSocket
        ├── res-svc (:8005) — resolution scenarios
        ├── del-svc (:8006) — delay classification
        ├── nlp-svc (:8007) — copilot
        ├── connector (:8009 / host :8016) — Odoo sync
        ├── demand-svc (:8040), scenario-svc (:8050)
        ├── supply-svc (:8060), order-svc (:8070), equipment-svc (:8061)
        ├── material-svc (:8090), procurement-svc (:8100)
        ├── alert, sustain, quality, scn, network, rec, ml-svc
        │
PostgreSQL 16 (:5433) — Alembic migrations 001–036
Redis — cache / sessions
Kafka — event mesh (full stack)
Ollama — local LLM (host or container)
```

### 14.2 Release 1 Topology

```
Browser → Kong (:8000) → dpe-svc | fea-svc | cap-svc | mat-svc | connector
                              ↓
                    PostgreSQL + Redis
                              ↓
              Odoo (:8069) via host.docker.internal
```

**8 containers:** db, redis, kong, dpe-svc, fea-svc, cap-svc, mat-svc, connector.

### 14.3 Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite 5, TypeScript, Redux (auth), Tailwind |
| API | FastAPI, Python 3.14+, Pydantic v2 |
| Solver | Google OR-Tools CP-SAT (cap-svc) |
| Database | PostgreSQL 16, RLS, Alembic |
| Gateway | Kong 3.x (declarative YAML) |
| Messaging | Kafka (full profile) |
| LLM | Ollama, OpenRouter, Anthropic (full profile) |
| ERP | Odoo 17–19 XML-RPC; optional REST addon |
| Container | Docker Compose (dev, release1) |

### 14.4 Core Data Model (CDM)

| Entity | Table | Key relationships |
|--------|-------|-------------------|
| Tenant | `cdm_tenant` | Root; `config` JSONB for Odoo creds |
| User | `cdm_user` | tenant_id, role, password_hash |
| Product | `cdm_product` | BOM, MO, demand |
| BillOfMaterial | `cdm_bill_of_material` | product_id, erp_source_id |
| BomLine | `cdm_bom_line` | bom_id, component_id, tenant_id |
| RoutingOperation | `cdm_routing_operation` | bom_id, work_center_id |
| WorkCenter | `cdm_work_center` | routing, schedule |
| ManufacturingOrder | `cdm_manufacturing_order` | product, bom, feasibility_score |
| DemandLine | `cdm_demand_line` | product, customer |
| SupplyOrder | `cdm_supply_order` | product, supplier |
| ResolutionScenario | `cdm_resolution_scenario` | mo_id |
| SyncRun | `cdm_sync_run` | tenant audit |
| DataQualityFlag | `cdm_data_quality_flag` | mo_id, flag_code |
| DelayEvent | `cdm_delay_event` | mo_id, cause |
| Plant / TransferRoute | `cdm_plant`, `cdm_transfer_route` | supply network (migration 034) |
| v8 entities | `copilot_session`, `demand_forecast`, `planning_scenario`, etc. | migrations 029–031 |

### 14.5 Scalability & Security (As-Is)

| Concern | Full stack | Release 1 |
|---------|------------|-----------|
| Horizontal scale | Kong + stateless services; DB single instance | Single VM target (8GB) |
| Secrets | Env vars in compose | ⚠️ Odoo password in DB JSONB |
| Network | CORS on Kong; internal Docker network | host.docker.internal for Odoo |
| Backup | Documented in runbooks | Customer responsibility |

---

## 15. Competitive Context

> **Market clarification:** IPE competes in **Advanced Planning & Scheduling (APS) / S&OP** for discrete manufacturing — **not** the AI marketing / MarTech space. References to "NEXUS" in external templates refer to a **separate out-of-scope product** (NEXUS Social). IPE competitive set = **SAP IBP + PP/DS, Kinaxis Maestro, o9, Blue Yonder, Oracle SCM Cloud**, and **Excel + Odoo MRP** for Release 1.

### 15.1 Competitor Set

| Vendor | Product | Primary strength |
|--------|---------|------------------|
| SAP | IBP + PP/DS | ERP-native, deep install base |
| Kinaxis | Maestro | Concurrent planning, scenarios |
| o9 Solutions | o9 platform | AI/ML forecasting, IBP |
| Blue Yonder | Luminate | Retail/CPG planning |
| Oracle | SCM Cloud Planning | Suite integration |
| **Excel + Odoo MRP** | — | **Release 1 direct competitor** |

### 15.2 Feature Comparison Matrix

| Capability | IPE v8.2.0 (full) | IPE Release 1 | SAP IBP | Kinaxis | Excel+Odoo |
|------------|:-----------------:|:-------------:|:-------:|:-------:|:----------:|
| Feasibility / risk queue | ✅ | ✅ | ✅ | ✅ | ❌ |
| Scenario comparison | ✅ | ✅ (seeded) | ✅ | ✅✅ | ❌ |
| Finite capacity scheduling | ✅ OR-Tools | ✅ | ✅ | ✅ | Partial |
| Excel plan upload | ✅ | ✅ | ✅ | ✅ | ✅ |
| Live Odoo sync | ✅ (validated local) | ✅ | N/A | Add-on | Native ERP |
| NL copilot | ✅ | ❌ (hidden) | SAP Joule | Limited | ❌ |
| Multi-echelon network | ✅ demo | ❌ | ✅✅ | ✅✅ | ❌ |
| Demand sensing ML | ✅ | ❌ | ✅ | ✅ | ❌ |
| ESG / quality same UI | ✅ | ❌ | Separate | Partial | ❌ |
| Time to local demo | ✅ hours | ✅ ~10 min compose | Months | Weeks | Days |
| Enterprise SSO | POST-B | ❌ | ✅ | ✅ | N/A |
| Proven multi-site scale | ❌ | ❌ | ✅ | ✅ | N/A |
| MENA implementation story | ✅ (target) | ✅ | Partner network | Partner | Local |

**Positioning:** IPE targets **mid-market discrete manufacturers** needing APS + optional AI in one hub UI with faster PoC than suite rollouts. Release 1 competes on **feasibility-before-the-shift** vs manual Excel+Odoo workflows.

---

## 16. Data & Privacy

### 16.1 Data Collection & Storage

| Data class | Storage | Retention (as-is) |
|------------|---------|-------------------|
| User credentials | `cdm_user.password_hash` | Until deleted |
| Tenant config / Odoo creds | `cdm_tenant.config` JSONB | Until updated |
| Manufacturing master | CDM tables | Tenant lifecycle |
| Sync audit | `cdm_sync_run` | No automatic purge documented |
| Audit log | `cdm_audit_log` | Append-only |
| Copilot sessions | `copilot_session` (v8) | **Retention policy not defined — flag for legal** |
| LLM prompts | Transient / service logs | PII redaction in nlp-svc responses |

### 16.2 GDPR / Compliance (As-Is)

| Requirement | Status |
|-------------|--------|
| DSAR export API | Scaffold in dpe-svc (`/dsar`) — POST-B activation |
| Consent tracking | `gdpr_consent` table scaffold |
| Right to erasure | Not fully automated — **stakeholder input required** |
| Data residency | Single-region PostgreSQL — customer deploy choice |
| SOC2 controls | `soc2_control` scaffold |

### 16.3 Privacy Safeguards

| Safeguard | Implementation |
|-----------|----------------|
| Tenant RLS | PostgreSQL policies |
| JWT expiry | Configurable |
| Webhook HMAC | `cdm_tenant.api_secret` for `/ipe/action` |
| Copilot PII | Redaction in response text (nlp-svc) |
| Production secrets | POST-B: vault, not compose env |

---

## 17. Implementation Roadmap

### 17.1 Completed Phases (As-Is)

| Phase | Scope | Status | Evidence |
|-------|-------|--------|----------|
| 0–2 | Stabilization + V5 convergence | ✅ | v1.0.0 tag, spec 003 |
| 3 | V6 AI-first | ✅ | v6.0.0, chaos 6/6 |
| 4 | v6.1 hardening | ✅ | JWT/TLS runbooks |
| 5 | v7.0 hub + LLM | ✅ | spec 006, Ollama |
| 6–8 | v8 U1–U8 | ✅ | migrations 029–031, 32/32 |
| 9 | v8.2 validation | ✅ | spec 010, QA-001–010 |
| 10 | Release 1 engineering | 🟡 90% | spec 013; **14/14 HTTPS demo**; customer UAT blocked |
| 11 | Release 2 commercial | 🟡 85% | spec 014; **5/5 demo**; Odoo write-back C+D |
| 12 | Enterprise Phase 0–2 | 🟡 70% | spec 015; Gates 1–5 pass; k6 + tag pending |

### 17.2 Active Phase — Enterprise Phase 2 Close (`v9.3.0-p2`)

| Milestone | Dependencies | Owner | Target | Status |
|-----------|--------------|-------|--------|--------|
| E2-M1 | Gate 1–5 scripts green | Eng | 2026-07-03 | 🟡 Individual gates pass; full Gate 5 re-run after `demo-http.ps1` fix |
| E2-M2 | k6 SLO profile under rate limit | Eng | Phase 2 close | ❌ Blocked — design: SLO profile ≤8 req/s vs stress profile |
| E2-M3 | Commit gate fixes + tag `v9.3.0-p2` | Eng + PO | After E2-M1/M2 | ⬜ Uncommitted |
| E2-M4 | Sync Speckit artifacts (`015/tasks.md`, `feature.json`) | PM | Post-tag | ⬜ Stale |
| E2-M5 | OTel + Loki (T063–T064) | Eng | Phase 2 remainder | ⬜ Not started |

### 17.3 Active Phase — Release 1 Go-Live (Star Trans)

| Milestone | Dependencies | Owner | Target |
|-----------|--------------|-------|--------|
| M1: Signed SOW | Legal | Business | **Blocked** |
| M2: Customer Odoo staging access | Customer IT | Customer | **Blocked** |
| M3: Live UAT sync (all Star Trans MOs) | M2 | Eng + Customer | Pending |
| M4: `ipe_connector` install (optional REST) | Admin PowerShell on Odoo host | Customer IT | Pending |
| M5: Arabic QA (native speaker) | M3 | Product | Pending |
| M6: 8GB VM deploy validation (T037) | Hardware | Ops | Pending |
| M7: Admin Odoo config UI (R1.1) | Eng | Eng | Post-UAT |
| M8: Tag `v9.0.0-r1` | M3 + M5 + sign-off | Eng | Pending |

### 17.4 Future Phases (Deferred — Not As-Is)

| Phase | Scope | Rationale |
|-------|-------|-----------|
| R2 nav expansion | Copilot, demand, scenarios in customer nav | Not in Star Trans SOW v1 |
| R2 Stream E | Managed SaaS self-service | Moved to 015 Phase 4 |
| POST-B | Stripe live | Mock + adapter scaffold |
| Phase 1 (015) | Helm/K8s HA all 22 services | After Phase 2 close |
| Phase 3 (015) | SAP S/4 + D365 connectors | Customer #2+ |
| R3 | Full Arabic (15 screens) | R2 |

### 17.5 Resource Requirements (Release 1)

| Role | Effort |
|------|--------|
| Implementation engineer | 2–4 weeks on-site/remote |
| Customer IT (Odoo admin) | 1–2 days module install + creds |
| Planner champion | 4 hrs training (see R1-TRAINING-CURRICULUM.md) |
| Infrastructure | 8GB RAM Windows/Linux VM or cloud equivalent |

---

## 18. Risks & Mitigation

| ID | Risk | Likelihood | Impact | Mitigation (as-is / planned) |
|----|------|------------|--------|------------------------------|
| R-01 | Odoo custom fields break mappers | High | Sync partial/fail | Data quality flags; field mapping worksheet with customer IT |
| R-02 | Odoo version drift (17 vs 19) | Medium | MO/date field errors | Mapper fallbacks; document canonical version (OQ-1) |
| R-03 | Plaintext Odoo password in DB | High | Security audit fail | R1.1 encrypted vault; env-based secrets |
| R-04 | No UI RBAC | Medium | Unauthorized approve | Backend permissions exist; UI gates planned |
| R-05 | Customer UAT delay | High | Revenue delay | Parallel second prospect (R-B4); local validation continues |
| R-06 | 8GB VM under-resourced | Medium | Slow solver/sync | Release 1 scope trim; cap subset MOs |
| R-07 | ipe_connector install blocked (Windows permissions) | Medium | REST path unavailable | XML-RPC path sufficient for R1 |
| R-08 | Demo overlay vs Odoo source confusion | Medium | Wrong prod data | Playbooks: prod = Odoo only; overlay = demo only |
| R-09 | Kafka unavailable in connector logs | Low (R1) | Log noise only | Kafka not required for release1 |
| R-10 | Keycloak POST-B blocks enterprise IT | Medium | Deal friction | Local auth acceptable for R1 contract |
| R-11 | fea-svc rescore before commit (fixed) | Low | Null scores | ✅ Commit-before-rescore in sync_engine |
| R-12 | Documentation version drift (README vs READINESS) | Medium | Onboarding confusion | This PRD as single reference; update README |
| R-13 | k6 SLO vs Kong rate limit (500/min) | High | Phase 2 close blocked | Separate SLO vs stress profiles; perf-test exemption |
| R-14 | `demo-http.ps1` alias recursion on PS 5.1 | Medium | Gate 5 R1 fail | ✅ Fixed — removed `Invoke-DemoRequest` alias |
| R-15 | Git dubious ownership on `E:/AISOP/ipe` | Medium | Cannot commit/tag | User must approve `safe.directory` |
| R-16 | Docker compose network label conflicts | Medium | Manual container recreate | Document runbook or fix compose labels |

---

## 19. Assumptions & Constraints

### 19.1 Assumptions

| ID | Assumption | Valid if |
|----|------------|----------|
| A-01 | Star Trans uses Odoo Manufacturing + Sales + Purchase | Modules installed |
| A-02 | Planners accept shadow-mode AI initially | Training delivered |
| A-03 | Single tenant per Release 1 deploy | No multi-tenant VM sharing |
| A-04 | English acceptable for Resolution/login in R1 MVP | Arabic partial OK per contract |
| A-05 | Network allows Docker → host Odoo (8069) | `host.docker.internal` works |
| A-06 | Demo 32/32 represents full product capability | Not all CP apply to R1 profile |
| A-07 | OR-Tools solver adequate for <20 MO subset | Validated in demo |

### 19.2 Technical Constraints

| Constraint | Detail |
|------------|--------|
| Single PostgreSQL instance | No sharding in as-is compose |
| Release 1: no Kafka | Batch sync only |
| LLM requires GPU/host Ollama or cloud key | Full profile only |
| Migrations through **036** required | Includes R1 sync tables |
| Web dev port **8082**; Kong **8000**; DB **5433** | Local defaults |
| Gitignored ORM models | Built into Docker images; local dev needs `ipe_shared` |

### 19.3 Business Constraints

| Constraint | Detail |
|------------|--------|
| Constitution Principle VII | Release 1 ≤8 services, 8GB VM |
| Freeze platform scope until Star Trans UAT | Spec 013 R-B1 |
| No Kinaxis feature parity pitch to R1 buyer | Spec 013 R-B5 |
| Pricing $18K–30K/yr | **Needs commercial confirmation** |

---

## 20. Appendices

### Appendix A — Version History & Changelog

| Version / tag | Date | Spec | Major changes |
|---------------|------|------|---------------|
| v1.0.0-rc1 | 2026-06-15 | 002 | Stabilization gates 1–3 |
| **v1.0.0** | 2026-06-22 | **003 (V5.0)** | Closed-loop persist, MDR, XAI, chaos/k6 |
| v6.0.0 | 2026-06-24 | 004 | Tariff, CPM, cost of chaos, war room |
| v6.0.1 | 2026-06-25 | — | MDR JWT, audit fixes |
| v6.1.0 | 2026-06-26 | — | TLS/JWT runbooks, SEC-05 |
| v7.0.0 | 2026-06-27 | 006 | Hubs, Ollama LLM, docs suite |
| v7.1 | 2026-06-27 | 006 | Planning/Command dashboards |
| v8.0.0 | 2026-06-27 | 007 | U1–U3 copilot, demand, scenario |
| v8.1.0 | 2026-06-27 | 008 | U4–U6 supply, orders, equipment |
| **v8.2.0** | 2026-06-28 | 009–010 | U7–U8 design/procurement; **32/32 demo** |
| v9.0.0-r1 | pending | 013 | Release 1 Odoo live; 8-service profile; **14/14 HTTPS** |
| v9.1.0-r2 | pending | 014 | R2 Outcomes + Copilot Lite; **5/5 demo** |
| **v9.3.0-p2** | pending | 015 | Enterprise Phase 2 gates; **uncommitted** |

**Naming note:** Product **“V5.0”** = git tag **v1.0.0**, not v5.0.0.

### Appendix B — Entity Relationship Summary

```
cdm_tenant
  ├── cdm_user
  ├── cdm_product
  │     ├── cdm_bill_of_material → cdm_bom_line → cdm_product (component)
  │     │     └── cdm_routing_operation → cdm_work_center
  │     └── cdm_manufacturing_order
  │           ├── cdm_resolution_scenario
  │           ├── cdm_data_quality_flag
  │           ├── cdm_delay_event
  │           └── cdm_work_order
  ├── cdm_demand_line → cdm_customer
  ├── cdm_supply_order → cdm_supplier
  ├── cdm_sync_run
  └── cdm_plant → cdm_transfer_route
```

### Appendix C — Configuration Options

| Setting | Location | Values |
|---------|----------|--------|
| `VITE_RELEASE_PROFILE` | web env | `full` \| `release1` |
| `IPE_RELEASE_PROFILE` | compose | same |
| `AUTH_PROVIDER` | dpe-svc | `local` \| `keycloak` |
| `AUTH_MODE` | `ipe-common.env` | `local` \| `keycloak` |
| `VAULT_ENABLED` / `IPE_VAULT_*` | compose | HashiCorp Vault integration |
| `IPE_AUDIT_REQUEST_MIDDLEWARE` | dpe-svc | `true` for enterprise audit trail |
| `IPE_JWT_SIGNING_MODE` | dpe-svc | `rs256` for enterprise |
| `JWT_SECRET_KEY` | compose | dev placeholder |
| `FEA_SVC_URL` | connector | `http://fea-svc:8004` |
| `ERP_SYNC_MODE` | cap-svc | `direct` for Odoo activate |
| `autonomy_mode` | cdm_tenant / Admin UI | shadow \| suggest \| autonomous |
| Odoo creds | cdm_tenant.config | odoo_url, odoo_db, odoo_username, odoo_password |

### Appendix D — Error Handling Protocols

| Error | User-visible behavior | System behavior |
|-------|----------------------|-----------------|
| Sync fail | SyncStatusBar shows error | `cdm_sync_run.status=failed`; error_summary stored |
| MO unscorable | Badge in queue; no score | fea-svc returns `unscorable=true` |
| DQ flag | Flag message on MO | Scheduling blocked for that MO |
| SYNC_CONFLICT | Badge after Odoo date change | `mo.sync_conflict` JSON stored |
| Solver timeout | Toast / message | cap-svc error; retry with subset |
| Copilot LLM down | Fallback message | Rule-based or Resolution redirect |
| 401 auth | Redirect to login | Token cleared |
| Odoo connect fail | API `ODOO_CONNECT_FAILED` | No partial commit |

### Appendix E — Demo vs Production Data Paths

| Path | Use | Command / artifact |
|------|-----|-------------------|
| **Demo (full 32/32)** | Sales/investor | `prepare-startrans-demo.ps1` → SQL overlay |
| **Release 1 production** | Customer live | Odoo sync only — **do not run overlay SQL** |
| **Local Odoo dev** | Engineering | `seed-odoo-startrans.py` + `setup-odoo-integration.ps1` |

### Appendix F — Glossary

| Term | Definition |
|------|------------|
| **APS** | Advanced Planning and Scheduling |
| **CDM** | Canonical Data Model — PostgreSQL `cdm_*` tables |
| **Control Tower** | MO risk queue UI with feasibility KPIs |
| **CP (Checkpoint)** | Automated demo validation step (32 total in v8.2) |
| **CP-SAT** | Constraint Programming SAT solver (OR-Tools) |
| **FEA** | Feasibility scoring service (`fea-svc`) |
| **MDR** | Manufacturing Data Readiness — composite data quality gate |
| **MO** | Manufacturing Order |
| **OTD** | On-Time Delivery |
| **POST-B** | Post–business-blocker — scaffolded, not production-active |
| **Release 1 / R1** | 8-service Odoo customer profile (spec 013) |
| **RLS** | Row-Level Security in PostgreSQL |
| **R1.1** | Release 1 hardening tranche (admin UI, vault, alerts) |
| **Shadow mode** | AI recommends; human must approve all actions |
| **SOW** | Statement of Work |
| **Star Trans** | Reference customer — electrical transformers, Egypt |
| **Sync run** | Audited Odoo→CDM import execution (`cdm_sync_run`) |
| **U1–U8** | v8 feature streams (copilot through procurement) |
| **Gate 1–5** | Enterprise Phase 2 verification scripts (observability, security, quotas, Odoo sync, full E2E) |
| **NEXUS** | Separate social/marketing product — **not in IPE program scope** |
| **V5.0** | Product convergence spec 003 — shipped as git v1.0.0 |
| **War Room** | Disruption aggregation dashboard |
| **WC** | Work Center |
| **XAI** | Explainable AI — constraint attribution on scores/schedules |

### Appendix G — Open Items Requiring Stakeholder Input

| ID | Item | Owner |
|----|------|-------|
| OQ-1 | Canonical Odoo version for Release 1 documentation (17 vs 19) | Product + Customer IT |
| OQ-2 | Production data source policy (Odoo-only confirmation in SOW) | Legal |
| OQ-3 | UI route-level RBAC implementation priority | Product + Eng |
| OQ-4 | v8.2.0 git tag and CHANGELOG update timing | Eng |
| OQ-5 | Formal MAPE / triage-time baseline study for G-01/G-02 | Product |
| OQ-6 | Copilot session retention / GDPR policy | Legal |
| OQ-7 | Commercial pricing confirmation ($18K–30K/yr) | Sales |
| OQ-8 | Second prospect parallel to Star Trans (R-B4) | Sales |
| OQ-9 | k6 SLO test design vs rate-limit stress test | Eng + PM |
| OQ-10 | Tag naming: `v9.3.0-p2` vs `v10.0.0-e2` | PM |
| OQ-11 | Canonical Odoo version for customer docs (17 vs 19) | Product + Customer IT |

### Appendix H — Reference Documents

| Document | Path |
|----------|------|
| Enterprise PRD (v8.2 partial) | `docs/PRD-IPE-v8.2.0-ENTERPRISE.md` |
| Product status matrix | `docs/PRODUCT-STATUS.md` |
| Deployment readiness | `docs/DEPLOYMENT-READINESS-v8.2.0.md` |
| Readiness score | `READINESS.md` |
| Release 1 spec | `specs/013-release1-odoo-mena/spec.md` |
| V5 convergence spec | `specs/003-autonomous-planning-v5/spec.md` |
| Odoo local setup | `docs/integration/ODOO-LOCAL-SETUP.md` |
| End user guide | `docs/END-USER-GUIDE.md` |
| Star Trans demo guide | `docs/demo-data/STARTRANS-DEMO-GUIDE.md` |
| R1 training curriculum | `docs/implementation/R1-TRAINING-CURRICULUM.md` |
| R1 customer support | `docs/runbooks/R1-CUSTOMER-SUPPORT-GUIDE.md` |
| Enterprise spec | `specs/015-enterprise-production-readiness/spec.md` |
| Release 2 spec | `specs/014-release2-growth/spec.md` |
| Constitution | `.specify/memory/constitution.md` |
| Gate 5 verifier | `scripts/security/verify-gate5.ps1` |
| Shared HTTP helper | `scripts/demo-http.ps1` |

### Appendix I — Document Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Engineering Lead | | | |
| Release 1 Sponsor (Star Trans) | | | |

---

## 21. Last 24 Hours — Engineering Activity Log (2026-07-02 → 2026-07-03)

| # | Workstream | Task / deliverable | Files / scripts | Status | Evidence / notes |
|---|------------|-------------------|-----------------|--------|------------------|
| 1 | **Gate 1 — Observability** | Prometheus scrape fix; Grafana 6 dashboards; verify script | `scripts/monitoring/verify-gate1.sh`, monitoring compose | ✅ **PASS** | 9/9 Prometheus targets UP |
| 2 | **Gate 2 — Security** | Network isolation (remove monitoring from backend nets); rate-limit probe; CORS | `scripts/security/verify-gate2.sh`, `rate-limit-burst.sh`, Kong config | ✅ **PASS** | Intermittent fail when bundled in Gate 5 |
| 3 | **Gate 3 — Quotas** | Tenant quotas JSON mount; Kafka consumer tenant scoping | `verify-gate3.sh`, `quota-probe.py`, `IPE_KAFKA_CONSUMER_TENANT_ID` | ✅ **PASS** | fea-svc + consumer groups verified after rebuild |
| 4 | **Gate 4 — Odoo sync** | Bidirectional sync; conflict resolver; MO ID resolution | `sync_engine.py`, `activate.py`, `verify-gate4.sh` | ✅ **PASS** | Fixed dead `sync_bom_details` code after unreachable return |
| 5 | **Gate 5 — Full E2E** | HTTPS demos + enterprise flags + audit trail | `verify-gate5.ps1`, `ipe-common.env`, `demo-http.ps1` | 🟡 **Partial** | R1 **14/14** + R2 **5/5** standalone; bundle run failed on SSL alias bug (fixed) |
| 6 | **Audit middleware** | JSON serialize `before_state`/`after_state` for asyncpg | `ipe_shared/audit/service.py` | ✅ **Done** | Audit export 102+ rows in Gate 5 session |
| 7 | **Enterprise env** | Keycloak, Vault, RS256, audit middleware, HTTPS CORS | `infrastructure/docker/ipe-common.env` | ✅ **Activated** | `AUTH_MODE=keycloak`, `VAULT_ENABLED=true` |
| 8 | **Demo scripts HTTPS** | Keycloak JWT + curl-based PS 5.1 TLS bypass | `demo-http.ps1`, `run-release1-integration-demo.ps1`, `run-release2-demo.ps1` | ✅ **Done** | Removed `Invoke-DemoRequest` alias — fixed call-depth overflow |
| 9 | **Connector networking** | Odoo access via `host.docker.internal:8069` | connector on `ipe-public` network | ✅ **Done** | Manual `docker run` when compose label conflicts |
| 10 | **k6 load test** | Phase 2 close SLO re-run | `scripts/perf/k6-load-test.js` (`health-only` profile) | ❌ **FAIL** | 429 from Kong 500 req/min; P95 > 500ms at 50 VU |
| 11 | **Unit tests** | Odoo conflict resolver + sync monitor | connector tests | ✅ **PASS** | `verify-gate4` supporting tests |
| 12 | **MO sync conflict test** | Integration test for conflict path | test script (task 684710) | ❌ → ✅ | Failed initially; **passed after patch** (task 225871) |
| 13 | **JWT for Kong auth** | Token obtain for auth probes | Keycloak password grant | ❌ → ✅ | Initial curl exit 3; resolved via `demo-http.ps1` / Keycloak realm |
| 14 | **Rate limit probe** | 510 requests to `/api/v1/health` | rate-limit scripts (tasks 897797, 2226) | 🟡 Mixed | One run success; one exit 1 — confirms 429 behavior at limit |
| 15 | **Kafka tenant groups** | Consumer rebuild + group verification | fea-svc, mat-svc, etc. redeploy | ✅ **PASS** | Tasks 332728, 527879, 746418, 208457, 754768, 778105 |
| 16 | **IPE→Odoo push prep** | Find MO IDs + AI schedule for activate | DB queries (tasks 509076, 896604) | ✅ **Done** | MO-ST-002 `d1eebc99-9c0b-4ef8-bb6d-6bb9bd380002` |
| 17 | **Speckit synthesis** | Full pipeline status (constitution → converge) | `.specify/`, specs 000–015 | ✅ **Doc** | Program rollup; artifact drift flagged |
| 18 | **Git tag `v9.3.0-p2`** | Phase 2 milestone tag | git | ⬜ **Pending** | Uncommitted changes; dubious ownership on `E:/AISOP/ipe` |
| 19 | **PRD update** | Comprehensive as-is PRD refresh | `docs/PRD-IPE-COMPREHENSIVE-AS-IS.md` | ✅ **This doc** | 2026-07-03 |
| 20 | **Speckit artifact sync** | `feature.json`, `015/tasks.md` reflect gates | `.specify/feature.json`, `015/tasks.md` | ⬜ **Pending** | `/speckit.converge` recommended |

**Summary (24h):** Enterprise Gates **1–4 PASS**; Gate **5 PASS** for R1/R2 when run standalone after `demo-http.ps1` fix; **k6 FAIL** blocks Phase 2 close; **git commit + tag pending**.

---

*End of document — PRD-IPE-2026-COMPREHENSIVE (As-Is) — Updated 2026-07-03*
