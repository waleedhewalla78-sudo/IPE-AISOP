# IPE Planning Intelligence — Cursor Prompt Library

**Usage:** Copy each prompt into Cursor's chat. Execute in order. Wait for completion and verify acceptance criteria before moving to next prompt.

**Workspace:** `E:\AISOP\ipe`

---

## PROMPT 0 — Master Context (Run First, Every Session)

> Paste this at the start of every Cursor session before any module prompt.

```
You are building planning intelligence modules for IPE (Intelligent Planning Engine), an AI-powered Advanced Planning & Scheduling platform for MENA discrete manufacturers.

WORKSPACE: E:\AISOP\ipe

ARCHITECTURE:
- Backend: FastAPI (Python 3.14+), Pydantic v2, SQLAlchemy, PostgreSQL 16 with RLS, Alembic migrations
- Frontend: React 18, Vite 5, TypeScript, Tailwind, recharts
- Gateway: Kong 3.x at :8000, JWT auth, X-Tenant-ID header
- All tables MUST have tenant_id column with Row Level Security policy
- All API endpoints MUST require JWT Bearer token + X-Tenant-ID header

EXISTING SERVICES:
- services/dpe-svc/ (:8001) — auth, dashboard, resolution, analytics, admin
- services/mat-svc/ (:8002) — material ATP, netting
- services/cap-svc/ (:8003) — scheduling (OR-Tools CP-SAT), CPM
- services/fea-svc/ (:8004) — feasibility scoring, WebSocket
- services/nlp-svc/ (:8007) — AI Copilot (Claude/Ollama/OpenRouter)
- services/connector/ (:8009) — Odoo 19 XML-RPC sync engine
- services/demand-svc/ (:8040) — demand sensing, SES/Prophet forecaster
- services/scenario-svc/ (:8050) — what-if sandbox

DATABASE:
- PostgreSQL 16 at :5433
- Alembic migrations in migrations/versions/ (currently 001–042)
- Core CDM tables: cdm_tenant, cdm_user, cdm_product, cdm_bill_of_material, cdm_bom_line, cdm_routing_operation, cdm_work_center, cdm_manufacturing_order, cdm_demand_line, cdm_supply_order, cdm_sync_run, cdm_data_quality_flag, cdm_delay_event, cdm_plant, cdm_customer, cdm_supplier
- RLS pattern: ALTER TABLE <table> ENABLE ROW LEVEL SECURITY; CREATE POLICY <name> ON <table> USING (tenant_id = current_setting('app.tenant_id')::uuid);

CONVENTIONS:
- Follow existing code patterns in each service (look at existing files before creating new ones)
- Pydantic v2 for all request/response schemas
- SQLAlchemy 2.0 style (mapped_column, DeclarativeBase)
- pytest with async fixtures for tests
- UUID primary keys: id = Column(UUID, primary_key=True, default=gen_random_uuid)
- All monetary values as NUMERIC(18,2), quantities as NUMERIC(18,4), percentages as NUMERIC(10,4)
- Arabic i18n keys in apps/web/src/i18n/ar.json using dot notation

IMPLEMENTATION GUIDE: docs/IPE-PLANNING-INTELLIGENCE-TECHNICAL-SPEC.md

I will now give you specific module prompts. For each:
1. Read existing code in the target service BEFORE writing new code
2. Follow existing patterns exactly (imports, error handling, response format)
3. Create complete files — no placeholders or TODOs
4. Include all imports, type hints, and docstrings
5. Create tests that actually verify the logic with known values

Confirm you understand by saying "Ready for module prompts."
```

---

## PROMPT 1 — Module B: ABC/XYZ Segmentation (Build First)

