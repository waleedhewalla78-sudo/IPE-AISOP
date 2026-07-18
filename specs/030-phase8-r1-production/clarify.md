# Clarify — Spec 030 Phase 8 Wave 1 (8A)

**Date**: 2026-07-18 · **Constitution**: 1.4.2 · **Mode**: No mid-pipeline approval stops (auto-resolve)

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Extend Spec 029 vs new Spec 030? | **Spec 030**. Spec 029 converge = ENG COMPLETE Wave 1; Phase 8 is a new production-agent track. |
| Q2 | Full Phase 8 v2 (30 weeks / 8A–8D) in this run? | **Wave 1 / 8A only**. 8B–8D deferred explicitly. |
| Q3 | Claim live Ollama 70B / fine-tuned weights? | **No.** Modelfile + ops README stubs; runtime degrade when unreachable. |
| Q4 | Live Odoo write-back execute? | **No.** Dry-run + approval log; `ipe.odoo.live_writeback` default false; PH1-02 OPEN. |
| Q5 | Close G-R2-04 / OQ-7 / apply `v9.1.1-r2`? | **Never.** Document COM OPEN; eng Arabic keys only. |
| Q6 | Absorb concurrent Phase 8 agent work? | **Yes.** Code already in tree (ollama/roles/write-back/upload/UI); Speckit fills docs, Kong route, reports, gaps only. |
| Q7 | Recreate Spec 029 from scratch? | **No.** Reference as prior; residuals #70/#72/#110 remain stack-OPEN. |
| Q8 | Excel “everywhere” (all screens)? | **Wave 1 slice only** — 3 new upload schemas + CT/MPS CSV export. Full matrix → 8C. |
| Q9 | A18–A20 full behaviour? | **Stubs + tests** in 8A; live multi-site/learning → 8B+. |
| Q10 | Migration head? | Continue **070** after 069; RLS on `cdm_write_back_log` mandatory. |

## Unresolved (intentionally OPEN — human/COM)

- OQ-7 pricing / SOW send
- PH1-02 live Odoo staging
- G-R2-04 Arabic native QA
- OQ-1 Odoo version confirmation
- Stack-dependent validate #70 / #72 / #110
