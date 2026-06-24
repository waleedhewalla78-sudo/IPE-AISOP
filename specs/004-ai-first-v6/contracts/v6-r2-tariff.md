# Contract: V6-R2 — Attribute-Based Planning & Tariff Shock

**Phase**: V6-R2 | **Tasks**: T016–T028 | **Exit**: SC-V6-02

---

## API Contracts

### POST `/api/v1/material/probabilistic-atp` (extended response)

**New fields per line**:

```json
{
  "landed_cost_per_unit": 14.25,
  "landed_cost_breakdown": {
    "base_usd": 10.0,
    "freight_usd": 1.5,
    "tariff_usd": 2.0,
    "risk_premium_usd": 0.75
  },
  "material_attributes": {
    "origin_region": "Region_X",
    "tariff_code": "HS-8471",
    "carbon_intensity_kg": 12.4
  }
}
```

### POST `/api/v1/demand/tariff/shock`

**Auth**: Planner, Admin

**Body**:

```json
{
  "region": "Region_X",
  "tariff_delta_pct": 25.0,
  "margin_threshold_pct": 15.0
}
```

**Response 200**:

```json
{
  "data": {
    "affected_mo_count": 4,
    "mos_below_threshold": [
      {
        "mo_id": "uuid",
        "net_margin_before": 18000,
        "net_margin_after": 11200,
        "erosion_usd": 6800
      }
    ],
    "substitute_drafts": [
      {
        "mo_id": "uuid",
        "from_material_id": "uuid",
        "to_material_id": "uuid",
        "status": "pending_approval"
      }
    ]
  }
}
```

### POST `/api/v1/demand/tariff/substitute-draft`

Enqueues connector action `sync_bom_substitution` — **no autonomous ERP write**.

---

## Database

### `cdm_material_attributes`

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID (RLS) |
| material_id | UUID |
| attributes | JSONB | origin, tariff_code, carbon_intensity |

### `cdm_landed_cost_profiles`

| Column | Type |
|--------|------|
| id | UUID PK |
| tenant_id | UUID (RLS) |
| supplier_id | UUID nullable |
| region | text |
| base_cost_usd | numeric |
| freight_usd | numeric |
| tariff_pct | numeric |
| risk_premium_pct | numeric |

---

## Kafka: `ipe.tariff.shock`

**Schema**: `ipe_tariff_shock.avsc`

**Payload**: tenant_id, region, delta_pct, affected_mo_ids[], timestamp

**Consumer**: connector (audit + optional Odoo notification stub)

---

## Acceptance Tests

| ID | Test |
|----|------|
| AC-R2-01 | pATP returns TLC fields for seeded material |
| AC-R2-02 | +25% Region X flags 100% seeded affected MOs |
| AC-R2-03 | Substitute draft appears in connector queue |
| AC-R2-04 | Demo checkpoint 18 passes |
