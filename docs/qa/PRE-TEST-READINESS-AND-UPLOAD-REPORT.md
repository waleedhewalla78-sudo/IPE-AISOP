# IPE Pre-Test Readiness & Upload Report

**Date:** 2026-07-12  
**Workspace:** `E:\AISOP\ipe`  
**Stack:** Docker R2 (`docker-compose.release2.yml`), Kong `:8000`, Web UI `:8082`, `AUTH_MODE=local`  
**Tenant:** `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11`  
**Login:** `Ahmed@nour` / `admin`  
**Evidence dir:** `docs/qa/pre-test-2026-07-12/`  
**Templates:** `docs/qa/upload-templates/`

---

## Overall readiness verdict

**CONDITIONAL PASS — engineering stack is testable for CDM / planning / OTD / mock-Odoo flows.**

Core R2 services are up, migration **050** applied, Star Trans seed loaded (10 `MO-ST-*` + extras), Release2 smoke **15/15**, planning UAT **8 PASS / 2 PARTIAL / 0 FAIL**, project-plan `.xlsx` upload **PASS**, mock-Odoo sync **PASS**.

**Not claimed:** live Odoo (PH1-02 / COM), Arabic native COM sign-off (G-R2-04), SOW signatures, OQ-7 pricing. Do not invent those.

---

## 1. System readiness check

### 1.1 Critical services

| Component | Port / path | Status | Notes |
|-----------|-------------|--------|-------|
| Web UI | `:8082` | **UP** healthy | Login page HTTP 200 |
| Kong | `:8000` | **UP** healthy | `/api/v1/health` → dpe |
| PostgreSQL | `:5433` → `ipe_test` | **UP** healthy | `docker-db-1` |
| Redis | `:6380` | **UP** | `PONG` |
| dpe-svc | `:8020` | **UP** | OTD analytics OK |
| fea-svc | `:8004` | **UP** | Queue returns 12 MOs |
| mat-svc | `:8002` | **UP** | Inventory summary OK |
| cap-svc | `:8003` | **UP** | Schedule + project-plan upload |
| res-svc | `:8005` | **UP** | Scenarios present |
| connector | `:8016` | **UP** healthy | Sync + ERP connections (direct) |
| nlp / demand / scenario / sop | `:8007/:8040/:8050/:8110` | **UP** | Smoke OK |
| mock-odoo-api | `:8010` | **UP** healthy | Used for eng sync |
| Keycloak | `:8180` | **UP** | Optional; local auth used |
| Minio / Vault | `:9000/:8200` | **UP** | Infra |

**Not on stock R2 compose (known gaps):** `network-svc`, `alert-svc`, `del-svc`, `rec-svc`, order/procurement/supply/equipment services — War Room / Digital Twin / several supply-chain pages will 404 or empty via Kong.

### 1.2 Migrations & env

| Check | Result |
|-------|--------|
| Alembic head | **050** (`050_erp_connections`) |
| `.env` present | Yes — `IPE_DATABASE_URL`, `IPE_REDIS_URL`, `IPE_KAFKA_*`, `IPE_JWT_SECRET_KEY`, `AUTH_MODE` set |
| Compile / import blockers | None observed on running containers; health returns `status: ok` |

### 1.3 Seed / data state (after this run)

| Entity | Count / note |
|--------|----------------|
| Tenant | 1 (Star Trans overlay applied) |
| Products | 7+ |
| Manufacturing orders | 12 (10 `MO-ST-*` + 2 mock-sync `101`/`102`) |
| Demand lines | ~89 |
| Work centers | 4 |
| Suppliers | 3 |
| Inventory positions | 15+ |
| Users | 3 |

**Seed notes:**
- Initial `seed-data.ps1` hit duplicate-key on `cdm_operator` (partial re-run) — non-blocking; data already present.
- `seed-startrans-demo.ps1` completed successfully (demo graph + overlay + MDR boost).

### 1.4 Readiness blockers (engineering)

| ID | Severity | Blocker | Mitigation for testing |
|----|----------|---------|------------------------|
| B1 | MEDIUM | Kong missing `/api/v1/erp/connections` (Wave 1 UI) | Call connector `:8016` directly |
| B2 | MEDIUM | `/api/v1/admin/odoo-config` shadowed by dpe Kong `/admin` | Direct connector `:8016` |
| B3 | LOW | star-trans sync status was `unknown` before sync | Run `POST /sync/run` with mock-odoo creds (done this run → `success`) |
| B4 | LOW | Odoo test-connection SKIP without live Odoo | Expected until PH1-02; mock-odoo OK for eng |
| B5 | MEDIUM | War Room / Digital Twin / Equipment / Orders / Procurement / Supply Planning not on R2 | Out of R2 scope or need full compose |
| B6 | LOW | Live Copilot chat timeout (UAT-10) | Unit tools OK; needs LLM config |
| B7 | COM | Live Odoo, G-R2-04 Arabic native, OQ-7 | Human / commercial — do not fake |

