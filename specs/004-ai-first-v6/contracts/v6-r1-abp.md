# Contract: V6-R1 — Activity-Based Planning & FR-I-06 Guardrail

**Phase**: V6-R1 | **Tasks**: T001–T015 | **Exit**: SC-V6-01

---

## API Contracts

### GET `/api/v1/demand/priority/margin-aware`

**Auth**: Planner, Admin  
**Query**: `tenant_id` (from JWT), optional `mo_ids[]`

**Response 200**:

```json
{
  "data": {
    "priorities": [
      {
        "mo_id": "uuid",
        "base_priority_score": 72,
        "margin_adjusted_score": 88,
        "net_margin_usd": 12000.0,
        "activity_overhead_usd": 450.0,
        "data_quality": "complete"
      }
    ],
    "warnings": [
      {"mo_id": "uuid", "code": "MISSING_COST_DRIVER", "message": "Fell back to base priority"}
    ]
  }
}
```

### POST `/api/v1/capacity/schedule` (extended)

**New body fields**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `strategy` | string | `balanced` | `activity_optimized` \| `margin_throughput` \| existing values |
| `alpha` | float | 0.5 | 0=time-first, 1=cost-first |

**Response extension**:

```json
{
  "activity_cost_breakdown": {
    "overtime_usd": 1200.0,
    "setup_usd": 800.0,
    "expedite_usd": 0.0,
    "total_usd": 2000.0
  },
  "optimality_gap_pct": 3.2
}
```

### POST `/api/v1/capacity/schedule/approve` (guardrail)

**When** `feasibility_score < 85`:

**Response 422**:

```json
{
  "error": "GUARDRAIL_FEASIBILITY",
  "message": "ERP write-back blocked; feasibility below 85%",
  "feasibility_score": 82.5,
  "autonomy_mode": "suggest"
}
```

---

## Database: `cdm_activity_cost_drivers`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | RLS |
| product_id | UUID | nullable for WC-level |
| setup_mins | numeric | |
| overtime_rate_usd_per_hr | numeric | |
| expedite_cost_per_unit | numeric | |
| overhead_pct | numeric | 0–1 |
| updated_at | timestamptz | |

---

## Events

None new in R1 (guardrail uses existing audit stream).

---

## Acceptance Tests

| ID | Test |
|----|------|
| AC-R1-01 | MO-A margin $12k precedes MO-B $3k on shared bottleneck |
| AC-R1-02 | Missing driver → Warning, base priority used |
| AC-R1-03 | alpha=0 vs alpha=1 measurably different activity cost |
| AC-R1-04 | Approve blocked at feasibility 84; allowed at 85 |
| AC-R1-05 | Demo checkpoint 17 passes |
