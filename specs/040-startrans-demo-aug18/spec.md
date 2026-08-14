# Feature Specification: Star Trans Demo Cycle — Aug 18, 2026

**Feature Branch**: `033-phase9-wave9a` (delivery) / Speckit `040-startrans-demo-aug18`  
**Created**: 2026-08-14  
**Status**: Active — demo gate Mon 18 Aug 2026 morning  
**Client**: Star Trans (Electrical Transformer Technology)  
**Prior**: Spec `012-startrans-client-demo` (CLOSED foundation) — this feature is the **Aug 18 intensive demo sprint** overlay  
**Constitution**: v1.4.7 · Honesty: never invent COM PASS  

---

## Goal

Ship a **customer-credible Star Trans demo** on IPE R2 that:

1. Shows **hygienic, professional UI** (no UUID greetings, Widget fixtures, epoch dates, fake AI autonomy zeros).
2. Lets planners/executives navigate a **role-aware Home** and Plan rail (Control Tower, Detailed Schedule Gantt, Feasibility drawer).
3. Accepts **Star Trans Excel workbook** (`IPE_Data_Template_StarTrans_v1.xlsx`, 24 sheets) via upload UI/API, with seed fallback if customer data is late.
4. Remains **honest** about COM blockers (Odoo live, Arabic QA, pricing) while engineering demo path is complete.

---

## Personas & User Stories

### US-1 — Demo lead (Waleed / Diligent)
**As** the demo lead, **I want** a documented environment + seed + walkthrough, **so that** Tuesday morning is reproducible without improvisation.

**Acceptance**
- [ ] `docs/DEMO_ENVIRONMENT.md` lists OS/browser/accounts/checklist
- [ ] `.\scripts\seed-startrans-demo.ps1` loads ≥20 MOs with feasibility bands
- [ ] Walkthrough checklist in `docs/STAR-TRANS-DEMO-WALKTHROUGH.md` executable in ≤45 min

### US-2 — Executive (Star Trans C-suite)
**As** an executive, **I want** a Home view with Factory Health, OTD, Cost of Chaos, top risk orders, and bottlenecks, **so that** I see factory risk in one screen.

**Acceptance**
- [ ] Role switcher → Executive → `/home` shows Executive layout
- [ ] KPI tiles + Copilot summary band + Top 5 at risk + WC heatmap
- [ ] Greeting never shows a UUID

### US-3 — Planner
**As** a planner, **I want** feasibility heatmap, MO risk queue, and material exceptions on Home, **so that** I start the day on the right MOs.

**Acceptance**
- [ ] Role=Planner → Planner Home
- [ ] Unscored MOs excluded from main CT queue; collapsible Needs data with reasons
- [ ] FeasibilityBadge opens decomposition drawer

### US-4 — Scheduler
**As** a scheduler, **I want** a library-based Gantt on Detailed Schedule, **so that** I see Work Center load without a custom SVG rewrite.

**Acceptance**
- [ ] `/plan/detailed-schedule` uses frappe-gantt (MIT)
- [ ] Day/Week toggle; WC + status filters; click bar → detail panel
- [ ] Bars colored by feasibility band when scores exist

### US-5 — Data owner (Star Trans IT / planning)
**As** Star Trans data owner, **I want** a filled Excel template ingested into IPE, **so that** Tuesday shows our products/WCs/MOs.

**Acceptance**
- [ ] Customer email + template file available
- [ ] `POST /api/v1/data/upload` accepts multipart `.xlsx`
- [ ] Sheet names match template (24); header row 4; data from row 5
- [ ] UI `/admin/data/upload` preview insert/fail + confirm commit
- [ ] Priority sheets: Plants, Work Centers, Products, Materials, Customers, MOs

### US-6 — Navigator (all roles)
**As** any user, **I want** Home / Plan / Execute / Supply / Analyze / Copilot (+ Admin), **so that** IA matches the redesign without broken deep links.

**Acceptance**
- [ ] Six-section rail + Admin gear; no MORE bucket
- [ ] Legacy routes redirect
- [ ] Breadcrumbs under header

---

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-040-01 | Time-aware greeting; never render UUID as name | P0 |
| FR-040-02 | Purge Widget A/B fixtures from seeds + optional SQL | P0 |
| FR-040-03 | DateCell: null/epoch → muted "Not set" | P0 |
| FR-040-04 | Unscored MOs → Needs data panel with BOM/routing/due reasons | P0 |
| FR-040-05 | Replace AI Autonomy:0 with Copilot actions (or hide) | P0 |
| FR-040-06 | Design tokens: feasibility bands, constraints, AI accent | P1 |
| FR-040-07 | Sidebar IA + breadcrumbs + reusable planning components | P1 |
| FR-040-08 | Demo role: executive \| planner \| supervisor \| buyer + localStorage | P0 |
| FR-040-09 | Executive Home + Planner Home on `/home` | P0 |
| FR-040-10 | frappe-gantt Detailed Schedule page | P0 |
| FR-040-11 | FeasibilityDrawer wired to all FeasibilityBadges | P0 |
| FR-040-12 | Terminology: Work Center, MO; percent/date formatting | P1 |
| FR-040-13 | Empty states with message + action | P1 |
| FR-040-14 | Excel multipart upload + 24-sheet parser + demo CDM ingest | P0 |
| FR-040-15 | Upload UI preview/confirm | P0 |
| FR-040-16 | Seed 20 MOs with band distribution 3/5/4/8 | P0 |
| FR-040-17 | Align parser to `IPE_Data_Template_StarTrans_v1.xlsx` | P0 |
| FR-040-18 | E2E walkthrough + hygiene grep + screenshots | P0 |

## Non-Functional

| ID | Requirement |
|----|-------------|
| NFR-040-01 | Do not break existing routes (redirect if rename) |
| NFR-040-02 | Ship ugly+working over pretty+broken for demo |
| NFR-040-03 | Commit per task `STREAM-N.T: …` |
| NFR-040-04 | Never fake COM gates (G-R2-04, PH1-02, OQ-7) |
| NFR-040-05 | Demo CDM may skip RLS/GIN for speed — must not claim production CDM |

## Out of Scope (explicit)

- Live Odoo write-back / PH1-02 staging proof
- G-R2-04 Arabic native QA sign-off
- OQ-7 pricing / SOW send
- Production-depth Phase 9B–9F ML/SAP/OCR
- Custom SVG Gantt rewrite
- Full RLS on `demo_*` tables for this demo cycle

## Success Criteria (demo morning)

1. Walkthrough steps 1–8 PASS on warm R2 stack  
2. Hygiene: zero Widget A/B, UUID greeting, 1/1/1970 display in demo path  
3. Customer template email sent; ingest path verified on sample workbook  
4. Screenshots captured under `docs/star-trans-demo-screenshots/`  

## Dependencies

- R2 compose (`docker-compose.release2.yml`), Kong `/api/v1/data` + `/api/v1/upload`
- Existing CT / feasibility / capacity / workspace APIs
- Spec 032 upload-svc foundation; Spec 012 seed scripts
