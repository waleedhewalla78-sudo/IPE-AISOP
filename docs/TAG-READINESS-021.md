# Tag Readiness — Spec 021 Release Closure

**Date:** 2026-07-11  
**Spec:** 021-release-closure  
**Prior policy:** `docs/TAG-DECISION.md`

---

## Tag Decision Matrix

| Tag | Purpose | Gate Conditions | Current State | Action |
|-----|---------|-----------------|---------------|--------|
| `v9.1.1-r2` | Release 2 MENA go-live tag | G-R2-04 Arabic native sign-off | **HOLD** — human blocker | Wait for native reviewer |
| `v9.2.0-planning` | Planning intelligence release | UAT-10/11 PASS on live stack (10/10 planning-uat.ps1) | **HOLD** — code fix committed; pending live re-run | Re-run after docker stack up |
| `v9.4.0-p3` | Phase 3 enterprise tag | Already applied at `4629119` | **DONE** | No action |
| `v9.1.0-r2` | Old R2 tag (local only) | Never pushed to origin | **IGNORE** | Do not push; superseded by v9.1.1-r2 path |

---

## v9.1.1-r2 Cut Conditions

**All must be true before cutting:**

1. G-R2-04: Native Arabic reviewer has signed off `docs/qa/arabic-qa-r2.md`
2. G-R2-01 still PASS: `scripts/release2-smoke.ps1` ≥15/15
3. G-R2-05 still PASS: `scripts/run-release2-demo.ps1` ≥7/7
4. `git push origin master` includes all R2 commits
5. No force-push to master or existing tags

**Procedure:**
```powershell
git tag -a v9.1.1-r2 -m "Release 2 MENA: G-R2-04 Arabic sign-off complete"
git push origin v9.1.1-r2
```

---

## v9.2.0-planning Cut Conditions

**All must be true before cutting:**

1. `scripts/planning-uat.ps1` scores **10/10 PASS, 0 PARTIAL** on a live stack
   - UAT-10 (`/copilot/chat` timeout): PASS after Spec 021 fix
   - UAT-11 (best-fit cold path): PASS after Spec 021 fix
2. `scripts/release2-smoke.ps1` still ≥15/15
3. All 021 code changes pushed to `origin/master`
4. No LLM key requirement for engineering gate — tool fallback is sufficient

**Procedure:**
```powershell
git tag -a v9.2.0-planning -m "Planning intelligence UAT 10/10 green"
git push origin v9.2.0-planning
```

---

## Notes on LLM Keys

- UAT-10 engineering PASS = endpoint returns within 20 s (tool fallback path when LLM unavailable)
- Full LLM-synthesised answer requires `IPE_ANTHROPIC_API_KEY` or `IPE_OLLAMA_ENDPOINT_URL` in `.env`
- LLM keys are a **demo quality** gate, not an **engineering** gate
- Do NOT store LLM keys in source or commit them

---

## Do NOT

- Do NOT push `v9.1.0-r2` — it is a stale local tag from an earlier cut
- Do NOT re-tag `v9.4.0-p3` — Phase 3 is closed
- Do NOT cut tags without all conditions green — constitutes gate theater (Principle VIII)
