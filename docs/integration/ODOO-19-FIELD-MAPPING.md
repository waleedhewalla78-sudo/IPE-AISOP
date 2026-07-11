# Odoo 19 Field Mapping — IPE Release 1

**Document:** IPE-INT-ODOO19-v1  
**Version:** 1.0  
**Date:** 2026-07-11  
**Source:** Derived from `services/connector/app/core/mapper.py` and `services/connector/app/odoo/sync_engine.py`  
**Sync Frequency (all entities):** Every 15 minutes (scheduled), plus on-demand trigger via `POST /api/v1/sync/run`

> **Odoo 17 vs 19 note:** The IPE connector automatically handles the field name differences between Odoo 17 and 19. Specifically, Manufacturing Order date fields differ — see Entity 1 and the "Known Differences" section at the bottom of this document.

---

## Entity 1: Manufacturing Orders

**Odoo Model:** `mrp.production`  
**Odoo Modules Required:** `mrp`  
**CDM Table:** `cdm_manufacturing_order`  
**Sync Direction:** Odoo → IPE (read); IPE → Odoo (write-back on schedule approval)  
**Sync Filter:** `state not in ['cancel']` — all non-cancelled orders synced  
**Frequency:** Every 15 minutes

| Odoo Field | Odoo Type | CDM Column | CDM Type | Required | Default | Validation | Notes |
|---|---|---|---|---|---|---|---|
| `id` | Integer | `erp_mo_id` | String | Yes | — | Must be non-null | Used as stable ERP reference key |
| `name` | Char | `mo_name` | String | Yes | — | Non-null | Display name (e.g., WH/MO/00123) |
| `product_id` | Many2one → `product.product` | `product_erp_id` | String | Yes | — | Product must exist in CDM | If product not yet synced, MO is skipped |
| `bom_id` | Many2one → `mrp.bom` | `bom_erp_id` | String | No | NULL | Null triggers `MISSING_BOM` flag | If null, MO cannot be scored |
| `product_qty` | Float | `quantity` | Float | Yes | 0 | Must be > 0 | Production quantity |
| `date_start` | Datetime | `planned_start` | Datetime (UTC) | No | NULL | Parsed with timezone normalization | **Odoo 19 field** — see note below |
| `date_finished` | Datetime | `planned_end` | Datetime (UTC) | No | NULL | Parsed with timezone normalization | **Odoo 19 field** — see note below |
| `state` | Selection | `status` | Enum | Yes | `draft` | Mapped via state table | `draft`→`draft`, `confirmed`→`confirmed`, `progress`→`in_progress`, `to_close`→`in_progress`, `done`→`completed` |
| `write_date` | Datetime | `erp_last_update` | Datetime (UTC) | Yes | — | Used for conflict detection | Odoo's internal last-modified timestamp |

**Odoo 17 → 19 difference:** In Odoo 17, date fields are named `date_planned_start` and `date_planned_finished`. In Odoo 19, they are renamed to `date_start` and `date_finished`. The IPE connector reads both field names and uses whichever is non-null — no configuration required.

**Write-back fields (IPE → Odoo):**

| CDM Column | Odoo Field | Direction | Trigger |
|---|---|---|---|
| `planned_start` (approved) | `date_start` (Odoo 19) / `date_planned_start` (Odoo 17) | IPE → Odoo | Planner approves schedule in IPE |
| `planned_end` (approved) | `date_finished` (Odoo 19) / `date_planned_finished` (Odoo 17) | IPE → Odoo | Planner approves schedule in IPE |

A chatter note is added to the Odoo MO record after successful write-back, documenting the IPE user who approved and the timestamp.

---

## Entity 2: Bills of Material (Headers)

**Odoo Model:** `mrp.bom`  
**Odoo Modules Required:** `mrp`  
**CDM Table:** `cdm_bill_of_material`  
**Sync Direction:** Odoo → IPE  
**Sync Filter:** `active = True`  
**Frequency:** Every 15 minutes

| Odoo Field | Odoo Type | CDM Column | CDM Type | Required | Default | Validation | Notes |
|---|---|---|---|---|---|---|---|
| `id` | Integer | `erp_source_id` | String | Yes | — | Non-null | Stable BOM reference key |
| `product_id` | Many2one → `product.product` | `product_erp_id` | String | Yes | — | Product must be synced first | Links BOM to product; if product missing, BOM is skipped |
| `product_tmpl_id` | Many2one → `product.template` | `product_tmpl_erp_id` | String | No | — | Used as fallback for product lookup | Used when `product_id` is not set (template-level BOM) |
| `product_qty` | Float | `product_qty` | Float | No | 1.0 | — | Base quantity the BOM produces |
| `bom_line_ids` | One2many → `mrp.bom.line` | — | — | No | [] | — | Retrieved separately in BOM detail sync |
| `operation_ids` | One2many → `mrp.routing.workcenter` | — | — | No | [] | — | Retrieved separately in BOM detail sync |
| `active` | Boolean | `is_active` | Boolean | Yes | True | Only True records synced | Inactive BOMs excluded |

