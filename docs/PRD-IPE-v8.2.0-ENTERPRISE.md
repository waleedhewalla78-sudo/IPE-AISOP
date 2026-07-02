# Product Requirements Document (PRD)

## Intelligent Planning Engine (IPE) v8.2.0

| Field | Value |
|-------|-------|
| **Document ID** | PRD-IPE-2026-001 |
| **Version** | 8.2.0 |
| **Status** | Approved for Staging/UAT |
| **Author** | Product & Engineering (AISOP) |
| **Last updated** | 2026-06-29 |
| **Primary vertical reference** | Discrete manufacturing — electrical transformers (Star Trans) |
| **Release tag** | v8.2.0 |
| **Superseded by** | [PRD-IPE-COMPREHENSIVE-AS-IS.md](./PRD-IPE-COMPREHENSIVE-AS-IS.md) (authoritative as-is spec) |

---

## 1. Executive summary

IPE (Intelligent Planning Engine) is a multi-tenant, AI-assisted **manufacturing planning and execution platform** that connects demand sensing, constraint detection, scenario resolution, finite-capacity scheduling, supply network planning, and shop-floor visibility in a single hub-based web application backed by 22 microservices.

**Product thesis:** Planners detect infeasibility before the shift starts, evaluate trade-offs in a Resolution Center, publish optimized schedules (OR-Tools), and leadership sees financial impact — with AI in **shadow mode** by default so humans retain control.

**Current maturity (v8.2.0):**

- 32/32 automated demo checkpoints (staging-validated)
- 870+ backend tests; ~180 dpe-svc tests
- Production scaffolds ready (Keycloak, secrets vault, Stripe, SAP/D365 ERP) — activation POST-B

---

## 2. Goals, non-goals, and success metrics

### 2.1 Business goals

| ID | Goal | Success metric |
|----|------|----------------|
| G-01 | Reduce planning cycle time | ≥30% faster MO triage vs spreadsheet baseline |
| G-02 | Improve OTD predictability | Feasibility score correlates with actual delay (MAPE tracked) |
| G-03 | Increase planner productivity | ≥3 resolution scenarios evaluated per at-risk MO |
| G-04 | Executive visibility | Single dashboard for OTD, delay root cause, cost of chaos |
| G-05 | AI adoption with trust | Shadow → suggest → autonomous progression with AI Trust KPIs |

### 2.2 Non-goals (v8.2.0)

- Full MES replacement
- Live SAP/D365 write-back (scaffold only)
- Enterprise SSO in production (Keycloak POST-B)
- WCAG 2.1 AA certification (POST-B)
- Multi-sheet Excel import on every hub (Schedule upload only in v8.2.0)

---

## 3. Personas and actors

| Persona | Role (RBAC) | Primary goals |
|---------|-------------|---------------|
| **Production Planner** | `planner` | Triage MOs, resolve constraints, build/approve schedule |
| **Plant Manager** | `manager` | Approve schedules, authorize overtime/expedite |
| **Shop Supervisor** | `supervisor` | Monitor shop floor, acknowledge disruptions |
| **Shop Operator** | `operator` | Execute work orders, update progress |
| **Executive / VP Ops** | `executive` | OTD, margin, disruption cost, ESG summary |
| **Procurement Analyst** | `procurement` | Supplier risk, spend, compliance |
| **Quality Engineer** | `planner` / read | FPY, defect trends, SPC |
| **ESG / Sustainability Lead** | read | Carbon, ESG score, circularity |
| **System Administrator** | `admin` | Tenant config, autonomy mode, users |
| **Auditor** | `auditor` | Read-only audit logs, KPIs, scenarios |
| **AI Copilot (system actor)** | service | NL queries, intent routing, session memory |
| **ERP / MES (external)** | integration | MO master, BOM, inventory, publish schedule |

---

## 4. Use cases

### UC-01 — Daily production health triage

