# IPE Phase 2 — Cursor Implementation Guide

> **⚠️ Reconciliation (2026-07-10)**  
> This guide is the **original execution reference**. Before implementing, read:
> - **`docs/PHASE2-SPRINT-PLAN.md`** — reconciled sprint order, stale assumptions, Spec 017 conflicts  
> - **`specs/018-phase2-release2/tasks.md`** — trackable sprint backlog  
>
> **Key deltas vs guide as-written:**
> - Alembic head is **038** (not 036); new migrations start at **039**  
> - Copilot is **already in R1 nav** (W1-01 done)  
> - `kong.release1.yml` does not exist — use `kong.yml` as source  
> - Profile file: `apps/web/src/lib/releaseProfile.ts` (not `config/releaseProfiles.ts`)  
> - **Sprint 12 SAP B1 CUT** per Spec 017  
> - Demand: **SES-first** per Spec 017 (not full Prophet/LSTM initially)  
> - **Execute W1-03–08 (Wave 1) before or parallel to Sprint 1**

**Version:** 1.0  
**Date:** July 2026  
**Workspace:** `E:\AISOP\ipe`  
**Authority:** PRD-IPE-COMPREHENSIVE-AS-IS.md + Phase 2 Proposal v1.0  
**Target tag:** v9.1.0-r2

---

## How to Use This Document

This file is the engineering execution plan for IPE Phase 2. It maps every sprint from the Phase 2 Proposal to concrete code tasks within the existing IPE codebase.

**For Cursor:** Open this file in your workspace. Use the sprint-level prompts at the end of each section to drive implementation. Each prompt is self-contained with file paths, acceptance criteria, and references to existing code.

**Conventions:**
- `services/<name>/` — backend Python service (FastAPI)
- `apps/web/` — React frontend (Vite + TypeScript + Tailwind)
- `infrastructure/docker/` — Docker Compose files and Kong configs
- `migrations/versions/` — Alembic migrations (shared across services)
- `docs/` — documentation
- `tests/` — per-service test directories

---

## Current State Summary (Pre-Phase 2)

| Dimension | As-Is (v9.0.0-r1) |
|-----------|-------------------|
| Release profile | `release1` — 8 containers: db, redis, kong, dpe-svc, fea-svc, cap-svc, mat-svc, connector |
| Frontend profile | `VITE_RELEASE_PROFILE=release1` — Planning (3 tabs), Command Center, Platform |
| Copilot | `nlp-svc` exists at `:8007` — hidden from R1 nav. 4 agent roles. Ollama/OpenRouter/Anthropic. |
| Demand | `demand-svc` exists at `:8040` — SES/Prophet/LSTM. Not in R1 compose. |
| Scenarios | `scenario-svc` exists at `:8050` — what-if sandbox. Not in R1 compose. |
| Arabic | `ar.json` covers Control Tower + nav. 4 screens. Needs 8+ for R2. |
| Kong routes | `kong.release1.yml` — subset. Full routes in `kong.yml`. |
| Tests | 870+ backend, 28 frontend Vitest, 4 Playwright specs |
| Migrations | 001–036 applied |
| Odoo connector | 16/16 FRs. XML-RPC. Write-back. DQ flags. Post-sync rescore. |

---

## Phase 2 Target State (v9.1.0-r2)

| Dimension | Target |
|-----------|--------|
| Release profile | `release2` — 11-12 containers: R1 + nlp-svc, demand-svc, scenario-svc, (optional Ollama) |
| Frontend profile | `VITE_RELEASE_PROFILE=release2` — adds Copilot, Demand, Scenarios tabs |
| Copilot | Visible in R2 nav. Connected to live planning data. Shadow mode default. |
| Demand | Visible in R2 nav. SES forecaster on Odoo sales history. Forecast overlay on Control Tower. |
| Scenarios | Visible in R2 nav. What-if sandbox with KPI delta. |
| Arabic | 8+ screens: Control Tower, Resolution, Schedule, Command Center, Admin, login, errors, nav |
| Kong routes | `kong.release2.yml` — R1 routes + nlp-svc, demand-svc, scenario-svc |
| SAP B1 connector | Scaffold or functional (pipeline-dependent) |
| Multi-tenant ops | Cross-tenant sync dashboard, health scores |
| OTD analytics | Trend, root cause, cost-of-chaos, executive PDF export |
| VM requirement | 16GB RAM (with Copilot/Ollama) or 8GB (without, using cloud Claude API) |

---

## Sprint 1 — Environment Setup + Release 2 Profile

### Tasks

#### 1.1 Create Release 2 Docker Compose

**File:** `infrastructure/docker/docker-compose.release2.yml`

Create a new compose overlay that extends the R1 profile with nlp-svc, demand-svc, and scenario-svc.

```yaml
# Extends docker-compose.yml with R2 services
# Usage: docker compose -f docker-compose.yml -f docker-compose.release2.yml up -d

services:
  nlp-svc:
    # ... inherit from base compose, expose :8007
  demand-svc:
    # ... inherit from base compose, expose :8040  
  scenario-svc:
    # ... inherit from base compose, expose :8050
```

**Reference:** `infrastructure/docker/docker-compose.yml` (base), `docker-compose.demo.yml` (overlay pattern)

#### 1.2 Create Release 2 Kong Routes

**File:** `infrastructure/docker/kong.release2.yml`

