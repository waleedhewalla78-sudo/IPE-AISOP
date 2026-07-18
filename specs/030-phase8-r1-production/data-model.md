# Data Model — Spec 030

## cdm_write_back_log (migration 070)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | gen_random_uuid |
| tenant_id | UUID FK → cdm_tenant | RLS key |
| entity_type | VARCHAR(64) | e.g. mrp.production |
| entity_id | VARCHAR(128) | MO / PO id |
| field_name | VARCHAR(128) | nullable |
| old_value / new_value | TEXT | proposed change |
| action | VARCHAR(64) | default update |
| status | VARCHAR(32) | dry_run / pending_approval / executed / failed / rolled_back |
| dry_run | BOOLEAN | default true |
| approved_by / requested_by | VARCHAR(128) | |
| financial_impact | FLOAT | role gate input |
| error_message | TEXT | |
| attempt_count | INT | max 3 (8B live path) |
| payload | JSONB | |
| is_live | BOOLEAN | default false |
| created_at / executed_at | TIMESTAMPTZ | |
| rollback_deadline | TIMESTAMPTZ | 4h window (spec rule) |

**RLS:** `tenant_isolation` policy on `tenant_id` vs `app.current_tenant_id`.

## Prior migrations (absorbed, not recreated)

- 068 RLS coverage gaps (Spec 029)
- 069 cdm_mps_mrp_runs (Spec 029)
- 067 cdm_andon_alert (Spec 028/029 dual-write)
