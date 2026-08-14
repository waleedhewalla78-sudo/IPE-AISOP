-- Star Trans demo CDM (simplified) — 16 entities, basic FKs + indexes
-- Demo only: skip RLS, deferred FKs, GIN indexes (STREAM-2.3)

CREATE TABLE IF NOT EXISTS demo_products (
  product_id TEXT PRIMARY KEY,
  name TEXT,
  product_type TEXT,
  uom TEXT,
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_work_centers (
  work_center_id TEXT PRIMARY KEY,
  name TEXT,
  capacity_hours NUMERIC,
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_customers (
  customer_id TEXT PRIMARY KEY,
  name TEXT,
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_suppliers (
  supplier_id TEXT PRIMARY KEY,
  name TEXT,
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_boms (
  bom_id TEXT PRIMARY KEY,
  product_id TEXT REFERENCES demo_products(product_id),
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_routings (
  routing_id TEXT PRIMARY KEY,
  product_id TEXT REFERENCES demo_products(product_id),
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_bom_components (
  bom_component_id TEXT PRIMARY KEY,
  bom_id TEXT REFERENCES demo_boms(bom_id),
  component_product_id TEXT,
  qty NUMERIC,
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_routing_operations (
  operation_id TEXT PRIMARY KEY,
  routing_id TEXT REFERENCES demo_routings(routing_id),
  work_center_id TEXT REFERENCES demo_work_centers(work_center_id),
  duration_hours NUMERIC,
  sequence_no INT,
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_manufacturing_orders (
  mo_id TEXT PRIMARY KEY,
  product_id TEXT REFERENCES demo_products(product_id),
  qty NUMERIC,
  feasibility NUMERIC,
  status TEXT,
  due_date TEXT,
  planned_start TEXT,
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_sales_orders (
  so_id TEXT PRIMARY KEY,
  customer_id TEXT REFERENCES demo_customers(customer_id),
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_purchase_orders (
  po_id TEXT PRIMARY KEY,
  supplier_id TEXT REFERENCES demo_suppliers(supplier_id),
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_inventory (
  inventory_id TEXT PRIMARY KEY,
  product_id TEXT REFERENCES demo_products(product_id),
  qty NUMERIC,
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_capacity_calendar (
  calendar_id TEXT PRIMARY KEY,
  work_center_id TEXT REFERENCES demo_work_centers(work_center_id),
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_lead_times (
  lead_time_id TEXT PRIMARY KEY,
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_cost_data (
  cost_id TEXT PRIMARY KEY,
  payload JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS demo_demand_forecast (
  forecast_id TEXT PRIMARY KEY,
  payload JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_demo_mo_feasibility ON demo_manufacturing_orders (feasibility);
CREATE INDEX IF NOT EXISTS idx_demo_mo_product ON demo_manufacturing_orders (product_id);
CREATE INDEX IF NOT EXISTS idx_demo_bom_product ON demo_boms (product_id);
CREATE INDEX IF NOT EXISTS idx_demo_routing_product ON demo_routings (product_id);
CREATE INDEX IF NOT EXISTS idx_demo_inv_product ON demo_inventory (product_id);
