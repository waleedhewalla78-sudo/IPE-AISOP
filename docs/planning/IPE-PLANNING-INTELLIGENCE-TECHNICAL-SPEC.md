# IPE Planning Intelligence Modules — Technical Implementation Specification

**Version:** 1.0  
**Date:** July 2026  
**Workspace:** `E:\AISOP\ipe`  
**Source:** SAP IBP SAPIBP1 Release 2508 Gap Analysis  
**Authority:** PRD-IPE-COMPREHENSIVE-AS-IS.md  
**Target:** v9.2.0 (R2 planning modules) → v10.0.0 (R3 S&OP engine)

---

## Document Purpose

This specification defines the exact technical implementation for 6 new modules and 4 modifications that bring SAP IBP-equivalent planning intelligence to IPE. Every section includes database schemas, API contracts, Odoo 19 field mappings, service integration flows, and Cursor prompts ready for execution.

**How to use:** Open this file in Cursor alongside the IPE workspace. Execute modules in the order specified. Each module is self-contained with its own migration, service code, API, frontend, and tests.

---

## Architecture Overview — After All Modules Built

```
Browser (React/Vite :8082)
    │
    ▼
Kong API Gateway (:8000)
    │
    ├── dpe-svc (:8001) — auth, dashboard, resolution, analytics, admin, MDR
    ├── mat-svc (:8002) — material ATP, netting, ABC/XYZ segmentation, safety stock
    ├── cap-svc (:8003) — scheduling, CPM, capacity analytics, utilisation alerts
    ├── fea-svc (:8004) — feasibility scoring (multi-version), WebSocket
    ├── nlp-svc (:8007) — Copilot with planning intelligence tools
    ├── connector (:8009) — Odoo 19 sync (extended: sales actuals, AOP, CRM)
    ├── demand-svc (:8040) — forecasting (ARIMA/SARIMA/SES/Prophet), forecast quality
    ├── scenario-svc (:8050) — what-if sandbox with inventory/S&OP integration
    ├── sop-svc (:8110) — [NEW] S&OP process engine, consensus, versions
    │
    PostgreSQL 16 (:5433) — migrations 001–055+
    Redis — cache / sessions
```

---

## Table of Contents