| Attribute | Description |
|-----------|-------------|
| **Actor** | Planner |
| **Preconditions** | Authenticated; tenant has active MOs; Control Tower data synced |
| **Main flow** | 1. Login → Planning Hub → Control Tower. 2. Review KPI cards (avg feasibility, orders at risk). 3. Sort MO risk queue by feasibility score. 4. Select MO below threshold (e.g. &lt;70). 5. Navigate to Resolution Center. |
| **Alternate flows** | A1: Filter by constraint type (material, capacity, labor). A2: Copilot query "Which orders are at risk this week?" |
| **Edge cases** | Empty queue → run seed or ERP sync. Stale scores → refresh feasibility job. |
| **Postcondition** | Planner identifies top 3 at-risk MOs for action |

### UC-02 — Constraint resolution with scenario comparison

| Attribute | Description |
|-----------|-------------|
| **Actor** | Planner, Manager (approve) |
| **Preconditions** | MO selected; ≥1 resolution scenario exists |
| **Main flow** | 1. Open Resolution Center. 2. Select MO (e.g. MO-ST-001). 3. Compare scenarios (expedite PO, substitute material, split MO). 4. Review cost vs delivery impact and business score. 5. Approve preferred scenario (manager if required). |
| **Alternate flows** | A1: Reject all → defer MO. A2: Create custom scenario (future). |
| **Edge cases** | No scenarios → trigger scenario generation batch. Cross-tenant MO access blocked by RLS. |
| **Postcondition** | Approved scenario recorded; MO status updated |

### UC-03 — Finite-capacity scheduling

| Attribute | Description |
|-----------|-------------|
| **Actor** | Planner |
| **Preconditions** | MOs have routing; work centers defined; solver service healthy |
| **Main flow** | 1. Planning → Schedule. 2. Configure solver options (optional). 3. Refresh → OR-Tools generates Gantt. 4. Review operations on work centers. 5. Approve schedule for eligible MOs (feasibility ≥85%). |
| **Alternate flows** | A1: Upload Excel project plan (.xlsx) → switch view to "Uploaded project plan". A2: CPM cascade preview on delay injection. |
| **Edge cases** | Solver timeout → limit MO subset (demo: 3 MOs). ERP publish deferred → message shown. |
| **Postcondition** | Active approved schedule persisted |

### UC-04 — Excel project plan import (ERP workaround)

| Attribute | Description |
|-----------|-------------|
| **Actor** | Planner |
| **Preconditions** | MO IDs exist in DB; WC codes valid; .xlsx format |
| **Main flow** | 1. Schedule → Upload Project Plan. 2. Create new plan. 3. Select file (PLAN-STARTRANS-W12.xlsx). 4. Upload. 5. Select uploaded plan in view dropdown. |
| **Alternate flows** | Update existing plan (new version). Activate prior version from history. |
| **Edge cases** | Invalid MO_ID → validation errors listed. CSV rejected → must be xlsx. |
| **Postcondition** | Project plan version active; Gantt reflects uploaded operations |

### UC-05 — Demand sensing and forecast

| Attribute | Description |
|-----------|-------------|
| **Actor** | Planner |
| **Preconditions** | Demand history in `cdm_demand_line`; demand-svc running |
| **Main flow** | 1. Planning → Demand. 2. View short-horizon forecasts. 3. Run sense cycle. 4. Review updated forecast rows (SES/Prophet/LSTM per factory). |
| **Alternate flows** | A1: Manual forecast adjustment via API. A2: Signal ingest (API POST-B UI). |
| **Postcondition** | Forecast rows created/updated for tenant |

### UC-06 — What-if scenario sandbox

| Attribute | Description |
|-----------|-------------|
| **Actor** | Planner |
| **Preconditions** | scenario-svc running |
| **Main flow** | 1. Planning → Scenarios. 2. Create sandbox (name + demand delta). 3. Simulate. 4. Review KPI impact. |
| **Postcondition** | Scenario persisted with simulation results |

### UC-07 — Multi-echelon supply visibility