Extend `kong.release1.yml` with routes for:
- `/api/v1/copilot` → nlp-svc:8007
- `/api/v1/nlp` → nlp-svc:8007
- `/api/v1/demand` → demand-svc:8040
- `/api/v1/scenario` → scenario-svc:8050

**Reference:** `infrastructure/docker/kong.release1.yml`, `infrastructure/docker/kong.yml` (full routes)

#### 1.3 Create Release 2 Frontend Profile

**File:** `apps/web/src/config/releaseProfiles.ts`

Add `release2` profile that includes everything in `release1` plus:
- Copilot tab in nav
- Demand tab under Planning
- Scenarios tab under Planning

**Reference:** Existing `release1` profile definition. Search for `VITE_RELEASE_PROFILE` in `apps/web/`.

#### 1.4 Create Release 2 Deploy Script

**File:** `scripts/deploy-release2.ps1` (and `deploy-release2.sh` for Linux)

Mirror `deploy-release1.ps1` but use `docker-compose.release2.yml` overlay.

#### 1.5 Create Release 2 Smoke Test

**File:** `scripts/release2-smoke.ps1`

Extend `release1-smoke.ps1` with health checks for nlp-svc, demand-svc, scenario-svc.

### Acceptance Criteria
- `docker compose -f docker-compose.yml -f docker-compose.release2.yml up -d` starts all 11-12 containers
- All services healthy via `/healthz`
- Kong routes nlp, demand, scenario endpoints correctly
- Frontend with `VITE_RELEASE_PROFILE=release2` shows Copilot + Demand + Scenarios in nav
- `release2-smoke.ps1` passes

### Cursor Prompt — Sprint 1

```
I'm implementing IPE Release 2 profile. The workspace is E:\AISOP\ipe.

Current state:
- Release 1 compose: infrastructure/docker/docker-compose.release1.yml (pattern reference)
- Release 1 Kong: infrastructure/docker/kong.release1.yml
- Release 1 deploy: scripts/deploy-release1.ps1
- Release 1 smoke: scripts/release1-smoke.ps1
- Release 1 frontend profile: apps/web/src/ (search for VITE_RELEASE_PROFILE)
- Full compose with all services: infrastructure/docker/docker-compose.yml
- Full Kong routes: infrastructure/docker/kong.yml

Tasks:
1. Create infrastructure/docker/docker-compose.release2.yml — overlay that adds nlp-svc (:8007), demand-svc (:8040), scenario-svc (:8050) to the R1 stack
2. Create infrastructure/docker/kong.release2.yml — add routes for /api/v1/copilot, /api/v1/nlp, /api/v1/demand, /api/v1/scenario
3. Update the frontend release profile system to add 'release2' that includes Copilot, Demand, and Scenarios tabs in the nav
4. Create scripts/deploy-release2.ps1 mirroring deploy-release1.ps1 pattern
5. Create scripts/release2-smoke.ps1 extending release1-smoke.ps1 with nlp-svc, demand-svc, scenario-svc health checks

Follow existing code patterns exactly. Do not modify release1 files — create new release2 files.
```

---

## Sprint 2 — Copilot Integration with Live Planning Data

### Tasks

#### 2.1 Connect Copilot to Planning Data Sources

**Files:**
- `services/nlp-svc/app/core/copilot_tools.py` — tool registry
- `services/nlp-svc/app/core/orchestrator.py` — LLM routing

The Copilot (nlp-svc) already has a tool registry with 4 agent roles. For R2, extend the tools to query live planning data:

| Tool | Data Source | API Call |
|------|------------|----------|
| `get_mo_status` | dpe-svc | `GET /api/v1/dashboard/mos` |
| `get_feasibility_queue` | fea-svc | `GET /api/v1/feasibility/queue` |
| `get_schedule` | cap-svc | `GET /api/v1/capacity/schedule/active` |
| `get_otd_metrics` | dpe-svc | `GET /api/v1/dashboard/analytics` |
| `get_material_availability` | mat-svc | `GET /api/v1/material/check-availability` |
| `get_sync_status` | connector | `GET /api/v1/sync/status` |
| `get_resolution_scenarios` | dpe-svc | `GET /api/v1/resolution/scenarios/{mo_id}` |

#### 2.2 Configure Shadow Mode Default

**File:** `services/nlp-svc/app/core/copilot_agent.py`

Ensure the Copilot operates in shadow mode by default — it suggests actions but does not execute them. The planner must approve any schedule change or write-back.

#### 2.3 Configure LLM Fallback Chain

**File:** `services/nlp-svc/app/core/llm_client.py`

Ensure the LLM fallback chain works for R2 deployment:
1. Anthropic Claude API (if `ANTHROPIC_API_KEY` set)
2. OpenRouter (if `OPENROUTER_API_KEY` set)
3. Ollama local (if `OLLAMA_BASE_URL` reachable)
4. Graceful error message if none available

#### 2.4 Frontend Copilot Panel

**File:** `apps/web/src/components/CopilotPanel.tsx` (or equivalent)

Verify the Copilot panel:
- Sends `X-Tenant-ID` header from JWT
- Handles 300s timeout (Kong upstream config)
- Displays structured responses (not raw LLM output)
- Shows agent role selector (planner, supervisor, executive, admin)
- Arabic support in chat interface

