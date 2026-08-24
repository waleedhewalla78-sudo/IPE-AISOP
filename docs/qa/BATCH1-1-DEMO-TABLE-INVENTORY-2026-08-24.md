# BATCH1-1 — demo_* table inventory

**Date:** 2026-08-24  
**Branch:** `batch1-foundation-hardening`  
**Lab DB:** `ipe_test` @ localhost:5433  
**Alembic head at inventory:** `082`

## Batch 0 smoke (prerequisite)

| Check | Result |
|-------|--------|
| Compose R2 | UP (kong, web-ui, dpe, fea, upload, cap, mat, res, db, redis) |
| http://localhost:8082/ | 200 |
| Kong `/api/v1/health` | 200 |
| Alembic | **082** |
| Batch 0 overall | **YELLOW** (JWT not on `/api/v1/data`; COM OPEN). User authorized Batch 1 anyway. |

## STEP 1 — Live `\dt demo_*`

**Zero tables.** Excel ingest creates `demo_*` on first **commit** via `ensure_demo_tables()`. Batch 0 T091 was preview-only (no commit), so the lab DB never materialized them.

Row counts: all **0** (tables absent).

## Canonical CDM vs demo ingest schema

Seed (`seed-startrans-demo.ps1`) already writes **CDM** (`cdm_manufacturing_order`, etc.). `demo_*` is a **parallel simplified staging** used only by Star Trans Excel ingest (`startrans_ingest.py`).

CDM counterparts exist but **schemas do not match** (UUID PKs, required FKs such as `bom_id` on `cdm_manufacturing_order`, typed columns vs TEXT + JSONB `payload`). Naive `INSERT INTO cdm_* SELECT * FROM demo_*` would fail or corrupt the 28 seeded MOs.

## STEP 2 — Categorization

| demo_* table | Canonical CDM | Category | Action |
|--------------|---------------|----------|--------|
| demo_plants | `cdm_plant` | **B/C** | Incompatible PK/FK. Promote to `cdm_ingest_plant` + RLS, then drop demo. |
| demo_products | `cdm_product` | **B/C** | Same — `cdm_ingest_product`. |
| demo_materials | `cdm_product` (purchased) | **C** | `cdm_ingest_material`. |
| demo_work_centers | `cdm_work_center` | **B/C** | `cdm_ingest_work_center`. |
| demo_customers | `cdm_customer` | **B/C** | `cdm_ingest_customer`. |
| demo_suppliers | `cdm_supplier` | **B/C** | `cdm_ingest_supplier`. |
| demo_boms | `cdm_bill_of_material` | **B/C** | `cdm_ingest_bom`. |
| demo_bom_components | `cdm_bom_line` | **B/C** | `cdm_ingest_bom_component`. |
| demo_routings | routing header | **C** | `cdm_ingest_routing`. |
| demo_routing_operations | `cdm_routing_operation` | **B/C** | `cdm_ingest_routing_operation`. |
| demo_manufacturing_orders | `cdm_manufacturing_order` | **B/C** | CDM requires `bom_id`. `cdm_ingest_manufacturing_order`. |
| demo_sales_orders | demand/SO | **C** | `cdm_ingest_sales_order`. |
| demo_purchase_orders | `cdm_supply_order` | **B/C** | `cdm_ingest_purchase_order`. |
| demo_inventory | inventory snapshot | **C** | `cdm_ingest_inventory`. |
| demo_capacity_calendar | calendar | **C** | `cdm_ingest_capacity_calendar`. |
| demo_lead_times | none | **C** | `cdm_ingest_lead_time`. |
| demo_cost_data | none | **C** | `cdm_ingest_cost_data`. |
| demo_demand_forecast | `cdm_sop_forecast` | **B/C** | `cdm_ingest_demand_forecast`. |
| demo_demand_history | none | **C** | `cdm_ingest_demand_history`. |
| demo_quality_results | `cdm_quality_event` | **B/C** | `cdm_ingest_quality_result`. |

**Category A:** none (no schema-identical twins).  
**Category D:** none (all Excel entities are production-intent staging).

Honesty: this is **ingest-layer promotion with RLS**, not a lossless dump into operational `cdm_manufacturing_order`. Operational seed data stays on CDM. Excel commit writes `cdm_ingest_*` under `tenant_id` + RLS (`app.current_tenant_id`, matching migrations 001–082 — not `ipe.tenant_id`).

## 083 applied

Migration **083** `cdm_promote_demo_tables` created 20 `cdm_ingest_*` tables with FORCE RLS.

## 084 — remaining workbook sheets

The Star Trans template has **24 sheets** (23 data + README). 083 mapped the old demo_* set; line/shift/employee/event sheets were still missing tables. See `BATCH1-1-PROMOTION-REPORT-2026-08-24.md`.