**Verdict section 1:** Stack is **READY for isolated eng/UAT** of planning, feasibility, OTD, inventory, schedule upload, and mock ERP sync. Not ready to claim live ERP or COM gates.

---

## 2. Excel template generation

**Location:** `ipe/docs/qa/upload-templates/`  
**Index:** `ipe/docs/qa/upload-templates/README.md`  
**Format:** real `.xlsx` (openpyxl 3.1.5) with header comments + `README` sheet per workbook.

### Templates created

| File | Purpose |
|------|---------|
| `products_upload_template.xlsx` | `cdm_product` |
| `work_centers_upload_template.xlsx` | `cdm_work_center` |
| `bom_routing_upload_template.xlsx` | BOM + routing |
| `mrp_orders_upload_template.xlsx` | `cdm_manufacturing_order` |
| `demand_lines_upload_template.xlsx` | `cdm_demand_line` / forecast history |
| `suppliers_upload_template.xlsx` | `cdm_supplier` |
| `customers_upload_template.xlsx` | `cdm_customer` |
| `inventory_upload_template.xlsx` | `cdm_inventory_position` |
| `supply_orders_upload_template.xlsx` | `cdm_supply_order` |
| `operators_upload_template.xlsx` | `cdm_operator` |
| `project_plan_upload_template.xlsx` | **Live UI upload** (cap-svc) |
| `tariff_matrix_upload_template.xlsx` | Tariff parser input (no HTTP upload yet) |
| `odoo_sync_entities_reference.xlsx` | Odoo→CDM field map (reference only) |

### How templates map to real load paths

| Load path | Status |
|-----------|--------|
| SQL: `seed-data.ps1` / `seed-startrans-demo.ps1` | **Primary** for master data |
| UI: Schedule → project plan `.xlsx` | **Only production-shaped file upload** (`mode=new\|update`) |
| Connector XML-RPC sync | Products/WCs/BOM/MO/inventory via mock or live Odoo |
| Star Trans CSVs | `docs/demo-data/startrans/*.csv` (parallel field set) |

**Verified this run:** `project_plan_upload_template.xlsx` uploaded successfully → plan `PLAN-STARTRANS-W12` version 1, 3 operations.

---

## 3. Data fetch dependency check

### 3.1 Screens that need external / ERP-origin data

| Screen / route | Data source today | Upload / import / mock / seed? | Isolated testing OK? |
|----------------|-------------------|--------------------------------|----------------------|
| Control Tower `/planning/control-tower` | CDM feasibility + sync status | Seed MOs; sync bar needs sync run | **Yes** (seed + optional mock sync) |
| Resolution `/planning/resolution` | CDM scenarios | Seed scenarios | **Yes** |
| Schedule `/planning/schedule` | CDM + **file upload** | **Yes** project-plan `.xlsx` | **Yes** |
| Digital Twin panel (on Schedule) | network-svc | No | **Gap** — network-svc not in R2 |
| Demand Forecast `/planning/demand` | demand-svc / CDM | Seed demand; no history upload | **Yes** with seed |
| Scenarios `/planning/scenarios` | scenario-svc | UI form + FE fallback KPIs | **Yes** |
| OTD Analytics `/command-center/otd-analytics` | dpe CDM aggregates | Seed MOs | **Yes** (OTD kpis returned) |
| Executive `/command-center/executive` | dpe analytics + FE S&OP body | Seed; Kong S&OP/cost-accounting gaps | **Partial** |
| War Room `/command-center/war-room` | alert-svc → twin | Hardcoded supplier id | **Gap** — not on R2 |
| Inventory `/supply-chain/inventory` | mat-svc CDM | Seed inventory | **Yes** |
| Orders / Procurement / Supply Planning | order/procurement/supply-svc | No | **Gap** — not on R2 |
| Tariff | dpe tariff | Parser only; no upload | **Partial** Kong routing |
| Odoo Connections `/platform/odoo-config` | connector + XML-RPC | No file upload; sync | **Partial** — use `:8016` (Kong 404) |
| Odoo Config versions | connector DB + test XML-RPC | No | **Partial** — Kong shadowing |
| Onboarding | Frontend mock only | N/A | **Yes** (non-persistent) |
| Copilot | nlp-svc / LLM | No | **Partial** without LLM key |

### 3.2 Gap list — missing upload/import for external-data screens

