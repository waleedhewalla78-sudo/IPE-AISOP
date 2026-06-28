# Tasks: v8 Validation Convergence

**Input**: [plan.md](./plan.md), [spec.md](./spec.md), [analyze.md](./analyze.md)  
**Feature**: `010-v8-validation-convergence` | **Updated**: 2026-06-28  
**Live evidence**: Demo **32/32** · Integration **5/5** · Vitest **28/28** · dpe-svc **~180 tests**

---

## Phase V0 — Validation sprint (QA-001–010) ✅

| ID | Task | QA | Status |
|----|------|-----|--------|
| T001 | Run migrations 029–035 | QA-001 | ✅ |
| T002 | Start 7 v8 services + Kong health | QA-001 | ✅ |
| T003 | Fix CopilotPanel Vitest | QA-004 | ✅ |
| T004 | Mark nlp SageMaker/vLLM `@integration` | QA-006 | ✅ |
| T005 | Add `PROCUREMENT` to Role enum | QA-008 | ✅ |
| T006 | v8 API tests (7 services) | QA-005 | ✅ 26+ tests |
| T007 | `test_v8_e2e.py` integration | QA-003 | ✅ 5 tests |
| T008 | Demo CP21–30 in run-full-demo.ps1 | QA-002 | ✅ |
| T009 | Vitest v8 page smoke tests | QA-009 | ✅ |
| T010 | Update PRODUCT-STATUS v8.2.0 | QA-007 | ✅ |
| T011 | Stack smoke T014/T008/T009 | QA-010 | ✅ |
| T012 | Fix CP30 — User ORM for CopilotSession FK | — | ✅ |
| T013 | Fix migration 033 table names + apply | — | ✅ |
| T014 | Fix integration test demo user UUID | — | ✅ |
| T015 | nlp copilot session/agents API tests | — | ✅ |

---

## Phase V1 — Documentation sync ✅

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T016 | Create 010 spec/analyze/plan/tasks/converge | P0 | ✅ |
| T017 | Update `.specify/feature.json` → 010 | P0 | ✅ readiness 100 |
| T018 | Sync READINESS.md → v8.2.0 / 32/32 | P1 | ✅ |
| T019 | Update 005 analyze.md v8 rollup pointer | P1 | ✅ |
| T020 | Update 006 T014 → 32/32 demo | P2 | ✅ |
| T021 | Update 007/008/009 converge validation evidence | P2 | ✅ |
| T022 | Clarify PRODUCT-STATUS test counts | P2 | ✅ ~180 dpe-svc |

---

## Phase V2 — P1/P2 closure ✅

| ID | Task | Priority | Status | Evidence |
|----|------|----------|--------|----------|
| T023 | Seed supply network (DEF-001) | P1 | ✅ | migration 034, CP25 ≥4 facilities |
| T024 | Kong health wait script (DEF-004) | P1 | ✅ | `scripts/wait-for-healthy-stack.ps1` |
| T025 | Port map comment (DEF-005) | P1 | ✅ | `docker-compose.yml` header |
| T026 | Prophet/LSTM factory (GAP-001) | P2 | ✅ | `demand-svc/app/core/forecaster_factory.py` |
| T027 | sustain + quality demo CP31–32 (GAP-007) | P2 | ✅ | `docs/qa-e2e-demo-v8.2.0-closure.txt` |
| T028 | Playwright E2E foundation (GAP-008) | P2 | ✅ | `apps/web/e2e/*.spec.ts` |
| T029 | Production scaffolds (Keycloak, secrets, Stripe, ERP) | P3 | ✅ | `docs/DEPLOYMENT-READINESS-v8.2.0.md` |
| T030 | RLS legacy INSERT migration 035 | P3 | ✅ | `migrations/versions/035_*.py` |

---

## Phase V3 — Final closure (2026-06-28) ✅

| ID | Task | Priority | Status | Evidence |
|----|------|----------|--------|----------|
| T031 | Chaos C1–C6 re-run post-v8 (DEF-003) | P1 | ✅ | `docs/chaos/chaos-post-v8-output.txt` |
| T032 | Supply→demand Kafka feedback (GAP-002) | P2 | ✅ | `demand-svc/app/consumers/supply_feedback_consumer.py`, `test_supply_feedback_e2e.py` |
| T033 | RLS INSERT integration test | P2 | ✅ | `tests/integration/test_rls_insert_legacy.py` |
| T034 | PRODUCT-STATUS refresh | P1 | ✅ | `docs/PRODUCT-STATUS.md` |
| T035 | Full verification suite + git tag v8.2.0 | P0 | ✅ | `docs/qa/*`, tag `v8.2.0` |

---

## Phase POST — Enterprise (unchanged — POST-B)

| Phase | Tasks | Status |
|-------|-------|--------|
| POST-B Enterprise | Keycloak live activation | Scaffold ready |
| POST-B Secrets | AWS SM / Vault | Scaffold ready |
| POST-B Commercial | Stripe live, WCAG, Alertmanager | Out of scope v8.2.0 |

---

## Program rollup

| Feature | Tasks | Done | Open |
|---------|-------|------|------|
| 010-v8-validation-convergence | T001–T035 | 35 | 0 |
| POST-B production | — | — | Live infra only |
