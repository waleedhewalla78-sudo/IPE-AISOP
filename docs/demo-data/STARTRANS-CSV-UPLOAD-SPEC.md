# Star Trans Demo — CSV / Data Upload Specification

**Client:** Star Trans — Electrical Transformer Technology  
**Version:** 1.0 · 2026-06-29  
**Environment:** Local laptop · `http://localhost:8082` · DB `ipe_test` @ Docker `docker-db-1:5433`

This document is the **single source of truth** for demo data loading. Follow it line-by-line to avoid upload failures.

---

## Critical platform facts

| Fact | Implication |
|------|-------------|
| Only **one** file uploads through the UI today | `06_project_plan` → must be **`.xlsx`**, not `.csv` |
| Sheets 01–05 load via **SQL seed**, not UI | Run `.\scripts\seed-startrans-demo.ps1` before demo |
| Do **not** run SQL in Cursor against empty DB | Use Docker: `docker exec -i docker-db-1 psql -U ipe -d ipe_test` |
| Login | `Ahmed@nour` / `admin` |

---

## 1. CSV files inventory

| # | Filename | Purpose | Required columns (types) | Rows | Screen | Demo step | Depends on | Upload method |
|---|----------|---------|--------------------------|------|--------|-----------|------------|---------------|
| 01 | `01_products.csv` | Transformer SKU master | PRODUCT_CODE (text), NAME (text), TYPE (text), UOM (text), STANDARD_COST (decimal), INTERNAL_REF (text) | 5 | *(none — pre-seed)* | T-90 prep | migrations + seed-data | SQL overlay / future importer |
| 02 | `02_work_centers.csv` | Shop resources | WC_CODE (text), NAME (text), CAPACITY_HRS (decimal), OEE (decimal), COST_PER_HR (decimal), STATUS (text) | 3 | *(pre-seed)* | T-90 prep | 01 | SQL overlay |
| 03 | `03_bom_routing.csv` | Operations per product | PRODUCT_CODE, OP_SEQ (int), OP_NAME, WC_CODE, DURATION_MIN (int), SETUP_MIN (int) | 6+ | *(pre-seed)* | T-90 prep | 01, 02 | SQL overlay |
| 04 | `04_manufacturing_orders.csv` | MO queue + feasibility | MO_ID, PRODUCT_CODE, QTY (int), FEASIBILITY (decimal), MATERIAL_SCORE, CAPACITY_SCORE, PRIMARY_CONSTRAINT, STATUS, CUSTOMER | 10 | Control Tower, Resolution | Act 1 (min 5–15) | 01, 03 | SQL seed (`seed-demo-client` + overlay) |
| 05 | `05_demand_history.csv` | Forecast input history | PRODUCT_CODE, WEEK_START (date YYYY-MM-DD), QTY (int), CUSTOMER, DEMAND_TYPE | 16+ | Demand | Act 3 (min 25–35) | 01 | SQL seed; live **Run sense cycle** button |
| 06 | `06_suppliers.csv` | Supplier scorecards | SUPPLIER_CODE, NAME, RELIABILITY_SCORE (0–1), AVG_DELAY_DAYS, TIER (int) | 3 | SCN Portal | Act 1 / Supply | — | SQL overlay |
| **07** | **`06_project_plan-startrans-w12.csv`** → **`.xlsx`** | **Live schedule upload** | PLAN_CODE, PLAN_NAME, MO_ID, OPERATION_SEQUENCE (int), OPERATION_NAME, WORK_CENTER_CODE, START_HOUR (decimal), DURATION_HOURS (decimal), STATUS, NOTES | 4+ | **Planning → Schedule** | **Act 2 (min 15–25)** | **04 MO-ST-* must exist** | **UI file picker (.xlsx only)** |

**Template location:** `docs/demo-data/startrans/*.csv`

---

## 2. Live upload file — project plan (Step 07)

### Column specification (exact headers — case-insensitive in parser)

| Column | Required | Type | Example | Rules |
|--------|----------|------|---------|-------|
| PLAN_CODE | Yes | text | PLAN-STARTRANS-W12 | Same on every row |
| PLAN_NAME | Yes | text | Star Trans Week 12 Production | Same on every row |
| MO_ID | Yes | text | MO-ST-001 | Must exist in DB (from 04) |
| OPERATION_SEQUENCE | Yes | integer | 10 | Unique per MO_ID in file |
| OPERATION_NAME | Yes | text | Wind LV/HV Coils | Display on Gantt |
| WORK_CENTER_CODE | Yes | text | WC002 | Must be WC001, WC002, or WC003 |
| START_HOUR | Yes | number | 0 | Hours from horizon start |
| DURATION_HOURS | Yes | number | 1.5 | Must be > 0 |
| STATUS | No | text | planned | planned, frozen, disrupted, ai_suggested |
| NOTES | No | text | Copper expedite lane | Optional |

### Convert CSV → XLSX before demo

```powershell
cd E:\AISOP\ipe
.\scripts\convert-project-plan-to-xlsx.ps1
# Output: docs\demo-data\startrans\project-plan-startrans-w12.xlsx
```

Or: open `project-plan-startrans-w12.csv` in Excel → **Save As** → `.xlsx`.

---

## 3. Demo execution sequence

