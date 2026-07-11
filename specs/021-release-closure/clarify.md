# Clarify — Spec 021 Release Closure

**Date:** 2026-07-11  
**Status:** Resolved (no blocking ambiguities)

---

## Q1: Should UAT-10/11 be marked PASS even when LLM keys are absent?

**Resolution:** No. The UAT definition requires the endpoint to return within ≤20 s with a useful (tool-backed) response. After the fix, the endpoint returns a structured tool snapshot within the budget even when no LLM key is set. This is an **engineering PASS** condition. A separate condition for "LLM-synthesised answer" requires live LLM keys and is documented in the honest-blockers section — it is not required for the engineering UAT gate.

## Q2: Does adding a time budget to best-fit change API contract or schema?

**Resolution:** No schema change. `BestFitResult.selected_model` may now be `"ses"` for segments that would previously have chosen ARIMA/SARIMA when history is short or the time budget is exhausted. This is a graceful degradation, not a breaking change. Existing tests that assert `selected_model in {"ses", "arima", "sarima"}` continue to pass.

## Q3: Should OQ-13 migration apply path block the tag, or just be documented?

**Resolution:** OQ-13 is a documentation + scripting task. Migrations 044–049 were already applied to the compose DB during Spec 020 UAT. The apply path needs to be scripted so operators can reproduce it on a fresh or upgraded environment. The script does not block the engineering tag — it is a release ops artefact.

## Q4: Which tag to cut — v9.1.1-r2 or v9.2.0-planning, or both?

**Resolution:** 
- `v9.1.1-r2`: HOLD until G-R2-04 Arabic native sign-off (human blocker). Do NOT cut without that sign-off.
- `v9.2.0-planning`: Cut after `planning-uat.ps1` scores 10/10 on a live stack (engineering gate). This gate is unblocked by fixing UAT-10/11. If LLM keys are absent, document as "LLM keys required for full LLM synthesis; tool fallback passes engineering gate."
- Both tags can co-exist; they address different release tracks.

## Q5: Do we need to close/comment existing GitHub issues as part of Spec 021?

**Resolution:** Yes. RC-05 covers triage comments on existing open issues (#27–#36, #29–#30 already closed). New GitHub issues are created for RC-01–RC-08 tasks. Issue #50 (commercial blockers) remains OPEN and is not touched by engineering.
