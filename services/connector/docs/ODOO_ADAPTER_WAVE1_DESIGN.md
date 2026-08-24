# Odoo Adapter Wave 1 — Design

**Date:** 2026-08-24  
**Scope:** READ-ONLY master-data sync into `cdm_ingest_*`. Not PH1-02. Not write-back. Not operational entities (SO/MO/PO/inventory/forecast/events).

## Existing connector

- `app/odoo/client.py` — XML-RPC `OdooClient`
- `app/erp/odoo_adapter.py` — REST pull against `ipe_connector` `/ipe/api/v1/*`
- `app/odoo/sync_engine.py` — CDM upsert path (Release 1)
- Lab R2 uses **mock-odoo-api** (`localhost:8010` XML-RPC), not Star Trans production Odoo

## Wave 1 architecture

Each of 10 master adapters:

1. `fetch_from_odoo(since)` — XML-RPC `search_read`, 100–500 rows/call
2. `transform_to_canonical(odoo_record)` — map known fields only; extra Odoo fields dropped with warning; missing canonical fields left NULL (never invented)
3. `upsert_to_ipe(record)` — idempotent by `(tenant_id, natural_key)` into the matching `cdm_ingest_*` table; `source_system=odoo`, `source_id`, `synced_at` stored in `payload`

Orchestrator `sync_all_master_data(tenant_id, since)` runs:

Plants → Calendars → Work Centers → Products → Materials → BOMs → Routings → Suppliers → Customers → Employees

One adapter failure does not stop the rest. `SyncReport` is written to JSON under `docs/qa/` (no new Alembic rev: 084 already used for ingest sheets; 085–086 reserved for Copilot audit + DQ).

## Entity map

| Adapter | Odoo model | Ingest table |
|---------|------------|--------------|
| Plants | `stock.warehouse` | `cdm_ingest_plant` |
| Work Centers | `mrp.workcenter` | `cdm_ingest_work_center` |
| Calendars | `resource.calendar` | `cdm_ingest_capacity_calendar` |
| Products | `product.template` (goods) | `cdm_ingest_product` |
| Materials | `product.template` (consu/raw) | `cdm_ingest_material` |
| BOMs | `mrp.bom` + `mrp.bom.line` | `cdm_ingest_bom` / `cdm_ingest_bom_component` |
| Routings | BOM `operation_ids` / `mrp.routing.workcenter` | `cdm_ingest_routing` / `cdm_ingest_routing_operation` |
| Suppliers | `res.partner` `supplier_rank>0` | `cdm_ingest_supplier` |
| Customers | `res.partner` `customer_rank>0` | `cdm_ingest_customer` |
| Employees | `hr.employee` + `hr.employee.skill` | `cdm_ingest_employee` / `cdm_ingest_employee_skill` |

## Honesty

PH1-02 remains **OPEN**. Wave 1 is foundation code + mock/XML-RPC tests. Not live customer Odoo.