| Attribute | Description |
|-----------|-------------|
| **Actor** | Planner, Executive |
| **Preconditions** | Plants and transfer routes seeded (migration 034) |
| **Main flow** | 1. Supply Chain → Supply Planning. 2. View facilities and lanes. 3. Discuss network resilience. |
| **Postcondition** | User understands source/make/distribute topology |

### UC-08 — Copilot natural-language query

| Attribute | Description |
|-----------|-------------|
| **Actor** | Planner (session role) |
| **Preconditions** | nlp-svc + LLM (Ollama/OpenRouter) available |
| **Main flow** | 1. AI & Governance → Copilot. 2. Start planner session. 3. Query e.g. "What is blocking MO-ST-001?" 4. Review intent + structured response. |
| **Alternate flows** | Material status, feasibility check, bottleneck work centers |
| **Edge cases** | LLM timeout (180s) → fallback to Resolution Center. PII redaction in response text. |
| **Postcondition** | User receives actionable answer |

### UC-09 — Executive disruption review

| Attribute | Description |
|-----------|-------------|
| **Actor** | Executive |
| **Preconditions** | Delay events and alerts seeded |
| **Main flow** | 1. Command Center → Executive (OTD, delay breakdown). 2. War Room (active alerts, recovery options). 3. Cost of Chaos (optional). |
| **Postcondition** | Leadership understands financial exposure |

### UC-10 — Shop floor execution monitoring

| Attribute | Description |
|-----------|-------------|
| **Actor** | Supervisor, Operator |
| **Preconditions** | Work orders exist for in-progress MOs |
| **Main flow** | 1. Shop Floor. 2. View active work orders by work center. 3. Monitor progress %. |
| **Postcondition** | Floor status visible |

### UC-11 — Star Trans demo data load (operations)

| Attribute | Description |
|-----------|-------------|
| **Actor** | Demo engineer / Admin |
| **Preconditions** | Docker `ipe_test`; migrations applied |
| **Main flow** | `.\scripts\prepare-startrans-demo.ps1` |
| **Edge cases** | Wrong DB (Cursor SQL) → cdm_tenant missing; use Docker script only |
| **Postcondition** | 32/32 Star Trans profile validation |

---

## 5. Functional requirements

### 5.1 Authentication and tenancy

| ID | Requirement | Validation rule |
|----|-------------|-----------------|
| FR-AUTH-01 | System shall authenticate users via JWT (demo) or Keycloak OIDC (POST-B) | Invalid credentials return 401 |
| FR-AUTH-02 | Every API request shall carry tenant context (`X-Tenant-ID` or JWT claim) | Missing tenant → 403 |
| FR-AUTH-03 | Row-level security shall isolate tenant data in PostgreSQL | Cross-tenant read/write blocked (migration 035 INSERT policies) |
| FR-AUTH-04 | Session timeout shall be configurable per tenant | Default 8h staging |

### 5.2 Planning Hub

| ID | Requirement | Module |
|----|-------------|--------|
| FR-PLN-01 | Display feasibility queue with ≥10 MOs when demo seed loaded | Control Tower |
| FR-PLN-02 | Compute and display KPIs: avg feasibility, orders at risk | Control Tower |
| FR-PLN-03 | List resolution scenarios per MO (≥8 for demo tenant) | Resolution |
| FR-PLN-04 | Run OR-Tools schedule for selected MOs within 90s | Schedule |
| FR-PLN-05 | Persist approved schedule; show ERP sync status | Schedule |
| FR-PLN-06 | Upload .xlsx project plan; validate MO_ID and WC_CODE | Schedule |
| FR-PLN-07 | Export schedule to MS Project format | Schedule |
| FR-PLN-08 | Run demand sense cycle; create forecast rows | Demand |
| FR-PLN-09 | Create/simulate what-if scenarios | Scenarios |
| FR-PLN-10 | CPM cascade preview &lt;2s for demo subset | Schedule |

**Business rules:**

- BR-PLN-01: Only MOs with feasibility ≥85% may be approved to active schedule (guardrail).
- BR-PLN-02: Autonomy mode `shadow` — AI never auto-applies without explicit approval.
- BR-PLN-03: Project plan PLAN_CODE must be consistent across all rows in upload file.