```
MODULE: ABC/XYZ Product Segmentation
SERVICE: services/mat-svc/
MIGRATION: 044

STEP 1 — Read existing code first:
- Read services/mat-svc/app/main.py to understand router registration pattern
- Read services/mat-svc/app/api/v1/ to see existing endpoint patterns
- Read services/mat-svc/app/models/ to see existing SQLAlchemy model patterns (if any)
- Read migrations/versions/ to see the latest migration number and naming pattern
- Read services/mat-svc/app/core/ to see existing business logic patterns

STEP 2 — Create Alembic migration:
File: migrations/versions/044_product_segmentation.py

Create two tables:

TABLE cdm_product_segment:
- id: UUID PK DEFAULT gen_random_uuid()
- tenant_id: UUID NOT NULL REFERENCES cdm_tenant(id)
- product_id: UUID NOT NULL REFERENCES cdm_product(id)
- segmentation_date: DATE NOT NULL
- abc_class: VARCHAR(1) NOT NULL CHECK (abc_class IN ('A','B','C'))
- revenue_total: NUMERIC(18,2)
- revenue_share_pct: NUMERIC(8,4)
- cumulative_revenue_pct: NUMERIC(8,4)
- xyz_class: VARCHAR(1) NOT NULL CHECK (xyz_class IN ('X','Y','Z'))
- demand_cv: NUMERIC(8,4)
- demand_mean: NUMERIC(18,4)
- demand_stddev: NUMERIC(18,4)
- combined_segment: VARCHAR(2) NOT NULL
- target_service_level_pct: NUMERIC(5,2)
- forecast_model_recommendation: VARCHAR(50)
- review_frequency: VARCHAR(20)
- created_at: TIMESTAMPTZ DEFAULT now()
UNIQUE INDEX: (tenant_id, product_id, segmentation_date)
INDEX: (tenant_id, combined_segment)
RLS: tenant_id = current_setting('app.tenant_id')::uuid

TABLE cdm_segmentation_config:
- id: UUID PK DEFAULT gen_random_uuid()
- tenant_id: UUID NOT NULL REFERENCES cdm_tenant(id) UNIQUE
- abc_a_threshold_pct: NUMERIC(5,2) DEFAULT 80.0
- abc_b_threshold_pct: NUMERIC(5,2) DEFAULT 95.0
- xyz_x_threshold: NUMERIC(5,2) DEFAULT 0.5
- xyz_y_threshold: NUMERIC(5,2) DEFAULT 1.0
- service_level_ax: NUMERIC(5,2) DEFAULT 99.0
- service_level_ay: NUMERIC(5,2) DEFAULT 97.0
- service_level_az: NUMERIC(5,2) DEFAULT 95.0
- service_level_bx: NUMERIC(5,2) DEFAULT 97.0
- service_level_by: NUMERIC(5,2) DEFAULT 95.0
- service_level_bz: NUMERIC(5,2) DEFAULT 90.0
- service_level_cx: NUMERIC(5,2) DEFAULT 95.0
- service_level_cy: NUMERIC(5,2) DEFAULT 90.0
- service_level_cz: NUMERIC(5,2) DEFAULT 85.0
- history_months: INTEGER DEFAULT 12
- created_at: TIMESTAMPTZ DEFAULT now()
RLS: tenant_id = current_setting('app.tenant_id')::uuid

STEP 3 — Create SQLAlchemy models:
File: services/mat-svc/app/models/segmentation.py

STEP 4 — Create core business logic:
File: services/mat-svc/app/core/segmentation.py

class SegmentationEngine:
    async def run_segmentation(self, db, tenant_id, config=None) -> dict:
        """
        1. Get or create config from cdm_segmentation_config (use defaults if not exists)
        2. Query cdm_demand_line for last config.history_months, grouped by product_id:
           - SUM(revenue) as total_revenue
           - Weekly/monthly qty buckets for CV calculation
        3. ABC classification:
           - Sort products by revenue DESC
           - Calculate cumulative revenue percentage
           - A: cumulative <= abc_a_threshold_pct
           - B: cumulative <= abc_b_threshold_pct
           - C: remainder
        4. XYZ classification:
           - For each product, get demand qty per period (weekly buckets)
           - CV = STDDEV(qty) / AVG(qty) where AVG > 0
           - X: CV < xyz_x_threshold
           - Y: CV < xyz_y_threshold
           - Z: CV >= xyz_y_threshold
           - Products with zero demand: Z class
        5. Combined segment = abc_class + xyz_class (e.g., "AX", "BZ")
        6. Assign target_service_level_pct from config per combined segment
        7. Assign forecast_model_recommendation:
           AX,BX → 'arima', AY,BY → 'ses', AZ,BZ,CX,CY → 'ses', CZ → 'croston'
        8. Assign review_frequency:
           A* → 'weekly', B* → 'monthly', C* → 'quarterly'
        9. Upsert all products into cdm_product_segment
        10. Return summary: { date, total_products, segments: {AX: n, AY: n, ...} }
        """

STEP 5 — Create Pydantic schemas:
File: services/mat-svc/app/schemas/segmentation.py

- SegmentationRunRequest: { history_months: int = 12 }
- SegmentationRunResponse: { segmentation_date, products_classified, segments: dict }
- ProductSegmentResponse: { product_id, product_name, abc_class, xyz_class, combined_segment, revenue_total, demand_cv, target_service_level_pct }
- SegmentationSummaryResponse: { matrix: dict, total_products, segmentation_date }
- SegmentationConfigResponse / SegmentationConfigUpdate

STEP 6 — Create API router:
File: services/mat-svc/app/api/v1/segmentation.py

Endpoints:
- POST /api/v1/material/segmentation/run → runs full segmentation
- GET /api/v1/material/segmentation/results?abc_class=A&xyz_class=X → filtered product list
- GET /api/v1/material/segmentation/summary → 3x3 matrix with counts and revenue
- GET /api/v1/material/segmentation/config → current thresholds
- PUT /api/v1/material/segmentation/config → update thresholds

All endpoints: JWT auth required, tenant_id from X-Tenant-ID header.

STEP 7 — Register router in services/mat-svc/app/main.py

STEP 8 — Create tests:
File: services/mat-svc/tests/test_segmentation.py

Test cases:
- 10 products: 2 should be A (80% revenue), 2 should be B, 6 should be C
- Product with CV=0.3 → X, CV=0.7 → Y, CV=1.5 → Z
- Product with zero demand → Z class
- Combined segment AX gets service_level 99%
- Config update changes thresholds
- Re-run updates existing segments (upsert, not duplicate)

Create all files completely. No TODOs, no placeholders. Working code.
```

---

## PROMPT 2 — Module A: Forecast Quality Engine

