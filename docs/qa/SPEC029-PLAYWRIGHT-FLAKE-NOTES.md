# Spec 029 — Playwright flake notes (QA-02)

**Date**: 2026-07-18  
**Status**: Notes + guidance (Wave 1)

## Observed flakes (prior campaign)

| Spec | Failure mode | Viewport |
|------|--------------|----------|
| Arabic RTL labels | Timeout waiting for Arabic labels on 8 screens | tablet |
| Critical-path a11y | Mobile login `h1` a11y violation flake | mobile |
| Login flow | Desktop/tablet generally green (3/3 login) | — |

Full suite historically **56 pass / 2 fail** with flakes above.

## Stabilization guidance (not claimed fixed in this run)

1. Prefer `getByRole` / stable `data-testid` over brittle text for Arabic i18n screens.
2. Increase tablet Arabic suite timeout; wait for network idle after locale switch.
3. Mobile a11y: assert on landmark present rather than exact `h1` count if marketing chrome differs.
4. Phase 3+ page e2e: prefer API/ASGI smoke for agents/intelligence hubs; browser e2e only for critical planner path until PH1-02 live data exists.

## Stub policy

Do not invent green Playwright evidence. Re-run `apps/web` e2e when UI stack healthy; attach `playwright-e2e.txt` under campaign folder.
