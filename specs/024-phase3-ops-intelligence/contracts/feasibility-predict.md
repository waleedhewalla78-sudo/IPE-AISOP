# Contracts — Feasibility Predictive & Root Cause

## GET `/api/v1/feasibility/predict/{mo_id}`

**Auth**: planner | manager | admin | auditor  
**Tenant**: required

**200 Response `data`**:
```json
{
  "mo_id": "uuid",
  "current": { "score": 72.5, "color": "amber", "gates": {} },
  "predictions": {
    "3": { "score": 65.0, "color": "amber", "primary_risk": "material", "risk_driver": "..." },
    "7": { "score": 48.0, "color": "red", "primary_risk": "material", "risk_driver": "..." },
    "14": { "score": 40.0, "color": "red", "primary_risk": "capacity", "risk_driver": "..." }
  },
  "trend": "deteriorating",
  "recommended_action": "Act within 2 days to prevent material gate failure"
}
```

## GET `/api/v1/feasibility/root-cause/{mo_id}`

**200 Response `data`**:
```json
{
  "mo_id": "uuid",
  "chain_depth": 3,
  "levels": [
    { "level": 1, "cause_type": "capacity_overload", "description": "..." }
  ],
  "root_cause_type": "systemic_supplier_issue",
  "recommendations": [
    { "timeframe": "immediate", "action": "...", "cost_estimate": 0 }
  ]
}
```

## POST `/api/v1/exceptions/{id}/acknowledge`

**Auth**: planner | manager | admin  
Sets `acknowledged_at`; does not resolve.

## Orchestrator (internal)

`AgentOrchestrator.run_chain(tenant_id, trigger, changed_data) -> ChainResult`  
Persists activity log entries; never raises away the whole chain on single-step timeout.
