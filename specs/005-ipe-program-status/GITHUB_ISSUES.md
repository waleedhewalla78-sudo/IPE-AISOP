# GitHub Issues — IPE Program Release (005)

**Generated**: 2026-06-26 via `/speckit.taskstoissues`  
**Script**: [`../../scripts/create-release-issues.ps1`](../../scripts/create-release-issues.ps1)  
**Status**: REL-STACK/TEST ✅ · REL-DEMO **19/20** · T016–T019 ✅ · T021 open

**Prerequisites**: `gh auth login` + git remote; Docker Desktop running.

```powershell
cd E:\AISOP\ipe
.\scripts\create-release-issues.ps1
```

---

## Epic: IPE v6.0.0 — Demo Gate & Tag

**Labels**: `release`, `v6.0.0`, `P0`  
**Milestone**: v6.0.0

| Issue | Title | Task ID | Status |
|-------|-------|---------|--------|
| #1 | [REL-STACK] Demo stack up + seed | REL-01–05 | ✅ Done |
| #2 | [REL-TEST] launch-verify 10/10 | REL-06–08 | ✅ Done |
| #3 | [REL-DEMO] run-full-demo 20/20 | T016–T022 | 🟡 19/20 |
| #4 | [PHASE-0] Git init + initial commit | T023 | ⬜ Open |
| #5 | [REL-TAG] Git tag v6.0.0 (T055) | T024 | ⬜ Blocked on #3–#4 |
| #6 | [AUDIT-P1] C-01, C-02, BUG-02, BUG-03 | T025–T026 | ⬜ Post-tag |
| #7 | [REL-PROD] k6 + Chaos → 100/100 | T027 | ⬜ Optional |

---

## Issue 3 — REL-DEMO (updated 2026-06-26)

**Title**: `[REL-DEMO] Achieve stable 20/20 live demo`

**Labels**: `release`, `P0`, `demo`

**Body**:

```markdown
## Summary
Complete remaining demo checkpoint CP15 after V6 demo fixes T016–T019.

## Completed subtasks
- [x] T016 Copilot 503 — nlp-svc structured fallback
- [x] T017 CP15 guardrail — ApproveMoIds 005/006 in run-full-demo.ps1
- [x] T018 Tariff shock — BomLine→BillOfMaterial join
- [x] T019 War Room — alert-svc init_database + recovery fallback

## Open
- [ ] T021 Skip MAINT_* synthetic ops in schedule_persistence.py
- [ ] T022 Rebuild cap-svc; rerun run-full-demo.ps1 → 20/20

## Acceptance
`docs/demo-run-report-v6.txt` shows 20/20 PASS.

## References
- specs/005-ipe-program-status/converge.md
- docs/demo-run-report-v6.txt
```

---

## Issue 4 — PHASE-0 Git Foundation

**Title**: `[PHASE-0] Initial git commit before v6.0.0 tag`

**Labels**: `release`, `P0`, `hygiene`

**Body**:

```markdown
## Summary
Repository has zero commits. Capture all demo fixes before tagging.

## Tasks
- [ ] T023 `git init` + `git add -A` + commit message v6.0.0-rc1
- [ ] Include: BUG-01, T016–T019, T021 fixes

## Acceptance
`git log -1` shows initial commit; user approved.

## References
- Master Execution Plan §5.1
- clarify.md C-P-32
```

---

## Issue 6 — Audit P1 Fixes (post-tag)

**Title**: `[AUDIT-P1] Production blockers from June 20 audit`

**Labels**: `audit`, `P1`, `security`

**Body**:

```markdown
## Tasks
- [ ] C-01 mat-svc check-availability → rule_based_atp()
- [ ] C-02 dpe-svc remove double /api/v1 prefix on ctp route
- [ ] BUG-02 MDR gate fail-closed when dpe-svc unreachable
- [ ] BUG-03 Optimistic lock on approve_schedule_mos UPDATE

## References
- Master Execution Plan §5.2, §7
- audit-report.md
```
