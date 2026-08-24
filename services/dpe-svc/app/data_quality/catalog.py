"""Data quality check catalog for ingest + operational CDM (BATCH1-4)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DQCheck:
    id: str
    entity: str
    severity: str  # critical | high | medium | low
    description: str
    sql_query: str
    fix_guidance: str


def _c(eid, entity, sev, desc, sql, fix) -> DQCheck:
    return DQCheck(eid, entity, sev, desc, sql, fix)


CATALOG: list[DQCheck] = [
    _c("products.missing_name", "products", "high", "Product missing name", "SELECT product_id AS id FROM cdm_ingest_product WHERE name IS NULL OR name = ''", "Set product name on ingest/Excel 04_Products."),
    _c("products.missing_uom", "products", "medium", "Product missing UOM", "SELECT product_id AS id FROM cdm_ingest_product WHERE uom IS NULL OR uom = ''", "Fill uom_primary on 04_Products."),
    _c("products.missing_type", "products", "medium", "Product missing type", "SELECT product_id AS id FROM cdm_ingest_product WHERE product_type IS NULL", "Set product_type."),
    _c("products.no_bom", "products", "critical", "Product has no BOM header", "SELECT p.product_id AS id FROM cdm_ingest_product p WHERE NOT EXISTS (SELECT 1 FROM cdm_ingest_bom b WHERE b.product_id = p.product_id AND b.tenant_id = p.tenant_id)", "Add 06a_BOMHeaders row for the product."),
    _c("products.no_routing", "products", "critical", "Product has no routing", "SELECT p.product_id AS id FROM cdm_ingest_product p WHERE NOT EXISTS (SELECT 1 FROM cdm_ingest_routing r WHERE r.product_id = p.product_id AND r.tenant_id = p.tenant_id)", "Add 07a_RoutingHeaders for the product."),
    _c("materials.missing_name", "materials", "high", "Material missing name", "SELECT material_id AS id FROM cdm_ingest_material WHERE name IS NULL OR name = ''", "Fill material_name on 05_Materials."),
    _c("materials.missing_payload", "materials", "low", "Material empty payload", "SELECT material_id AS id FROM cdm_ingest_material WHERE payload = '{}'::jsonb", "Re-ingest Excel so payload retains lead time/supplier."),
    _c("mos.missing_product", "manufacturing_orders", "critical", "MO missing product", "SELECT mo_id AS id FROM cdm_ingest_manufacturing_order WHERE product_id IS NULL", "Set product_id on 12_ManufacturingOrders."),
    _c("mos.qty_non_positive", "manufacturing_orders", "critical", "MO qty <= 0", "SELECT mo_id AS id FROM cdm_ingest_manufacturing_order WHERE qty IS NOT NULL AND qty <= 0", "Correct quantity_planned."),
    _c("mos.missing_qty", "manufacturing_orders", "high", "MO missing qty", "SELECT mo_id AS id FROM cdm_ingest_manufacturing_order WHERE qty IS NULL", "Fill quantity_planned."),
    _c("mos.missing_due", "manufacturing_orders", "high", "MO missing due date", "SELECT mo_id AS id FROM cdm_ingest_manufacturing_order WHERE due_date IS NULL OR due_date = ''", "Fill required_date."),
    _c("sales.missing_customer", "sales_orders", "critical", "SO missing customer", "SELECT so_id AS id FROM cdm_ingest_sales_order WHERE customer_id IS NULL OR customer_id = ''", "Fill customer_id on 11a."),
    _c("sales_lines.missing_product", "sales_order_lines", "high", "SO line missing product", "SELECT so_line_id AS id FROM cdm_ingest_sales_order_line WHERE product_id IS NULL", "Fill product_id on 11b."),
    _c("sales_lines.qty_non_positive", "sales_order_lines", "high", "SO line qty <= 0", "SELECT so_line_id AS id FROM cdm_ingest_sales_order_line WHERE qty IS NOT NULL AND qty <= 0", "Correct quantity_ordered."),
    _c("po.missing_supplier", "purchase_orders", "critical", "PO missing supplier", "SELECT po_id AS id FROM cdm_ingest_purchase_order WHERE supplier_id IS NULL OR supplier_id = ''", "Fill supplier_id on 13a."),
    _c("po_lines.missing_material", "purchase_order_lines", "high", "PO line missing material", "SELECT po_line_id AS id FROM cdm_ingest_purchase_order_line WHERE material_id IS NULL", "Fill material_id on 13b."),
    _c("po_lines.qty_non_positive", "purchase_order_lines", "high", "PO line qty <= 0", "SELECT po_line_id AS id FROM cdm_ingest_purchase_order_line WHERE qty IS NOT NULL AND qty <= 0", "Correct quantity_ordered."),
    _c("suppliers.missing_name", "suppliers", "high", "Supplier missing name", "SELECT supplier_id AS id FROM cdm_ingest_supplier WHERE name IS NULL OR name = ''", "Fill supplier_name."),
    _c("customers.missing_name", "customers", "high", "Customer missing name", "SELECT customer_id AS id FROM cdm_ingest_customer WHERE name IS NULL OR name = ''", "Fill customer_name."),
    _c("wc.missing_name", "work_centers", "medium", "WC missing name", "SELECT work_center_id AS id FROM cdm_ingest_work_center WHERE name IS NULL OR name = ''", "Fill work_center_name."),
    _c("wc.missing_capacity", "work_centers", "high", "WC missing capacity", "SELECT work_center_id AS id FROM cdm_ingest_work_center WHERE capacity_hours IS NULL", "Fill capacity_per_shift."),
    _c("plants.missing_name", "plants", "high", "Plant missing name", "SELECT plant_id AS id FROM cdm_ingest_plant WHERE name IS NULL OR name = ''", "Fill plant_name."),
    _c("calendars.orphan_shift", "calendars", "medium", "Shift without matching calendar header", "SELECT s.shift_id AS id FROM cdm_ingest_calendar_shift s WHERE NOT EXISTS (SELECT 1 FROM cdm_ingest_capacity_calendar c WHERE c.calendar_id = s.calendar_id AND c.tenant_id = s.tenant_id)", "Add 03a_Calendars row first."),
    _c("employees.missing_name", "employees", "medium", "Employee missing name", "SELECT employee_id AS id FROM cdm_ingest_employee WHERE employee_name IS NULL OR employee_name = ''", "Fill employee_name."),
    _c("skills.orphan_employee", "employee_skills", "medium", "Skill row without employee", "SELECT employee_skill_id AS id FROM cdm_ingest_employee_skill s WHERE NOT EXISTS (SELECT 1 FROM cdm_ingest_employee e WHERE e.employee_id = s.employee_id AND e.tenant_id = s.tenant_id)", "Load 10a_Employees before 10b."),
    _c("bom.missing_product", "boms", "critical", "BOM missing product", "SELECT bom_id AS id FROM cdm_ingest_bom WHERE product_id IS NULL", "Fill product_id on 06a."),
    _c("bom_lines.missing_qty", "bom_lines", "high", "BOM line missing qty", "SELECT bom_component_id AS id FROM cdm_ingest_bom_component WHERE qty IS NULL", "Fill quantity_per on 06b."),
    _c("routing.missing_product", "routings", "high", "Routing missing product", "SELECT routing_id AS id FROM cdm_ingest_routing WHERE product_id IS NULL", "Fill product_id on 07a."),
    _c("routing_ops.missing_wc", "routing_operations", "high", "Operation missing work center", "SELECT operation_id AS id FROM cdm_ingest_routing_operation WHERE work_center_id IS NULL", "Fill work_center_id_primary on 07b."),
    _c("inventory.missing_qty", "inventory", "high", "Inventory missing qty", "SELECT inventory_id AS id FROM cdm_ingest_inventory WHERE qty IS NULL", "Fill quantity_on_hand."),
    _c("inventory.negative_qty", "inventory", "critical", "Negative on-hand", "SELECT inventory_id AS id FROM cdm_ingest_inventory WHERE qty IS NOT NULL AND qty < 0", "Correct snapshot quantities."),
    _c("forecasts.empty_payload", "forecasts", "low", "Forecast empty payload", "SELECT forecast_id AS id FROM cdm_ingest_demand_forecast WHERE payload = '{}'::jsonb", "Re-ingest 15_Forecasts."),
    _c("events.missing_mo", "execution_events", "high", "Event missing MO", "SELECT event_id AS id FROM cdm_ingest_execution_event WHERE mo_id IS NULL OR mo_id = ''", "Fill mo_id on 16_ExecutionEvents."),
    _c("events.missing_type", "execution_events", "medium", "Event missing type", "SELECT event_id AS id FROM cdm_ingest_execution_event WHERE event_type IS NULL OR event_type = ''", "Fill event_type."),
    _c("cdm_mo.null_feasibility", "manufacturing_orders", "medium", "Operational MO missing feasibility", "SELECT id::text AS id FROM cdm_manufacturing_order WHERE feasibility_score IS NULL", "Run fea-svc score / seed overlay."),
    _c("lead_time.empty", "lead_times", "low", "Lead time empty payload", "SELECT lead_time_id AS id FROM cdm_ingest_lead_time WHERE payload = '{}'::jsonb", "Populate lead-time ingest or ignore if unused."),
    _c("cost.empty", "cost_data", "low", "Cost row empty payload", "SELECT cost_id AS id FROM cdm_ingest_cost_data WHERE payload = '{}'::jsonb", "Populate cost ingest or ignore if unused."),
    _c("quality.empty", "quality", "low", "Quality row empty payload", "SELECT quality_id AS id FROM cdm_ingest_quality_result WHERE payload = '{}'::jsonb", "Populate quality ingest or ignore if unused."),
    _c("history.empty", "demand_history", "low", "Demand history empty payload", "SELECT history_id AS id FROM cdm_ingest_demand_history WHERE payload = '{}'::jsonb", "Populate history ingest or ignore if unused."),
    _c("so_lines.orphan_header", "sales_order_lines", "high", "SO line without header", "SELECT so_line_id AS id FROM cdm_ingest_sales_order_line l WHERE NOT EXISTS (SELECT 1 FROM cdm_ingest_sales_order h WHERE h.so_id = l.sales_order_id AND h.tenant_id = l.tenant_id)", "Load 11a before 11b."),
    _c("po_lines.orphan_header", "purchase_order_lines", "high", "PO line without header", "SELECT po_line_id AS id FROM cdm_ingest_purchase_order_line l WHERE NOT EXISTS (SELECT 1 FROM cdm_ingest_purchase_order h WHERE h.po_id = l.purchase_order_id AND h.tenant_id = l.tenant_id)", "Load 13a before 13b."),
    _c("bom_lines.orphan_bom", "bom_lines", "critical", "BOM line without header", "SELECT bom_component_id AS id FROM cdm_ingest_bom_component c WHERE NOT EXISTS (SELECT 1 FROM cdm_ingest_bom b WHERE b.bom_id = c.bom_id AND b.tenant_id = c.tenant_id)", "Load 06a before 06b."),
    _c("shifts.missing_calendar", "calendars", "medium", "Shift missing calendar_id", "SELECT shift_id AS id FROM cdm_ingest_calendar_shift WHERE calendar_id IS NULL OR calendar_id = ''", "Fill calendar_id on 03b."),
    _c("exceptions.missing_type", "calendars", "low", "Exception missing type", "SELECT exception_id AS id FROM cdm_ingest_calendar_exception WHERE exception_type IS NULL OR exception_type = ''", "Fill exception_type on 03c."),
    _c("employees.missing_plant", "employees", "medium", "Employee missing plant", "SELECT employee_id AS id FROM cdm_ingest_employee WHERE plant_id IS NULL OR plant_id = ''", "Fill plant_id on 10a."),
]

WEIGHT = {"critical": 10, "high": 5, "medium": 2, "low": 1}


def compute_score(offense_counts: dict[str, int]) -> float:
    weighted = 0.0
    capacity = 0.0
    for chk in CATALOG:
        w = WEIGHT[chk.severity]
        capacity += w
        weighted += w * (1 if offense_counts.get(chk.id, 0) > 0 else 0)
    if capacity == 0:
        return 100.0
    pct = 100.0 * weighted / capacity
    return max(0.0, min(100.0, 100.0 - pct))