### Acceptance Criteria
- Planner can ask "What is blocking MO-ST-001?" and get a structured response with data from fea-svc
- Copilot queries live planning data (not demo seed)
- Shadow mode: Copilot suggests but does not execute
- LLM fallback chain works: cloud → local → error
- 300s timeout handled gracefully in UI

### Cursor Prompt — Sprint 2

```
I'm connecting the IPE Copilot (nlp-svc) to live planning data for Release 2.

Current state:
- nlp-svc exists at services/nlp-svc/ with copilot_tools.py, orchestrator.py, llm_client.py, copilot_agent.py
- Planning services expose APIs: dpe-svc (:8001), fea-svc (:8004), cap-svc (:8003), mat-svc (:8002), connector (:8009)
- API routes documented in docs/api-reference.md and docs/api/*.md

Tasks:
1. In services/nlp-svc/app/core/copilot_tools.py — add tools that call planning service APIs:
   - get_mo_status → GET dpe-svc:8001/api/v1/dashboard/mos
   - get_feasibility_queue → GET fea-svc:8004/api/v1/feasibility/queue
   - get_schedule → GET cap-svc:8003/api/v1/capacity/schedule/active
   - get_otd_metrics → GET dpe-svc:8001/api/v1/dashboard/analytics
   - get_material_availability → GET mat-svc:8002/api/v1/material/check-availability
   - get_sync_status → GET connector:8009/api/v1/sync/status
   - get_resolution_scenarios → GET dpe-svc:8001/api/v1/resolution/scenarios/{mo_id}

2. In copilot_agent.py — ensure shadow_mode=True by default (suggest only, no auto-execute)

3. In llm_client.py — verify fallback chain: Anthropic → OpenRouter → Ollama → graceful error

4. Add tests in services/nlp-svc/tests/ for each new tool (mock HTTP calls to planning services)

Each tool should: accept tenant_id, make authenticated HTTP call, parse response, return structured data for LLM context. Use httpx or aiohttp consistent with existing code patterns.
```

---

## Sprint 3 — Demand Sensing Activation

### Tasks

#### 3.1 Connect Demand Service to Odoo Sales Data

**Files:**
- `services/demand-svc/app/core/forecaster.py` — SES/Prophet/LSTM factory
- `services/demand-svc/app/api/v1/demand.py` — API endpoints

The demand-svc already has forecaster implementations. For R2:
1. Feed it Odoo sales order history from `cdm_demand_line` (synced by connector)
2. Train SES forecaster on 4-8 quarters of history
3. Generate short-term forecast (7/14/30 day horizon)
4. Expose forecast via API for Control Tower overlay

#### 3.2 Forecast Overlay on Control Tower

**File:** `apps/web/src/pages/Planning/ControlTower.tsx` (or equivalent)

Add a forecast overlay widget to Control Tower:
- Shows predicted demand for next 7/14/30 days
- Compares to current MO capacity
- Highlights demand-supply gaps
- Uses data from `GET /api/v1/demand/forecast`

#### 3.3 Demand Tab in R2 Nav

**File:** `apps/web/src/pages/Planning/Demand.tsx`

Create or enable the Demand tab with:
- Forecast chart (line chart with confidence bands)
- Product-level breakdown
- Forecast accuracy tracking (MAPE)
- Historical vs predicted comparison

### Acceptance Criteria
- Demand forecast generated from Odoo sales history
- Forecast visible on Control Tower as overlay
- Demand tab shows forecast chart with confidence bands
- MAPE tracked for forecast accuracy measurement

### Cursor Prompt — Sprint 3

```
I'm activating demand sensing for IPE Release 2.

Current state:
- demand-svc exists at services/demand-svc/ with forecaster.py (SES/Prophet/LSTM factory)
- Odoo sales orders sync to cdm_demand_line via connector
- Control Tower page at apps/web/src/pages/Planning/ (find exact file)
- demand-svc API at :8040, routes in services/demand-svc/app/api/v1/

Tasks:
1. In services/demand-svc/app/core/forecaster.py — ensure SES forecaster can:
   - Query cdm_demand_line for historical demand (4-8 quarters by product)
   - Generate 7/14/30 day forecast with confidence bounds
   - Fall back to simple SES when Prophet/LSTM libs unavailable
   
2. In services/demand-svc/app/api/v1/demand.py — ensure endpoints:
   - GET /api/v1/demand/forecast?product_id=X&horizon=14 returns forecast with bounds
   - GET /api/v1/demand/accuracy returns MAPE metrics
   
3. In apps/web/ — add demand forecast overlay to Control Tower dashboard:
   - Small chart widget showing predicted vs capacity for next 14 days
   - Highlight demand-supply gaps in red
   - Data from demand-svc API

4. In apps/web/ — create or enable Demand tab page:
   - Line chart with forecast + confidence bands (use recharts, already in deps)
   - Product selector
   - Horizon toggle (7d/14d/30d)
   - MAPE accuracy display

5. Add tests in services/demand-svc/tests/ for forecaster with mock demand data
```

---

## Sprint 4 — Scenario Workbench Activation

### Tasks

#### 4.1 Connect Scenario Service to Planning Data

**Files:**
- `services/scenario-svc/app/api/v1/scenarios.py`
- `services/scenario-svc/app/core/simulator.py`

