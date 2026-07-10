# IPE vs SAP IBP SAPIBP1 — Gap Analysis & Module Proposal

**Date:** July 2026  
**Source:** SAP IBP SAPIBP1 Planning Model Template, Release 2508 (209 pages)  
**Target:** IPE v9.x Release 2/3 roadmap  
**Author:** Product Management Assessment

---

## Executive Summary

SAP IBP's SAPIBP1 is a unified planning area covering five integrated planning domains: Demand Planning, S&OP, Supply Planning, Inventory Optimisation, and Demand Sensing — with 200+ key figures, 60+ planning levels, and dozens of planning operators. It represents 15+ years of enterprise planning product development at a price point of $200K–$500K/year.

IPE cannot and should not attempt feature parity with SAP IBP. That is a $100M+ engineering effort. Instead, this analysis identifies the **20% of SAP IBP capabilities that deliver 80% of the value** for IPE's target market (mid-market MENA discrete manufacturers), maps them against what IPE already has, and proposes new modules or modifications that create competitive differentiation while remaining buildable by a small team.

**The strategic insight:** SAP IBP's power comes from its planning model framework (key figures, planning levels, planning operators). IPE's advantage comes from its **intelligence layer** (Claude AI reasoning over planning data) and **implementation speed** (2–4 weeks vs 6–12 months). The winning strategy is not to replicate SAP IBP's data model — it is to deliver the same planning outcomes through AI-augmented workflows that are 10x faster to implement.

---

## 1. Capability Map — SAP IBP vs IPE Current State

### 1.1 Demand Planning

| SAP IBP Capability | SAP IBP Implementation | IPE Current State | Gap | Priority |
|---|---|---|---|---|
| Statistical forecasting (Exponential Smoothing, ARIMA, SARIMA) | Managed Forecast Models with best-fit selection | demand-svc: SES only. Prophet/LSTM optional. | **Significant** — missing ARIMA, SARIMA, best-fit selection | P1 |
| Gradient Boosting / ML forecasting | XGBoost as forecast algorithm with independent variables | Not implemented | **Gap** — but Claude can reason over forecast outputs | P2 |
| Croston method (intermittent demand) | Croston TSB with auto-coefficient | Not implemented | Gap — relevant for spare parts manufacturers | P3 |
| Forecast error calculation (MAPE, MASE, bias by lag) | Lag-based snapshot profiles, multi-lag error tracking | FR-R1-16 OTD baseline only. No MAPE/MASE by lag. | **Significant** — critical for forecast quality | P1 |
| ABC/XYZ segmentation | K-Means clustering on revenue + demand variability | Not implemented | **Gap** — important for inventory and demand prioritisation | P1 |
| Demand sensing (42-day short-term) | Gradient Boosting on daily data | demand-svc has SES. No daily granularity. | Gap — Phase 2 addresses partially | P2 |
| Impact analysis (events, marketing budget on forecast) | Independent variables in forecast model | Not implemented | Gap — valuable but requires customer data maturity | P3 |
| Forecast disaggregation | Disaggregation factors for top-down planning | Not implemented | Gap | P3 |
| Data cleansing (outlier detection, mean/stddev) | StdDevActualsQty model, manual adjustment keys | Not implemented | Gap | P2 |
| Forecast stability tracking | Cycle-over-cycle forecast change monitoring | Not implemented | Gap | P3 |
| Forecast value-add analysis | Measures improvement from manual adjustments | Not implemented | Gap — useful for process maturity | P3 |

### 1.2 Sales & Operations Planning (S&OP)