```
MODULE: Forecast Quality Engine (MAPE, Bias, MASE, Stability)
SERVICE: services/demand-svc/
MIGRATION: 043

STEP 1 — Read existing code first:
- Read services/demand-svc/app/main.py
- Read services/demand-svc/app/api/v1/ for endpoint patterns
- Read services/demand-svc/app/core/forecaster.py to understand existing forecast output format
- Read services/demand-svc/app/models/ for model patterns
- Read the latest migration file for naming and structure patterns

STEP 2 — Create Alembic migration:
File: migrations/versions/043_forecast_quality.py

TABLE cdm_forecast_snapshot:
- id: UUID PK DEFAULT gen_random_uuid()
- tenant_id: UUID NOT NULL REFERENCES cdm_tenant(id)
- product_id: UUID NOT NULL REFERENCES cdm_product(id)
- location_id: UUID NULL REFERENCES cdm_plant(id)
- snapshot_date: DATE NOT NULL
- target_period_start: DATE NOT NULL
- target_period_type: VARCHAR(10) NOT NULL DEFAULT 'month'
- forecast_qty: NUMERIC(18,4) NOT NULL
- forecast_source: VARCHAR(50) NOT NULL
- model_id: VARCHAR(100) NULL
- model_version: VARCHAR(50) NULL
- created_at: TIMESTAMPTZ DEFAULT now()
INDEX: (tenant_id, product_id, snapshot_date)
INDEX: (tenant_id, target_period_start)
RLS on tenant_id

TABLE cdm_forecast_error:
- id: UUID PK DEFAULT gen_random_uuid()
- tenant_id: UUID NOT NULL REFERENCES cdm_tenant(id)
- product_id: UUID NOT NULL REFERENCES cdm_product(id)
- location_id: UUID NULL
- period_start: DATE NOT NULL
- period_type: VARCHAR(10) NOT NULL DEFAULT 'month'
- lag_periods: INTEGER NOT NULL
- forecast_source: VARCHAR(50) NOT NULL
- forecast_qty: NUMERIC(18,4)
- actuals_qty: NUMERIC(18,4)
- absolute_error: NUMERIC(18,4)
- error_pct: NUMERIC(10,4)
- bias: NUMERIC(18,4)
- bias_pct: NUMERIC(10,4)
- mase_component: NUMERIC(10,4)
- calculated_at: TIMESTAMPTZ DEFAULT now()
INDEX: (tenant_id, product_id, period_start, lag_periods)
RLS on tenant_id

TABLE cdm_forecast_stability:
- id: UUID PK DEFAULT gen_random_uuid()
- tenant_id: UUID NOT NULL
- product_id: UUID NOT NULL
- target_period_start: DATE NOT NULL
- cycle_date: DATE NOT NULL
- prior_cycle_date: DATE NULL
- current_forecast_qty: NUMERIC(18,4)
- prior_forecast_qty: NUMERIC(18,4) NULL
- change_qty: NUMERIC(18,4) NULL
- change_pct: NUMERIC(10,4) NULL
- created_at: TIMESTAMPTZ DEFAULT now()
RLS on tenant_id

STEP 3 — Create SQLAlchemy models:
File: services/demand-svc/app/models/forecast_quality.py

STEP 4 — Create core business logic:
File: services/demand-svc/app/core/forecast_quality.py

class ForecastQualityEngine:
    async def create_snapshot(self, db, tenant_id, product_ids, source) -> dict:
        """
        For each product, query current forecast values from demand-svc forecast table.
        Store as snapshot with today's date and the future periods being forecasted.
        Return: { snapshot_id, products_captured, snapshot_date }
        """

    async def calculate_errors(self, db, tenant_id, period_start, period_end, lags) -> dict:
        """
        For each (product, period, lag):
        1. Find snapshot from (period - lag months) ago → gets the forecast that was made lag months before
        2. Find actuals from cdm_demand_line for that period (state='done' or confirmed)
        3. Calculate:
           - absolute_error = |forecast_qty - actuals_qty|
           - error_pct = absolute_error / actuals_qty (MAPE component) — skip if actuals = 0
           - bias = forecast_qty - actuals_qty (positive = over-forecast)
           - bias_pct = bias / actuals_qty
           - mase_component = absolute_error / naive_mae
             where naive_mae = mean(|actuals_t - actuals_{t-1}|) over history
        4. Upsert into cdm_forecast_error
        Return: { errors_calculated: int }
        """

    async def get_mape(self, db, tenant_id, filters) -> dict:
        """
        Query cdm_forecast_error with filters.
        Weighted MAPE = SUM(absolute_error) / SUM(actuals_qty) * 100
        Return by_product and by_period breakdowns.
        """

    async def get_bias(self, db, tenant_id, filters) -> dict:
        """
        Average bias_pct across products.
        Count positive (over-forecast) vs negative (under-forecast).
        """

    async def get_stability(self, db, tenant_id, product_id=None) -> dict:
        """
        From cdm_forecast_stability:
        avg_change_pct and max_change_pct per product.
        High instability = forecast changes > 20% between cycles.
        """

    async def get_value_add(self, db, tenant_id, product_ids=None, lag=3) -> dict:
        """
        Compare MAPE of 'statistical' source vs 'consensus' or 'final' source.
        value_add_pct = (statistical_mape - final_mape) / statistical_mape * 100
        Positive = manual adjustments improved accuracy.
        Negative = manual adjustments made it worse.
        """

STEP 5 — Create Pydantic schemas and API router:
File: services/demand-svc/app/schemas/forecast_quality.py
File: services/demand-svc/app/api/v1/forecast_quality.py

Endpoints:
- POST /api/v1/demand/snapshot/create { products: list[UUID] | "all", source: str }
- POST /api/v1/demand/error/calculate { period_start: date, period_end: date, lags: list[int] }
- GET /api/v1/demand/error/mape?product_id=&lag=1&period_start=&period_end=
- GET /api/v1/demand/error/bias?product_id=&lag=1
- GET /api/v1/demand/error/mase?product_id=&lag=1
- GET /api/v1/demand/error/stability?product_id=
- GET /api/v1/demand/error/value-add?product_id=&lag=3

STEP 6 — Register router in demand-svc main.py

STEP 7 — Tests:
File: services/demand-svc/tests/test_forecast_quality.py

Test with known data:
- Forecast=100, Actuals=80 → MAPE=25%, bias=+25% (over-forecast)
- Forecast=100, Actuals=120 → MAPE=16.7%, bias=-16.7% (under-forecast)
- Actuals=0 → skip (no division by zero)
- MASE with naive series [100,110,90,105] → naive_mae = mean(|10|,|20|,|15|) = 15
- Stability: forecast changed from 100 to 130 → change_pct = 30%
- Value-add: statistical MAPE=25%, final MAPE=18% → value_add=28%

Create all files completely. Working code with real calculations.
```

---

## PROMPT 3 — Module D: ARIMA/SARIMA + Best-Fit

```
MODULE: Statistical Forecasting Upgrade — ARIMA, SARIMA, Best-Fit Selection
SERVICE: services/demand-svc/
MIGRATION: None needed

STEP 1 — Read existing forecaster:
- Read services/demand-svc/app/core/forecaster.py completely
- Understand the current interface (input format, output format, how SES is called)
- Check services/demand-svc/requirements.txt or pyproject.toml for current dependencies

STEP 2 — Add statsmodels dependency:
Add 'statsmodels>=0.14' to the service's requirements file.

STEP 3 — Create ARIMA forecaster:
File: services/demand-svc/app/core/forecasters/arima_forecaster.py

class ARIMAForecaster:
    """
    ARIMA forecaster with auto-order selection.
    Uses statsmodels.tsa.arima.model.ARIMA.
    
    Auto-order: try combinations of p=0-3, d=0-2, q=0-3
    Select by lowest AIC on training data.
    Fallback to (1,1,1) if auto-selection fails.
    """
    
    def forecast(self, history: list[float], horizon: int) -> dict:
        """
        Returns: {
            forecast: list[float],  # horizon values
            model_order: tuple,  # (p,d,q) selected
            aic: float,
            confidence_lower: list[float],
            confidence_upper: list[float],
        }
        """

class SARIMAForecaster:
    """
    Seasonal ARIMA for data with weekly/monthly seasonality.
    Uses statsmodels.tsa.statespace.sarimax.SARIMAX.
    
    Seasonal period auto-detection:
    - If weekly data: try m=52 (yearly) or m=4 (monthly)
    - If monthly data: try m=12 (yearly)
    - Use ACF peaks to detect dominant seasonality
    """
    
    def forecast(self, history: list[float], horizon: int, seasonal_period: int = None) -> dict:
        """Same return format as ARIMA"""

STEP 4 — Create best-fit model selector:
File: services/demand-svc/app/core/forecasters/model_selector.py

class BestFitSelector:
    """
    Runs multiple forecast models, selects best by validation MAPE.
    
    Algorithm:
    1. Split history: training = history[:-3], validation = history[-3:]
    2. Run each candidate model on training data, forecast 3 periods
    3. Calculate MAPE on validation periods for each model
    4. Select model with lowest validation MAPE
    5. Re-train selected model on FULL history
    6. Generate final forecast for requested horizon
    
    Segment-driven candidate filtering (if ABC/XYZ segment provided):
    - AX, BX: [ARIMA, SARIMA, SES, Prophet]
    - AY, BY: [SES, ARIMA]
    - AZ, BZ, CX, CY: [SES]
    - CZ: [SES] (Croston if intermittent pattern detected)
    
    Intermittent detection: if >30% of periods have zero demand → intermittent
    """
    
    def select_and_forecast(
        self,
        history: list[float],
        horizon: int,
        segment: str = None,
        candidates: list[str] = None,
    ) -> dict:
        """
        Returns: {
            forecast: list[float],
            selected_model: str,  # 'ses', 'arima', 'sarima', 'prophet'
            validation_mape: float,
            all_models_mape: dict,  # {'ses': 12.3, 'arima': 8.7, ...}
            confidence_lower: list[float],
            confidence_upper: list[float],
        }
        """

STEP 5 — Integrate into existing forecaster factory:
Update services/demand-svc/app/core/forecaster.py to:
- Import ARIMAForecaster, SARIMAForecaster, BestFitSelector
- Add model options: 'arima', 'sarima', 'best_fit' alongside existing 'ses', 'prophet', 'lstm'
- When model='best_fit', use BestFitSelector
- Handle ImportError gracefully: if statsmodels not installed, log warning and fall back to SES

STEP 6 — Update forecast API:
In services/demand-svc/app/api/v1/demand.py (or equivalent forecast endpoint):
- Add model parameter: model = Query(default='best_fit', enum=['ses','arima','sarima','prophet','lstm','best_fit'])
- Add segment parameter: segment = Query(default=None) — if provided, filters candidate models
- Return selected_model and validation_mape in response

STEP 7 — Tests:
File: services/demand-svc/tests/test_arima_forecaster.py
File: services/demand-svc/tests/test_best_fit.py

Test cases:
- Seasonal data [100,120,80,100,125,85,105,130,90,...] → SARIMA should win over SES
- Trend data [100,102,105,108,112,...] → ARIMA should win
- Flat data [100,101,99,100,102,...] → SES should win (simplest adequate model)
- Intermittent data [0,0,50,0,0,0,45,0,...] → should detect intermittent pattern
- Segment filtering: segment='CZ' should only try SES, not ARIMA

Handle edge cases:
- History too short for ARIMA (< 10 points): skip ARIMA, use SES
- statsmodels.tsa.arima raises convergence error: catch, skip, try next model
- All models fail validation: return SES with warning flag
```

