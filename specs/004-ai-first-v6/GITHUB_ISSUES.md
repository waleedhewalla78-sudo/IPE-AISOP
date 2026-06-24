# GitHub Issues — IPE V6 Release Track

**Generated**: 2026-06-23 via `/speckit.taskstoissues`  
**Script**: [`../../scripts/create-release-issues.ps1`](../../scripts/create-release-issues.ps1)  
**Status**: REL-01, REL-06–08, P-DOC-01–03/05–08 ✅ | REL-02–05 blocked (Docker build RO FS) | REL-09–17 open

**Prerequisites**: Docker Desktop with writable build cache; `gh auth login` + git remote for live issue creation.

```powershell
git remote add origin https://github.com/YOUR_ORG/AISOP.git
gh auth login
```

**Bulk create** (from repo root):

```powershell
cd D:\AISOP\ipe
.\scripts\create-release-issues.ps1
```

---

## Epic: IPE v6.0.0 Release Verification

**Labels**: `release`, `v6.0.0`, `P0`  
**Milestone**: v6.0.0

| Issue | Title | Task ID | Blocks |
|-------|-------|---------|--------|
| #1 | [REL-STACK] Start docker stack and seed demo data | REL-01–05 | tag |
| #2 | [REL-TEST] launch-verify 10/10 + evidence | REL-06–08 | tag |
| #3 | [REL-DEMO] run-full-demo 20/20 live | REL-09–11 | tag |
| #4 | [REL-TAG] Git tag v6.0.0 (T055) | REL-12–17 | — |
| #5 | [P-DOC] Sync speckit doc drift | P-DOC-01–08 | — |
| #6 | [REL-PROD] k6 + Chaos → 100/100 | REL-18–20 | optional |

---

## Issue Templates

### Issue 1 — REL-STACK

**Title**: `[REL-STACK] Docker stack up + seed demo tenant`

**Labels**: `release`, `P0`, `ops`

**Body**:

```markdown
## Summary
Bring up IPE docker stack and seed V6 demo data for live verification.

## Tasks
- [ ] REL-01 `docker compose config` exit 0
- [ ] REL-02 `docker compose up -d`
- [ ] REL-03 API http://localhost:8000/health → 200
- [ ] REL-04 Migrations through 027 applied
- [ ] REL-05 `scripts/seed-demo-client.ps1`

## Tech stack
Docker Compose, PostgreSQL 16, Kafka, Kong @ :8000, React @ :8082

## Acceptance
API + web reachable; demo tenant seeded.

## References
- specs/004-ai-first-v6/tasks-release.md
- specs/005-ipe-program-status/plan.md § RV-01
```

---

### Issue 2 — REL-TEST

**Title**: `[REL-TEST] launch-verify.ps1 10/10 services`

**Labels**: `release`, `P0`, `testing`

**Body**:

```markdown
## Summary
Run backend test matrix across 10 services.

## Tasks
- [x] REL-06 launch-verify.ps1 — **10/10 passed 2026-06-23**
- [x] REL-07 nlp-svc 4 copilot tools (no fix needed)
- [x] REL-08 Evidence at specs/004-ai-first-v6/evidence/rv-02-launch-verify.txt

## Acceptance
`RESULT: 10 passed, 0 failed`

## Depends on
REL-STACK (optional — unit tests run without live stack)
```

---

### Issue 3 — REL-DEMO

**Title**: `[REL-DEMO] run-full-demo.ps1 20/20 checkpoints`

**Labels**: `release`, `P0`, `demo`

**Body**:

```markdown
## Summary
Live API demo verification including V6 checkpoints 17–20.

## Tasks
- [ ] REL-09 Run run-full-demo.ps1
- [ ] REL-10 CP17–20 pass (margin, tariff, CPM, chaos/war room)
- [ ] REL-11 Summary 20/20

## Command
.\scripts\run-full-demo.ps1 -ReportPath docs\demo-run-report-v6.txt

## Depends on
#1 REL-STACK
```

---

### Issue 4 — REL-TAG

**Title**: `[REL-TAG] Git tag v6.0.0 (T055)`

**Labels**: `release`, `P0`, `tag`

**Body**:

```markdown
## Summary
Complete T055 after live demo passes and stakeholder approves.

## Tasks
- [ ] REL-12 Stakeholder approval
- [ ] REL-13 `git tag -a v6.0.0`
- [ ] REL-14 Mark T055 in tasks.md
- [ ] REL-15–17 Notion + program table update

## Depends on
#3 REL-DEMO
```

---

### Issue 5 — P-DOC

**Title**: `[P-DOC] Speckit documentation sync`

**Labels**: `docs`, `P1`

**Body**:

```markdown
## Tasks
- [x] P-DOC-01–03, 05, 08 (005 spec, tracker, Notion note)
- [x] P-DOC-06 quickstart CP numbering
- [x] P-DOC-07 SPECKIT footnote
- [ ] P-DOC-04 SC-V6 live proven after demo
```

---

### Issue 6 — REL-PROD (optional)

**Title**: `[REL-PROD] k6 + Chaos evidence → READINESS 100/100`

**Labels**: `production`, `P2`, `performance`

**Body**:

```markdown
## Tasks
- [ ] REL-18 run-k6-200vu.ps1
- [ ] REL-19 r4-verify.ps1 (Chaos)
- [ ] REL-20 READINESS.md 100/100

## Depends on
#4 REL-TAG
```
