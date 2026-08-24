# BATCH1-1 — Promote demo_* to canonical ingest + RLS

**Date:** 2026-08-24  
**Branch:** `batch1-foundation-hardening`  
**Lab DB:** `ipe_test` @ localhost:5433  
**Workbook SoT:** `c:\Users\HP\Downloads\IPE_Data_Template_StarTrans_v1 (2).xlsx` (24 sheets: 23 data + README)  
**Alembic head:** **084**  
**COM:** **OPEN** (PH1-02 / G-R2-04 / OQ-7 / C-01…C-08 unchanged)

## 1. Inventory

Live `\dt demo_*` after 083: **zero tables** (none existed before promotion; Excel commit never materialized `demo_*` on this lab volume). Operational CDM (`cdm_manufacturing_order` etc.) already held Star Trans seed (28 MOs).

## 2. Categorization

All former `demo_*` entities are **B/C**: schemas incompatible with operational UUID/FK CDM. Promotion target is **`cdm_ingest_*`** (ingest layer + FORCE RLS), not a dump into `cdm_manufacturing_order`. See `BATCH1-1-DEMO-TABLE-INVENTORY-2026-08-24.md`.

## 3. Migrations

| Rev | Name | Result |
|-----|------|--------|
| **083** | `cdm_promote_demo_tables` | 20 `cdm_ingest_*` tables + FORCE RLS; drop leftover `demo_*` if present |
| **084** | `cdm_ingest_missing_sheets` | 7 tables for remaining workbook sheets |

Applied: `IPE_DATABASE_URL_SYNC=postgresql://ipe:ipe_test_pass@localhost:5433/ipe_test` → `alembic upgrade head` → **084**.

`\dt cdm_ingest_*` = **27 tables**. All data sheets mapped. README is not a table.

Policy uses `app.current_tenant_id` (platform convention matching 001–082). Not `ipe.tenant_id`. Not BYPASSRLS.

## 4. Sheet → table

| Sheet | Table | Origin |
|-------|-------|--------|
| README | skip (metadata) | — |
| 01_Plants | `cdm_ingest_plant` | 083 |
| 02_WorkCenters | `cdm_ingest_work_center` | 083 |
| 03a_Calendars | `cdm_ingest_capacity_calendar` | 083 |
| 03b_CalendarShifts | `cdm_ingest_calendar_shift` | **084** |
| 03c_CalendarExceptions | `cdm_ingest_calendar_exception` | **084** |
| 04_Products | `cdm_ingest_product` | 083 |
| 05_Materials | `cdm_ingest_material` | 083 |
| 06a_BOMHeaders | `cdm_ingest_bom` | 083 |
| 06b_BOMLines | `cdm_ingest_bom_component` | 083 table, ingest wired |
| 07a_RoutingHeaders | `cdm_ingest_routing` | 083 |
| 07b_RoutingOperations | `cdm_ingest_routing_operation` | 083 table, ingest wired |
| 08_Suppliers | `cdm_ingest_supplier` | 083 |
| 09_Customers | `cdm_ingest_customer` | 083 |
| 10a_Employees | `cdm_ingest_employee` | **084** |
| 10b_EmployeeSkills | `cdm_ingest_employee_skill` | **084** |
| 11a_SalesOrderHeaders | `cdm_ingest_sales_order` | 083 |
| 11b_SalesOrderLines | `cdm_ingest_sales_order_line` | **084** |
| 12_ManufacturingOrders | `cdm_ingest_manufacturing_order` | 083 |
| 13a_PurchaseOrderHeaders | `cdm_ingest_purchase_order` | 083 |
| 13b_PurchaseOrderLines | `cdm_ingest_purchase_order_line` | **084** |
| 14_Inventory | `cdm_ingest_inventory` | 083 |
| 15_Forecasts | `cdm_ingest_demand_forecast` | 083 |
| 16_ExecutionEvents | `cdm_ingest_execution_event` | **084** |

Legacy 083-only (no workbook sheet): `cdm_ingest_lead_time`, `cdm_ingest_cost_data`, `cdm_ingest_demand_history`, `cdm_ingest_quality_result`.

## 5. Application code

- `services/upload-svc/app/core/startrans_ingest.py` — `SHEET_TABLE` all 23 data sheets; FK rules; upsert extras
- `services/upload-svc/app/core/startrans_workbook.py` — composite `NATURAL_KEYS` for line/shift/event sheets
- `services/upload-svc/app/api/v1/data_upload.py` — commit passes `tenant_id`
- `scripts/seed-startrans-demo.ps1` — comment: Excel ingest writes `cdm_ingest_*`; seed still fills operational CDM

## 6. RLS tests

`pytest services/tests/rls/test_batch1_promotion.py -v` → **8/8 PASS** (7 required + 084 FORCE-RLS catalog check).

Lab role `ipe` is SUPERUSER + BYPASSRLS, so isolation tests connect as `ipe_rls_app` (NOSUPERUSER, NOBYPASSRLS). Tests do **not** use BYPASSRLS.

Upload-svc: `test_startrans_ingest_tables.py` → **4/4 PASS**.

## 7. Walkthrough smoke (warm R2, not Playwright re-run)

| # | Step | Result |
|---|------|--------|
| 1 | Login / Home | `http://localhost:8082/` and `/login` **200** |
| 2 | Executive / Home | `/home` **200** (SPA shell) |
| 3 | Planner / MO seed | **28** `cdm_manufacturing_order` rows for Star Trans tenant |
| 4 | Feasibility API | fea-svc `/api/v1/health` **200** |
| 5 | Data upload UI | `/admin/data/upload` **200**; upload-svc health **200** |
| 6 | Stack | kong, web-ui, dpe, fea, upload, cap, mat, res, db **up** |
| 7 | Kong health | `http://localhost:8000/api/v1/health` **200** |
| 8 | `/workspace` coexistence | SPA same shell **200** (not re-shot) |

Visual 8/8 Playwright not re-executed this session (same honesty as T093 YELLOW*). No walkthrough **regression** on operational CDM (ingest promotion does not replace `cdm_manufacturing_order`).

## 8. Honesty

- This is **ingest-layer** promotion, not lossless load into operational CDM.
- COM items remain OPEN.
- Do not treat as production Odoo or Arabic QA close.

## VERDICT

**YELLOW** — ENG tables + RLS tests PASS; walkthrough API/smoke intact; visual Playwright not re-run; COM OPEN.
