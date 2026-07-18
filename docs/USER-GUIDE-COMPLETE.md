# IPE Platform — Complete End-User Guide (Authoritative)

**Product:** IPE — Intelligent Planning Engine  
**Document:** `USER-GUIDE-COMPLETE.md` — **the definitive exhaustive end-user guide**  
**Audience:** Planners, supervisors, managers, executives, admins, and trainers who need every screen, form field, validation, Excel/Odoo integration, and E2E workflow  
**Companions (lighter):** [`USER-GUIDE.md`](./USER-GUIDE.md) (overview) · [`USER-GUIDE-BY-SCREEN.md`](./USER-GUIDE-BY-SCREEN.md) (screen index; superseded in depth by this file)  
**Grounding:** `apps/web` router/`lazyRoutes`/`constants`; `locales/en.json`/`ar.json`; `services/upload-svc` validator + wizard; `services/connector` mapper/sync; `dpe-svc` phase5/phase7/phase8; `docs/integration/ODOO-19-FIELD-MAPPING.md`; `docs/project/FINAL-PROGRAM-STATUS.md`  
**Language:** English primary. Arabic/RTL via sidebar switcher; native Arabic QA (**G-R2-04**) is **OPEN**.  
**As of:** 2026-07-18 · Phase 8 Wave 1 (**8A**) ENG COMPLETE · Constitution 1.4.2

> **Honesty first:** IPE is an intelligence layer over ERP (Odoo), not a replacement. Live Odoo staging (**PH1-02**) is **OPEN**. Write-back is dry-run / mock-odoo only in Wave 1. Several screens are raw-JSON workbenches, offline shells, or stubs — each is flagged below. Do not invent polish that is not in the code.

---

## Table of contents

### Functional areas (by screen / workflow)

