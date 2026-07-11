---
status: CLOSED
closed_by: foundation
date: 2026-07-11
---
# Feature Specification: IPE v8.2.0 Phase 3 Design & Procurement

**Feature Branch**: `009-v8-phase3-design-procurement`  
**Created**: 2026-06-24  
**Status**: Implemented (MVP)  
**Input**: SAP Gap Analysis Phase 3 — U7, U8

---

## What We Build

| Stream | Deliverable | Service | Port |
|--------|-------------|---------|------|
| **U7** | Product Design AI — material catalog, recommendations, process compliance | `material-svc` | 8090 |
| **U8** | Responsible Procurement — supplier ESG/risk, spend, compliance checks | `procurement-svc` | 8100 |

### UI

- **AI & Governance Hub**: Design AI tab
- **Supply Chain Hub**: Procurement tab

---

## Requirements

### FR-P3-01 Material intelligence
Expose engineering material catalog; rank alternatives by strength/cost/sustainability; check design rules per process.

### FR-P3-02 Responsible procurement
List suppliers with ESG and risk scores; aggregate spend by category/period; run compliance rule checks and persist results.

### FR-P3-03 Integration
Reuse `cdm_supplier`, `cdm_material_attributes`; extend supplier with ESG/risk columns (migration 031).

---

## User Stories

| ID | Story | Acceptance |
|----|-------|------------|
| US-P3-1 | Engineer requests material recommendation | Ranked list with scores returned |
| US-P3-2 | Engineer validates machining parameters | Compliance pass/fail per rule |
| US-P3-3 | Procurement views supplier risk | ESG, tier, composite score shown |
| US-P3-4 | Procurement runs compliance audit | Checks persisted; overall status returned |

---

## Out of Scope

- CAD/PLM integration
- Full supplier onboarding workflow
- Real-time ESG data feeds (Phase 3.1)
