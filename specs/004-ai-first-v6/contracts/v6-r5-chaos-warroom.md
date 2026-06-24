# Contract: V6-R5 — Cost of Chaos & Generative War Room

**Phase**: V6-R5 | **Tasks**: T046–T055 | **Exit**: SC-V6-05–08, tag v6.0.0

---

## API Contracts

### GET `/api/v1/analytics/cost-of-chaos`

**Auth**: CFO (read), Admin, Planner (read)

**Query**: `period=7d|30d`, optional `category`

**Response 200**:

```json
{
  "data": {
    "period": "7d",
    "total_chaos_usd": 48200.0,
    "categories": [
      {"code": "idle_time", "label": "Idle Time", "usd": 22000, "pct": 45.6},
      {"code": "rework", "label": "Rework", "usd": 15200, "pct": 31.5},
      {"code": "expedite", "label": "Expedite Freight", "usd": 11000, "pct": 22.9}
    ],
    "top_mos": [
      {"mo_id": "uuid", "chaos_usd": 8400, "primary_category": "idle_time"}
    ],
    "war_room_links": [
      {"disruption_id": "uuid", "chaos_usd": 12000}
    ]
  }
}
```

### GET `/api/v1/war-room/recovery-plan`

**Query**: `disruption_id` or auto from latest Tier-1 event

**Response 200**:

```json
{
  "data": {
    "disruption_id": "uuid",
    "impacted_mo_count": 12,
    "recovery_options": [
      {
        "rank": 1,
        "scenario_id": "uuid",
        "business_score_usd": 45000,
        "delivery_impact_days": 2,
        "activity_cost_usd": 3200,
        "summary": "Re-route MO-101/102 to WC-2"
      }
    ]
  }
}
```

---

## Database: `cdm_chaos_cost_snapshot`

Daily rollup per tenant; RLS enabled.

---

## Kafka: `ipe.chaos.metric` (optional tail)

Emitted on manual override audit entries for real-time dashboard refresh.

---

## Frontend Routes

| Route | Role |
|-------|------|
| `/cost-of-chaos` | CFO read, Admin |
| `/war-room` | Extended with recovery cards (003 base) |

---

## Release

- `READINESS.md` ≥96/100
- `RELEASE_NOTES.md` v6.0.0
- Git tag `v6.0.0`
- Demo checkpoints **17–20** in `run-full-demo.ps1`

---

## Acceptance Tests

| ID | Test |
|----|------|
| AC-R5-01 | ≥3 chaos categories with non-zero $ |
| AC-R5-02 | War Room shows top 3 with $ columns |
| AC-R5-03 | Copilot cites scenario IDs when routing enabled |
| AC-R5-04 | MS Project XML export downloads |
| AC-R5-05 | Demo 20/20 checkpoints pass |
