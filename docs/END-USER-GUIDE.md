# IPE Platform — End User Guide

**Version:** 1.0.0  
**Last Updated:** June 2026

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Getting Started](#2-getting-started)
3. [Navigation Overview](#3-navigation-overview)
4. [Control Tower](#4-control-tower)
5. [Schedule](#5-schedule)
6. [Resolution Center](#6-resolution-center)
7. [Copilot (AI Assistant)](#7-copilot-ai-assistant)
8. [Shop Floor](#8-shop-floor)
9. [Executive Dashboard](#9-executive-dashboard)
10. [War Room](#10-war-room)
11. [AI Trust Dashboard](#11-ai-trust-dashboard)
12. [Supply Chain Network Portal](#12-supply-chain-network-portal)
13. [MLOps Dashboard](#13-mlops-dashboard)
14. [Onboarding Wizard](#14-onboarding-wizard)
15. [Common Workflows](#15-common-workflows)
16. [Troubleshooting](#16-troubleshooting)
17. [Glossary](#17-glossary)
18. [Index](#18-index)

---

## 1. Introduction

### What is IPE?

IPE (Intelligent Production Engine) is an AI-powered manufacturing operations platform that helps you:

- **Prioritize demand** using AI-driven scoring across customer value, urgency, margin, and strategic importance
- **Schedule production** with constraint-aware optimization (capacity, materials, labor)
- **Resolve disruptions** by generating and comparing resolution scenarios
- **Track quality** with statistical process control and defect prediction
- **Monitor sustainability** through carbon footprint and circularity scoring
- **Get AI assistance** via a natural language copilot that can query production data

### Who is this guide for?

This guide is for **planners, operators, managers, and executives** who use IPE daily to plan, schedule, monitor, and resolve manufacturing operations.

### Key Concepts

| Term | Definition |
|------|-----------|
| **MO** | Manufacturing Order — a work order to produce a specific product |
| **Feasibility Score** | AI-computed score (0–100) indicating how likely an MO can be completed on time |
| **Constraint** | A bottleneck or shortage preventing an MO from being feasible (Material, Capacity, Labor, Demand, BOM) |
| **Scenario** | A proposed resolution strategy for a constraint, with cost and delivery impact estimates |
| **Control Tower** | The main dashboard showing production health at a glance |
| **Shadow Mode** | AI makes recommendations but does not take automatic actions |

---

## 2. Getting Started

### Logging In

1. Open your browser and navigate to the IPE URL provided by your administrator (e.g., `http://localhost:8082`)
2. Enter your **email** and **password**
3. Click **Sign In**
4. You will be redirected to the **Control Tower** (home page)

### Session Management

- Your session expires after **60 minutes** of inactivity
- If your session expires, you will be redirected to the login page
- Click **Sign In** again to resume

### Understanding Your Role

Your role determines what you can see and do:

| Role | Can Do |
|------|--------|
| **Operator** | View shop floor, update own tasks |
| **Planner** | Full access to scheduling, resolution, demand management |
| **Manager** | All planner access plus S&OP and financial projections |
| **Executive** | View dashboards, KPIs, and analytics |
| **Admin** | Full system access including configuration and user management |

---

## 3. Navigation Overview

### Sidebar Menu

The sidebar on the left provides access to all main modules:

| Icon | Module | Description |
|------|--------|-------------|
| 🏠 | **Control Tower** | Production overview and live monitoring |
| 📅 | **Schedule** | Gantt chart and production schedule approval |
| 🔧 | **Resolution Center** | View and resolve production constraints |
| 🤖 | **Copilot** | AI assistant for natural language queries |
| 🏭 | **Shop Floor** | Offline-capable shop floor operations |
| ⚙️ | **Admin** | System configuration (admin only) |

### Top-Level Pages (via URL or sidebar links)

| Page | URL | Description |
|------|-----|-------------|
| Control Tower | `/control-tower` | Default home page |
| Executive Dashboard | `/executive` | High-level analytics and P&L |
| War Room | `/war-room` | Disruption aggregation and mitigation |
| AI Trust | `/ai-trust` | AI model transparency and adoption |
| SCN Portal | `/scn-portal` | Supplier management |
| MLOps | `/ml-ops` | ML model monitoring |
| Onboarding | `/onboarding` | New tenant setup wizard |

---

## 4. Control Tower

**Purpose:** Real-time production health overview. This is your home page and primary monitoring screen.

**URL:** `/control-tower` (default landing page)

### 4.1 KPI Cards

At the top of the page, four cards display key metrics:

| Card | Description | What it means |
|------|-------------|---------------|
| **Avg Feasibility Score** | Average feasibility score across all active MOs | Higher is better; green ≥80, yellow 60–79, red <60 |
| **Active Bottlenecks** | Number of work centers running above 85% utilization | More bottlenecks = more production risk |
| **Orders at Risk** | MOs with feasibility score below 70 | These orders need attention |
| **On-Time Delivery** | Percentage of MOs delivered on schedule | "Not available in Shadow Mode" when AI is not auto-scheduling |

### 4.2 MO Risk Queue

A table showing all manufacturing orders sorted by risk (lowest feasibility first):

| Column | Description |
|--------|-------------|
| **MO ID** | Manufacturing order identifier |
| **Product** | Product being manufactured |
| **Customer** | Customer who placed the order |
| **Required Date** | When the order is due |
| **Feasibility** | Color-coded badge: 🟢 Green ≥90, 🟡 Yellow 70–89, 🔴 Red <70 |
| **Constraint** | Icons indicating constraint type: M=Material, C=Capacity, L=Labor, D=Demand, B=BOM |
| **Resolve** | Button to open this MO in the Resolution Center |

**Actions:**
- Click **Resolve** on any row to jump to the Resolution Center with that MO pre-selected
- The table updates in **real-time** via WebSocket — you'll see new scores appear without refreshing

### 4.3 Bottleneck Map

Shows work centers running above capacity:

- **Red bar** (>95%): Critical — severely overloaded
- **Orange bar** (>85%): Warning — near capacity
- **Yellow bar** (>70%): Watch — approaching limit
- **Green bar** (≤70%): Healthy — within capacity

### 4.4 How to Use the Control Tower

**Daily monitoring workflow:**
1. Check the **KPI cards** for overall health
2. Scan the **MO Risk Queue** for red (critical) items
3. Click **Resolve** on any red/yellow MO to investigate
4. Check the **Bottleneck Map** to see which work centers are overloaded
5. The queue updates automatically — no manual refresh needed

---

## 5. Schedule

**Purpose:** Visualize the production schedule as a Gantt chart and approve AI-suggested schedules.

**URL:** `/schedule`

### 5.1 Gantt Chart

The main area shows a timeline-based view of all scheduled operations:

**Visual Elements:**
- **Blue bars**: Planned operations (current schedule)
- **Green overlay**: AI-suggested improvements
- **Gray bars**: Frozen operations (cannot be changed)
- **Red pulsing bars**: Disrupted operations (delayed or impacted)
- **Time axis**: Shows hours across the scheduling horizon

**Interactions:**
- **Hover** over a bar to see operation details (MO, work center, start/end time)
- **Click** a row to expand and see the "Disruption Cascade" — which downstream operations are affected
- **Status badges**: Impacted (red), Approved (green)

### 5.2 Approval Queue

A card at the top showing pending AI schedule suggestions:

- Displays the number of MOs with pending approvals
- Click **Approve All (N)** to accept all AI suggestions at once
- Once approved, the schedule can be synced to your ERP system

### 5.3 How to Use the Schedule

**Schedule approval workflow:**
1. Open the **Schedule** page
2. Review the Gantt chart — look for red (disrupted) and green (AI-suggested) bars
3. Click on individual rows to see disruption cascades
4. Review the **Approval Queue** card at the top
5. Click **Approve All** or approve individual MOs
6. After approval, the schedule is ready to sync to your ERP

---

## 6. Resolution Center

**Purpose:** View production constraints and compare AI-generated resolution scenarios.

**URL:** `/resolution` (alias: `/resolution-center`)

### 6.1 Left Panel — Unresolved MOs

A table listing MOs with active constraints:

| Column | Description |
|--------|-------------|
| **MO ID** | Manufacturing order identifier |
| **Feasibility** | Color-coded badge (same as Control Tower) |
| **Cause** | Primary constraint type (Material Shortage, Capacity Overload, etc.) |
| **Select** | Button to view scenarios for this MO |

**Constraint Detail Card (appears when you select an MO):**
- **Severity**: Critical / High / Medium / Low
- **Constraint Type**: Material / Capacity / Labor / BOM / Demand
- **Detail**: Description of the specific issue
- **Classified Cause**: AI-identified root cause with confidence percentage

### 6.2 Right Panel — Scenario Comparison

For the selected MO, you see resolution scenario cards:

| Field | Description |
|-------|-------------|
| **Strategy Name** | e.g., "Expedite Material", "Reroute to Backup WC", "Reschedule" |
| **Status Badge** | Approved (green) / Rejected (red) / Proposed (gray) |
| **Business Score** | AI-computed score (0–100) of how well this resolves the constraint |
| **Delivery Impact** | Days saved or lost (green = positive, red = negative) |
| **Cost Impact** | Dollar cost of this resolution |
| **Approve** | Button to approve and execute this scenario |
| **Reject** | Button to reject this scenario |

### 6.3 How to Resolve a Constraint

**Resolution workflow:**
1. Open the **Resolution Center**
2. Find the MO you want to resolve in the left panel
3. Click **Select** to view available scenarios
4. Review each scenario's **Business Score**, **Delivery Impact**, and **Cost Impact**
5. Choose the best scenario and click **Approve**
6. The resolution is executed and the MO status updates

---

## 7. Copilot (AI Assistant)

**Purpose:** Natural language interface for querying production data and getting AI-powered insights.

**URL:** `/copilot`

### 7.1 Chat Interface

- **Message input**: Type your question at the bottom
- **Send button**: Submit your query
- **Response area**: AI responses appear with:
  - **Intent badge**: Shows what the AI understood (e.g., "demand_query", "schedule_query", "disruption_analysis")
  - **Sources**: Data sources used to generate the response
  - **Streaming**: Text appears character by character as the AI generates it

### 7.2 Example Queries

| Query | What the AI does |
|-------|-----------------|
| "What is the status of MO-001?" | Queries the MO status and returns progress, constraints, and timeline |
| "Why is order 123 delayed?" | Classifies the delay cause and provides root cause analysis |
| "Show me capacity for WC-01" | Returns current utilization and available capacity |
| "What's the best resolution for the material shortage on MO-005?" | Generates and recommends resolution scenarios |
| "Simulate a 3-day supplier delay for Supplier X" | Runs a disruption simulation and shows impact |

### 7.3 Tool Calls

The Copilot can invoke backend tools to get real-time data. You'll see:
- A **spinner** while the tool executes
- The **tool name** (e.g., `get_order_status`, `simulate_disruption`)
- The **result** displayed inline

### 7.4 Streaming Responses

Responses stream in real-time via Server-Sent Events (SSE):
- Text appears word by word
- A blinking cursor (`|`) shows the response is still generating
- If the response is long, a heartbeat ping keeps the connection alive

---

## 8. Shop Floor

**Purpose:** Offline-capable interface for shop floor operators to view and update production tasks.

**URL:** `/shop-floor`

### 8.1 Status Indicators

At the top of the page:
- **Online/Offline badge**: Green when connected, red when offline
- **Pending sync counter**: Yellow badge showing how many changes are queued for sync

### 8.2 Barcode Scanner

- A text input field at the top
- Scan a barcode or type an MO/product ID
- Press **Enter** to look up the scanned item

### 8.3 Task Columns

**In Progress column:**
- Cards with green left border
- Shows: MO ID, Work Center, Operator name, Progress bar with percentage

**Pending column:**
- Cards with yellow left border
- Shows: MO ID, Work Center, Operator name

### 8.4 Offline Support

When you lose internet connection:
1. The status badge turns **red** (Offline)
2. Any updates you make are saved locally
3. A **pending sync counter** shows queued changes
4. When connection is restored, changes sync automatically
5. The counter returns to zero when all changes are synced

---

## 9. Executive Dashboard

**Purpose:** High-level analytics, P&L, and strategic planning views for managers and executives.

**URL:** `/executive`

### 9.1 KPI Cards

| Card | Description |
|------|-------------|
| **AI-Scheduled OTD %** | On-time delivery rate when AI manages scheduling |
| **Manual-Scheduled OTD %** | On-time delivery rate with manual scheduling |
| **Planning Cycle Time** | Average days from order to production start |
| **Inventory Investment** | Total value of inventory held |

### 9.2 Charts and Visualizations

- **AI vs Manual OTD Trend**: Line chart comparing AI and manual scheduling performance over 90 days
- **Delay Root Cause Coverage**: Progress bar showing what percentage of delays have been root-cause analyzed
- **Planner Productivity**: Cards showing time savings from AI automation

### 9.3 Detailed Tables

- **OTD by Work Center**: Table showing on-time delivery percentage per work center
- **Delay Root Cause Breakdown**: Pie chart and table of delay causes with percentages
- **Planning Accuracy**: Statistical measures of how accurate plans are vs actuals

### 9.4 Financial Views

- **P&L Statement**: Revenue, COGM, COPQ, Gross Margin, Net Margin with percentage breakdowns
- **S&OP Gap Analysis**: Demand vs capacity comparison with bottleneck identification
- **What-If Simulation**: Test different scenarios and see margin/OTD impact

---

## 10. War Room

**Purpose:** Aggregated view of all active disruptions with mitigation options.

**URL:** `/war-room`

### 10.1 KPI Cards

| Card | Description |
|------|-------------|
| **Active Disruptions** | Number of unresolved disruption events (red) |
| **Impacted MOs** | Total manufacturing orders affected |
| **Revenue at Risk** | Dollar value of revenue threatened by disruptions |
| **Mitigation Options** | Number of available resolution strategies |

### 10.2 Disruption Event Cards

Each disruption shows:
- **Type**: Supplier delay, port strike, machine breakdown, etc.
- **Status**: Active (red), Mitigating (yellow), Resolved (green)
- **Source**: Name and ID of the disrupted entity
- **Delay Days**: How many days of delay (red text)
- **Impacted MOs count**: Number of affected orders

**Expanded view** shows a table of impacted MOs with:
- MO ID
- Delay days
- Affected components
- Revenue at risk
- Severity badge

### 10.3 Mitigation Scenario Cards

Three columns showing available mitigation options:
- **Name**: e.g., "Switch to Backup Supplier", "Expedite Shipping"
- **Description**: What this mitigation does
- **Cost**: Dollar cost ($K)
- **OTD Impact**: Percentage improvement in on-time delivery
- **Delay Reduction**: Days saved
- **Confidence**: AI confidence in this mitigation
- **Assign Task**: Button to assign this mitigation to a team member

---

## 11. AI Trust Dashboard

**Purpose:** Transparent view of AI model performance, accuracy, and adoption metrics.

**URL:** `/ai-trust`

### 11.1 Trust Score Cards

Five cards showing trust dimensions:
- **Accuracy**: How often AI predictions are correct
- **Consistency**: How stable AI outputs are over time
- **Fairness**: Whether AI treats all scenarios equitably
- **Transparency**: How explainable AI decisions are
- **Reliability**: System uptime and availability

Each card shows: Score %, Trend arrow (up/down/stable), Delta % change

### 11.2 Composite Trust Score

A weighted average of all trust dimensions with a badge:
- **High** (≥80): AI is performing well
- **Good** (60–79): Acceptable performance
- **Needs Improvement** (<60): Attention required

### 11.3 Model Accuracy Table

| Column | Description |
|--------|-------------|
| **Model** | Name of the ML model |
| **Predictions** | Number of predictions made |
| **Accuracy %** | Correct predictions / total (color-coded) |
| **Confidence** | Average confidence score |
| **MAPE** | Mean Absolute Percentage Error |

### 11.4 AI vs Manual Impact

Side-by-side comparison showing how AI performs against manual processes:
- **OTD**: On-time delivery comparison
- **Cycle Time**: Planning cycle time comparison
- **Delta**: Improvement or regression amount

### 11.5 Override Nudge

When users frequently override AI recommendations:
- Shows current adoption percentage
- Warns that overriding AI reduces OTD by a specific percentage
- Encourages reviewing AI reasoning before overriding

---

## 12. Supply Chain Network Portal

**Purpose:** Monitor supplier performance and manage supply chain relationships.

**URL:** `/scn-portal`

### 12.1 KPI Cards

| Card | Description |
|------|-------------|
| **Total Suppliers** | Number of registered suppliers |
| **Active** | Currently active suppliers (green) |
| **Avg Score** | Average supplier performance score |
| **At Risk** | Suppliers with score below 70 (red) |

### 12.2 Supplier Table

| Column | Description |
|--------|-------------|
| **Name** | Supplier company name |
| **Tier** | Supply chain tier (1 = direct, 2 = sub-supplier, 3 = lower tier) |
| **Score** | Performance score: 🟢 Green ≥80, 🟡 Yellow ≥60, 🔴 Red <60 |
| **Lead Time** | Average delivery lead time in days |
| **Defect Rate** | Percentage of defective deliveries |
| **Status** | Active (green), Warning (yellow), Inactive (gray) |

---

## 13. MLOps Dashboard

**Purpose:** Monitor deployed ML models, their accuracy, and drift detection.

**URL:** `/ml-ops`

### 13.1 KPI Cards

| Card | Description |
|------|-------------|
| **Total Models** | Number of registered ML models |
| **Deployed** | Models currently in production (green) |
| **Avg Accuracy** | Average accuracy across all models |
| **Drift Alerts** | Models with PSI > 0.25 (red) — indicating data drift |

### 13.2 Models Table

| Column | Description |
|--------|-------------|
| **Model** | Model name |
| **Version** | Current version number |
| **Accuracy %** | Model accuracy (color-coded) |
| **Drift PSI** | Population Stability Index: 🔴 >0.25 (drift), 🟡 >0.1 (warning), 🟢 ≤0.1 (stable) |
| **Status** | Deployed (green), Staging (yellow), Retired (gray) |
| **Last Trained** | Date of last training run |

---

## 14. Onboarding Wizard

**Purpose:** Guided setup for new tenants to configure their IPE instance.

**URL:** `/onboarding`

### Step-by-Step Process

**Step 1 — Welcome**
- Introduction to IPE and what you'll configure

**Step 2 — Company Info**
- **Company Name**: Your company's name
- **Industry**: Select from Automotive, Electronics, Aerospace, Food & Beverage, Pharmaceuticals
- **Employee Count**: 1-50, 51-200, 201-1000, 1000+

**Step 3 — Choose Plan**

| Plan | Price | Features |
|------|-------|----------|
| **Basic** | $5K/mo | Core scheduling, demand management |
| **Professional** | $15K/mo | All Basic + AI copilot, advanced analytics |
| **Enterprise** | $50K/mo | All Professional + custom integrations, priority support |

**Step 4 — Admin Account**
- **Admin Email**: Primary administrator email
- **Admin Name**: Administrator's full name

**Step 5 — Integrations**
Connect to your ERP system:
- SAP (RFC/BAPI)
- Microsoft Dynamics 365 (OData)
- Odoo (JSON-RPC)
- **Skip for now** — configure later

**Step 6 — Complete**
- Confirmation screen with a button to go to the Control Tower

---

## 15. Common Workflows

### Workflow 1: Daily Production Review

**Goal:** Start your day by assessing production health

1. **Log in** to IPE → You land on the **Control Tower**
2. Check **KPI cards** — note any red indicators
3. Review the **MO Risk Queue** — focus on red (feasibility <70) items
4. Click **Resolve** on the highest-risk MO
5. In the **Resolution Center**, review the proposed scenarios
6. **Approve** the best scenario for each critical MO
7. Check the **Bottleneck Map** — if any work center is red, investigate capacity
8. Switch to the **Schedule** page to review the Gantt chart
9. **Approve** any pending AI schedule suggestions

### Workflow 2: Resolving a Material Shortage

**Goal:** Address a material constraint on a specific MO

1. From the **Control Tower**, find the MO with an "M" (Material) constraint icon
2. Click **Resolve** to open the **Resolution Center**
3. Review the constraint detail card — note the specific material shortage
4. Compare scenarios:
   - **Expedite Material**: Higher cost, faster delivery
   - **Reroute to Alternative**: Uses different materials, moderate cost
   - **Reschedule**: Delay the MO, lowest cost
5. Click **Approve** on your chosen scenario
6. The system executes the resolution and updates the MO status

### Workflow 3: Using the Copilot for Quick Insights

**Goal:** Get a quick answer without navigating dashboards

1. Click **Copilot** in the sidebar
2. Type a natural language question, such as:
   - "What's the status of all orders for Customer X?"
   - "Which work centers are overloaded this week?"
   - "What caused the delay on MO-123?"
3. Wait for the streaming response
4. Review the **intent badge** to confirm the AI understood your question
5. Check **sources** to see where the data came from

### Workflow 4: Approving a Schedule and Syncing to ERP

**Goal:** Finalize the production schedule and push to your ERP

1. Open the **Schedule** page
2. Review the **Gantt chart** for the coming week
3. Check the **Approval Queue** — see how many MOs need approval
4. Click **Approve All** (or approve individually)
5. The schedule is now finalized
6. To sync to ERP, the system automatically sends approved MOs via the Connector service

### Workflow 5: Responding to a Disruption

**Goal:** Handle a supply chain disruption

1. An alert appears on the **Control Tower** or **War Room**
2. Open the **War Room** page
3. Review the **disruption event card** — type, source, delay days
4. Check the **Impacted MOs** table — see which orders are affected
5. Review **Mitigation Scenario Cards** — compare cost, OTD impact, and confidence
6. Click **Assign Task** on the best mitigation option
7. The assigned team member receives notification and takes action

### Workflow 6: Shop Floor Updates (Offline)

**Goal:** Update production progress from the shop floor

1. Open the **Shop Floor** page on a tablet or mobile device
2. Check the **Online/Offline** indicator at the top
3. **Scan a barcode** or type the MO ID
4. Find the MO in the **In Progress** column
5. Update the progress percentage
6. If offline, changes are queued locally
7. When reconnected, changes sync automatically (check pending counter)

---

## 16. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Cannot reach this page" | Docker services not running | Ask admin to run `docker compose up -d` |
| 401 Unauthorized | Session expired | Log in again |
| "Not available in Shadow Mode" | AI auto-scheduling disabled | This is normal in Shadow Mode — AI makes recommendations but doesn't auto-apply |
| Feasibility score not updating | WebSocket disconnected | Refresh the page; check network connection |
| Copilot not responding | NLP service down or no API key | Contact admin to check NLP service health |
| Shop floor shows "Offline" | Network connection lost | Changes will sync when connection is restored |
| Empty dashboard | No seed data loaded | Ask admin to run seed data script |

### Health Check

If you suspect a service issue, your admin can check:
- Each service has a health endpoint at `/api/v1/health`
- Docker status: `docker ps` should show all services as "healthy"

---

## 17. Glossary

| Term | Definition |
|------|-----------|
| **ATP** | Available to Promise — inventory availability check |
| **BOM** | Bill of Materials — list of components needed to make a product |
| **CTP** | Capable to Promise — checks both material and capacity availability |
| **COPQ** | Cost of Poor Quality — total cost of defects, rework, scrap, warranty |
| **COGM** | Cost of Goods Manufactured — total production cost |
| **CP-SAT** | Constraint Programming SATisfiability solver (OR-Tools) |
| **DSAR** | Data Subject Access Request (GDPR) |
| **EOL** | End of Life |
| **Feasibility Score** | AI score (0–100) predicting if an MO can be completed on time |
| **Gantt Chart** | Timeline visualization of production schedule |
| **HMAC** | Hash-based Message Authentication Code — used for webhook verification |
| **JWT** | JSON Web Token — authentication token |
| **KMS** | Key Management Service — encryption key management |
| **MO** | Manufacturing Order |
| **OTD** | On-Time Delivery |
| **pATP** | Probabilistic ATP — Monte Carlo simulation of material availability |
| **PSI** | Population Stability Index — measures data drift in ML models |
| **RBAC** | Role-Based Access Control |
| **RLS** | Row-Level Security — database-level tenant isolation |
| **S&OP** | Sales and Operations Planning |
| **SCN** | Supply Chain Network |
| **SPC** | Statistical Process Control |
| **XAI** | Explainable AI — transparency in AI decision-making |

---

## 18. Index

| Topic | Section |
|-------|---------|
| Approving schedules | 5.3, 15.4 |
| Barcode scanning | 8.2 |
| Bottleneck Map | 4.3 |
| Copilot queries | 7.2 |
| Constraint resolution | 6.3, 15.2 |
| Control Tower overview | 4.1 |
| Daily review workflow | 15.1 |
| Disruption response | 15.5 |
| Executive analytics | 9 |
| Feasibility score meaning | 4.1 |
| GDPR DSAR | Admin Guide |
| Gantt chart | 5.1 |
| Login | 2.1 |
| MO Risk Queue | 4.2 |
| Offline mode | 8.4 |
| Onboarding | 14 |
| P&L Statement | 9.4 |
| Quality SPC | Admin Guide |
| Resolution scenarios | 6.2 |
| Role permissions | 2.4 |
| Schedule approval | 5.2, 15.4 |
| Session management | 2.2 |
| Shop Floor updates | 8, 15.6 |
| Sidebar navigation | 3 |
| Streaming responses | 7.4 |
| Supplier management | 12 |
| Sustainability | Admin Guide |
| Trust scores | 11.1 |
| War Room | 10 |
| WebSocket live updates | 4.2 |
| What-If simulation | 9.4 |
