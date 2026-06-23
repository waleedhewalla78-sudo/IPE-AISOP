# 05 — Event Architecture Verification (V2 Audit)

**Generated**: 2026-06-20 | **Methodology**: Code-level verification of every producer, consumer, topic, and schema.

## Event Infrastructure Status

| Component | Status | Evidence |
|-----------|--------|----------|
| Producer (KafkaProducer) | VERIFIED | `services/shared/ipe_shared/events/producer.py` |
| Consumer (KafkaConsumer) | VERIFIED | `services/shared/ipe_shared/events/consumer.py` |
| Schema Registry Client | VERIFIED | `services/shared/ipe_shared/events/schema_registry.py` |
| Avro Schemas (12 .avsc files) | VERIFIED | `services/shared/ipe_shared/events/schemas/` |
| DLQ Implementation | VERIFIED | consumer.py:30-40, 161-176 |
| Idempotency (Redis, 24h TTL) | VERIFIED | consumer.py:122-155 |
| Registered Avro Subjects | 12/12 | `scripts/register_schemas.py` |

## Topics Created via Scripts: 17/24

| Topic | Bash Script | Python Script | Status |
|-------|-------------|---------------|--------|
| ipe.demand.created | ✅ | — | CREATED |
| ipe.demand.classified | ✅ | — | CREATED |
| ipe.mo.material_scored | **MISSING** | **MISSING** | **NOT CREATED** |
| ipe.mo.capacity_scored | — | ✅ | CREATED |
| ipe.mo.feasibility_scored | ✅ | — | CREATED |
| ipe.supply.updated | ✅ | — | CREATED |
| ipe.supply.delay_detected | ✅ | — | CREATED |
| ipe.inventory.changed | ✅ | — | CREATED |
| ipe.workcenter.status_changed | ✅ | — | CREATED |
| ipe.operator.absence | ✅ | — | CREATED |
| ipe.delay.logged | ✅ | — | CREATED |
| ipe.resolution.proposed | ✅ | — | CREATED |
| ipe.resolution.approved | ✅ | — | CREATED |
| ipe.mo.auto_confirmed | ✅ | — | CREATED |
| ipe.reconciliation.completed | ✅ | — | CREATED |
| ipe.schedule.updated | **MISSING** | **MISSING** | **NOT CREATED** |
| ipe.disruption.detected | **MISSING** | **MISSING** | **NOT CREATED** |
| ipe.po.suggested | **MISSING** | **MISSING** | **NOT CREATED** |
| ipe.delay.classified | **MISSING** | **MISSING** | **NOT CREATED** |
| ipe.workcenter.bottleneck_detected | **MISSING** | **MISSING** | **NOT CREATED** |
| ipe.copilot.chat | **MISSING** | **MISSING** | **NOT CREATED** |
| ipe.copilot.queried | **MISSING** | **MISSING** | **NOT CREATED** |
| ipe.quality.event_created | **MISSING** | **MISSING** | **NOT CREATED** |
| ipe.quality.event_resolved | **MISSING** | **MISSING** | **NOT CREATED** |

## Complete Event Flow Map

### Primary Flow: Demand → Schedule → Resolution

```
Producer                Topic                        Consumer                Handler
connector/sync.py:98  → ipe.demand.created         → dpe-svc/consumers.py:11  → handle_demand_created
                       ipe.demand.created          → mat-svc/consumers.py:61  → handle_demand_created [DUPLICATE CONSUMPTION]
dpe-svc/handlers.py:95→ ipe.demand.classified      → mat-svc/consumers.py:16  → handle_demand_classified
(mat also emits)       ipe.demand.classified       → connector/consumers.py:37 → sync_demand_classification
mat-svc/consumers.py:38→ ipe.mo.material_scored    → fea-svc/consumers.py:11  → handle_material_scored
cap-svc/capacity.py:261→ ipe.mo.capacity_scored    → fea-svc/consumers.py:17  → handle_capacity_scored
fea-svc/handlers.py:74 → ipe.mo.feasibility_scored → res-svc/consumers.py:11  → handle_feasibility_scored
                       ipe.mo.feasibility_scored   → connector/consumers.py:25 → sync_feasibility
                       ipe.mo.feasibility_scored   → alert-svc/consumers.py:15 → **BROKEN (non-existent create_consumer)** 
res-svc/handlers.py:34 → ipe.resolution.proposed   → (no consumer)
res-svc/resolution.py  → ipe.resolution.approved   → connector/consumers.py:43 → handle_resolution_approved
```

### CRITICAL: Alert Service Consumer Broken

**File**: `services/alert-svc/app/events/consumers.py:15`
**Issue**: Calls `create_consumer()` — this function does NOT exist in the shared library.
**Evidence**: `ipe_shared/events/consumer.py` exports `KafkaConsumer` (class) and `start_consumers`/`stop_consumers`. No `create_consumer` function.
**Impact**: alert-svc consumer will crash at startup. Service won't process any events.

### DLQ Gaps

| Service | DLQ Topic Created? | Uses Shared Consumer? |
|---------|-------------------|----------------------|
| dpe-svc | ✅ | ✅ |
| mat-svc | ✅ | ✅ |
| cap-svc | ✅ | ✅ |
| fea-svc | ✅ | ✅ |
| res-svc | ✅ | ✅ |
| del-svc | ✅ | ✅ |
| nlp-svc | ✅ | ✅ |
| rec-svc | **MISSING** | ✅ |
| connector | **MISSING** | ✅ |
| alert-svc | **MISSING** | **BROKEN** |

### Avro Schema Gaps

8 producer calls use `send_avro()` but have NO `.avsc` file:
- `ipe.po.suggested` — mat-svc/material.py:384
- `ipe.reconciliation.completed` — rec-svc/handlers.py:58
- `ipe.quality.event_created` — del-svc/quality.py:124
- `ipe.quality.event_resolved` — del-svc/quality.py:202

These will silently fall back to JSON serialization — the schema registry won't validate.

## Summary

| Metric | Count |
|--------|-------|
| Total event flows mapped | 38 |
| VERIFIED_COMPLETE | 18 |
| PARTIALLY IMPLEMENTED (no topic creation) | 11 |
| IMPLEMENTED NOT INTEGRATED (broken consumer) | 1 |
| Topics without consumers | 4 (orphan topics) |
| Consumers without topics | 8 (topics not created) |
| Missing DLQ topics | 3 |
| Missing Avro schemas | 4 |
