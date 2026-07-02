# Plan — 012 Star Trans Client Demo

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Authoring (offline)                                         │
│  docs/demo-data/STARTRANS-EXCEL-SCHEMA.md                   │
│  docs/demo-data/startrans/project-plan-startrans-w12.csv    │
└──────────────────────────┬──────────────────────────────────┘
                           │ T-90 min
┌──────────────────────────▼──────────────────────────────────┐
│  prepare-startrans-demo.ps1                                  │
│    1. prepare-demo.ps1 (Docker + Kong + Ollama)             │
│    2. seed-demo-client.ps1 (base graph)                      │
│    3. seed-startrans-overlay.sql (branding)                  │
│    4. run-full-demo.ps1 -Profile startrans                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   Control Tower      Copilot (live)    Schedule upload
   MO-ST-001…         DB-backed names    .xlsx from CSV
```

## Tech Stack (unchanged)

| Layer | Choice |
|-------|--------|
| Runtime | Docker Compose + Kong :8000 |
| UI | Vite React :8082 |
| DB | PostgreSQL `ipe_test` |
| LLM | Ollama `llama3.2:3b` host :11434 |
| Seed | psql via `docker exec` |
| Validation | PowerShell `run-full-demo.ps1` |
| Live upload | Existing `cap-svc` Excel parser |

## File Plan

| Path | Purpose |
|------|---------|
| `scripts/seed-startrans-overlay.sql` | Industry rename overlay |
| `scripts/seed-startrans-demo.ps1` | Base seed + overlay |
| `scripts/prepare-startrans-demo.ps1` | Full prep + validation |
| `scripts/run-full-demo.ps1` | Add `-Profile startrans` |
| `docs/demo-data/STARTRANS-DEMO-GUIDE.md` | 60-min presenter script |
| `docs/demo-data/STARTRANS-COPILOT-CHEATSHEET.md` | Live query card |
| `docs/demo-data/STARTRANS-EXCEL-SCHEMA.md` | Workbook spec |
| `docs/demo-data/startrans/project-plan-startrans-w12.csv` | Upload sample |

## Live Demo Actions (in meeting)

1. **Demand** — Run sense cycle (button)
2. **Scenario** — Create sandbox + simulate
3. **Schedule** — Upload `project-plan-startrans-w12.xlsx` (convert CSV → xlsx before demo)
4. **Orders** — Create utility order (optional)
5. **Copilot** — 3 queries from cheat sheet

## Rollback

```powershell
.\scripts\seed-demo-client.ps1   # restores MO-DEMO-* erp_mo_id if overlay re-run idempotent
# Re-run generic seed-data for product names if needed
```
