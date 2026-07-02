# Odoo Field Mapping Worksheet — Customer Discovery

**Customer:** Star Trans — Electrical Transformer Technology  
**Odoo version:** **17.0** (locked OQ-3)  
**Date:** _______________  
**Completed by:** _______________

---

## 1. Environment

| Field | Value |
|-------|-------|
| Odoo URL (staging) | |
| Odoo URL (production) | |
| Database name | |
| Odoo edition | Community / Enterprise |
| Installed modules | mrp, stock, purchase, sale |
| Custom modules affecting MRP | |
| Approx. active MOs/month | |
| Deployment | Diligent cloud / On-prem |

---

## 2. Service account

| Field | Value |
|-------|-------|
| Username | |
| Has MRP write access | Yes / No |
| Has BOM read access | Yes / No |

---

## 3. Standard field mapping (Odoo 17 → IPE)

| Odoo model | Odoo field | IPE entity | IPE field | Custom? |
|------------|------------|------------|-----------|---------|
| `product.product` | `id` | `cdm_product` | `erp_source_id` | |
| `product.product` | `name` | `cdm_product` | `name` | |
| `product.product` | `default_code` | `cdm_product` | `internal_ref` | |
| `mrp.workcenter` | `id` | `cdm_work_center` | `erp_source_id` | |
| `mrp.workcenter` | `name` | `cdm_work_center` | `name` | |
| `mrp.workcenter` | `default_capacity` | `cdm_work_center` | `capacity_hours_per_day` | |
| `mrp.bom` | `id` | `cdm_bill_of_material` | `erp_source_id` | |
| `mrp.bom` | `product_id` | `cdm_bill_of_material` | `product_id` | |
| `mrp.production` | `id` | `cdm_manufacturing_order` | `erp_mo_id` | |
| `mrp.production` | `name` | — | display only | |
| `mrp.production` | `product_id` | `cdm_manufacturing_order` | `product_id` | |
| `mrp.production` | `bom_id` | `cdm_manufacturing_order` | `bom_id` | |
| `mrp.production` | `product_qty` | `cdm_manufacturing_order` | `quantity` | |
| `mrp.production` | `date_start` | `cdm_manufacturing_order` | `planned_start` | |
| `mrp.production` | `date_finished` | `cdm_manufacturing_order` | `planned_end` | |
| `mrp.production` | `state` | `cdm_manufacturing_order` | `status` | |
| `mrp.production` | `write_date` | `cdm_manufacturing_order` | `erp_last_update` | |

---

## 4. Custom fields (if any)

| Model | Field name | Type | Maps to | Notes |
|-------|------------|------|---------|-------|
| | | | | |

---

## 5. Data quality sample (10 MOs)

| Odoo MO name | Has BOM? | Has routing? | WC defined? | Notes |
|--------------|----------|--------------|-------------|-------|
| | | | | |

**Estimated scorable MO % after cleanup:** _______%

---

## 6. Sign-off

Discovery complete — ready for staging sync: Yes / No

Customer IT: _______________  Date: _______

Diligent: _______________  Date: _______
