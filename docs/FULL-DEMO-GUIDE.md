# IPE Full-Cycle Client Demo Guide

Complete end-to-end walkthrough for **Demo Manufacturing Inc** using pre-loaded sample data. A presenter can run this in **45–60 minutes**; a self-guided client can follow the numbered steps independently.

---

## Quick reference

| Item | Value |
|------|--------|
| **Web app** | http://localhost:8082 |
| **Login (admin)** | `Ahmed@nour` / `admin` |
| **Alternate login** | `admin@demo.com` / `demo` |
| **Tenant** | Demo Manufacturing Inc |
| **Demo MOs** | MO-DEMO-001 … MO-DEMO-010 |
| **Hero products** | Widget A, Gadget B, Assembly D |
| **Customers** | Acme Corp (Tier 1), Globex (Tier 2), Initech (Tier 3) |

---

## Part A — Prerequisites (do this once, ~10 minutes)

### Step A1 — Start the platform

Open **PowerShell** and run:

```powershell
cd d:\AISOP\ipe
.\scripts\start-product.ps1
```

Keep the terminal window open (it runs the web UI). Wait until you see:

```
Login: admin@demo.com / demo
```

**Checkpoint:** Browser opens or you can manually open http://localhost:8082/login — login page loads without errors.

### Step A2 — Load demo sample data

If the stack was already running, reload data in a **second** PowerShell window:

```powershell
cd d:\AISOP\ipe
.\scripts\seed-data.ps1
.\scripts\seed-demo-client.ps1
docker compose -f infrastructure\docker build dpe-svc mat-svc nlp-svc
docker compose -f infrastructure\docker up -d dpe-svc mat-svc nlp-svc
docker compose -f infrastructure\docker up -d --force-recreate kong
```

**Expected output (seed-demo-client.ps1):**

```
Client demo data loaded.
  - 10 MOs with feasibility scores (Control Tower queue)
  - 8 resolution scenarios (Resolution Center)
  - 8 delay events (Executive / War Room)
  - BOMs + routing (Schedule Gantt)
```

### Step A3 — Verify everything before the client arrives

```powershell
cd d:\AISOP\ipe
.\scripts\check-product.ps1
.\scripts\run-full-demo.ps1 -ReportPath docs\demo-run-report.txt
```

**Expected:** All checks show `[PASS]`. Report saved to `docs/demo-run-report.txt`.