The scenario-svc already exists. For R2:
1. Accept what-if parameters: demand change %, supplier delay days, capacity reduction %
2. Clone current planning state
3. Re-run feasibility scoring on modified state
4. Return KPI delta (OTD change, cost change, capacity utilisation change)

#### 4.2 Scenarios Tab in R2 Nav

**File:** `apps/web/src/pages/Planning/Scenarios.tsx`

Create or enable Scenarios tab:
- Parameter input form (demand %, supplier delay, capacity change)
- "Simulate" button triggers scenario-svc
- Results panel: side-by-side KPI comparison (baseline vs scenario)
- Save/compare multiple scenarios

### Acceptance Criteria
- User can model "+10% demand" and see cascade impact
- User can model "supplier X delayed 2 weeks" and see material impact
- KPI delta displayed clearly (OTD change, cost change)
- Multiple scenarios can be saved and compared

### Cursor Prompt — Sprint 4

```
I'm activating the scenario workbench for IPE Release 2.

Current state:
- scenario-svc exists at services/scenario-svc/ with API endpoints and simulator
- Planning data available via dpe-svc, fea-svc, cap-svc, mat-svc APIs
- Frontend at apps/web/

Tasks:
1. In services/scenario-svc/ — ensure the simulator can:
   - Accept parameters: demand_change_pct, supplier_delay_days, capacity_reduction_pct
   - Clone current planning state (feasibility scores, schedule, material availability)
   - Re-score feasibility on modified parameters
   - Return KPI delta: otd_change, cost_delta, capacity_utilisation_change
   
2. In services/scenario-svc/app/api/v1/scenarios.py — endpoints:
   - POST /api/v1/scenario/simulate — accepts parameters, returns KPI delta
   - GET /api/v1/scenario/list — saved scenarios
   - GET /api/v1/scenario/{id} — single scenario details
   
3. In apps/web/ — create or enable Scenarios tab:
   - Parameter input form with sliders/inputs for demand %, delay days, capacity %
   - "Simulate" button calls scenario-svc API
   - Results panel: baseline vs scenario KPIs side by side (use recharts bar chart)
   - Save scenario button, compare up to 3 scenarios

4. Add tests in services/scenario-svc/tests/
```

---

## Sprint 5 — Arabic Expansion (8+ Screens)

### Tasks

#### 5.1 Expand Arabic Translation Keys

**File:** `apps/web/src/i18n/ar.json`

Current coverage: Control Tower + navigation (4 screens). Expand to 8+:

| Screen | Priority | Key Namespace |
|--------|----------|---------------|
| Resolution Center | Must | `resolution.*` |
| Schedule | Must | `schedule.*` |
| Command Center dashboard | Must | `command.*` |
| Admin panel | Must | `admin.*` |
| Login page | Must | `auth.*` |
| Error messages | Must | `errors.*` |
| Copilot chat | Should | `copilot.*` |
| Demand tab | Should | `demand.*` |
| Scenarios tab | Should | `scenarios.*` |

**Reference:** `apps/web/src/i18n/en.json` for full key list.

#### 5.2 RTL Layout Validation

Verify all expanded screens render correctly in RTL:
- Table headers right-aligned
- Form labels right-aligned
- Chart labels readable
- Navigation drawer on correct side
- Numbers remain LTR within RTL context

#### 5.3 Language Toggle

**File:** `apps/web/src/components/Settings/` (or equivalent)

Verify language toggle (Arabic/English) is accessible from:
- User settings panel
- Header quick toggle
- Persists across sessions (localStorage or user preference API)

### Cursor Prompt — Sprint 5

```
I'm expanding Arabic coverage for IPE Release 2 from 4 screens to 8+.

Current state:
- apps/web/src/i18n/ar.json — has Arabic keys for Control Tower + navigation
- apps/web/src/i18n/en.json — has full English keys for all screens
- Tailwind CSS with RTL support

Tasks:
1. In apps/web/src/i18n/ar.json — add Arabic translations for:
   - Resolution Center (all labels, buttons, status values, scenario types)
   - Schedule (all column headers, action buttons, approval workflow labels)
   - Command Center dashboard (all KPI labels, chart titles, alert text)
   - Admin panel (sync config, user management, system settings labels)
   - Login page (form labels, error messages, buttons)
   - All error/toast messages
   - Copilot chat interface (input placeholder, role labels, response headers)
   - Demand tab (chart labels, forecast terms, accuracy labels)
   - Scenarios tab (parameter labels, KPI names, comparison table headers)

2. Review all pages for RTL layout issues:
   - Tables: headers right-aligned, data right-aligned for Arabic text
   - Forms: labels right-aligned, inputs right-aligned
   - Navigation: correct side for RTL
   - Numbers: remain LTR within RTL context (dir="ltr" on numeric elements)

3. Verify language toggle works and persists across sessions

Use professional Arabic manufacturing terminology. Control Tower = برج التحكم, Manufacturing Order = أمر تصنيع, Feasibility = الجدوى, Resolution = الحلول, Schedule = الجدولة, etc. Match existing ar.json terminology.
```

---

## Sprint 6 — OTD Analytics Dashboard

### Tasks

#### 6.1 Backend Analytics API

**File:** `services/dpe-svc/app/api/v1/analytics.py` (or create)

