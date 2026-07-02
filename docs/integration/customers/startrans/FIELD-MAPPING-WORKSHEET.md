# Star Trans — Odoo Field Mapping Worksheet (Standard Fields)

**Customer**: Star Trans — Electrical Transformer Technology  
**Odoo version**: 17.0 / 19.0 (Community or Enterprise + `mrp`)  
**Status**: Standard mapping locked for R1 UAT — custom fields pending customer workshop  
**Date**: 2026-06-24

---

## 1. Manufacturing orders (`mrp.production`)

| Odoo field | IPE CDM field | Required | Notes |
|------------|---------------|----------|-------|
| `id` | `cdm_manufacturing_order.erp_mo_id` | Yes | Upsert key |
| `product_id` | `product_id` (via `erp_source_id`) | Yes | Skip MO if product missing |
| `bom_id` | `bom_id` | Yes | Skip MO if BOM missing |
| `product_qty` | `quantity` | Yes | |
| `date_start` | `planned_start` | Yes | Odoo 19 |
| `date_finished` | `planned_end` | Yes | Odoo 19 |
| `state` | `status` | Yes | Excludes `cancel` |
| `write_date` | `erp_last_update` | Yes | Conflict detection |

**Custom fields**: None signed for R1. Optional `metadata` JSONB in R1.1.

---

## 2. Products (`product.product`)

| Odoo field | IPE CDM field | Notes |
|------------|---------------|-------|
| `id` | `erp_source_id` | |
| `name` | `name` | |
| `default_code` | `internal_ref` | `False` → null |
| `standard_price` | `standard_cost` | |
| `qty_available` | `safety_stock` (proxy) | Product sync |
| `stock.quant` aggregate | `safety_stock` | Inventory sync (T088) |

---

## 3. BOMs (`mrp.bom`, `mrp.bom.line`, `mrp.routing.workcenter`)

| Odoo model | IPE table | Notes |
|------------|-----------|-------|
| `mrp.bom` | `cdm_bill_of_material` | Header sync |
| `mrp.bom.line` | `cdm_bom_line` | T080 |
| `mrp.routing.workcenter` | `cdm_routing_operation` | T080 — required for scoring |

---

## 4. Partners, supply, demand

| Odoo model | IPE table |
|------------|-----------|
| `res.partner` (customer) | `cdm_customer` |
| `res.partner` (supplier) | `cdm_supplier` |
| `sale.order.line` | `cdm_demand_line` |
| `purchase.order.line` | `cdm_supply_order` |

---

## 5. Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Star Trans IT | _pending T003_ | | |
| Star Trans Production | _pending workshop_ | | |
| Diligent Engineering | Implemented | 2026-06-24 | Code complete |

**Workshop action (T086)**: Customer to confirm custom fields on `mrp.production` and sign this worksheet before production cutover.
