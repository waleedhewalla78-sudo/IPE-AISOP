# Research — Spec 024

**Date**: 2026-07-15

## Decisions

### R1 — Pure-logic first for scorers
**Decision**: Implement predictive/root-cause/batch/auction as testable pure functions/classes with optional AsyncSession persist, mirroring existing `scorer.py` style.  
**Why**: Faster GREEN tests without Docker; matches Tech Spec intent.

### R2 — Absorb peer migrations
**Decision**: Treat 051–059 as source of truth; Speckit does not rewrite unless bug.  
**Why**: Constitution IX; concurrent Phase agents.

### R3 — supplier_score ALTER not CREATE
**Decision**: Keep 055 ALTER pattern vs Tech Spec CREATE.  
**Why**: Migration 041 already created table.

### R4 — upload-svc optional compose
**Decision**: Scaffold service directory acceptable; compose/Kong residual via converge.  
**Why**: Avoid destabilising Star Trans R1 package mid-COM hold.

### R5 — Phase 4/5 not stubbed as DONE
**Decision**: Document backlog only; no fake module shells claiming Premium complete.  
**Why**: Honesty rule VII.

## Alternatives rejected

| Idea | Rejected because |
|------|------------------|
| New feature per phase (024/025/026) immediately | User asked program slice OR Phase 3 first with analyze covering 4/5 — single 024 with FR-B* fits |
| Recreate all Tech Spec SQL verbatim | Conflicts with 041 and peer migrations |
| Full Planning Cockpit UI this run | Phase 5 scope; peers may already touch web UX |

## Open tech items (non-blocking)

- Persist hooks for auction/batch may use raw SQL until shared models land.
- Predict-all bulk endpoint deferred if single-MO predict + tests suffice for SC-001.
