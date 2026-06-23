# 06 — Database Verification (V2 Audit)

**Generated**: 2026-06-20 | **Methodology**: Cross-referenced all 12 migration files against model schemas and RLS policies.

## Migration Chain

```
001 → 002 → 003 → 004 → 005 → 006 → 007 → 008 → 009 → 010 → 011 → 012
```

| Check | Result |
|-------|--------|
| All have `upgrade()` + `downgrade()` | PASS (12/12) |
| Revision chain valid | PASS |
| alembic.ini configured | PASS |
| env.py uses `IPE_DATABASE_URL_SYNC` | PASS |

## Database Growth

| Migration | New Tables | Total Tables | RLS Coverage |
|-----------|-----------|--------------|--------------|
| 001 | 19 | 19 | 19/19 (dynamic loop) |
| 002 | 1 | 20 | 19/20 |
| 003 | 3 | 23 | 19/23 |
| 004 | 2 | 25 | 19/25 |
| 005 | 5 | 30 | 19/30 |
| 006 | 4 | 34 | 19/34 |
| 007 | 0 (cols only) | 34 | 19/34 |
| 008 | 3 | 37 | 19/37 |
| 009 | 1 | 38 | 19/38 |
| 010 | 3 | 41 | 19/41 |
| 011 | 1 | 42 | 19/42 |
| 012 | 4 | 46 | 19/46 |

## RLS Coverage: 19/46 tables (41%)

### Tables WITH RLS (migration 001 dynamic loop)

cdm_tenant, cdm_user, cdm_product, cdm_bill_of_material, cdm_bom_line, cdm_work_center, cdm_routing_operation, cdm_supplier, cdm_supply_order, cdm_operator, cdm_manufacturing_order, cdm_demand_line, cdm_work_order, cdm_inventory_position, cdm_delay_event, cdm_resolution_scenario, cdm_mdr_score, cdm_export_queue, cdm_audit_log

### Tables WITH tenant_id but WITHOUT RLS (27 tables)

| Migration | Tables |
|-----------|--------|
| 002 | cdm_model_registry |
| 003 | cdm_customer, cdm_resource_calendar |
| 004 | cdm_disruption_event, cdm_duration_prediction |
| 005 | cdm_scenario, cdm_delay_root_cause |
| 006 | cdm_skill, cdm_worker, cdm_shift |
| 008 | cdm_plant, cdm_transfer_route, cdm_transport_fleet |
| 009 | cdm_quality_event |
| 010 | cdm_emission_factor, cdm_material_carbon, cdm_transport_emission |
| 011 | cdm_financial_projection |
| 012 | cdm_edge_gateway, cdm_edge_sync_batch, cdm_edge_sync_record, cdm_edge_schedule_delta |

### NOTE: cdm_tenant RLS is self-defeating

The tenant table has `tenant_isolation` POLICY filtering on its own `tenant_id` column. This means `SELECT * FROM cdm_tenant` while `SET app.current_tenant_id` is active will return 0 rows (each tenant filtered by its own ID, which for the tenant table itself is semantically meaningless).

## Seed Data Script Validation

| Script | Broken References |
|--------|------------------|
| seed-data.sh | `cdm_user.password_hash` (column does NOT exist), `cdm_user.full_name` (column does NOT exist), `cdm_location` (table does NOT exist) |
| seed_dev_data.py | OK — all columns exist |
| seed_sprint2_data.py | OK — but `ON CONFLICT DO NOTHING` has no unique constraint |

## Orphan Analysis

| Type | Count | Details |
|------|-------|---------|
| Tables WITHOUT Pydantic schemas | 31 | No API contract defined |
| Pydantic schemas WITHOUT tables | 0 | All schemas have matching tables |
| Tables NEVER accessed in application code | ~10 | cdm_mdr_score, cdm_export_queue, etc. (RARE usage) |

## Critical Findings

| # | Severity | Finding |
|---|----------|---------|
| DB-01 | **CRITICAL** | 22 tables with tenant_id have NO RLS — multi-tenant isolation broken |
| DB-02 | **CRITICAL** | seed-data.sh references non-existent columns + tables — will fail |
| DB-03 | **HIGH** | cdm_tenant RLS is self-referencing — tenant table queries fail under RLS |
| DB-04 | **HIGH** | cdm_model_registry (AI models) has NO RLS — models exposed across tenants |
| DB-05 | **MED** | cdm_financial_projection has NO RLS — financial data exposed across tenants |
| DB-06 | **MED** | cdm_edge_gateway has NO RLS — edge device API keys exposed across tenants |