### 5.3 Command Center

| ID | Requirement |
|----|-------------|
| FR-CC-01 | Executive summary: OTD trend, delay breakdown by cause category |
| FR-CC-02 | War Room: ≥8 active alerts; recovery plan options |
| FR-CC-03 | Cost of Chaos: category USD breakdown (7d default) |
| FR-CC-04 | Equipment fleet health scores |

### 5.4 Supply Chain Hub

| ID | Requirement |
|----|-------------|
| FR-SC-01 | Supply network: ≥4 facilities, ≥6 lanes |
| FR-SC-02 | Order creation with ATP check |
| FR-SC-03 | Procurement spend aggregation and supplier list |
| FR-SC-04 | Tariff shock simulation with substitute drafts |
| FR-SC-05 | SCN supplier scorecards (≥3 suppliers) |
| FR-SC-06 | Inventory summary by product/location |

### 5.5 AI & Governance

| ID | Requirement |
|----|-------------|
| FR-AI-01 | Copilot intents: material_status, feasibility_check, bottleneck, general |
| FR-AI-02 | Role-based copilot sessions (planner agent) |
| FR-AI-03 | AI Trust dashboard: model scores, adoption metrics |
| FR-AI-04 | Design AI: material catalog and recommendations |
| FR-AI-05 | Quality dashboard: defect rate, FPY, trend |
| FR-AI-06 | Sustainability dashboard: ESG score, carbon tCO2e |
| FR-AI-07 | MDR and Compliance read-only dashboards |

### 5.6 Platform

| ID | Requirement |
|----|-------------|
| FR-PLT-01 | Admin: tenant config including autonomy_mode |
| FR-PLT-02 | Onboarding wizard (staging) |
| FR-PLT-03 | MLOps model registry dashboard |
| FR-PLT-04 | Shop Floor PWA work order list |

### 5.7 Integrations (scaffold vs live)

| ID | Requirement | Status v8.2.0 |
|----|-------------|---------------|
| FR-INT-01 | ERP fetch MO/material master | Scaffold |
| FR-INT-02 | ERP publish approved schedule | Deferred message |
| FR-INT-03 | Kafka topic `ipe.supply.adjusted` supply→demand feedback | Wired (demand-svc consumer) |
| FR-INT-04 | Stripe billing | Mock |
| FR-INT-05 | LLM: Ollama primary, OpenRouter/Anthropic fallback | Live (demo) |

---

## 6. Feature requirements

| Feature | Purpose | User benefit | Acceptance criteria | Dependencies | Priority |
|---------|---------|--------------|---------------------|--------------|----------|
| **Control Tower** | MO risk visibility | Start day with prioritized queue | 10 MOs; 3 &lt;70 score | dpe-svc, seed | Must |
| **Resolution Center** | Scenario trade-offs | Data-driven decisions | ≥8 scenarios; cost/delivery shown | dpe-svc | Must |
| **Schedule + OR-Tools** | Constraint-aware Gantt | Feasible capacity plan | ≥1 op scheduled; approve persists | cap-svc | Must |
| **Excel plan upload** | ERP-delay workaround | Planner-native import | .xlsx validates; version history | cap-svc | Must |
| **Demand sensing** | Statistical forecast | Short-term demand view | Sense cycle creates rows | demand-svc | Must |
| **Scenario workbench** | Sandbox KPIs | Safe what-if | Create + simulate returns KPIs | scenario-svc | Must |
| **Supply network** | Multi-echelon view | Network resilience story | 4 facilities, 6 lanes | supply-svc, mig 034 | Must |
| **Copilot** | NL interface | Faster triage | 3 demo queries pass CP10-11,30 | nlp-svc, LLM | Must |
| **War Room + Executive** | Leadership KPIs | Board-ready metrics | OTD + delays + alerts | dpe-svc | Must |
| **Quality + Sustainability** | ESG differentiation | Beyond APS | CP31-32 pass | quality/sustain-svc | Should |
| **Tariff shock** | Landed cost what-if | Supply risk | Affected MOs + substitute drafts | dpe-svc | Should |
| **Keycloak SSO** | Enterprise auth | IT compliance | AUTH_PROVIDER=keycloak | POST-B | Should |
| **Live SAP/D365** | ERP sync | Single source of truth | Real publish/fetch | POST-B | Should |
| **Bulk Excel import (all hubs)** | Self-service data | Reduce SI effort | Multi-sheet importer | POST-B | Nice |