Endpoints:
- `GET /api/v1/analytics/otd/trend` — OTD % over time (daily/weekly/monthly)
- `GET /api/v1/analytics/otd/root-cause` — delay breakdown by cause category
- `GET /api/v1/analytics/otd/cost-of-chaos` — financial impact of delays
- `GET /api/v1/analytics/otd/baseline` — baseline vs current comparison

Data sources: `cdm_manufacturing_order` (planned vs actual dates), `cdm_delay_event` (cause classification).

#### 6.2 Frontend OTD Dashboard

**File:** `apps/web/src/pages/Analytics/OTDDashboard.tsx`

- OTD trend chart (line chart, daily/weekly/monthly toggle)
- Root cause breakdown (bar chart, by delay category)
- Cost of chaos summary ($ by category, 7d/30d toggle)
- Baseline comparison (before IPE vs after)
- PDF export button (use existing report generation pattern)

### Cursor Prompt — Sprint 6

```
I'm building the OTD analytics dashboard for IPE Release 2.

Current state:
- dpe-svc at services/dpe-svc/ handles analytics
- cdm_manufacturing_order table has planned_start_date, actual_start_date, planned_end_date, actual_end_date
- cdm_delay_event table has cause_category, duration_minutes, cost_impact
- Frontend at apps/web/ uses recharts for charts

Tasks:
1. In services/dpe-svc/app/api/v1/ — create analytics endpoints:
   - GET /api/v1/analytics/otd/trend?period=daily&range=30d — returns OTD % per period
   - GET /api/v1/analytics/otd/root-cause?range=30d — returns delay counts by cause category
   - GET /api/v1/analytics/otd/cost-of-chaos?range=30d — returns $ impact by cause
   - GET /api/v1/analytics/otd/baseline — returns pre-IPE baseline vs current OTD

2. In apps/web/ — create OTD Analytics dashboard page:
   - OTD trend line chart (recharts LineChart) with period toggle
   - Root cause bar chart (recharts BarChart) by category
   - Cost of chaos summary cards with 7d/30d toggle
   - Baseline comparison: "Before IPE: X% → After IPE: Y% (improvement: Z%)"
   - Arabic labels from i18n

3. Add route to analytics page in R2 nav profile
4. Add tests for analytics API endpoints
```

---

## Sprint 7 — Admin Odoo Config UI v2

### Tasks

#### 7.1 Self-Service Odoo Configuration

**File:** `apps/web/src/pages/Admin/OdooConfig.tsx`

Partner-friendly configuration wizard:
- Odoo URL input with "Test Connection" button
- Username/password (or API key) with "Save" button
- Database name selector (auto-detected from Odoo)
- Sync schedule config (interval in minutes, default 900)
- Sync now button with progress indicator
- DQ flag dashboard: unresolved flags with resolution guidance
- Sync history: last 10 runs with status, duration, entity counts

#### 7.2 Backend Config API

**File:** `services/connector/app/api/v1/` (extend existing)

Endpoints:
- `POST /api/v1/erp/odoo/test-connection` — test Odoo credentials
- `PUT /api/v1/erp/odoo/config` — save Odoo config to `cdm_tenant.config`
- `GET /api/v1/sync/history` — last N sync runs with details

### Cursor Prompt — Sprint 7

```
I'm building the Admin Odoo config UI v2 for IPE Release 2.

Current state:
- connector service at services/connector/ handles Odoo sync
- cdm_tenant.config JSONB stores Odoo credentials
- Existing API: /api/v1/sync/run, /api/v1/sync/status, /api/v1/sync/data-quality
- Frontend at apps/web/

Tasks:
1. In services/connector/app/api/v1/ — add endpoints:
   - POST /api/v1/erp/odoo/test-connection — test Odoo URL + creds, return success/error
   - PUT /api/v1/erp/odoo/config — save Odoo URL, db, user, password to cdm_tenant.config
   - GET /api/v1/sync/history?limit=10 — return last N sync runs with status, duration, counts

2. In apps/web/ — create Admin Odoo Config page:
   - Connection wizard: URL, DB, username, password inputs
   - "Test Connection" button → calls test-connection API, shows green/red result
   - "Save" button → calls config API
   - Sync schedule: interval input (minutes), "Sync Now" button
   - DQ flags table: unresolved flags from /api/v1/sync/data-quality
   - Sync history table: last 10 runs from /api/v1/sync/history
   - All labels in Arabic (from i18n)

3. Add this page to Admin section in R2 nav
```

---

## Sprint 8 — Multi-Tenant Ops Dashboard

### Tasks

#### 8.1 Cross-Tenant Health API

**File:** `services/dpe-svc/app/api/v1/ops.py` (create)

Admin-only endpoints (require admin role):
- `GET /api/v1/ops/tenants/health` — all tenants with last sync time, sync status, MO count, error count
- `GET /api/v1/ops/tenants/alerts` — sync failures across all tenants (>3 retries)
- `GET /api/v1/ops/tenants/{id}/details` — single tenant deep view

#### 8.2 Frontend Ops Dashboard

**File:** `apps/web/src/pages/Platform/OpsDashboard.tsx`

- Tenant health table: name, last sync, status (green/amber/red), MO count, DQ flag count
- Sync failure alerts: tenants with failed syncs, time since last success
- System health: container status, memory usage, disk usage
- Support queue summary (if Freshdesk integration exists)

### Cursor Prompt — Sprint 8