| SAP IBP Capability | SAP IBP Implementation | IPE Current State | Gap | Priority |
|---|---|---|---|---|
| S&OP process workflow (demand review → supply review → reconciliation → management review) | Planning views, workspaces, dashboards per step | No formal S&OP process workflow | **Critical** — this is the core S&OP gap | P1 |
| Consensus demand planning | Sales + marketing + finance inputs → consensus qty | Not implemented | **Critical** — key S&OP capability | P1 |
| Version management (baseline, upside, downside) | Multi-version key figures, version comparison analytics | Not implemented | **Significant** | P1 |
| Annual Operating Plan (AOP) integration | AOP qty/rev imported, compared to consensus | Not implemented | Gap — requires customer finance data | P2 |
| Cost rollup (aggregated unit cost across supply network) | Network aggregation operator, 20+ cost key figures | Not implemented | **Significant** — needed for financial S&OP | P2 |
| Profit & loss in S&OP (gross profit, margin, COGS) | Calculated from consensus × price – cost | Basic cost-of-chaos in dpe-svc | **Gap** — needs expansion | P2 |
| Forecast consumption (sales orders consuming forecast) | Time-series-based consumption algorithm | Not implemented | Gap | P2 |
| Supply review (heuristic + optimiser) | Time-series-based supply planning algorithms | cap-svc has OR-Tools scheduler | **Partial** — OR-Tools covers scheduling but not TS supply planning | P2 |
| Reconciliation review dashboards | Revenue vs AOP, constrained vs consensus, capacity utilisation | Not implemented | Gap | P2 |
| Management business review analytics | Executive-level quarterly comparison, profit by version | OTD dashboard (Sprint 6 of Phase 2) | Partial — needs expansion | P2 |

### 1.3 Supply Planning

| SAP IBP Capability | SAP IBP Implementation | IPE Current State | Gap | Priority |
|---|---|---|---|---|
| Time-series-based supply heuristic | Multi-period heuristic across supply network | cap-svc OR-Tools solver (single-period focus) | **Partial** — different algorithm approach | P2 |
| Supply optimiser (LP/MIP-based) | Cost-minimising supply allocation across network | cap-svc OR-Tools CP-SAT | Partial — same solver class, different model | P2 |
| Capacity planning (utilisation, overload alerts) | UTILIZATIONPCT, ALRTCAPACITYOVERLOAD key figures | cap-svc has capacity analytics (Phase 2 Sprint 9) | Partial — extend with alerts | P2 |
| Multi-resource scheduling | Resource allocation across locations and products | cap-svc handles single-plant scheduling | Gap — multi-plant is Phase 3 | P3 |
| Transportation planning | Transport qty by lane, from/to location | supply-svc has network topology (v8.2) | Partial — extend with transport planning | P3 |
| Component explosion (dependent demand) | BOM explosion for material requirements | mat-svc has ATP/netting | Partial | P2 |
| Fair share distribution | Proportional allocation when supply < demand | Not implemented | Gap — useful for constrained scenarios | P3 |
| Forecast consumption | Sales orders consuming input forecast | Not implemented | Gap | P2 |

### 1.4 Inventory Optimisation

| SAP IBP Capability | SAP IBP Implementation | IPE Current State | Gap | Priority |
|---|---|---|---|---|
| Multi-stage inventory optimisation | Global safety stock optimisation across network echelons | Not implemented | **Critical gap for enterprise** | P2 |
| Safety stock calculation | Service level → safety stock, demand/lead time variability | mat-svc has basic reorder suggestions (Phase 2 Sprint 10) | **Significant** — needs proper statistical model | P1 |
| Service level prediction | Predict service level from safety stock levels | Not implemented | Gap | P2 |
| Inventory budget entitlement | Budget allocation across product families and regions | Not implemented | Gap — relevant for enterprise tier | P3 |
| EOQ (Economic Order Quantity) | Fixed cost per order, holding cost rate calculations | Not implemented | Gap | P3 |
| Inventory health (slow-moving, excess, obsolete) | Consumption rate analysis, stock classification | mat-svc has slow-moving detection (Phase 2 Sprint 10) | Partial | P2 |
| Lead time variability analysis | Production and transportation lead time CV | Not implemented | Gap — important for safety stock accuracy | P2 |
| Scenario analysis for inventory | Impact of parameter changes on safety stock and service level | scenario-svc exists but not connected to inventory | Partial — connect existing scenario engine | P2 |

