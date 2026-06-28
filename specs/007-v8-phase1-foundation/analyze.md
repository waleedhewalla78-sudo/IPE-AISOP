# Analyze — 007 v8 Phase 1

**Date**: 2026-06-27

## Cross-artifact consistency

| Artifact | Coverage | Notes |
|----------|----------|-------|
| spec.md FR-V8-01..05 | plan.md, tasks.md | Aligned |
| SAP gap matrix U1–U3 | Partial parity MVP | Full Joule parity remains Phase 2+ |
| 006 hub routes | Planning Hub +2 tabs | Demand, Scenarios |
| ADR-001 Keycloak | Unchanged | JWT auth continues |
| dpe-svc demand.py | Unchanged paths | No breaking API |
| res-svc resolution | Complementary | Not duplicated |

## Module integrations

```
Planning Hub
  Demand tab ──► demand-svc:8040 ──► cdm_demand_line, cdm_demand_forecast, cdm_demand_signal
  Scenarios tab ──► scenario-svc:8050 ──► cdm_scenario*, cdm_scenario_parameter, cdm_scenario_result
  Resolution tab ──► res-svc (unchanged) ──► cdm_resolution_scenario

AI & Governance / Copilot ──► nlp-svc ──► cdm_copilot_session, orchestrator, Ollama tools
Control Tower / Schedule ──► fea-svc, cap-svc (unchanged)
```

## Gap vs SAP (post Phase 1)

| Capability | Before | After MVP |
|------------|--------|-----------|
| Role-based copilot | Single chat | 4 role agents + sessions |
| Demand sensing | None | SES forecasts + signal ingest |
| What-if workbench | Resolution only | Sandbox KPI simulation |
| Multi-echelon supply | None | Still Phase 2 |

## Risks

| Risk | Mitigation |
|------|------------|
| Migration 029 not applied | migrate service in compose |
| Kong route order | Specific sub-paths before dpe `/demand` |
| Empty demand history | Fallback synthetic history in sense cycle |
