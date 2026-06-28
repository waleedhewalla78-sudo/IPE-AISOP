# Plan — 007 v8 Phase 1

**Stack**: FastAPI 3.12, uv workspace, PostgreSQL CDM+RLS, Kong, React 18, Vite, Tailwind

## Architecture

```
Kong :8000
├── nlp-svc:8007     /api/v1/copilot/* (+ session, agents)
├── demand-svc:8040  /api/v1/demand/{forecast,sense,accuracy,signal/*}
├── scenario-svc:8050 /api/v1/scenario/*
└── dpe-svc:8001     /api/v1/demand/{classify,tariff,queue,...}  (unchanged)
```

## Migration 029

- `cdm_copilot_session`
- `cdm_demand_signal`, `cdm_demand_forecast`
- `cdm_scenario_parameter`, `cdm_scenario_result`
- ORM: `ipe_shared/models/v8_planning.py`

## Service scaffolds

| Service | Template | Port |
|---------|----------|------|
| demand-svc | rec-svc | 8040 |
| scenario-svc | rec-svc | 8050 |

## Frontend

| File | Purpose |
|------|---------|
| `DemandForecastPage.tsx` | Forecast UI |
| `ScenarioWorkbenchPage.tsx` | Scenario CRUD + simulate |
| `CopilotPanel.tsx` | Role switcher + session |
| `PlanningHub.tsx` | +Demand, +Scenarios tabs |

## Phases

1. Migration + shared models
2. demand-svc + scenario-svc + Kong/compose
3. nlp-svc role agents + sessions
4. Web UI + lazy routes
5. Tests + demo validation

## Non-goals

- copilot-svc microservice split
- Prophet dependency in container
- Kafka events for scenario lifecycle (Phase 1.1)