### 1.5 Analytics & Alerts

| SAP IBP Capability | SAP IBP Implementation | IPE Current State | Gap | Priority |
|---|---|---|---|---|
| Preconfigured analytics stories (6 personas) | Demand planner, inventory planner, supply planner, sales manager, finance, S&OP lead | Control Tower + Resolution Center + OTD dashboard | **Significant** — need persona-based dashboards | P1 |
| Alert framework (threshold-based) | Safety stock delta, capacity overload, demand sensing threshold | fea-svc has feasibility alerts. alert-svc has war room. | Partial — extend alert types | P2 |
| Planning views per role | Role-specific data views with filtered key figures | VITE_RELEASE_PROFILE exists but not role-based views | Gap — but RBAC is OQ-3 | P2 |
| Planner workspaces | Configurable workspace with preferred views and charts | Not implemented | Gap | P3 |
| Supply chain network visualisation | Network topology map with flow visualisation | supply-svc has topology data | Partial — add visualisation | P2 |

### 1.6 Footprint / Sustainability

| SAP IBP Capability | SAP IBP Implementation | IPE Current State | Gap | Priority |
|---|---|---|---|---|
| CO2 emissions rollup across supply chain | Carbon rollup operator, emissions per unit by location | sustain-svc exists (v8.2) with basic ESG scoring | Partial — extend with emissions rollup | P3 |
| Emissions scenario comparison | Compare CO2 across supply versions | scenario-svc not connected to sustainability | Gap | P3 |

---

## 2. Proposed New Modules

Based on the gap analysis, I propose **6 new modules** and **4 major modifications** to existing services. Ordered by priority and customer value.

### Module 1: S&OP Process Engine (NEW SERVICE)

**Priority:** P1 — This is the most valuable missing capability  
**Service:** `sop-svc` at `:8110`  
**Effort:** 8–12 weeks  
**Phase:** R2/R3

**What it does:** Implements a structured S&OP process with four stages: demand review, supply review, reconciliation, and management review. Each stage has defined inputs, outputs, and approval gates.

**Key features:**
- S&OP cycle management (monthly cycle with configurable stages)
- Consensus demand calculation: weighted combination of sales forecast, marketing forecast, statistical forecast, and finance plan
- Version management: baseline, upside, downside, what-if versions with comparison
- Stage gates: demand must be reviewed before supply review starts
- Reconciliation dashboard: constrained demand vs consensus, capacity utilisation, financial impact
- Management review: executive summary with top 5 decision items

**Database:**

| Table | Key Fields |
|---|---|
| `cdm_sop_cycle` | id, tenant_id, cycle_month, status (demand_review, supply_review, reconciliation, management_review, closed) |
| `cdm_sop_version` | id, cycle_id, version_type (baseline, upside, downside, whatif), name |
| `cdm_consensus_demand` | id, version_id, product_id, location_id, period, qty, revenue, cost, profit |
| `cdm_sop_stage_gate` | id, cycle_id, stage, approved_by, approved_at |

