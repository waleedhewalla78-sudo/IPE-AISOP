# Clarifications — Spec 040 Star Trans Demo Aug 18

**Date:** 2026-08-14  
**Method:** Full analysis of sprint prompt + real `IPE_Data_Template_StarTrans_v1.xlsx` + codebase STREAM commits  

---

## Decisions (resolved)

| # | Ambiguity | Decision | Rationale |
|---|-----------|----------|-----------|
| C1 | Sheet naming vs early sprint invent (`00_README`, `01_Products`…) | **Use real template names** (`README`, `01_Plants`, `04_Products`, `12_ManufacturingOrders`, …) | Customer email + Downloads workbook are source of truth |
| C2 | Header/data rows | **Header row 4, data from row 5** | Matches workbook legend layout |
| C3 | 16 CDM entities vs 24 sheets | Ingest **priority + mapped sheets** into simplified `demo_*`; line sheets (06b, 07b, …) may preview without full upsert | Demo timebox; FR-040 NFR skip RLS |
| C4 | `/home` vs `/workspace` | Both render role-aware UnifiedWorkspace; `/home` is primary demo URL | Sprint FR; legacy redirect preserved |
| C5 | Gantt library | **frappe-gantt MIT** (not dhtmlx, not custom SVG) | License + 5-day risk |
| C6 | Role model | Demo roles executive/planner/supervisor/buyer via **localStorage override**; JWT unchanged | Demo switcher ≠ authz |
| C7 | Excel commit target | `demo_*` tables via upload-svc — **not** claim full CDM/RLS production path | Honesty / constitution VII |
| C8 | If customer file late | Seed script + template sample rows are backup | US-1 |
| C9 | AI Autonomy tile | Copilot actions today (or hide) | STREAM-1.5 |
| C10 | Spec numbering | New Spec **040** overlays CLOSED 012; feature.json points here for this cycle | Avoid reopening 012 |

## Still OPEN (human / ops — not eng-fakeable)

| # | Item | Owner | Notes |
|---|------|-------|-------|
| O1 | Customer returns filled workbook by Sunday EOD | Star Trans | Email ready |
| O2 | Warm R2 walkthrough PASS + screenshots | Diligent eng | STREAM-7 checklist open boxes |
| O3 | G-R2-04 Arabic QA | Human COM | Never invent PASS |
| O4 | PH1-02 live Odoo | Customer IT + Diligent | MOCK/dry-run only |
| O5 | OQ-7 pricing / SOW | Commercial | Blocks SOW send |

## Underspec → defaults applied

| Topic | Default |
|-------|---------|
| Supervisor/Buyer home | Planner-style home until dedicated layouts |
| Feasibility breakdown without API | Derive component scores around overall in drawer |
| Empty active schedule | Placeholder Gantt bar + empty-state CTA |
| Kong `/api/v1/data` | Added to `kong.release2.yml`; requires stack reload |
