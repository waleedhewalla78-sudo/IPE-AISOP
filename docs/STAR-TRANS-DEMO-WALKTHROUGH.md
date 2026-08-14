# Star Trans Demo — End-to-end Walkthrough (STREAM-7.1)

**Date:** 2026-08-14  
**Branch:** `033-phase9-wave9a`  
**Demo morning:** 2026-08-18

## Preconditions

1. R2 stack up: `cd ipe; docker compose -f infrastructure/docker/docker-compose.release2.yml up -d`
2. Seed: `.\scripts\seed-startrans-demo.ps1`
3. Optional purge: `psql … -f scripts/purge-widget-fixtures.sql`
4. Login: see [DEMO_ENVIRONMENT.md](./DEMO_ENVIRONMENT.md)

## Walkthrough checklist

| # | Step | Expected | Pass? |
|---|------|----------|-------|
| 1 | Login → set Role **Executive** (top-right) → open `/home` | Executive Home: 3 KPIs, Copilot band, Top 5 risk, bottleneck heatmap | ☐ |
| 2 | Switch Role → **Planner** → `/home` | Planner Home: feasibility heatmap, MO risk queue, material + Copilot | ☐ |
| 3 | Plan → Control Tower | Main risk queue excludes unscored; **Needs data (N)** collapsible | ☐ |
| 4 | Click any **FeasibilityBadge** | FeasibilityDrawer opens with breakdown weights | ☐ |
| 5 | Plan → **Detailed Schedule** (`/plan/detailed-schedule`) | frappe-gantt renders; Day/Week toggle; WC filter | ☐ |
| 6 | Click a Gantt bar | Task detail panel shows MO / Work Center / feasibility | ☐ |
| 7 | Admin → `/admin/data/upload` | Drag-drop Excel; preview insert/fail counts | ☐ |
| 8 | Greeting on Home | Never shows UUID; time-aware Good morning/afternoon/evening | ☐ |

## Known demo caveats

- Live DB must be up for seed/purge; Excel commit writes `demo_*` tables (simplified CDM).
- If active schedule empty, Gantt shows placeholder bar — run Auto Schedule or project-plan upload first.
- Role switcher is localStorage UX only (does not change JWT).