---

## PROMPT 4 — Odoo 19 Connector Extensions

```
MODULE: Odoo 19 Connector Extensions — Lead Time History + Product Costs
SERVICE: services/connector/
MIGRATION: 048

STEP 1 — Read existing connector code:
- Read services/connector/app/odoo/ (or app/core/) to find existing mapper pattern
- Read the Odoo XML-RPC client code to understand how calls are made
- Read existing mappers (product, demand, supply, etc.) for the pattern
- Find how sync scheduler works (APScheduler config)

STEP 2 — Create migration for new tables and columns:
File: migrations/versions/048_connector_extensions.py

TABLE cdm_lead_time_history:
- id: UUID PK DEFAULT gen_random_uuid()
- tenant_id: UUID NOT NULL REFERENCES cdm_tenant(id)
- product_id: UUID NOT NULL REFERENCES cdm_product(id)
- supplier_id: UUID NULL REFERENCES cdm_supplier(id)
- po_erp_id: VARCHAR(100)
- order_date: DATE
- expected_date: DATE
- actual_receipt_date: DATE
- lead_time_days: INTEGER
- lead_time_variance_days: INTEGER
- created_at: TIMESTAMPTZ DEFAULT now()
INDEX: (tenant_id, product_id)
RLS on tenant_id

ALTER TABLE cdm_product:
- ADD COLUMN unit_cost NUMERIC(18,4) NULL
- ADD COLUMN list_price NUMERIC(18,4) NULL
- ADD COLUMN weight NUMERIC(10,4) NULL

STEP 3 — Create lead time mapper:
File: services/connector/app/odoo/mappers/lead_time_mapper.py (or matching your directory structure)

class LeadTimeMapper:
    """
    Syncs purchase order lead times from Odoo 19 to cdm_lead_time_history.
    
    Algorithm:
    1. Fetch purchase.order via XML-RPC:
       - domain: [('state', 'in', ['purchase', 'done'])]
       - fields: ['id', 'name', 'date_order', 'date_planned', 'partner_id', 'order_line']
       
    2. For each PO, fetch purchase.order.line:
       - fields: ['product_id', 'product_qty', 'date_planned']
       
    3. For each PO, find matching stock.picking (incoming receipt):
       - domain: [('origin', '=', po.name), ('picking_type_code', '=', 'incoming'), ('state', '=', 'done')]
       - fields: ['date_done']
       
    4. Calculate:
       - lead_time_days = (picking.date_done - po.date_order).days
       - lead_time_variance_days = (picking.date_done - po.date_planned).days
       
    5. Upsert into cdm_lead_time_history per PO line
    
    Edge cases:
    - PO has no receipt yet (not delivered): skip, don't create record
    - PO has multiple partial receipts: use earliest receipt for LT, or create one record per receipt
    - PO line product not in cdm_product: skip with warning log
    - date_done or date_order is None: skip with warning
    
    Odoo 19 specifics:
    - purchase.order.date_order is Datetime in Odoo 19 (convert to Date)
    - stock.picking.date_done is Datetime
    - partner_id on PO maps to supplier_id in CDM
    """

STEP 4 — Extend product mapper:
In the existing product mapper file, add these fields to the sync:

Odoo 19 product.product fields to add:
- standard_price → cdm_product.unit_cost
- list_price → cdm_product.list_price  
- weight → cdm_product.weight

These are simple field additions to the existing product sync mapper.

STEP 5 — Add lead time sync to scheduler:
Find the sync scheduler configuration (likely APScheduler in connector's main.py or a scheduler module).
Add a new job:
- Job: sync_lead_times
- Schedule: daily at 02:00 (not every 15 min — PO data changes less frequently)
- Calls: LeadTimeMapper.sync(session, odoo_client, tenant_id)

STEP 6 — Tests:
File: services/connector/tests/test_lead_time_mapper.py

Mock Odoo XML-RPC responses:
- PO with one line, one receipt: verify lead_time_days calculated correctly
- PO with receipt date before expected: lead_time_variance_days is negative (early delivery)
- PO with no receipt: verify no record created
- PO line with unknown product: verify skipped with warning
- Multiple POs: verify all processed

STEP 7 — Test product mapper extension:
Verify standard_price and list_price fields sync to cdm_product.unit_cost and list_price columns.
```

---

## PROMPT 5 — Module C: Safety Stock Calculator

