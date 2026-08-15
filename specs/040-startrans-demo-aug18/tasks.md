# Tasks — Spec 040 Star Trans Demo Aug 18

**Feature:** `040-startrans-demo-aug18`  
**Convention:** STREAM commits already landed; remaining = ops + harden  

Legend: `[x]` done · `[ ]` open

---

## Phase A — Demo hygiene (STREAM-1) — DONE

- [x] T001 STREAM-1.1 Remove UUID from greeting
- [x] T002 STREAM-1.2 Purge Widget A/B fixtures
- [x] T003 STREAM-1.3 DateCell for epoch/null
- [x] T004 STREAM-1.4 Needs data panel for unscored MOs
- [x] T005 STREAM-1.5 Copilot actions tile
- [x] T006 STREAM-1.6 DEMO_ENVIRONMENT.md

## Phase B — Excel ingestion (STREAM-2) — ENG DONE

- [x] T010 STREAM-2.1 POST /api/v1/data/upload
- [x] T011 STREAM-2.2 24-sheet parser
- [x] T012 STREAM-2.3 Demo CDM tables
- [x] T013 STREAM-2.4 Ingest + FK batch report
- [x] T014 STREAM-2.5 Upload UI /admin/data/upload
- [x] T015 STREAM-2.6 Seed 20 MOs feasibility bands
- [x] T016 Align parser to IPE_Data_Template_StarTrans_v1.xlsx
- [x] T017 Customer email draft + template in repo

## Phase C — Nav / tokens / components (STREAM-3) — DONE

- [x] T020 Design tokens
- [x] T021 Sidebar six sections + Admin
- [x] T022 Breadcrumbs
- [x] T023 FeasibilityBadge / ConstraintChip / KpiTile

## Phase D — Homes (STREAM-4) — DONE

- [x] T030 Demo role switcher
- [x] T031 Executive Home
- [x] T032 Planner Home

## Phase E — Gantt (STREAM-5) — DONE

- [x] T040 Install frappe-gantt
- [x] T041 Schedule adapter
- [x] T042 Detailed Schedule page

## Phase F — Drawer / polish (STREAM-6) — DONE

- [x] T050 FeasibilityDrawer
- [x] T051 Wire badges globally
- [x] T052 Terminology + formatPercent
- [x] T053 Empty states

## Phase G — Integration docs (STREAM-7) — PARTIAL

- [x] T060 Walkthrough markdown
- [x] T061 Hygiene report markdown
- [x] T062 Screenshot README checklist
- [x] T063 **Execute** walkthrough on warm R2 (8 steps PASS)
- [x] T064 Capture PNGs to `docs/star-trans-demo-screenshots/`
- [x] T065 Reload Kong; verify `POST /api/v1/data/upload` via gateway
- [x] T066 Apply seed + optional purge on live DB

## Phase H — Speckit / governance (this run)

- [x] T070 Create Spec 040 spec/clarify/plan/analyze/tasks
- [x] T071 Point `.specify/feature.json` → 040
- [x] T071a `scripts/verify-startrans-template.ps1` PASS on canonical xlsx
- [ ] T072 Sync root constitution pointer if Speckit run from AISOP root (N/A — no root memory path)
- [ ] T073 Close or defer Spec 040 after demo with evidence link

## Phase I — Explicitly NOT eng tasks (COM)

- [ ] T080 OQ-7 pricing — HUMAN
- [ ] T081 PH1-02 live Odoo — HUMAN/IT
- [ ] T082 G-R2-04 Arabic QA — HUMAN
- [ ] T083 C-01…C-08 — HUMAN (#163)

## Phase J — Appended by `/speckit.converge` (2026-08-14)

- [x] T090 Bring up R2 stack healthy
- [x] T091 Kong `/api/v1/data` live verify
- [x] T092 Seed + purge on live DB
- [x] T093 Walkthrough 8 steps PASS
- [x] T094 Screenshot PNGs
- [ ] T095 Send customer template email — HUMAN (not Cursor)
- [ ] T096 Sunday customer ingest (if file arrives) — HUMAN/OPS
- [x] T097 Hard stop discipline Sun 18:00 / Mon morning — see `docs/qa/T097-HARD-STOP-DISCIPLINE-2026-08-15.md`
- [x] T100 Playwright home role smoke — `e2e/home-role.spec.ts` desktop **3/3 PASS** (`docs/qa/T100-HOME-ROLE-SMOKE-2026-08-15.md`)
- [ ] T101 BOM/routing line sheet upsert depth (optional)
- [ ] T102 demo_* → CDM+RLS post-demo
- [ ] T103 Supervisor/Buyer dedicated homes (optional)
- [ ] T110–T113 COM blockers (see T080–T083) — **remain OPEN**; honesty lock `docs/qa/COM-BLOCKERS-REMAIN-OPEN-2026-08-15.md`
