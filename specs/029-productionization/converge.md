# Converge — Spec 029 Productionization

**STATUS:** ENG COMPLETE Wave 1  
**Date**: 2026-07-18 · **Finalize refresh:** 2026-07-18  
**Verdict**: **ENG COMPLETE Wave 1**  
**Authoritative:** `docs/project/FINAL-PROGRAM-STATUS.md`

## Closed by engineering

- Kong `/api/v1/enterprise` (R2 + deploy mirrors)
- Andon dual-write → `cdm_andon_alert`
- RLS migration **068**; MPS/MRP **069**
- S&OP stage-gate scaffold APIs
- QA notes (k6 p95 + Playwright flakes) + Phase3+ e2e stub
- Speckit artifacts; GH issues #111–#122 (+ resume dups #123/#137–#143 closed as duplicates)
- Unit tests: Spec 029 suite green (absorbed in `38e78fa`)

## Remaining (honest — listed once)

| ID | Item | Status |
|----|------|--------|
| #70/#72/#110/#120/#136/#142 | seed + star-trans-validate | **OPEN** (stack-dependent; Docker down finalize) |
| QA-01 | k6 p95 under load | **OPEN** — notes only |
| QA-02 | Playwright flakes | **OPEN** — notes + stub |
| #106/#108/#109/#107 | COM blockers | **OPEN** — never fake |
| REL | `v9.1.1-r2` | **HOLD** (G-R2-04); never push `v9.1.0-r2` |

## Follow-on

Spec **030** Phase 8 R1 production scaffold continued (`constitution` 1.4.2). Spec 029 Wave 1 remains ENG COMPLETE.
