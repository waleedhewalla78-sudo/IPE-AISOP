---
status: CLOSED
closed_by: foundation
date: 2026-07-11
superseded_for_aug18_demo: specs/040-startrans-demo-aug18
---
# Feature Specification: Star Trans Client Demo (Today)

**Feature Branch**: `012-startrans-client-demo`  
**Created**: 2026-06-29  
**Status**: Implementing  
**Client**: Star Trans — Electrical Transformer Technology  
**Audience**: Ops planners + C-suite · 60 minutes · live Copilot · local laptop

---

## Goal

Deliver a **demo-ready Star Trans–themed dataset** on the existing IPE v8.2.0 platform (32/32 checkpoints) without waiting for ERP/SSO integrations. Data must be **consistent across screens** so live Copilot queries resolve correctly.

## In Scope

| ID | Deliverable |
|----|-------------|
| FR-ST-01 | SQL overlay renames tenant, products, MOs, work centers, suppliers, plants to transformer industry |
| FR-ST-02 | `seed-startrans-demo.ps1` — one command after base seed |
| FR-ST-03 | `prepare-startrans-demo.ps1` — stack + seed + validation |
| FR-ST-04 | `run-full-demo.ps1 -Profile startrans` — 32/32 with Star Trans assertions |
| FR-ST-05 | Presenter guide + Copilot cheat sheet + Excel workbook schema |
| FR-ST-06 | Sample project-plan CSV for live Schedule upload (MO-ST-001) |

## Out of Scope (POST-demo)

- Multi-sheet Excel importer UI on every hub
- Live SAP/D365/Keycloak
- New tenant UUID (reuse demo tenant for stability)
- Copilot model fine-tuning

## Success Criteria

- [ ] `prepare-startrans-demo.ps1` completes with 32/32 PASS
- [ ] Copilot answers 3 scripted queries using Star Trans MO/product names
- [ ] Schedule Excel upload accepts `PLAN-STARTRANS-W12` referencing MO-ST-001
- [ ] Presenter can run 60-min arc from `docs/demo-data/STARTRANS-DEMO-GUIDE.md`

---

## Demo Arc (60 min)

| Min | Module | Hero data |
|-----|--------|-----------|
| 0–5 | Login + framing | Star Trans tenant |
| 5–15 | Control Tower + Resolution | MO-ST-001 copper delay, MO-ST-007 CRGO shortage |
| 15–25 | Schedule + Excel upload | PLAN-STARTRANS-W12 |
| 25–35 | Demand + Scenario + Supply | 4-plant network, sense cycle |
| 35–42 | Copilot live | 3 scripted queries |
| 42–50 | Executive + War Room | Delay breakdown |
| 50–55 | Sustain + Quality | ESG + FPY |
| 55–60 | Close | Shadow mode + integration roadmap |
