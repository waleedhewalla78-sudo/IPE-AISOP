# Data Model — Spec 024 (Ops Phase 3)

**Migrations**: 051–059 (peer-absorbed). All tenant tables MUST have RLS.

| Table | Migration | Purpose | Keys / notes |
|-------|-----------|---------|--------------|
| `cdm_agent_activity_log` | 051 | Agent run audit | (tenant_id, agent_id, created_at) |
| `cdm_exception_sla` | 052 | Ack/resolve SLA by severity | uq (tenant_id, severity) |
| `cdm_agent_exception` | 052 | Exception lifecycle | status open→acked→resolved; no auto-close |
| `cdm_upload_history` | 053 | Upload jobs | wizard_phase, counts |
| `cdm_upload_error` | 053 | Row-level errors | FK history |
| `cdm_demand_signal` | 054 | Fused demand | confidence_label |
| `cdm_supplier_score` | 041+**055 ALTER** | Reliability + P3 cols | overall_score, recommendation, … |
| `cdm_root_cause_chain` | 056 | 5-why JSON chain | chain_data JSONB |
| `cdm_prediction_log` | 057 | Horizon snapshots | horizon_days 3/7/14 |
| `cdm_capacity_auction_log` | 058 | Auction decisions | winner/loser scores |
| `cdm_batch_group` | 059 | Smart batch results | savings_min/pct |

## Entity relationships (logical)

```
ManufacturingOrder 1──* PredictionLog
ManufacturingOrder 1──* RootCauseChain
RootCauseChain 0..1──* AgentException
Tenant 1──* AgentActivityLog
Tenant 1──* UploadHistory 1──* UploadError
Supplier 1──* SupplierScore
WorkCenter 1──* CapacityAuctionLog / BatchGroup
```

## Shared ORM

- Extend/create models only when application code needs them.
- Existing `SupplierScore` model SHOULD gain Phase 3 columns when mat-svc writes them.
