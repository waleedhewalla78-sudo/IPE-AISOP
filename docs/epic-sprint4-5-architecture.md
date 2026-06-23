# AI-Driven Finite Scheduling & Closed-Loop Execution — Architecture

## Component Map (Existing vs New)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                                 │
│  ┌──────────────────────┐  ┌─────────────────────────────────────────┐ │
│  │ Control Tower (EXIST) │  │ Gantt Dashboard ★ NEW ★                │ │
│  │ - KPI cards           │  │ - Side-by-side native vs AI schedule   │ │
│  │ - Risk queue          │  │ - Disruption cascade highlight         │ │
│  │ - Bottleneck map      │  │ - Approval queue                       │ │
│  └──────────┬───────────┘  └──────────────────┬──────────────────────┘ │
└─────────────┼─────────────────────────────────┼────────────────────────┘
              │ HTTP + WS (existing)            │ HTTP
              ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY (nginx, existing)                    │
└──────┬──────────────────────┬──────────────────────┬───────────────────┘
       │                      │                      │
       ▼                      ▼                      ▼
┌──────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  dpe-svc     │   │  mat-svc         │   │  cap-svc         │
│  (EXIST)     │   │  (EXIST)         │   │  (MODIFY)        │
│ Demand       │   │ Priority netting │   │ OR-Tools solver  │
│ classify     │   │ Probabilistic ATP│   │ + FROZEN HORIZON │
│ priority     │   │ Supplier model   │   │ + WARM START     │
└──────┬───────┘   └────────┬─────────┘   │ + DISRUPTION EVT │
       │                     │             └────────┬─────────┘
       │                     │                       │
       ▼                     ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        fea-svc (EXIST)                                  │
│  5-gate feasibility scorer, auto-confirm, WS broadcaster               │
└────────────────────────────┬───────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        res-svc (EXIST)                                  │
│  Strategy generation, business scoring, optimistic-locked approval     │
└────────────────────────────┬───────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     CONNECTOR (MODIFY)                                  │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────────────────┐  │
│  │ Odoo Sync      │  │ Shadow Writer    │  │ Activation API        │  │
│  │ (EXIST)        │  │ (EXIST: shadow   │  │ ★ NEW ★               │  │
│  │ Products,      │  │  fields ipe_*)   │  │ POST /sync/odoo/      │  │
│  │ Demands,       │  │                  │  │   activate            │  │
│  │ Supply orders  │  │                  │  │ Optimistic lock via   │  │
│  └────────────────┘  └──────────────────┘  │ __last_update         │  │
│                                             │ + reserve/unreserve   │  │
│                                             └────────────────────────┘  │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ODOO ERP                                        │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────────────────┐  │
│  │ mrp.production │  │ Shadow fields    │  │ Action receiver       │  │
│  │ (live)         │  │ (EXIST: ipe_*)   │  │ (EXIST: HMAC)         │  │
│  │ date_start     │  │ x_ai_suggested_* │  │ confirm_mo,           │  │
│  │ date_finished  │  │ ★ NEW ★          │  │ reschedule_mo         │  │
│  └────────────────┘  └──────────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

                        NEW SERVICE
┌─────────────────────────────────────────────────────────────────────────┐
│                    ml-svc ★ NEW ★                                       │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────────────────┐  │
│  │ Duration       │  │ MLflow Registry  │  │ Inference API         │  │
│  │ Prediction     │  │ (uses existing   │  │ GET /predict/duration │  │
│  │ XGBoost model  │  │  cdm_model_     │  │ POST /predict/duration│  │
│  │                │  │  registry table) │  │ fallback to static    │  │
│  └────────────────┘  └──────────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

INFRASTRUCTURE (EXISTING)
┌──────┐  ┌──────┐  ┌────────────┐  ┌────────────────┐  ┌──────────────┐
│ PG   │  │Redis │  │ Kafka      │  │ Schema Reg     │  │ Prometheus   │
│ 16   │  │ 7    │  │ 7.7 (6p)   │  │ 7.7 (Avro)     │  │ + Grafana    │
└──────┘  └──────┘  └────────────┘  └────────────────┘  └──────────────┘
```

## New Kafka Topics Required

| Topic | Producer | Consumer(s) | Schema |
|---|---|---|---|
| `ipe.disruption.detected` | connector (Odoo webhook) | cap-svc (replan) | NEW Avro |
| `ipe.schedule.updated` | cap-svc (solver) | fea-svc, connector, frontend WS | NEW Avro |
| `ipe.ml.duration.predicted` | ml-svc | cap-svc (solver) | NEW Avro |

## New/Modified Service Boundaries

### cap-svc — Frozen Horizon + Dynamic Replan (MODIFY)

**Existing:** `solve_schedule(work_centers, operations, horizon, timeout)` — cold start, full horizon

**Changes needed:**
```
solve_schedule(work_centers, operations, horizon, timeout,
               frozen_ops: list[UUID] = None,    ← NEW
               warm_start: dict[str, int] = None) ← NEW
               -> dict
