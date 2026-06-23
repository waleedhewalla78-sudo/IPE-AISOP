# 09 — Critical Business Flow Analysis (V2 Audit)

**Generated**: 2026-06-20 | **Methodology**: Traced end-to-end business flows through all service layers.

## Flow 1: Core APS Pipeline (Demand → Schedule → Resolution)

```
Step 1: Odoo ERP → Connector (sync.py:98) → Kafka ipe.demand.created
Step 2: dpe-svc consumer → handle_demand_created → priority scoring → Kafka ipe.demand.classified
Step 3: mat-svc consumer → probabilistic ATP → Kafka ipe.mo.material_scored
Step 4: cap-svc API → solve_schedule (OR-Tools CP-SAT) → Kafka ipe.mo.capacity_scored  
Step 5: fea-svc dual-gate → feasibility scoring → Kafka ipe.mo.feasibility_scored
Step 6: res-svc consumer → generate_strategies → Kafka ipe.resolution.proposed
Step 7: Planner approves → res-svc /approve → Kafka ipe.resolution.approved
Step 8: connector consumer → export to Odoo
```

| Step | Status | Issues |
|------|--------|--------|
| 1. ERP Integration | VERIFIED (HMAC) | Requires Odoo XML-RPC connectivity |
| 2. Priority Scoring | VERIFIED | Uses DB-backed tenant config |
| 3. Material ATP | VERIFIED | `check-availability` endpoint previously broken, now fixed |
| 4. Capacity Schedule | VERIFIED | OR-Tools solver with 30s timeout |
| 5. Feasibility Score | VERIFIED | G1-G5 gates all functional |
| 6. Resolution Generation | VERIFIED | 8 constraint types, business scoring |
| 7. Planner Approval | VERIFIED | Optimistic locking on `version` column |
| 8. Odoo Export | VERIFIED | 3 retries, HMAC signed |

**Flow Status**: VERIFIED_COMPLETE for Steps 1-8

**Failure Points Identified**:
- Step 4: Solver timeout (30s) → returns partial schedule → downstream scores may be inaccurate
- Step 5: Kafka hardcoded "ok" in readiness → if Kafka is down, fea-svc still reports healthy
- Step 8: Odoo unreachable → export queue persists with 3 retry cap → manual intervention required

## Flow 2: Copilot Query

```
1. User types query in CopilotPanel
2. POST /api/v1/copilot/query → nlp-svc
3. _classify_intent() → 7 categories
4. route_query() → service routing hints
5. Optional: SSE streaming response
6. Kafka ipe.copilot.queried (audit)
```

| Step | Status | Issues |
|------|--------|--------|
| 1. UI Input | VERIFIED | |
| 2. API Route | VERIFIED | RBAC enforced (require_roles) |
| 3. Intent Classification | VERIFIED | LLM-based with fallback |
| 4. Service Routing | PARTIALLY | Hints only — no real downstream API calls |
| 5. SSE Streaming | **MOCKED** | `_mock_llm_response()` with word-split, not real Anthropic |
| 6. Audit Event | **BROKEN** | `ipe.copilot.queried` topic NOT CREATED |

**Flow Status**: PARTIALLY IMPLEMENTED

## Flow 3: Alert Lifecycle

```
1. Kafka event received by alert-svc consumer
2. evaluate_event() → match rules
3. Create alert in _alert_store
4. Optionally notify via SMTP
5. Frontend polls /api/v1/alerts
6. Planner acknowledges via POST /alerts/{id}/acknowledge
```

| Step | Status | Issues |
|------|--------|--------|
| 1-4. Event→Alert | **BROKEN** | alert-svc consumer uses non-existent `create_consumer()` |
| 5. Frontend Poll | VERIFIED | Correct API call to alert-svc |
| 6. Acknowledge | **INSECURE** | No authentication at all on acknowledge endpoint |

**Flow Status**: IMPLEMENTED_NOT_INTEGRATED

## Flow 4: Quality Event

```
1. Quality event detected → POST /api/v1/quality/events
2. process_quality_event() → severity + rework + escalation
3. Kafka ipe.quality.event_created
4. Optional: POST /api/v1/quality/resolve
5. Kafka ipe.quality.event_resolved
```

| Step | Status | Issues |
|------|--------|--------|
| 1. API | VERIFIED | No RBAC |
| 2. Processing | VERIFIED | severity/rerouting/escalation all functional |
| 3-5. Events | **BROKEN** | Both quality topics NOT CREATED, no schemas |

**Flow Status**: IMPLEMENTED_NOT_INTEGRATED

## Flow 5: Network Optimization (Multi-Plant)

```
1. POST /api/v1/capacity/network-optimize
2. solve_network_optimization() → CP-SAT make-vs-transfer
3. Returns plant assignments + transfer costs
```

| Step | Status | Issues |
|------|--------|--------|
| 1. API | VERIFIED | RBAC enforced |
| 2. Solver | VERIFIED | Functional code in network_optimizer.py |
| 3. Persistence | **MISSING** | No DB write, no Kafka event, no audit log |

**Flow Status**: PARTIALLY IMPLEMENTED

## Overall Flow Assessment

| Flow | Status | Production Ready? |
|------|--------|-------------------|
| Core APS Pipeline | VERIFIED_COMPLETE | Yes (with solver timeout caveat) |
| Copilot Query | PARTIALLY IMPLEMENTED | No (mocked SSE, missing audit topics) |
| Alert Lifecycle | IMPLEMENTED_NOT_INTEGRATED | No (broken consumer, no auth) |
| Quality Events | IMPLEMENTED_NOT_INTEGRATED | No (topics not created) |
| Network Optimization | PARTIALLY IMPLEMENTED | No (no persistence layer) |
