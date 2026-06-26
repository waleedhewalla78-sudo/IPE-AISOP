# Tasks: IPE V6.0 — Release Verification & Post-Release

**Input**: [plan.md](./plan.md), [../005-ipe-program-status/plan.md](../005-ipe-program-status/plan.md), [clarify-v6.md](./clarify-v6.md), [analyze-v6.md](./analyze-v6.md)

**Branch**: `004-ai-first-v6`

**Prerequisite**: [tasks.md](./tasks.md) T001–T054 ✅ complete

**Format**: `- [ ] ID [P?] [Phase] Description — acceptance criteria`

**Critical path**: REL-01 → REL-04 → REL-05 → REL-07 → REL-08 → REL-10 → REL-11 → REL-13 (T055)

---

## Phase P-DOC — Documentation Sync (parallel, non-blocking)

- [x] P-DOC-01 [P1] [P-DOC] Fix stale **15/55** header in `specs/005-ipe-program-status/spec.md` L139 — table shows **54/55**, V6-R2–R5 ✅
- [x] P-DOC-02 [P1] [P-DOC] Fix mermaid `F004[004 V6 15/55]` → `54/55` in `specs/005-ipe-program-status/spec.md` L180
- [x] P-DOC-03 [P1] [P-DOC] Refresh V6-R2–R5 rows in `specs/004-ai-first-v6/implementation-tracker.md` — all ✅ Done, not ⬜ To Do
- [x] P-DOC-04 [P1] [P-DOC] After REL-10 passes, mark SC-V6-01–08 **Proven (live)** in `implementation-tracker.md` + `analyze-v6.md`
- [x] P-DOC-05 [P2] [P-DOC] Mark Notion sync ✅ in `specs/005-ipe-program-status/spec.md` Notion table
- [x] P-DOC-06 [P2] [P-DOC] Add note in `specs/004-ai-first-v6/quickstart.md`: demo **CP15** = 003 **checkpoint 16** (persist-after-approve)
- [x] P-DOC-07 [P2] [P-DOC] Add V6 drift footnote to `specs/SPECKIT-CHECKLIST.md` summary dashboard
- [x] P-DOC-08 [P1] [P-DOC] Label **92/100** as historical post-003; **96/100** as current in `005/spec.md` readiness table

**Exit gate**: analyze X-02, X-03, X-08 resolved (zero HIGH doc drift).

---

## Phase REL-STACK — Stack & Infrastructure (blocks tag)

**Depends on**: Docker Desktop, `ipe/.env` from `.env.template`

- [x] REL-01 [P0] [REL-STACK] Run `docker compose config` in `ipe/infrastructure/docker/docker-compose.yml` — exit 0, no duplicate service keys
- [x] REL-02 [P0] [REL-STACK] Run `docker compose up -d` — all dependent services healthy within 5 min
- [x] REL-03 [P0] [REL-STACK] Verify `GET http://localhost:8000/health` returns 200 and web UI @ `:8082` loads login
- [x] REL-04 [P0] [REL-STACK] Confirm Alembic head includes migration **028** on demo DB
- [x] REL-05 [P0] [REL-STACK] Run `ipe/scripts/seed-demo-client.ps1` — demo tenant + V6 tariff/activity/telemetry seed present

**Exit gate**: API reachable; seed complete; migrations 024–027 applied.

**Commands**:

```powershell
cd D:\AISOP\ipe\infrastructure\docker
docker compose config
docker compose up -d
cd ..\..
.\scripts\seed-demo-client.ps1
```

---

## Phase REL-TEST — Backend Verification (blocks tag)

**Depends on**: REL-STACK complete

- [x] REL-06 [P0] [REL-TEST] Run `ipe/scripts/launch-verify.ps1` — **10/10** services pass (0 failed)
- [x] REL-07 [P0] [REL-TEST] If nlp-svc fails: fix `services/nlp-svc/tests/test_copilot_tools.py` — assert **4 tools** incl. `get_war_room_recovery` in `app/core/copilot_tools.py`
- [x] REL-08 [P0] [REL-TEST] Save console output to `specs/004-ai-first-v6/evidence/rv-02-launch-verify.txt`

**Services under test**: shared, cap-svc, dpe-svc, fea-svc, connector, nlp-svc, mat-svc, res-svc, del-svc, alert-svc