---

## Entity 3: BOM Lines (Components)

**Odoo Model:** `mrp.bom.line`  
**Odoo Modules Required:** `mrp`  
**CDM Table:** `cdm_bom_line`  
**Sync Direction:** Odoo → IPE  
**Sync Method:** Read by ID list from BOM header sync (`bom_line_ids`)  
**Frequency:** Every 15 minutes (deleted and re-created on each BOM detail sync)

| Odoo Field | Odoo Type | CDM Column | CDM Type | Required | Default | Validation | Notes |
|---|---|---|---|---|---|---|---|
| `id` | Integer | `erp_source_id` | String | Yes | — | Non-null | |
| `bom_id` | Many2one → `mrp.bom` | `bom_erp_id` | String | Yes | — | Parent BOM must exist | |
| `product_id` | Many2one → `product.product` | `component_erp_id` | String | Yes | — | Component product must be synced | If component product not synced, line is skipped |
| `product_qty` | Float | `quantity_per` | Float | Yes | 1.0 | Must be > 0 | Quantity of component per BOM output qty |
| `product_uom_id` | Many2one → `uom.uom` | `uom` | String (16 chars) | No | `"unit"` | Truncated to 16 chars | Unit of measure label |

---

## Entity 4: Routing Operations

**Odoo Model:** `mrp.routing.workcenter`  
**Odoo Modules Required:** `mrp`  
**CDM Table:** `cdm_routing_operation`  
**Sync Direction:** Odoo → IPE  
**Sync Method:** Read by ID list from BOM header sync (`operation_ids`)  
**Frequency:** Every 15 minutes (deleted and re-created on each BOM detail sync)

| Odoo Field | Odoo Type | CDM Column | CDM Type | Required | Default | Validation | Notes |
|---|---|---|---|---|---|---|---|
| `id` | Integer | `erp_source_id` | String | Yes | — | Non-null | |
| `bom_id` | Many2one → `mrp.bom` | `bom_erp_id` | String | Yes | — | Parent BOM must exist | |
| `sequence` | Integer | `sequence` | Integer | No | 100 | — | Order of operation within BOM |
| `name` | Char | `operation_name` | String | No | `"Operation"` | — | Operation display name |
| `workcenter_id` | Many2one → `mrp.workcenter` | `work_center_erp_id` | String | Yes | — | Work centre must be synced | If work centre not synced, routing op is skipped |
| `time_cycle_manual` | Float | `duration_planned_mins` | Float | No | 60.0 | — | Planned cycle time in minutes |

**Note:** In older Odoo 17 configurations, this model may be named `mrp.routing.workcenter` and linked via a separate `mrp.routing` model. In Odoo 19, routing operations are attached directly to BOMs via `operation_ids`. The IPE connector reads `operation_ids` directly from the BOM.

---

## Entity 5: Work Centres

**Odoo Model:** `mrp.workcenter`  
**Odoo Modules Required:** `mrp`  
**CDM Table:** `cdm_work_center`  
**Sync Direction:** Odoo → IPE  
**Sync Filter:** `active = True`  
**Frequency:** Every 15 minutes

| Odoo Field | Odoo Type | CDM Column | CDM Type | Required | Default | Validation | Notes |
|---|---|---|---|---|---|---|---|
| `id` | Integer | `erp_source_id` | String | Yes | — | Non-null | |
| `name` | Char | `name` | String | Yes | `"Work Center"` | Non-null | Display name (e.g., "Winding Station 1") |
| `code` | Char | `code` | String | No | NULL | — | Internal code (optional) |
| `time_efficiency` | Float | `time_efficiency` | Float | No | 100.0 | 0–200 | Efficiency % — 80 means 80% of nominal capacity |

**Capacity note:** In Odoo 17, the field `default_capacity` maps to `capacity_hours_per_day`. In Odoo 19, capacity is derived from `time_efficiency` and the work centre's resource calendar. The connector uses `time_efficiency` as the primary capacity indicator; `capacity_hours_per_day` defaults to 8.0 hours/day if not overridden by custom logic. If your Odoo instance uses a custom capacity model, document the custom fields in the Pre-Implementation Verification Checklist.

