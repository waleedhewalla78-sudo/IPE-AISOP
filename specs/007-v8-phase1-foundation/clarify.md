# Clarify — 007 v8 Phase 1

**Date**: 2026-06-27

## Decisions

| Topic | Proposal ambiguity | Decision |
|-------|-------------------|----------|
| copilot-svc vs nlp-svc | New service on 8030 | **Extend nlp-svc** for MVP; sessions in PostgreSQL |
| demand-svc vs dpe-svc | Extract all demand | **Split**: dpe keeps classify/tariff/queue; demand-svc owns forecast/sense/signal |
| scenario vs resolution | Both called "scenario" | **scenario-svc** = planning sandbox (`cdm_scenario*`); res-svc = MO mitigation |
| Forecast model | Prophet required day-1 | **SES v1** (exponential smoothing); upgrade path to Prophet in v8.1 |
| Redis sessions | Proposal mentions Redis | **PostgreSQL JSONB** for auditability + RLS |
| Role count | Unlimited personas | **4 agents** day-1: planner, manager, supervisor, executive |
| Kong path conflict | `/api/v1/demand` on dpe | **Sub-path routes** on demand-svc: `/forecast`, `/sense`, `/accuracy`, `/signal` |

## Open for Phase 2

- External signal connectors (POS, weather)
- Scenario promotion workflow to production plan
- Copilot rich response cards (embedded charts)