```
MODULE: Statistical Safety Stock Calculator
SERVICE: services/mat-svc/
MIGRATION: 045
DEPENDENCY: Module B (segmentation) must be built first. Module Odoo Extensions (lead time) must be built first.

STEP 1 — Read existing mat-svc code and verify dependencies:
- Read services/mat-svc/app/core/segmentation.py (from Module B) — confirm it exists
- Read services/mat-svc/app/models/ for existing models
- Verify cdm_lead_time_history table exists (from Module Odoo Extensions)
- Verify cdm_product_segment table exists (from Module B)

STEP 2 — Create migration:
File: migrations/versions/045_safety_stock.py

TABLE cdm_safety_stock:
- id: UUID PK DEFAULT gen_random_uuid()
- tenant_id: UUID NOT NULL
- product_id: UUID NOT NULL REFERENCES cdm_product(id)
- location_id: UUID NULL REFERENCES cdm_plant(id)
- calculation_date: DATE NOT NULL
- service_level_target_pct: NUMERIC(5,2)
- z_score: NUMERIC(6,4)
- avg_demand_per_period: NUMERIC(18,4)
- demand_stddev: NUMERIC(18,4)
- demand_cv: NUMERIC(8,4)
- avg_lead_time_periods: NUMERIC(10,2)
- lead_time_stddev: NUMERIC(10,2)
- lead_time_cv: NUMERIC(8,4)
- safety_stock_qty: NUMERIC(18,4)
- safety_stock_demand_component: NUMERIC(18,4)
- safety_stock_leadtime_component: NUMERIC(18,4)
- reorder_point_qty: NUMERIC(18,4)
- current_stock_qty: NUMERIC(18,4) NULL
- delta_qty: NUMERIC(18,4) NULL
- delta_pct: NUMERIC(10,4) NULL
- prior_safety_stock_qty: NUMERIC(18,4) NULL
- cycle_change_qty: NUMERIC(18,4) NULL
- unit_cost: NUMERIC(18,4) NULL
- safety_stock_value: NUMERIC(18,2) NULL
- delta_value: NUMERIC(18,2) NULL
- created_at: TIMESTAMPTZ DEFAULT now()
UNIQUE INDEX: (tenant_id, product_id, calculation_date)
RLS on tenant_id

STEP 3 — Create core calculator:
File: services/mat-svc/app/core/safety_stock.py

"""
Safety Stock Formula:
SS = z × σ_d × √(LT) + z × d̄ × σ_LT

Where:
- z = scipy.stats.norm.ppf(service_level / 100.0)
- σ_d = standard deviation of demand per period (from cdm_demand_line, weekly buckets)
- LT = average lead time in periods (from cdm_lead_time_history, converted to weeks)
- d̄ = average demand per period
- σ_LT = standard deviation of lead time in periods

Reorder Point:
ROP = d̄ × LT + SS
"""

import numpy as np
from scipy.stats import norm

def calculate_safety_stock(
    demand_series: list[float],
    lead_time_days_series: list[int],
    service_level_pct: float,
    period_days: int = 7,
) -> dict:
    # Demand statistics
    d_mean = float(np.mean(demand_series)) if demand_series else 0
    d_std = float(np.std(demand_series, ddof=1)) if len(demand_series) > 1 else 0
    d_cv = d_std / d_mean if d_mean > 0 else 0
    
    # Lead time statistics (convert days to periods)
    lt_mean_periods = float(np.mean(lead_time_days_series)) / period_days if lead_time_days_series else 1.0
    lt_std_periods = float(np.std(lead_time_days_series, ddof=1)) / period_days if len(lead_time_days_series) > 1 else 0
    lt_cv = lt_std_periods / lt_mean_periods if lt_mean_periods > 0 else 0
    
    # Z-score for service level
    z = float(norm.ppf(service_level_pct / 100.0))
    
    # Safety stock components
    ss_demand = z * d_std * np.sqrt(max(lt_mean_periods, 0))
    ss_leadtime = z * d_mean * lt_std_periods
    safety_stock = float(ss_demand + ss_leadtime)
    reorder_point = float(d_mean * lt_mean_periods + safety_stock)
    
    return {
        'safety_stock_qty': round(safety_stock, 2),
        'safety_stock_demand_component': round(float(ss_demand), 2),
        'safety_stock_leadtime_component': round(float(ss_leadtime), 2),
        'reorder_point_qty': round(reorder_point, 2),
        'z_score': round(z, 4),
        'avg_demand_per_period': round(d_mean, 4),
        'demand_stddev': round(d_std, 4),
        'demand_cv': round(d_cv, 4),
        'avg_lead_time_periods': round(lt_mean_periods, 2),
        'lead_time_stddev': round(lt_std_periods, 2),
        'lead_time_cv': round(lt_cv, 4),
    }

STEP 4 — Create service layer:
File: services/mat-svc/app/core/safety_stock_service.py

class SafetyStockService:
    async def calculate_all(self, db, tenant_id, product_ids=None, use_segments=True):
        """
        For each product (or specified products):
        1. Get service level target:
           - If use_segments and product has segment: get from cdm_product_segment.target_service_level_pct
           - Else: default 95%
        2. Get demand history: cdm_demand_line for last 12 months, bucketed weekly
        3. Get lead time history: cdm_lead_time_history for this product
           - If no lead time data: use default 14 days with stddev 3 days
        4. Call calculate_safety_stock()
        5. Get current stock: query cdm_product or Odoo stock.quant data
        6. Calculate delta = recommended - current
        7. Get unit_cost from cdm_product.unit_cost
        8. Calculate safety_stock_value = qty * unit_cost
        9. Get prior calculation from cdm_safety_stock (most recent before today)
        10. Calculate cycle_change = current_ss - prior_ss
        11. Upsert into cdm_safety_stock
        """

STEP 5 — Create API router:
File: services/mat-svc/app/api/v1/safety_stock.py

- POST /api/v1/material/safety-stock/calculate { products: list | "all", use_segmentation_service_levels: true }
- GET /api/v1/material/safety-stock/results?product_id=&abc_class=&sort_by=delta_value&order=desc
- GET /api/v1/material/safety-stock/summary
  → { total_ss_value, total_delta_value, by_segment: {AX: {count, total_value},...}, over_stocked: top10, under_stocked: top10 }
- GET /api/v1/material/safety-stock/lead-time?product_id=&supplier_id=

STEP 6 — Register router

STEP 7 — Tests:
File: services/mat-svc/tests/test_safety_stock.py

Known value tests:
- demand_series=[100,110,90,105,95,100], lt_days=[14,16,12,15,13], service_level=95%
  → z=1.645, d_mean=100, d_std≈7.07, lt_mean=2 weeks, lt_std≈0.23 weeks
  → ss_demand = 1.645 * 7.07 * √2 ≈ 16.45
  → ss_leadtime = 1.645 * 100 * 0.23 ≈ 37.84
  → total SS ≈ 54.29
  → ROP = 100*2 + 54.29 = 254.29

- Empty lead time history: uses defaults (14 days, stddev 3)
- Zero demand: SS = 0
- Segment AX with 99% service level → higher z → higher SS than CZ with 85%

Install scipy: add 'scipy>=1.14' to mat-svc requirements.
```

---

## PROMPT 6 — Module E: Capacity Utilisation Alerts