1. [Module A: Forecast Quality Engine](#module-a)
2. [Module B: ABC/XYZ Segmentation Engine](#module-b)
3. [Module C: Safety Stock Calculator](#module-c)
4. [Module D: Statistical Forecasting Upgrade](#module-d)
5. [Module E: Capacity Utilisation Alerts](#module-e)
6. [Module F: S&OP Process Engine](#module-f)
7. [Odoo 19 Connector Extensions](#odoo-extensions)
8. [Cross-Module Integration Flows](#integration-flows)
9. [Key Figure Registry](#key-figure-registry)
10. [Frontend Components](#frontend)
11. [Copilot Tool Extensions](#copilot-tools)

---

<a name="module-a"></a>
## Module A: Forecast Quality Engine

**Service:** Extend `demand-svc` at `:8040`  
**Migration:** 043  
**Priority:** P1  
**Effort:** 4–6 weeks  
**Dependencies:** None (builds on existing demand-svc)

### A.1 Database Schema

**Migration 043: `043_forecast_quality.py`**

```python
"""
Migration 043: Forecast quality tracking — snapshots, error metrics, stability
"""

# Table: cdm_forecast_snapshot
# Stores monthly snapshots of forecasts for lag-based error calculation
cdm_forecast_snapshot:
  columns:
    id: UUID PK DEFAULT gen_random_uuid()
    tenant_id: UUID NOT NULL REFERENCES cdm_tenant(id)
    product_id: UUID NOT NULL REFERENCES cdm_product(id)
    location_id: UUID NULL REFERENCES cdm_plant(id)
    snapshot_date: DATE NOT NULL  # When the snapshot was taken
    target_period_start: DATE NOT NULL  # The future period being forecasted
    target_period_type: VARCHAR(10) NOT NULL  # 'day', 'week', 'month'
    forecast_qty: NUMERIC(18,4) NOT NULL
    forecast_source: VARCHAR(50) NOT NULL  # 'statistical', 'consensus', 'manual', 'sensed'
    model_id: VARCHAR(100) NULL  # Which forecast model produced this
    model_version: VARCHAR(50) NULL
    created_at: TIMESTAMPTZ DEFAULT now()
  indexes:
    - idx_fsnap_tenant_product: (tenant_id, product_id, snapshot_date)
    - idx_fsnap_target: (tenant_id, target_period_start)
  rls: tenant_id = current_setting('app.tenant_id')::uuid

# Table: cdm_forecast_error
# Calculated error metrics per product, period, and lag
cdm_forecast_error:
  columns:
    id: UUID PK DEFAULT gen_random_uuid()
    tenant_id: UUID NOT NULL REFERENCES cdm_tenant(id)
    product_id: UUID NOT NULL REFERENCES cdm_product(id)
    location_id: UUID NULL
    period_start: DATE NOT NULL
    period_type: VARCHAR(10) NOT NULL  # 'week', 'month'
    lag_periods: INTEGER NOT NULL  # 1 = 1-month-ago forecast, 3 = 3-months-ago forecast
    forecast_source: VARCHAR(50) NOT NULL
    forecast_qty: NUMERIC(18,4)
    actuals_qty: NUMERIC(18,4)
    absolute_error: NUMERIC(18,4)  # |forecast - actuals|
    error_pct: NUMERIC(10,4)  # absolute_error / actuals (MAPE component)
    bias: NUMERIC(18,4)  # forecast - actuals (signed)
    bias_pct: NUMERIC(10,4)  # bias / actuals
    mase_component: NUMERIC(10,4)  # |error| / naive_mae
    calculated_at: TIMESTAMPTZ DEFAULT now()
  indexes:
    - idx_ferr_tenant_product: (tenant_id, product_id, period_start, lag_periods)
  rls: tenant_id = current_setting('app.tenant_id')::uuid

# Table: cdm_forecast_stability
# Tracks how forecast for the same future period changes across cycles
cdm_forecast_stability:
  columns:
    id: UUID PK DEFAULT gen_random_uuid()
    tenant_id: UUID NOT NULL
    product_id: UUID NOT NULL
    target_period_start: DATE NOT NULL
    cycle_date: DATE NOT NULL  # When this forecast cycle ran
    prior_cycle_date: DATE NULL
    current_forecast_qty: NUMERIC(18,4)
    prior_forecast_qty: NUMERIC(18,4) NULL
    change_qty: NUMERIC(18,4) NULL  # current - prior
    change_pct: NUMERIC(10,4) NULL
    created_at: TIMESTAMPTZ DEFAULT now()
  rls: tenant_id = current_setting('app.tenant_id')::uuid
```

### A.2 API Endpoints

**File:** `services/demand-svc/app/api/v1/forecast_quality.py`

```
POST /api/v1/demand/snapshot/create
  Body: { products: ["all" | UUID[]], source: "statistical" }
  Response: { snapshot_id, products_captured: int, snapshot_date }
  Logic: For each product, store current forecast values as snapshot row.

GET /api/v1/demand/error/mape
  Query: product_id?, location_id?, period_start?, period_end?, lag=1, source="statistical"
  Response: {
    summary: { weighted_mape, product_count, period_count },
    by_product: [{ product_id, product_name, mape, bias_pct, periods_measured }],
    by_period: [{ period_start, mape, bias_pct, forecast_qty, actuals_qty }]
  }
  Logic:
    MAPE = AVG(|forecast - actuals| / actuals) × 100 where actuals > 0
    Weighted MAPE = SUM(|forecast - actuals|) / SUM(actuals) × 100

GET /api/v1/demand/error/bias
  Query: product_id?, period_start?, period_end?, lag=1
  Response: {
    summary: { avg_bias_pct, positive_bias_count, negative_bias_count },
    by_product: [{ product_id, bias_pct, direction: "over" | "under" }]
  }
  Logic: Bias = (forecast - actuals) / actuals. Positive = over-forecast.

GET /api/v1/demand/error/mase
  Query: product_id?, lag=1
  Response: { by_product: [{ product_id, mase }] }
  Logic: MASE = MAE / naive_MAE. naive_MAE = mean of |actuals_t - actuals_{t-1}|

GET /api/v1/demand/error/stability
  Query: product_id?, target_period?
  Response: {
    by_product: [{ product_id, avg_change_pct, max_change_pct, cycles_measured }]
  }

GET /api/v1/demand/error/value-add
  Query: product_id?, lag=3
  Response: {
    by_product: [{
      product_id,
      statistical_mape,
      final_demand_mape,
      value_add_pct  # (statistical_mape - final_mape) / statistical_mape
    }]
  }

POST /api/v1/demand/error/calculate
  Body: { period_start, period_end, lags: [1, 3, 6] }
  Response: { errors_calculated: int }
  Logic:
    For each (product, period, lag):
      1. Find snapshot from (period - lag months) ago
      2. Find actuals for period from cdm_demand_line
      3. Calculate error metrics
      4. Store in cdm_forecast_error
```

### A.3 Odoo 19 Data Source for Actuals

The forecast error engine needs actual sales data. This comes from Odoo 19 via the connector:

| Odoo 19 Model | Odoo Field | CDM Target | Purpose |
|---|---|---|---|
| `sale.order.line` | `product_uom_qty` | `cdm_demand_line.quantity` | Actual demand quantity |
| `sale.order.line` | `price_subtotal` | `cdm_demand_line.revenue` | Actual revenue |
| `sale.order` | `date_order` | `cdm_demand_line.demand_date` | Period assignment |
| `sale.order` | `state` = 'sale' or 'done' | Filter | Only confirmed orders |
| `stock.picking` (outgoing) | `date_done` | Alternative actuals source | Shipment-based actuals |

**Connector mapping (existing — verify field names for Odoo 19):**

```python
# services/connector/app/odoo/mappers/demand_mapper.py
ODOO_19_DEMAND_FIELDS = {
    'sale.order.line': {
        'id': 'erp_source_id',
        'product_id': 'product_erp_id',  # → lookup cdm_product
        'product_uom_qty': 'quantity',
        'price_subtotal': 'revenue',
        'order_id.date_order': 'demand_date',
        'order_id.partner_id': 'customer_erp_id',  # → lookup cdm_customer
        'order_id.state': '_filter_state',  # Only 'sale' or 'done'
    }
}
```

### A.4 Cursor Prompt — Module A

```
I'm building the Forecast Quality Engine for IPE demand-svc.

Workspace: E:\AISOP\ipe
Service: services/demand-svc/

CONTEXT:
- demand-svc already exists with forecaster.py (SES/Prophet/LSTM)
- Database uses PostgreSQL 16 with Alembic migrations in migrations/versions/
- API uses FastAPI with Pydantic v2 schemas
- All tables require tenant_id column with RLS
- Existing CDM tables: cdm_product, cdm_demand_line, cdm_plant, cdm_tenant

TASKS:
1. Create Alembic migration 043_forecast_quality.py with three tables:
   - cdm_forecast_snapshot (tenant_id, product_id, location_id, snapshot_date, target_period_start, target_period_type, forecast_qty, forecast_source, model_id, model_version)
   - cdm_forecast_error (tenant_id, product_id, location_id, period_start, period_type, lag_periods, forecast_source, forecast_qty, actuals_qty, absolute_error, error_pct, bias, bias_pct, mase_component)
   - cdm_forecast_stability (tenant_id, product_id, target_period_start, cycle_date, prior_cycle_date, current_forecast_qty, prior_forecast_qty, change_qty, change_pct)
   All with RLS on tenant_id. Add indexes per schema above.

2. Create services/demand-svc/app/models/forecast_quality.py — SQLAlchemy models for all three tables.

3. Create services/demand-svc/app/core/forecast_quality.py with:
   - create_snapshot(tenant_id, product_ids, source) → captures current forecast values
   - calculate_errors(tenant_id, period_start, period_end, lags) → computes MAPE, bias, MASE for each (product, period, lag) combination
   - calculate_stability(tenant_id, target_period) → compares current vs prior cycle forecast
   - get_value_add(tenant_id, product_ids, lag) → compares statistical vs final demand MAPE

   MAPE formula: AVG(|forecast - actuals| / actuals) × 100 where actuals > 0
   Weighted MAPE: SUM(|forecast - actuals|) / SUM(actuals) × 100
   Bias: (forecast - actuals) / actuals (signed)
   MASE: MAE / naive_MAE where naive_MAE = mean(|actuals_t - actuals_{t-1}|)

4. Create services/demand-svc/app/api/v1/forecast_quality.py — FastAPI router with endpoints:
   - POST /api/v1/demand/snapshot/create
   - GET /api/v1/demand/error/mape
   - GET /api/v1/demand/error/bias
   - GET /api/v1/demand/error/mase
   - GET /api/v1/demand/error/stability
   - GET /api/v1/demand/error/value-add
   - POST /api/v1/demand/error/calculate
   All require JWT auth + X-Tenant-ID. Use Pydantic v2 response models.

5. Create services/demand-svc/app/schemas/forecast_quality.py — Pydantic response models.

6. Register router in services/demand-svc/app/main.py

7. Create tests in services/demand-svc/tests/test_forecast_quality.py:
   - Test MAPE calculation with known values
   - Test bias calculation (positive and negative)
   - Test MASE with naive baseline
   - Test snapshot creation and retrieval
   - Test stability detection

Follow existing demand-svc code patterns exactly.
```

---

<a name="module-b"></a>
## Module B: ABC/XYZ Segmentation Engine

**Service:** Extend `mat-svc` at `:8002`  
**Migration:** 044  
**Priority:** P1  
**Effort:** 2–3 weeks

### B.1 Database Schema

**Migration 044: `044_product_segmentation.py`**

```python
# Table: cdm_product_segment
cdm_product_segment:
  columns:
    id: UUID PK DEFAULT gen_random_uuid()
    tenant_id: UUID NOT NULL REFERENCES cdm_tenant(id)
    product_id: UUID NOT NULL REFERENCES cdm_product(id)
    segmentation_date: DATE NOT NULL
    # ABC classification (revenue contribution)
    abc_class: VARCHAR(1) NOT NULL  # 'A', 'B', 'C'
    revenue_total: NUMERIC(18,2)
    revenue_share_pct: NUMERIC(8,4)
    cumulative_revenue_pct: NUMERIC(8,4)
    # XYZ classification (demand variability)
    xyz_class: VARCHAR(1) NOT NULL  # 'X', 'Y', 'Z'
    demand_cv: NUMERIC(8,4)  # Coefficient of variation
    demand_mean: NUMERIC(18,4)
    demand_stddev: NUMERIC(18,4)
    # Combined
    combined_segment: VARCHAR(2) NOT NULL  # 'AX', 'AY', 'AZ', 'BX', ..., 'CZ'
    # Recommended policies
    target_service_level_pct: NUMERIC(5,2)  # Based on segment
    forecast_model_recommendation: VARCHAR(50)  # 'arima', 'ses', 'croston'
    review_frequency: VARCHAR(20)  # 'weekly', 'monthly', 'quarterly'
    created_at: TIMESTAMPTZ DEFAULT now()
  indexes:
    - idx_pseg_tenant_product: (tenant_id, product_id, segmentation_date) UNIQUE
    - idx_pseg_segment: (tenant_id, combined_segment)
  rls: tenant_id = current_setting('app.tenant_id')::uuid

# Table: cdm_segmentation_config
cdm_segmentation_config:
  columns:
    id: UUID PK DEFAULT gen_random_uuid()
    tenant_id: UUID NOT NULL REFERENCES cdm_tenant(id)
    abc_a_threshold_pct: NUMERIC(5,2) DEFAULT 80.0  # Top 80% of revenue
    abc_b_threshold_pct: NUMERIC(5,2) DEFAULT 95.0  # Next 15%
    xyz_x_threshold: NUMERIC(5,2) DEFAULT 0.5  # CV < 0.5
    xyz_y_threshold: NUMERIC(5,2) DEFAULT 1.0  # CV < 1.0
    service_level_ax: NUMERIC(5,2) DEFAULT 99.0
    service_level_ay: NUMERIC(5,2) DEFAULT 97.0
    service_level_az: NUMERIC(5,2) DEFAULT 95.0
    service_level_bx: NUMERIC(5,2) DEFAULT 97.0
    service_level_by: NUMERIC(5,2) DEFAULT 95.0
    service_level_bz: NUMERIC(5,2) DEFAULT 90.0
    service_level_cx: NUMERIC(5,2) DEFAULT 95.0
    service_level_cy: NUMERIC(5,2) DEFAULT 90.0
    service_level_cz: NUMERIC(5,2) DEFAULT 85.0
    history_months: INTEGER DEFAULT 12
    created_at: TIMESTAMPTZ DEFAULT now()
  rls: tenant_id = current_setting('app.tenant_id')::uuid
```

### B.2 API Endpoints

**File:** `services/mat-svc/app/api/v1/segmentation.py`

```
POST /api/v1/material/segmentation/run
  Body: { history_months: 12, config_overrides: {} }
  Response: { segmentation_date, products_classified: int, segments: { AX: n, AY: n, ... } }
  Logic:
    1. Pull revenue data from cdm_demand_line for last N months (sum revenue per product)
    2. Sort products by revenue descending
    3. Calculate cumulative revenue percentage
    4. Assign ABC: A if cumulative <= abc_a_threshold, B if <= abc_b_threshold, else C
    5. Pull demand quantity time series per product (weekly/monthly buckets)
    6. Calculate CV = stddev / mean for each product
    7. Assign XYZ: X if CV < xyz_x_threshold, Y if < xyz_y_threshold, else Z
    8. Combine: segment = ABC + XYZ
    9. Assign service level targets and forecast model recommendations per config
    10. Upsert into cdm_product_segment

GET /api/v1/material/segmentation/results
  Query: segmentation_date?, abc_class?, xyz_class?, combined_segment?
  Response: { products: [{ product_id, name, abc, xyz, combined, revenue, cv, service_level }] }

GET /api/v1/material/segmentation/summary
  Response: { matrix: { AX: { count, revenue_pct, avg_cv }, ... }, total_products, date }

GET /api/v1/material/segmentation/config
PUT /api/v1/material/segmentation/config
  Body: { abc_a_threshold_pct, xyz_x_threshold, service_level_ax, ... }
```

### B.3 Odoo 19 Data Source

| Odoo 19 Source | Field | Used For |
|---|---|---|
| `sale.order.line` (state=sale/done) | `price_subtotal` summed by product | ABC revenue ranking |
| `sale.order.line` (state=sale/done) | `product_uom_qty` weekly/monthly | XYZ demand variability (CV) |
| Already synced to `cdm_demand_line` | `quantity`, `revenue` | No new sync needed |

### B.4 Cursor Prompt — Module B

```
I'm building ABC/XYZ segmentation for IPE mat-svc.

Workspace: E:\AISOP\ipe
Service: services/mat-svc/

TASKS:
1. Create Alembic migration 044_product_segmentation.py:
   - cdm_product_segment (tenant_id, product_id, segmentation_date, abc_class, xyz_class, combined_segment, revenue_total, revenue_share_pct, demand_cv, target_service_level_pct, forecast_model_recommendation, review_frequency)
   - cdm_segmentation_config (tenant_id, thresholds for ABC/XYZ, service level targets per segment, history_months)

2. Create services/mat-svc/app/core/segmentation.py:
   - run_segmentation(tenant_id, config) → classifies all products
   ABC algorithm:
     1. Sum revenue per product from cdm_demand_line for last N months
     2. Sort descending by revenue
     3. Calculate cumulative %
     4. A = top 80%, B = next 15%, C = bottom 5% (configurable)
   XYZ algorithm:
     1. Get demand qty time series per product (weekly or monthly buckets)
     2. CV = stddev(qty) / mean(qty)
     3. X = CV < 0.5, Y = CV < 1.0, Z = CV >= 1.0 (configurable)
   Combined: AX, AY, AZ, BX, BY, BZ, CX, CY, CZ
   Policy mapping: each segment gets target service level and forecast model recommendation

3. Create services/mat-svc/app/api/v1/segmentation.py — FastAPI router:
   - POST /run, GET /results, GET /summary, GET/PUT /config

4. Tests with known product data testing ABC and XYZ boundary conditions

Data source: cdm_demand_line (already populated by Odoo sync)
```

---

<a name="module-c"></a>
## Module C: Safety Stock Calculator

**Service:** Extend `mat-svc` at `:8002`  
**Migration:** 045  
**Priority:** P1  
**Effort:** 3–4 weeks

### C.1 Database Schema

**Migration 045: `045_safety_stock.py`**

```python
# Table: cdm_safety_stock
cdm_safety_stock:
  columns:
    id: UUID PK DEFAULT gen_random_uuid()
    tenant_id: UUID NOT NULL
    product_id: UUID NOT NULL REFERENCES cdm_product(id)
    location_id: UUID NULL REFERENCES cdm_plant(id)
    calculation_date: DATE NOT NULL
    # Inputs
    service_level_target_pct: NUMERIC(5,2)  # From segmentation or manual
    z_score: NUMERIC(6,4)  # Normal distribution z for service level
    avg_demand_per_period: NUMERIC(18,4)
    demand_stddev: NUMERIC(18,4)
    demand_cv: NUMERIC(8,4)
    avg_lead_time_periods: NUMERIC(10,2)  # In same period units as demand
    lead_time_stddev: NUMERIC(10,2)
    lead_time_cv: NUMERIC(8,4)
    # Outputs
    safety_stock_qty: NUMERIC(18,4)  # Recommended
    safety_stock_demand_component: NUMERIC(18,4)  # z * σ_demand * √LT
    safety_stock_leadtime_component: NUMERIC(18,4)  # z * d̄ * σ_LT
    reorder_point_qty: NUMERIC(18,4)  # d̄ * LT + SS
    # Comparison
    current_stock_qty: NUMERIC(18,4) NULL  # From Odoo stock.quant
    delta_qty: NUMERIC(18,4) NULL  # recommended - current
    delta_pct: NUMERIC(10,4) NULL
    prior_safety_stock_qty: NUMERIC(18,4) NULL  # Previous cycle
    cycle_change_qty: NUMERIC(18,4) NULL
    # Valuation
    unit_cost: NUMERIC(18,4) NULL
    safety_stock_value: NUMERIC(18,2) NULL
    delta_value: NUMERIC(18,2) NULL
    created_at: TIMESTAMPTZ DEFAULT now()
  indexes:
    - idx_ss_tenant_product: (tenant_id, product_id, calculation_date) UNIQUE
  rls: tenant_id = current_setting('app.tenant_id')::uuid

# Table: cdm_lead_time_history
# Stores actual lead times from Odoo PO receipts for variability calculation
cdm_lead_time_history:
  columns:
    id: UUID PK DEFAULT gen_random_uuid()
    tenant_id: UUID NOT NULL
    product_id: UUID NOT NULL
    supplier_id: UUID NULL
    po_erp_id: VARCHAR(100)
    order_date: DATE
    expected_date: DATE
    actual_receipt_date: DATE
    lead_time_days: INTEGER  # actual_receipt_date - order_date
    lead_time_variance_days: INTEGER  # actual - expected
    created_at: TIMESTAMPTZ DEFAULT now()
  rls: tenant_id = current_setting('app.tenant_id')::uuid
```

### C.2 Core Algorithm

**File:** `services/mat-svc/app/core/safety_stock.py`

```python
"""
Safety Stock Formula (SAP IBP equivalent):
SS = z × σ_d × √(LT) + z × d̄ × σ_LT

Where:
- z = normal distribution z-score for target service level
- σ_d = standard deviation of demand per period
- LT = average lead time in periods
- d̄ = average demand per period
- σ_LT = standard deviation of lead time in periods

Reorder Point:
ROP = d̄ × LT + SS
"""

from scipy.stats import norm
import numpy as np

SERVICE_LEVEL_TO_Z = {
    85.0: 1.036, 90.0: 1.282, 92.0: 1.405, 95.0: 1.645,
    97.0: 1.881, 98.0: 2.054, 99.0: 2.326, 99.5: 2.576, 99.9: 3.090
}

def calculate_safety_stock(
    demand_series: list[float],  # Historical demand per period
    lead_time_days_series: list[int],  # Historical lead times
    service_level_pct: float,
    period_days: int = 7,  # Period length (7 = weekly demand)
) -> dict:
    d_mean = np.mean(demand_series)
    d_std = np.std(demand_series, ddof=1)
    d_cv = d_std / d_mean if d_mean > 0 else 0

    lt_periods = np.mean(lead_time_days_series) / period_days
    lt_std_periods = np.std(lead_time_days_series, ddof=1) / period_days
    lt_cv = lt_std_periods / lt_periods if lt_periods > 0 else 0

    z = norm.ppf(service_level_pct / 100.0)

    ss_demand = z * d_std * np.sqrt(lt_periods)
    ss_leadtime = z * d_mean * lt_std_periods
    safety_stock = ss_demand + ss_leadtime
    reorder_point = d_mean * lt_periods + safety_stock

    return {
        'safety_stock_qty': round(safety_stock, 2),
        'safety_stock_demand_component': round(ss_demand, 2),
        'safety_stock_leadtime_component': round(ss_leadtime, 2),
        'reorder_point_qty': round(reorder_point, 2),
        'z_score': round(z, 4),
        'avg_demand_per_period': round(d_mean, 4),
        'demand_stddev': round(d_std, 4),
        'demand_cv': round(d_cv, 4),
        'avg_lead_time_periods': round(lt_periods, 2),
        'lead_time_stddev': round(lt_std_periods, 2),
        'lead_time_cv': round(lt_cv, 4),
    }
```

### C.3 API Endpoints

**File:** `services/mat-svc/app/api/v1/safety_stock.py`

```
POST /api/v1/material/safety-stock/calculate
  Body: { products: ["all" | UUID[]], history_months: 12, use_segmentation_service_levels: true }
  Response: { calculated: int, results: [{ product_id, safety_stock_qty, reorder_point, delta_qty, delta_value }] }

GET /api/v1/material/safety-stock/results
  Query: product_id?, abc_class?, sort_by=delta_value, order=desc
  Response: { products: [{ product_id, name, segment, safety_stock, current_stock, delta, value }] }

GET /api/v1/material/safety-stock/summary
  Response: {
    total_safety_stock_value, total_delta_value,
    by_segment: { AX: { count, total_value, avg_service_level }, ... },
    over_stocked: [top 10 products by positive delta value],
    under_stocked: [top 10 products by negative delta value]
  }

GET /api/v1/material/safety-stock/lead-time
  Query: product_id?, supplier_id?
  Response: { products: [{ product_id, avg_lead_time, lt_stddev, lt_cv, samples }] }
```

### C.4 Odoo 19 Data Sources

**Lead time data from Odoo 19 purchase orders:**

| Odoo 19 Model | Field | CDM Target | Purpose |
|---|---|---|---|
| `purchase.order.line` | `product_id` | product_erp_id → cdm_product | Product lookup |
| `purchase.order` | `date_order` | cdm_lead_time_history.order_date | PO creation date |
| `purchase.order` | `date_planned` | cdm_lead_time_history.expected_date | Expected delivery |
| `stock.picking` (incoming) | `date_done` | cdm_lead_time_history.actual_receipt_date | Actual receipt date |
| `purchase.order` | `partner_id` | supplier_id → cdm_supplier | Supplier lookup |

**New connector mapper needed:**

```python
# services/connector/app/odoo/mappers/lead_time_mapper.py
# Sync purchase.order.line + stock.picking to cdm_lead_time_history

async def sync_lead_times(session, odoo_client, tenant_id):
    """
    1. Fetch purchase.order.line with state in ('purchase', 'done')
    2. For each PO line, find matching stock.picking.move (incoming)
    3. Calculate lead_time_days = picking.date_done - po.date_order
    4. Upsert into cdm_lead_time_history
    """
```

**Current stock from Odoo 19 (FR-R1-05 — stock.quant sync):**

| Odoo 19 Model | Field | CDM Target | Purpose |
|---|---|---|---|
| `stock.quant` | `product_id` | product lookup | Which product |
| `stock.quant` | `quantity` | current_stock_qty | On-hand quantity |
| `stock.quant` | `location_id` | location lookup | Which warehouse |
| Filter: `location_id.usage` = 'internal' | | | Only internal locations |

### C.5 Cursor Prompt — Module C

```
I'm building the Safety Stock Calculator for IPE mat-svc.

Workspace: E:\AISOP\ipe
Service: services/mat-svc/

TASKS:
1. Create Alembic migration 045_safety_stock.py:
   - cdm_safety_stock (all fields from schema above)
   - cdm_lead_time_history (tenant_id, product_id, supplier_id, po_erp_id, order_date, expected_date, actual_receipt_date, lead_time_days, lead_time_variance_days)

2. Create services/mat-svc/app/core/safety_stock.py:
   Implementation of the statistical safety stock formula:
   SS = z × σ_d × √(LT) + z × d̄ × σ_LT
   ROP = d̄ × LT + SS
   Use scipy.stats.norm.ppf for z-score calculation.
   Include the full calculate_safety_stock() function from the spec above.

3. Create service layer services/mat-svc/app/core/safety_stock_service.py:
   - For each product: get demand history from cdm_demand_line, get lead time history from cdm_lead_time_history
   - Get service level target from cdm_product_segment (if segmentation ran) or default 95%
   - Call calculate_safety_stock()
   - Compare to current stock from Odoo sync (cdm_inventory or stock.quant data)
   - Calculate delta and valuation
   - Upsert into cdm_safety_stock

4. Create API router services/mat-svc/app/api/v1/safety_stock.py:
   - POST /calculate, GET /results, GET /summary, GET /lead-time

5. Create services/connector/app/odoo/mappers/lead_time_mapper.py:
   - Sync purchase.order + stock.picking (incoming) to cdm_lead_time_history
   - Odoo 19 fields: purchase.order.date_order, purchase.order.date_planned, stock.picking.date_done (where picking_type_code='incoming')
   - lead_time_days = date_done - date_order

6. Tests with known demand series and lead time data, verifying SS formula output
```

---

<a name="module-d"></a>
## Module D: Statistical Forecasting Upgrade

**Service:** Modify `demand-svc` at `:8040`  
**Migration:** None (no schema changes)  
**Priority:** P1  
**Effort:** 2–3 weeks

### D.1 Add ARIMA/SARIMA Forecasters

**File:** `services/demand-svc/app/core/forecasters/arima.py`

```python
"""
Add ARIMA and SARIMA to the existing forecaster factory.
Uses statsmodels.tsa.arima.model.ARIMA and statsmodels.tsa.statespace.sarimax.SARIMAX

Best-fit selection:
1. Run SES, ARIMA, SARIMA (and Prophet if available) on historical data
2. Hold out last 3 periods as validation set
3. Calculate MAPE on validation set for each model
4. Select model with lowest MAPE
5. Re-train selected model on full history
6. Generate forecast
"""

from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
```

### D.2 Segment-Driven Model Selection

**File:** `services/demand-svc/app/core/forecasters/model_selector.py`

SAP IBP uses ABC/XYZ segmentation to drive forecast model selection. IPE should too:

| Segment | Recommended Models | Rationale |
|---|---|---|
| AX, BX | ARIMA, SARIMA, Prophet | Stable demand, complex patterns worth modelling |
| AY, BY | SES, ARIMA | Moderate variability, simpler models often win |
| AZ, BZ | SES with dampening | High variability, complex models overfit |
| CX, CY | SES | Low revenue, not worth model complexity |
| CZ | Croston TSB (if intermittent) or SES | Intermittent demand needs special handling |

### D.3 Cursor Prompt — Module D

```
I'm upgrading demand forecasting in IPE demand-svc to add ARIMA/SARIMA and best-fit selection.

Workspace: E:\AISOP\ipe
Service: services/demand-svc/

Current: services/demand-svc/app/core/forecaster.py has SES (and optional Prophet/LSTM)

TASKS:
1. Install statsmodels: add to services/demand-svc/requirements.txt (or pyproject.toml)

2. Create services/demand-svc/app/core/forecasters/arima.py:
   - ARIMAForecaster class implementing same interface as existing SES forecaster
   - Auto-order selection using AIC (try p=0-3, d=0-2, q=0-3)
   - SARIMA with seasonal_order auto-detection if seasonality detected

3. Create services/demand-svc/app/core/forecasters/model_selector.py:
   - best_fit_forecast(demand_series, horizon, segment=None)
   - Runs SES, ARIMA, SARIMA in parallel
   - Holds out last 3 periods for validation
   - Selects by lowest MAPE on validation set
   - If segment provided, restricts candidate models per segment table:
     AX/BX → [ARIMA, SARIMA, SES], AY/BY → [SES, ARIMA], AZ/BZ/CX/CY → [SES], CZ → [SES/Croston]
   - Returns forecast + selected_model_id + validation_mape

4. Update existing forecaster factory to include ARIMA and best-fit options

5. Update POST /api/v1/demand/forecast endpoint to accept model="best_fit" parameter

6. Tests: compare SES vs ARIMA on known seasonal data, verify ARIMA wins when seasonality present
```

---

<a name="module-e"></a>
## Module E: Capacity Utilisation Alerts

**Service:** Extend `cap-svc` at `:8003`  
**Migration:** 046  
**Priority:** P1  
**Effort:** 1–2 weeks

### E.1 Database Schema

**Migration 046: `046_capacity_alerts.py`**

```python
# Table: cdm_capacity_utilisation
cdm_capacity_utilisation:
  columns:
    id: UUID PK DEFAULT gen_random_uuid()
    tenant_id: UUID NOT NULL
    work_center_id: UUID NOT NULL REFERENCES cdm_work_center(id)
    period_start: DATE NOT NULL
    period_type: VARCHAR(10) DEFAULT 'week'
    capacity_available_hours: NUMERIC(10,2)
    capacity_used_hours: NUMERIC(10,2)
    utilisation_pct: NUMERIC(6,2)  # used / available × 100
    overload: BOOLEAN DEFAULT FALSE  # utilisation > threshold
    overload_hours: NUMERIC(10,2) DEFAULT 0  # hours over capacity
    calculated_at: TIMESTAMPTZ DEFAULT now()
  indexes:
    - idx_cutil_tenant_wc: (tenant_id, work_center_id, period_start)
  rls: tenant_id = current_setting('app.tenant_id')::uuid

# Table: cdm_capacity_alert_config
cdm_capacity_alert_config:
  columns:
    id: UUID PK DEFAULT gen_random_uuid()
    tenant_id: UUID NOT NULL
    overload_threshold_pct: NUMERIC(5,2) DEFAULT 90.0
    critical_threshold_pct: NUMERIC(5,2) DEFAULT 100.0
    alert_enabled: BOOLEAN DEFAULT TRUE
    created_at: TIMESTAMPTZ DEFAULT now()
  rls: tenant_id = current_setting('app.tenant_id')::uuid
```

### E.2 API Endpoints

```
POST /api/v1/capacity/utilisation/calculate
  Body: { period_start, period_end, period_type: "week" }
  Response: { work_centers_calculated: int, overloaded: int }

GET /api/v1/capacity/utilisation
  Query: work_center_id?, period_start?, period_end?, overloaded_only=false
  Response: { work_centers: [{ wc_id, wc_name, period, available, used, utilisation_pct, overload }] }

GET /api/v1/capacity/utilisation/alerts
  Response: {
    overloaded: [{ wc_id, wc_name, period, utilisation_pct, overload_hours }],
    critical: [those above critical_threshold]
  }

GET /api/v1/capacity/utilisation/ranking
  Query: period_start, period_end, top_n=10
  Response: { ranked: [{ wc_id, wc_name, avg_utilisation, peak_utilisation, overloaded_periods }] }
```

### E.3 Odoo 19 Data Source

Capacity data comes from Odoo 19 work centres (already synced by connector):

| Odoo 19 Model | Field | CDM Target | Purpose |
|---|---|---|---|
| `mrp.workcenter` | `capacity` | cdm_work_center.capacity | Products per hour |
| `mrp.workcenter` | `time_start`, `time_stop` | Setup/teardown time | Effective available hours |
| `resource.calendar` (via workcenter) | Working hours definition | capacity_available_hours | Shift-based availability |
| `mrp.workorder` | `duration_expected` | capacity_used_hours | Planned load per MO |
| `mrp.workorder` | `workcenter_id` | work_center_id | Assignment |

---

<a name="module-f"></a>
## Module F: S&OP Process Engine

**Service:** NEW `sop-svc` at `:8110`  
**Migration:** 047  
**Priority:** P2 (R3)  
**Effort:** 8–12 weeks

### F.1 Service Structure

```
services/sop-svc/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app on :8110
│   ├── api/
│   │   └── v1/
│   │       ├── sop.py       # S&OP cycle management
│   │       ├── consensus.py # Consensus demand endpoints
│   │       ├── versions.py  # Version management
│   │       └── reviews.py   # Stage review dashboards
│   ├── core/
│   │   ├── consensus.py     # Consensus calculation engine
│   │   ├── version.py       # Version operations
│   │   ├── cycle.py         # Cycle state machine
│   │   └── cost_rollup.py   # Cost aggregation
│   ├── models/
│   │   ├── sop_cycle.py
│   │   ├── sop_version.py
│   │   ├── consensus_demand.py
│   │   └── stage_gate.py
│   └── schemas/
│       ├── sop.py
│       ├── consensus.py
│       └── version.py
├── tests/
│   ├── test_consensus.py
│   ├── test_cycle.py
│   └── test_versions.py
├── Dockerfile
├── pyproject.toml
└── requirements.txt
```

### F.2 Database Schema

**Migration 047: `047_sop_engine.py`**

```python
# Table: cdm_sop_cycle
# Represents one S&OP planning cycle (typically monthly)
cdm_sop_cycle:
  columns:
    id: UUID PK
    tenant_id: UUID NOT NULL
    cycle_name: VARCHAR(100)  # "September 2027 S&OP"
    cycle_month: DATE NOT NULL  # First day of the planning month
    status: VARCHAR(30) NOT NULL DEFAULT 'draft'
      # States: draft → demand_review → supply_review → reconciliation → management_review → closed
    demand_review_deadline: TIMESTAMPTZ NULL
    supply_review_deadline: TIMESTAMPTZ NULL
    reconciliation_deadline: TIMESTAMPTZ NULL
    management_review_deadline: TIMESTAMPTZ NULL
    created_by: UUID REFERENCES cdm_user(id)
    created_at: TIMESTAMPTZ DEFAULT now()
    closed_at: TIMESTAMPTZ NULL

# Table: cdm_sop_version
# Versions within a cycle: baseline, upside, downside, what-if
cdm_sop_version:
  columns:
    id: UUID PK
    tenant_id: UUID NOT NULL
    cycle_id: UUID NOT NULL REFERENCES cdm_sop_cycle(id)
    version_type: VARCHAR(20) NOT NULL  # 'baseline', 'upside', 'downside', 'whatif'
    version_name: VARCHAR(100)
    description: TEXT NULL
    is_active: BOOLEAN DEFAULT TRUE
    created_by: UUID
    created_at: TIMESTAMPTZ DEFAULT now()

# Table: cdm_consensus_demand
# Consensus demand per version × product × location × period
cdm_consensus_demand:
  columns:
    id: UUID PK
    tenant_id: UUID NOT NULL
    version_id: UUID NOT NULL REFERENCES cdm_sop_version(id)
    product_id: UUID NOT NULL REFERENCES cdm_product(id)
    location_id: UUID NULL
    customer_id: UUID NULL
    period_start: DATE NOT NULL
    period_type: VARCHAR(10) DEFAULT 'month'
    # Demand quantities
    sales_forecast_qty: NUMERIC(18,4) NULL
    marketing_forecast_qty: NUMERIC(18,4) NULL
    statistical_forecast_qty: NUMERIC(18,4) NULL
    finance_plan_qty: NUMERIC(18,4) NULL
    consensus_qty: NUMERIC(18,4)  # Weighted result
    # Revenue and cost
    planned_price: NUMERIC(18,4) NULL
    consensus_revenue: NUMERIC(18,2) NULL  # consensus_qty × planned_price
    cost_per_unit: NUMERIC(18,4) NULL
    consensus_cost: NUMERIC(18,2) NULL  # consensus_qty × cost_per_unit
    consensus_profit: NUMERIC(18,2) NULL  # revenue - cost
    # Constrained (after supply review)
    constrained_demand_qty: NUMERIC(18,4) NULL
    constrained_revenue: NUMERIC(18,2) NULL
    lost_sales_qty: NUMERIC(18,4) NULL  # consensus - constrained
    lost_sales_value: NUMERIC(18,2) NULL
    created_at: TIMESTAMPTZ DEFAULT now()
  indexes:
    - idx_cd_version_product: (version_id, product_id, period_start) UNIQUE

# Table: cdm_sop_stage_gate
# Approval records for each stage
cdm_sop_stage_gate:
  columns:
    id: UUID PK
    tenant_id: UUID NOT NULL
    cycle_id: UUID NOT NULL
    stage: VARCHAR(30) NOT NULL  # demand_review, supply_review, reconciliation, management_review
    status: VARCHAR(20) NOT NULL  # 'pending', 'approved', 'rejected'
    approved_by: UUID NULL
    approved_at: TIMESTAMPTZ NULL
    notes: TEXT NULL
    created_at: TIMESTAMPTZ DEFAULT now()

# Table: cdm_sop_consensus_weight
# Configurable weights for consensus calculation per tenant
cdm_sop_consensus_weight:
  columns:
    id: UUID PK
    tenant_id: UUID NOT NULL
    weight_sales: NUMERIC(5,2) DEFAULT 0.30
    weight_statistical: NUMERIC(5,2) DEFAULT 0.40
    weight_marketing: NUMERIC(5,2) DEFAULT 0.20
    weight_finance: NUMERIC(5,2) DEFAULT 0.10
    created_at: TIMESTAMPTZ DEFAULT now()
```

### F.3 Consensus Calculation

**File:** `services/sop-svc/app/core/consensus.py`

```python
"""
Consensus demand = weighted average of input forecasts.

Default weights (configurable per tenant):
- Statistical forecast: 40%
- Sales forecast: 30%
- Marketing forecast: 20%
- Finance plan: 10%

If an input is NULL for a product-period, redistribute its weight proportionally.

SAP IBP equivalent: CONSENSUSDEMANDQTY calculation with SOPDEMANDPLANNINGQTY fallback.
"""

def calculate_consensus(
    sales_qty: float | None,
    stat_qty: float | None,
    marketing_qty: float | None,
    finance_qty: float | None,
    weights: dict,
) -> float:
    inputs = []
    if sales_qty is not None:
        inputs.append((sales_qty, weights['sales']))
    if stat_qty is not None:
        inputs.append((stat_qty, weights['statistical']))
    if marketing_qty is not None:
        inputs.append((marketing_qty, weights['marketing']))
    if finance_qty is not None:
        inputs.append((finance_qty, weights['finance']))

    if not inputs:
        return 0.0

    total_weight = sum(w for _, w in inputs)
    return sum(qty * (w / total_weight) for qty, w in inputs)
```

### F.4 Odoo 19 Data Sources for S&OP

| S&OP Input | Odoo 19 Source | Sync Method |
|---|---|---|
| Sales forecast | `sale.order.line` (confirmed, future dates) | Existing demand sync — filter by `order_id.date_order` > today |
| Actuals quantity | `sale.order.line` (done) | Existing demand sync — filter state='done' |
| Actuals revenue | `sale.order.line.price_subtotal` (done) | Existing demand sync |
| AOP (Annual Operating Plan) | Not in standard Odoo. Manual upload or budget module. | CSV import endpoint or manual entry in S&OP UI |
| Marketing forecast | Not in standard Odoo. Manual input. | Direct entry in S&OP demand review UI |
| Statistical forecast | Generated by demand-svc forecaster | Internal API call to demand-svc |
| Cost per unit | `product.product.standard_price` | Existing product sync — add `standard_price` field |
| Planned price | `product.product.list_price` or pricelist | Existing product sync — add `list_price` field |
| Current inventory | `stock.quant` (FR-R1-05) | Existing or R1.1 sync |
| Open orders | `sale.order.line` where state='sale', not shipped | Filter on existing demand sync |

**New connector fields needed:**

```python
# Add to services/connector/app/odoo/mappers/product_mapper.py
ODOO_19_PRODUCT_EXTRA_FIELDS = {
    'product.product': {
        'standard_price': 'unit_cost',    # → cdm_product.unit_cost (new column)
        'list_price': 'list_price',        # → cdm_product.list_price (new column)
    }
}

# Migration: ALTER TABLE cdm_product ADD COLUMN unit_cost NUMERIC(18,4) NULL;
# Migration: ALTER TABLE cdm_product ADD COLUMN list_price NUMERIC(18,4) NULL;
```

### F.5 S&OP API Endpoints

```
# Cycle management
POST /api/v1/sop/cycle                          # Create new cycle
GET  /api/v1/sop/cycle                          # List cycles
GET  /api/v1/sop/cycle/{id}                     # Get cycle with stages
POST /api/v1/sop/cycle/{id}/advance             # Advance to next stage
POST /api/v1/sop/cycle/{id}/stage/{stage}/approve  # Approve stage gate

# Consensus demand
POST /api/v1/sop/consensus/calculate            # Run consensus calculation
GET  /api/v1/sop/consensus                      # Get consensus by version/product/period
PUT  /api/v1/sop/consensus/{id}                 # Manual override of consensus qty

# Versions
POST /api/v1/sop/version                        # Create new version (clone from baseline)
GET  /api/v1/sop/version/compare                # Compare two versions side by side
DELETE /api/v1/sop/version/{id}                  # Delete what-if version

# Supply review (calls cap-svc)
POST /api/v1/sop/supply-review/run              # Run supply planning on consensus demand
GET  /api/v1/sop/supply-review/results          # Constrained demand, lost sales, capacity util

# Reconciliation
GET  /api/v1/sop/reconciliation/dashboard       # Revenue vs AOP, profit by version, top risks

# Management review
GET  /api/v1/sop/management-review/executive-summary  # AI-generated executive S&OP brief

# Configuration
GET  /api/v1/sop/config/weights                 # Get consensus weights
PUT  /api/v1/sop/config/weights                 # Set consensus weights
```

### F.6 Cursor Prompt — Module F

```
I'm building the S&OP Process Engine as a new service for IPE.

Workspace: E:\AISOP\ipe
New service: services/sop-svc/

CONTEXT:
- Follow the exact service structure of existing services (e.g., services/demand-svc/)
- FastAPI on port 8110
- PostgreSQL with Alembic, RLS on tenant_id
- JWT auth + X-Tenant-ID header on all endpoints
- Existing services: dpe-svc (:8001), demand-svc (:8040), cap-svc (:8003), mat-svc (:8002)

TASKS:
1. Create the full service directory structure as specified in F.1 above

2. Create Alembic migration 047_sop_engine.py with all 5 tables from F.2

3. Create core modules:
   - consensus.py: calculate_consensus() with weighted average and NULL redistribution
   - version.py: create version (clone baseline), compare versions
   - cycle.py: state machine (draft → demand_review → supply_review → reconciliation → management_review → closed)
   - cost_rollup.py: consensus_revenue = qty × price, consensus_cost = qty × unit_cost, profit = rev - cost

4. Create API routes for all endpoints in F.5

5. Create Dockerfile matching existing service pattern

6. Add to docker-compose.release2.yml and kong.release2.yml

7. Tests: consensus calculation, cycle state machine, version comparison

The S&OP engine coordinates data from:
- demand-svc: statistical forecast (GET /api/v1/demand/forecast)
- mat-svc: safety stock (GET /api/v1/material/safety-stock/results)
- cap-svc: capacity utilisation (GET /api/v1/capacity/utilisation)
- connector: Odoo actuals, prices, costs
It synthesises these into a consensus view with version comparison.
```

---

<a name="odoo-extensions"></a>
## 7. Odoo 19 Connector Extensions — Complete Field Map

### 7.1 New Entities to Sync

| Entity | Odoo 19 Model | New/Existing | CDM Target | Purpose |
|---|---|---|---|---|
| Lead time history | `purchase.order` + `stock.picking` | **NEW** | `cdm_lead_time_history` | Safety stock LT variability |
| Product costs | `product.product.standard_price` | **EXTEND** | `cdm_product.unit_cost` | Cost rollup, S&OP P&L |
| Product prices | `product.product.list_price` | **EXTEND** | `cdm_product.list_price` | S&OP revenue calculation |
| Stock quant | `stock.quant` | **R1.1** (FR-R1-05) | Material availability | Current stock for SS delta |
| Sales actuals (revenue) | `sale.order.line.price_subtotal` | **EXTEND** | `cdm_demand_line.revenue` | Forecast error, S&OP actuals |
| Open orders | `sale.order.line` (state='sale') | **EXTEND** | `cdm_demand_line.status` | Forecast consumption |

### 7.2 Extended Odoo 19 XML-RPC Calls

**New mapper: `services/connector/app/odoo/mappers/lead_time_mapper.py`**

```python
LEAD_TIME_SYNC_SPEC = {
    'model': 'purchase.order',
    'domain': [('state', 'in', ['purchase', 'done'])],
    'fields': ['id', 'name', 'date_order', 'date_planned', 'partner_id', 'state'],
    'related': {
        'order_line': {
            'model': 'purchase.order.line',
            'fields': ['product_id', 'product_qty', 'date_planned'],
        },
        'picking': {
            'model': 'stock.picking',
            'domain': [('picking_type_code', '=', 'incoming'), ('state', '=', 'done')],
            'fields': ['date_done', 'origin'],  # origin links to PO name
        }
    }
}
```

**Extended product sync fields:**

```python
# Add to existing product mapper
PRODUCT_EXTRA_FIELDS_ODOO_19 = [
    'standard_price',  # → cdm_product.unit_cost
    'list_price',      # → cdm_product.list_price
    'weight',          # → cdm_product.weight (useful for transport cost)
    'volume',          # → cdm_product.volume
]
```

### 7.3 Connector Sync Schedule

| Sync Type | Frequency | Entities |
|---|---|---|
| Core planning data | Every 15 min (existing) | MOs, BOMs, routings, WCs, products, demands, supply |
| Lead time history | Daily (new) | Purchase orders + incoming receipts |
| Product costs/prices | Daily (extend) | standard_price, list_price |
| Stock quant | Every 15 min (R1.1) | On-hand inventory |

### 7.4 Cursor Prompt — Odoo Extensions

```
I'm extending the IPE Odoo 19 connector with new sync entities for planning intelligence modules.

Workspace: E:\AISOP\ipe
Service: services/connector/

CURRENT STATE:
- Connector syncs: MOs, BOMs, routings, work centres, products, customers, suppliers, demands, supply orders
- XML-RPC via odoo_client.py
- Mappers in services/connector/app/odoo/mappers/

TASKS:
1. Create services/connector/app/odoo/mappers/lead_time_mapper.py:
   - Fetch purchase.order (state in ['purchase','done']) via XML-RPC
   - For each PO, find matching stock.picking (incoming, state='done') via origin field
   - Calculate lead_time_days = picking.date_done - po.date_order
   - Upsert into cdm_lead_time_history
   - Handle: missing picking (PO not yet received), multiple pickings per PO (partial receipts)

2. Extend product mapper to sync additional fields:
   - product.product.standard_price → cdm_product.unit_cost
   - product.product.list_price → cdm_product.list_price
   - Requires migration: ALTER TABLE cdm_product ADD COLUMN unit_cost NUMERIC(18,4), list_price NUMERIC(18,4)

3. Extend demand mapper to capture revenue:
   - sale.order.line.price_subtotal → cdm_demand_line.revenue (if not already synced)
   - Add order status: 'confirmed' vs 'done' for open orders vs actuals distinction

4. Add lead_time sync to the sync scheduler:
   - Daily schedule (not every 15 min — PO data changes less frequently)
   - Separate from the main 15-min MO sync cycle

5. Tests: lead time mapper with mock Odoo XML-RPC responses
```

---

<a name="integration-flows"></a>
## 8. Cross-Module Integration Flows

### 8.1 Monthly S&OP Cycle Flow

```
1. DEMAND REVIEW (Week 1)
   ├── demand-svc → statistical forecast (auto-generated)
   ├── Connector → Odoo 19 sales actuals (synced)
   ├── Manual → sales forecast, marketing forecast (entered in S&OP UI)
   ├── sop-svc → consensus calculation (weighted average)
   └── Gate: Demand review approved by Ops Director

2. SUPPLY REVIEW (Week 2)
   ├── sop-svc → passes consensus demand to cap-svc
   ├── cap-svc → runs OR-Tools solver with consensus demand as input
   ├── cap-svc → returns constrained demand, capacity utilisation
   ├── mat-svc → safety stock check against consensus demand
   ├── sop-svc → calculates lost sales = consensus - constrained
   └── Gate: Supply review approved by Supply Manager

3. RECONCILIATION (Week 3)
   ├── sop-svc → compares revenue (consensus × price vs AOP)
   ├── sop-svc → compares profit (revenue - cost per version)
   ├── sop-svc → highlights top 5 gaps vs plan
   ├── nlp-svc → AI generates reconciliation narrative
   └── Gate: Reconciliation approved by Finance

4. MANAGEMENT REVIEW (Week 4)
   ├── nlp-svc → generates executive S&OP briefing from all data
   ├── sop-svc → presents version comparison (baseline/upside/downside)
   ├── Decision: approve consensus plan or request revision
   └── Gate: Management approval → close cycle
```

### 8.2 Data Flow Between New Modules

```
Odoo 19 ──sync──→ Connector ──writes──→ CDM Tables
                                           │
                    ┌──────────────────────┼──────────────────┐
                    │                      │                  │
              demand-svc              mat-svc             cap-svc
              (forecast)         (segmentation,        (scheduling,
                 │               safety stock)         utilisation)
                 │                      │                  │
                 └──────────┬──────────┘──────────┬───────┘
                            │                      │
                         sop-svc               fea-svc
                    (consensus, S&OP)       (feasibility)
                            │                      │
                            └──────────┬───────────┘
                                       │
                                   nlp-svc
                              (Copilot + S&OP
                               narrative + alerts)
```

---

<a name="key-figure-registry"></a>
## 9. Key Figure Registry

IPE's equivalent of SAP IBP's 200+ key figures, consolidated to ~45 that matter:

| ID | Key Figure | Domain | Source | Unit |
|---|---|---|---|---|
| KF-D01 | ACTUALSQTY | Demand | cdm_demand_line (state=done) | qty |
| KF-D02 | ACTUALSREV | Demand | cdm_demand_line.revenue | currency |
| KF-D03 | STATISTICALFORECASTQTY | Demand | demand-svc forecast | qty |
| KF-D04 | SALESFORECASTQTY | Demand | sop-svc manual input | qty |
| KF-D05 | MARKETINGFORECASTQTY | Demand | sop-svc manual input | qty |
| KF-D06 | CONSENSUSDEMANDQTY | S&OP | sop-svc consensus | qty |
| KF-D07 | CONSENSUSDEMANDREV | S&OP | qty × planned_price | currency |
| KF-D08 | CONSTRAINEDDEMAND | S&OP | cap-svc solver output | qty |
| KF-D09 | LOSTSALESQTY | S&OP | consensus - constrained | qty |
| KF-D10 | FORECASTMAPE | Quality | cdm_forecast_error | pct |
| KF-D11 | FORECASTBIAS | Quality | cdm_forecast_error | pct |
| KF-S01 | PRODUCTION | Supply | cdm_manufacturing_order (scheduled) | qty |
| KF-S02 | CAPACITYSUPPLY | Supply | cdm_work_center.capacity × hours | hours |
| KF-S03 | CAPACITYUSAGE | Supply | sum of MO durations per WC | hours |
| KF-S04 | UTILISATIONPCT | Supply | usage / supply × 100 | pct |
| KF-S05 | PROJECTEDINVENTORY | Supply | on_hand + receipts - demand | qty |
| KF-I01 | SAFETYSTOCK | Inventory | cdm_safety_stock.safety_stock_qty | qty |
| KF-I02 | REORDERPOINT | Inventory | cdm_safety_stock.reorder_point_qty | qty |
| KF-I03 | CURRENTSTOCK | Inventory | stock.quant sync | qty |
| KF-I04 | SAFETYSTOCKDELTA | Inventory | recommended - current | qty |
| KF-I05 | SAFETYSTOCKVALUE | Inventory | qty × unit_cost | currency |
| KF-F01 | COSTPERUNIT | Finance | cdm_product.unit_cost (from Odoo) | currency |
| KF-F02 | PLANNEDPRICE | Finance | cdm_product.list_price (from Odoo) | currency |
| KF-F03 | GROSSPROFIT | Finance | revenue - (qty × cost) | currency |
| KF-F04 | AOPQTY | Finance | sop-svc manual/import | qty |
| KF-F05 | AOPREV | Finance | sop-svc manual/import | currency |
| KF-G01 | FEASIBILITYSCORE | Gate | fea-svc | score |
| KF-G02 | OTDPCT | Gate | cdm_otd_snapshot | pct |
| KF-G03 | ABCSEGMENT | Class | cdm_product_segment | class |
| KF-G04 | XYZSEGMENT | Class | cdm_product_segment | class |

---

<a name="copilot-tools"></a>
## 11. Copilot Tool Extensions for Planning Intelligence

**File:** `services/nlp-svc/app/core/copilot_tools.py` — add these tools:

| Tool | API Call | What It Returns |
|---|---|---|
| `get_forecast_accuracy` | demand-svc `/demand/error/mape` | MAPE and bias by product/period |
| `get_product_segments` | mat-svc `/material/segmentation/summary` | ABC/XYZ matrix with counts |
| `get_safety_stock_gaps` | mat-svc `/material/safety-stock/summary` | Over/under stocked products |
| `get_capacity_alerts` | cap-svc `/capacity/utilisation/alerts` | Overloaded work centres |
| `get_sop_status` | sop-svc `/sop/cycle` | Current S&OP cycle stage |
| `get_consensus_vs_constrained` | sop-svc `/sop/reconciliation/dashboard` | Revenue gap, lost sales |
| `get_version_comparison` | sop-svc `/sop/version/compare` | Side-by-side version KPIs |
| `generate_sop_briefing` | Internal Claude call | Full executive S&OP narrative |

**Example Copilot interactions after modules built:**

> **Planner:** "What is our forecast accuracy this quarter?"
> **Copilot:** "Weighted MAPE across all products is 18.3% at 3-month lag. Segment A products are at 12.1% (good). Segment C products are at 34.7% — these are pulling your overall accuracy down. I recommend switching segment C to simple SES instead of ARIMA to reduce overfitting."

> **Ops Director:** "Where are we overstocked?"
> **Copilot:** "You have $42,000 in excess safety stock across 15 products. The top 3 are copper wire (12mm), transformer core L-type, and insulation tape — together accounting for $28,000. All three are in the B-Z segment with high demand variability. Reducing their service level target from 95% to 90% would save $18,000 in holding cost with minimal stockout risk."

> **CEO:** "Generate the September S&OP briefing."
> **Copilot:** Generates a structured narrative covering consensus demand vs AOP, constrained demand, lost sales, capacity utilisation, safety stock status, and top 5 decisions required — all from live data across demand-svc, cap-svc, mat-svc, and sop-svc.

---

## Migration Execution Order

| # | Migration | Module | Pre-requisite |
|---|---|---|---|
| 043 | forecast_quality | A | None |
| 044 | product_segmentation | B | None |
| 045 | safety_stock | C | 044 (uses segments for service levels) |
| 046 | capacity_alerts | E | None |
| 047 | sop_engine | F | 043, 044, 045 (uses forecast, segments, safety stock) |
| 048 | product_cost_fields | Odoo ext | None (ALTER cdm_product) |

Run in order. Each migration is independent except 045 and 047 which reference prior tables.

---

## Build Order for Cursor Execution

1. **Module B** (ABC/XYZ) — 2–3 weeks. No dependencies. Foundation for everything else.
2. **Module A** (Forecast Quality) — 4–6 weeks. No dependencies.
3. **Module D** (ARIMA/SARIMA) — 2–3 weeks. Benefits from Module B (segment-driven model selection).
4. **Odoo Extensions** — 2–3 weeks. Adds lead time data needed for Module C.
5. **Module C** (Safety Stock) — 3–4 weeks. Uses Module B segments + Odoo lead time data.
6. **Module E** (Capacity Alerts) — 1–2 weeks. Independent.
7. **Module F** (S&OP Engine) — 8–12 weeks. Uses all prior modules.

**Total sequential: 22–34 weeks with 1 developer. Parallel: 14–20 weeks with 2 developers.**

---

*End of Technical Specification. Execute modules in build order. Each Cursor prompt is self-contained.*