---

## 7. Competitive mapping

### 7.1 Competitor set (APS / IBP / supply chain planning)

| Vendor | Product | Strength vs IPE |
|--------|---------|-----------------|
| **SAP** | IBP + PP/DS | ERP-native, deep SAP install base, mature ATP |
| **Kinaxis** | Maestro | Concurrent planning, scenario comparison, supply chain |
| **o9 Solutions** | o9 platform | AI/ML forecasting, integrated IBP |
| **Blue Yonder** | Luminate | Retail/CPG strong; cognitive planning |
| **Oracle** | SCM Cloud (Planning) | Cloud suite integration |

### 7.2 Feature comparison matrix

| Capability | IPE v8.2.0 | SAP IBP | Kinaxis | o9 | Blue Yonder |
|------------|------------|---------|---------|-----|-------------|
| Feasibility / risk queue | ✅ Control Tower | ✅ | ✅ | ✅ | ✅ |
| Scenario comparison | ✅ Resolution | ✅ | ✅✅ | ✅ | ✅ |
| Finite capacity scheduling | ✅ OR-Tools | ✅ PP/DS | ✅ | ✅ | ✅ |
| Excel plan upload | ✅ Schedule | ✅ | ✅ | Partial | ✅ |
| NL copilot (manufacturing) | ✅ shadow mode | SAP Joule (ERP) | Limited | ✅ AI | Partial |
| Multi-echelon network | ✅ 4P/6L demo | ✅✅ | ✅✅ | ✅✅ | ✅ |
| Demand sensing ML | ✅ SES/Prophet/LSTM | ✅ | ✅ | ✅✅ | ✅ |
| Shop floor PWA | ✅ | MES separate | Add-on | Partial | ✅ |
| ESG / quality in same UI | ✅ | Separate modules | Partial | Partial | Partial |
| Time to demo (local) | ✅ 32 CP / Docker | Months | Weeks | Weeks | Weeks |
| Live ERP (staging) | ❌ scaffold | ✅ | ✅ | ✅ | ✅ |

**Positioning:** IPE targets **mid-market discrete manufacturers** needing APS + AI copilot + ESG/quality in one hub UI, with faster PoC deployment than suite rollouts. Gap vs leaders: production ERP connectors, enterprise SSO at scale, proven multi-site performance benchmarks.

---

## 8. Business scenarios

### BS-01 — Star Trans: copper delay on utility transformer order

| Step | Actor | Action | Success metric |
|------|-------|--------|----------------|
| 1 | Planner | Sees MO-ST-001 at 52% feasibility, material_shortage | Identified &lt;5 min |
| 2 | Planner | Evaluates expedite vs substitute vs split scenarios | Scenario selected |
| 3 | Planner | Re-schedules after Excel upload or solver refresh | Gantt updated |
| 4 | Executive | Reviews War Room cost of delay | $ impact quantified |
| 5 | Copilot | Confirms blocker in NL | Query &lt;90s |

**KPI:** Demo 32/32 pass; client confirms "would use weekly."

### BS-02 — Monthly S&OP demand review

| Step | Actor | Action | Success metric |
|------|-------|--------|----------------|
| 1 | Planner | Runs demand sense cycle | Forecast rows +14 days |
| 2 | Planner | Creates scenario "+10% utility demand" | KPI delta visible |
| 3 | Manager | Reviews supply network capacity | Lane bottleneck identified |

**KPI:** Forecast MAPE &lt;15% on demo history (target production).