```
I'm building the multi-tenant ops dashboard for IPE Release 2.

Current state:
- dpe-svc handles admin APIs at services/dpe-svc/
- cdm_tenant table has all tenants
- cdm_sync_run table has sync history per tenant
- cdm_data_quality_flag has DQ flags per tenant
- Frontend at apps/web/

Tasks:
1. In services/dpe-svc/app/api/v1/ — create ops.py with admin-only endpoints:
   - GET /api/v1/ops/tenants/health — all tenants with: last_sync_time, sync_status, mo_count, dq_flag_count, health_score (green/amber/red)
   - GET /api/v1/ops/tenants/alerts — tenants where last sync failed or >1hr since last success
   - Require admin role on all ops endpoints

2. In apps/web/ — create Ops Dashboard page:
   - Tenant health table with color-coded status indicators
   - Alert panel: tenants with sync failures
   - Add to Platform section in nav (admin-only visibility)
   - Arabic labels

3. Add tests for ops endpoints
```

---

## Sprint 9 — Production & Quality Intelligence

### Tasks

#### 9.1 Production Analytics

**File:** `services/cap-svc/app/api/v1/analytics.py` (create)

- `GET /api/v1/capacity/analytics/bottlenecks` — work centres with highest utilisation and delay correlation
- `GET /api/v1/capacity/analytics/changeover` — changeover analysis by product family sequence
- `GET /api/v1/capacity/analytics/utilisation` — shift-level and line-level utilisation trends

#### 9.2 Quality Pattern Analysis (Copilot Tool)

**File:** `services/nlp-svc/app/core/copilot_tools.py`

Add tool: `analyze_quality_patterns` — queries `cdm_delay_event` where cause is quality-related, cross-references with production parameters, returns pattern summary for LLM to narrate.

### Cursor Prompt — Sprint 9

```
I'm adding production and quality intelligence for IPE Release 2.

Tasks:
1. In services/cap-svc/app/api/v1/ — create analytics.py:
   - GET /api/v1/capacity/analytics/bottlenecks — work centres ranked by utilisation + delay correlation
   - GET /api/v1/capacity/analytics/changeover — changeover duration analysis by product family sequence
   - GET /api/v1/capacity/analytics/utilisation — utilisation % by shift, line, period

2. In services/nlp-svc/app/core/copilot_tools.py — add tool:
   - analyze_quality_patterns: queries cdm_delay_event (quality causes), cross-refs production data, returns structured analysis for LLM context

3. Add tests for analytics endpoints and quality tool
```

---

## Sprint 10 — Supply Chain Intelligence

### Tasks

#### 10.1 Supplier Risk Scoring

**File:** `services/mat-svc/app/api/v1/supplier.py` (create or extend)

- `GET /api/v1/material/suppliers/risk` — risk score per supplier based on:
  - Lead time variance (std dev of actual vs promised)
  - Quality rejection rate
  - On-time delivery percentage
  - Concentration risk (% of total spend)

#### 10.2 Inventory Analytics

**File:** `services/mat-svc/app/api/v1/inventory.py` (create or extend)

- `GET /api/v1/material/inventory/classification` — ABC analysis by value
- `GET /api/v1/material/inventory/slow-moving` — items with no demand in N days
- `GET /api/v1/material/inventory/reorder-suggestions` — safety stock recommendations

#### 10.3 Copilot Supply Chain Tools

**File:** `services/nlp-svc/app/core/copilot_tools.py`

Add tools: `get_supplier_risk`, `get_inventory_classification`, `get_reorder_suggestions`

### Cursor Prompt — Sprint 10

```
I'm adding supply chain intelligence for IPE Release 2.

Tasks:
1. In services/mat-svc/app/api/v1/ — add supplier risk and inventory analytics:
   - GET /api/v1/material/suppliers/risk — risk score per supplier (lead time variance, quality, OTD, concentration)
   - GET /api/v1/material/inventory/classification — ABC analysis
   - GET /api/v1/material/inventory/slow-moving?days=90 — items without demand
   - GET /api/v1/material/inventory/reorder-suggestions — safety stock recommendations

2. In services/nlp-svc/app/core/copilot_tools.py — add Copilot tools:
   - get_supplier_risk → calls mat-svc supplier risk API
   - get_inventory_classification → calls mat-svc ABC API
   - get_reorder_suggestions → calls mat-svc reorder API

3. Add tests for supplier risk scoring (mock data) and inventory analytics
```

---

## Sprint 11 — S&OP Synthesis + Automated Reporting

### Tasks

#### 11.1 S&OP Report Generator

**File:** `services/nlp-svc/app/core/sop_report.py` (create)

Automated weekly S&OP report using Copilot:
1. Fetch data from all domains: demand forecast, schedule status, material availability, supplier risk, OTD metrics
2. Construct structured prompt with all data
3. Claude generates executive S&OP narrative identifying top 3-5 decision items
4. Output as structured JSON (for UI rendering) and plain text (for email/PDF)

#### 11.2 Scheduled Report API

**File:** `services/nlp-svc/app/api/v1/reports.py` (create)

- `POST /api/v1/copilot/report/sop` — trigger S&OP report generation
- `GET /api/v1/copilot/report/sop/latest` — get latest generated report

#### 11.3 Frontend Report View

**File:** `apps/web/src/pages/Command/SOPReport.tsx`

- Display latest S&OP report with structured sections
- Download as PDF button
- Arabic rendering of report content

