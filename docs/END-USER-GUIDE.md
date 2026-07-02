# IPE Platform — Comprehensive End User Guide

**Product:** Intelligent Planning Engine (IPE)  
**Version:** v7.0.0  
**Last updated:** June 2026  
**Audience:** Planners, supervisors, operators, managers, executives, auditors, and administrators

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Getting Access](#2-getting-access)
3. [User Interface Layout](#3-user-interface-layout)
4. [User Roles and Permissions](#4-user-roles-and-permissions)
5. [How IPE Works — The Planning Pipeline](#5-how-ipe-works--the-planning-pipeline)
6. [Module Reference](#6-module-reference)
7. [Role-Based Workflows](#7-role-based-workflows)
8. [Integrations](#8-integrations)
9. [Configuration and Autonomy Modes](#9-configuration-and-autonomy-modes)
10. [Advanced and Power-User Topics](#10-advanced-and-power-user-topics)
11. [Best Practices](#11-best-practices)
12. [Troubleshooting](#12-troubleshooting)
13. [Glossary](#13-glossary)
14. [Quick Reference Index](#14-quick-reference-index)

---

## 1. Product Overview

### 1.1 What is IPE?

IPE (Intelligent Planning Engine) is an AI-assisted manufacturing operations platform. It connects demand, materials, capacity, feasibility scoring, resolution planning, and shop-floor execution into one coordinated system.

IPE helps your organization:

- **Prioritize manufacturing orders (MOs)** using multi-factor scoring (customer value, margin, urgency, strategic importance)
- **Detect constraints early** — material shortages, capacity overloads, labor gaps, BOM issues
- **Generate resolution scenarios** with cost, delivery, and business impact estimates
- **Build optimized schedules** using constraint programming (Google OR-Tools)
- **Monitor disruptions** in a centralized War Room with mitigation options
- **Query production data in natural language** through the AI Copilot
- **Track trust, quality, sustainability, and compliance** metrics alongside operations

### 1.2 Core Capabilities at a Glance

| Capability | Primary modules | Who uses it most |
|------------|-----------------|------------------|
| Production health monitoring | Control Tower, War Room | Planners, supervisors |
| Constraint resolution | Resolution Center | Planners, managers |
| Schedule planning & approval | Schedule | Planners, managers |
| Shop-floor execution | Shop Floor | Operators, supervisors |
| Executive analytics | Executive, Cost of Chaos | Managers, executives |
| Supply chain visibility | SCN Portal, Tariff | Supply chain managers |
| AI assistance | Copilot, AI Trust | Planners, all roles (read) |
| Governance | Admin, MDR, Compliance | Administrators, auditors |
| Quality & sustainability | Quality, Sustainability | Quality engineers, ESG teams |

### 1.3 Key Concepts

| Term | Definition |
|------|------------|
| **MO (Manufacturing Order)** | A work order to produce a specific product quantity by a required date |
| **Feasibility Score** | AI score from 0–100 predicting whether an MO can complete on time |
| **Constraint** | A bottleneck blocking feasibility: Material (M), Capacity (C), Labor (L), Demand (D), BOM (B) |
| **Scenario** | A proposed resolution strategy with estimated cost and delivery impact |
| **Control Tower** | Default home dashboard — live production health |
| **Shadow Mode** | AI recommends actions but does not auto-apply them (default in demo) |
| **Suggest Mode** | AI proposes changes; planner must approve |
| **Autonomous Mode** | AI may auto-apply within configured guardrails |
| **MDR (Master Data Readiness)** | Composite data-quality gate before autonomous scheduling |
| **ATP** | Available to Promise — inventory availability check |
| **CPM** | Critical Path Method — identifies schedule-driving operations |

### 1.4 Demo Environment Reference

When using the bundled demo tenant **Demo Manufacturing Inc**:

| Item | Value |
|------|--------|
| Web application | http://localhost:8082 |
| API gateway | http://localhost:8000 |
| Primary login | `Ahmed@nour` / `admin` |
| Alternate login | `admin@demo.com` / `demo` |
| Demo MOs | MO-DEMO-001 through MO-DEMO-010 |
| Hero products | Widget A, Gadget B, Assembly D |
| Customers | Acme Corp, Globex, Initech |

Your production deployment will use URLs and credentials provided by your administrator.

---

## 2. Getting Access

### 2.1 Logging In

1. Open the IPE URL in a supported browser (Chrome, Edge, or Firefox recommended).
2. You arrive at the **Login** page (`/login`).
3. Enter your **email** and **password**.
4. Click **Sign In**.
5. On success, you are redirected to the **Planning Dashboard** (`/planning/dashboard`).

**UI elements on the login page:**

- Email field — your corporate email or assigned demo account
- Password field — masked input
- Sign In button — submits credentials to the authentication service

**Expected outcome:** The header shows your name or email; the sidebar lists all modules you are permitted to use.

### 2.2 Signing Out

1. Look at the top-right of the header bar (labeled **Intelligent Planning Engine**).
2. Click **Sign out**.
3. You return to the login page; your session token is cleared.

### 2.3 Session Behavior

- Sessions expire after approximately **60 minutes** of inactivity.
- If your session expires, API calls return **401 Unauthorized** and the app redirects you to login.
- Sign in again to continue; unsaved form changes may be lost.

### 2.4 Browser and Device Recommendations

| Use case | Recommendation |
|----------|----------------|
| Planning & analytics | Desktop or laptop, 1920×1080 or larger |
| Shop floor | Tablet; Shop Floor supports offline queue |
| Executive review | Desktop; Executive and War Room use charts |
| Copilot | Any device with keyboard; responses may take 5–15 seconds |

---

## 3. User Interface Layout

Every authenticated page shares the same shell:

```
┌─────────────────────────────────────────────────────────────┐
│  Header: "Intelligent Planning Engine"    [User] [Sign out] │
├──────────────┬──────────────────────────────────────────────┤
│   Sidebar    │  Main content area (module page)             │
│   (nav)      │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

### 3.1 Header Bar

- **Left:** Product title — *Intelligent Planning Engine*
- **Right:** Your display name (or email) and **Sign out** button

### 3.2 Sidebar Navigation

The left sidebar lists **six hubs**. Each hub opens a landing page with **tabs** for related modules. The active hub is highlighted in blue.

| Icon | Hub | Root URL | Tabs |
|------|-----|----------|------|
| 📊 | Planning Hub | `/planning` | Dashboard, Control Tower, Resolution, Schedule |
| 🎯 | Command Center | `/command-center` | Dashboard, War Room, Executive, Cost of Chaos |
| 🌐 | Supply Chain | `/supply-chain` | Tariff, SCN Portal, Inventory |
| 🤖 | AI & Governance | `/ai-governance` | Copilot, AI Trust, MDR, Compliance, Quality, Sustainability |
| 🏭 | Shop Floor | `/shop-floor` | (standalone — operator work orders) |
| ⚙️ | Platform | `/platform` | Admin, Onboarding, MLOps |

**Default after login:** `/planning/dashboard` (Planning team dashboard).

**Legacy bookmarks:** Old URLs such as `/control-tower`, `/copilot`, or `/executive` automatically redirect to the matching hub tab.

### 3.3 Hub Tab Navigation

Within a hub, use the horizontal tab bar below the hub title to switch modules without leaving the hub context. Example — **Planning Hub**:

| Tab | URL | Purpose |
|-----|-----|---------|
| Dashboard | `/planning/dashboard` | Planner KPI overview and quick links |
| Control Tower | `/planning/control-tower` | Feasibility queue and bottlenecks |
| Resolution | `/planning/resolution` | Constraint scenarios |
| Schedule | `/planning/schedule` | Gantt chart and approval |

**Command Center Dashboard** (`/command-center/dashboard`) serves executives with alerts, OTD, and cost-of-chaos summaries.

### 3.4 Legacy Module URLs (Redirects)

These former sidebar URLs still work via automatic redirect:

| Legacy URL | Redirects to |
|------------|--------------|
| `/control-tower` | `/planning/control-tower` |
| `/resolution`, `/resolution-center` | `/planning/resolution` |
| `/schedule` | `/planning/schedule` |
| `/war-room`, `/executive`, `/cost-of-chaos` | Matching Command Center tab |
| `/tariff`, `/scn-portal` | Matching Supply Chain tab |
| `/copilot`, `/ai-trust`, `/mdr`, etc. | Matching AI & Governance tab |
| `/admin`, `/onboarding`, `/ml-ops` | Matching Platform tab |

### 3.5 Common UI Patterns

| Element | Meaning |
|---------|---------|
| **Card** | White panel grouping related content |
| **Badge** | Small colored label (green = good, yellow = warning, red = critical) |
| **Spinner** | Data loading — wait before interacting |
| **Tab buttons** | Switch views within a page (e.g., Admin → Configuration / Data Quality / LLM) |
| **Primary button** | Main action (blue) — Approve, Save, Send |
| **Secondary button** | Alternate action — Cancel, Retry |

---

## 4. User Roles and Permissions

IPE uses **Role-Based Access Control (RBAC)**. Your role is assigned by an administrator and embedded in your login token. If you attempt an action your role cannot perform, the system returns **403 Forbidden**.

### 4.1 Role Definitions

| Role | Typical job title | Primary responsibility |
|------|-------------------|------------------------|
| **admin** | System / tenant administrator | Full configuration, user management, all operational actions |
| **planner** | Production planner | Scheduling, resolution, demand management, Copilot |
| **manager** | Operations manager | Approvals, solver runs, analytics, team oversight |
| **supervisor** | Line supervisor | View schedules, acknowledge disruptions, shop floor oversight |
| **executive** | Director / VP Operations | KPIs, War Room recovery options, read-only analytics |
| **auditor** | Compliance / internal audit | Read-only access, audit logs, KPIs, scenarios |
| **operator** | Shop floor operator | Own task updates, limited read access |

### 4.2 Permission Matrix

The table below summarizes what each role can do. “✓” = allowed; “—” = not allowed or read-only only.

| Action / Area | admin | planner | manager | supervisor | executive | auditor | operator |
|---------------|:-----:|:-------:|:-------:|:----------:|:---------:|:-------:|:--------:|
| View Control Tower & KPIs | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| View feasibility queue | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Run capacity schedule (solver) | ✓ | ✓ | ✓ | — | — | — | — |
| Approve schedule | ✓ | ✓ | ✓ | — | — | — | — |
| Approve resolution scenarios | ✓ | ✓ | ✓ | — | — | — | — |
| Use Copilot (query) | ✓ | ✓ | ✓ | ✓ | — | ✓ | — |
| View War Room disruptions | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| War Room recovery options | ✓ | ✓ | ✓ | — | ✓ | — | — |
| View Executive / Cost of Chaos | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| Shop Floor — view tasks | ✓ | ✓ | ✓ | ✓ | — | — | ✓ |
| Shop Floor — update own tasks | ✓ | — | — | ✓ | — | — | ✓ |
| Admin configuration | ✓ | — | — | — | — | — | — |
| View audit / compliance logs | ✓ | — | — | — | — | ✓ | — |
| Material write (ATP, netting) | ✓ | ✓ | — | — | — | — | — |
| Tariff shock simulation | ✓ | ✓ | ✓ | — | — | — | — |
| MDR dashboard | ✓ | ✓ | ✓ | — | — | — | — |

### 4.3 What Happens When Access Is Denied

- **401 Unauthorized:** Session expired — sign in again.
- **403 Forbidden:** Your role lacks permission — contact your administrator to request access or use an account with the appropriate role.

### 4.4 Autonomy Mode Interaction with Roles

Even with planner permissions, **Shadow Mode** (default) means:

- AI generates recommendations and scenarios
- **You** must explicitly approve schedules and resolutions
- OTD metrics may show “Not available in Shadow Mode” until autonomous scheduling is enabled

Only **admin** users can change autonomy mode in the Admin console.

---

## 5. How IPE Works — The Planning Pipeline

Understanding the end-to-end flow helps you know which module to open for each task.

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│ ERP / Demand│───▶│ Material ATP │───▶│  Capacity   │───▶│ Feasibility  │
│  (Orders)   │    │  (mat-svc)   │    │  Schedule   │    │   Scoring    │
└─────────────┘    └──────────────┘    │  (cap-svc)  │    │  (fea-svc)   │
                                         └─────────────┘    └──────┬───────┘
                                                                    │
                    ┌──────────────┐    ┌─────────────┐            ▼
                    │ Shop Floor   │◀───│  Approved   │◀─── Resolution
                    │  Execution   │    │  Schedule   │     Scenarios
                    └──────────────┘    └─────────────┘     (res-svc)
```

### 5.1 Stage-by-Stage Summary

| Stage | What happens | Where you see it |
|-------|--------------|------------------|
| 1. Demand intake | Customer orders and MOs enter the system | Control Tower queue |
| 2. Material check | Inventory ATP determines material feasibility | Constraint icon **M** |
| 3. Capacity schedule | OR-Tools assigns operations to work centers | Schedule Gantt |
| 4. Feasibility score | Dual-gate AI scoring (0–100) | Control Tower, KPI cards |
| 5. Resolution | AI proposes expedite, reroute, reschedule options | Resolution Center |
| 6. Approval | Planner approves scenario and/or schedule | Resolution Center, Schedule |
| 7. ERP sync | Approved plan exported to ERP (when connected) | Automatic via Connector |
| 8. Execution | Operators progress work on shop floor | Shop Floor |

### 5.2 Data Dependencies

- **Resolution scenarios** require a feasibility score and identified constraint — open Resolution Center from Control Tower for best results.
- **Schedule approval** requires MOs with feasibility above the planner threshold (typically ≥85% for approve guardrail in demo).
- **Copilot material queries** pull live data from mat-svc — ensure ERP/inventory sync is current for accurate answers.
- **MDR gate** must pass (composite score ≥ threshold) before autonomous scheduling is allowed.

---

## 6. Module Reference

Each section follows: **Purpose → When to use → How to access → UI walkthrough → Expected outcomes → Tips**

---

### 6.1 Control Tower

**Purpose:** Real-time production health overview — your daily starting point.

**URL:** `/planning/control-tower` (also reachable via Planning Hub → Control Tower tab; legacy `/control-tower` redirects here)

**When to use:** Start of shift, before production meetings, after disruptions.

#### KPI Cards (top row)

| Card | Meaning | Color guidance |
|------|---------|----------------|
| Avg Feasibility Score | Mean score across active MOs | Green ≥80, Yellow 60–79, Red <60 |
| Active Bottlenecks | Work centers above 85% utilization | Higher = more risk |
| Orders at Risk | MOs with feasibility below 70 | Requires immediate attention |
| On-Time Delivery | OTD percentage | May show “Not available in Shadow Mode” |

#### MO Risk Queue (main table)

| Column | Description |
|--------|-------------|
| MO ID | Manufacturing order identifier (e.g., MO-DEMO-001) |
| Product | Product name |
| Customer | Customer who placed the order |
| Required Date | Due date |
| Feasibility | Color badge: Green ≥90, Yellow 70–89, Red <70 |
| Constraint | Icons: M=Material, C=Capacity, L=Labor, D=Demand, B=BOM |
| Resolve | Button — opens Resolution Center for this MO |

**Live updates:** The queue refreshes via WebSocket when feasibility scores change — no manual refresh needed.

#### Bottleneck Map

Horizontal bars per work center:

- **Red (>95%):** Critical overload
- **Orange (>85%):** Warning
- **Yellow (>70%):** Watch
- **Green (≤70%):** Healthy

**Expected outcome:** You can identify the highest-risk MOs and overloaded work centers within seconds.

**Best practice:** Sort mentally by red feasibility first, then check bottleneck map for systemic capacity issues.

---

### 6.2 Schedule

**Purpose:** Visualize and approve the production schedule on a Gantt timeline.

**URL:** `/schedule`

**When to use:** After reviewing Control Tower; before releasing plan to shop floor or ERP.

**Roles required:** View — supervisor+; Approve — planner, admin, manager

#### Gantt Chart Elements

| Visual | Meaning |
|--------|---------|
| Blue bars | Planned operations |
| Green overlay | AI-suggested improvements |
| Gray bars | Frozen operations (cannot move) |
| Red pulsing bars | Disrupted / impacted operations |

**Interactions:**

- **Hover** a bar — see MO, work center, start/end time
- **Click** a row — expand disruption cascade (downstream impact)
- Status badges: **Impacted** (red), **Approved** (green)

#### Approval Queue (top card)

- Shows count of MOs pending approval
- **Approve All (N)** — accepts all pending AI suggestions
- Individual MO approval also available

**Expected outcome:** After approval, schedule persists in the system and is eligible for ERP export.

**Important:** Demo guardrail requires feasibility ≥85% for approve on certain MOs (MO-DEMO-005/006 in seed data).

#### V6 Advanced Features on Schedule Page

| Feature | What it does |
|---------|--------------|
| **Margin-aware priority** | Shows activity-based cost and margin scores for top MOs |
| **CPM cascade** | Critical path analysis — typically completes in under 2 seconds |
| **Disruption simulation** | Model machine breakdown impact on downstream ops |

---

### 6.3 Resolution Center

**Purpose:** Compare AI-generated resolution scenarios for constrained MOs.

**URL:** `/resolution-center` or `/resolution`

**When to use:** When an MO shows a constraint in Control Tower or Copilot identifies an at-risk order.

#### Left Panel — Unresolved MOs

| Column | Description |
|--------|-------------|
| MO ID | Order identifier |
| Feasibility | Color-coded score |
| Cause | Primary constraint (Material Shortage, Capacity Overload, etc.) |
| Select | Opens scenarios for this MO |

**Constraint Detail Card** (after selecting an MO):

- Severity: Critical / High / Medium / Low
- Constraint type and detailed description
- AI-classified root cause with confidence percentage

#### Right Panel — Scenario Comparison

Each scenario card shows:

| Field | Description |
|-------|-------------|
| Strategy Name | e.g., Expedite Material, Reroute, Reschedule |
| Status | Approved / Rejected / Proposed |
| Business Score | 0–100 — how well this resolves the constraint |
| Delivery Impact | Days saved (green) or lost (red) |
| Cost Impact | Estimated dollar cost |
| Approve / Reject | Action buttons |

**Workflow:**

1. Open Resolution Center
2. Select an MO from the left panel
3. Review scenario cards — compare score, cost, delivery
4. Click **Approve** on the best option
5. MO status updates; feasibility may improve on next queue refresh

**Expected outcome:** Approved scenario is recorded; resolution event may publish to Kafka for downstream services.

---

### 6.4 Copilot (AI Assistant)

**Purpose:** Ask production questions in plain language; receive data-driven answers.

**URL:** `/copilot`

**When to use:** Quick lookups, executive briefings, exploratory analysis without navigating multiple dashboards.

**Roles:** planner, admin, manager, supervisor, auditor

#### Chat Interface

| Element | Location | Action |
|---------|----------|--------|
| Message history | Center | Scrollable conversation |
| Text input | Bottom | Type your question |
| Send button | Bottom-right | Submit query |

**Response includes:**

- **Intent badge** — how the AI classified your question
- **Answer text** — synthesized from live system data
- **Sources** — which services contributed (e.g., `nlp-svc:material_status`)

#### Supported Intent Categories

| Intent | Example question | Data sources |
|--------|------------------|--------------|
| `material_status` | “What is our finished goods inventory?” | mat-svc inventory |
| `demand_query` | “Show customer orders due this week” | dpe-svc demands |
| `capacity_status` | “Which work centers are overloaded?” | cap-svc schedule |
| `delay_analysis` | “Why are orders late?” | dpe-svc alerts |
| `feasibility_check` | “Which MOs are at risk?” | fea-svc queue |
| `resolution_help` | “What scenarios exist for MO-DEMO-001?” | res-svc scenarios |
| `general` | “Hello” / general manufacturing questions | LLM with context |

#### Example Queries

```
What is our Widget A on-hand quantity?
Which orders are at risk this week?
Show me capacity utilization for Assembly Line 1
What resolution options exist for material shortages?
Summarize active alerts in the war room
```

**Expected outcome:** Response within 5–15 seconds with intent label and sourced data.

**Limitations:**

- Copilot **reads** data and explains — it does **not** modify live production records
- If LLM service is offline, you see: *“Copilot is offline or could not reach the API…”*
- Complex “what-if” simulations may require Resolution Center or Schedule tools

**Best practice:** Be specific — include MO IDs, product names, or date ranges for best results.

---

### 6.5 Shop Floor

**Purpose:** Operator-facing view of active and pending work orders.

**URL:** `/shop-floor`

**When to use:** On the production line; tablet-friendly.

#### Page Elements

| Element | Description |
|---------|-------------|
| Online/Offline badge | Green = connected; Red = offline mode |
| Pending sync counter | Yellow badge — queued changes awaiting upload |
| Barcode scanner input | Scan or type MO/product ID, press Enter |
| In Progress column | Green-bordered cards with progress bars |
| Pending column | Yellow-bordered cards awaiting start |

**Card contents:** MO ID, Work Center, Operator name, Progress percentage

#### Offline Behavior

1. Connection lost → badge turns **Offline**
2. Updates saved locally
3. Pending sync counter increments
4. On reconnect → automatic sync; counter returns to zero

**Roles:** Operators update own tasks; supervisors view all.

---

### 6.6 Executive Dashboard

**Purpose:** Strategic KPIs, OTD trends, delay analysis, and financial views.

**URL:** `/executive`

**When to use:** Weekly operations review, board reporting, S&OP meetings.

**Roles:** All can view; executives and managers primary audience.

#### KPI Cards

| Card | Description |
|------|-------------|
| AI-Scheduled OTD % | On-time delivery under AI scheduling |
| Manual-Scheduled OTD % | OTD under manual planning |
| Planning Cycle Time | Days from order to production start |
| Inventory Investment | Total inventory value |

#### Charts and Tables

- **AI vs Manual OTD Trend** — 90-day line chart
- **Delay Root Cause Coverage** — percentage of delays analyzed
- **OTD by Work Center** — tabular breakdown
- **Delay Root Cause Breakdown** — pie chart by category
- **P&L Statement** — Revenue, COGM, COPQ, margins
- **S&OP Gap Analysis** — demand vs capacity
- **What-If Simulation** — test scenario impact on margin/OTD

**Expected outcome:** Executive-ready view of planning effectiveness and financial exposure.

---

### 6.7 War Room

**Purpose:** Aggregated disruption view with mitigation options and recovery planning.

**URL:** `/war-room`

**When to use:** During supply chain events, machine breakdowns, supplier delays.

#### KPI Cards

| Card | Description |
|------|-------------|
| Active Disruptions | Count of unresolved events |
| Impacted MOs | Orders affected |
| Revenue at Risk | Dollar exposure |
| Mitigation Options | Available recovery strategies |

#### Disruption Event Cards

Each event shows:

- **Type** — supplier delay, port strike, machine breakdown, etc.
- **Status** — Active (red), Mitigating (yellow), Resolved (green)
- **Source** — Entity name and ID
- **Delay Days** — duration impact
- **Impacted MOs** — expandable table with severity

#### Mitigation Scenario Cards

Three-column comparison:

- Name and description
- Cost ($K)
- OTD impact (%)
- Delay reduction (days)
- Confidence score
- **Assign Task** — delegate to team member

**Roles:** View — planner, admin, manager, supervisor; Recovery options — includes executive.

---

### 6.8 Cost of Chaos

**Purpose:** Quantify financial impact of production disruptions over time.

**URL:** `/cost-of-chaos`

**When to use:** Justify investment in resilience; prioritize mitigation spending.

#### Page Elements

| Element | Description |
|---------|-------------|
| Period toggle | **7d** or **30d** view |
| Total chaos cost | Aggregate USD impact |
| Category breakdown | Pareto bar chart by disruption type |
| Top drivers | Ranked list with percentage contribution |
| Link to War Room | Navigate to active mitigations |

**Categories typically include:** Material delay, capacity loss, quality hold, supplier failure, logistics disruption.

**Expected outcome:** Clear dollar attribution of chaos cost by category for the selected period.

---

### 6.9 Tariff Resilience

**Purpose:** Simulate regional tariff increases and identify margin-erosion risk with substitute material drafts.

**URL:** `/tariff`

**When to use:** Trade policy changes, sourcing reviews, margin protection planning.

#### Tariff Shock Simulator

| Input | Description | Default (demo) |
|-------|-------------|----------------|
| Region | Target region code | Region_X |
| Tariff delta (%) | Percentage increase | 25 |
| Margin threshold (%) | Flag MOs below this margin | 15 |

Click **Run Shock Simulation**.

#### Results

| Output | Description |
|--------|-------------|
| Affected MOs | Orders whose margin falls below threshold |
| Margin impact table | Per-MO margin before/after |
| Substitute drafts | AI-proposed BOM substitutions to recover margin |

**Expected outcome (demo):** ~6 affected MOs, ~6 substitute drafts generated.

---

### 6.10 AI Trust Dashboard

**Purpose:** Transparency into AI model performance and adoption.

**URL:** `/ai-trust`

**When to use:** Governance reviews, AI adoption campaigns, override analysis.

#### Trust Dimensions

| Dimension | Measures |
|-----------|----------|
| Accuracy | Prediction correctness |
| Consistency | Output stability over time |
| Fairness | Equitable treatment across scenarios |
| Transparency | Explainability of decisions |
| Reliability | System availability |

**Composite score:** High (≥80), Good (60–79), Needs Improvement (<60)

#### Additional Sections

- **Model Accuracy Table** — per-model predictions, MAPE, confidence
- **AI vs Manual Impact** — OTD and cycle time comparison
- **Override Nudge** — warns when frequent AI overrides reduce OTD

---

### 6.11 SCN Portal (Supply Chain Network)

**Purpose:** Supplier performance scorecards and relationship monitoring.

**URL:** `/scn-portal`

#### KPI Cards

| Card | Description |
|------|-------------|
| Total Suppliers | Registered count |
| Active | Currently active suppliers |
| Avg Score | Mean performance score |
| At Risk | Suppliers scoring below 70 |

#### Supplier Table

| Column | Description |
|--------|-------------|
| Name | Supplier company |
| Tier | 1=direct, 2=sub, 3=lower tier |
| Score | Green ≥80, Yellow ≥60, Red <60 |
| Lead Time | Average delivery days |
| Defect Rate | Percentage defective |
| Status | Active / Warning / Inactive |

**Demo suppliers:** Global Materials Ltd (88%), Parts R Us (95%), QuickShip Logistics (75%)

---

### 6.12 MLOps Dashboard

**Purpose:** Monitor deployed ML models, accuracy, and data drift.

**URL:** `/ml-ops`

| Column | Description |
|--------|-------------|
| Model | Model name |
| Version | Current version |
| Accuracy % | Color-coded performance |
| Drift PSI | Population Stability Index — red if >0.25 |
| Status | Deployed / Staging / Retired |
| Last Trained | Training date |

**When to use:** ML engineering reviews; investigate feasibility score degradation.

---

### 6.13 Admin Console

**Purpose:** Tenant configuration, data quality monitoring, LLM provider health.

**URL:** `/admin`

**Roles:** **admin only**

#### Tab: Configuration

| Setting | Description |
|---------|-------------|
| Priority Weights | Sliders/inputs for demand scoring factors (customer tier, margin, urgency, etc.) |
| Feasibility Thresholds | Auto-confirm and planner approval thresholds (0–100) |
| Autonomy Mode | **shadow** / **suggest** / **autonomous** |
| Strategic Product IDs | Products receiving priority boost |

Click **Save Configuration** to apply.

#### Tab: Data Quality

| Metric | Threshold |
|--------|-----------|
| BOM Completeness | Good ≥80%, Review 60–79%, Critical <60% |
| Lead Time Accuracy | Same thresholds |
| Inventory Record Accuracy | Same thresholds |

#### Tab: LLM Tiers

- Active provider (e.g., openrouter, anthropic)
- Routing enabled/disabled
- Per-provider health badges

---

### 6.14 Master Data Readiness (MDR)

**Purpose:** Composite data-quality gate controlling whether AI autonomous scheduling is permitted.

**URL:** `/mdr`

#### Key Metrics

| Metric | Description |
|--------|-------------|
| Composite Score | Weighted average across dimensions |
| Gate Threshold | Minimum score required (typically 70%) |
| Scheduling Allowed | Badge — pass/fail |

#### Dimensions (weighted)

| Dimension | Typical weight |
|-----------|----------------|
| BOM completeness | 35% |
| Lead time accuracy | 25% |
| Routing accuracy | 20% |
| Inventory accuracy | 20% |

**Recommendations list:** Action items to improve score below gate.

**Dependency:** Autonomous mode in Admin should not be enabled until MDR gate passes.

---

### 6.15 Quality Dashboard

**URL:** `/quality`

**Purpose:** Statistical process control and defect prediction.

#### Tabs

| Tab | Content |
|-----|---------|
| SPC (X-bar) | Control chart with UCL/LCL, out-of-control points, process sigma |
| P-Chart | Defect proportion over time |
| Defect Prediction | Risk level (low/medium/high), contributing factors |

**When to use:** Quality holds affecting schedule; root-cause analysis for delay category “quality.”

---

### 6.16 Sustainability Dashboard

**URL:** `/sustainability`

**Purpose:** Circularity scoring, end-of-life planning, recyclability analysis.

#### Tabs

| Tab | Content |
|-----|---------|
| Circularity | Score /100, material recovery %, take-back eligibility |
| EOL Plan | Product lifecycle phases (Active Sale → End of Life) |
| Recyclability | Per-component recyclable flag and grade |

---

### 6.17 Compliance Dashboard

**URL:** `/compliance`

**Purpose:** Audit trail visibility and compliance KPIs.

**Roles:** admin, auditor (primary)

#### Contents

- Compliance KPI cards (audit coverage, policy adherence)
- **Audit Log Table** — timestamp, actor, action, entity, rationale
- Common actions: `APPROVE_SCHEDULE`, `RUN_SCENARIO`, `COPILOT_CHAT`, `COST_OPTIMIZE`

**When to use:** Regulatory audits, internal controls verification, post-incident review.

---

### 6.18 Onboarding Wizard

**URL:** `/onboarding`

**Purpose:** Guided setup for new tenants (typically run once by admin).

| Step | Content |
|------|---------|
| 1. Welcome | Introduction |
| 2. Company Info | Name, industry, employee count |
| 3. Choose Plan | Basic / Professional / Enterprise |
| 4. Admin Account | Primary admin email and name |
| 5. Integrations | SAP, D365, Odoo, or Skip |
| 6. Complete | Confirmation → Control Tower |

---

## 7. Role-Based Workflows

### 7.1 Planner — Daily Production Review (15–30 min)

**Goal:** Ensure no critical MO is unaddressed before shift start.

1. Sign in → **Control Tower**
2. Review KPI cards — note red/yellow indicators
3. Scan **MO Risk Queue** — sort by lowest feasibility
4. For each red MO (<70): click **Resolve**
5. In **Resolution Center**: compare scenarios → **Approve** best option
6. Open **Schedule** — review Gantt for conflicts
7. **Approve** pending schedule suggestions
8. Optional: ask Copilot *“Summarize orders at risk today”*

**Success criteria:** No unreviewed red MOs; schedule approved for release.

---

### 7.2 Manager — Weekly Operations Meeting

**Goal:** Present performance and assign mitigation resources.

1. **Executive Dashboard** — capture OTD and delay breakdown
2. **Cost of Chaos** — 30-day view for financial narrative
3. **War Room** — review active disruptions; **Assign Task** on top mitigation
4. **AI Trust** — note adoption rate and override warnings
5. **SCN Portal** — flag at-risk suppliers for sourcing review

---

### 7.3 Supervisor — Shift Handoff

**Goal:** Align shop floor with approved plan.

1. **Control Tower** — note bottleneck work centers
2. **Schedule** — confirm approved operations for the shift
3. **Shop Floor** — verify In Progress and Pending columns match plan
4. Acknowledge disruptions in **War Room** if assigned

---

### 7.4 Operator — Task Execution

**Goal:** Progress assigned work orders accurately.

1. Open **Shop Floor** on tablet
2. Confirm **Online** status (or work offline if needed)
3. Scan barcode or enter MO ID
4. Update progress on assigned operation
5. Verify sync when back online

---

### 7.5 Executive — Monthly Business Review

**Goal:** Assess planning ROI and disruption exposure.

1. **Executive** — OTD trend, P&L, S&OP gap
2. **Cost of Chaos** — top 3 cost drivers
3. **War Room** — revenue at risk summary
4. **AI Trust** — composite trust score trend
5. Optional Copilot: *“What were the top delay causes this month?”*

---

### 7.6 Auditor — Compliance Review

**Goal:** Verify controls and traceability.

1. **Compliance** — export mental note of audit log entries
2. **Admin → Data Quality** — verify master data metrics
3. **Resolution Center** — spot-check approved scenarios have rationale
4. **MDR** — confirm gate status documented

**Note:** Auditors have read access; approval actions require planner/manager roles.

---

### 7.7 Administrator — Tenant Setup

**Goal:** Configure tenant for production use.

1. Complete **Onboarding Wizard** (or manual setup)
2. **Admin → Configuration** — set priority weights and thresholds
3. Set **Autonomy Mode** to **shadow** initially
4. Verify **MDR** gate status at `/mdr`
5. Configure ERP connector (see §8.1)
6. Configure LLM provider in Admin → LLM Tiers
7. Run demo verification script (ask IT) before go-live

---

## 8. Integrations

### 8.1 ERP Systems (Odoo, SAP, Microsoft D365)

**What it does:** Synchronizes demands, BOMs, inventory, and approved schedules between IPE and your ERP.

**User-visible effects:**

- MOs appear in Control Tower after ERP sync
- Approved schedules export back to ERP for execution
- Inventory in Copilot matches ERP when sync is healthy

**Odoo (supported in demo/test):**

- Connector service polls or receives webhooks from Odoo
- Uses HMAC-signed requests for security

**SAP / D365:**

- Adapter scaffolding exists; live connection requires enterprise credentials
- Configure during Onboarding Step 5 or contact administrator

**If ERP sync fails:**

- Schedule still persists in IPE (CDM path)
- Approve may show “ERP sync deferred” — planner should retry or contact admin
- Chaos scenario C3 validates this graceful degradation

### 8.2 AI / LLM (Copilot)

**What it does:** Powers natural-language Copilot responses.

**Providers (configured by admin):**

- **OpenRouter** (recommended for demo) — routes to models like Gemini, Claude, GPT
- **Anthropic Claude** — direct API
- **Ollama** — local/on-prem fallback

**User impact:** No configuration needed — if Copilot responds, integration is working.

### 8.3 Kafka Event Mesh (Background)

**What it does:** Services communicate asynchronously (demand classified, feasibility scored, resolution approved, etc.).

**User impact:** Generally invisible. If Kafka is paused:

- Core UI still works
- ERP export may defer until messaging restores

### 8.4 Identity (Keycloak / SSO)

**Production target:** Enterprise SSO via SAML/OAuth (Azure AD, Okta).

**Current demo:** Local email/password authentication.

**When SSO is enabled:** Login page redirects to corporate IdP; roles mapped from IdP groups.

---

## 9. Configuration and Autonomy Modes

### 9.1 Autonomy Modes (Admin)

| Mode | AI behavior | User responsibility |
|------|-------------|---------------------|
| **shadow** | Recommend only; never auto-apply | Approve all schedules and resolutions |
| **suggest** | Pre-fill approvals; highlight changes | Review and confirm each suggestion |
| **autonomous** | Auto-apply within guardrails | Monitor exceptions only |

**Default in demo:** `shadow`

### 9.2 Feasibility Thresholds

| Threshold | Typical use |
|-----------|-------------|
| Auto-confirm | MOs above this may skip manual review (autonomous mode) |
| Planner | MOs below this blocked from schedule approve |

Configure in **Admin → Configuration**.

### 9.3 Priority Weights

Adjust how demand scoring ranks MOs:

- Customer tier weight
- Margin weight
- Urgency / required date weight
- Strategic product boost

Changes affect queue ordering over time — save and monitor Control Tower after adjustment.

---

## 10. Advanced and Power-User Topics

### 10.1 Critical Path (CPM) Analysis

On **Schedule**, trigger CPM cascade after changing an operation date:

- Identifies critical path operations (typically 3 ops in demo)
- Completes in under 2 seconds
- Use when negotiating dates with customers — shows minimum feasible duration

### 10.2 Tariff Substitute Drafts

After running tariff shock:

- Review substitute drafts per affected MO
- Compare margin recovery vs material risk
- Coordinate with sourcing before applying BOM changes in ERP

### 10.3 Schedule Approve Guardrails

- MOs with feasibility <85% may be rejected at approve
- Improve feasibility via Resolution Center first
- Check MDR gate if autonomous scheduling blocked

### 10.4 Copilot Intent Debugging

If answer seems wrong:

1. Check **intent badge** — did AI classify correctly?
2. Rephrase with explicit MO ID or module name
3. Verify source services in **Sources** line
4. Admin: check **Admin → LLM Tiers** for provider health

### 10.5 WebSocket Live Updates

Control Tower queue updates live — if stale:

- Refresh page once
- Check network stability
- Persistent issue → report to admin (fea-svc WebSocket)

### 10.6 Multi-Tenant Isolation

Each user belongs to one tenant. You only see your organization's MOs, inventory, and suppliers. Cross-tenant data is never displayed.

---

## 11. Best Practices

### 11.1 General

- Start every day at **Control Tower**, not Schedule
- Resolve **material constraints before capacity** — material fixes often improve feasibility score
- Use **Copilot for questions**, **Resolution Center for actions**
- Approve schedules only after reviewing **disruption cascades** on red bars

### 11.2 Data Quality

- Monitor **Admin → Data Quality** weekly
- Do not enable **autonomous** mode until **MDR** gate passes
- Keep BOM and routing data current in ERP — IPE scores depend on it

### 11.3 AI Trust

- Read scenario **Business Score** and **confidence** before approving
- Minimize unnecessary AI overrides — AI Trust dashboard shows OTD impact
- Review **AI Trust** monthly with planning team

### 11.4 Disruption Response

- **War Room** for multi-MO events; **Resolution Center** for single-MO fixes
- Assign mitigation tasks with clear owners
- After resolution, verify **Cost of Chaos** category decreases in next period

---

## 12. Troubleshooting

### 12.1 Common Issues

| Symptom | Likely cause | What to do |
|---------|--------------|------------|
| Login page won't load | Web UI not running | Contact admin — run `npm run dev` in apps/web or deploy UI |
| 401 after working session | Session expired | Sign in again |
| 403 on Approve | Wrong role | Use planner/admin/manager account |
| Empty Control Tower | No seed data / wrong tenant | Admin runs seed scripts |
| Feasibility not updating | WebSocket disconnected | Refresh page; check network |
| Copilot offline message | nlp-svc down or no LLM key | Admin checks service health and OpenRouter/Anthropic config |
| Schedule approve fails | Feasibility below threshold | Resolve constraints first |
| “Not available in Shadow Mode” | Autonomy is shadow | Expected — enable suggest/autonomous only with admin approval |
| Shop Floor offline | Network loss | Continue working; sync when reconnected |
| ERP not updated after approve | Connector down or Kafka paused | Schedule saved in IPE; admin retries ERP sync |
| Tariff simulation error | API timeout | Retry; reduce scope; contact admin |
| Empty War Room | No active disruptions in data | Normal if no seeded delay events |

### 12.2 Health Checks (Administrator)

Each service exposes `GET /api/v1/health`. Gateway health: `http://localhost:8000/api/v1/health`

Quick product check script:

```powershell
cd E:\AISOP\ipe
.\scripts\check-product.ps1
```

Full regression (20 checkpoints):

```powershell
.\scripts\run-full-demo.ps1
```

### 12.3 Getting Help

| Issue type | Contact |
|------------|---------|
| Access / roles | Tenant administrator |
| ERP sync | Integration administrator |
| AI / Copilot | Platform administrator (LLM config) |
| Data discrepancies | Master data steward + admin |
| Compliance / audit | Auditor role user or compliance officer |

---

## 13. Glossary

| Term | Definition |
|------|------------|
| **ATP** | Available to Promise — can we fulfill from inventory? |
| **BOM** | Bill of Materials — components to make a product |
| **CDM** | Canonical Data Model — IPE’s internal persisted schedule format |
| **CP-SAT** | OR-Tools constraint programming solver |
| **CPM** | Critical Path Method |
| **CTP** | Capable to Promise — material + capacity check |
| **COPQ** | Cost of Poor Quality |
| **COGM** | Cost of Goods Manufactured |
| **DSAR** | Data Subject Access Request (GDPR) |
| **EOL** | End of Life (product phase) |
| **Gantt** | Timeline chart of scheduled operations |
| **HMAC** | Message authentication for secure webhooks |
| **JWT** | JSON Web Token — session credential |
| **Kafka** | Event streaming platform (background messaging) |
| **MDR** | Master Data Readiness |
| **MO** | Manufacturing Order |
| **OTD** | On-Time Delivery |
| **pATP** | Probabilistic ATP — statistical availability |
| **PSI** | Population Stability Index (ML drift) |
| **RBAC** | Role-Based Access Control |
| **RLS** | Row-Level Security — database tenant isolation |
| **S&OP** | Sales and Operations Planning |
| **SCN** | Supply Chain Network |
| **SPC** | Statistical Process Control |
| **SSE** | Server-Sent Events (streaming responses) |
| **XAI** | Explainable AI |

---

## 14. Quick Reference Index

| Topic | Section |
|-------|---------|
| Login / logout | §2.1, §2.2 |
| Role permissions | §4 |
| Control Tower KPIs | §6.1 |
| Schedule approval | §6.2, §7.1 |
| Resolution scenarios | §6.3 |
| Copilot queries | §6.4 |
| Shop Floor offline | §6.5 |
| Executive analytics | §6.6 |
| War Room | §6.7 |
| Cost of Chaos | §6.8 |
| Tariff simulation | §6.9 |
| AI Trust | §6.10 |
| Suppliers | §6.11 |
| MLOps | §6.12 |
| Admin config | §6.13 |
| MDR gate | §6.14 |
| Quality SPC | §6.15 |
| Sustainability | §6.16 |
| Compliance audit | §6.17 |
| Onboarding | §6.18 |
| ERP integration | §8.1 |
| Autonomy modes | §9.1 |
| Daily planner workflow | §7.1 |
| Troubleshooting | §12 |
| Glossary | §13 |

---

## Related Documentation

| Document | Audience | Content |
|----------|----------|---------|
| [FULL-DEMO-GUIDE.md](./FULL-DEMO-GUIDE.md) | Presenters | Step-by-step demo script with checkpoints |
| [ADMIN-GUIDE.md](./ADMIN-GUIDE.md) | Administrators | Installation, Docker, Kafka, security |
| [qa-e2e-readiness-report.md](./qa-e2e-readiness-report.md) | QA / release | Validation evidence |
| [api-reference.md](./api-reference.md) | Developers | API endpoints |

---

*This guide covers IPE v7.0.0 as validated in the demo environment. Production deployments may differ in URLs, SSO, and enabled modules — consult your administrator for environment-specific details.*