### BS-03 — Executive quarterly review

| Step | Actor | Action | Success metric |
|------|-------|--------|----------------|
| 1 | Executive | Executive dashboard OTD trend | 2+ periods shown |
| 2 | Executive | Quality FPY + Sustainability ESG | Single-session story |
| 3 | Executive | AI Trust adoption score | Shadow mode explained |

**KPI:** Single-pane review &lt;15 min without planner support.

---

## 9. User workflows and interactions

### 9.1 Primary planner day (decision tree)

```
Login
 └─ Planning Hub
     ├─ Control Tower [feasibility OK?]
     │   ├─ YES → Schedule refresh → Approve
     │   └─ NO  → Resolution Center
     │           ├─ Approve scenario → Schedule
     │           └─ Need data → Excel upload OR Copilot query
     ├─ Demand [forecast stale?] → Run sense cycle
     └─ Scenarios [major disruption?] → Create sandbox → Simulate
```

### 9.2 Schedule source selection

```
Schedule page
 ├─ View: AI/solver schedule → Refresh → Approve
 └─ View: Uploaded project plan → Select PLAN_CODE → Display Gantt
```

### 9.3 Navigation architecture

**Level 1 — Sidebar hubs:**

1. Planning Hub  
2. Command Center  
3. Supply Chain Hub  
4. AI & Governance  
5. Shop Floor  
6. Platform  

**Level 2 — Tab bar within hub** (see Section 10).

---

## 10. Screens and forms structure

### 10.1 Information architecture

| Hub | Route prefix | Tabs |
|-----|--------------|------|
| Planning | `/planning` | Dashboard, Demand, Scenarios, Control Tower, Resolution, Schedule |
| Command Center | `/command-center` | Dashboard, War Room, Executive, Equipment, Cost of Chaos |
| Supply Chain | `/supply-chain` | Supply Planning, Orders, Procurement, Tariff, SCN Portal, Inventory |
| AI & Governance | `/ai-governance` | Copilot, Design AI, AI Trust, MDR, Compliance, Quality, Sustainability |
| Platform | `/platform` | Admin, Onboarding, MLOps |
| Shop Floor | `/shop-floor` | (single page) |

Legacy routes (`/control-tower`, `/copilot`, etc.) redirect to hub paths.

### 10.2 Key screens — fields and controls

#### Login (`/login`)

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| email | email | Yes | Valid user in tenant |
| password | password | Yes | bcrypt verify |

#### Control Tower

| Element | Type | Data source |
|---------|------|-------------|
| KPI cards | metric tiles | `/api/v1/feasibility/kpis` |
| MO risk queue | sortable table | `/api/v1/feasibility/queue` |
| Columns | text/number | MO ID, product, score, constraint, status |

#### Resolution Center

| Element | Type |
|---------|------|
| MO selector | dropdown/list |
| Scenario cards | cost, delivery_days, business_score, strategy |

#### Schedule

| Element | Type |
|---------|------|
| Refresh button | action |
| Upload Project Plan | collapsible panel |
| Upload mode | radio: new / update |
| File | file (.xlsx only) |
| Notes | text (optional) |
| View source | radio: solver / uploaded |
| Plan selector | dropdown (when uploaded) |
| Gantt chart | visual |

**Excel upload columns:** PLAN_CODE, PLAN_NAME, MO_ID, OPERATION_SEQUENCE, OPERATION_NAME, WORK_CENTER_CODE, START_HOUR, DURATION_HOURS, STATUS, NOTES.

#### Demand

| Element | Type |
|---------|------|
| Forecast table | product_id, date, value, bounds |
| Run sense cycle | button |

#### Scenarios

| Field | Type |
|-------|------|
| name | text |
| demand_delta | text/percent |
| Simulate | button |
| KPI results | key-value grid |

#### Copilot

| Field | Type |
|-------|------|
| query | textarea |
| session role | planner (from session API) |
| response | markdown + structured_data |

#### Admin

