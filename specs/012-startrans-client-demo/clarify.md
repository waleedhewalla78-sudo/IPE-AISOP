# Clarify — 012 Star Trans Client Demo

Decisions locked for **today's** implementation (2026-06-29).

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| Q1 | New tenant vs overlay? | **Overlay on existing demo tenant** (`a0eebc99…`) | Preserves UUID graph; 32/32 script unchanged structurally |
| Q2 | Full SQL fork vs UPDATE overlay? | **Overlay SQL after `seed-demo-client.sql`** | Lower risk; faster to validate |
| Q3 | Upload on every screen? | **No** — Schedule Excel only (existing UI) | Avoid demo-day UI bugs |
| Q4 | Excel format? | **6-sheet workbook schema** + CSV samples for Schedule sheet | Document now; full importer POST-demo |
| Q5 | MO ID scheme? | `MO-ST-001` … `MO-ST-010` (maps 1:1 from MO-DEMO-xxx) | Copilot + presenter script alignment |
| Q6 | Keep PROD001 codes? | **Yes** — rename `name` only | BOM/routing FKs stable |
| Q7 | Live Copilot LLM? | **Ollama host** (`prepare-demo.ps1` pattern) | Required by client; pre-run CP10–11 |
| Q8 | ERP integration story? | **Verbal + "ERP sync deferred"** in schedule approve | Honest; scaffold exists |
| Q9 | Revert after demo? | **`seed-demo-client.ps1`** restores generic names | Optional rollback path |
| Q10 | Validation gate? | `run-full-demo.ps1 -Profile startrans` must pass | Same 32 CPs, Star Trans strings |

## Open (acceptable for demo)

| Item | Mitigation |
|------|------------|
| Plant codes still `DEMO-*` internally | Display names updated to Star Trans cities |
| Copilot may use generic phrasing | Cheat sheet uses MO-ST-xxx and product full names |
| No client SSO accounts | Screen share; single presenter login |
