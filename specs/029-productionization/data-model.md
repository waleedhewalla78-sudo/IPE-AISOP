# Data Model — Spec 029

## Existing (wired)
- `cdm_andon_alert` (067) — Andon dual-write target
- `cdm_sop_stage_gate` / `cdm_sop_cycle` — stage-gate conceptual store (scaffold may use in-memory first)

## New (069)
### cdm_mps_run
- id UUID PK
- tenant_id UUID NOT NULL
- product_id TEXT/UUID
- run_payload JSONB NOT NULL
- created_at timestamptz

### cdm_mrp_run
- id UUID PK
- tenant_id UUID NOT NULL
- root_product_id TEXT/UUID
- run_payload JSONB NOT NULL
- created_at timestamptz

Both: RLS tenant_isolation + index (tenant_id, created_at).