### T-90 — Pre-demo (not shown to client)

| Step | Action | Validation |
|------|--------|------------|
| P1 | `cd infrastructure\docker; docker compose up -d db dpe-svc` | `docker ps` shows db healthy |
| P2 | `.\scripts\seed-data.ps1` | No ERROR in output |
| P3 | `.\scripts\seed-startrans-demo.ps1` | "Star Trans demo data ready" |
| P4 | Start v8 services + Kong (see `prepare-startrans-demo.ps1`) | Login works on :8000 |
| P5 | `.\scripts\run-full-demo.ps1 -Profile startrans` | **32/32 PASS** |
| P6 | Convert project plan to `.xlsx` | File on desktop |
| P7 | `cd apps\web; npm run dev` | :8082 login page loads |
| P8 | Pre-run 3 Copilot queries | Cheat sheet |

### T-0 — Live demo (client visible)

| Step | Time | Screen path | Action | File / data |
|------|------|-------------|--------|-------------|
| 1 | 0–5 | `/login` → `/planning/dashboard` | Login, frame the story | — |
| 2 | 5–15 | Planning → **Control Tower** | Show MO-ST-001, MO-ST-007 at-risk | Pre-seed 04 |
| 3 | 5–15 | Planning → **Resolution** | Select MO-ST-001, show 3 scenarios | Pre-seed 04 |
| 4 | 15–20 | Planning → **Schedule** → Refresh | OR-Tools Gantt | Pre-seed 03 |
| 5 | 20–25 | Schedule → **Upload Project Plan** | Create new plan → upload `.xlsx` | **07 project-plan-startrans-w12.xlsx** |
| 6 | 20–25 | Schedule → View: **Uploaded project plan** | Select PLAN-STARTRANS-W12 | — |
| 7 | 25–30 | Planning → **Demand** → Run sense cycle | Forecast chart | Pre-seed 05 |
| 8 | 30–35 | Planning → **Scenarios** | Create + simulate sandbox | UI form (no file) |
| 9 | 35–38 | Supply Chain → **Supply Planning** | 4 plants, 6 lanes | Pre-seed |
| 10 | 38–45 | AI & Governance → **Copilot** | 3 live queries | Cheat sheet |
| 11 | 45–52 | Command Center → **Executive** + **War Room** | OTD, delays, alerts | Pre-seed 04 |
| 12 | 52–60 | AI & Governance → **Quality** + **Sustainability** | FPY, ESG close | API seed |

**Only step 5–6 uses a file upload during the live demo.**

---

## 4. Cross-file dependencies

```
01_products ──┬──► 03_bom_routing ──► 04_manufacturing_orders ──► 07_project_plan (MO_ID)
              ├──► 05_demand_history
              └──► 04_manufacturing_orders (PRODUCT_CODE)

02_work_centers ──► 03_bom_routing
                 └──► 07_project_plan (WORK_CENTER_CODE)

06_suppliers ──► SCN Portal (independent of upload chain)
```

| Rule | Enforced by |
|------|-------------|
| MO_ID in project plan ∈ MO-ST-* in DB | cap-svc Excel parser |
| WC_CODE ∈ {WC001, WC002, WC003} | parser + DB work centers |
| PRODUCT_CODE stable (PROD001–005) | overlay SQL keeps FKs |

---

## 5. Known issues & mitigation

| Issue | Symptom | Mitigation |
|-------|---------|------------|
| Wrong database / Cursor SQL runner | `cdm_tenant does not exist` | Use `.\scripts\seed-startrans-demo.ps1` only |
| Docker DB down | container not running | `docker compose up -d db dpe-svc` |
| Kong 502 after restart | Login fails | `docker compose up -d --force-recreate kong` |
| Re-run seed-demo-client | duplicate key MO | Use `seed-startrans-demo.ps1` (skips if MO-ST exists) |
| Upload `.csv` in UI | rejected | Convert to `.xlsx` |
| Upload panel hidden | can't find upload | Click **Upload Project Plan** button on Schedule |
| MO_ID typo MO-DEMO-* | validation error | Use MO-ST-001 format after overlay |
| Copilot timeout | blank 180s | Ollama on :11434; pre-run queries |
| Copilot `[REDACTED]` text | looks broken | Data correct; mention demo redaction |
| v8 services 500 | CP21–29 fail | `docker compose up -d demand-svc scenario-svc supply-svc ...` |
| UTF-8 em-dash in SQL | PowerShell parse error | Overlay uses ASCII hyphens only |

---

## 6. One-command demo prep

```powershell
cd E:\AISOP\ipe
.\scripts\prepare-startrans-demo.ps1
.\scripts\convert-project-plan-to-xlsx.ps1
cd apps\web; npm run dev
```

**Gate:** `docs\demo-data\startrans-pre-demo.txt` shows `32 / 32 passed`.

---

## 7. Reference docs

| Doc | Path |
|-----|------|
| 60-min presenter script | `docs/demo-data/STARTRANS-DEMO-GUIDE.md` |
| Copilot queries | `docs/demo-data/STARTRANS-COPILOT-CHEATSHEET.md` |
| Excel schema detail | `docs/PROJECT-PLAN-EXCEL-SCHEMA.md` |
| SQL overlay | `scripts/seed-startrans-overlay.sql` |
