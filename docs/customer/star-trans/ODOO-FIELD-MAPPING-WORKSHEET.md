# Odoo Field Mapping Worksheet — Star Trans

**Instructions:** Customer IT completes this **before** implementation week. Return to IPE Engineering.

---

## Standard Fields (No Action Required)

These are mapped automatically by IPE:

| Odoo model | Fields |
|------------|--------|
| `product.product` | `name`, `default_code`, `type` |
| `mrp.bom` | `product_id` |
| `mrp.bom.line` | `product_id`, `product_qty` |
| `mrp.routing.workcenter` | `sequence`, `workcenter_id`, `time_cycle_manual` |
| `mrp.production` | `id`, `date_start`, `date_finished`, `state` |
| `sale.order.line` | `scheduled_date`, `product_uom_qty` |
| `purchase.order.line` | `date_planned` |

---

## Custom Fields (Customer Must List)

| Odoo Model | Field Name | Field Type | IPE Target | Notes |
|------------|------------|------------|------------|-------|
| `mrp.production` | | | | |
| `product.product` | | | | |
| `mrp.bom` | | | | |
| | | | | |

---

## Custom Odoo Modules

| Module Name | Purpose | Affects IPE? |
|-------------|---------|--------------|
| | | |

---

## Odoo Version Confirmation

- [ ] Odoo **17**
- [ ] Odoo **19**

**Exact version string:** _______________

**Database name (staging):** _______________

**Completed by:** _______________ **Date:** _______________
