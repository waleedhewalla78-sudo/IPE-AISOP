# Contract: V6-R3 — Visual CPM Drag-Drop Gantt

**Phase**: V6-R3 | **Tasks**: T029–T036 | **Exit**: SC-V6-03

---

## API Contracts

### POST `/api/v1/capacity/cpm/cascade`

**Auth**: Planner, Admin

**Body**:

```json
{
  "mo_id": "uuid",
  "operation_id": "uuid",
  "delta_minutes": 2880,
  "mode": "preview"
}
```

**Response 200** (target p95 <2000ms for ≤20 MOs):

```json
{
  "data": {
    "operations": [
      {
        "operation_id": "uuid",
        "planned_start": "2026-07-01T08:00:00Z",
        "planned_end": "2026-07-01T12:00:00Z",
        "is_critical": true,
        "slack_minutes": 0
      }
    ],
    "critical_path_ids": ["uuid", "uuid"],
    "financial_delta": {
      "overtime_usd": 150.0,
      "tardiness_penalty_usd": 0.0,
      "activity_cost_delta_usd": 150.0
    },
    "conflicts": [],
    "cascade_ms": 842
  }
}
```

**When infeasible**:

```json
{
  "conflicts": [
    {
      "operation_id": "uuid",
      "reason": "WC CNC-01 capacity exceeded on 2026-07-02"
    }
  ]
}
```

### POST `/api/v1/capacity/cpm/apply`

**Body**: `{ "cascade_token": "..." }` or full operation snapshot from preview

**Behavior**: Sets `ai_suggested_*` only; user must call existing `/schedule/approve`.

---

## Frontend

| Component | Behavior |
|-----------|----------|
| `GanttChart.tsx` | Drag bar → debounced cascade preview |
| Critical path | Red border + dependency SVG arrows |
| Confirm | Opens approve modal (003 flow) |

---

## Metrics

- `cap_svc_cpm_cascade_duration_seconds` histogram
- SLO alert if p95 > 2s on demo tenant

---

## Acceptance Tests

| ID | Test |
|----|------|
| AC-R3-01 | Drag +2 days updates critical path within 2s p95 |
| AC-R3-02 | Infeasible drag highlights conflict reason |
| AC-R3-03 | Apply does not write ERP until approve |
| AC-R3-04 | Demo checkpoint 19 passes |
