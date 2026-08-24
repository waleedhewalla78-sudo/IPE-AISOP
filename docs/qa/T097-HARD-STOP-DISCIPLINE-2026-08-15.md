# T097 — Hard-stop discipline (Star Trans demo)

**Status:** CLOSED (process locked)  
**Effective:** Sun 17 Aug 2026 **18:00 Cairo** → Mon 18 Aug 2026 morning demo  
**Spec:** `040-startrans-demo-aug18`

## Rules (locked)

1. **After Sun 17 Aug 18:00 Cairo** — no new Cursor feature/ops prompts; **bug-fix only**.
2. **Mon 18 morning** — demo mode only (no rebuilds, no schema changes, no “quick polish”).
3. **Do not** open new Speckit waves or Batch 1 work until post-demo (Tue) post-mortem.

## Allowed after hard stop

- Hotfix for a demo-blocking crash (login, blank home, seed wipe) — document in `docs/qa/` with timestamp.
- Practice walkthrough on the warm R2 stack already UP.

## Forbidden after hard stop

- New UI/nav/theme changes  
- New seed/script changes unless seed is empty  
- “While we’re here” refactors  
- Fake-closing COM / Arabic / live Odoo items

## Owners

| Window | Owner | Action |
|--------|-------|--------|
| Sat–Sun before 18:00 | ENG | Finish T095 email / T096 ingest if file arrives |
| Sun 18:00+ | ENG | Bug-fix only |
| Mon morning | Demo lead | Run walkthrough; no Cursor prompts |

## Evidence

- Spec tasks: T097 checked in `specs/040-startrans-demo-aug18/tasks.md`
- Batch 0 prompt post-checklist item closed here (human calendar commitment)