```
MODULE: Capacity Utilisation Alerts
SERVICE: services/cap-svc/
MIGRATION: 046

STEP 1 — Read existing cap-svc code:
- Read services/cap-svc/app/main.py
- Read services/cap-svc/app/api/v1/capacity.py
- Understand how work centers and scheduling data is structured

STEP 2 — Create migration:
File: migrations/versions/046_capacity_alerts.py

TABLE cdm_capacity_utilisation:
- id: UUID PK
- tenant_id: UUID NOT NULL
- work_center_id: UUID NOT NULL REFERENCES cdm_work_center(id)
- period_start: DATE NOT NULL
- period_type: VARCHAR(10) DEFAULT 'week'
- capacity_available_hours: NUMERIC(10,2)
- capacity_used_hours: NUMERIC(10,2)
- utilisation_pct: NUMERIC(6,2)
- overload: BOOLEAN DEFAULT FALSE
- overload_hours: NUMERIC(10,2) DEFAULT 0
- calculated_at: TIMESTAMPTZ DEFAULT now()
INDEX: (tenant_id, work_center_id, period_start)
RLS on tenant_id

TABLE cdm_capacity_alert_config:
- id: UUID PK
- tenant_id: UUID NOT NULL UNIQUE
- overload_threshold_pct: NUMERIC(5,2) DEFAULT 90.0
- critical_threshold_pct: NUMERIC(5,2) DEFAULT 100.0
- alert_enabled: BOOLEAN DEFAULT TRUE
RLS on tenant_id

STEP 3 — Create core logic:
File: services/cap-svc/app/core/utilisation.py

class UtilisationCalculator:
    async def calculate(self, db, tenant_id, period_start, period_end, period_type='week'):
        """
        For each work center:
        1. Get available capacity:
           - cdm_work_center.capacity (products/hour) × hours_per_shift × shifts_per_week
           - Or: total_available_hours per period from work center definition
        2. Get used capacity:
           - Sum of cdm_manufacturing_order.duration_expected for MOs assigned to this WC in this period
        3. utilisation_pct = used / available * 100
        4. overload = utilisation_pct > threshold (from config)
        5. overload_hours = max(0, used - available)
        6. Upsert into cdm_capacity_utilisation
        """

STEP 4 — Create API endpoints:
File: services/cap-svc/app/api/v1/utilisation.py

- POST /api/v1/capacity/utilisation/calculate { period_start, period_end, period_type }
- GET /api/v1/capacity/utilisation?work_center_id=&period_start=&overloaded_only=false
- GET /api/v1/capacity/utilisation/alerts → overloaded and critical work centers
- GET /api/v1/capacity/utilisation/ranking?top_n=10 → worst utilisation work centers
- GET /api/v1/capacity/utilisation/config
- PUT /api/v1/capacity/utilisation/config { overload_threshold_pct, critical_threshold_pct }

STEP 5 — Tests with known capacity data
```

---

## PROMPT 7 — Module F: S&OP Process Engine (Large — Break Into Parts)

### Part 7A — Service Scaffold + Database

```
MODULE: S&OP Process Engine — Part A: Service Scaffold and Database
NEW SERVICE: services/sop-svc/
PORT: 8110
MIGRATION: 047

STEP 1 — Create service directory structure:
services/sop-svc/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── sop.py
│   │       ├── consensus.py
│   │       └── versions.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── consensus.py
│   │   ├── version.py
│   │   └── cycle.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── sop_cycle.py
│   │   ├── sop_version.py
│   │   ├── consensus_demand.py
│   │   └── stage_gate.py
│   └── schemas/
│       ├── __init__.py
│       ├── sop.py
│       ├── consensus.py
│       └── version.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_consensus.py
│   └── test_cycle.py
├── Dockerfile
└── pyproject.toml

Copy patterns from an existing service (e.g., services/demand-svc/) for:
- Dockerfile
- pyproject.toml
- main.py (FastAPI app setup, CORS, health endpoint, router registration)
- conftest.py (test fixtures)

STEP 2 — Create migration 047_sop_engine.py with 5 tables:

TABLE cdm_sop_cycle:
- id: UUID PK
- tenant_id: UUID NOT NULL
- cycle_name: VARCHAR(100)
- cycle_month: DATE NOT NULL
- status: VARCHAR(30) NOT NULL DEFAULT 'draft'
  CHECK (status IN ('draft','demand_review','supply_review','reconciliation','management_review','closed'))
- demand_review_deadline: TIMESTAMPTZ NULL
- supply_review_deadline: TIMESTAMPTZ NULL
- reconciliation_deadline: TIMESTAMPTZ NULL
- management_review_deadline: TIMESTAMPTZ NULL
- created_by: UUID NULL
- created_at: TIMESTAMPTZ DEFAULT now()
- closed_at: TIMESTAMPTZ NULL
RLS on tenant_id

TABLE cdm_sop_version:
- id: UUID PK
- tenant_id: UUID NOT NULL
- cycle_id: UUID NOT NULL REFERENCES cdm_sop_cycle(id) ON DELETE CASCADE
- version_type: VARCHAR(20) NOT NULL CHECK (version_type IN ('baseline','upside','downside','whatif'))
- version_name: VARCHAR(100)
- description: TEXT NULL
- is_active: BOOLEAN DEFAULT TRUE
- created_by: UUID NULL
- created_at: TIMESTAMPTZ DEFAULT now()
RLS on tenant_id

TABLE cdm_consensus_demand:
- id: UUID PK
- tenant_id: UUID NOT NULL
- version_id: UUID NOT NULL REFERENCES cdm_sop_version(id) ON DELETE CASCADE
- product_id: UUID NOT NULL REFERENCES cdm_product(id)
- location_id: UUID NULL
- customer_id: UUID NULL
- period_start: DATE NOT NULL
- period_type: VARCHAR(10) DEFAULT 'month'
- sales_forecast_qty: NUMERIC(18,4) NULL
- marketing_forecast_qty: NUMERIC(18,4) NULL
- statistical_forecast_qty: NUMERIC(18,4) NULL
- finance_plan_qty: NUMERIC(18,4) NULL
- consensus_qty: NUMERIC(18,4)
- planned_price: NUMERIC(18,4) NULL
- consensus_revenue: NUMERIC(18,2) NULL
- cost_per_unit: NUMERIC(18,4) NULL
- consensus_cost: NUMERIC(18,2) NULL
- consensus_profit: NUMERIC(18,2) NULL
- constrained_demand_qty: NUMERIC(18,4) NULL
- constrained_revenue: NUMERIC(18,2) NULL
- lost_sales_qty: NUMERIC(18,4) NULL
- lost_sales_value: NUMERIC(18,2) NULL
- created_at: TIMESTAMPTZ DEFAULT now()
UNIQUE INDEX: (version_id, product_id, period_start)
RLS on tenant_id

TABLE cdm_sop_stage_gate:
- id: UUID PK
- tenant_id: UUID NOT NULL
- cycle_id: UUID NOT NULL REFERENCES cdm_sop_cycle(id)
- stage: VARCHAR(30) NOT NULL
- status: VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected'))
- approved_by: UUID NULL
- approved_at: TIMESTAMPTZ NULL
- notes: TEXT NULL
- created_at: TIMESTAMPTZ DEFAULT now()
RLS on tenant_id

TABLE cdm_sop_consensus_weight:
- id: UUID PK
- tenant_id: UUID NOT NULL UNIQUE
- weight_sales: NUMERIC(5,2) DEFAULT 0.30
- weight_statistical: NUMERIC(5,2) DEFAULT 0.40
- weight_marketing: NUMERIC(5,2) DEFAULT 0.20
- weight_finance: NUMERIC(5,2) DEFAULT 0.10
- created_at: TIMESTAMPTZ DEFAULT now()
RLS on tenant_id

STEP 3 — Create all SQLAlchemy models

STEP 4 — Create main.py with FastAPI app on port 8110, health endpoint, CORS

STEP 5 — Create Dockerfile matching existing service pattern

Create all files completely. This is Part A — the scaffold. Part B will add business logic and API endpoints.
```

