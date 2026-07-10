# Spec 020 — Planning Intelligence (SAP IBP Gap Closure)

**Version:** 1.0  
**Target:** v9.2.0 (R2 modules) → v10.0.0 (S&OP engine)  
**Authority:** `docs/planning/IPE-PLANNING-INTELLIGENCE-TECHNICAL-SPEC.md`  
**Gap source:** `docs/planning/IPE-SAP-IBP-GAP-ANALYSIS.md`  
**Prompts:** `docs/planning/IPE-PLANNING-CURSOR-PROMPTS.md`

## Goal

Deliver the 20% of SAP IBP capabilities that provide 80% of value for MENA mid-market discrete manufacturers — as IPE-native modules (not SAP connectors; SAP B1 CUT in R2).

## In-scope modules

| ID | Module | Service | Migration |
|----|--------|---------|-----------|
| B | ABC/XYZ Segmentation | mat-svc | 044 |
| A | Forecast Quality (MAPE/Bias/MASE/Stability) | demand-svc | 045 |
| D | ARIMA/SARIMA + best-fit | demand-svc | — |
| Odoo | Lead time + product cost/price sync | connector | 046 |
| C | Statistical Safety Stock | mat-svc | 047 |
| E | Capacity Utilisation Alerts | cap-svc | 048 |
| F | S&OP Process Engine | sop-svc (:8110) NEW | 049 |
| Copilot | Planning intelligence tools | nlp-svc | — |
| Infra | Docker Compose + Kong routes | infrastructure/docker | — |

## Out of scope / deferred

- Full SAPIBP1 key-figure taxonomy (200+ KFs) — use ~45 KF registry overlay
- Multi-stage inventory optimisation (R4)
- Gradient boosting / XGBoost forecasting (P2)
- Live customer Odoo — protocol-compatible stand-ins when unavailable; document honestly

## Acceptance

1. Migrations 044–049 apply cleanly on head `042`
2. Unit tests green for each module’s known-value cases
3. Kong routes expose new APIs under `/api/v1/{material,demand,capacity,sop}`
4. Copilot registers ≥9 planning tools
5. Finalize report at `docs/qa/PLANNING-INTELLIGENCE-FINALIZE-REPORT.md`