1. [Access & Login](#1-access--login)
2. [Data Onboarding / Upload Wizard](#2-data-onboarding--upload-wizard)
3. [Control Tower / Feasibility](#3-control-tower--feasibility)
4. [Resolution Center (+ role thresholds)](#4-resolution-center)
5. [Copilot (Ctrl+K)](#5-copilot-ctrlk)
6. [Planning Center](#6-planning-center)
7. [Command Center](#7-command-center)
8. [OTD Analytics](#8-otd-analytics)
9. [Intelligence Hub / M1–M9](#9-intelligence-hub--m1m9)
10. [Deep Planning Phase 7](#10-deep-planning-phase-7)
11. [Odoo Config / ERP Connections / Write-back](#11-odoo-config--erp-connections)
12. [Customer Portal](#12-customer-portal)
13. [Shop Floor / A16](#13-shop-floor--a16)
14. [Platform / Admin](#14-platform--admin)
15. [Daily / Weekly / Monthly Routines](#15-daily--weekly--monthly-routines)

### Dedicated master chapters

18. [Excel Master Chapter](#18-excel-master-chapter)
19. [Odoo Master Chapter](#19-odoo-master-chapter)
20. [E2E Workflow Chapter](#20-e2e-workflow-chapter)

### Appendices

16. [Appendix — Stub / mock / deferred inventory](#16-appendix--stub--mock--deferred-inventory)
17. [Appendix — Full route index](#17-appendix--full-route-index)

### How to use each section

Every major area below follows this structure:

- **Main Process** — when to use it; warnings before you start  
- **Step-by-Step Instructions** — numbered steps with real menu paths and button labels  
- **Screens & Forms** — purpose, route, fields, actions  
- **Validations & Restrictions** — rules and error messages from code  
- **Integrations** — external systems and failure behaviour  
- **Component Interactions** — what must happen first; cross-effects

### Navigation map (sidebar)

| Sidebar label (EN) | Route | Notes |
|--------------------|-------|-------|
| Unified Workspace | `/workspace` | Default home (`/` redirects here) |
| Planning Hub | `/planning` | Detect → decide → schedule |
| Command Center | `/command-center` | Alerts, KPIs, disruption impact |
| Intelligence | `/intelligence` | Hidden in release1 constrained profile |
| Customer Portal | `/customer-portal` | Hidden in release1 |
| Copilot | `/ai-governance/copilot` | Shown as top-level nav **only** in release1 |
| Supply Chain | `/supply-chain` | Hidden in release1 |
| AI & Governance | `/ai-governance` | Hidden in release1 |
| Shop Floor | `/shop-floor` | Hidden in release1 |
| Platform | `/platform` | Always available |

Legacy bookmarks (`/control-tower`, `/war-room`, `/copilot`, `/admin`, …) redirect to the hub tabs above.

---

## 1. Access & Login

### Main Process

Users authenticate before any hub loads. The app boots `AuthProvider`, which calls `GET /api/v1/auth/info` to choose **local** email/password or **Keycloak SSO**. Protected routes use `ProtectedRoute`: no valid session → redirect to `/login`.

**Prerequisites / warnings**

- Stack must be up (`docker compose … release2.yml`). Web UI: **http://localhost:8082**. API gateway (Kong): **http://localhost:8000**.
- Demo users live in `cdm_user` after `.\scripts\seed-data.ps1`. Empty DB → login fails.
- Non-production backends accept passwords `demo` or `admin` for seeded users.
- `ProtectedRoute` checks **authentication only** — it does not hide hubs by role. Sensitive APIs still enforce RBAC server-side (401/403).

### Step-by-Step Instructions

1. Open **http://localhost:8082** — unauthenticated users land on `/login`.
2. **Local mode** (default): enter **Email** and **Password**, click **Sign In**.
3. On success the app calls `POST /api/v1/auth/login` then `GET /api/v1/auth/me`, stores JWT tokens in `localStorage`, and navigates to **`/planning/dashboard`**.
4. **SSO mode** (when auth info returns `mode=keycloak`): click **Sign in with SSO** → Keycloak → redirect to `/planning/dashboard`.
5. To leave: header **Sign out** → clears tokens → `/login`.
6. If an API returns 401, the client tries refresh; on failure it clears tokens and sends you to `/login`.

### Screens & Forms

#### Login — `/login`

| | |
|--|--|
| **Purpose** | Authenticate into IPE |
| **When** | First visit, session expiry, after Sign out |

**Fields (local mode)**

| Label (EN) | AR | Required | Format | Default / placeholder |
|------------|-----|----------|--------|------------------------|
| Email | البريد الإلكتروني | Yes (HTML5) | `type="email"` | Placeholder `admin@demo.com` (EN) / `Ahmed@nour` (AR) |
| Password | كلمة المرور | Yes (HTML5) | `type="password"` | Placeholder `Enter password` / `أدخل كلمة المرور` |

**Primary actions**

| Button | Effect |
|--------|--------|
| **Sign In** / **دخول** | Local login → Planning Dashboard |
| **Sign in with SSO** / **تسجيل الدخول عبر SSO** | Keycloak login (only when mode=keycloak) |

**Demo credentials**

| Email | Password | Role |
|-------|----------|------|
| `Ahmed@nour` | `admin` | Admin |
| `admin@demo.com` | `demo` | Admin |
| `planner@demo.com` | `demo` | Planner |

#### Protected chrome (all hubs)

| Element | Label | Effect |
|---------|-------|--------|
| App name | Intelligent Planning Engine | Header |
| User | `full_name` or `email` or `User` | Display only |
| **Sign out** | Clears session → `/login` | |

#### Unified Workspace — `/workspace`

| | |
|--|--|
| **Purpose** | Cross-tool home: KPIs, recent activity, pending actions |
| **API** | `GET /api/v1/dashboard/unified` |
| **Failure** | *"Failed to load unified dashboard"* / *"Unified dashboard unavailable"* |

### Validations & Restrictions

| Rule | Message / behaviour |
|------|---------------------|
| Empty email/password | Browser native required validation |
| Bad credentials | UI: **Invalid credentials. Try Ahmed@nour / admin** (i18n `auth.error`). Backend may return `Invalid credentials` — UI does not show that string verbatim. |
| Auth boot (local) | **"Loading…"** |
| Auth boot (keycloak) | **"Connecting to SSO…"** |
| `/auth/info` fails | Falls back to **local** mode |

### Integrations

| System | Role |
|--------|------|
| **dpe-svc** auth | login / refresh / logout / me / info |
| **Keycloak** | Optional SSO (PKCE S256) |
| **Kong** | All subsequent `/api/v1/*` calls; JWT + `X-Tenant-ID` from claim |
| **Ollama (Phase 8)** | Amber banner via `GET /api/v1/phase8/ai-status` when unreachable — core planning continues; narratives degrade to rule-based (`AiDegradedBanner`) |

**Failure:** Kong/dpe down → login fails or session cannot refresh → returned to `/login`. Ollama down → amber banner only (not a login block).

### Component Interactions

```
Login success → JWT in localStorage → Axios Authorization + X-Tenant-ID
             → first land: /planning/dashboard
             → sidebar hubs become usable
             → Copilot Ctrl+K available on every protected page
```

---

## 2. Data Onboarding / Upload Wizard

### Main Process

Three distinct onboarding paths exist — do not confuse them:

| Path | Where | Persists to CDM? |
|------|-------|------------------|
| **Data Upload Center** (5-phase wizard) | Platform → Data Upload | **Validates only** + in-memory wizard progress; does **not** seed CDM rows |
| **SQL seed / Star Trans seed** | `scripts/seed-data.ps1` | Yes |
| **Odoo sync** | Platform → Odoo Connections | Yes (when connected; PH1-02 live staging OPEN) |
| **Project plan Excel** | Planning → Schedule | Yes (cap-svc project plans) |
| **Tenant Onboarding Wizard** | Platform → Onboarding | **UI stub only** — no API |

**Warnings before you start**

- Upload Center requires **upload-svc** (Kong `/api/v1/upload`, service port 8120). If down: **"Upload service unavailable — ensure upload-svc is running on :8120"**.
- Phases are **locked** until the previous phase is completed — you cannot skip ahead.
- Completing phases **labels agents as active** in wizard state; it does not itself invoke live agent Kafka pipelines from upload-svc.
- QA templates under `docs/qa/upload-templates/` use CDM/seed column names that may differ from upload-svc required headers — match the **upload-svc** column lists below for the wizard.
- Tariff matrix has **no HTTP upload** (parser only).

### Step-by-Step Instructions — Upload Center

1. Open **Platform → Data Upload** (`/platform/upload`).
2. Read the five phase cards: status `in_progress` / `complete` / `locked`, `{files_uploaded}/{files} files`.
3. Choose **File type** from the dropdown (types from current wizard status, fallback `product_master`).
4. Use the file picker (accepts `.xlsx`, `.csv`, `.xlsm`). Upload starts **on file select** — there is no separate Upload button.
5. Read the result: e.g. `Accepted {accepted}/{total_rows} rows` and optional ` · {rejected} rejected`.
6. When a phase’s files are ready, click **Complete phase**.
7. Watch the footer: `Agents active: … · Pending: …`.
8. Repeat until Phase 5 completes: API message **"Phase 5 complete. All 14 files loaded. IPE agents are now active."**

### Step-by-Step Instructions — Project plan (Schedule)

1. Open **Planning → Schedule** (`/planning/schedule`).
2. Click **Upload Project Plan**.
3. Choose **Create new plan** or **Update existing plan (new version)**.
4. For update: select **Existing plan** from the list.
5. Choose an `.xlsx` file; optional **Notes**.
6. Click **Upload New Plan** or **Upload New Version**.
7. Activate a version with **Activate** when ready.
8. Switch view radio to **Uploaded project plan** to Gantt that plan.

### Screens & Forms

#### Data Upload Center — `/platform/upload`

| | |
|--|--|
| **Purpose** | 5-phase file onboarding with live validation |
| **Title** | Data Upload Center |
| **Subtitle** | 5-phase onboarding wizard with live validation |

**Phase definitions (backend)**

| Phase | Name | name_ar | File types |
|-------|------|---------|------------|
| 1 | Master Data | البيانات الأساسية | `product_master`, `customer_master`, `supplier_master`, `work_centre_master` |
| 2 | Product Structure | هيكل المنتجات | `bom`, `routing` |
| 3 | Planning Parameters | معاملات التخطيط | `capacity_calendar`, `lead_time`, `cost_data` |
| 4 | Current State | الحالة الحالية | `inventory`, `production_orders`, `sales_orders`, `purchase_orders` |
| 5 | Historical Data | البيانات التاريخية | `historical_otd` |

**Phase 8 Wave 1 operational types** (validated by upload-svc; **not** part of the 5-phase wizard lock sequence — use file-type dropdown / API with aliases `forecast`, `quality_inspection`, `sop_sales`):

| file_type | Required columns | Agents tagged |
|-----------|------------------|---------------|
| `demand_forecast` | product_code, period, forecast_qty | A1, A4 |
| `quality_results` | mo_number, inspection_date, result, measured_value | A10 |
| `sop_sales_input` | product_family, period, sales_forecast_qty | A1, A14 |

See [§18 Excel Master](#18-excel-master-chapter) for full column rules, templates, and CT/MPS CSV exports.

**Upload form**

| Control | Required | Notes |
|---------|----------|-------|
| **File type** `<select>` | Yes | Options from wizard status |
| File input | Yes (implicit) | `.xlsx,.csv,.xlsm`; fires on change |

**Actions:** **Complete phase** (only when phase `in_progress`).

**Required columns by file type**

| file_type | Required columns | Agents tagged |
|-----------|------------------|---------------|
| `product_master` | product_code, name, type, uom | A2, A4 |
| `customer_master` | customer_code, name | A1 |
| `supplier_master` | supplier_code, name | A2 |
| `work_centre_master` | work_centre_code, name | A3, A4 |
| `bom` | product_code, component_code, quantity | A4 |
| `routing` | product_code, operation_seq, work_centre_code | A3, A4 |
| `capacity_calendar` | work_centre_code, date, shift, available_hours | A3 |
| `lead_time` | product_code, supplier_code, lead_time_days | A2 |
| `cost_data` | product_code, unit_cost | A5, A6 |
| `inventory` | product_code, on_hand | A2, A4 |
| `production_orders` | mo_number, product_code, quantity, planned_start, planned_end, status | A3, A4 |
| `sales_orders` | order_number, customer_code, product_code, quantity, order_date, requested_delivery, status | A1, A4 |
| `purchase_orders` | po_number, supplier_code, product_code, quantity | A2 |
| `historical_otd` | mo_number, planned_end, actual_end | A6 |
| `demand_forecast` | product_code, period, forecast_qty | A1, A4 |
| `quality_results` | mo_number, inspection_date, result, measured_value | A10 |
| `sop_sales_input` | product_family, period, sales_forecast_qty | A1, A14 |

Aliases accepted: `products`→product_master, `customers`, `suppliers`, `work_centers`/`work_centres`, `mrp_orders`→production_orders, `demand_lines`→sales_orders, `supply_orders`→purchase_orders, `forecast`→demand_forecast, `quality_inspection`→quality_results, `sop_sales`→sop_sales_input.

#### Project Plan Upload (on Schedule) — `/planning/schedule`

| Field / control | Required | Notes |
|-----------------|----------|-------|
| Mode radios | Yes | Create new plan / Update existing plan (new version); default `new` |
| Existing plan | If update | Placeholder **Select plan...** |
| Excel file (.xlsx) | Yes | Max **5 MB**; preferred sheet **ProjectPlan** |
| Notes | Optional | Placeholder `e.g. Q3 rebalance after material delay` |

**Actions:** **Upload New Plan** / **Upload New Version** / **Uploading...**; **View Excel schema**; **Activate** / **Activating...**; toggle **Upload Project Plan** / **Hide Upload**.

#### Tenant Onboarding Wizard — `/platform/onboarding` ⚠️ UI stub

| Step | Title | Fields / content |
|------|-------|------------------|
| 0 Welcome | Welcome | Intro copy only |
| 1 Company Info | Company Name; Industry (automotive/electronics/aerospace/food/pharma); Employee Count (1-50 … 1000+) | **No validation** |
| 2 Choose Plan | Basic $5,000/mo · Professional $15,000/mo · Enterprise $50,000/mo | Demo pricing |
| 3 Admin Account | Admin Email; Admin Name | No validation |
| 4 Integrations | Odoo (Recommended) · SAP · Dynamics · Skip for now | **Continue** disabled until ERP selected |
| 5 All Set! | **Open Odoo setup →** → `/platform/admin` if Odoo; else **Go to Control Tower →** → `/planning` | |

**Nav:** **← Back** · **Continue →**. Entire wizard is **client state only** — does not create tenants or users.

### Validations & Restrictions (upload-svc)

**Four stages** in every upload response: `stage_1_structure`, `stage_2_types`, `stage_3_referential`, `stage_4_business`.

| Condition | Exact / near-exact message | Resolve by |
|-----------|----------------------------|------------|
| Bad extension / magic | **Invalid file format. Expected .xlsx or .csv** | Use `.xlsx`/`.csv`/`.xlsm` |
| Unknown type | **Unknown file_type: {file_type}** | Pick a known type / alias |
| Missing columns | **Missing columns: {col1, col2, …}** | Add required headers |
| Headers OK, 0 rows | **0 rows found. Nothing to import.** | Add data rows |
| Empty required cell | **{col} is required** | Fill cell |
| Non-numeric qty fields | **{qty_col} must be numeric** | Fix numbers (`quantity`, `on_hand`, `unit_cost`, `available_hours`, `lead_time_days`) |
| Negative qty/on_hand | **{qty_col} must be non-negative** | Use ≥ 0 |
| Duplicate product_code | **Duplicate product_code (first seen row {n})** | Deduplicate |
| BOM parent missing | **{parent} not found in Product Master.** | Upload product_master first (needs known_codes) |
| Customer FK | **Customer not found in master** | Upload customers first |
| Product FK | **Product not found in master** | Upload products first |
| Unknown priority | Warning: **Unknown priority. Defaulting to 'high'** | Use low/normal/high/urgent |
| Phase lock (API) | Complete Phase {n-1} first | Complete prior phase |
| Project plan no file | **Select an Excel (.xlsx) file first.** | Choose file |
| Project plan update no plan | **Select an existing plan to update.** | Select plan |
| Upload UI exception | `String(e)` from axios | Check Kong / upload-svc |

**Error workbook (API, not wired in UI):** `GET /api/v1/upload/{upload_id}/errors.xlsx` — columns `row`, `column`, `value`, `message`, `severity`. Templates: `GET /api/v1/upload/templates/{file_type}` (UI does not expose download buttons today).

### Integrations

| System | Direction | Trigger |
|--------|-----------|---------|
| **upload-svc** via Kong | Client → validate → response | File select / Complete phase |
| **Postgres** | upload-svc lifecycle only | Startup — **not** used for row import |
| **Kafka** | Not used by upload-svc | — |
| **cap-svc** | Project plan upload | Schedule upload |
| **SQL seed / Odoo** | Real master data | Outside wizard |

**Failure:** Upload Center shows amber unavailable message; Schedule upload shows API error + up to 8 `details[]`.

### Component Interactions

```
Phase complete → agents marked active in wizard store
Seed / Odoo sync → CDM populated → Control Tower queue / Schedule / Agents become useful
Project plan upload → Schedule view switches to "Uploaded project plan"
Upload Center ≠ CDM seed — empty Control Tower after wizard alone is expected without seed/Odoo
```

---

## 3. Control Tower / Feasibility

### Main Process

Morning triage for production risk (A4 Feasibility). Planners open this daily to work the MO risk queue, bottlenecks, and optional inline resolutions.

**Warnings**

- Empty DB → **"No manufacturing orders synced yet"** with hint to configure Odoo.
- Footnote: **"Capacity & Labor scoring pending — scores are material-driven only."**
- In shadow mode, OTD may show **"Not available in Shadow Mode"** rather than a fake 0%.
- **Reject** on inline scenarios has **no click handler** (UI only).

### Step-by-Step Instructions

1. Open **Planning Hub → Control Tower** (`/planning/control-tower`).
2. Read **Morning triage** hero: Orders at Risk, highest-risk MO, or **"All manufacturing orders look feasible right now."**
3. Check support metrics: **On-Time Delivery**, **Avg Feasibility Score**, **Active Bottlenecks**, **Sync**.
4. Scan **MO Risk Queue** (columns: MO ID, Product, Customer, Required, Feasibility, Constraint). Colour tiers: Excellent / Good / Review / Action today / Escalate; also **Cannot score**, **Odoo conflict**.
5. Review **Bottleneck Map** — work centres >85% utilisation (Critical overload / Bottleneck risk / Moderate load).
6. Optional: use **Planner Copilot Lite** suggestions or ask a question → **Ask**.
7. Optional: read **Demand vs Capacity** forecast overlay (14d).
8. Click **Resolve** on a row → expand **InlineResolutionPanel**; compare scenarios; click **Approve ★** on the recommended option.
9. Tariff teaser: **Full view →** opens Supply Chain Tariff.
10. Empty state: **Open Odoo Settings** → `/platform/odoo-config`.

### Screens & Forms

#### Control Tower — `/planning/control-tower`

| Widget | Purpose | Inputs |
|--------|---------|--------|
| HeroMetrics | At-risk hero + KPIs | Read-only |
| SyncStatusBar | Last sync (R1 profile) | Read-only; stale if >30 min |
| MO Risk Queue | Triage table | **Resolve** / **Collapse** |
| Bottleneck Map | WC utilisation | Read-only |
| PlannerAssistPanel | Structured Q&A | Query text + **Ask**; suggestions chips |
| ForecastOverlayWidget | 14-day demand vs capacity | Read-only (capacity baseline hardcoded 100) |
| InlineResolutionPanel | Approve scenario for one MO | **Approve ★** / **Reject** (Reject noop) |
| TariffShockPanel | Tariff teaser | **Full view →** |

### Validations & Restrictions

| Rule | Message |
|------|---------|
| Feasibility colour bands | ≥90 Excellent/Good path; 70–89 Review; &lt;70 Action/Escalate |
| Assist load fail | **Planner assist failed to load** / query error string |
| Forecast empty | **No forecast data. Run demand sense cycle.** |
| Forecast fail | **Forecast overlay unavailable** |
| Empty queue | **No manufacturing orders synced yet** |

### Integrations

| Call | Endpoint |
|------|----------|
| Queue | `GET /api/v1/feasibility/queue` |
| KPIs | `GET /api/v1/feasibility/kpis` |
| Bottlenecks | `POST /api/v1/capacity/analyze` (filter OEE/util &gt; 0.85) |
| Sync | `GET /api/v1/sync/status` |
| Assist | `POST /api/v1/planner-assist/query` |
| Forecast | `GET /api/v1/demand/forecast?days=14` |
| Scenarios | `GET /api/v1/resolution/scenarios?mo_id=` |
| Approve | `POST /api/v1/resolution/scenarios/{id}/approve` or `/resolution/approve` |
| Live updates | WebSocket feasibility feed (patches queue by `mo_id`) |

**Failure:** Soft-empty lists; empty guided state — not fake MOs.

### Component Interactions

```
Control Tower Resolve → same Resolution APIs as Resolution Center
Demand Sensing (Planning → Demand) → feeds Forecast overlay
Odoo sync → populates queue
Approve → reloads queue/KPIs
Dashboard "Orders at risk" → deep-links here
```

---

## 4. Resolution Center

### Main Process

Full-page compare-and-approve trade-offs for unresolved MOs (A5 Resolution). Use when Control Tower inline resolve is not enough, or when working a batch of at-risk orders.

**Warnings**

- **Reject** button has **no API handler**.
- Constraints list is often empty (payload may not hydrate constraints).
- Financial projection uses fixed `selling_price: 500` and qty from queue or **100**.
- **Phase 8 role thresholds** (`ipe_shared.roles.AgentRoleContext`) gate write-back / approve authority by financial impact — see table below. Copilot **Agent role** select (Planner / Manager / Supervisor / Executive) maps onto these agent roles via aliases (`planner`→supervisor, `admin`/`executive`→manager).

### Step-by-Step Instructions

1. Open **Planning Hub → Resolution** (`/planning/resolution`).
2. In **Unresolved MOs**, click **Select** on a row (columns: MO ID, Feasibility, Cause).
3. Review constraints / Classified Cause / Confidence if present.
4. Read financial strip: **COGM (baseline)**, **Revenue at risk**, **Margin**.
5. Compare scenario cards: strategy, status, **Scenario cost**, **OTD**, **Delay**; **★ Recommended** = highest `business_score`.
6. Click **Approve** on the chosen scenario (disabled if already approved or acting).
7. Empty success: **"All manufacturing orders are feasible"** / *Nothing requires immediate action.*

### Screens & Forms

#### Resolution Center — `/planning/resolution`

| Panel | Contents |
|-------|----------|
| Left | Unresolved MO list + Select |
| Right empty | **Select an MO** / *Choose an unresolved MO…* |
| Right selected | Constraints, financials, scenario cards, **Approve** / **Reject** |

No free-text fields.

#### Role thresholds (Phase 8 — Employee / Supervisor / Manager)

| Agent role | JWT aliases | Max financial impact (USD) | Approve resolution | Override AI | Financial visibility | Escalation target |
|------------|-------------|----------------------------|--------------------|-------------|----------------------|-------------------|
| **employee** | operator, viewer | 1,000 | No | No | cost_impact | supervisor |
| **supervisor** | planner | 10,000 | Yes | No | cost_impact, department_pnl | manager |
| **manager** | admin, executive | 50,000 | Yes | Yes | cost_impact, margin, pnl, cash_flow | executive |

- Impact above role max → `escalation_required=true`; write-back approve returns `insufficient_authority`.
- A11 Finance agent: non-managers only see `cost_impact` (margin stripped).
- UI Resolution **Approve** still calls res-svc; Phase 8 write-back safety is under Platform/API `POST /api/v1/phase8/write-back` (dry-run default). See [§19](#19-odoo-master-chapter).

### Validations & Restrictions

| Rule | Behaviour |
|------|-----------|
| Recommended | Highest business_score |
| Approve | Disabled when `approved` or in-flight |
| Reject | Visible but **noop** |
| Load fail | Empty lists (no offline fake scenarios) |

### Integrations

| Call | Endpoint |
|------|----------|
| Scenarios | `GET /api/v1/resolution/scenarios` (+ `mo_id`) |
| Queue (product_id) | `GET /api/v1/feasibility/queue` |
| Financial | `POST /api/v1/financial/project` `{ product_id, quantity, selling_price: 500 }` |
| Approve | `/resolution/scenarios/{id}/approve` or `/resolution/approve` |

Approval is optimistic-locked server-side — conflict → error surfaced to UI.

### Component Interactions

```
Control Tower inline panel ↔ Resolution Center (same APIs)
Planning Dashboard "Resolve" / "Scenarios" → here
Approved scenario → may feed War Room recovery / schedule changes downstream (planner still drives Schedule)
```

---

## 5. Copilot (Ctrl+K)

### Main Process

Natural-language assistant (A7 / `nlp-svc`). Available as a full page and as a global drawer from every protected screen.

**Warnings**

- LLM routes allow up to **300 seconds**; without an API key the assistant degrades gracefully (offline/limited copy), not a crash.
- Drawer and full page are **separate React instances** of the same panel.

### Step-by-Step Instructions

1. From any screen: press **Ctrl+K** (Windows) or **Cmd+K** (macOS), or click the floating **AI** button (aria **Open Copilot**).
2. Or open **AI & Governance → Copilot** (`/ai-governance/copilot`).
3. Choose **Agent role**: Planner · Manager · Supervisor · Executive (defaults toward JWT role).
4. Type in **Ask about your production...** and click **Send** (or use a suggestion chip).
5. Read answer under **IPE Copilot**; review **Sources** and follow-up chips.
6. Close drawer with **Close** or **Escape**.

### Screens & Forms

#### CopilotPanel — `/ai-governance/copilot` + global palette

| Field / control | Required | Notes |
|-----------------|----------|-------|
| Agent role | Yes (select) | Planner / Manager / Supervisor / Executive |
| Query | Yes | Placeholder **Ask about your production...** |
| **Send** | — | Disabled when empty or **Thinking...** |

Empty hint explains role-aware behaviour and *"If AI assistant is not configured…"*.

### Validations & Restrictions

| Rule | Message |
|------|---------|
| Empty query | Submit disabled |
| Offline / API fail | **"Copilot is offline or could not reach the API. Check Kong and nlp-svc."** |
| Timeout | Error after 300s |

### Integrations

| Call | Endpoint |
|------|----------|
| Session | `POST /api/v1/copilot/session` |
| Query | `POST /api/v1/copilot/query` |
| Auth | Bearer + `X-Tenant-ID` |
| Kafka | `ipe.copilot.queried` (server-side emit) |

PII stripping middleware may redact sensitive fields before SaaS LLM tiers.

### Component Interactions

```
Ctrl+K anywhere → same capabilities as full Copilot page
Planner Assist on Control Tower → separate lighter endpoint (/planner-assist/query), not Copilot
Meeting Prep (AI Governance) → related briefing workflow, different route
```

---

## 6. Planning Center

Hub shell: **Planning Hub** — *"Detect → decide → schedule"* (`/planning` → default `/planning/dashboard`).

**Release note:** With `VITE_RELEASE_PROFILE=release1`, tabs Dashboard, Cockpit, Horizons, Demand, Scenarios, Predictions, Root Cause may be hidden; Control Tower / Resolution / Schedule always show.

### Main Process

Planners move: **Dashboard → Control Tower → Resolution → Cockpit tools (MPS/MRP/Promise) → Schedule**. Demand sensing and scenarios support weekly rebalance; Horizons ties strategic/tactical/operational.

**Warnings**

- Cockpit / Horizons show amber **"… offline shell"** with demo numbers if APIs fail.
- Predictions & Root Cause are **sample-MO demos** (hardcoded UUID); Root Cause **ignores** `:moId` route param.
- Scenario Workbench baseline KPIs are **hardcoded** in the UI for comparison.
- Cockpit attention strings (`→ resolve`, `→ run_mrp`) are **labels only** — not clickable navigation.

### Step-by-Step Instructions — primary weekly planning loop

1. **Planning → Dashboard** — scan KPI cards; follow **View queue →**, **Resolve →**, **Open Gantt →** as needed.
2. **Planning → Control Tower** — triage risk ([§3](#3-control-tower--feasibility)).
3. **Planning → Resolution** — approve trade-offs ([§4](#4-resolution-center)).
4. **Planning → Cockpit** — read health tiles; click **Update MPS**, **Run MRP**, **Check ATP/CTP**, **RCCP**, **Level production**, **Scenario +20%** as needed; inspect JSON result.
5. **Planning → Schedule** — set optimization controls; **Regenerate schedule**; approve Gantt / upload project plan.
6. Optional: **Demand** → **Run sense cycle**; **Scenarios** → create what-ifs; **Horizons** → cascade/escalate; **Predictions** / **Root Cause** → sample demos.

### Screens & Forms

#### Planning Dashboard — `/planning/dashboard`

| Metric card | Action button | Goes to |
|-------------|---------------|---------|
| MOs in queue | View queue → | Control Tower |
| Avg feasibility | KPIs → | Control Tower |
| Orders at risk | Resolve → | Resolution |
| Resolution scenarios | Scenarios → | Resolution |
| Scheduled operations | Open Gantt → | Schedule |

APIs: feasibility kpis/queue, resolution scenarios, capacity schedule/active. Soft-fail empties.

#### Planning Cockpit — `/planning/cockpit`

| | |
|--|--|
| **Purpose** | Plan health, attention queue, weekly horizon, planning tools |
| **Offline** | **"Cockpit API unavailable — offline shell."** |

**Health cards:** Plan coverage · Demand-supply · Horizon · Stability · Frozen weeks  

**Tool buttons → `POST /api/v1/planning-command/…`**

| Button | Path | Default body highlights |
|--------|------|-------------------------|
| Update MPS | `mps` | Backend defaults e.g. product `FG-DT100` |
| Run MRP | `mrp/explode` | `{ mo_qty: 20 }` |
| Check ATP/CTP | `promise` | `{ qty: 5 }` — implements ATP/CTP/PTP |
| RCCP | `capacity/rccp` | `{}` |
| Level production | `level` | `{}` |
| Scenario +20% | `scenarios/cascade` | `{ demand_uplift_pct: 20 }` |

Busy: **Running…**; result in `<pre>`; fail: `{name}: offline / unavailable`. UI does **not** send `persist: true` (optional DB save on backend unused from UI).

#### Demand Sensing — `/planning/demand`

| Control | Effect |
|---------|--------|
| **7d / 14d / 30d** | Horizon; reload forecast |
| **Run sense cycle** / **Running…** | `POST /api/v1/demand/sense` then reload |

Title **Demand Sensing**; empty: *No forecasts yet. Click "Run sense cycle"…*; error **Could not load forecasts.**

#### Scenario Workbench — `/planning/scenarios`

| Field | Default / placeholder |
|-------|----------------------|
| Scenario name | Required (trim); empty disables create |
| Demand Δ | `10%` |
| Supplier delay | `3` days |
| Capacity reduction | `5%` |

Buttons: **Create & simulate**, **Compare**, **Re-simulate**, **Promote**. Cap **3** scenarios in compare panel. Baseline KPIs hardcoded (OTD 87.5, etc.). Distinct from Resolution scenarios and Cockpit cascade.

#### Schedule — `/planning/schedule`

**View radios:** **AI / solver schedule** | **Uploaded project plan**

**Optimization controls**

| Field | Default | Range / options |
|-------|---------|-----------------|
| Strategy | hybrid | Hybrid, Earliest due date, Maximum throughput, Revenue focus, Inventory optimization |
| Delivery focus | 70% | 0–100 → alpha |
| Efficiency focus | 50% | 0–100 → beta |
| Capacity buffer | 10% | 0–20 step 5 |
| Allow overtime scheduling | checked | boolean |
| **Regenerate schedule** | | `POST /capacity/schedule` |

**Also:** Project plan upload ([§2](#2-data-onboarding--upload-wizard)); **Download MS Project**; Digital Twin (**Supplier ID** default `SUP-T2-001`, **Delay (days)** default 14, **Run disruption**); Explain panel; Gantt CPM **Discard** / **Confirm & Approve**; **Approve All (n)**.

Empty Gantt: *No schedule data available. Run a capacity schedule first.* Version conflict on approve throws `VERSION_CONFLICT`.

#### Predictive Risk — `/planning/predictions` ⚠️ sample stub UX

Button **Load sample MO** → `GET /api/v1/feasibility/predict/{SAMPLE_MO}`. Cards for 3/7/14 days. Error: **Predictive scoring unavailable**. Sample UUID hardcoded.

#### Root Cause Explorer — `/planning/root-cause` (`/:moId` unused) ⚠️ sample stub UX

Button **Analyze sample MO** → `GET /api/v1/feasibility/root-cause/{SAMPLE_MO}`. Levels **Level {n} · Why?**; **Recommendations**. Route param ignored.

#### Horizons — `/planning/horizons` (also Phase 7)

See [§10](#10-deep-planning-phase-7).

### Validations & Restrictions

| Area | Rule |
|------|------|
| Scenario create | Disabled if name blank or busy |
| Schedule upload | `.xlsx` only; messages in §2 |
| CPM Confirm | Disabled if conflicts |
| Cockpit tools | Fail → offline JSON message |

### Integrations

| Domain | Services |
|--------|----------|
| Feasibility / predict / root-cause | fea-svc |
| Resolution | res-svc |
| Schedule / project plans / CPM | cap-svc |
| Demand sense/forecast | dpe-svc |
| Planning-command MPS/MRP/promise/level/RCCP/scenarios/ops | dpe-svc phase5 |
| Horizons cascade | dpe-svc phase7 |
| Digital twin disrupt | network-svc |
| Scenarios sandbox | scn-svc (`/api/v1/scenario`) |

### Component Interactions

```
Dashboard → CT / Resolution / Schedule
Demand sense → CT forecast overlay
Cockpit MPS → (manual) Schedule regenerate
Cockpit Scenario +20% ≠ Scenario Workbench ≠ Resolution scenarios
Ops Live (Command Center) shares phase5 ops APIs, not Planning Hub
```

---

## 7. Command Center

Hub: **Command Center** — *"Alerts, KPIs, and financial impact of disruption"* (`/command-center` → `dashboard`). In release1, often only **OTD Analytics** remains visible.

### Main Process

Leadership and supervisors use Command Center for disruption response (War Room), shift live ops, executive P&L, outcomes/QBR, and Operations Deep (Andon/Gemba).

**Warnings**

- Ops Live has offline shell + demo War Room object.
- War Room **Assign Task** is **UI only** (no handler).
- S&OP Report **Export** downloads **JSON**, not PDF.
- Operations Deep is a **raw-JSON workbench**; Digital Gemba is stub (`iot_live=false`, PH1-02 OPEN).
- Ops Live **Activate War Room** is separate from the War Room page aggregate.

### Step-by-Step Instructions — shift start

1. **Command Center → Ops Live** — read shift header, scorecards, work centres, alerts.
2. Optionally **Activate War Room** (posts ops war-room; shows JSON).
3. **War Room** page — review disruptions, recovery options, mitigation scenarios.
4. Clear Andon via **Operations Deep** tools if needed.
5. Leadership: **Executive**, **Outcomes**, **Cost of Chaos**, **OTD Analytics**, **S&OP Report**.

### Screens & Forms

#### Command Center Dashboard — `/command-center/dashboard`

Cards with deep-links: Active alerts → War Room; AI OTD → Executive; Cost of chaos (7d) → Pareto; Recovery options → Mitigate; Delay categories → Analytics.

#### Ops Live — `/command-center/ops-live`

| | |
|--|--|
| **Title** | Operations Live |
| **Header** | `Shift {shift} · Supervisor {supervisor} · {n} MOs in production` |
| **Scorecards** | Output (done/planned) · OEE · Quality · On-time starts |
| **Sections** | Work centres · Live alerts · Performance cockpit · Predictive command (3/7/14d) · War Room active |
| **Button** | **Activate War Room** (red) |
| **Offline** | **"Ops API unavailable — offline shell."** (Shift B / Mohamed demo) |

APIs: `GET .../ops/dashboard|performance|predictive`, `POST .../ops/war-room`.  
Backend also exposes `POST .../ops/shift-handover` and `/actions` — **not wired as dedicated UI screens** in the current frontend (use API / calendar routines).

#### War Room — `/command-center/war-room`

KPIs: Active Disruptions · Impacted MOs · Revenue at Risk · Mitigation Options.  
Sections: Top Recovery Options; Active Disruption Events (+ MO table); Mitigation Scenarios with **Assign Task** (noop).  
APIs: war-room aggregate (default supplier `SUP-T2-001`, delay 21), resolution scenarios, recovery-plan.

#### Executive Analytics — `/command-center/executive`

KPIs, AI vs Manual OTD (may show **"Simulated Comparison"** 94.2% / 71.8%), delay coverage, planner productivity, WC OTD, P&L S&OP view, S&OP gap (`POST /sop/solve`), what-if simulation. Soft-fail empties.

#### Outcomes — `/command-center/outcomes`

**Capture OTD baseline** / **Capturing…**; **Copy QBR summary**. Cards: OTD (30 days), vs baseline, MOs saved; **Odoo sync health**.

#### Cost of Chaos — `/command-center/cost-of-chaos`

Period **7 days** / **30 days**; **Retry**; **Open War Room →**. Pareto + category breakdown + top MOs.

#### Equipment Health — `/command-center/equipment`

Fleet health %; **Predictive alerts (RUL &lt; 48h)**. No action buttons; silent empty on fail.

#### S&OP Executive Report — `/command-center/sop-report`

**Generate Report** / **Generating...** (`POST /api/v1/reports/sop` with horizon_weeks 12); **Export** → JSON file; history table.

#### Operations Deep — `/command-center/operations-deep`

See [§10](#10-deep-planning-phase-7).

### Validations & Restrictions

| Screen | Notes |
|--------|-------|
| Ops Live | Offline shell when API down |
| War Room | Soft-empty on error; Assign Task noop |
| S&OP Export | JSON download only |
| Outcomes Capture | lookback_days 30, source `outcomes_dashboard` |

### Integrations

| Area | Backend |
|------|---------|
| Ops Live / war-room activate | dpe-svc planning-command |
| War Room aggregate | war-room / network / resolution |
| Executive / chaos / outcomes | dpe analytics + sop + capacity |
| Equipment | equipment / maintenance APIs |
| S&OP report | reports/sop |
| Disruption WS | fea-svc disruption broadcaster (infra) |

### Component Interactions

```
Ops Live Activate War Room ≠ War Room page (different APIs/payloads)
Cost of Chaos → Open War Room
Intelligence Pulse overnight actions → morning Ops Live / Control Tower
Shift handover API exists without dedicated page — use routines §15
```

---

## 8. OTD Analytics

### Main Process

On-time delivery analytics for planners and executives — trend, root cause, cost of chaos, filters, print export.

**Warnings**

- Empty until snapshots exist: **"No OTD snapshots yet"** (+ first production week hint).
- **Export PDF** uses `window.print` (browser print), not a server PDF.

### Step-by-Step Instructions

1. Open **Command Center → OTD Analytics** (`/command-center/otd-analytics`).
2. Set filters: supplier / line / region (All…), period Daily/Weekly/Monthly, range 30/60/90/180d, chaos 7d/30d.
3. Read KPI strip, trend, **Executive summary** narrative.
4. Review root-cause and cost details (mobile: **Show/Hide root cause & cost details**).
5. Click **Export PDF** to print.

### Screens & Forms

| Control | Options / effect |
|---------|------------------|
| Filters | All suppliers/lines/regions |
| Period | Daily / Weekly / Monthly |
| Range | 30 / 60 / 90 / 180 days |
| Chaos window | 7d / 30d |
| **Export PDF** | `window.print` |

APIs under `/api/v1/analytics/otd/*`, baseline, filter options, cost-of-chaos.

### Validations & Restrictions

Empty state blocks charts until data; no client-side field schema beyond filter selects.

### Integrations

Analytics APIs via Kong → dpe-svc. Outcomes page can **Capture OTD baseline** that feeds related metrics.

### Component Interactions

```
Outcomes Capture baseline ↔ OTD Analytics
Cost of Chaos page ↔ OTD chaos panel (shared analytics family)
```

---

## 9. Intelligence Hub / M1–M9

Hub: **Manufacturing Intelligence** — *"Nine command modules · 17 agents · autonomous cross-functional orchestration"* (`/intelligence` → `/intelligence/pulse`).

### Main Process

Daily: start at **Today's Pulse**, drill into M1–M9. M1–M6 are **navigation shells** (no live widgets). M7–M9 are **ToolRunner** screens that POST tools and show **raw JSON**.

**Warnings**

- Pulse offline shell with amber banner if API fails.
- M9 subtitle states: *"IoT = stub, Odoo write-back = PH1-02 (mock)."*
- `/api/v1/enterprise/*` may be **offline in Kong-only release2** (not routed) — buttons show `"{label}: offline / unavailable"`.
- M1–M6 do not call module APIs themselves.

### Step-by-Step Instructions

1. Open **Intelligence → Today's Pulse**.
2. Read MO track / OTD / margin / at-risk / auto-actions; skim **Agent Activity**.
3. Click **Open ▸** on a module card, or use hub tabs M1–M9.
4. For M1–M6: follow outbound links to Planning / Supply / Quality / etc.
5. For M7–M9: click tool buttons; read JSON results.
6. Optional links from Pulse: **Customer portal**, **Digital factory (shop floor)**, **All agents**.

### Screens & Forms

#### Today's Pulse — `/intelligence/pulse`

Loading: **Loading intelligence pulse…**  
Offline: **Pulse API unavailable — showing offline shell.**  
API: `GET /api/v1/intelligence/pulse`.

#### M1–M6 shells

| Route | Title | Links (exact) |
|-------|-------|---------------|
| `/intelligence/demand` | M1 Demand Command | Demand forecast ▸ · Orders ▸ |
| `/intelligence/production` | M2 Production Command | Control tower ▸ · Predictions ▸ · Schedule ▸ |
| `/intelligence/supply` | M3 Supply Command | Inventory ▸ · Procurement ▸ · Suppliers ▸ |
| `/intelligence/quality` | M4 Quality Command | Quality dashboard ▸ |
| `/intelligence/finance` | M5 Finance Command | Cost of chaos ▸ · Executive ▸ |
| `/intelligence/customer` | M6 Customer Command | Customer portal ▸ · Order management ▸ |

#### M7 Analytics — `/intelligence/analytics` ⚠️ raw JSON tools

On load: insights cards via `POST .../enterprise/analytics/insights`.  
Tools: **Predictions** · **Trend (copper)** · **Anomaly (throughput)**. Offline amber banner.

#### M8 Commercial — `/intelligence/commercial` ⚠️ raw JSON

**Optimize price** · **Deal profitability** · **Contract compliance**; A17: **Orchestrated ATP/CTP** · **Enforce policies** · **Cascade demand change**.

#### M9 Procurement + Shop Floor — `/intelligence/procurement` ⚠️ stub/mock flags in copy

**3-way match** · **Confirm receipt** · **Work instructions** · **Time tracking** · **Production progress**. Compute locally; **no live Odoo write-back**.

### Validations & Restrictions

ToolRunner busy **Running…**; catch → `"{label}: offline / unavailable"`. No form-field schemas on M1–M6.

### Integrations

| Module | Agents / APIs |
|--------|----------------|
| Pulse | intelligence/pulse |
| M7–M9 | `/api/v1/enterprise/*` on dpe-svc (Kong gap in release2) |
| M1–M6 | Navigation only → other hubs |

### Component Interactions

```
Pulse → module routes / portal / shop floor / agents
M2 links → Control Tower / Predictions / Schedule
M9 tools ↔ Shop Floor page (related A16 surfaces; different UX)
Deep Planning tabs sit in same Intelligence hub shell
```

---

## 10. Deep Planning Phase 7

### Main Process

Analyst workbench for three horizons and deep S&OP / demand / production / operations tools. Results render as **raw JSON**, not polished dashboards.

**Warnings**

- Explicit stub: Digital Gemba `iot_live=false — PH1-02 OPEN`.
- Andon lifecycle may be **in-memory** (resets on service restart — Spec 029 moves toward DB persistence).
- S&OP interactive stage-gate UI is **deferred**; Deep tabs compute analysis only.
- Horizons offline shell with FALLBACK cards.

### Step-by-Step Instructions

1. **Planning → Horizons** — review Strategic / Tactical / Operational cards.
2. Click **Cascade decision down ▾** or **Escalate constraint up ▴**; read JSON.
3. **Intelligence → S&OP Deep / Demand Deep / Production Deep** — run tool buttons.
4. **Command Center → Operations Deep** — OEE / Gemba / Andon / KPI tree / standard work / calendar.

### Screens & Forms

#### Three Horizons — `/planning/horizons`

Title: **Planning Horizons — آفاق التخطيط**. Coverage %; per-card window, granularity, health bar, pending, metrics.  
APIs: `GET /planning-command/horizons`, `POST /horizons/cascade` `{direction}`.

#### S&OP Deep — `/intelligence/sop-deep`

Buttons: **Financial S&OP (P&L per consensus)** · **Rolling S&OP (event-driven)** · **Demand shaping options** · **Portfolio mix optimization** → `POST sop/financial|rolling|demand-shaping|portfolio`.

#### Demand Deep — `/intelligence/demand-deep`

**Decompose demand** · **Decompose (with promo)** · **Collaboration consensus** · **NPI forecast**.

#### Production Deep — `/intelligence/production-deep`

**Setup-sequence optimize** · **Multi-resource schedule** · **Campaign plan** · **Labour + SPOF flags** · **Make-or-buy (at bottleneck)** (sample utilisation 95%).

#### Operations Deep — `/command-center/operations-deep`

| Button | Call |
|--------|------|
| OEE improvement programme | POST operations/oee-programme |
| Digital Gemba (stub live) | GET operations/gemba |
| Andon board | GET operations/andon |
| Trigger Andon (yellow) | POST with sample WC-WND / Mohamed message |
| KPI tree drill-down | GET operations/kpi-tree |
| Standard work (A16) | POST operations/standard-work |
| Planning calendar | GET calendar |

Idle copy: **"Select an analysis above to run it."**

### Validations & Restrictions

No user field forms — fixed demo bodies in buttons. Failures → `"{label}: offline / unavailable"`.

### Integrations

All under `/api/v1/planning-command/*` (dpe-svc phase7). Calendar endpoint supports daily/weekly/monthly routine mapping ([§15](#15-daily--weekly--monthly-routines)).

### Component Interactions

```
Horizons cascade ↔ Cockpit / S&OP Deep decisions (conceptual; manual navigation)
Operations Deep Andon ↔ Ops Live alerts (related ops domain)
Planning calendar GET ↔ routines in §15
```

---

## 11. Odoo Config / ERP Connections

### Main Process

Configure ERP connections for sync into IPE CDM. Primary self-service UI is **Odoo Connections**; a versioned **Odoo Configuration** screen and R1 Admin wizard also exist. Phase 8 adds **write-back safety** (dry-run → approve → mock execute) via `/api/v1/phase8/write-back*` — full map in [§19 Odoo Master](#19-odoo-master-chapter).

**Warnings**

- **PH1-02 live Odoo staging is OPEN.** Testing typically uses **mock-odoo-api** (:8010) or SQL seed — do not assume production sync.
- Password required for **new** connections.
- Sync may report success against mock without real plant data.
- Feature flag `ipe.odoo.live_writeback` defaults **false**. Even with `execute=true`, Wave 1 records **MOCK** execute (`is_live=false`, `ph1_02_blocker` message) — never claim live Odoo success.

### Step-by-Step Instructions

1. Open **Platform → Odoo Connections** (`/platform/odoo-config`).
2. Click **Add new connection**.
3. Fill **Display name**, **Odoo URL**, **Database name**, **Username**, **Password**, **Sync interval** (5/15/30/60 min), **Environment** Production/Staging.
4. Click **Save**.
5. **Test Connection** → confirm success/fail message.
6. **Activate** the connection; optionally **Sync now**.
7. Open **Activity log** to inspect sync events.
8. Advanced: `/platform/odoo-config/versions` for entity mappings, test, save, **Rollback**.

### Screens & Forms

#### Odoo Connections — `/platform/odoo-config`

| Field | Required | Options / default |
|-------|----------|-------------------|
| Display name | Yes (practical) | text |
| Odoo URL | Yes | host_url |
| Database name | Yes | text |
| Username | Yes | text |
| Password | **Required on create** | blank on edit unless changing |
| Sync interval | Yes | 5/15/30/60 min (default 15 min / 900s) |
| Environment | | Production checkbox (`is_production`) |

**Row actions:** Test Connection · Edit · Activate / Deactivate · Sync now · Activity log.  
**Buttons:** Add new connection · Save · Cancel · Close (logs).  
Empty: *"No connections yet. Add one to get started."*  
Validation: *"Password is required for new connections"*.

#### Odoo Configuration (versions) — `/platform/odoo-config/versions`

Entity select · Add entity · Display name · Sync interval (minutes) · Odoo URL · Database · Username · Password · Integration enabled · **Test Connection** · **Save Configuration** · version history **Rollback** / **Current**.

### Validations & Restrictions

| Rule | Message / behaviour |
|------|---------------------|
| New connection password | Password is required for new connections |
| Load fail | Failed to load connections (or err.message) |
| Test | Success/fail message with status dot |

### Integrations

| API family | Purpose |
|------------|---------|
| `/api/v1/erp/connections` | CRUD, test, activate, sync-now, logs |
| `/api/v1/admin/odoo-config` | Versioned config / rollback |
| `/api/v1/sync/*` | Sync status (Control Tower / Outcomes) |
| Connector service | XML-RPC/JSON-RPC HMAC to Odoo / mock |

**Failure / delay:** Stale sync badge on Control Tower; Outcomes sync health degraded; queue stays empty until seed or successful sync.

### Component Interactions

```
Odoo sync → CDM → Control Tower / Schedule / Agents
Onboarding wizard (stub) → navigates toward Admin / Odoo setup
Control Tower empty state → Open Odoo Settings
```

---

## 12. Customer Portal

### Main Process

Read-only order tracking for customer-facing status (A8). No edits.

**Warning:** Offline shows **"Portal API unavailable — demo empty state (read-only)."**

### Step-by-Step Instructions

1. Open **Customer Portal** (`/customer-portal`) from sidebar or Intelligence Pulse link.
2. Read table: Order · Status · Delivery · Confidence · Invoice.
3. Confidence colours: green / red / amber from API `color` field.
4. Empty: **"No active orders to display."**

### Screens & Forms

No input fields. Title **Customer Portal**; subtitle mentions delivery confidence & invoice status (A8).  
API: `GET /api/v1/orders/portal/summary`.

### Validations & Restrictions

Read-only — no client validation. Soft empty on failure.

### Integrations

dpe-svc portal summary. Depends on order/demand data in CDM (seed/Odoo).

### Component Interactions

```
M6 Customer Command → Customer portal ▸
Intelligence Pulse → Customer portal link
Order Management (Supply Chain) → related orders domain (editable promise there)
```

---

## 13. Shop Floor / A16

### Main Process

Shop Floor PWA-style board for operators: list in-progress/pending work, scan barcode to bump local progress.

**Warnings**

- Tenant UUID is **hardcoded** in the router for this page.
- Barcode scan updates **client state only** — **no server POST** on scan; offline queue uses `localStorage` key `ipe_pending_sync`.
- IoT telemetry / polished operator tablet UI are **stub/deferred** (PH1-02 / Wave 2).
- M9 **Work instructions / Time tracking / Production progress** are separate enterprise JSON tools.

### Step-by-Step Instructions

1. Open **Shop Floor** (`/shop-floor`).
2. Confirm **Online** / **Offline** badge; note `{n} pending sync` if any.
3. Review **In Progress** and **Pending** columns (mo_id, workcenter, operator, progress).
4. In **Scan Barcode**, enter/scan MO id and press Enter — matching row progress +10 and status `in_progress`.

### Screens & Forms

| Control | Notes |
|---------|-------|
| Scan Barcode | Placeholder *Scan MO barcode or enter ID...* |
| Online/Offline | Badge |
| Lists | In Progress (n) · Pending (n) |

API: `GET /api/v1/shop-floor/items?tenant_id={hardcoded}`.

### Validations & Restrictions

No schema validation on scan — unmatched scans simply do nothing visible beyond local attempt.

### Integrations

Shop-floor API; localStorage offline queue. Enterprise A16 tools via M9 (`/api/v1/enterprise/...`) — raw JSON, mock write-back.

### Component Interactions

```
Intelligence Pulse → Digital factory (shop floor)
M9 A16 tools ↔ conceptual same domain
Operations Deep Standard work (A16) → JSON programme, not this PWA
```

---

## 14. Platform / Admin

### Main Process

Tenant configuration, upload, agents, exceptions, Odoo, onboarding stub, MLOps, multi-tenant ops.

### Step-by-Step Instructions — admin config

1. **Platform → Admin** (`/platform/admin`).
2. **Configuration** tab: adjust **Priority Weights** (0–1), **Auto-Confirm Threshold** / **Planner Threshold** (0–100), **Autonomy Mode** (`shadow` · `suggest` · `autonomous`).
3. Click **Save Configuration** / **Saving...**.
4. Review **Data Quality** and **LLM Tiers** tabs.
5. Use other Platform tabs as needed (Upload, Agents, Exceptions, Odoo, Onboarding, MLOps, Ops).

### Screens & Forms

#### Admin Console — `/platform/admin`

| Tab | Fields / content | APIs |
|-----|------------------|------|
| Configuration | Priority weights; feasibility thresholds; autonomy mode; **Save Configuration** | GET/PUT `/api/v1/admin/config` |
| Data Quality | BOM Completeness · Lead Time Accuracy · Inventory Record Accuracy (+ Good/Needs Review/Critical) | GET `/api/v1/admin/data-quality` |
| LLM Tiers | Active Provider · health Available/Unavailable | LLM status fetch |
| Odoo ERP (R1) | Wizard panel | R1 only |

#### Data Upload — `/platform/upload` — see [§2](#2-data-onboarding--upload-wizard)

#### Agent Dashboard — `/platform/agents`

`GET /api/v1/agents/status`. Cards: agent_id, name, Healthy/{status}, last run. Error: **Unable to load agent status**. No buttons.

#### Exception Manager — `/platform/exceptions`

**Create sample exception** (fixed A2 / STOCKOUT_RISK / copper wire message). Filter All/Critical/High/Medium. **Acknowledge** on open rows. Empty: **No exceptions yet**. **No initial GET list** — only session-created rows appear.

#### Onboarding — `/platform/onboarding` — stub [§2](#2-data-onboarding--upload-wizard)

#### MLOps — `/platform/ml-ops`

Model table: Version, Accuracy, Drift PSI, Status, Last Trained. KPIs include Drift Alerts (PSI &gt; 0.25). Hardcoded tenant query param. No actions.

#### Multi-Tenant Ops — `/platform/ops`

Tenant health summary + **Recent Alerts** (*No active alerts*). APIs: `/api/v1/ops/tenants/health`, `/ops/alerts?limit=20`.

### Supply Chain Hub (related platform-adjacent ops)

Not under Platform sidebar but operational:

| Screen | Route | Key actions |
|--------|-------|-------------|
| Supply Planning | `/supply-chain/supply-planning` | **Generate plan** |
| Order Management | `/supply-chain/orders` | **Promise latest order**; empty hints API create |
| Procurement | `/supply-chain/procurement` | **Run compliance check** |
| Suppliers | `/supply-chain/suppliers` | Scorecard read-only |
| Tariff | `/supply-chain/tariff` | Region · Tariff delta (%) · Margin threshold (%) · **Run Shock Simulation** |
| SCN Portal | `/supply-chain/scn-portal` | Network suppliers table |
| Inventory | `/supply-chain/inventory` | SKU on-hand list |

Tariff matrix **upload** still unwired (parser only).

### AI & Governance (brief)

| Screen | Route | Notes |
|--------|-------|-------|
| Copilot | `/ai-governance/copilot` | [§5](#5-copilot-ctrlk) |
| Meeting Prep | `/ai-governance/meeting-prep` (`/:type`) | Briefing prep |
| Design AI | `/ai-governance/design-ai` | Design assist surface |
| AI Trust | `/ai-governance/ai-trust` | Trust scores / adoption |
| MDR | `/ai-governance/mdr` | Model decision records |
| Compliance | `/ai-governance/compliance` | Compliance KPIs |
| Quality | `/ai-governance/quality` | Quality dashboard (A10) |
| Sustainability | `/ai-governance/sustainability` | Carbon / green |

### Validations & Restrictions

| Area | Rule |
|------|------|
| Admin thresholds | 0–100 numeric; weights 0–1 |
| Exceptions | Sample create only until refreshed from API patterns |
| Autonomy | shadow (default product posture) / suggest / autonomous |

### Integrations

Admin config → feasibility auto-confirm thresholds; Odoo → sync; Agents status → A1–A17 health; upload-svc; ops multi-tenant health.

### Component Interactions

```
Admin autonomy/thresholds → Feasibility action_taken behaviour
Upload / Odoo → data for all hubs
Agents page ← Pulse "All agents"
Exceptions ← agent-raised SLA items (sample button for demo)
```

---

## 15. Daily / Weekly / Monthly Routines

Cross-workflow cadence mapped to real screens. Calendar data also available via `GET /api/v1/planning-command/calendar`.

### Daily (shift) — supervisors & planners

1. **Ops Live** (`/command-center/ops-live`) — shift scorecard, WC load, alerts.
2. **Operations Deep → Andon board / Trigger Andon** — triage calls (in-memory caveat).
3. **Control Tower** — work MO risk queue; **Resolve** / approve.
4. **Today's Pulse** — overnight auto-actions.
5. **Shift handover** — backend `POST /planning-command/ops/shift-handover` (no dedicated page; use Ops Live notes / API until UI lands).
6. Optional: **Shop Floor** scan board; **Copilot** Ctrl+K for ad-hoc questions.

### Weekly — planners

1. **Planning Cockpit** — health + attention.
2. **Update MPS** · **Run MRP** · **Check ATP/CTP** · **RCCP** · **Level production**.
3. **Schedule → Regenerate** / approve / project plan as needed.
4. **Demand → Run sense cycle**; **Scenario Workbench** what-ifs.
5. **Supply Chain → Suppliers / Procurement / Inventory**.
6. **Predictions / Root Cause** sample checks (demo UUID until live MO picker ships).

### Monthly — S&OP / leadership

1. **S&OP Deep** — financial / rolling / shaping / portfolio tools.
2. **Horizons** — cascade / escalate.
3. **Executive** + **S&OP Report** — P&L, gaps, JSON export brief.
4. **OTD Analytics** + **Outcomes** (capture baseline, QBR copy) + **Cost of Chaos**.
5. **AI Trust / Compliance / Sustainability** governance pass.
6. **Admin** — review thresholds, data quality, LLM tier health.

### End-to-end dependency chain (honest)

```
Seed or Odoo sync (PH1-02 OPEN → often seed/mock)
  → Upload wizard (validation/agents labels) optional
  → Feasibility queue (Control Tower)
  → Resolution approve
  → Cockpit MPS/MRP/Promise
  → Schedule solve / project plan
  → Ops Live / War Room / OTD
  → Intelligence Pulse / Deep tools
```

---

## 16. Appendix — Stub / mock / deferred inventory

Screens and capabilities to treat as **non-production-polished** or **non-live**:

| Screen / capability | Flag | Notes |
|---------------------|------|-------|
| Tenant Onboarding Wizard | **UI stub** | No API persistence |
| Data Upload Center row import | **Validate-only** | Does not seed CDM |
| Upload template/error download in UI | **Not wired** | APIs exist |
| Predictions page | **Sample-MO stub UX** | Hardcoded UUID |
| Root Cause page | **Sample-MO stub**; `:moId` unused | Same UUID |
| Planning Cockpit | **Offline shell** fallback | Amber banner |
| Ops Live | **Offline shell** + demo war room | Amber banner |
| Horizons | **Offline shell** fallback | Amber banner |
| Intelligence Pulse | **Offline shell** fallback | Amber banner |
| M1–M6 | **Nav shells only** | No live widgets |
| M7–M9 ToolRunner | **Raw JSON workbench** | Enterprise Kong gap possible |
| M9 IoT / Odoo write-back | **Stub / mock** (PH1-02) | Stated in UI subtitle |
| Deep Planning (all Deep tabs) | **Raw JSON workbench** | Not polished dashboards |
| Digital Gemba | **Stub** `iot_live=false` | PH1-02 OPEN |
| Andon persistence | **In-memory** (pre Spec 029 DB) | Resets on restart |
| War Room Assign Task | **UI noop** | No handler |
| Resolution / Inline Reject | **UI noop** | No handler |
| Scenario Workbench baselines | **Hardcoded KPIs** | Comparison only |
| Executive Simulated Comparison | **Synthetic OTD** when empty | 94.2% / 71.8% |
| S&OP Report Export | **JSON not PDF** | Filename `sop-report-*.json` |
| OTD Export PDF | **Browser print** | Not server PDF |
| Shop Floor scan | **Client-only progress** | No POST |
| Shop Floor / SCN / MLOps tenant | **Hardcoded UUID** | Router constant |
| Tariff matrix upload | **No HTTP upload** | Parser only |
| Live Odoo staging | **PH1-02 OPEN** | Use mock/seed |
| Phase 8 write-back | **Dry-run / MOCK execute** | `ipe.odoo.live_writeback` false; PH1-02 |
| Phase 8 A18–A20 | **STUB** | Full behaviour in 8B–8D |
| Ollama narratives | **Degrade banner** | Core planning continues |
| CT/MPS CSV export | **API available** | UI download not first-class |
| Phase 8 Excel types in wizard lock | **Types exist; not in PHASES 1–5 list** | Use file_type / API aliases |
| Shift handover / Actions tracker | **API without dedicated UI** | phase5 endpoints |
| S&OP stage-gate interactive UI | **Deferred** | |
| Operator tablet polish / WhatsApp hub | **Deferred** | |
| Arabic native QA | **G-R2-04 OPEN** | |
| `/api/v1/enterprise/*` via Kong release2 | **Not routed** | Direct dpe-svc |

---

## 17. Appendix — Full route index

| Route | Screen |
|-------|--------|
| `/login` | Login |
| `/workspace` | Unified Workspace |
| `/planning/dashboard` | Planning Dashboard |
| `/planning/cockpit` | Planning Cockpit |
| `/planning/horizons` | Three Horizons |
| `/planning/demand` | Demand Sensing |
| `/planning/scenarios` | Scenario Workbench |
| `/planning/control-tower` | Control Tower |
| `/planning/resolution` | Resolution Center |
| `/planning/schedule` | Schedule + Project Plan upload |
| `/planning/predictions` | Predictive Risk |
| `/planning/root-cause` (`/:moId`) | Root Cause Explorer |
| `/command-center/dashboard` | Command Dashboard |
| `/command-center/ops-live` | Ops Live |
| `/command-center/war-room` | War Room |
| `/command-center/executive` | Executive Analytics |
| `/command-center/outcomes` | Outcomes |
| `/command-center/equipment` | Equipment Health |
| `/command-center/cost-of-chaos` | Cost of Chaos |
| `/command-center/otd-analytics` | OTD Analytics |
| `/command-center/sop-report` | S&OP Report |
| `/command-center/operations-deep` | Operations Deep |
| `/intelligence/pulse` | Today's Pulse |
| `/intelligence/demand` … `/customer` | M1–M6 shells |
| `/intelligence/analytics` | M7 Analytics |
| `/intelligence/commercial` | M8 Commercial + A17 |
| `/intelligence/procurement` | M9 Procurement + Shop Floor tools |
| `/intelligence/sop-deep` | S&OP Deep |
| `/intelligence/demand-deep` | Demand Deep |
| `/intelligence/production-deep` | Production Deep |
| `/customer-portal` | Customer Portal |
| `/supply-chain/*` | Supply Planning, Orders, Procurement, Tariff, SCN, Inventory, Suppliers |
| `/ai-governance/*` | Copilot, Meeting Prep, Design AI, AI Trust, MDR, Compliance, Quality, Sustainability |
| `/shop-floor` | Shop Floor PWA |
| `/platform/admin` | Admin Console |
| `/platform/upload` | Data Upload Center |
| `/platform/agents` | Agent Dashboard |
| `/platform/exceptions` | Exception Manager |
| `/platform/odoo-config` | Odoo Connections |
| `/platform/odoo-config/versions` | Odoo Configuration versions |
| `/platform/onboarding` | Onboarding Wizard (stub) |
| `/platform/ml-ops` | MLOps |
| `/platform/ops` | Multi-Tenant Ops |

---

---

## 18. Excel Master Chapter

Every Excel/CSV path IPE exposes today — uploads, validation stages, templates, and exports.

### 18.1 How data actually loads (do not confuse paths)

| Path | Mechanism | Persists to CDM? | UI |
|------|-----------|------------------|-----|
| SQL seed | `scripts/seed-data.ps1`, `seed-startrans-demo.ps1` | **Yes** | No |
| Odoo sync | Connector `/erp/connections/{id}/sync-now`, `/sync/run` | **Yes** (when connected) | Platform → Odoo Connections |
| Data Upload Center | upload-svc multi-stage validate + wizard state | **No** (validate + in-memory progress only) | Platform → Data Upload |
| Project plan | `POST /api/v1/capacity/project-plans/upload` | **Yes** (cap-svc plans) | Planning → Schedule |
| Phase 8 CT/MPS export | `GET /api/v1/phase8/export/risk-queue.csv`, `/export/mps.csv` | N/A (download) | API / future UI wiring |
| Tariff matrix | Parser in code | No HTTP upload | **Unwired** |

### 18.2 Upload-svc file types (complete)

Source: `services/upload-svc/app/core/validator.py` `FILE_SCHEMAS` + `ALIASES`.

| file_type | Phase | Required columns | Agents | Aliases |
|-----------|-------|------------------|--------|---------|
| product_master | 1 | product_code, name, type, uom | A2, A4 | products |
| customer_master | 1 | customer_code, name | A1 | customers |
| supplier_master | 1 | supplier_code, name | A2 | suppliers |
| work_centre_master | 1 | work_centre_code, name | A3, A4 | work_centers, work_centres |
| bom | 2 | product_code, component_code, quantity | A4 | — |
| routing | 2 | product_code, operation_seq, work_centre_code | A3, A4 | — |
| capacity_calendar | 3 | work_centre_code, date, shift, available_hours | A3 | — |
| lead_time | 3 | product_code, supplier_code, lead_time_days | A2 | — |
| cost_data | 3 | product_code, unit_cost | A5, A6 | — |
| inventory | 4 | product_code, on_hand | A2, A4 | — |
| production_orders | 4 | mo_number, product_code, quantity, planned_start, planned_end, status | A3, A4 | mrp_orders |
| sales_orders | 4 | order_number, customer_code, product_code, quantity, order_date, requested_delivery, status | A1, A4 | demand_lines |
| purchase_orders | 4 | po_number, supplier_code, product_code, quantity | A2 | supply_orders |
| historical_otd | 5 | mo_number, planned_end, actual_end | A6 | — |
| **demand_forecast** | **8** | product_code, period, forecast_qty | A1, A4 | forecast |
| **quality_results** | **8** | mo_number, inspection_date, result, measured_value | A10 | quality_inspection |
| **sop_sales_input** | **8** | product_family, period, sales_forecast_qty | A1, A14 | sop_sales |

**Formats accepted:** `.xlsx`, `.xlsm`, `.csv`, `.tsv`, `.txt`. Magic-byte check for Excel (`PK…`). Message on failure: **Invalid file format. Expected .xlsx or .csv**.

### 18.3 Four validation stages

Every upload response includes:

| Stage | Key | Pass criteria | Typical fail messages |
|-------|-----|---------------|------------------------|
| 1 Structure | `stage_1_structure` | All required headers present | Missing columns: … · Invalid file format… · Unknown file_type… · 0 rows found… |
| 2 Types | `stage_2_types` | Required cells filled; qty fields numeric ≥0 | {col} is required · {qty_col} must be numeric · must be non-negative · Duplicate product_code… |
| 3 Referential | `stage_3_referential` | Codes exist in known_codes catalogs when provided | Product/Customer not found in master · {parent} not found in Product Master |
| 4 Business | `stage_4_business` | Structure passed | Fail if stage 1 failed |

**Warnings (non-blocking):** Unknown priority → **Unknown priority. Defaulting to 'high'** (allowed: low/normal/high/urgent).

**Error report download (API):** `GET /api/v1/upload/{upload_id}/errors.xlsx` — columns `row`, `column`, `value`, `message`, `severity`. **UI does not expose a download button today.**

**Template download (API):** `GET /api/v1/upload/templates/{file_type}` — **UI does not expose download buttons today.**

### 18.4 QA Excel templates (paths)

Directory: `docs/qa/upload-templates/`

| Template file | Entity / use | Load path today |
|---------------|--------------|-----------------|
| products_upload_template.xlsx | cdm_product | SQL seed / Odoo sync |
| work_centers_upload_template.xlsx | cdm_work_center | SQL / Odoo |
| bom_routing_upload_template.xlsx | BOM + routing | SQL / Odoo |
| mrp_orders_upload_template.xlsx | cdm_manufacturing_order | SQL / Odoo |
| demand_lines_upload_template.xlsx | cdm_demand_line | SQL / Odoo |
| suppliers_upload_template.xlsx | cdm_supplier | SQL / Odoo |
| customers_upload_template.xlsx | cdm_customer | SQL / Odoo |
| inventory_upload_template.xlsx | inventory position | SQL seed |
| supply_orders_upload_template.xlsx | cdm_supply_order | SQL / Odoo |
| operators_upload_template.xlsx | cdm_operator | SQL seed |
| **project_plan_upload_template.xlsx** | Project plan | **UI — Schedule upload** |
| tariff_matrix_upload_template.xlsx | Tariff shock | Parser only — **no upload API** |
| odoo_sync_entities_reference.xlsx | Field map reference | Not an upload |

Star Trans CSV originals: `docs/demo-data/startrans/*.csv` · Spec: `docs/demo-data/STARTRANS-CSV-UPLOAD-SPEC.md`.

**Recommended load order:** Products → WC → Operators → Customers → Suppliers → BOM/routing → Inventory → Supply → MOs → Demand → Project plan Excel.

### 18.5 Project plan Excel (Schedule — live UI upload)

Schema: `docs/PROJECT-PLAN-EXCEL-SCHEMA.md` · cap-svc.

| Rule | Value |
|------|--------|
| Format | **.xlsx only** (CSV rejected in UI) |
| Max size | **5 MB** |
| Sheet | First worksheet (prefer name `ProjectPlan`) |
| Mode | Create new plan / Update existing (new version) |

| Column | Required | Type | Rules |
|--------|----------|------|-------|
| PLAN_CODE | Yes | text | Same on every row |
| PLAN_NAME | Yes | text | Same on every row |
| MO_ID | Yes | text | Must exist in DB (`MO-ST-*` after Star Trans seed) |
| OPERATION_SEQUENCE | Yes | int | Unique per MO_ID in file |
| OPERATION_NAME | Yes | text | Gantt label |
| WORK_CENTER_CODE | Yes | text | Must match WC master (e.g. WC001–WC003) |
| START_HOUR | Yes | number | Hours from horizon start |
| DURATION_HOURS | Yes | number | Must be > 0 |
| STATUS | No | text | planned / frozen / disrupted / ai_suggested |
| NOTES | No | text | Optional |

**UI labels:** **Upload Project Plan** · **Create new plan** · **Update existing plan (new version)** · **Upload New Plan** / **Upload New Version** · **Activate** · view radio **Uploaded project plan** · **View Excel schema**.

**UI errors:** Select an Excel (.xlsx) file first · Select an existing plan to update · API `details[]` (up to 8 shown).

### 18.6 Phase 8 CSV exports (Control Tower / MPS)

| Endpoint | Filename | Columns | Notes |
|----------|----------|---------|-------|
| `GET /api/v1/phase8/export/risk-queue.csv` | risk_queue.csv | mo_id, product, customer, feasibility_score, primary_constraint, status | Demo rows when no live queue injected |
| `GET /api/v1/phase8/export/mps.csv` | mps_export.csv | product_id, period, demand, supply, projected_on_hand | Demo period schedule |

Kong route: `/api/v1/phase8` (R2 + deploy/star-trans). UI download buttons for these exports are **not** first-class on Control Tower today — call API or wire in 8B+.

### 18.7 Excel error handling — planner checklist

1. Confirm file extension and UTF-8 CSV (BOM OK — `utf-8-sig`).
2. Match **upload-svc** headers (not necessarily QA template display names — check README sheet).
3. Upload masters before BOM/sales (referential stage).
4. For project plan: seed MOs first; convert CSV→XLSX (`scripts/convert-project-plan-to-xlsx.ps1`).
5. If Upload Center unavailable: **"Upload service unavailable — ensure upload-svc is running on :8120"**.
6. Remember: wizard green ≠ Control Tower populated — still need seed or Odoo sync.

---

## 19. Odoo Master Chapter

Entity sync map, write-back safety, mock vs PH1-02 honesty.

### 19.1 Role of Odoo in IPE

```
Odoo (SoR) ──15min / Sync now──► Connector ──► CDM (Postgres)
                                      ▲
IPE decisions (schedule/resolution) ──┘ write-back (Wave 1: dry-run / MOCK only)
```

IPE does **not** replace Odoo master data. Empty Control Tower usually means no seed and no successful sync.

### 19.2 Entity sync map (Odoo → IPE)

Source of truth: `docs/integration/ODOO-19-FIELD-MAPPING.md` ← `connector` mapper + sync_engine. Frequency: **every 15 minutes** scheduled + on-demand **Sync now**.

| # | Odoo model | CDM | Direction | Filter highlights |
|---|------------|-----|-----------|-------------------|
| 1 | mrp.production | cdm_manufacturing_order | Read (+ write-back dates) | state not cancel |
| 2 | mrp.bom | cdm_bill_of_material | Read | active=True |
| 3 | mrp.bom.line | cdm_bom_line | Read | via BOM lines |
| 4 | mrp.routing.workcenter | cdm_routing_operation | Read | via BOM operation_ids |
| 5 | mrp.workcenter | cdm_work_center | Read | active=True |
| 6 | product.product | cdm_product | Read | active=True |
| 7 | res.partner | cdm_customer | Read | customer_rank > 0 |
| 8 | res.partner | cdm_supplier | Read | supplier_rank > 0 |
| 9 | sale.order.line | cdm_demand_line | Read | state in sale/done |
| 10 | purchase.order.line | cdm_supply_order | Read | state in purchase/done |
| 11 | stock.quant | updates product safety_stock proxy | Read | internal locations, qty>0 |
| 12 | PO + picking | cdm_lead_time_history | Read | receipts last 90d |
| 13 | mrp.production (write) | approved schedule dates | **IPE → Odoo** | Event-driven (not batch) |

**Odoo 17 vs 19:** Connector reads both `date_planned_start`/`date_start` and `date_planned_finished`/`date_finished`. Capacity: Odoo 17 `default_capacity` vs Odoo 19 `time_efficiency`.

### 19.3 UI — Connections & Config

| Screen | Route | Key actions |
|--------|-------|-------------|
| Odoo Connections | `/platform/odoo-config` | Add · Save · Test Connection · Activate · Sync now · Activity log |
| Odoo Configuration (versions) | `/platform/odoo-config/versions` | Entity mappings · Test · Save · Rollback |

**Connection fields:** Display name, Odoo URL, Database name, Username, Password (**required on create**), Sync interval 5/15/30/60 min (default 15), Environment Production/Staging.

**APIs:** `/api/v1/erp/connections*`, `/api/v1/admin/odoo-config`, `/api/v1/sync/status`.

### 19.4 Write-back safety (Phase 8 Wave 1)

Source: `dpe-svc/app/core/phase8/write_back.py`, API `phase8_production.py`, migration **070** `cdm_write_back_log`.

| Step | API | Default behaviour |
|------|-----|-------------------|
| Propose | `POST /api/v1/phase8/write-back` | `dry_run=true` → status `dry_run`, preview only, **never hits live Odoo** |
| List | `GET /api/v1/phase8/write-back` | Tenant-scoped proposals |
| Approve | `POST /api/v1/phase8/write-back/{id}/approve` | Role check; `execute=false` → pending/queue message |
| Execute (opt-in) | same + `execute=true` | If flag `ipe.odoo.live_writeback` false → queued, **not sent**. If flag true → still **MOCK** (`mock_odoo=true`, `is_live=false`, message cites PH1-02) |

**Request fields (propose):** entity_type (default `mrp.production`), entity_id, field_name (default `date_planned_start`), old_value, new_value, action, requested_by, user_role, financial_impact, dry_run, payload.

**Role gate:** `AgentRoleContext.can_execute(user_role, "approve_resolution", financial_impact)` — see [§4](#4-resolution-center).

**Rollback window (mock execute):** `rollback_deadline` = now + 4 hours (recorded on mock execute).

### 19.5 What works on mock-odoo vs blocked on PH1-02

| Capability | mock-odoo-api / seed | Live customer Odoo (PH1-02) |
|------------|----------------------|-----------------------------|
| Read sync entities 1–12 | **Works** against mock or SQL seed | **Blocked** until staging credentials + checklist |
| Control Tower queue from synced MOs | Works with seed/mock data | Needs live staging |
| Schedule / resolution approve in IPE | Works in IPE DB | Works in IPE; write to Odoo blocked |
| Write-back dry-run / approve queue | **Works** (Phase 8) | Same APIs; live send blocked |
| Live write-back to mrp.production dates | **MOCK only** even if flag flipped in Wave 1 | **OPEN** — PH1-02 |
| A15 3-way match / PO write-back | MOCK | OPEN |
| IoT / Digital Gemba live | STUB (`iot_live=false`) | OPEN |
| Accounting / FX live | Not claimed | OPEN |

**Do not claim:** “Odoo is connected in production” or “schedule changes appear in customer Odoo” until PH1-02 closes.

### 19.6 Failure / delay impact

| Symptom | Likely cause | Resolve |
|---------|--------------|---------|
| Control Tower empty + Open Odoo Settings | No CDM MOs | Seed or Sync now / fix connection |
| Sync badge stale (>30 min) | Connector/Odoo down | Activity log; Test Connection; restart connector |
| Outcomes Odoo sync health degraded | Same | Check `/sync/status` |
| Write-back `insufficient_authority` | Role vs financial_impact | Escalate to supervisor/manager |
| Write-back queued not sent | live_writeback=false or PH1-02 | Expected in Wave 1 |
| Login/API 502 | Kong upstream | Recreate Kong / check service health |

### 19.7 Pre-go-live checklist (from field-mapping doc)

Odoo modules: mrp, sale, purchase, stock · sample MOs/BOMs/WCs/SOs · XML-RPC reachable · API user READ on listed models + WRITE on mrp.production · version 17/19 documented · custom fields noted. Full checklist: `docs/integration/ODOO-19-FIELD-MAPPING.md`.

---

## 20. E2E Workflow Chapter

End-to-end processes with decision points, Excel/Odoo fit, prerequisites, and completion criteria. **Flags stub/mock/deferred plainly.**

### 20.1 Prerequisites (all flows)

1. Stack up: `docker compose -f infrastructure/docker/docker-compose.release2.yml up -d` (or project equivalent).
2. Web **http://localhost:8082** · Kong **http://localhost:8000**.
3. Seed: `.\scripts\seed-data.ps1` (+ Star Trans overlay for demo MOs).
4. Login: e.g. `Ahmed@nour` / `admin`.
5. Optional: Ollama for narratives; if down → amber degrade banner (planning continues).

### 20.2 Order-to-cash (intelligence layer view)

**Intent:** Confirmed demand → feasible production → schedule → delivery confidence → customer visibility.

```
[Odoo SO confirm / seed demand]
        │
        ▼
Demand classify (A1) → Material pATP (A2) → Capacity (A3) → Feasibility (A4)
        │
        ├─ score ≥90 + autonomous → auto_confirm path
        ├─ score 70–89 → planner queue (Control Tower)
        └─ score <70 → Resolution (A5) → Approve
        │
        ▼
Cockpit Promise / MPS / MRP → Schedule regenerate or project-plan Excel
        │
        ▼
Shop Floor progress (client/local) · Customer Portal confidence (A8)
        │
        ▼
OTD / Outcomes capture  ·  Write-back schedule to Odoo = MOCK/PH1-02
```

| Step | Screen / system | Excel / Odoo |
|------|-----------------|--------------|
| Demand in | Seed / Odoo SO sync / sales_orders upload validate | Odoo sale.order.line · Excel sales_orders |
| Triage | Control Tower | CT export CSV (phase8) |
| Decide | Resolution | Role thresholds |
| Plan | Cockpit + Schedule | Project plan xlsx |
| Inform customer | Customer Portal | — |
| Close loop ERP | phase8 write-back | **Dry-run/MOCK** |

**Completion criteria:** MO feasible or approved scenario; schedule active; portal shows order (if data present). **Not complete:** live Odoo date write.

**Branches:** Empty queue → seed/Odoo; Reject button → noop (do not rely); VERSION_CONFLICT on schedule approve → reload and retry.

### 20.3 Weekly planning cycle

| # | Action | Screen | Completion signal |
|---|--------|--------|-------------------|
| 1 | Review health | Planning Cockpit | Health tiles load (or offline shell acknowledged) |
| 2 | Update MPS | Cockpit **Update MPS** | JSON result (UI does not persist=true) |
| 3 | Run MRP | **Run MRP** | JSON |
| 4 | Promise check | **Check ATP/CTP** | JSON |
| 5 | RCCP / Level | **RCCP** · **Level production** | JSON |
| 6 | Demand sense | Demand **Run sense cycle** | Forecast chart |
| 7 | What-if | Scenario Workbench (≤3 compare) | Simulated KPIs (baseline hardcoded) |
| 8 | Solve schedule | Schedule **Regenerate schedule** | Gantt populated |
| 9 | Optional upload | **Upload Project Plan** | Plan active + Uploaded view |
| 10 | Supplier/inventory | Supply Chain tabs | Plans / scorecards |

**Excel fit:** demand_forecast / sop_sales_input (Phase 8 validate); project plan xlsx; MPS export CSV.  
**Odoo fit:** overnight sync refreshes MOs/inventory before Monday cockpit.

### 20.4 Crisis / War Room

| # | Action | Screen | Notes |
|---|--------|--------|-------|
| 1 | Detect disruption | Ops Live alerts / War Room KPIs | Offline shell if API down |
| 2 | Optional activate | Ops Live **Activate War Room** | Different API from War Room page |
| 3 | Impact | War Room events + MO table | Revenue at risk |
| 4 | Mitigate | Mitigation scenarios | **Assign Task = UI noop** |
| 5 | Resolve MOs | Control Tower / Resolution | Approve real API |
| 6 | Andon | Operations Deep **Trigger Andon** / board | In-memory caveat / Spec 029 DB path |
| 7 | Digital twin | Schedule Digital Twin disrupt | network-svc |
| 8 | Chaos cost | Cost of Chaos / OTD | Soft-empty OK |

**Completion:** Approved mitigation path + risk queue reduced. **Not:** Slack/Teams guaranteed without webhook config; Assign Task persistence.

### 20.5 Autonomous overnight → morning triage

```
Night: agents score / Pulse auto-actions (where autonomy allows)
        │
Morning: Intelligence → Today's Pulse  →  Control Tower  →  Ops Live
        │
        └─ Amber Ollama banner? Narratives rule-based; scores still material-driven footnote
```

| Autonomy mode (Admin) | Behaviour |
|-----------------------|-----------|
| shadow | Observe / suggest; no auto-confirm expectation for demos |
| suggest | Queue recommendations |
| autonomous | High-score auto_confirm path (server thresholds) |

**Completion:** Pulse reviewed; at-risk MOs owned. Flag offline shells if APIs down.

### 20.6 S&OP (honest stage-gate)

| Layer | What exists | What does **not** |
|-------|-------------|-------------------|
| Analysis | S&OP Deep tools (financial/rolling/shaping/portfolio) — raw JSON | Interactive stage-gate governance UI (**deferred**) |
| Report | S&OP Report **Generate** + **Export** JSON | PDF export |
| Executive | S&OP gap `POST /sop/solve`, P&L views | Certified commercial sign-off |
| Excel | sop_sales_input upload type (validate) | Full S&OP workbook round-trip UI |
| Horizons | Cascade / escalate JSON | Automatic cross-horizon locking UI |

**Monthly routine:** S&OP Deep → Horizons → Executive + S&OP Report → OTD/Outcomes → AI Trust. Treat as **analysis scaffold**, not closed-loop IBP governance.

### 20.7 Upload → agent chain

```
Upload Center phases 1–5 (validate + wizard agents A1–A7 labels)
        ≠
CDM population (seed / Odoo)
        →
Kafka agent pipelines (when services consume CDM events)
        →
Control Tower / Pulse / Copilot
```

Phase 8 types (`demand_forecast`, `quality_results`, `sop_sales_input`) tag A1/A4/A10/A14 — same honesty: **validation ≠ CDM insert** in Wave 1 Upload Center.

**Completion of onboarding wizard:** Phase 5 message **"All 14 files loaded. IPE agents are now active."** — means wizard state complete, **not** that plant data is in Postgres.

### 20.8 Decision-point cheat sheet

| Decision | Where | If Yes | If No / blocked |
|----------|-------|--------|-----------------|
| Feasibility ≥90 + autonomous | fea-svc | auto_confirm | else queue/resolution |
| Approve scenario | Resolution / CT inline | Optimistic lock approve | Reject noop; conflict → retry |
| Financial impact > role max | Phase 8 roles | Escalate | insufficient_authority |
| Live Odoo write | phase8 execute | MOCK message | PH1-02 OPEN |
| Ollama up? | ai-status | LLM narratives | Amber banner / rule-based |
| Enterprise tools via Kong R2 | M7–M9 | May be offline | Call dpe-svc direct / accept unavailable |

---

*Grounded in `apps/web` routes/pages/i18n, `upload-svc` validator/wizard, `connector` Odoo map, `dpe-svc` phase5/7/8, and program honesty in `FINAL-PROGRAM-STATUS.md`. Mock, stub, deferred, offline-shell, and PH1-02 items are stated plainly. Overview: [`USER-GUIDE.md`](./USER-GUIDE.md) · Screen index: [`USER-GUIDE-BY-SCREEN.md`](./USER-GUIDE-BY-SCREEN.md).*