**API endpoints:**

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/sop/cycle` | Create new S&OP cycle |
| GET | `/api/v1/sop/cycle/{id}` | Get cycle with stage status |
| POST | `/api/v1/sop/cycle/{id}/demand-review` | Submit demand review |
| POST | `/api/v1/sop/cycle/{id}/supply-review` | Submit supply review |
| POST | `/api/v1/sop/cycle/{id}/reconciliation` | Submit reconciliation |
| POST | `/api/v1/sop/cycle/{id}/approve/{stage}` | Approve stage gate |
| GET | `/api/v1/sop/consensus` | Get consensus demand by version |
| POST | `/api/v1/sop/version` | Create what-if version |
| GET | `/api/v1/sop/version/compare` | Compare two versions |

**IPE differentiation vs SAP IBP:** SAP IBP requires planners to configure planning views and manually run operators. IPE's Copilot generates the S&OP executive summary automatically using Claude, synthesising data across all stages. The planner asks "generate S&OP briefing for September" and gets a structured narrative in 30 seconds.

---

### Module 2: Forecast Quality Engine (MODIFICATION to demand-svc)

**Priority:** P1 — Customers cannot improve without measurement  
**Service:** Extend `demand-svc` at `:8040`  
**Effort:** 4–6 weeks  
**Phase:** R2

**What it adds:**

| Feature | SAP IBP Equivalent | IPE Implementation |
|---|---|---|
| MAPE calculation by lag (1, 3, 6 months) | Lag-based snapshot profiles | Store forecast snapshots monthly. Calculate MAPE comparing snapshot to actuals. |
| Bias measurement | CONSENSUSDEMANDQTYBIAS | (forecast - actuals) / actuals as signed metric |
| MASE (Mean Absolute Scaled Error) | FORECASTMASE | MASE using naive forecast as baseline |
| Forecast stability | Cycle-over-cycle change tracking | Compare current forecast to previous cycle for same future period |
| Forecast value-add | Manual adjustment impact measurement | Compare stat forecast error to final demand plan error |

**Database:**

| Table | Key Fields |
|---|---|
| `cdm_forecast_snapshot` | id, tenant_id, product_id, snapshot_date, forecast_date, forecast_qty, model_version |
| `cdm_forecast_error` | id, tenant_id, product_id, period, lag_months, mape, mase, bias, forecast_qty, actuals_qty |

**API endpoints:**

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/demand/snapshot` | Trigger snapshot creation |
| GET | `/api/v1/demand/error/mape` | MAPE by product, period, lag |
| GET | `/api/v1/demand/error/bias` | Bias by product, period, lag |
| GET | `/api/v1/demand/error/stability` | Forecast stability metrics |
| GET | `/api/v1/demand/error/value-add` | Value-add analysis |

---

### Module 3: ABC/XYZ Segmentation Engine (MODIFICATION to mat-svc)

**Priority:** P1 — Foundation for inventory and demand prioritisation  
**Service:** Extend `mat-svc` at `:8002`  
**Effort:** 2–3 weeks  
**Phase:** R2

**What it adds:**
- ABC classification by revenue (A: top 80%, B: next 15%, C: bottom 5%)
- XYZ classification by demand variability (X: CV < 0.5, Y: 0.5–1.0, Z: > 1.0)
- Combined ABC/XYZ matrix (9 segments)
- Service level targets by segment (A-X: 99%, C-Z: 85%)
- Segmentation drives safety stock policy, forecast model selection, and planning attention

**Database:**

| Table | Key Fields |
|---|---|
| `cdm_product_segment` | id, tenant_id, product_id, abc_class, xyz_class, combined_segment, revenue_share_pct, cv |

**IPE differentiation:** SAP IBP runs segmentation as a batch operator. IPE's Copilot can explain: "Product X moved from A-X to B-Y because sales dropped 30% in Q3. Your safety stock policy should shift from 99% to 95% service level, saving $12K/year in holding cost."

---

### Module 4: Safety Stock Calculator (MODIFICATION to mat-svc)

**Priority:** P1 — Direct financial impact for customers  
**Service:** Extend `mat-svc` at `:8002`  
**Effort:** 3–4 weeks  
**Phase:** R2/R3

**What it adds:**
- Statistical safety stock calculation: SS = z × σ_demand × √(lead_time) + z × d̄ × σ_lead_time
- Service level → z-score mapping (90% → 1.28, 95% → 1.65, 99% → 2.33)
- Lead time variability from Odoo PO history
- Demand variability from sales history
- Recommended safety stock vs current stock comparison
- Safety stock delta tracking (cycle-over-cycle change)
- Safety stock valuation (qty × standard cost)

**Database:**

