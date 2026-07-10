# Sprint S12 — SAP Business One connector (CUT)

**Feature**: `018-phase2-release2`  
**Date**: 2026-07-10  
**Status**: **DEFERRED / CUT**  
**Authority**: Spec 017 §5 (Strategy Assessment), `docs/PHASE2-SPRINT-PLAN.md`

## Decision

SAP B1 ERP connector work (S12-ALL) is **out of scope** for Release 2 (`v9.1.0-r2`). Odoo remains the integrated ERP path for Star Trans UAT and Phase 2 demos.

## Rationale

1. **Spec 017** explicitly cuts SAP B1 in favor of Odoo self-service and Wave 1 bridge capacity.
2. **Commercial sequencing**: Phase 1 Star Trans UAT blocked on commercial items unrelated to SAP scaffold.
3. **Risk**: SAP DI-API / Service Layer certification and tenant credential handling exceed R2 timeline.
4. **Gate focus**: Program energy directed to G-R2-01–G-R2-05 (compose, Copilot, Odoo v2, Arabic, demo).

## Deferred backlog (if revived)

| ID | Item | Notes |
|----|------|-------|
| S12-01 | B1 Service Layer auth scaffold | Reuse `connector` pattern |
| S12-02 | Chart of accounts sync | Behind feature flag |
| S12-03 | Inventory document mapping | Depends on CDM item master |
| S12-04 | Helm `values` ERP profile | Not for kind dev |

## Evidence

- Tasks marked CUT: `specs/018-phase2-release2/tasks.md` (Sprint S12)
- Gate matrix: `specs/018-phase2-release2/GATES.md` (no SAP gate)
- Implement rollup: `specs/018-phase2-release2/IMPLEMENT-LOG.md`

## Revisit trigger

- Post `v9.1.0-r2` tag and green G-R2-03 Wave 1, product may open **Spec 019** for optional SAP under enterprise tier (out of current constitution scope).