| Gap ID | Screen / capability | Missing capability | Recommended eng path for isolated test |
|--------|---------------------|--------------------|----------------------------------------|
| G1 | Products / WC / BOM / MO / demand / suppliers | No FastAPI bulk CSV/XLSX importer (SQL only) | Use templates + `seed-*.ps1` / future importer |
| G2 | Inventory positions | No upload; Odoo quants → `safety_stock` not full position table | Seed `cdm_inventory_position` |
| G3 | Demand history upload | No file import on Demand page | Seed demand lines; Run sense cycle |
| G4 | Tariff matrix | Parser exists, **no UploadFile route** | Template ready; wire endpoint later |
| G5 | Supply / PO lines | No upload | Seed or mock sync |
| G6 | Wave 1 ERP Connections via Kong | Route absent | Direct `:8016` or add Kong route |
| G7 | War Room / Digital Twin | Services absent from R2 | Full compose or skip for R2 UAT |
| G8 | Orders / Procurement / Supply Planning / Equipment | Services absent from R2 | Skip or expand compose |
| G9 | Live Odoo write-back / test-connection | Needs staging Odoo (PH1-02) | mock-odoo for eng only |

---

## 4. End-to-end testing with sample data

### 4.1 Suites executed (this run)

| Suite | Result | Evidence |
|-------|--------|----------|
| Release2 smoke | **15/15 PASS** | `docs/qa/pre-test-2026-07-12/release2-smoke.txt` |
| star-trans-validate | **16 PASS / 1 FAIL / 1 SKIP** | sync status was unknown *before* mock sync; Odoo test SKIP | `star-trans-validate.txt` |
| planning-uat | **8 PASS / 2 PARTIAL / 0 FAIL** | UAT-4 health partial; UAT-10 copilot timeout | `planning-uat.txt` + `PLANNING-UAT-RESULTS-2026-07-11.md` |
| Seed Star Trans | **PASS** | 10 `MO-ST-*` in DB |
| Project plan upload | **PASS** | `PLAN-STARTRANS-W12` v1, 3 ops |
| Mock-Odoo `POST /sync/run` | **PASS** | `status=success`, products/WCs/BOM/MO/inventory updated |
| Feasibility queue | **PASS** | 12 MOs, HTTP 200 |
| OTD KPIs | **PASS** | `otd_pct=50`, `orders_at_risk=4`, `chaos_cost_usd=17770` |
| Inventory summary | **PASS** | HTTP 200 |
| Resolution scenarios | **PASS** | HTTP 200, payload present |
| ERP connections Kong | **FAIL 404** | Expected Kong gap (B1) |
| ERP connections direct `:8016` | **PASS** | HTTP 200 |
| Web login page | **PASS** | HTTP 200 |

### 4.2 Flow results (sample data exercised)

| Flow | Pass/Fail | Notes |
|------|-----------|-------|
| Login via Kong | PASS | JWT issued |
| Feasibility queue display data | PASS | Scores from seed (hero MO-ST-001 ~52) |
| OTD analytics calculations | PASS | Aggregates from completed/at-risk MOs |
| Schedule / project plan import | PASS | Template uploaded with `mode=new` |
| Mock ERP sync integration | PASS | Connector → mock-odoo → CDM |
| Sync status after sync | PASS | `last_sync.status=success` |
| Live Copilot | PARTIAL | Timeout (known) |
| Live Odoo test-connection | SKIP | COM / PH1-02 |
| War Room E2E | NOT RUN | Service not on R2 |
| Arabic native COM | NOT CLAIMED | Eng keys present (405); G-R2-04 open |

### 4.3 Edge cases

| Case | Result |
|------|--------|
| Project plan upload without `mode` | 422 missing field |
| Project plan `mode=create` (invalid) | Error `INVALID_MODE` (must be `new`/`update`) |
| `sync/run` without Odoo creds body | 422 |
| Duplicate seed operator insert | Unique constraint — idempotent seed friction (document only) |

---

## 5. Completion summary

| Area | Result |
|------|--------|
| **Readiness verdict** | **CONDITIONAL PASS** for eng/isolated UAT on R2 |
| **Templates** | 13 workbooks under `docs/qa/upload-templates/` (+ README) |
| **External-data gaps** | G1–G9 above (no master-data HTTP importer; Kong ERP routes; R2 missing war-room/twin/supply services; live Odoo COM) |
| **E2E** | Smoke 15/15; validate 16/18; planning UAT 8/2/0; upload+mock sync+OTD+queue **PASS** |
| **Blockers to claim full go-live** | PH1-02 live Odoo, G-R2-04 Arabic COM, OQ-7, Kong Wave 1 routes, optional R2 service expansion |

### Recommended next eng actions (non-COM)

1. Add Kong routes for `/api/v1/erp/connections*` and connector `admin/odoo-config` (avoid dpe shadow).  
2. Re-run `star-trans-validate.ps1` after a successful sync (sync status should clear B3).  
3. Optionally wire CSV bulk import endpoints using templates in `upload-templates/`.  
4. Document R2 out-of-scope pages (War Room, Digital Twin, Orders, …) in customer UAT scripts.

---

*Generated by IPE QA/integration pass 2026-07-12. Does not constitute COM sign-off.*
