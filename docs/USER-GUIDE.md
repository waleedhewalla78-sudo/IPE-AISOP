# IPE Platform — End-User Guide

**Product:** IPE — Intelligent Planning Engine
**Audience:** Planners, supervisors, managers, executives, admins (non-technical friendly)
**Scope:** The full platform as it actually ships today — every hub, screen, agent (A1–A17) and command module (M1–M9), grounded in the real frontend routes, pages, and APIs in `E:\AISOP\ipe`.
**Language:** English. IPE ships with an Arabic/RTL locale (in-app language switcher); Arabic native-language QA sign-off (**G-R2-04**) is still **OPEN**, so Arabic copy is engineering-level and not yet certified.

> **Honesty note (read this first):** IPE is an intelligence layer *over* your ERP (Odoo), not a replacement for it. Several enterprise-grade capabilities are **engineering-complete but run on scaffold/mock data** because live Odoo staging (**PH1-02**) and IoT telemetry are not yet connected. Every such area is flagged inline and summarised in [Section 8 — Honest limitations](#8-honest-limitations--whats-mock-or-stubbed). Nothing in this guide invents a feature that isn't in the code.

---

## Table of contents

1. [Introduction & concepts](#1-introduction--concepts)
2. [Getting started](#2-getting-started)
3. [Data onboarding](#3-data-onboarding)
4. [Module-by-module walkthroughs](#4-module-by-module-walkthroughs)
5. [Daily / weekly / monthly routines](#5-daily--weekly--monthly-routines-the-planning-calendar)
6. [Roles & permissions](#6-roles--permissions)
7. [Troubleshooting & FAQ](#7-troubleshooting--faq)
8. [Honest limitations — what's mock or stubbed](#8-honest-limitations--whats-mock-or-stubbed)
9. [Quick reference — routes & agents](#9-quick-reference--routes--agents)

---

## 1. Introduction & concepts

### 1.1 What IPE is

IPE sits on top of your ERP and turns raw manufacturing data (orders, BOMs, routings, inventory, capacity, history) into **decisions**: what's feasible, what's at risk, and what to do about it. It does **not** own your master data — Odoo (or a seeded database) remains the system of record. IPE reads that data, scores it, predicts problems, proposes resolutions, and — where you allow it — acts within guardrails.

The mental model:

```
Odoo / seeded DB  →  IPE ingests  →  17 agents score & reason  →  planners decide  →  actions (some autonomous)  →  written back to Odoo*
```

\* Odoo write-back is currently mock — see [Section 8](#8-honest-limitations--whats-mock-or-stubbed).

### 1.2 The 17 agents (A1–A17)

Agents are specialised reasoning services. Each owns a slice of the planning problem. You rarely call an agent directly — they run behind the screens and behind the **Copilot**. The live roster (from `GET /api/v1/agents/status` and the Phase 4/6 agent endpoints):

| Agent | Name | Focus |
|-------|------|-------|
| A1 | Demand Intelligence | Demand signals, forecast, priority |
| A2 | Inventory Intelligence | Stock health, safety stock, reorder |
| A3 | Production Intelligence | Scheduling, capacity, work centres |
| A4 | Feasibility Intelligence | Gate scoring (material/capacity/labour) |
| A5 | Resolution Intelligence | Scenario generation & trade-offs |
| A6 | S&OP Intelligence | Sales & operations planning cycle |
| A7 | Copilot Orchestrator | Natural-language assistant routing |
| A8 | Customer Intelligence | Customer health, delay notices, portal |
| A9 | Procurement Intelligence | PO recommendations, supplier risk |
| A10 | Quality Intelligence | SPC, defect prediction, CAPA |
| A11 | Finance Intelligence | MO margin, decision P&L, cash |
| A12 | Sustainability Intelligence | Carbon / green scheduling |
| A13 | Commercial Intelligence (M8) | Dynamic pricing, deal profitability, contracts |
| A14 | Analytics Intelligence (M7) | Auto insights, trend/anomaly, prediction |
| A15 | Procurement Execution (M9) | 3-way match, receipt confirmation |
| A16 | Shop Floor Intelligence (M9) | Work instructions, time tracking, progress |
| A17 | Cross-Functional Orchestrator | Meta-agent: policy gate, conflict resolution, cross-functional ATP/CTP |

Agents A1–A7 are activated progressively as you complete the [data onboarding wizard](#3-data-onboarding). A8–A12 (premium) and A13–A17 (enterprise agentic) power the **Intelligence Hub** modules.

### 1.3 The 9 command modules (M1–M9)

The **Intelligence Hub** organises agent output into nine business command modules:

| Module | Name | Backing agents |
|--------|------|----------------|
| M1 | Demand Command | A1, A8 |
| M2 | Production Command | A3, A4, A5 |
| M3 | Supply Command | A2, A9 |
| M4 | Quality Command | A10 |
| M5 | Finance Command | A11 |
| M6 | Customer Command | A8 |
| M7 | Analytics Command | A14 |
| M8 | Commercial Command | A13 |
| M9 | Procurement + Shop Floor Command | A15, A16 |

### 1.4 Planning horizons

IPE plans across **three simultaneous horizons**, and decisions cascade between them:

- **Strategic** — 12–24 months, monthly/quarterly granularity (revenue targets, growth, capex).
- **Tactical** — 1–6 months, weekly granularity (S&OP consensus, MPS).
- **Operational** — 0–1 month, daily/shift granularity (active MOs, at-risk orders, shop floor).

You can **cascade a decision down** (strategic goal → tactical/operational plan) or **escalate a constraint up** (shop-floor bottleneck → tactical/strategic) from the **Planning → Horizons** screen.

### 1.5 Shadow mode & autonomy

By default IPE runs in **shadow mode**: it scores and recommends, but a human approves every action. Feasibility scoring auto-classifies each manufacturing order (MO):

- **≥ 90** → eligible for auto-confirm (only if autonomy is enabled)
- **70–89** → queued for planner review
- **< 70** → routed to the Resolution Center

Autonomous overnight actions (reorders, batching, low-risk resolutions) run only inside **guardrails** and are always reversible within a configurable window.

---

## 2. Getting started

### 2.1 Bring the stack up

From `E:\AISOP\ipe` (PowerShell):

```powershell
cd E:\AISOP\ipe
docker compose -f infrastructure/docker/docker-compose.release2.yml up -d
```

This starts the database, Redis, Kafka, all backend services, the Kong API gateway, and the web UI. First start can take a few minutes while images build and migrations run.

If the database is empty (fresh volume), load demo data:

```powershell
.\scripts\seed-data.ps1
```

### 2.2 Access URLs

| Surface | URL | Notes |
|---------|-----|-------|
| Web UI | http://localhost:8082 | The app you log into |
| API Gateway (Kong) | http://localhost:8000 | All `/api/v1/*` calls route here |
| Health check | http://localhost:8000/api/v1/health | Should return `{"status":"ok"}` |

### 2.3 Log in

Open **http://localhost:8082** → you'll be redirected to `/login`.

Demo credentials (tenant `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11`, `AUTH_MODE=local`):

| Email | Password | Role |
|-------|----------|------|
| `Ahmed@nour` | `admin` | Admin |
| `admin@demo.com` | `demo` | Admin |
| `planner@demo.com` | `demo` | Planner |

> In non-production environments the passwords `demo` and `admin` are accepted for any seeded user. Login issues a JWT that carries your `role` and `tenant_id`; the UI attaches these to every API call automatically.

**Steps:**
1. Enter email + password, click **Sign in**.
2. On success you land on the **Unified Workspace** (`/workspace`), the app home.
3. Your session refreshes silently; if it expires you're returned to `/login`.

### 2.4 Navigation map of the whole app

The left **sidebar** is the top-level map. Selecting a hub opens a tabbed workspace (the "Hub Shell"). The hubs and their tabs:

| Sidebar item | Route | Tabs / screens inside |
|--------------|-------|-----------------------|
| 🧩 Workspace | `/workspace` | Unified home (cross-hub summary) |
| 📊 Planning | `/planning` | Dashboard · Cockpit · Horizons · Demand · Scenarios · Control Tower · Resolution · Schedule · Predictions · Root Cause |
| 🎯 Command Center | `/command-center` | Dashboard · Ops Live · War Room · Outcomes · OTD Analytics · Executive · Equipment · Cost of Chaos · S&OP Report · Operations Deep |
| 🧠 Intelligence | `/intelligence` | Today's Pulse · M1 Demand · M2 Production · M3 Supply · M4 Quality · M5 Finance · M6 Customer · M7 Analytics · M8 Commercial · M9 Procurement · S&OP Deep · Demand Deep · Production Deep |
| 📦 Customer Portal | `/customer-portal` | Read-only external order tracking |
| 💬 Copilot | `/ai-governance/copilot` | Assistant (also global via Ctrl+K) |
| 🌐 Supply Chain | `/supply-chain` | Supply Planning · Orders · Procurement · Tariff · SCN Portal · Inventory · Suppliers |
| 🤖 AI & Governance | `/ai-governance` | Copilot · Meeting Prep · Design AI · AI Trust · MDR · Compliance · Quality · Sustainability |
| 🏭 Shop Floor | `/shop-floor` | Live work orders |
| ⚙️ Platform | `/platform` | Admin · Upload · Agents · Exceptions · Odoo Config · Onboarding · ML Ops · Ops |

Notes:
- The default route `/` redirects to **Workspace**. Any unknown URL redirects to **Planning → Dashboard**.
- Older bookmark-style URLs (`/control-tower`, `/copilot`, `/war-room`, `/admin`, etc.) still work — they redirect to the new hub tab.
- Some tabs are hidden in the "release1" constrained profile; the full profile (`VITE_RELEASE_PROFILE=release2`, the default compose build) shows everything above.

---

## 3. Data onboarding

There are three ways data enters IPE. Know which one applies before you start.

| Data | How it loads | Via UI? |
|------|--------------|---------|
| Master data (products, work centres, BOM/routing, MOs, demand, suppliers, customers, inventory, supply orders, operators) | SQL seed scripts **or** Odoo sync | No (seed) / Yes (Odoo Config) |
| Onboarding Excel workbooks (14 file types across 5 phases) | **Upload Center** wizard (`upload-svc`) | **Yes** |
| Project plan (Gantt) | Schedule page upload (`.xlsx`) | **Yes** |
| Odoo ERP live data | Connector XML-RPC/JSON-RPC sync | Yes (Odoo Config) |
| Tariff matrix | Parser exists in code; **no HTTP upload wired** | No |

### 3.1 The Upload Wizard (5 phases)

**Where:** Platform → **Upload** (`/platform/upload`, the *Data Upload Center*). Backed by `upload-svc` (Kong route `/api/v1/upload`).

The wizard onboards data in **five ordered phases**. Each phase, when completed, **activates agents**. You cannot skip ahead — a phase is *locked* until the prior phase is complete.

| Phase | Name | File types (columns are validated) | Agents activated |
|-------|------|-------------------------------------|------------------|
| 1 | Master Data | `product_master`, `customer_master`, `supplier_master`, `work_centre_master` | A2, A4 |
| 2 | Product Structure | `bom`, `routing` | A4 |
| 3 | Planning Parameters | `capacity_calendar`, `lead_time`, `cost_data` | A2, A3, A5 |
| 4 | Current State | `inventory`, `production_orders`, `sales_orders`, `purchase_orders` | A1, A2, A3, A4 |
| 5 | Historical Data | `historical_otd` | A6, A7 |

**14 file types total.** When all phases complete, the message confirms *"All 14 files loaded. IPE agents are now active."*

**Step-by-step:**
1. Open **Platform → Upload**. You'll see five phase cards showing status (`in_progress` / `complete` / `locked`), files uploaded vs required, and which agents are active vs pending.
2. Pick a **file type** from the dropdown (it lists the file types for the phases).
3. Click the file picker and choose an `.xlsx`, `.xlsm`, or `.csv` file.
4. IPE validates the file in **4 stages** and reports the result inline: e.g. *"Accepted 47/50 rows · 3 rejected"*.
5. Fix rejected rows (see [error report](#33-error-report-download) below) and re-upload if needed.
6. When a phase's required files are all uploaded, click **Complete phase**. The newly activated agents appear, and the next phase unlocks.

**What the 4 validation stages check:**
- **Stage 1 — Structure:** file format is `.xlsx`/`.csv`, and all required columns exist.
- **Stage 2 — Types:** numeric fields (`quantity`, `on_hand`, `unit_cost`, `available_hours`, `lead_time_days`) are numeric and non-negative; duplicate keys flagged.
- **Stage 3 — Referential:** codes reference known masters (e.g. a BOM's `product_code` must exist in Product Master; sales orders' `customer_code`/`product_code` must be known).
- **Stage 4 — Business:** overall pass/fail rollup.

### 3.2 Download a blank template

Each file type has a generated template with the exact required columns and a sample row:

- In-app: the Upload Center offers per-type templates via `GET /api/v1/upload/templates/{file_type}` (downloads `<type>_template.xlsx`).
- List all templates: `GET /api/v1/upload/templates`.
- Pre-built QA workbooks with sample rows and column comments live at `docs/qa/upload-templates/` (see its `README.md`). Index:

| Template file | Entity | Load path |
|---------------|--------|-----------|
| `products_upload_template.xlsx` | Products | SQL seed / Odoo `product.product` |
| `work_centers_upload_template.xlsx` | Work centres | SQL seed / Odoo `mrp.workcenter` |
| `bom_routing_upload_template.xlsx` | BOM + routing | SQL seed / Odoo `mrp.bom` |
| `mrp_orders_upload_template.xlsx` | Manufacturing orders | SQL seed / Odoo `mrp.production` |
| `demand_lines_upload_template.xlsx` | Demand / sales lines | SQL seed / Odoo `sale.order.line` |
| `suppliers_upload_template.xlsx` | Suppliers | SQL seed / Odoo partner |
| `customers_upload_template.xlsx` | Customers | SQL seed / Odoo partner |
| `inventory_upload_template.xlsx` | Inventory positions | SQL seed |
| `supply_orders_upload_template.xlsx` | Supply / purchase orders | SQL seed / Odoo `purchase.order.line` |
| `operators_upload_template.xlsx` | Operators | SQL seed |
| `project_plan_upload_template.xlsx` | Project plan (Gantt) | **UI upload** (Schedule page) |
| `tariff_matrix_upload_template.xlsx` | Tariff shock input | Parser ready; **no upload API** |
| `odoo_sync_entities_reference.xlsx` | Field-map reference | Mapping doc, not an upload |

**Recommended load order (SQL / importer):** Products → Work centres → Operators → Customers → Suppliers → BOM/routing → Inventory → Supply orders → MOs → Demand lines → Project plan.

### 3.3 Error report download

Every upload returns a `download_errors_url`. To get a spreadsheet of exactly which rows/columns failed and why:

- `GET /api/v1/upload/{upload_id}/errors.xlsx`

The workbook has columns: `row`, `column`, `value`, `message`, `severity` (`error` or `warning`). Fix those rows in your source file and re-upload.

### 3.4 Project plan (Gantt) upload

Master project/Gantt plans upload through the **Schedule** page (not the wizard):
- Endpoint: `POST /api/v1/capacity/project-plans/upload` (`.xlsx` only, max 5 MB, preferred sheet name `ProjectPlan`).
- `MO_ID` values must match `erp_mo_id` already in the database; `WORK_CENTER_CODE` must match seeded WC codes.

### 3.5 Odoo sync (ERP connection)

To ingest live ERP data instead of seeds, configure a connection in **Platform → Odoo Config** — see [Section 4.9](#49-odoo-config-platform--odoo-config). Live Odoo staging (**PH1-02**) is currently OPEN; until it's connected, use the SQL seed or the mock Odoo service for testing.

---

## 4. Module-by-module walkthroughs

Every major screen below is grounded in a real route and its real API calls. Where a screen shows a built-in "offline shell" (demo fallback data when the API is unavailable), that's noted so you're not surprised.

### 4.1 Planning Hub

Route root: `/planning`. Purpose: *Detect → decide → schedule.*

#### 4.1.1 Control Tower — `/planning/control-tower`
Your morning production-health screen (A4 Feasibility).
1. Open **Planning → Control Tower**.
2. Read the **KPI cards**: open demands, active MOs, average feasibility, bottleneck count, delay alerts. (KPIs come from `GET /api/v1/feasibility/kpis`; in shadow mode OTD may read "not available" rather than a fake 0%.)
3. Scan the **MO Risk Queue** (`GET /api/v1/feasibility/queue`) — rows are colour-coded: green ≥ 90, yellow 70–89, red < 70, with the primary constraint (material / capacity / labour) shown.
4. Review the **Bottleneck map** — work centres above ~85% utilisation (`POST /api/v1/capacity/analyze`).
5. Click **Resolve** on a red row → jumps to the Resolution Center for that MO.
- *Expect:* if the database isn't seeded, the queue is empty. Run `seed-data.ps1`.

#### 4.1.2 Resolution Center — `/planning/resolution`
Turn a constraint into scored, comparable options (A5 Resolution).
1. Open **Planning → Resolution**.
2. Select an MO from the constraint list (severity badges, constraint type & value).
3. Review the **scenario cards** (e.g. expedite PO, substitute material, split MO, alternate work centre).
4. Compare **cost vs delivery impact** and the business score; the recommended option is highlighted.
5. Approve the option you want (scenarios come from `/api/v1/resolution/scenarios`; approval is optimistic-locked).
- *Talking point:* the AI scores options; the human picks the trade-off.

#### 4.1.3 Copilot (Ctrl+K) — `/ai-governance/copilot`
A natural-language assistant (A7 Copilot Orchestrator, `nlp-svc`).
1. Press **Ctrl+K** (or **Cmd+K**) from *any* screen to open the Copilot side-drawer, or use the floating **AI** button bottom-right, or open the full page from **AI & Governance → Copilot**.
2. Choose an **agent role** (planner / manager / supervisor / executive) — the assistant tailors its answers; your JWT role is the default.
3. Type a question and **Send**. Examples that work well:
   - "Which orders are at risk this week?"
   - "What is blocking MO-DEMO-001?"
   - "Show bottleneck work centres."
4. Each answer shows the detected **intent** and any **sources**; suggested follow-ups appear as chips.
- *Notes:* the Copilot calls `POST /api/v1/copilot/session` then `POST /api/v1/copilot/query`, with a 300-second timeout for LLM routes. If no LLM key is configured it responds with a graceful offline/limited message rather than failing.

#### 4.1.4 Planning Cockpit — `/planning/cockpit`
Plan-health command surface (`GET /api/v1/planning-command/cockpit`).
1. Open **Planning → Cockpit**.
2. Read the five health tiles: **Plan coverage, Demand-supply balance, Horizon coverage, Stability, Frozen weeks**.
3. Work the **Attention required** queue (colour-coded actions like "5 MOs at risk → resolve", "MRP run needed → run_mrp").
4. Use the **weekly horizon** table (coverage, MOs, at-risk, materials, capacity per week).
5. Run inline planning tools from the button row — each posts to `/api/v1/planning-command/*` and shows the JSON result:
   - **Update MPS**, **Run MRP**, **Check ATP/CTP**, **RCCP**, **Level production**, **Scenario +20%**.
- *Offline shell:* if the API is down, the cockpit shows representative demo numbers with an amber "offline shell" banner.

#### 4.1.5 Master Production Schedule (MPS)
Triggered from the Cockpit ("Update MPS") or directly: `POST /api/v1/planning-command/mps`. Computes the period-by-period production schedule from opening inventory, lot size, safety stock, and weekly demand.

#### 4.1.6 Material Requirements Planning (MRP)
"Run MRP" → `POST /api/v1/planning-command/mrp/explode`. Explodes the BOM for an MO quantity against on-hand inventory (with scrap %), returning net requirements per component.

#### 4.1.7 ATP / CTP / PTP (order promising)
"Check ATP/CTP" → `POST /api/v1/planning-command/promise`. Given an order (qty, requested date, inventory available, capacity hours, lead times), IPE returns an **available-to-promise / capable-to-promise** date and confidence. The enterprise cross-functional promise (A17, price + margin aware) is `POST /api/v1/enterprise/orchestrator/atp`.

#### 4.1.8 Leveling
"Level production" → `POST /api/v1/planning-command/level`. Smooths lumpy weekly demand against a weekly capacity ceiling.

#### 4.1.9 RCCP / CRP (rough-cut & detailed capacity)
- **RCCP:** `POST /api/v1/planning-command/capacity/rccp` — rough-cut load vs capacity for a week.
- **CRP:** `POST /api/v1/planning-command/capacity/crp` — detailed daily load for a work centre (hours/shift × shifts/day).

#### 4.1.10 Scenarios — `/planning/scenarios` & cascade
- **Scenario Workbench** (`/planning/scenarios`) — what-if simulations.
- **Scenario cascade:** "Scenario +20%" → `POST /api/v1/planning-command/scenarios/cascade`. Applies a demand uplift and cascades the effect to revenue, utilisation, material cover, and OTD.

#### 4.1.11 Horizons — `/planning/horizons`
Three-horizon planning (`GET /api/v1/planning-command/horizons`).
1. Open **Planning → Horizons**.
2. Read the three cards (Strategic / Tactical / Operational): window, granularity, coverage %, health bar, pending decisions, key metrics.
3. Click **Cascade decision down ▾** to push a strategic goal into tactical/operational plans, or **Escalate constraint up ▴** to raise a shop-floor constraint (`POST /api/v1/planning-command/horizons/cascade`).
- *Offline shell:* falls back to representative coverage numbers if the API is unavailable.

#### 4.1.12 Schedule — `/planning/schedule`
Constraint-aware scheduling (OR-Tools CP-SAT, `cap-svc`).
1. Open **Planning → Schedule**.
2. Click **Refresh** to load the Gantt from live MOs + routing.
3. Review operations across work centres; compare planned vs AI-suggested bars when the solver returns assignments.
4. Upload a project plan here if you maintain a Gantt externally ([Section 3.4](#34-project-plan-gantt-upload)).

#### 4.1.13 Predictions — `/planning/predictions`
Predictive risk (`fea-svc`). Shows T+3 / T+7 / T+14 risk predictions per MO (`GET /api/v1/feasibility/predict/{mo_id}`).

#### 4.1.14 Root Cause — `/planning/root-cause` (and `/planning/root-cause/:moId`)
5-why root-cause chain (`GET /api/v1/feasibility/root-cause/{mo_id}`) with horizon-tagged recommendations.

### 4.2 Command Center

Route root: `/command-center`. Purpose: *Alerts, KPIs, and the financial impact of disruption.*

#### 4.2.1 Dashboard — `/command-center/dashboard`
The command overview (alerts, KPIs, live status roll-up).

#### 4.2.2 Ops Live — `/command-center/ops-live`
Live shop-floor operations (`GET /api/v1/planning-command/ops/dashboard`, `.../ops/performance`, `.../ops/predictive`).
1. Open **Command Center → Ops Live**.
2. Read the header: current shift, supervisor, MOs in production, on-schedule vs behind.
3. Scan the scorecard tiles: **Output (done/planned), OEE, Quality, On-time starts**.
4. Review **Work centres** (utilisation, current MO/product) and **Live alerts** (timestamped).
5. See the **Performance cockpit** (factory OEE, OTD) and **Predictive command** (3/7/14-day signal counts) panels.
6. Click **Activate War Room** to escalate an incident (`POST /api/v1/planning-command/ops/war-room`).
- *Offline shell:* shows a representative live snapshot if the API is down.

#### 4.2.3 War Room — `/command-center/war-room`
Disruption aggregation and mitigation.
1. Open **Command Center → War Room** (or activate from Ops Live).
2. Review KPI cards: active disruptions, impacted MOs, revenue at risk, mitigation options.
3. Open a disruption event; review the impacted-MO table and mitigation scenarios (cost / OTD / delay reduction / confidence).
4. Assign a mitigation as a task. War-room simulation uses `POST /api/v1/planning-command/ops/war-room`.

#### 4.2.4 Shift Handover
Structured handover between shifts: `POST /api/v1/planning-command/ops/shift-handover`. Captures completed MOs, in-progress work, open issues, quality holds, and free-text notes to produce a handover brief.

#### 4.2.5 Action Tracker
Cross-shift action list:
- List: `GET /api/v1/planning-command/actions` (optional `status` filter).
- Create: `POST /api/v1/planning-command/actions` (title, owner, source, due, MO).
- Complete: `POST /api/v1/planning-command/actions/{action_id}/complete` (with outcome).

#### 4.2.6 Performance / OEE
`GET /api/v1/planning-command/ops/performance` — factory OEE, KPIs (OTD, throughput). The deeper OEE improvement programme is under **Operations Deep** (Section 4.5.5).

#### 4.2.7 Predictive Command
`GET /api/v1/planning-command/ops/predictive` — forward-looking signal summary across 3/7/14-day windows (total signals, critical count).

#### 4.2.8 Other Command tabs
- **Executive** (`/command-center/executive`) — leadership P&L, S&OP gap, what-if.
- **Outcomes** (`/command-center/outcomes`) — realised business outcomes.
- **Equipment** (`/command-center/equipment`) — equipment health.
- **Cost of Chaos** (`/command-center/cost-of-chaos`) — quantified cost of disruption.
- **S&OP Report** (`/command-center/sop-report`) — auto-generated executive S&OP brief.
- **Operations Deep** (`/command-center/operations-deep`) — see Section 4.5.5.

### 4.3 OTD Analytics — `/command-center/otd-analytics`

On-Time-Delivery analytics (`dpe-svc`, migration 039). This is a polished charting dashboard (uses Recharts).
1. Open **Command Center → OTD Analytics**.
2. Pick a **date range** (30 / 60 / 90 / 180 days) and any filters (`fetchFilterOptions`).
3. Read the headline **OTD KPI** (colour-coded: ≥90 excellent, ≥80 good, ≥70 warning, else risk) vs the **baseline** (`fetchOtdKpis`, `fetchOtdBaseline`).
4. Review the **trend** line (`fetchOtdTrend`) and the **root-cause** breakdown by cause (`fetchOtdRootCause`).
5. Read the auto-generated **narrative** ("OTD improved from X% to Y%, top cause … , est. savings $…") and the **Cost of Chaos** figure (`fetchOtdCostOfChaos`).
- *Empty state:* with no completed-MO history, the page shows an empty state rather than fake numbers.

### 4.4 Intelligence Hub

Route root: `/intelligence`. Subtitle: *Nine command modules · 17 agents · autonomous cross-functional orchestration.* Tabs: Today's Pulse, M1–M9, and the three "Deep" workbenches.

#### 4.4.1 Today's Pulse — `/intelligence/pulse`
Morning brief (A7 + Phase 4): `GET /api/v1/intelligence/pulse?planner_name=...`. Summarises overnight autonomous actions and the day's priorities.

#### 4.4.2 M1 Demand / M2 Production / M3 Supply / M4 Quality / M5 Finance / M6 Customer
These six are **module shells** — each is a concise landing page with a description and quick links into the concrete screens that do the work:
- **M1 Demand** → Demand forecast, Orders (A1 + A8).
- **M2 Production** → Control Tower, Predictions, Schedule (A3/A4/A5 + predictive risk).
- **M3 Supply** → Inventory, Procurement, Suppliers (A2 + A9 PO recommendations, supplier risk).
- **M4 Quality** → Quality dashboard (A10 SPC / defect prediction / CAPA).
- **M5 Finance** → Cost of Chaos, Executive (A11 MO margin / decision P&L / cash).
- **M6 Customer** → Customer Portal, Order management (A8 customer health / delay notices).

#### 4.4.3 M7 Analytics Command (A14) — `/intelligence/analytics`
Automated insights, trend, anomaly, and predictions — "SAC-equivalent, zero analyst setup".
1. Open the tab; **auto insights** load on entry (`POST /api/v1/enterprise/analytics/insights`) as cards with category, confidence %, and a suggested action.
2. Use the tool buttons to run **Predictions** (`analytics/predictions`), **Trend** (`analytics/trend`, e.g. copper cost), and **Anomaly** (`analytics/anomaly`, z-score) on a series; results render as JSON.
- ⚠️ **Market data / FX feed is NOT wired** — analytics run on supplied/seeded history only (PH1-02 OPEN). See [Section 8](#8-honest-limitations--whats-mock-or-stubbed).

#### 4.4.4 M8 Commercial Command (A13) — `/intelligence/commercial`
Dynamic pricing, deal profitability, contract compliance ("SD-equivalent above Odoo/SAP"). Tool buttons:
- **Optimize price** — `POST /api/v1/enterprise/commercial/pricing` (list price, cost, quantity, tier, competitive pressure, margin floor, discount authority).
- **Deal profitability** — `.../commercial/deal-profitability`.
- **Contract compliance** — `.../commercial/contract-compliance` (volume commitment, YTD delivered, SLA).
- The same page also exposes the **A17 Cross-Functional Orchestrator**: Orchestrated ATP/CTP, Enforce policies, Cascade demand change.

#### 4.4.5 M9 Procurement + Shop Floor Command (A15 · A16) — `/intelligence/procurement`
Tool buttons:
- **3-way match** — `POST /api/v1/enterprise/procurement/three-way-match` (PO vs invoice vs receipt, tolerances, auto-approve ceiling).
- **Confirm receipt** — `.../procurement/receipt`.
- **Work instructions** — `.../shop-floor/work-instructions`.
- **Time tracking** — `.../shop-floor/time-track`.
- **Production progress** — `.../shop-floor/progress`.
- ⚠️ **IoT/machine telemetry is a STUB** and **Odoo PO/invoice write-back is mock** (PH1-02 OPEN).

> **Deployment note:** the `/api/v1/enterprise/*` endpoints (M7/M8/M9, A13–A17) are **not** exposed through the Kong gateway route table in the release2 profile — they are served directly by `dpe-svc`. In a Kong-only deployment these tool buttons may show *"offline / unavailable"*; the pages degrade gracefully and never fabricate data.

#### 4.4.6 Customer health, PO recs, quality, finance, sustainability (A8–A12)
These premium agents are reachable via the module screens above and directly:
- **A8 Customer:** `POST /api/v1/intelligence/customer/health`, `.../customer/delay-notice`.
- **A11 Finance:** `.../finance/mo-margin`, `.../finance/decision-pnl`, `.../finance/cash-flow`.
- **Autonomous overnight (guardrailed):** `.../autonomous/overnight` evaluates reorder, batching, low-risk resolution, and quality-risk candidates and returns which are safe to auto-execute.
- **A9 Procurement / A10 Quality / A12 Sustainability** surface through Supply Chain (Suppliers/Procurement), AI & Governance → Quality, and AI & Governance → Sustainability respectively.

### 4.5 Deep Planning (Phase 7)

Phase 7 deepens five disciplines. The three Intelligence "Deep" tabs and the Command "Operations Deep" tab are **analyst workbenches**: a titled panel with a row of buttons; clicking a button runs the analysis and shows the structured JSON result. All under `/api/v1/planning-command/*`.

#### 4.5.1 Three Horizons
See Section 4.1.11 (`/planning/horizons`).

#### 4.5.2 S&OP Deep — `/intelligence/sop-deep`
*"Every S&OP decision is simultaneously a volume and a financial decision."*
- **Financial S&OP (P&L per consensus)** — `POST .../sop/financial` (with A11 margin-floor alerts).
- **Rolling S&OP (event-driven)** — `.../sop/rolling` (recalculates consensus on events).
- **Demand shaping options** — `.../sop/demand-shaping` (shift mix off a constrained work centre).
- **Portfolio mix optimization** — `.../sop/portfolio` (best product mix per constraint hour).

#### 4.5.3 Demand Deep — `/intelligence/demand-deep`
*"Demand decomposed into components, each independently managed."*
- **Decompose demand** (base / trend / seasonality / promo / event / noise, with 95% CI) — `.../demand/decompose`.
- **Collaboration consensus** (weighted inputs, disagreement flag) — `.../demand/collaborate`.
- **NPI forecast** (analogy ramp, cannibalization, market sizing) — `.../demand/npi`.

#### 4.5.4 Production Deep — `/intelligence/production-deep`
*"Sequence-dependent setup, multi-resource, campaign, skills SPOF, dynamic make-or-buy."*
- **Setup-sequence optimize** — `.../production/setup-sequence` (minimise changeovers; exact ≤ 8 jobs else greedy).
- **Multi-resource schedule** — `.../production/multi-resource`.
- **Campaign plan** — `.../production/campaign`.
- **Labour + SPOF flags** — `.../production/labour` (single-point-of-failure skill detection).
- **Make-or-buy (at bottleneck)** — `.../production/make-or-buy` (dynamic rule using utilisation).

#### 4.5.5 Operations Deep — `/command-center/operations-deep`
*"OEE, Gemba, Andon, KPI Tree, Standard Work."*
- **OEE improvement programme** — `POST .../operations/oee-programme` (availability × performance × quality vs target).
- **Digital Gemba** — `GET .../operations/gemba`. ⚠️ **STUB** — machine status is not live (`iot_live=false`, PH1-02 OPEN).
- **Andon board** — `GET .../operations/andon`; **Trigger Andon** — `POST .../operations/andon` (colour, work centre, reporter, message); **Resolve** — `POST .../operations/andon/{alert_id}/resolve`. ⚠️ Andon state is **in-memory** (database persistence deferred to Wave 2 — alerts reset when the service restarts).
- **KPI tree drill-down** — `GET .../operations/kpi-tree`.
- **Standard work (A16)** — `POST .../operations/standard-work` (steps vs actuals; >120% time flags).
- **Planning calendar** — `GET .../calendar` (see Section 5).

### 4.6 Supply Chain Hub — `/supply-chain`
Tabs: **Supply Planning, Orders, Procurement, Tariff, SCN Portal, Inventory, Suppliers**.
- **Suppliers** (`/supply-chain/suppliers`) — supplier scorecards & predictive stockout / supplier score (A9, `mat-svc`).
- **Procurement** (`/supply-chain/procurement`) — PO recommendations.
- **Inventory** (`/supply-chain/inventory`) — stock positions, ABC/XYZ, safety stock.
- **Tariff** (`/supply-chain/tariff`) — tariff-shock analysis (parser exists; no HTTP upload — inputs are seeded/coded).
- **SCN Portal** (`/supply-chain/scn-portal`) — supply-chain-network / supplier collaboration view.
- **Orders** (`/supply-chain/orders`) — order management.

### 4.7 AI & Governance Hub — `/ai-governance`
Tabs: **Copilot, Meeting Prep, Design AI, AI Trust, MDR, Compliance, Quality, Sustainability**.
- **Copilot** — Section 4.1.3.
- **Meeting Prep** (`/ai-governance/meeting-prep`, and `/meeting-prep/:type`) — auto-generated meeting brief templates (A7).
- **AI Trust** (`/ai-governance/ai-trust`) — model transparency, accuracy, adoption, AI-vs-manual impact.
- **MDR** (`/ai-governance/mdr`) — model/decision registry dashboard.
- **Compliance** (`/ai-governance/compliance`) — compliance KPIs & controls.
- **Quality** (`/ai-governance/quality`) — SPC, defect prediction, CAPA (A10).
- **Sustainability** (`/ai-governance/sustainability`) — carbon/green metrics (A12).

### 4.8 Shop Floor — `/shop-floor`
Live work-order view for operators/supervisors (real API with fallback). Shows current work orders by work centre. Note operator-tablet UI polish and live IoT are deferred/stubbed.

### 4.9 Odoo Config (Platform → Odoo Config)
Self-service ERP connection management (`/platform/odoo-config`, connector service).
1. Open **Platform → Odoo Config**.
2. Click **Add** and fill: display name, host URL (e.g. `http://odoo.example:8069`), database, username, password, environment (staging/production), sync interval (5/15/30/60 min).
3. **Save**, then **Test** the saved connection — a green dot and Odoo version confirm success (`/api/v1/erp/odoo/...`, `/api/v1/sync/...`).
4. **Activate** the connection you want live (only one active at a time).
5. Use **Sync now** to run an immediate sync, **Logs** to review sync history, **Edit**/**Deactivate** as needed.
- The **Sync status** card shows last sync, next scheduled sync, and the active connection.
- Version-specific config (Odoo 17 vs 19 field aliases) lives under `/platform/odoo-config/versions`.
- ⚠️ **Live Odoo staging (PH1-02) is OPEN.** Until a real Odoo is connected, testing uses the mock Odoo service or SQL seed.

### 4.10 Customer Portal — `/customer-portal`
Read-only external view for customers (A8): `GET /api/v1/orders/portal/summary`.
1. Open **Customer Portal**.
2. Review the order table: **Order, Status, Delivery date, Confidence** (green/amber/red), **Invoice status**.
- It is strictly read-only. If the portal API isn't reachable it shows an empty read-only state.

### 4.11 Platform Hub — `/platform`
Admin & operations tools. Tabs: **Admin, Upload, Agents, Exceptions, Odoo Config, Onboarding, ML Ops, Ops**.
- **Admin** (`/platform/admin`) — tenant/user & Odoo settings.
- **Upload** (`/platform/upload`) — the [Data Upload Center](#31-the-upload-wizard-5-phases).
- **Agents** (`/platform/agents`) — **Agent Dashboard**: live status of every agent (`GET /api/v1/agents/status`), each showing agent id, name, health, and last run.
- **Exceptions** (`/platform/exceptions`) — **Exception Manager**: the SLA lifecycle for agent-raised exceptions (create / acknowledge / resolve / escalate via `/api/v1/exceptions/*`).
- **Onboarding** (`/platform/onboarding`) — the account/company setup wizard (welcome → company → plan → admin → ERP → done).
- **ML Ops** (`/platform/ml-ops`) — model operations dashboard.
- **Ops** (`/platform/ops`) — platform operations dashboard.

### 4.12 Agent orchestration (behind the screens)
- Run the full agent chain (dry-run): `POST /api/v1/agents/run-chain` (trigger + changed data).
- Financial decision framework: `POST /api/v1/agents/financial-options` ranks options by P&L impact.

---

## 5. Daily / weekly / monthly routines (the planning calendar)

IPE exposes an **integrated planning calendar** at `GET /api/v1/planning-command/calendar` (optional `cadence` filter). Use it to see "who does what, when". A practical cadence mapped to the screens above:

### Daily (shift-based) — supervisors & planners
1. **Ops Live** (`/command-center/ops-live`) — check the shift scorecard, work-centre load, and live alerts at shift start.
2. **Andon** (Operations Deep) — clear/triage any active Andon calls. *(In-memory — see Section 8.)*
3. **Control Tower** (`/planning/control-tower`) — work the MO risk queue; resolve red rows.
4. **Today's Pulse** (`/intelligence/pulse`) — review overnight autonomous actions.
5. **Shift Handover** — file the structured handover to the next shift.

### Weekly — planners
1. **Planning Cockpit** (`/planning/cockpit`) — review plan health & attention queue.
2. **Run MRP** and **Update MPS** for the new order book.
3. **RCCP / CRP** — confirm rough-cut and detailed capacity.
4. **Level production** and re-run **Schedule**.
5. **Suppliers / Procurement** — review PO recommendations and supplier risk.
6. **Predictions & Root Cause** — pre-empt next-week risk.

### Monthly — S&OP / leadership
1. **S&OP Deep** (`/intelligence/sop-deep`) — financial S&OP, rolling recalculation, demand shaping, portfolio mix.
2. **Horizons** (`/planning/horizons`) — reconcile strategic → tactical → operational; cascade decisions.
3. **Executive** & **S&OP Report** (Command Center) — leadership P&L, gap analysis, executive brief.
4. **OTD Analytics** & **Outcomes** — review realised performance and cost of chaos.
5. **AI Trust / Compliance / Sustainability** — governance review.

---

## 6. Roles & permissions

IPE issues a JWT at login carrying your **role** and **tenant_id**. There are five roles referenced across the app:

| Role | Typical use |
|------|-------------|
| `admin` | Full access incl. Platform (users, Odoo config, uploads) |
| `planner` | Planning, scheduling, resolution, supply chain |
| `manager` | Oversight, Command Center, approvals |
| `supervisor` | Shop floor, Ops Live, Andon, handover |
| `executive` | Command Center leadership views, S&OP, outcomes |

How enforcement works today:
- **Page access:** the frontend `ProtectedRoute` gate checks that you are **authenticated** (a valid session). It does not itself hide hubs by role — every signed-in user can navigate the hubs.
- **Action-level RBAC:** sensitive **API** actions enforce roles server-side (e.g. capacity scheduling/cost-optimization, resolution approval, feasibility auto-confirm, copilot chat). If your role lacks permission, the API returns 401/403 and the UI surfaces the error.
- **Copilot** adapts its persona and answers to the selected role (defaulting to your JWT role).
- **Tenant isolation:** every record is scoped by `tenant_id` (row-level security). You only ever see your tenant's data; the gateway strips any client-supplied tenant header and trusts the JWT claim.

---

## 7. Troubleshooting & FAQ

**The stack is down / I need to restart it.**
```powershell
cd E:\AISOP\ipe
docker compose -f infrastructure/docker/docker-compose.release2.yml up -d
# check everything is running:
docker compose -f infrastructure/docker/docker-compose.release2.yml ps
```

**http://localhost:8082 refuses to connect.**
- The `web-ui` container maps host **8082 → container 80**. Confirm it's up: `docker compose -f infrastructure/docker/docker-compose.release2.yml ps web-ui`.
- If not, start/recreate it: `docker compose -f infrastructure/docker/docker-compose.release2.yml up -d web-ui`.
- If another process holds port 8082, stop it or change the host port mapping in the compose file.

**Login fails (401 Invalid credentials).**
- Ensure the database is seeded (users live in `cdm_user`): `.\scripts\seed-data.ps1`.
- Use a seeded account: `Ahmed@nour` / `admin`, or `admin@demo.com` / `demo`.
- Confirm backends are healthy: `curl http://localhost:8000/api/v1/health`.

**Screens are empty (Control Tower, Resolution, Schedule, OTD).**
- The database has no data. Run the seed script, or complete the [Upload Wizard](#31-the-upload-wizard-5-phases), or connect Odoo.
- Pages that show representative numbers with an amber "offline shell" banner mean the specific API was unreachable — check the service is up.

**API returns 500 on data routes.**
- Recreate the app containers after any env change:
  `docker compose -f infrastructure/docker/docker-compose.release2.yml up -d --force-recreate dpe-svc kong`

**Frontend can't reach the API.**
- All `/api/v1/*` traffic goes through Kong on port 8000. Confirm Kong is healthy (`docker compose ... ps kong`).

**Upload service unavailable on the Upload page.**
- Ensure `upload-svc` is running (Kong route `/api/v1/upload`). The page will say *"Upload service unavailable — ensure upload-svc is running on :8120."*

**Copilot times out or says it's offline.**
- LLM routes allow up to 300 seconds. If no LLM API key is configured, the Copilot degrades to a limited/offline response by design — it won't crash.

**Enterprise (M7/M8/M9) tool buttons say "offline / unavailable".**
- Those `/api/v1/enterprise/*` endpoints are served by `dpe-svc` directly and are **not** in the Kong route table in the release2 profile. This is expected in a Kong-only deployment; the data itself is scaffold/mock (see Section 8).

**How do I switch language / try Arabic (RTL)?**
- Use the language switcher in the sidebar header. The layout supports RTL. Arabic strings are engineering-level; native QA (**G-R2-04**) is not yet signed off, so treat Arabic copy as provisional.

---

## 8. Honest limitations — what's mock or stubbed

These capabilities are **engineering-complete** but do **not** yet operate on live data. They are clearly flagged in the product responses so you're never misled.

| Area | Status | Why |
|------|--------|-----|
| **Live Odoo staging (PH1-02)** | **OPEN** | No customer Odoo staging connected yet. Odoo Config lets you create/test connections, but production sync against a real Odoo is pending. |
| **Odoo Accounting integration (A11/A15)** | **SCAFFOLD / MOCK** (`is_live=false`) | Depends on PH1-02. Finance figures use seeded/supplied data. |
| **Odoo PO / invoice write-back (A15)** | **NOT executed (mock)** | 3-way match & receipts compute correctly but are not written back to Odoo yet. |
| **Market data / FX feed (A14 Analytics)** | **NOT WIRED** | Analytics run on supplied/seeded history only — no external market/FX source. |
| **IoT / machine telemetry (A16, Digital Gemba)** | **STUB** (`iot_live=false`) | No live MQTT/REST from machines. Gemba/OEE inputs are supplied, not sensed. |
| **Andon persistence** | **In-memory** | Andon trigger→resolve lifecycle works, but state resets on service restart (DB persistence is Wave 2). |
| **S&OP interactive stage-gate** | **Deferred** | S&OP Deep computes the analysis; interactive stage-gate governance UI is future work. |
| **Operator tablet UI / monetary net-saving rollup** | **Deferred** | Wave 2. |
| **Collaborative multi-user conflict UI** | **Deferred** | Residual from Phase 5. |
| **WhatsApp / Comms Hub** | **Deferred** | Residual from Phase 5. |
| **Tariff matrix upload** | **No HTTP upload** | Parser exists in code; inputs are seeded/coded, not uploaded via UI. |
| **`/api/v1/enterprise/*` via Kong** | **Not routed in release2** | Served directly by `dpe-svc`; may read offline in Kong-only setups. |
| **Deep Planning "Deep" tabs** | **Analyst workbench (raw JSON)** | The three Deep tabs + Operations Deep run tools and show structured JSON, not polished dashboards. |
| **Arabic native QA (G-R2-04)** | **OPEN** | Arabic/RTL is present but not certified by a native reviewer. |
| **Several dashboards** | **Offline-shell fallback** | Horizons, Cockpit, Ops Live show representative demo data (with an amber banner) when their API is unavailable — never silently faked. |

Commercial gates that remain **OPEN** and must be closed by a human (not the product): OQ-7 pricing, PH1-02 Odoo staging, G-R2-04 Arabic sign-off.

---

## 9. Quick reference — routes & agents

### 9.1 All frontend routes

| Route | Screen |
|-------|--------|
| `/login` | Login |
| `/workspace` | Unified Workspace (home) |
| `/planning/dashboard` | Planning dashboard |
| `/planning/cockpit` | Planning Cockpit |
| `/planning/horizons` | Three Horizons |
| `/planning/demand` | Demand forecast |
| `/planning/scenarios` | Scenario Workbench |
| `/planning/control-tower` | Control Tower |
| `/planning/resolution` | Resolution Center |
| `/planning/schedule` | Schedule (Gantt) |
| `/planning/predictions` | Predictive risk view |
| `/planning/root-cause` (`/:moId`) | Root-cause explorer |
| `/command-center/dashboard` | Command dashboard |
| `/command-center/ops-live` | Ops Live |
| `/command-center/war-room` | War Room |
| `/command-center/executive` | Executive dashboard |
| `/command-center/outcomes` | Outcomes |
| `/command-center/equipment` | Equipment health |
| `/command-center/cost-of-chaos` | Cost of Chaos |
| `/command-center/otd-analytics` | OTD Analytics |
| `/command-center/sop-report` | S&OP report |
| `/command-center/operations-deep` | Operations Deep workbench |
| `/intelligence/pulse` | Today's Pulse |
| `/intelligence/demand` … `/customer` | M1–M6 module shells |
| `/intelligence/analytics` | M7 Analytics (A14) |
| `/intelligence/commercial` | M8 Commercial (A13) + A17 |
| `/intelligence/procurement` | M9 Procurement + Shop Floor (A15/A16) |
| `/intelligence/sop-deep` | S&OP Deep workbench |
| `/intelligence/demand-deep` | Demand Deep workbench |
| `/intelligence/production-deep` | Production Deep workbench |
| `/customer-portal` | Customer Portal (read-only) |
| `/supply-chain/supply-planning` | Supply planning |
| `/supply-chain/orders` | Order management |
| `/supply-chain/procurement` | Procurement |
| `/supply-chain/tariff` | Tariff shock |
| `/supply-chain/scn-portal` | SCN Portal |
| `/supply-chain/inventory` | Inventory |
| `/supply-chain/suppliers` | Supplier scorecards |
| `/ai-governance/copilot` | Copilot |
| `/ai-governance/meeting-prep` (`/:type`) | Meeting prep |
| `/ai-governance/design-ai` | Design AI |
| `/ai-governance/ai-trust` | AI Trust |
| `/ai-governance/mdr` | MDR |
| `/ai-governance/compliance` | Compliance |
| `/ai-governance/quality` | Quality |
| `/ai-governance/sustainability` | Sustainability |
| `/shop-floor` | Shop Floor |
| `/platform/admin` | Admin |
| `/platform/upload` | Data Upload Center |
| `/platform/agents` | Agent Dashboard |
| `/platform/exceptions` | Exception Manager |
| `/platform/odoo-config` (`/versions`) | Odoo connections / version config |
| `/platform/onboarding` | Onboarding wizard |
| `/platform/ml-ops` | ML Ops |
| `/platform/ops` | Ops dashboard |

### 9.2 Key API endpoints (via Kong `http://localhost:8000`)

| Purpose | Method + path | Kong-routed |
|---------|---------------|-------------|
| Login / refresh | `POST /api/v1/auth/login`, `/auth/refresh` | ✅ |
| Current user | `GET /api/v1/auth/me` | ✅ |
| Health | `GET /api/v1/health` | ✅ |
| Feasibility queue / KPIs | `GET /api/v1/feasibility/queue`, `/feasibility/kpis` | ✅ |
| Predictive / root cause | `GET /api/v1/feasibility/predict/{mo}`, `/feasibility/root-cause/{mo}` | ✅ |
| Resolution scenarios | `GET/POST /api/v1/resolution/scenarios` | ✅ |
| Capacity analyze / schedule | `POST /api/v1/capacity/analyze`, `/capacity/schedule` | ✅ |
| Project plan upload | `POST /api/v1/capacity/project-plans/upload` | ✅ |
| Copilot | `POST /api/v1/copilot/session`, `/copilot/query` | ✅ |
| Agents / exceptions | `POST /api/v1/agents/run-chain`, `GET /api/v1/agents/status`, `/api/v1/exceptions/*` | ✅ |
| Intelligence pulse / A8–A12 | `GET /api/v1/intelligence/pulse`, `POST /api/v1/intelligence/*` | ✅ |
| Planning Command (Cockpit/MPS/MRP/ATP/RCCP/Ops/Horizons/Deep) | `/api/v1/planning-command/*` | ✅ |
| Upload wizard | `GET /api/v1/upload/wizard/status`, `POST /api/v1/upload/{file_type}`, `/upload/wizard/complete-phase/{n}` | ✅ |
| Templates / error report | `GET /api/v1/upload/templates(/{type})`, `/upload/{id}/errors.xlsx` | ✅ |
| Odoo sync / ERP | `/api/v1/sync/*`, `/api/v1/erp/odoo/*` | ✅ |
| Dashboard / analytics | `/api/v1/dashboard/*`, `/api/v1/analytics` | ✅ |
| S&OP | `/api/v1/sop/*` | ✅ |
| Enterprise M7/M8/M9, A13–A17 | `/api/v1/enterprise/*` | ❌ direct `dpe-svc` |
| Customer portal | `GET /api/v1/orders/portal/summary` | served by `dpe-svc` |

### 9.3 Agents at a glance

See [Section 1.2](#12-the-17-agents-a1a17). Live status any time at **Platform → Agents** (`GET /api/v1/agents/status`).

### 9.4 Command modules at a glance

See [Section 1.3](#13-the-9-command-modules-m1m9). Navigate via the **Intelligence Hub** tabs.

---

*This guide is grounded entirely in the shipping codebase (`apps/web/src` routes/pages and `services/*` APIs) as of the current build. Where a capability is mock, stubbed, deferred, or not gateway-routed, it is stated plainly so planners are never misled. Live Odoo (PH1-02) and Arabic native QA (G-R2-04) remain OPEN.*
