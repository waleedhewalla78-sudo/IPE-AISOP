# Contract: Promote Scenario

## `POST /api/v1/scenario/{scenario_id}/promote`

**Auth**: Bearer JWT; roles `planner` | `admin` | `manager`  
**Tenant**: from token / middleware `tenant_ctx`

### Success 200

```json
{
  "success": true,
  "data": {
    "scenario_id": "uuid",
    "status": "promoted",
    "name": "string"
  },
  "error": null
}
```

### Not found 200 (APIResponse envelope)

```json
{
  "success": false,
  "data": null,
  "error": { "code": "NOT_FOUND", "message": "Scenario not found" }
}
```

### Rules

- Must match `tenant_id`
- Idempotent if already `promoted`
- Does not call connector / ERP
