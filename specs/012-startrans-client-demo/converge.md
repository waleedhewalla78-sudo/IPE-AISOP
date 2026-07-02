# Converge — 012 Star Trans Client Demo

**Date**: 2026-06-29  
**Status**: Implemented — **32/32 PASS** (2026-06-29)

---

## Delivered

| Task | Evidence |
|------|----------|
| Industry overlay SQL | `scripts/seed-startrans-overlay.sql` |
| Seed + prepare scripts | `scripts/seed-startrans-demo.ps1`, `prepare-startrans-demo.ps1` |
| Demo profile validation | `run-full-demo.ps1 -Profile startrans` |
| Presenter guide | `docs/demo-data/STARTRANS-DEMO-GUIDE.md` |
| Copilot cheat sheet | `docs/demo-data/STARTRANS-COPILOT-CHEATSHEET.md` |
| Excel schema + CSV sample | `docs/demo-data/STARTRANS-EXCEL-SCHEMA.md`, `startrans/project-plan-startrans-w12.csv` |

## Pre-meeting command

```powershell
.\scripts\prepare-startrans-demo.ps1
cd apps\web; npm run dev
```

## POST-demo backlog

- Multi-sheet Excel → SQL importer (`import-startrans-workbook.ps1`)
- Demand signal CSV upload UI on Demand page
- Optional dedicated Star Trans tenant UUID

## Gate

**PASSED:** `docs/demo-data/startrans-pre-demo.txt` — **32/32** (2026-06-29 07:12).