**Exit gate**: `RESULT: 10 passed, 0 failed` in launch-verify summary.

---

## Phase REL-DEMO — Live Demo (blocks tag)

**Depends on**: REL-TEST complete

- [x] REL-09 [P0] [REL-DEMO] Run `ipe/scripts/run-full-demo.ps1 -ReportPath docs/demo-run-report-v6.txt`
- [x] REL-10 [P0] [REL-DEMO] Verify V6 checkpoints **17–20** pass
- [x] REL-11 [P0] [REL-DEMO] Confirm script summary **20/20 passed**

**Exit gate**: `docs/demo-run-report-v6.txt` shows 20/20; SC-V6-01–06 live proven.

---

## Phase REL-TAG — Release v6.0.0 (T055)

**Depends on**: REL-DEMO complete + stakeholder approval (clarify C-V6-09)

- [x] REL-12 [P0] [REL-TAG] Stakeholder approval → tag **v6.0.0**
- [x] REL-13 [P0] [REL-TAG] Annotated tag on `a203e68`
- [x] REL-14 [P0] [REL-TAG] T055 marked in `tasks.md`
- [x] REL-15 [P1] [REL-TAG] READINESS + RELEASE_NOTES updated
- [ ] REL-16 [P1] [REL-TAG] Update Notion (optional)
- [x] REL-17 [P1] [REL-TAG] Program table **55/55** on 004

**Exit gate**: Tag exists locally; program **158/162** tasks; 004 **55/55** complete.

---

## Phase REL-PROD — Production 100/100

**Depends on**: REL-TAG complete

- [x] REL-18 [P2] [REL-PROD] k6 smoke + 10 VU + 200 VU — `docs/k6-summary.md`
- [x] REL-19 [P2] [REL-PROD] Chaos C1–C6 — `docs/chaos/chaos-summary.md`
- [x] REL-20 [P2] [REL-PROD] Coverage ≥60% cap/mat/dpe — `docs/coverage-summary.md`
- [x] REL-21 [P2] [REL-PROD] Add `docker-compose.monitoring.yml` overlay
- [x] REL-22 [P2] [REL-PROD] Prometheus + Loki + Grafana configs under `infrastructure/monitoring/`
- [x] REL-23 [P2] [REL-PROD] `scripts/run-monitoring-stack.ps1` + `docs/ops-monitoring.md`
- [x] REL-24 [P2] [REL-PROD] Live verify monitoring stack — `docs/ops-monitoring-verify.txt`

**Exit gate**: k6 + chaos + coverage + ops evidence attached; audit ~91/100.

---

## Phase G-002 — Git Hygiene (optional, parallel)

- [ ] G-002-01 [P2] [G-002] Close or cancel `specs/002-release-stabilization-gates/tasks.md` **T053** (v1.0.0-rc1 superseded)
- [ ] G-002-02 [P2] [G-002] Optional commits for T049–T051 per 002 plan (test/env, docs, evidence)

---

## Summary

| Phase | Task IDs | Count | Blocks tag |
|-------|----------|-------|------------|
| P-DOC | P-DOC-01–08 | 8 | No |
| REL-STACK | REL-01–05 | 5 | **Yes** |
| REL-TEST | REL-06–08 | 3 | **Yes** |
| REL-DEMO | REL-09–11 | 3 | **Yes** |
| REL-TAG | REL-12–17 | 6 | **Yes** (T055) |
| REL-PROD | REL-18–24 | 7 | No |
| **Total open** | | **4** | |

**Testing track**: [tasks-testing.md](./tasks-testing.md) — TEST-01–09 (unit, integration, UI, k6, chaos)

---

## Dependency Graph

```text
P-DOC-* (parallel)
REL-01 → REL-02 → REL-03 → REL-04 → REL-05
  → REL-06 → REL-07? → REL-08
  → REL-09 → REL-10 → REL-11
  → REL-12 → REL-13 → REL-14–17 (T055)
  → REL-18–20 (optional 100/100)
G-002-* (parallel)
```

---

## Link to T055

| Main task | Release tasks |
|-----------|---------------|
| **T055** Tag v6.0.0 | REL-12 through REL-14 (minimum) |

T055 in [tasks.md](./tasks.md) remains open until REL-13 + REL-14 complete.

**Next**: `/speckit.implement` starting REL-01.