| Field | Type |
|-------|------|
| autonomy_mode | enum: shadow, suggest, autonomous |

---

## 11. Authorization and permissions

### 11.1 Roles and permissions matrix

| Permission | admin | planner | manager | supervisor | operator | executive | auditor | procurement |
|------------|-------|---------|---------|------------|----------|-----------|---------|-------------|
| read | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| write | ✅ | ✅ | ✅ | — | own | — | — | ✅ |
| approve schedule | ✅ | ✅ | ✅ | — | — | — | — | — |
| run_solver | ✅ | ✅ | ✅ | — | — | — | — | — |
| view_copilot | ✅ | ✅ | ✅ | ✅ | — | — | — | — |
| run_scenario | ✅ | ✅ | ✅ | — | — | — | — | — |
| admin / users | ✅ | — | — | — | — | — | — | — |
| view_audit_logs | ✅ | — | — | — | — | — | ✅ | — |
| acknowledge_disruption | ✅ | — | — | ✅ | — | — | — | — |

### 11.2 Data visibility

- **Tenant isolation:** PostgreSQL RLS on all `tenant_id` tables; policy `tenant_isolation` with INSERT WITH CHECK (migration 035).
- **Executive:** Read KPIs only; no write to schedule or resolution.
- **Operator:** Write own work order progress only.

### 11.3 Compliance constraints (staging vs production)

| Constraint | Staging | Production target |
|------------|---------|-------------------|
| JWT secret | Dev placeholder | Vault rotation |
| SSO | Local login | Keycloak / Azure AD |
| Audit immutability | Enabled | SOC2 evidence |
| GDPR DSAR | API scaffold | Legal review |
| FDA 21 CFR Part 11 | E-sign scaffold | Validated deployment |

---

## 12. Reports and dashboards

| Dashboard / Report | Metrics | Data sources | Filters | Refresh | Audience |
|--------------------|---------|--------------|---------|---------|----------|
| **Control Tower KPIs** | avg feasibility, orders at risk, bottleneck WCs | dpe-svc feasibility | tenant, date | On load | Planner |
| **MO Risk Queue** | feasibility_score, primary_constraint | cdm_manufacturing_order | status, constraint | Real-time | Planner |
| **Executive Summary** | OTD trend, completed MO count | analytics API | period | Daily | Executive |
| **Delay Breakdown** | cause category, minutes, $ | cdm_delay_event | category | Daily | Executive, Planner |
| **War Room Alerts** | alert count, severity | dashboard/alerts | severity | Real-time | Supervisor, Planner |
| **Cost of Chaos** | USD by category (7d) | analytics/cost-of-chaos | period | Daily | Executive |
| **Demand Forecast** | value, bounds, model_version | demand_forecast | product, horizon | On sense cycle | Planner |
| **Scenario KPIs** | simulated metrics | scenario simulate | scenario_id | On demand | Planner |
| **Supply Network** | facilities, lanes, transit | supply network | — | On load | Planner |
| **SCN Scorecards** | supplier score, lead time | cdm_supplier | tier | Weekly | Procurement |
| **Procurement Spend** | total by category | procurement API | period | Monthly | Procurement |
| **Equipment Health** | health_score by asset | equipment-svc | — | Hourly | Maintenance |
| **Quality Dashboard** | defect_rate_pct, FPY, trend | quality-svc | — | Daily | Quality |
| **Sustainability Dashboard** | esg_score, carbon tCO2e | sustain-svc | — | Monthly | ESG |
| **AI Trust** | adoption, model scores | ai-trust API | — | Daily | Admin, Planner |
| **Shop Floor** | WO progress by WC | shop-floor items | WC, status | Real-time | Operator |

---

## 13. Technical specifications

### 13.1 Architecture overview

