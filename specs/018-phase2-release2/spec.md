# Feature Specification: IPE Phase 2 — Release 2 (018)

**Feature**: `018-phase2-release2`  
**Version**: 1.1  
**Date**: 2026-07-10  
**Status**: **IN_PROGRESS** — R2 scaffold complete; Wave 1 bridge 25%; Kind stable; compose smoke pending  
**Target tag**: `v9.1.0-r2`  
**Authority**: `docs/PHASE2-IMPLEMENTATION-GUIDE.md` (reconciled)  
**Depends on**: Spec 017 Phase 0 ✓, Wave 1 partial (25%)

---

## Vision

Deliver **Release 2** (`release2` profile): R1 manufacturing stack plus **Copilot live data**, **demand sensing**, **scenario workbench**, **OTD analytics**, **Odoo admin self-service**, **Arabic 8+ screens**, and **multi-tenant ops** — without SAP B1 (cut per Spec 017).

---

## Scope

| In scope | Out of scope |
|----------|--------------|
| R2 compose (nlp, demand, scenario) | SAP B1 connector (Sprint 12 CUT) |
| Copilot planning tools + shadow mode | Full Prophet/LSTM demand (SES first) |
| Scenario simulate/compare | Enterprise K8s sales tier |
| OTD trend/root-cause/cost | NEXUS Social |
| Odoo Config v2 UI | Gate 11 14/14 on kind (#27 WON'T FIX) |
| Arabic 8+ screens | |

---

## Program gates (2026-07-10)

See **`GATES.md`** for PASS/FAIL evidence paths.

| Gate | Summary | Status |
|------|---------|--------|
| G-R2-01 | release2-smoke | FAIL (compose down) |
| G-R2-02 | Copilot S2 | PASS |
| G-R2-03 | Wave 1 W1-03–08 | IN_PROGRESS |
| G-R2-04 | Arabic QA | PASS |
| G-R2-05 | run-release2-demo + Kind | PASS (partial) |

**Kind cluster**: 8/8 pods Ready after `docs/qa/kind-restabilize-2026-07-10.txt` remediation.

---

## Sprint summary

| Sprint | Focus | Status |
|--------|-------|--------|
| W1 bridge | Odoo v2 + OTD (Spec 017) | 🔄 25% |
| S1 | R2 infrastructure | ✅ |
| S2 | Copilot live data | ✅ partial (W1-02 smoke) |
| S3–S4 | Demand + Scenarios | ✅ |
| S5 | Arabic | ✅ |
| S6–S7 | OTD extended + Odoo polish | ✅ |
| S8–S11 | Ops, intel, S&OP | ✅ |
| S12 | SAP B1 | **CUT** (`sprints/S12-CUT.md`) |

Full backlog: `tasks.md` · Reconciliation: `docs/PHASE2-SPRINT-PLAN.md`  
Master rollup: **`IMPLEMENT-LOG.md`**

---

*Spec v1.1 — Phase 2 status after 2026-07-10 ops cutover*