### Part 7B — Business Logic + API

```
MODULE: S&OP Process Engine — Part B: Business Logic and API
SERVICE: services/sop-svc/ (created in Part A)

STEP 1 — Verify Part A files exist:
Check services/sop-svc/app/models/ has all 5 model files
Check migration 047 exists

STEP 2 — Create cycle state machine:
File: services/sop-svc/app/core/cycle.py

VALID_TRANSITIONS = {
    'draft': ['demand_review'],
    'demand_review': ['supply_review'],
    'supply_review': ['reconciliation'],
    'reconciliation': ['management_review'],
    'management_review': ['closed'],
}

class CycleManager:
    async def create_cycle(self, db, tenant_id, cycle_month, name=None) -> SopCycle:
        """Create new cycle in 'draft' status. Auto-create baseline version."""
    
    async def advance_stage(self, db, cycle_id, tenant_id) -> SopCycle:
        """Move cycle to next stage. Validate current stage gate is approved."""
    
    async def approve_stage(self, db, cycle_id, stage, user_id, notes=None) -> SopStageGate:
        """Record stage approval. Only current stage can be approved."""

STEP 3 — Create consensus engine:
File: services/sop-svc/app/core/consensus.py

class ConsensusEngine:
    def calculate_consensus_qty(
        self,
        sales_qty: float | None,
        stat_qty: float | None,
        marketing_qty: float | None,
        finance_qty: float | None,
        weights: dict,
    ) -> float:
        """
        Weighted average with NULL redistribution.
        If an input is None, redistribute its weight proportionally to non-None inputs.
        """
        inputs = []
        if sales_qty is not None: inputs.append((sales_qty, weights['sales']))
        if stat_qty is not None: inputs.append((stat_qty, weights['statistical']))
        if marketing_qty is not None: inputs.append((marketing_qty, weights['marketing']))
        if finance_qty is not None: inputs.append((finance_qty, weights['finance']))
        
        if not inputs: return 0.0
        total_weight = sum(w for _, w in inputs)
        return sum(qty * (w / total_weight) for qty, w in inputs)
    
    async def run_consensus(self, db, tenant_id, version_id) -> dict:
        """
        For each product × period in the version:
        1. Get statistical forecast from demand-svc API (HTTP call to localhost:8040)
        2. Get sales/marketing/finance inputs from cdm_consensus_demand (manual entries)
        3. Get weights from cdm_sop_consensus_weight
        4. Calculate consensus_qty
        5. Get planned_price and cost_per_unit from cdm_product
        6. Calculate revenue, cost, profit
        7. Update cdm_consensus_demand row
        """

STEP 4 — Create version manager:
File: services/sop-svc/app/core/version.py

class VersionManager:
    async def create_version(self, db, cycle_id, tenant_id, version_type, name=None) -> SopVersion:
        """Create new version. If 'whatif', clone demand data from baseline."""
    
    async def compare_versions(self, db, tenant_id, version_id_a, version_id_b) -> dict:
        """
        Side-by-side comparison:
        - Total consensus qty, revenue, profit for each version
        - By-product deltas
        - Constrained demand comparison (if supply review done)
        - Lost sales comparison
        """

STEP 5 — Create Pydantic schemas:
File: services/sop-svc/app/schemas/sop.py, consensus.py, version.py

Key schemas:
- CycleCreateRequest, CycleResponse, CycleListResponse
- ConsensusCalculateRequest, ConsensusDemandResponse
- VersionCreateRequest, VersionCompareResponse
- StageApproveRequest, StageGateResponse
- WeightConfigResponse, WeightConfigUpdate

STEP 6 — Create API routers:
File: services/sop-svc/app/api/v1/sop.py

Cycle endpoints:
- POST /api/v1/sop/cycle → create cycle
- GET /api/v1/sop/cycle → list cycles (with pagination)
- GET /api/v1/sop/cycle/{id} → get cycle with stages
- POST /api/v1/sop/cycle/{id}/advance → advance to next stage
- POST /api/v1/sop/cycle/{id}/stage/{stage}/approve → approve stage gate

File: services/sop-svc/app/api/v1/consensus.py
- POST /api/v1/sop/consensus/calculate → run consensus for a version
- GET /api/v1/sop/consensus?version_id=&product_id=&period_start= → get consensus data
- PUT /api/v1/sop/consensus/{id} → manual override of a consensus line

File: services/sop-svc/app/api/v1/versions.py
- POST /api/v1/sop/version → create version
- GET /api/v1/sop/version/compare?a={id}&b={id} → compare two versions
- DELETE /api/v1/sop/version/{id} → delete whatif version

Config:
- GET /api/v1/sop/config/weights
- PUT /api/v1/sop/config/weights

STEP 7 — Register all routers in main.py

STEP 8 — Tests:
File: services/sop-svc/tests/test_consensus.py
- Test weighted average: sales=100(w0.3), stat=120(w0.4), marketing=90(w0.2), finance=110(w0.1) → 107
- Test NULL redistribution: sales=100(w0.3), stat=120(w0.4), marketing=None, finance=None → (100*0.3+120*0.4)/(0.3+0.4) = 82.86/0.7 = 118.4 (wait let me recalc: (100*0.3 + 120*0.4) / (0.3+0.4) = (30+48)/0.7 = 111.4)
- Test all None → 0

File: services/sop-svc/tests/test_cycle.py
- Test valid transitions: draft→demand_review→supply_review→reconciliation→management_review→closed
- Test invalid transition: draft→reconciliation raises error
- Test stage approval: can't approve supply_review when cycle is in demand_review
```

