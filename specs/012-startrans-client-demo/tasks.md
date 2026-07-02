# Tasks — 012 Star Trans Client Demo

| ID | Task | Status | Evidence |
|----|------|--------|----------|
| T001 | Create spec + clarify + analyze + plan | ✅ | `specs/012-startrans-client-demo/` |
| T002 | Write `seed-startrans-overlay.sql` | ✅ | `scripts/seed-startrans-overlay.sql` |
| T003 | Write `seed-startrans-demo.ps1` | ✅ | `scripts/seed-startrans-demo.ps1` |
| T004 | Write `prepare-startrans-demo.ps1` | ✅ | `scripts/prepare-startrans-demo.ps1` |
| T005 | Add `-Profile startrans` to `run-full-demo.ps1` | ✅ | `-Profile startrans` param |
| T006 | STARTRANS-DEMO-GUIDE.md (60 min) | ✅ | `docs/demo-data/STARTRANS-DEMO-GUIDE.md` |
| T007 | STARTRANS-COPILOT-CHEATSHEET.md | ✅ | `docs/demo-data/STARTRANS-COPILOT-CHEATSHEET.md` |
| T008 | STARTRANS-EXCEL-SCHEMA.md + sample CSV | ✅ | `docs/demo-data/startrans/` |
| T009 | Update `.specify/feature.json` | ✅ | phase 012 |
| T010 | Run validation 32/32 startrans profile | ✅ | `docs/demo-data/startrans-pre-demo.txt` — 32/32 |
| T011 | converge.md closure | ✅ | `converge.md` |

## Execution order

```
T002 → T003 → T004 → T005 → T006–T008 → T009 → T010 → T011
```

## Gate

**T010:** `.\scripts\prepare-startrans-demo.ps1` → `docs/demo-data/startrans-pre-demo.txt` must show 32/32.