**If any step fails:** See [Troubleshooting](#part-d--troubleshooting) at the end of this guide.

---

## Part B — End-to-end workflow (the full cycle)

This is the **story arc** the system demonstrates: demand → feasibility → resolution → schedule → execution → analytics → AI assistance.

```
Login → Control Tower → Resolution Center → Schedule → Shop Floor
   → SCN Portal → Executive → War Room → Copilot → AI Trust → Admin
```

Each UI module below has:
- **Presenter narrative** (what to say)
- **Numbered client steps** (exact clicks and inputs)
- **Expected output** (what should appear on screen)
- **Checkpoint** (how to confirm success)

---

## Module 1 — Login & landing

### Presenter narrative

Every user enters through a secure login tied to a manufacturing tenant. After sign-in, planners land on the Control Tower — the daily starting point for production health.

### Steps

1. Open http://localhost:8082/login
2. Enter email: `Ahmed@nour`
3. Enter password: `admin`
4. Click **Sign In**

### Expected output

- Redirect to **Control Tower** (`/control-tower`)
- Left sidebar shows all modules: Control Tower, Schedule, Resolution Center, Copilot, Executive, War Room, AI Trust, Shop Floor, SCN Portal, MLOps, Onboarding, Admin
- Header shows **Intelligent Planning Engine**

### Checkpoint

You are logged in and see KPI cards at the top of Control Tower (not a blank page).

---

## Module 2 — Control Tower (feasibility & risk)

**URL:** `/control-tower`  
**Sample data:** 10 manufacturing orders MO-DEMO-001 … MO-DEMO-010

### Presenter narrative

The Control Tower aggregates AI feasibility scores across every open manufacturing order. Planners instantly see which orders are at risk and what constraint — material, capacity, or labor — is driving the score. The platform runs in **shadow mode**, meaning AI recommends but humans approve.

### Steps

1. Click **Control Tower** in the left sidebar (if not already there)
2. Review the **KPI cards** at the top
3. Scroll to the **MO Risk Queue** table
4. Find these rows (sort by lowest score):

| MO ID | Product | Feasibility | Primary constraint | Status |
|-------|---------|-------------|-------------------|--------|
| **MO-DEMO-007** | Widget A | **~45%** | material_shortage | planned |
| **MO-DEMO-001** | Widget A | **~52%** | material_shortage | in_progress |
| **MO-DEMO-008** | Gadget B | **~62%** | capacity_overload | planned |
| **MO-DEMO-002** | Gadget B | **~68%** | capacity_overload | planned |

5. Click **Resolve** (or navigate manually) on **MO-DEMO-001**

### Expected output

- KPI area shows average feasibility near **75%** and at least **1 order at risk**
- Queue lists **10 rows** with MO-DEMO-* IDs
- Lowest scores appear in red/orange
- Bottleneck section references **Assembly Line 1** and **Machining Center**

### Checkpoint

You can name three at-risk orders and their constraint type without scrolling away from the page.

---

## Module 3 — Resolution Center (scenario comparison)

**URL:** `/resolution-center`  
**Sample data:** 8 scenarios on demo MOs

### Presenter narrative

When an order is constrained, the Resolution Center generates ranked scenarios — expedite a PO, split a batch, add overtime, or route to an alternate work center. Each scenario shows cost impact, delivery impact, and a business score so planners choose the best trade-off rather than accepting the first suggestion.

### Steps

1. Click **Resolution Center** in the sidebar
2. Select or filter to **MO-DEMO-001** (Widget A — material shortage)
3. Review the three proposed scenarios:

| Strategy | Description | Cost impact | Delivery impact | Score |
|----------|-------------|-------------|-----------------|-------|
| expedite_po | Expedite Component C PO from Parts R Us | $4,200 | +1 day | 0.82 |
| substitute_material | Use alternate supplier for Component C | $1,800 | +2 days | 0.74 |
| split_mo | Split MO into two batches | $950 | +3 days | 0.68 |

4. Switch to **MO-DEMO-002** (Gadget B — capacity)
5. Point out the **approved** scenario: *Route to backup CNC cell* (alternate_wc, $2,100)

### Expected output

- Scenario cards or table rows with strategy names, costs, and status badges (`proposed` / `approved`)
- MO-DEMO-001 shows **3 scenarios**
- MO-DEMO-002 shows at least one **approved** scenario

### Checkpoint

You can explain why expedite_po on MO-DEMO-001 costs more but recovers one day vs split_mo.

---

## Module 4 — Schedule (constraint-aware Gantt)

**URL:** `/schedule`  
**Sample data:** 6 routing operations, ~22 scheduled operations

### Presenter narrative

The schedule engine uses OR-Tools to place operations on work centers while respecting BOM routing, capacity hours, and due dates. Planners refresh the Gantt to see how at-risk orders fit alongside healthy ones across Assembly, Machining, and Packaging.

### Steps

1. Click **Schedule** in the sidebar
2. Click **Refresh** (or equivalent load button on the page)
3. Wait 5–15 seconds for the solver to return
4. Identify bars on these work centers:

| Work center | ERP ID | Sample operations |
|-------------|--------|-------------------|
| Assembly Line 1 | WC001 | Assemble Widget A, Build Assembly D |
| Machining Center | WC002 | Machine Widget Housing, Fabricate Gadget B |
| Packaging Station | WC003 | Pack Widget A, QC Gadget B |

### Expected output

- Gantt or timeline view populated (not empty)
- Multiple operations across **3 work centers**
- API returns ~**22 total operations** when schedule loads successfully

### Checkpoint

You can point to at least one Widget A operation and one Gadget B operation on different work centers.

---

## Module 5 — Shop Floor (execution)

**URL:** `/shop-floor`  
**Sample data:** 3 active work orders

### Presenter narrative

Shop Floor connects planning to execution. Supervisors see which operations are in progress right now, who is assigned, and progress percentage — bridging the plan in the Control Tower to reality on the line.

### Steps

1. Click **Shop Floor** in the sidebar
2. Review the work order cards/rows

### Expected output

| MO | Work center | Operator | Status | Progress |
|----|-------------|----------|--------|----------|
| MO-DEMO-001 | Assembly Line 1 | John Smith | in_progress | ~65% |
| MO-DEMO-005 | Machining Center | Jane Doe | in_progress | ~65% |
| MO-DEMO-005 | Packaging Station | Bob Wilson | pending | ~10% |

### Checkpoint

Three work orders visible; two show **in_progress**.

---

## Module 6 — SCN Portal (supplier collaboration)

**URL:** `/scn-portal`  
**Sample data:** 3 suppliers

### Presenter narrative

Supply Chain Network (SCN) Portal gives procurement visibility into supplier reliability. Scorecards highlight who is performing and who needs attention before a material shortage becomes a line stoppage.

### Steps

1. Click **SCN Portal** in the sidebar
2. Review supplier cards

### Expected output

| Supplier | Score | Lead time | Status |
|----------|-------|-----------|--------|
| Parts R Us | **95%** | 1.5 days | active (Tier 1) |
| Global Materials Ltd | **88%** | 3.2 days | active (Tier 2) |
| QuickShip Logistics | **75%** | 5.0 days | **warning** (Tier 2) |

### Checkpoint

QuickShip Logistics shows a warning status — tie this back to MO-DEMO-001 material constraint.

---

## Module 7 — Executive Dashboard (leadership KPIs)

**URL:** `/executive`  
**Sample data:** Completed MOs MO-DEMO-009/010, 8 delay events

### Presenter narrative

Executives need trend lines, not transaction detail. This dashboard summarizes on-time delivery, delay causes, and planning accuracy so leadership can see whether the operation is improving week over week.

### Steps

1. Click **Executive** in the sidebar
2. Review **OTD trend** chart (2 data points from completed demo MOs)
3. Review **Delay breakdown** by category
4. Review **Planning accuracy** metrics

### Expected output

- Delay categories include: **material**, **capacity**, **labor**, **supplier**, **quality**
- OTD trend shows history from **MO-DEMO-009** and **MO-DEMO-010** (completed orders)
- Charts render without "no data" placeholders

### Checkpoint

You can state the top delay cause category shown on the chart.

---

## Module 8 — War Room (disruption response)

**URL:** `/war-room`  
**Sample data:** 8 delay events + resolution scenarios

### Presenter narrative

War Room is the incident command view for active disruptions. Operations leaders see aggregated delays, linked manufacturing orders, and mitigation options pulled from the Resolution Center — designed for fast cross-functional response.

### Steps

1. Click **War Room** in the sidebar
2. Review the disruption/event list
3. Cross-reference **MO-DEMO-001** (Component C PO delayed 2 days — material, 2880 min)
4. Review mitigation scenarios linked from resolution data

### Expected output

- List of disruption events with cause categories
- Material delay on MO-DEMO-001 visible
- Mitigation/scenario references available

### Checkpoint

War Room shows at least **8** delay-related items or alerts.

---

## Module 9 — Copilot (natural language queries)

**URL:** `/copilot`  
**Sample data:** Live inventory, feasibility queue, delays

### Presenter narrative

Copilot lets planners ask questions in plain English and get answers grounded in live tenant data — inventory levels, at-risk orders, delays, and capacity. It removes the need to navigate multiple screens for ad-hoc questions during morning stand-ups.

### Steps

1. Click **Copilot** in the sidebar
2. Type exactly: `What is the current FG stock for Widget A and Gadget B?`
3. Click **Send**
4. Wait for the response (5–20 seconds)

### Expected output

- Intent badge: **material_status**
- Response lists finished goods with quantities, for example:
  - **Widget A (WGT-A-100):** ~497 units available (~647 on hand, ~150 reserved)
  - **Gadget B (GDT-B-200):** ~462 units available (~615 on hand, ~153 reserved)

5. Ask a second question: `Which manufacturing orders are at risk this week?`

### Expected output (second query)

- Intent badge: **feasibility_check**
- Response lists MO-DEMO orders with scores below 70% (001, 007, 008, 002)

### Checkpoint

Both questions return **non-empty** assistant messages (not blank bubbles).

---

## Module 10 — AI Trust (transparency)

**URL:** `/ai-trust`

### Presenter narrative

Before granting autonomy, manufacturers need visibility into model accuracy and adoption. AI Trust surfaces how often planners accept AI recommendations versus overriding them — building the confidence required to move from shadow mode to assisted mode.

### Steps

1. Click **AI Trust** in the sidebar
2. Review trust scores, model accuracy, and impact sections

### Expected output

- Dashboard sections load (scores, accuracy, impact)
- Metrics derived from demo MO history (including MO-DEMO-010 with `auto_confirmed`)

### Checkpoint

Page loads without error banners; at least one metric card shows a numeric value.

---

## Module 11 — Admin (tenant configuration)

**URL:** `/admin`

### Presenter narrative

Administrators control tenant-level settings including autonomy mode. Demo Manufacturing Inc runs in **shadow mode** — AI scores and suggests, but every action requires human approval.

### Steps

1. Click **Admin** in the sidebar
2. Review tenant configuration

### Expected output

- **Autonomy mode:** `shadow`
- Tenant settings for Demo Manufacturing Inc visible

### Checkpoint

Autonomy mode displays as **shadow**.

---

## Module 12 — MLOps & Onboarding (optional, 5 min)

### MLOps (`/ml-ops`)

**Narrative:** MLOps tracks model performance and shadow-mode ROI — how much value AI recommendations would have delivered if fully automated.

**Steps:** Click **MLOps** → review model/shadow ROI panels.

### Onboarding (`/onboarding`)

**Narrative:** New tenants walk through ERP connection, master data validation, and go-live checks. Useful to show implementation path after the demo.

**Steps:** Click **Onboarding** → step through wizard screens (no data entry required for demo).

---

## Part C — Sample data reference

### Manufacturing orders (MO-DEMO-*)

| MO ID | Product | Qty | Feasibility | Constraint | Status |
|-------|---------|-----|-------------|------------|--------|
| MO-DEMO-001 | Widget A | 500 | 52% | material_shortage | in_progress |
| MO-DEMO-002 | Gadget B | 250 | 68% | capacity_overload | planned |
| MO-DEMO-003 | Assembly D | 120 | 74% | labor_shortage | planned |
| MO-DEMO-004 | Widget A | 300 | 81% | — | confirmed |
| MO-DEMO-005 | Gadget B | 180 | 88% | — | in_progress |
| MO-DEMO-006 | Assembly D | 90 | 91% | — | confirmed |
| MO-DEMO-007 | Widget A | 600 | 45% | material_shortage | planned |
| MO-DEMO-008 | Gadget B | 400 | 62% | capacity_overload | planned |
| MO-DEMO-009 | Widget A | 200 | 95% | — | completed |
| MO-DEMO-010 | Gadget B | 150 | 93% | — | completed |

### Products & BOMs

| ERP ID | Name | Ref | Type |
|--------|------|-----|------|
| PROD001 | Widget A | WGT-A-100 | manufactured (FG) |
| PROD002 | Gadget B | GDT-B-200 | manufactured (FG) |
| PROD003 | Component C | CMP-C-300 | purchased |
| PROD004 | Assembly D | ASM-D-400 | manufactured (FG) |
| PROD005 | Raw Material E | RAW-E-500 | purchased |

### Demand lines

| ID | Product | Customer | Qty | Linked MO |
|----|---------|----------|-----|-----------|
| DEM-DEMO-001 | Widget A | Acme Corp | 500 | MO-DEMO-001 |
| DEM-DEMO-002 | Gadget B | Globex | 250 | MO-DEMO-002 |
| DEM-DEMO-004 | Widget A | Acme Corp | 600 | MO-DEMO-007 |

---

## Part D — Troubleshooting

| Symptom | Fix |
|---------|-----|
| Login page won't load | Run `.\scripts\start-product.ps1`; ensure port 8082 is free |
| Empty Control Tower queue | `.\scripts\seed-demo-client.ps1` |
| Blank Copilot responses | Rebuild nlp-svc + mat-svc; hard-refresh browser (Ctrl+F5) |
| Shop Floor / SCN empty | `docker compose -f infrastructure\docker up -d --force-recreate kong` |
| Schedule blank after Refresh | Confirm MOs exist; re-run demo seed |
| API 401 errors | Log out and log in again; token may have expired |

**Full automated check:**

```powershell
.\scripts\run-full-demo.ps1 -ReportPath docs\demo-run-report.txt
```

---

## Part E — Presenter closing (2 minutes)

**Key messages to leave with the client:**

1. **End-to-end flow works:** demand classification → feasibility scoring → resolution scenarios → capacity scheduling → shop floor execution → executive analytics.
2. **Shadow mode by design:** AI scores and recommends; planners stay in control until trust is established (AI Trust dashboard tracks this).
3. **Copilot reduces swivel-chair:** natural-language access to inventory, risk queue, and delays without exporting to spreadsheets.
4. **Next steps:** connect live ERP (Odoo), enable Keycloak SSO, move from shadow → suggest → assisted autonomy per tenant policy.

---

## Appendix — Automated demo execution

To reproduce this entire verification without clicking through the UI:

```powershell
cd d:\AISOP\ipe
.\scripts\run-full-demo.ps1 -ReportPath docs\demo-run-report.txt
notepad docs\demo-run-report.txt
```

The report lists **14 API checkpoints** matching every primary UI module. Share `demo-run-report.txt` with the client as tangible proof the system passed end-to-end validation before the live session.

**Screenshot tip for presenters:** At each module checkpoint, press **Win+Shift+S** (Windows) to capture the screen state described in the Expected output sections above. Save captures to a `demo-screenshots/` folder for leave-behind materials.