---

## PROMPT 8 — Copilot Integration (All Modules)

```
MODULE: Copilot Tool Extensions for Planning Intelligence
SERVICE: services/nlp-svc/

STEP 1 — Read existing copilot tools:
- Read services/nlp-svc/app/core/copilot_tools.py
- Understand the tool registration pattern (how tools are defined and registered)
- Read how existing tools make HTTP calls to other services

STEP 2 — Add new planning intelligence tools:

Add these tools to the Copilot tool registry:

TOOL: get_forecast_accuracy
  Calls: demand-svc GET /api/v1/demand/error/mape?lag=3
  Returns: weighted MAPE, by-product breakdown, periods measured
  Copilot context: "Current forecast accuracy across all products"

TOOL: get_forecast_bias
  Calls: demand-svc GET /api/v1/demand/error/bias?lag=3
  Returns: avg bias, over/under-forecast count
  Context: "Whether forecasts are systematically high or low"

TOOL: get_product_segments
  Calls: mat-svc GET /api/v1/material/segmentation/summary
  Returns: 3x3 ABC/XYZ matrix with counts and revenue percentages
  Context: "Product classification by revenue and demand variability"

TOOL: get_safety_stock_gaps
  Calls: mat-svc GET /api/v1/material/safety-stock/summary
  Returns: total SS value, delta value, top over-stocked, top under-stocked
  Context: "Inventory positions relative to recommended safety stock"

TOOL: get_capacity_alerts
  Calls: cap-svc GET /api/v1/capacity/utilisation/alerts
  Returns: overloaded work centers with utilisation % and overload hours
  Context: "Work centers at or above capacity limit"

TOOL: get_capacity_ranking
  Calls: cap-svc GET /api/v1/capacity/utilisation/ranking?top_n=5
  Returns: top 5 most utilised work centers
  Context: "Most constrained production resources"

TOOL: get_sop_cycle_status
  Calls: sop-svc GET /api/v1/sop/cycle (latest)
  Returns: current cycle, stage, deadlines
  Context: "Current S&OP cycle progress"

TOOL: get_consensus_vs_plan
  Calls: sop-svc GET /api/v1/sop/consensus?version_id=baseline
  Returns: consensus revenue vs AOP, profit summary
  Context: "How consensus demand compares to annual plan"

TOOL: compare_sop_versions
  Calls: sop-svc GET /api/v1/sop/version/compare?a=baseline&b=upside
  Returns: side-by-side KPI comparison
  Context: "Difference between S&OP baseline and upside scenarios"

Each tool should:
1. Accept tenant_id parameter
2. Make authenticated HTTP call (pass JWT and X-Tenant-ID headers)
3. Parse response JSON
4. Return structured dict that the LLM can reason about
5. Handle connection errors gracefully (service unavailable → return error message, don't crash)
6. Include a tool description that helps the LLM decide when to use it

STEP 3 — Update the Copilot system prompt:
The system prompt sent to Claude/Ollama should mention the new tools:
"You have access to planning intelligence tools: forecast accuracy, product segmentation, safety stock analysis, capacity alerts, and S&OP cycle management. Use these tools to answer questions about planning quality, inventory health, capacity constraints, and S&OP progress."

STEP 4 — Tests:
File: services/nlp-svc/tests/test_planning_tools.py
- Mock each HTTP call, verify tool returns expected structure
- Test error handling: service returns 500 → tool returns error message
- Test error handling: service unreachable → tool returns connectivity error
```

---

## PROMPT 9 — Docker + Kong Integration

```
MODULE: Infrastructure Integration — Docker Compose + Kong Routes
FILES: infrastructure/docker/

STEP 1 — Read existing compose and Kong files:
- Read infrastructure/docker/docker-compose.release2.yml (if exists from Phase 2)
- Read infrastructure/docker/kong.release2.yml (if exists)
- Read infrastructure/docker/docker-compose.yml (base)

STEP 2 — Add sop-svc to Docker Compose:
Add to docker-compose.release2.yml (or create docker-compose.planning.yml overlay):

sop-svc:
  build: ../../services/sop-svc
  ports: ["8110:8110"]
  environment:
    - IPE_DATABASE_URL=${IPE_DATABASE_URL}
    - IPE_JWT_SECRET_KEY=${IPE_JWT_SECRET_KEY}
  depends_on:
    db: { condition: service_healthy }
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8110/healthz"]
    interval: 30s
    timeout: 10s
    retries: 3

STEP 3 — Add Kong routes for sop-svc:
Add to kong.release2.yml (or kong.planning.yml):

- name: sop-svc
  url: http://sop-svc:8110
  routes:
    - name: sop-route
      paths: ["/api/v1/sop"]
      strip_path: false
  plugins:
    - name: jwt
    - name: request-transformer
      config:
        add:
          headers: ["X-Tenant-ID:$(jwt.tenant_id)"]

STEP 4 — Update deploy scripts:
Add sop-svc health check to scripts/release2-smoke.ps1

STEP 5 — Update .env.example with any new variables:
- SOP_SVC_URL=http://sop-svc:8110 (for inter-service calls from nlp-svc)
```

---

## Execution Checklist

Run prompts in this order. Check each box before proceeding.

```
[ ] PROMPT 0 — Master context (every session)
[ ] PROMPT 1 — Module B: ABC/XYZ Segmentation → verify: POST /segmentation/run returns 9-segment matrix
[ ] PROMPT 2 — Module A: Forecast Quality → verify: GET /error/mape returns MAPE with known test data
[ ] PROMPT 3 — Module D: ARIMA/SARIMA → verify: best-fit selects ARIMA for seasonal data
[ ] PROMPT 4 — Odoo Extensions → verify: lead time mapper syncs PO→receipt data
[ ] PROMPT 5 — Module C: Safety Stock → verify: SS formula matches known calculation
[ ] PROMPT 6 — Module E: Capacity Alerts → verify: overloaded WCs flagged above threshold
[ ] PROMPT 7A — S&OP Scaffold → verify: sop-svc starts on :8110, /healthz returns 200
[ ] PROMPT 7B — S&OP Logic → verify: consensus calculation with weighted average
[ ] PROMPT 8 — Copilot Tools → verify: all 9 tools registered and return structured data
[ ] PROMPT 9 — Docker/Kong → verify: full stack starts with sop-svc routed through Kong
```

After all prompts complete:
```
[ ] Run all migrations: alembic upgrade head
[ ] Run all backend tests: pytest across all modified services
[ ] Start full stack: docker compose up -d
[ ] Verify all services healthy: release2-smoke.ps1
[ ] Test Copilot: ask "What is our forecast accuracy?" and verify it calls the new tool
[ ] Tag: v9.2.0
```