```
- `frozen_ops`: operations that must keep their current `planned_start`/`planned_end` (in-progress work orders). The solver adds `model.FixedDurationIntervalVar` for these or constrains their start/end to exact values.
- `warm_start`: optional `{operation_id: start_time}` hint passed via `solver.AddHint()` — available in OR-Tools CP-SAT.
- New event consumer on `ipe.disruption.detected` — triggers re-solve with frozen horizon.
- New event emitter on `ipe.schedule.updated` after successful re-solve.
- Performance target: <5s for up to 200 operations with <20% frozen.

### ml-svc — Predictive Duration Model (NEW)

```
services/ml-svc/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── trainer.py          ← XGBoost training pipeline
│   │   ├── predictor.py        ← Inference + fallback to static
│   │   ├── features.py         ← Feature engineering (product_id, wc_id, batch_size, operator_skill)
│   │   └── registry.py         ← MLflow model versioning via cdm_model_registry
│   └── api/v1/
│       └── predict.py          ← GET/POST /api/v1/predict/duration
├── pyproject.toml               ← depends on xgboost, scikit-learn, mlflow
├── Dockerfile
└── tests/
```

**Training:** Historical `cdm_work_order` actuals → features (product, work center, batch size, operator skill tags, day of week, month) → target `duration_actual_mins / duration_planned_mins` (ratio). XGBoost regressor, 15% MAE target.

**Inference:** `predict_duration(product_id, work_center_id, batch_size, operator_id) -> predicted_mins, confidence`  
Fallback: `duration_planned_mins * historical_avg_ratio` if ML endpoint unavailable.

**MLflow integration:** Existing `cdm_model_registry` table + `scripts/ml/train_cycle_time.py` pattern extended for XGBoost artifact tracking.

### connector — Shadow-to-Active Activation (MODIFY)

**New endpoint:**
```
POST /api/v1/sync/odoo/activate
{
  "mo_ids": ["uuid1", "uuid2"],
  "approved_by": "planner@example.com"
}
→ {
  "activated": ["uuid1"],
  "failed": [{"mo_id": "uuid2", "reason": "MATERIAL_CONFLICT"}]
}
```

**Logic:**
1. Read approved AI dates from `cdm_manufacturing_order` (shadow fields or columns)
2. Call Odoo `mrp.production.write({'date_planned_start': ..., 'date_planned_finished': ...})`
3. Handle Odoo reservation: call `do_unreserve()` before date change, `do_reserve()` after
4. If `UserError` raised (material conflict) → mark as `MATERIAL_CONFLICT` in response, surface to UI
5. Optimistic lock via Odoo's `__last_update` field (similar to our DB `version` column)
6. On success: clear shadow fields, post chatter message via `message_post()`

## Data Model Changes

### New Tables

```sql
-- Disruption events for dynamic replanning
CREATE TABLE cdm_disruption_event (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mo_id           UUID REFERENCES cdm_manufacturing_order(id),
    work_order_id   UUID REFERENCES cdm_work_order(id),
    work_center_id  UUID REFERENCES cdm_work_center(id),
    event_type      VARCHAR(50) NOT NULL,   -- 'machine_breakdown', 'material_shortage',
                                            -- 'operator_absence', 'quality_hold'
    severity        VARCHAR(20) NOT NULL,   -- 'critical', 'major', 'minor'
    description     TEXT,
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at     TIMESTAMPTZ,
    metadata        JSONB,                  -- flexible details
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ML prediction audit trail
CREATE TABLE cdm_duration_prediction (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mo_id            UUID REFERENCES cdm_manufacturing_order(id),
    work_order_id    UUID REFERENCES cdm_work_order(id),
    actual_duration_mins   NUMERIC(10,2),
    predicted_duration_mins NUMERIC(10,2) NOT NULL,
    model_version    VARCHAR(50) NOT NULL,
    confidence       NUMERIC(5,4),
    fallback_used    BOOLEAN NOT NULL DEFAULT false,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Existing Table Modifications

```sql
-- Add AI suggestion columns to manufacturing_order
ALTER TABLE cdm_manufacturing_order ADD COLUMN ai_suggested_start TIMESTAMPTZ;
ALTER TABLE cdm_manufacturing_order ADD COLUMN ai_suggested_end TIMESTAMPTZ;
ALTER TABLE cdm_manufacturing_order ADD COLUMN ai_schedule_version INTEGER DEFAULT 0;
ALTER TABLE cdm_manufacturing_order ADD COLUMN active_schedule_id UUID;   -- FK to approved resolution

-- Add disruption-ready statuses
ALTER TABLE cdm_manufacturing_order ADD COLUMN disruption_status VARCHAR(20)
    DEFAULT 'none' CHECK (disruption_status IN ('none', 'impacted', 'resolved'));

-- Add frozen horizon support to work_order
ALTER TABLE cdm_work_order ADD COLUMN is_frozen BOOLEAN NOT NULL DEFAULT false
    CHECK (is_frozen = false OR status IN ('in_progress', 'completed'));
ALTER TABLE cdm_work_order ADD COLUMN frozen_at TIMESTAMPTZ;
```

## Flow: Dynamic Replan (Story 2.2)

```
Time ->
1. Odoo webhook: work order status = 'blocked'
2. Connector receives webhook, maps to DisruptionEvent
3. Connector emits ipe.disruption.detected (Avro)
4. cap-svc consumer receives event
5. cap-svc loads current schedule from DB
6. cap-svc identifies frozen ops (status = in_progress, or within next 2h)
7. cap-svc calls solve_schedule(..., frozen_ops=..., warm_start=...)
8. Solver runs < 5 seconds, returns updated schedule
9. cap-svc writes updated dates to cdm_work_order / cdm_manufacturing_order
10. cap-svc emits ipe.schedule.updated (Avro)
11. fea-svc consumer re-scores affected MOs
12. Frontend WS broadcast: new schedule available
13. Planner sees red cascade on Gantt dashboard
```

## Flow: Shadow-to-Active Approval (Story 3.2)

```
Time ->
1. Planner reviews comparative Gantt in frontend
2. Planner clicks "Approve" on one or more MOs (new row action in risk queue or gantt)
3. Frontend calls POST /api/v1/sync/odoo/activate
4. Connector reads ai_suggested_start/end from cdm_manufacturing_order
5. Connector calls Odoo external API:
   a. Read __last_update (optimistic lock)
   b. Call do_unreserve() on existing reservations
   c. Write date_planned_start, date_planned_finished
   d. Call do_reserve()
   e. message_post("Schedule updated by IPE AI — approved by planner@example.com")
6. If success:
   - Copy ai_suggested_* -> planned_start/planned_end on cdm_manufacturing_order
   - Clear ai_suggested_* and shadow fields
   - Emit ipe.schedule.updated
7. If UserError (material conflict):
   - Return failed status with MATERIAL_CONFLICT reason
   - Frontend shows conflict badge, planner handles manually
```

## Solver Performance Strategy

| Scenario | Ops count | Timeout | Strategy |
|---|---|---|---|
| Cold solve (initial) | ≤ 500 | 60s | Standard CP-SAT, no hints |
| Dynamic replan | ≤ 200 | 5s | Frozen horizon + warm start hints |
| Scale risk | > 500 | 60s + fallback | Configurable planning horizon (default 14d), solver.StopSearch() returns best feasible |

## Dependencies for Odoo Admin

Before integration testing:

```xml
<!-- Odoo custom shadow fields required on mrp.production -->
<field name="x_ai_suggested_start" type="datetime"/>
<field name="x_ai_suggested_end" type="datetime"/>
<field name="x_ai_schedule_version" type="integer"/>
<field name="x_ai_approved_by" type="char" size="120"/>
<field name="x_ai_approved_at" type="datetime"/>
<field name="x_ai_rationale" type="text"/>
```

## Migration Plan

| Step | File | Description |
|---|---|---|
| 004 | `migrations/versions/004_add_disruption_events.py` | Create `cdm_disruption_event`, `cdm_duration_prediction` |
| 005 | `migrations/versions/005_add_ai_schedule_columns.py` | ALTER `cdm_manufacturing_order` + `cdm_work_order` |

## Testing Strategy

| Layer | Scope | Tool |
|---|---|---|
| Unit | Solver frozen horizon logic, warm start | pytest |
| Unit | ML feature engineering, fallback | pytest |
| Unit | Activation endpoint parsing, Odoo mock | pytest + respx |
| Integration | Solver → DB write → read back | pytest + asyncpg |
| Integration | Connector → mock Odoo (xmlrpc mock) | pytest + respx |
| E2E | Full lifecycle: classify → schedule → disrupt → replan → approve → activate | Existing `tests/integration/test_sprint2_e2e.py` + new tests |
| Performance | Solver 500 ops < 60s, replan < 5s | pytest-benchmark or k6 |
