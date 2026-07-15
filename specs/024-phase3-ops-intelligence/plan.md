# Implementation Plan — Spec 024 Ops Phase 3

**Branch**: `024-phase3-ops-intelligence` (work permitted on `master` per repo convention)  
**Date**: 2026-07-15  
**Constitution**: 1.3.0  
**Spec**: `ipe/specs/024-phase3-ops-intelligence/spec.md`  
**Sources**: Phase3 Blueprint/Tech Spec v2.0; Phase4 Premium; Phase5 Planning-Command-Deep

---

## Summary

Deliver Ops Blueprint Phase 3 application layer atop peer-landed migrations **051–059**: predictive risk + root-cause (fea-svc), exception APIs (dpe-svc), smart batch/auction (cap-svc), orchestrator activity logging (dpe-svc), upload scaffolding, and honest program docs. Phase 4/5 stay backlog. Absorb peer deltas; do not recreate schema.

---

## Technical Context

| Dimension | Choice |
|-----------|--------|
| **Language** | Python 3.11 (services); TypeScript/React (web — defer deep UI to P5/peers) |
| **API** | FastAPI + Pydantic v2 + `APIResponse` |
| **ORM / DB** | SQLAlchemy 2.0 async; Alembic **051–059** (verify); RLS |
| **Auth** | JWT + `require_roles` + `tenant_ctx` |
| **Tests** | pytest unit with stubs; no live Odoo/LLM required |
| **Compose** | R1/R2 unchanged unless upload-svc wired (residual OK) |
| **Target** | Eng-complete Ops P3 core scorers; upload/compose may be partial |

---

## Constitution Check

| Principle | Plan compliance |
|-----------|-----------------|
| I RLS | 051–059 include RLS / ALTER preserves |
| II Auth | New routes role-gated |
| III Tests | Unit tests for scorers/analyzers/batchers |
| IV Events | Orchestrator works without Kafka |
| V Layering | `core/` + `api/v1/` |
| VI Obs | Activity log + exceptions |
| VII Honesty | COM OPEN; no fake tags |
| VIII Gates | Do not reopen platform P3 without scripts |
| IX Ops program | Spec 024 active; P4/P5 backlog; absorb peers |

**Gate:** PASS

---

## Project Structure (touched)

```text
ipe/
├── migrations/versions/051_*.py … 059_*.py          # verify / absorb
├── services/fea-svc/app/core/predictive_scorer.py
├── services/fea-svc/app/core/root_cause_analyzer.py
├── services/fea-svc/app/api/v1/feasibility.py        # predict + root-cause routes
├── services/fea-svc/tests/test_predictive_scorer.py
├── services/fea-svc/tests/test_root_cause_analyzer.py
├── services/cap-svc/app/core/smart_batcher.py
├── services/cap-svc/app/core/capacity_auction.py
├── services/cap-svc/tests/test_smart_batcher.py
├── services/cap-svc/tests/test_capacity_auction.py
├── services/dpe-svc/app/core/agent_orchestrator.py
├── services/dpe-svc/app/api/v1/exceptions.py         # if missing
├── services/dpe-svc/tests/test_agent_orchestrator.py
├── services/upload-svc/                              # scaffold if missing
├── services/shared/ipe_shared/models/                # phase3 models as needed
├── PRODUCT-STATUS.md / AGENTS.md / CHANGELOG.md
├── .specify/memory/constitution.md                   # 1.3.0
└── specs/024-phase3-ops-intelligence/
```

---

## Implementation Approach

### A — Schema absorb
Verify linear 050→059; no new CREATE conflicting with 041/055 ALTER.

### B — Feasibility intelligence (US1/US2)
Implement predictive scorer + root cause analyzer + API routes + unit tests.

### C — Capacity intelligence (US3)
Smart batcher + capacity auction pure-logic + tests; optional DB persist hooks.

### D — Orchestration & exceptions (US2/US5)
Agent orchestrator stub chain + activity log helper; exception list/ack API if absent.

### E — Upload scaffold (US4)
Minimal upload-svc FastAPI + health + models hookup OR document residual.

### F — Docs & program (US6)
PRODUCT-STATUS, feature.json (root+ipe), AGENTS.md; Phase 4/5 backlog explicit.

### G — Do NOT implement this run
Phase 4 modules/agents A8–A12 full; Phase 5 Planning Cockpit/MPS/MRP; COM closes; force-push tags.

---

## Phase 0 Research

See `research.md`.

## Phase 1 Design

See `data-model.md`, `contracts/`, `quickstart.md`.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Peer agent race on same files | Re-read before write; smaller pure-logic modules |
| Schema without models | Add shared models only when needed by code |
| Scope explosion into P4/P5 | Hard backlog FR-B*; converge only |
| Docker validate #70/#72 | Remain OPEN if stack down |