| Table | Key Fields |
|---|---|
| `cdm_safety_stock` | id, tenant_id, product_id, location_id, recommended_qty, current_qty, delta, service_level_target, demand_cv, lead_time_cv, valuation |

---

### Module 5: Planning Operators Framework (NEW CORE)

**Priority:** P2 — Infrastructure for configurable algorithms  
**Service:** Core framework in `ipe_shared/`  
**Effort:** 4–6 weeks  
**Phase:** R3

**What it adds:**

SAP IBP's power comes from planning operators — configurable algorithms that transform key figures. IPE needs a lightweight equivalent:

| Operator Type | What It Does | IPE Implementation |
|---|---|---|
| Copy operator | Copy key figure values between planning levels | Python function: copy source KF to target KF with optional aggregation |
| Forecast operator | Run statistical forecast on historical data | Calls demand-svc forecaster with configurable model selection |
| Segmentation operator | Run ABC/XYZ on product data | Calls mat-svc segmentation engine |
| Supply operator | Run supply heuristic/optimiser | Calls cap-svc OR-Tools solver with parameters |
| Inventory operator | Run safety stock calculation | Calls mat-svc safety stock calculator |
| Snapshot operator | Create lag-based snapshot for error tracking | Calls demand-svc snapshot API |
| S&OP operator | Run consensus calculation | Calls sop-svc consensus engine |

**Architecture:**

```python
# ipe_shared/planning_operators/base.py
class PlanningOperator:
    def __init__(self, tenant_id: str, config: dict): ...
    async def execute(self) -> OperatorResult: ...
    
class CopyOperator(PlanningOperator): ...
class ForecastOperator(PlanningOperator): ...
class SegmentationOperator(PlanningOperator): ...
```

**IPE differentiation:** SAP IBP operators are rigid configurations. IPE operators are AI-augmented — the Copilot can suggest "you should re-run segmentation because Q3 actuals shifted 15 products from A to B segment" and trigger the operator with one click.

---

### Module 6: Key Figure Framework (MODIFICATION to CDM)

**Priority:** P2 — Data model alignment with planning standards  
**Service:** Database migration + shared library  
**Effort:** 3–4 weeks  
**Phase:** R3

**What it adds:**

IPE's current data model stores planning data in domain-specific tables (cdm_manufacturing_order, cdm_demand_line, etc.). SAP IBP uses a unified key figure model where all planning data is stored as key figure values at specific planning levels.

IPE does not need SAP IBP's full key figure architecture (that would require rewriting the entire CDM). Instead, add a **key figure overlay** that maps IPE's existing data into standardised planning metrics:

| Key Figure Group | Key Figures | Source |
|---|---|---|
| Demand | ACTUALSQTY, STATISTICALFORECASTQTY, CONSENSUSDEMANDQTY, SALESFORECASTQTY | cdm_demand_line, cdm_forecast |
| Supply | PRODUCTION, RECEIPT, PROJECTEDINVENTORY, INITIALINVENTORY | cdm_manufacturing_order, cdm_supply_order |
| Capacity | CAPASUPPLY, CAPAUSAGE, UTILIZATIONPCT | cap-svc scheduling output |
| Inventory | SAFETYSTOCK, REORDERPOINT, INVENTORYPOSITION, SERVICELEVEL | cdm_safety_stock, mat-svc |
| Financial | COSTPERUNIT, PLANNEDPRICE, GROSSPROFIT, CONSTRAINEDDEMANDREV | cdm_product, sop-svc |
| Error | FORECASTMAPE, FORECASTBIAS, FORECASTMASE | cdm_forecast_error |

**Database:**

| Table | Key Fields |
|---|---|
| `cdm_key_figure_value` | id, tenant_id, key_figure_id, product_id, location_id, period_start, period_type (day/week/month), version_id, value, uom |
| `cdm_key_figure_definition` | id, key_figure_id, name_en, name_ar, unit_type (qty/currency/pct), domain, calculation_formula |

