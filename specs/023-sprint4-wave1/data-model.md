# Data Model — Spec 023

## cdm_erp_connection (migration 050)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | gen_random_uuid() |
| tenant_id | UUID FK cdm_tenant | RLS |
| erp_type | varchar(20) | default `odoo` |
| display_name | varchar(100) | |
| host_url | varchar(500) | |
| database_name | varchar(100) | |
| username | varchar(100) | |
| password_encrypted | text | Fernet ciphertext |
| api_protocol | varchar(20) | default xmlrpc |
| is_active | bool | |
| is_production | bool | |
| last_test_at / result / message | timestamptz / str / text | |
| sync_interval_seconds | int | default 900 |
| sync_enabled | bool | |
| created_at / updated_at | timestamptz | |
| created_by | UUID nullable | |

**Indexes:** tenant; partial unique active `(tenant_id, erp_type) WHERE is_active`.

**RLS:** `tenant_id = current_setting('app.current_tenant_id')::uuid`

## cdm_erp_connection_log (migration 050)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID | RLS |
| connection_id | UUID FK | ON DELETE CASCADE |
| action | varchar(50) | create/update/test/activate/sync/delete |
| result | varchar(20) | |
| details | JSONB | no passwords |
| performed_by | UUID nullable | |
| created_at | timestamptz | |

## cdm_otd_snapshot (migration 039 — existing)

Daily OTD metrics per tenant; used by `OTDAggregator` / dashboard. No schema change required unless gaps found in converge.