---

## Entity 6: Products

**Odoo Model:** `product.product`  
**Odoo Modules Required:** `product` (included with all modules)  
**CDM Table:** `cdm_product`  
**Sync Direction:** Odoo → IPE  
**Sync Filter:** `active = True`  
**Frequency:** Every 15 minutes

| Odoo Field | Odoo Type | CDM Column | CDM Type | Required | Default | Validation | Notes |
|---|---|---|---|---|---|---|---|
| `id` | Integer | `erp_source_id` | String | Yes | — | Non-null | |
| `name` | Char | `name` | String | Yes | — | Non-null | Product display name |
| `default_code` | Char | `internal_ref` | String | No | NULL | — | Internal SKU / product code |
| `type` | Selection | `source_type` | Enum | No | `"manufactured"` | `product`→`manufactured`, `consu`→`purchased`, `service`→`subcontracted` | Determines cost calculation method |
| `uom_id` | Many2one → `uom.uom` | `uom` | String | No | `"unit"` | — | Unit of measure label |
| `standard_price` | Float | `standard_cost` / `unit_cost` | Float | No | 0 | — | Cost price; used in financial impact calculations |
| `list_price` | Float | `list_price` | Float | No | NULL | — | Sales price; used in revenue-at-risk calculations |
| `weight` | Float | `weight` | Float | No | NULL | — | Product weight (kg) |
| `qty_available` | Float | `safety_stock` (proxy) | Float | No | 0 | — | On-hand quantity; **overwritten by stock.quant sync** |

---

## Entity 7: Customers

**Odoo Model:** `res.partner`  
**Odoo Modules Required:** `base`, `sale`  
**CDM Table:** `cdm_customer`  
**Sync Direction:** Odoo → IPE  
**Sync Filter:** `customer_rank > 0`  
**Frequency:** Every 15 minutes

| Odoo Field | Odoo Type | CDM Column | CDM Type | Required | Default | Validation | Notes |
|---|---|---|---|---|---|---|---|
| `id` | Integer | `erp_source_id` | String | Yes | — | Non-null | |
| `name` | Char | `name` | String | Yes | `"Customer [id]"` | Non-null | Customer company or individual name |
| `customer_rank` | Integer | `customer_rank` | Integer | Yes | — | Must be > 0 for sync filter | Indicates how many times used as customer |
| `supplier_rank` | Integer | `supplier_rank` | Integer | No | 0 | — | A partner may be both customer and supplier |

**Note:** Partners where both `customer_rank > 0` and `supplier_rank > 0` are synced to both `cdm_customer` and `cdm_supplier`.

---

## Entity 8: Suppliers

**Odoo Model:** `res.partner`  
**Odoo Modules Required:** `base`, `purchase`  
**CDM Table:** `cdm_supplier`  
**Sync Direction:** Odoo → IPE  
**Sync Filter:** `supplier_rank > 0`  
**Frequency:** Every 15 minutes

| Odoo Field | Odoo Type | CDM Column | CDM Type | Required | Default | Validation | Notes |
|---|---|---|---|---|---|---|---|
| `id` | Integer | `erp_source_id` | String | Yes | — | Non-null | |
| `name` | Char | `name` | String | Yes | `"Supplier [id]"` | Non-null | |
| `customer_rank` | Integer | `customer_rank` | Integer | No | 0 | — | |
| `supplier_rank` | Integer | `supplier_rank` | Integer | Yes | — | Must be > 0 for sync filter | |

---

## Entity 9: Sales Order Lines / Demand

**Odoo Model:** `sale.order.line`  
**Odoo Modules Required:** `sale`  
**CDM Table:** `cdm_demand_line`  
**Sync Direction:** Odoo → IPE  
**Sync Filter:** `state in ['sale', 'done']` — only confirmed and done order lines synced  
**Frequency:** Every 15 minutes

| Odoo Field | Odoo Type | CDM Column | CDM Type | Required | Default | Validation | Notes |
|---|---|---|---|---|---|---|---|
| `id` | Integer | `erp_source_id` | String | Yes | — | Non-null | |
| `product_id` | Many2one → `product.product` | `product_erp_id` | String | Yes | — | Product must be synced | Line skipped if product not found |
| `product_uom_qty` | Float | `quantity` | Float | Yes | — | Must be > 0 | Ordered quantity |
| `price_subtotal` | Float | `revenue` | Float | No | NULL | — | Line value; used in revenue-at-risk calculation |
| `scheduled_date` | Datetime | `required_date` | Datetime (UTC) | No | `now()` | — | Customer-requested delivery date |
| `order_partner_id` | Many2one → `res.partner` | `customer_erp_id` | String | No | NULL | — | Customer linked from order header |
| `state` | Selection | `status` | String | No | — | — | Inherited from parent sale.order |

