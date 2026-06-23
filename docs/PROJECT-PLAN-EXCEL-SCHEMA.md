# Project Plan Excel Schema (v1.0)

Use this format when preparing project plans for upload on the **Schedule** page.

## File requirements

| Rule | Value |
|------|--------|
| Format | `.xlsx` only (Excel 2007+) |
| Max size | 5 MB |
| Sheet | First worksheet is read (recommended name: `ProjectPlan`) |
| Header row | Row 1 — exact column names below (case-insensitive) |
| Data rows | Row 2 onward — one operation per row |

## Column specification

| Column | Required | Type | Example | Rules |
|--------|----------|------|---------|-------|
| PLAN_CODE | Yes | text | `PLAN-DEMO-Q3` | Same value on every row; unique per tenant |
| PLAN_NAME | Yes | text | `Q3 Widget Production Plan` | Same value on every row |
| MO_ID | Yes | text | `MO-DEMO-001` | Manufacturing order reference |
| OPERATION_SEQUENCE | Yes | integer | `10` | Unique per MO_ID within the file |
| OPERATION_NAME | Yes | text | `Assemble Widget A` | Shown on Gantt chart |
| WORK_CENTER_CODE | Yes | text | `WC001` | Must match work center master (WC001, WC002, WC003) |
| START_HOUR | Yes | number | `1.5` | Hours from schedule horizon start (0 = hour zero) |
| DURATION_HOURS | Yes | number | `2.0` | Must be > 0 |
| STATUS | No | text | `planned` | `planned`, `frozen`, `disrupted`, or `ai_suggested` (default: `planned`) |
| NOTES | No | text | `Expedite lane` | Optional planner comment |

## Example rows (demo tenant)

```
PLAN_CODE          | PLAN_NAME              | MO_ID        | OPERATION_SEQUENCE | OPERATION_NAME      | WORK_CENTER_CODE | START_HOUR | DURATION_HOURS | STATUS
PLAN-DEMO-Q3       | Q3 Demo Production     | MO-DEMO-001  | 10                 | Machine Widget      | WC002            | 0          | 1.5            | planned
PLAN-DEMO-Q3       | Q3 Demo Production     | MO-DEMO-001  | 20                 | Assemble Widget A   | WC001            | 1.5        | 2              | planned
PLAN-DEMO-Q3       | Q3 Demo Production     | MO-DEMO-005  | 10                 | Fabricate Gadget B  | WC002            | 2.5        | 2.5            | frozen
```

## Upload modes

| Mode | When to use | System behavior |
|------|-------------|-----------------|
| **Create new plan** | First upload for a PLAN_CODE | Creates plan + version 1 (active) |
| **Update existing plan** | Revised Excel for same PLAN_CODE | Creates version N+1 (active); previous versions kept |

## Version control

- Each upload creates an immutable version record.
- Only one version is **active** at a time (shown on Gantt when "Uploaded project plan" is selected).
- Use **Activate** in version history to roll back to an older version.

## API schema endpoint

Developers and integrators can fetch the machine-readable schema:

```
GET /api/v1/capacity/project-plans/schema
Authorization: Bearer <token>
```

## Changing the schema later

1. Update `app/core/project_plan_schema.py` (`COLUMN_SPECS`, bump `SCHEMA_VERSION`).
2. Update this document.
3. Add migration only if new fields must be persisted beyond the JSON operations payload.
