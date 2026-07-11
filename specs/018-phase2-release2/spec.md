---
status: CLOSED
closed_by: v9.1.1-r2
date: 2026-07-11
---

# Feature Specification: IPE Phase 2 — Release 2 (018)

**Feature**: `018-phase2-release2`  
**Version**: 1.2  
**Date**: 2026-07-10  
**Status**: **FINALIZE** — engineering gates green; G-R2-04 native Arabic sign-off human-open; tag Option B `v9.1.1-r2`  
**Target tag**: `v9.1.1-r2` (prior local `v9.1.0-r2` retained; see `TAG-DECISION.md`)  
**Authority**: `docs/PHASE2-IMPLEMENTATION-GUIDE.md` (reconciled)  
**Depends on**: Spec 017 Phase 0 ✓, Wave 1 engineering ✓ (commercial PH1 open)

---

## Vision

Deliver **Release 2** (`release2` profile): R1 manufacturing stack plus **Copilot live data**, **demand sensing**, **scenario workbench**, **OTD analytics**, **Odoo admin self-service**, **Arabic 8+ screens**, and **multi-tenant ops** — without SAP B1 (cut per Spec 017).

---

## Scope

| In scope | Out of scope |
|----------|--------------|
| R2 compose (nlp, demand, scenario, mat-svc) | SAP B1 connector (Sprint 12 CUT) |
| Copilot planning tools + shadow mode | Full Prophet/LSTM demand (SES first) |
| Scenario simulate/compare/promote | Enterprise K8s sales tier |
| OTD trend/root-cause/cost | NEXUS Social |
| Odoo Config v2 UI | Gate 11 14/14 on kind (#27 WON'T FIX) |
| Arabic 8+ screens (eng) | Wave 3 NL + supplier comms (#43–#46) |

---

## Program gates (2026-07-10) — synced with `GATES.md`

| Gate | Summary | Status |
|------|---------|--------|
| G-R2-01 | release2-smoke | **PASS** 15/15 |
| G-R2-02 | Copilot S2 | **PASS** |
| G-R2-03 | Wave 1 W1-03–08 | **PASS** (engineering; live Odoo = PH1-02) |
| G-R2-04 | Arabic QA | **PASS (engineering)** · native sign-off ⬜ |
| G-R2-05 | run-release2-demo + Kind | **PASS** 7/7 |
| G-R2-TAG | `v9.1.1-r2` | **HOLD** until G-R2-04 human (Option B) |

**Kind cluster**: 8/8 pods Ready after `docs/qa/kind-restabilize-2026-07-10.txt` remediation.

---

## Sprint summary

| Sprint | Focus | Status |
|--------|-------|--------|
| W1 bridge | Odoo v2 + OTD (Spec 017) | ✅ eng |
| S1 | R2 infrastructure | ✅ |
| S2 | Copilot live data | ✅ |
| S3–S4 | Demand + Scenarios (+ promote) | ✅ |
| S5 | Arabic | ✅ eng / human open |
| S6–S7 | OTD extended + Odoo polish | ✅ |
| S8–S11 | Ops, intel, S&OP | ✅ |
| S12 | SAP B1 | **CUT** (`sprints/S12-CUT.md`) |

Full backlog: `tasks.md` · Reconciliation: `docs/PHASE2-SPRINT-PLAN.md`  
Master rollup: **`IMPLEMENT-LOG.md`** · Open inventory: **`OPEN-ITEMS-PROJECT.md`** · Tag: **`TAG-DECISION.md`**

---

*Spec v1.2 — FINALIZE status after 2026-07-10 R2 closure pass*