---

## Entity 10: Purchase Order Lines / Supply

**Odoo Model:** `purchase.order.line`  
**Odoo Modules Required:** `purchase`  
**CDM Table:** `cdm_supply_order`  
**Sync Direction:** Odoo → IPE  
**Sync Filter:** `state in ['purchase', 'done']` — only confirmed and received lines synced  
**Frequency:** Every 15 minutes

| Odoo Field | Odoo Type | CDM Column | CDM Type | Required | Default | Validation | Notes |
|---|---|---|---|---|---|---|---|
| `id` | Integer | `erp_source_id` | String | Yes | — | Non-null | |
| `product_id` | Many2one → `product.product` | `product_erp_id` | String | Yes | — | Product must be synced | Line skipped if product not found |
| `product_qty` | Float | `quantity_ordered` | Float | Yes | 1 | — | Ordered quantity |
| `qty_received` | Float | `quantity_received` | Float | No | 0 | — | Quantity received to date |
| `date_planned` | Datetime | `expected_date` | Datetime (UTC) | No | `now()` | — | Promised delivery date from supplier |
| `partner_id` | Many2one → `res.partner` | `supplier_erp_id` | String | No | NULL | — | Linked from order header |
| `state` | Selection | `status` | String | No | — | — | Inherited from parent purchase.order |

---

## Entity 11: Inventory / Stock Quantities

**Odoo Model:** `stock.quant`  
**Odoo Modules Required:** `stock`  
**CDM Table:** Updates `cdm_product.safety_stock` (not a separate CDM table in R1)  
**Sync Direction:** Odoo → IPE  
**Sync Filter:** `location_id.usage = 'internal'` AND `quantity > 0`  
**Frequency:** Every 15 minutes

| Odoo Field | Odoo Type | CDM Target | CDM Type | Required | Default | Validation | Notes |
|---|---|---|---|---|---|---|---|
| `product_id` | Many2one → `product.product` | Used as lookup key | — | Yes | — | Must match synced product | |
| `quantity` | Float | `cdm_product.safety_stock` (aggregated) | Float | Yes | — | Must be ≥ 0 | Gross on-hand quantity |
| `reserved_quantity` | Float | Subtracted from `quantity` | Float | No | 0 | — | `available = quantity - reserved_quantity` |
| `location_id` | Many2one → `stock.location` | Filter only | — | Yes | — | Only `usage = 'internal'` | Excludes transit, virtual, customer locations |

**Aggregation:** If a product has stock in multiple internal locations, quantities are summed. The result overwrites `cdm_product.safety_stock` on each sync run.

---

## Entity 12: Lead Time History

**Odoo Models:** `purchase.order` + `stock.picking`  
**Odoo Modules Required:** `purchase`, `stock`  
**CDM Table:** `cdm_lead_time_history`  
**Sync Direction:** Odoo → IPE  
**Sync Scope:** Purchase orders with receipts in last 90 days  
**Frequency:** Every 15 minutes (incremental by `date_order`)

| Source | Odoo Field | CDM Column | CDM Type | Notes |
|---|---|---|---|---|
| `purchase.order` | `date_order` | `po_date` | Datetime | PO creation date |
| `purchase.order` | `partner_id` | `supplier_erp_id` | String | Supplier reference |
| `stock.picking` (receipt) | `date_done` | `receipt_date` | Datetime | Actual goods receipt date |
| Calculated | `receipt_date - po_date` | `actual_lead_days` | Integer | Actual lead time in days |
| `purchase.order.line` | `date_planned` | `promised_date` | Datetime | Supplier-promised date |
| Calculated | `promised_date - po_date` | `promised_lead_days` | Integer | Promised lead time in days |
| Calculated | `actual_lead_days - promised_lead_days` | `delay_days` | Integer | Delay vs. promise (negative = early) |

**Used for:** Supplier reliability scoring in the material availability gate; lead time variance in OTD analytics.

---

## Entity 13: Write-Back — Schedule Dates

