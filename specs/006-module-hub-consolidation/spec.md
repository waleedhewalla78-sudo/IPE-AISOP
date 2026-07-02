# Feature Specification: Module Hub Consolidation (006)

**Feature Branch**: `006-module-hub-consolidation`  
**Created**: 2026-06-27  
**Status**: Implemented  
**Input**: Confirmed 5-hub consolidation + Planning Dashboard + Executive Command Dashboard

---

## What We Build

Consolidate 18 scattered UI modules into **6 navigation hubs** (5 confirmed + Shop Floor standalone) with **tabbed sub-navigation**, preserving all existing page components and API contracts.

| Hub | Tabs | Source modules |
|-----|------|----------------|
| **Planning Hub** | Dashboard, Control Tower, Resolution, Schedule | fea, res, cap |
| **Command Center** | Dashboard, War Room, Executive, Cost of Chaos | alert, dpe analytics |
| **Supply Chain Hub** | Tariff, SCN Portal, Inventory | mat, scn |
| **AI & Governance** | Copilot, AI Trust, MDR, Compliance, Quality, Sustainability | nlp, dpe |
| **Platform** | Admin, Onboarding, MLOps | dpe admin |
| **Shop Floor** | (standalone) | del/cap |

### New dashboards

- **Planning Dashboard** — KPI cards: queue size, feasibility, at-risk MOs, scenarios, scheduled ops
- **Command Center Dashboard** — KPI cards: alerts, AI OTD, cost of chaos, recovery options, delay categories

---

## What We Want (requirements)

### FR-HUB-01 Navigation
Sidebar shows **6 items** max (down from 14). Hub tabs expose all former modules.

### FR-HUB-02 Zero data loss
All existing routes redirect to hub tabs. No API or backend changes.

### FR-HUB-03 Role compatibility
Existing RBAC unchanged; hubs are UX-only composition.

### FR-HUB-04 Demo compatibility
`run-full-demo.ps1` updated to hub UI paths; legacy URLs redirect.

---

## User Stories

| ID | Story | Acceptance |
|----|-------|------------|
| US-H1 | Planner opens Planning Hub dashboard and jumps to Resolution | Dashboard links work; tabs render |
| US-H2 | Executive opens Command Center dashboard | Alerts, OTD, chaos $ visible |
| US-H3 | Buyer opens Supply Chain inventory tab | FG SKUs from mat-svc |
| US-H4 | Admin uses Platform hub | Admin, onboarding, MLOps tabs |
| US-H5 | Bookmark `/control-tower` still works | Redirect to `/planning/control-tower` |

---

## Out of Scope

- Backend service merges
- Removing legacy API endpoints
- Role-based hub visibility (future)
