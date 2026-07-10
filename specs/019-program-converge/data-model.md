# Data Model: 019-program-converge

## PlanningScenario (existing)

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| tenant_id | UUID | RLS |
| name | string(128) | required |
| description | text | optional |
| status | string(24) | `active` \| `promoted` \| `archived` |
| created_by | string | user sub |
| completed_at | timestamptz | set on simulate |

**Transition**: `active` → `promoted` (idempotent if already promoted).

## Odoo stock.quant (mock)

| Field | Type | Notes |
|-------|------|-------|
| id | int | mock id |
| product_id | [id, name] | Odoo many2one shape |
| quantity | float | on-hand |
| reserved_quantity | float | reserved |
| location_id | [id, name] | usage=internal implied by filter |

**CDM mapping**: available = quantity − reserved → `Product.safety_stock` (existing connector behavior).
