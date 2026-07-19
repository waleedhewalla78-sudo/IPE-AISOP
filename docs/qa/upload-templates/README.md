# IPE Upload Templates (aligned to upload-svc)

**Regenerated:** 2026-07-18
**Source of truth:** `services/upload-svc/app/core/validator.py` `FILE_SCHEMAS`

## Important — superseded 2026-07-12 pack

The July 12 templates used CDM/seed-style **UPPER_SNAKE** headers (`PRODUCT_CODE`, …).
Data Upload Center / upload-svc requires **lowercase** headers (`product_code`, …).
This pack matches upload-svc **Phases 1–5 + Phase 8** types with **full operational columns**
(e.g. product: code, group, type, short/full name, UoM, main storage location + optional cost/stock fields).

## How data loads

| Path | Mechanism | Persists? |
|------|-----------|-----------|
| Data Upload Center | `POST /api/v1/upload/{file_type}` | Validate + wizard state (**not** full CDM row import) |
| Project plan | Schedule UI → `.xlsx` | **Yes** (cap-svc) |
| SQL seed | `seed-data.ps1` / `seed-startrans-demo.ps1` | **Yes** |
| Odoo sync | Platform → Odoo Connections | **Yes** when live (PH1-02 OPEN → mock) |
| Tariff matrix | Template only | **No HTTP upload** |

## Template index

| File | file_type | Phase | Required columns |
|------|-----------|-------|------------------|
| `product_master_upload_template.xlsx` | `product_master` | 1 | product_code, product_group, product_type, short_name, full_name, uom, main_storage_location, name_ar, standard_cost, currency, safety_stock, reorder_point, lead_time_days, abc_class, active, weight_kg, hs_code |
| `customer_master_upload_template.xlsx` | `customer_master` | 1 | customer_code, name, name_ar, tier, country, city, currency, credit_limit, payment_terms, contact_name, contact_email, contact_phone, tax_id, active |
| `supplier_master_upload_template.xlsx` | `supplier_master` | 1 | supplier_code, name, name_ar, lead_time_days, country, city, currency, reliability_pct, payment_terms, contact_name, contact_email, min_order_qty, active |
| `work_centre_master_upload_template.xlsx` | `work_centre_master` | 1 | work_centre_code, name, name_ar, capacity_hrs_day, location, shifts_per_day, efficiency_pct, calendar_code, cost_per_hour, active |
| `bom_upload_template.xlsx` | `bom` | 2 | product_code, component_code, quantity, uom, scrap_pct, operation_seq, effective_from, effective_to |
| `routing_upload_template.xlsx` | `routing` | 2 | product_code, operation_seq, work_centre_code, run_minutes, setup_minutes, description, overlap_pct |
| `capacity_calendar_upload_template.xlsx` | `capacity_calendar` | 3 | work_centre_code, date, shift, available_hours, overtime_hours, notes |
| `lead_time_upload_template.xlsx` | `lead_time` | 3 | product_code, supplier_code, lead_time_days, min_qty, transport_mode, incoterm |
| `cost_data_upload_template.xlsx` | `cost_data` | 3 | product_code, unit_cost, currency, cost_type, effective_from, standard_cost |
| `inventory_upload_template.xlsx` | `inventory` | 4 | product_code, on_hand, location, reserved, available, lot_number, uom |
| `production_orders_upload_template.xlsx` | `production_orders` | 4 | mo_number, product_code, quantity, planned_start, planned_end, status, priority, work_centre_code, customer_code, sales_order |
| `sales_orders_upload_template.xlsx` | `sales_orders` | 4 | order_number, line_number, customer_code, product_code, quantity, uom, unit_price, currency, order_date, requested_delivery, status, warehouse |
| `purchase_orders_upload_template.xlsx` | `purchase_orders` | 4 | po_number, supplier_code, product_code, quantity, unit_price, currency, expected_delivery, warehouse, status |
| `historical_otd_upload_template.xlsx` | `historical_otd` | 5 | mo_number, product_code, customer_code, planned_end, actual_end, delay_days |
| `demand_forecast_upload_template.xlsx` | `demand_forecast` | 8 | product_code, period, forecast_qty, uom, source, confidence_pct |
| `quality_results_upload_template.xlsx` | `quality_results` | 8 | mo_number, product_code, inspection_date, result, measured_value, defect_type, inspector, notes |
| `sop_sales_input_upload_template.xlsx` | `sop_sales_input` | 8 | product_family, period, sales_forecast_qty, rationale, region, confidence_pct |
| `project_plan_upload_template.xlsx` | `project_plan (cap-svc)` | Schedule UI | MO_ID, OPERATION_SEQ, WORK_CENTER_CODE, PLANNED_START, PLANNED_END, DURATION_HRS |

| `tariff_matrix_upload_template.xlsx` | *(unwired)* | — | Parser only |
| `odoo_sync_entities_reference.xlsx` | *(reference)* | — | Not an upload |

## UI

1. Open http://localhost:8082 → login `Ahmed@nour` / `admin`
2. **Platform → Data Upload** — pick file_type matching the template
3. **Planning → Schedule** — Upload Project Plan (`project_plan_upload_template.xlsx`)

## Regenerator

```powershell
cd E:\AISOP\ipe
.\.venv\Scripts\python.exe scripts\generate_upload_templates.py
```