```
Browser (React/Vite :8082)
        │
        ▼
Kong API Gateway (:8000)
        │
        ├── dpe-svc (8020) — core planning, feasibility, resolution, analytics
        ├── cap-svc — capacity, schedule, project plans
        ├── demand-svc (8040) — forecast, sense, signal ingest
        ├── scenario-svc (8050) — sandbox simulate
        ├── supply-svc (8060) — network, Kafka publish
        ├── order-svc (8070) — orders, ATP
        ├── equipment-svc (8061) — fleet health
        ├── material-svc (8090) — design AI
        ├── procurement-svc (8100) — spend, suppliers
        ├── nlp-svc (8007) — copilot
        ├── quality-svc (8013), sustain-svc (8012)
        └── … (22 services total)

PostgreSQL 16 (ipe_test :5433) — RLS, Alembic migrations 001–035
Redis, Kafka, Ollama (host LLM)
```

### 13.2 Data model overview (core entities)

| Entity | Table | Key relationships |
|--------|-------|-------------------|
| Tenant | cdm_tenant | Root |
| Product | cdm_product | BOM, MO, demand |
| Manufacturing Order | cdm_manufacturing_order | scenarios, delays, WOs |
| Work Center | cdm_work_center | routing, schedule |
| Resolution Scenario | cdm_resolution_scenario | MO |
| Demand Line / Forecast | cdm_demand_line, demand_forecast | product |
| Plant / Lane | cdm_plant, cdm_transfer_route | supply network |
| Project Plan | project_plan + versions | Excel upload JSON ops |
| Supplier | cdm_supplier | SCN, procurement |

### 13.3 Demo data pipeline (Star Trans)

| Stage | Mechanism | Artifact |
|-------|-----------|----------|
| Base master | seed-data.ps1 | products, WCs, users |
| Demo graph | seed-demo-client.ps1 | 10 MOs, scenarios |
| Industry overlay | seed-startrans-overlay.sql via Docker | MO-ST-*, transformer names |
| Live upload | Schedule UI | project-plan-startrans-w12.xlsx |
| Validation | run-full-demo.ps1 -Profile startrans | 32/32 |

**Critical:** Do not run overlay SQL in IDE against empty database.

### 13.4 Non-functional requirements

| NFR | Target (staging) |
|-----|------------------|
| API availability | 99% during demo window |
| Schedule solver | &lt;90s for 3-MO subset |
| Copilot P95 | &lt;180s (LLM dependent) |
| Concurrent users (demo) | 1 presenter + 10 viewers |
| Test coverage | 870+ backend; 32 demo CP |

### 13.5 Technical dependencies

- Docker Desktop, PostgreSQL 16, Kong 3.x  
- Python 3.14+, FastAPI, OR-Tools  
- Node 20+, Vite, React  
- Ollama llama3.2:3b (Copilot demo)  
- POST-B: Keycloak, HashiCorp Vault/AWS SM, Stripe, SAP/D365 connectors  

---

## 14. Release criteria (v8.2.0)

| Criterion | Evidence |
|-----------|----------|
| 32/32 demo checkpoints | docs/demo-data/startrans-pre-demo.txt |
| 870+ unit/integration tests | docs/qa/full-test-suite-v8.2.0.txt |
| Star Trans data overlay | scripts/seed-startrans-demo.ps1 |
| Upload spec documented | docs/demo-data/STARTRANS-CSV-UPLOAD-SPEC.md |
| Production scaffolds in repo | Keycloak, secrets, Stripe, ERP base |
| Known POST-B items documented | READINESS.md, PRODUCTION-BLOCKERS.md |

---

## 15. Appendices

### A. Reference documents

- `docs/END-USER-GUIDE.md` — operator manual  
- `docs/demo-data/STARTRANS-DEMO-GUIDE.md` — 60-min demo script  
- `docs/PROJECT-PLAN-EXCEL-SCHEMA.md` — upload format  
- `docs/DEPLOYMENT-READINESS-v8.2.0.md` — ops checklist  
- `specs/010-v8-validation-convergence/` — validation convergence  

### B. Glossary

See END-USER-GUIDE Section 13.

### C. Document approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Engineering Lead | | | |
| Client Sponsor (Star Trans) | | | |

---

*End of PRD — IPE v8.2.0 Enterprise Specification*