---

## 3. Modifications to Existing Services

### 3.1 demand-svc — Add ARIMA/SARIMA + Best-Fit Selection

**Current:** SES only (Prophet/LSTM optional when libs available)  
**Add:** 
- ARIMA/SARIMA via `statsmodels` 
- Best-fit selection: run SES, ARIMA, Prophet in parallel, select by lowest MAPE
- Forecast model configuration per product segment (ABC-driven)

**Effort:** 2–3 weeks

### 3.2 cap-svc — Add Capacity Utilisation Alerts

**Current:** OR-Tools solver + analytics (Phase 2 Sprint 9)  
**Add:**
- UTILIZATIONPCT key figure per resource per period
- Alert threshold: trigger when utilisation > 90% (configurable)
- Capacity overload report: resources ranked by overload severity

**Effort:** 1–2 weeks

### 3.3 fea-svc — Add Version-Aware Feasibility Scoring

**Current:** Single-version feasibility scoring  
**Add:**
- Score feasibility against multiple S&OP versions (baseline, upside, downside)
- Compare feasibility scores across versions
- Flag MOs that are feasible in baseline but infeasible in upside scenario

**Effort:** 2–3 weeks

### 3.4 connector — Add S&OP Data Pull from Odoo

**Current:** Syncs MOs, BOMs, routings, WCs, products, customers, suppliers, demands, supply orders  
**Add:**
- Pull sales forecast from Odoo CRM (if available)
- Pull actual revenue from Odoo accounting
- Pull AOP data if stored in Odoo budgets module
- Map to S&OP key figures

**Effort:** 2–3 weeks

---

## 4. Priority Roadmap

### Phase 2 (R2) — Build Immediately

| # | Module/Change | Effort | Value |
|---|---|---|---|
| 1 | Forecast Quality Engine (MAPE, bias, stability) | 4–6 wks | Enables measurement → improvement cycle |
| 2 | ABC/XYZ Segmentation | 2–3 wks | Foundation for all inventory and demand decisions |
| 3 | Safety Stock Calculator | 3–4 wks | Direct financial impact: right-size inventory |
| 4 | ARIMA/SARIMA + best-fit in demand-svc | 2–3 wks | Forecast accuracy improvement |
| 5 | Capacity utilisation alerts | 1–2 wks | Proactive bottleneck detection |

**Total R2 effort: 12–18 weeks (1 developer)**

### Phase 3 (R3) — Build After R2 Validated

| # | Module/Change | Effort | Value |
|---|---|---|---|
| 6 | S&OP Process Engine (sop-svc) | 8–12 wks | Enterprise-grade S&OP process |
| 7 | Planning Operators Framework | 4–6 wks | Configurable algorithm platform |
| 8 | Key Figure Framework | 3–4 wks | Standardised planning data model |
| 9 | Version-aware feasibility scoring | 2–3 wks | Multi-scenario planning |
| 10 | S&OP data pull from Odoo connector | 2–3 wks | Complete data integration |

**Total R3 effort: 19–28 weeks (2 developers)**

### Phase 4 (R4) — Enterprise Features

| # | Module/Change | Effort | Value |
|---|---|---|---|
| 11 | Multi-stage inventory optimisation | 8–12 wks | Enterprise inventory planning |
| 12 | CO2 emissions rollup | 3–4 wks | ESG compliance for Gulf enterprises |
| 13 | Inventory budget entitlement | 4–6 wks | Financial inventory governance |
| 14 | Demand sensing (daily, ML-based) | 4–6 wks | Short-term demand accuracy |
| 15 | Driver-based planning (causal factors) | 6–8 wks | Advanced demand modelling |

**Total R4 effort: 25–36 weeks (2 developers)**

---

## 5. What IPE Should NOT Build

These SAP IBP capabilities are **not worth replicating** for IPE's target market:

