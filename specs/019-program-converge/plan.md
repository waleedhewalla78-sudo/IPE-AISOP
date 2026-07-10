# Implementation Plan: 019-program-converge

**Branch**: `019-program-converge` (docs on `master`) | **Date**: 2026-07-10 | **Spec**: [spec.md](./spec.md)

## Summary

Close unblocked whole-project engineering gaps: add `mat-svc` to Release 2 compose, implement scenario promote API+UI, fix mock-odoo `stock.quant` fidelity, and keep Speckit/GitHub status honest for commercial blockers.

## Technical Context

**Language/Version**: Python 3.12, TypeScript/React (Vite)  
**Primary Dependencies**: FastAPI, SQLAlchemy async, Docker Compose, Kong, pytest, Vitest  
**Storage**: PostgreSQL 16 (CDM), Redis 7  
**Testing**: pytest (scenario-svc, mock-odoo), Vitest optional for UI smoke  
**Target Platform**: Windows host + Docker Desktop (PowerShell scripts)  
**Project Type**: Microservices monorepo (`ipe/`)  
**Performance Goals**: No new SLO; preserve R2 smoke/demo green  
**Constraints**: Do not destructively restart shared QA stack; AUTH_MODE=local for R2; no fake commercial closes  
**Scale/Scope**: 3 user stories + program hygiene; Wave 2/3 deferrals documented

## Constitution Check

| Gate | Status |
|------|--------|
| I Tenant isolation on promote | PASS — check tenant_id |
| II Auth on promote | PASS — require_roles planner/admin/manager |
| III Tests for behavioral change | PASS — API + mock tests |
| VII No unpaid scope creep | PASS — Wave 3 deferred |
| VIII No tag without evidence | PASS — tag HOLD |

## Project Structure

```text
specs/019-program-converge/
├── spec.md, clarify.md, analyze.md, plan.md
├── research.md, data-model.md, quickstart.md
├── contracts/promote-scenario.md
├── tasks.md, implement.md, converge.md, taskstoissues.md
└── checklists/requirements.md

infrastructure/docker/docker-compose.release2.yml  # +mat-svc
services/scenario-svc/app/api/v1/scenarios.py      # +promote
services/mock-odoo-api/app/main.py                 # +stock.quant samples
apps/web/src/features/hubs/planning/ScenarioWorkbenchPage.tsx
apps/web/src/locales/{en,ar}.json
```

## Phase 0 Research

See [research.md](./research.md) — decisions locked in clarify.md.

## Phase 1 Design

- [data-model.md](./data-model.md) — scenario status + stock.quant mapping  
- [contracts/promote-scenario.md](./contracts/promote-scenario.md)  
- [quickstart.md](./quickstart.md)

## Implementation Approach

1. Additive compose service for mat-svc (Kafka empty, AUTH_MODE=local).
2. Promote endpoint sets `PlanningScenario.status = "promoted"`; list includes promoted.
3. Workbench Promote button + i18n.
4. mock-odoo `_sample_quants()` wired into search_read.
5. Tests; Speckit logs; GH issues.

## Risks

| Risk | Mitigation |
|------|------------|
| Port conflict with QA agent | Config-first; no compose down |
| Promote semantics unclear | Clarify: mark preferred; does not mutate live schedule |
| stock.quant product match miss | Skip unmatched; return counts |