### Cursor Prompt — Sprint 11

```
I'm building automated S&OP synthesis for IPE Release 2.

Tasks:
1. In services/nlp-svc/app/core/ — create sop_report.py:
   - Fetch data from: demand-svc (forecast), cap-svc (schedule/capacity), mat-svc (material/supplier risk), dpe-svc (OTD metrics)
   - Construct structured prompt with all data for Claude
   - Claude generates executive S&OP narrative: top 3-5 decision items, risk register, recommendations
   - Return structured JSON and plain text

2. In services/nlp-svc/app/api/v1/ — create reports.py:
   - POST /api/v1/copilot/report/sop — trigger report generation
   - GET /api/v1/copilot/report/sop/latest — return latest report

3. In apps/web/ — create S&OP Report page in Command Center:
   - Display structured report sections
   - PDF download button
   - Arabic rendering

4. Add tests for report generation with mock data
```

---

## Sprint 12 — SAP Business One Connector Scaffold

### Tasks

#### 12.1 SAP B1 Connector Scaffold

**File:** `services/connector/app/erp/sapb1/` (create directory)

Create the scaffold for SAP Business One integration:
- `client.py` — SAP B1 Service Layer API client (REST)
- `mappers.py` — SAP B1 entity → CDM entity mapping
- `adapter.py` — sync adapter following the same pattern as Odoo adapter

SAP B1 Service Layer API pattern:
- Auth: `POST /Login` with CompanyDB, UserName, Password
- MOs: `GET /ProductionOrders`
- BOMs: `GET /ProductTrees`
- Items: `GET /Items`

#### 12.2 Connector Factory Pattern

**File:** `services/connector/app/erp/base.py`

Ensure the connector uses a factory pattern:
```python
def get_erp_adapter(erp_type: str) -> ERPAdapter:
    if erp_type == "odoo": return OdooAdapter(...)
    if erp_type == "sapb1": return SAPB1Adapter(...)
    raise ValueError(f"Unknown ERP: {erp_type}")
```

`cdm_tenant.config` should include `erp_type` field to select the adapter.

### Cursor Prompt — Sprint 12

```
I'm creating the SAP Business One connector scaffold for IPE Release 2.

Current state:
- Odoo connector at services/connector/app/erp/ (or app/core/) — XML-RPC adapter pattern
- connector/app/erp/base.py likely has base ERPAdapter class

Tasks:
1. Create services/connector/app/erp/sapb1/ directory with:
   - __init__.py
   - client.py — SAP B1 Service Layer REST client (POST /Login, GET /ProductionOrders, etc.)
   - mappers.py — SAP B1 entity → CDM entity mapping (ProductionOrder → cdm_manufacturing_order, etc.)
   - adapter.py — SAPB1Adapter implementing same interface as Odoo adapter

2. Update connector factory to select adapter based on cdm_tenant.config.erp_type:
   - "odoo" → OdooAdapter
   - "sapb1" → SAPB1Adapter

3. Add placeholder tests for SAP B1 mappers

This is scaffold only — no live SAP B1 instance required. The adapter should be structurally complete but tested against mock data.
```

---

## Testing Strategy

### Per-Sprint Test Requirements

| Sprint | Test Type | Target | Files |
|--------|-----------|--------|-------|
| 1 | Smoke | R2 compose health checks | `scripts/release2-smoke.ps1` |
| 2 | Unit | Copilot tools (mock HTTP) | `services/nlp-svc/tests/test_copilot_tools_r2.py` |
| 3 | Unit | Forecaster with mock demand | `services/demand-svc/tests/test_forecaster_r2.py` |
| 4 | Unit | Simulator with mock state | `services/scenario-svc/tests/test_simulator_r2.py` |
| 5 | Manual | Arabic QA with native speaker | Checklist in `docs/qa/arabic-qa-r2.md` |
| 6 | Unit | Analytics API endpoints | `services/dpe-svc/tests/test_analytics_otd.py` |
| 7 | Unit | Config API + test-connection | `services/connector/tests/test_config_api.py` |
| 8 | Unit | Ops dashboard API | `services/dpe-svc/tests/test_ops_dashboard.py` |
| 9 | Unit | Production analytics | `services/cap-svc/tests/test_analytics.py` |
| 10 | Unit | Supplier risk, inventory | `services/mat-svc/tests/test_supplier_risk.py` |
| 11 | Unit | S&OP report generation | `services/nlp-svc/tests/test_sop_report.py` |
| 12 | Unit | SAP B1 mappers | `services/connector/tests/test_sapb1_mappers.py` |

### Frontend Tests

| Sprint | Test | File |
|--------|------|------|
| 1 | R2 nav renders Copilot/Demand/Scenarios | `apps/web/e2e/release2-nav.spec.ts` |
| 5 | Arabic rendering on 8+ screens | `apps/web/e2e/arabic-r2.spec.ts` |
| 6 | OTD dashboard renders charts | `apps/web/src/__tests__/OTDDashboard.test.tsx` |

---

## Migration Plan

### New Migrations Required