| Capability | Why Skip |
|---|---|
| 60+ planning levels with UoM/currency conversion at each | Over-engineered for mid-market. IPE's product × location × period is sufficient. |
| Full SAPIBP1 key figure taxonomy (200+ key figures) | Most are intermediate calculation artifacts. IPE needs ~40 key figures. |
| Time-series-based supply planning algorithms (SAP's proprietary heuristic) | OR-Tools CP-SAT is more flexible and already implemented. |
| Planning area configuration framework | Enterprise infrastructure overhead. IPE uses code-configured services. |
| Managed Forecast Models UI (SAP's model builder) | Replace with AI-selected best-fit. The Copilot picks the model, not the planner. |
| Custom attribute as key figure framework | Database engineering that adds complexity without customer value. |
| Cross-currency and cross-UoM planning levels | Most IPE customers operate in a single currency (EGP, AED, SAR). Add only when needed. |

---

## 6. Competitive Positioning After Modules Built

With the proposed modules implemented through R2–R4:

| Dimension | SAP IBP | IPE (after modules) | IPE Advantage |
|---|---|---|---|
| S&OP process | 4-stage with operator-driven | 4-stage with AI-generated synthesis | AI generates the S&OP briefing in 30 seconds |
| Demand planning | 8 algorithm types, manual model config | Best-fit auto-selection, AI-explained forecast | Planner doesn't need to understand ARIMA |
| Forecast quality | Lag-based snapshots, manual error review | MAPE/bias auto-tracked, AI explains what to improve | Copilot says "segment B products have 40% MAPE — retrain on weekly data" |
| Inventory | Multi-stage optimisation, 30+ key figures | Statistical safety stock + AI recommendations | Right answer in 2 weeks of implementation, not 6 months |
| Supply planning | Heuristic + LP/MIP optimiser | OR-Tools CP-SAT + AI scenario analysis | Same solver quality, 10x faster implementation |
| Implementation time | 6–12 months, $200K+ | 2–4 weeks, $18K–$30K | 10x faster, 10x cheaper |
| Arabic | Translatable but not default | Arabic-first, RTL native | Built for MENA, not adapted |
| User experience | Planning views + Excel add-in | Control Tower + Copilot + mobile PWA | Planner asks questions in Arabic, gets answers |

---

## 7. Cursor Implementation — Module 1 Quick Start (S&OP Process Engine)

```
I'm building the S&OP Process Engine for IPE as a new service.

Workspace: E:\AISOP\ipe
Pattern: Follow existing service structure (e.g., services/demand-svc/)

Create services/sop-svc/ with:
1. app/api/v1/sop.py — endpoints for cycle management, stage gates, consensus calculation, version comparison
2. app/core/consensus.py — consensus demand calculation: weighted average of sales forecast, marketing forecast, statistical forecast
3. app/core/version.py — version management: create, compare, clone versions
4. app/models/ — SQLAlchemy models: SopCycle, SopVersion, ConsensusDemand, SopStageGate
5. app/main.py — FastAPI app on port 8110
6. Dockerfile — matching other services
7. tests/ — unit tests for consensus calculation, version comparison

Database tables needed (Alembic migration):
- cdm_sop_cycle (id, tenant_id, cycle_month, status, created_at)
- cdm_sop_version (id, cycle_id, version_type, name, created_at)
- cdm_consensus_demand (id, version_id, product_id, location_id, period_start, qty, revenue, cost, profit)
- cdm_sop_stage_gate (id, cycle_id, stage, approved_by, approved_at)

Consensus calculation:
consensus_qty = w_sales * sales_forecast + w_stat * statistical_forecast + w_marketing * marketing_forecast
where weights are configurable per tenant in cdm_tenant.config

Follow existing service conventions: Pydantic v2 schemas, JWT auth, X-Tenant-ID header, RLS on tenant_id.
```

---

*End of SAP IBP Gap Analysis. Execute modules in priority order: P1 items in Phase 2, P2 in Phase 3, P3/P4 in Phase 4.*