**Odoo Model:** `mrp.production` (write)  
**Odoo Module Required:** `mrp` (write access required)  
**CDM Source:** `cdm_manufacturing_order` (approved schedule)  
**Sync Direction:** IPE → Odoo  
**Trigger:** Manual — planner approves a resolution scenario or schedule in IPE  
**Not scheduled:** Write-back is event-driven, not part of the 15-minute batch sync

| CDM Column | Odoo 19 Field | Odoo 17 Field | Type | Validation |
|---|---|---|---|---|
| `planned_start` (approved) | `date_start` | `date_planned_start` | Datetime | Must be a valid datetime; not in the past by more than 7 days |
| `planned_end` (approved) | `date_finished` | `date_planned_finished` | Datetime | Must be ≥ `date_start` |

**Chatter note format:**
```
IPE Schedule Update — [Timestamp]
Approved by: [Planner username]
New planned start: [date_start]
New planned finish: [date_finished]
Previous start: [old_date_start]
Previous finish: [old_date_finished]
```

**Permissions required:** The Odoo API service account must have `write` access to `mrp.production`. Read-only accounts will cause write-back to fail silently in Odoo (403 error logged in connector).

---

## Pre-Implementation Verification Checklist

Complete this checklist with Customer IT before Week 1 Day 1.

```
ODOO MODULES
[ ] Odoo has mrp module installed and active
[ ] Odoo has sale module installed and active
[ ] Odoo has purchase module installed and active
[ ] Odoo has stock module installed and active

ODOO DATA
[ ] At least 1 mrp.production record exists in state 'confirmed' or 'progress'
[ ] At least 1 mrp.bom record exists with at least 1 active bom_line
[ ] At least 1 mrp.workcenter record exists
[ ] Products are linked to BOMs (bom.product_id or bom.product_tmpl_id set)
[ ] At least 1 sale.order.line exists in state 'sale' or 'done'

ODOO CONNECTIVITY
[ ] XML-RPC enabled on Odoo (port 8069 accessible from IPE server)
[ ] IPE server can reach Odoo server: telnet [ODOO_HOST] 8069 succeeds
[ ] API service account created with username and password

ODOO API USER PERMISSIONS
[ ] API user has READ access to: mrp.production, mrp.bom, mrp.bom.line
[ ] API user has READ access to: mrp.workcenter, mrp.routing.workcenter
[ ] API user has READ access to: product.product, res.partner
[ ] API user has READ access to: sale.order.line, purchase.order.line
[ ] API user has READ access to: stock.quant, stock.picking, stock.location
[ ] API user has WRITE access to: mrp.production (for schedule write-back)

ODOO VERSION
[ ] Odoo version confirmed: 17 / 19 (circle one; document sub-version: _______)

CUSTOM FIELDS
[ ] Custom fields on mrp.production documented: _______________
[ ] Custom fields on mrp.bom documented: _______________
[ ] Custom modules affecting MRP data flow documented: _______________

ESTIMATED DATA VOLUMES
[ ] Active MOs (state = confirmed or progress): _____ (target: <500 for good performance)
[ ] Active BOMs: _____
[ ] Work centres: _____
[ ] Active products with BOMs: _____
```

---

## Known Odoo 19 vs. Odoo 17 Field Differences

| Entity | Odoo 17 Field | Odoo 19 Field | IPE Handling |
|---|---|---|---|
| `mrp.production` | `date_planned_start` | `date_start` | Connector reads both; uses whichever is non-null. `normalize_mo_mapped()` in `mapper.py` handles this automatically. |
| `mrp.production` | `date_planned_finished` | `date_finished` | Same as above. |
| `mrp.production` (write-back) | `date_planned_start` | `date_start` | Write-back uses the appropriate field based on version detected at connect time. |
| `mrp.workcenter` | `default_capacity` | `time_efficiency` | In Odoo 17, `default_capacity` was a simple hours/day float. In Odoo 19, `time_efficiency` (a percentage) is used instead. IPE maps `time_efficiency` to its internal capacity model. |
| `mrp.routing.workcenter` | Linked via `mrp.routing` | Linked directly via `bom.operation_ids` | In Odoo 17, routing operations were attached to a separate `mrp.routing` record. In Odoo 19, they attach directly to the BOM. IPE reads `operation_ids` from the BOM directly. |
| `sale.order.line` | `order_id.partner_id` (traverse) | `order_partner_id` (direct) | In Odoo 17, customer required traversal through parent order. In Odoo 19, `order_partner_id` is available directly on the line. |

---

*This document is the single source of truth for IPE ↔ Odoo field mapping. Update when new fields are added to the connector. Source code reference: `services/connector/app/core/mapper.py` rev. at time of document creation.*