| ID | Sprint | Table/Change | Purpose |
|----|--------|-------------|---------|
| 037 | 6 | `cdm_otd_snapshot` | Daily OTD snapshot for trend tracking |
| 038 | 7 | `cdm_tenant.config` schema update | Add `erp_type`, `sync_interval_seconds` fields |
| 039 | 8 | `cdm_tenant_health` | Materialised view for ops dashboard |
| 040 | 10 | `cdm_supplier_score` | Cached supplier risk scores |
| 041 | 11 | `cdm_sop_report` | Generated S&OP reports storage |
| 042 | 12 | SAP B1 field mappings | Add `erp_source_system` to CDM entities |

---

## Environment Variables (New for R2)

| Variable | Service | Required | Default | Description |
|----------|---------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | nlp-svc | For cloud AI | — | Claude API key |
| `OPENROUTER_API_KEY` | nlp-svc | Fallback | — | OpenRouter API key |
| `OLLAMA_BASE_URL` | nlp-svc | For local AI | `http://host.docker.internal:11434` | Ollama endpoint |
| `COPILOT_TIMEOUT_SECONDS` | nlp-svc | No | `300` | LLM response timeout |
| `DEMAND_FORECAST_HORIZON_DAYS` | demand-svc | No | `14` | Default forecast horizon |
| `SOP_REPORT_SCHEDULE` | nlp-svc | No | `0 6 * * 1` | Cron for weekly S&OP (Monday 6 AM) |

Add all to `.env.example` and `.env.template`.

---

## Master Cursor Prompt — Full Phase 2

Use this prompt to give Cursor the complete context before starting any sprint:

```
You are implementing IPE (Intelligent Planning Engine) Release 2. The workspace is at E:\AISOP\ipe.

PROJECT CONTEXT:
- IPE is an AI-powered Advanced Planning & Scheduling platform for MENA manufacturers
- Backend: FastAPI Python services, PostgreSQL 16 with RLS, Alembic migrations
- Frontend: React 18 + Vite 5 + TypeScript + Tailwind + recharts
- Current release: v9.0.0-r1 (Release 1) with 8 containers
- Target: v9.1.0-r2 (Release 2) with 11-12 containers

ARCHITECTURE:
- services/dpe-svc/ (:8001) — auth, dashboard, resolution, analytics, admin, MDR
- services/mat-svc/ (:8002) — material ATP, netting
- services/cap-svc/ (:8003) — scheduling, OR-Tools solver, CPM
- services/fea-svc/ (:8004) — feasibility scoring, WebSocket
- services/nlp-svc/ (:8007) — AI Copilot (hidden in R1, visible in R2)
- services/connector/ (:8009) — Odoo XML-RPC sync, DQ flags, write-back
- services/demand-svc/ (:8040) — demand sensing (not in R1 compose)
- services/scenario-svc/ (:8050) — scenarios (not in R1 compose)
- apps/web/ — React frontend with VITE_RELEASE_PROFILE switching
- infrastructure/docker/ — compose files, Kong configs

KEY FILES:
- infrastructure/docker/docker-compose.yml — base compose
- infrastructure/docker/docker-compose.release1.yml — R1 overlay
- infrastructure/docker/kong.release1.yml — R1 routes
- apps/web/src/i18n/ar.json — Arabic translations
- apps/web/src/i18n/en.json — English translations
- docs/PRD-IPE-COMPREHENSIVE-AS-IS.md — full product reference
- docs/api-reference.md — API index

CONVENTIONS:
- Follow existing code patterns in each service
- Use Pydantic v2 for API schemas
- Use SQLAlchemy for DB queries
- Tests use pytest with fixtures from conftest.py
- Arabic i18n keys follow dot notation: section.subsection.label
- All API routes require JWT auth and X-Tenant-ID header
- RLS enforces tenant isolation at DB level

IMPLEMENTATION GUIDE:
Read docs/PHASE2-IMPLEMENTATION-GUIDE.md for sprint-by-sprint tasks.
Current sprint: [SPECIFY SPRINT NUMBER]
```

---

## File Index — New Files Created in Phase 2

| Sprint | File | Type |
|--------|------|------|
| 1 | `infrastructure/docker/docker-compose.release2.yml` | Config |
| 1 | `infrastructure/docker/kong.release2.yml` | Config |
| 1 | `scripts/deploy-release2.ps1` | Script |
| 1 | `scripts/deploy-release2.sh` | Script |
| 1 | `scripts/release2-smoke.ps1` | Script |
| 6 | `services/dpe-svc/app/api/v1/analytics.py` | API |
| 7 | `apps/web/src/pages/Admin/OdooConfig.tsx` | Frontend |
| 8 | `services/dpe-svc/app/api/v1/ops.py` | API |
| 8 | `apps/web/src/pages/Platform/OpsDashboard.tsx` | Frontend |
| 9 | `services/cap-svc/app/api/v1/analytics.py` | API |
| 10 | `services/mat-svc/app/api/v1/supplier.py` | API |
| 10 | `services/mat-svc/app/api/v1/inventory.py` | API |
| 11 | `services/nlp-svc/app/core/sop_report.py` | Core |
| 11 | `services/nlp-svc/app/api/v1/reports.py` | API |
| 12 | `services/connector/app/erp/sapb1/__init__.py` | Module |
| 12 | `services/connector/app/erp/sapb1/client.py` | Client |
| 12 | `services/connector/app/erp/sapb1/mappers.py` | Mappers |
| 12 | `services/connector/app/erp/sapb1/adapter.py` | Adapter |

---

*End of Phase 2 Implementation Guide. Execute sprint by sprint. Do not skip acceptance criteria.*
