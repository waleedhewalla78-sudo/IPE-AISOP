# Contract: S&OP stage-gate scaffold

## Endpoints
- `GET /api/v1/planning-command/sop/stage-gate` — current cycle stages + status
- `POST /api/v1/planning-command/sop/stage-gate/advance` — advance one stage
- `POST /api/v1/planning-command/sop/stage-gate/skip` — skip to `management_review` (E2E-SOP-03 path)

## Stages (ordered)
`demand_review` → `supply_review` → `reconciliation` → `management_review` → `closed`

## Response shape
```json
{
  "success": true,
  "data": {
    "cycle_id": "...",
    "current_stage": "demand_review",
    "stages": [{"stage":"demand_review","status":"in_progress"}, ...],
    "can_skip_to_management_review": true
  }
}
```
