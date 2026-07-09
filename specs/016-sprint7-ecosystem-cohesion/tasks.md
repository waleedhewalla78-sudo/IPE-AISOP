# Tasks: Sprint 7 Ecosystem Cohesion + Program Close-Out

**Version**: 2.0 | **Date**: 2026-07-07

---

## Sprint 7 — Tier 1 foundation

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T701 | Migration 038 — `cdm_activity_event` + RLS | P0 | ✅ |
| T702 | ActivityEvent schema + EIB normalizer | P0 | ✅ |
| T703 | EIB topic constants | P0 | ✅ |
| T704 | Event stream audit script | P0 | ✅ |
| T710 | Activity feed GET API | P0 | ✅ |
| T711 | Activity ingest POST API | P0 | ✅ |
| T712 | EIB Kafka consumer (dpe-svc) | P1 | ✅ |
| T713 | Unified dashboard GET API | P0 | ✅ |
| T714 | Unified Workspace UI page | P0 | ✅ |

## Sprint 7 — Integration wiring

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T715 | `ipe_shared/activity/emit.py` helper | P0 | ✅ |
| T716 | fea-svc emit on feasibility scored | P0 | ✅ |
| T717 | connector emit on Odoo sync completed | P0 | ✅ |
| T718 | cap-svc emit on schedule created | P0 | ✅ |
| T719 | res-svc emit on resolution approved | P1 | ✅ |
| T730 | Apply migration 038 (compose + K8s) | P0 | ⬜ |
| T731 | Activity API integration tests (`test_activity_api.py`) | P1 | ⬜ |
| T732 | Reconcile mat-svc in release1 compose (OQ-8) | P1 | ⬜ |

## Sprint 7 — Tier 2 stretch

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T720 | Pattern discovery engine (3 types) | P2 | ⬜ |
| T721 | Anomaly alerting framework | P2 | ⬜ |
| T722 | Role-based insight templates | P2 | ⬜ |

## Sprint 7 — Tier 3 UX

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T723 | Contextual command palette | P3 | ⬜ |
| T724 | Intelligent notification triage | P3 | ⬜ |

## Program 015 — Phase 3 gate close-out

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T166 | Gate 11 R1 K8s demo script | P0 | 🔄 12/14 |
| T166-R1 | Gate 11 remediation — cap-svc CPU / cluster recovery | P0 | ⬜ |
| T157 | Tag `v9.4.0-p3` (Constitution VIII) | P0 | ⬜ blocked |
| T169 | Kafka-optional health probes | P0 | ✅ |

## Program 015 — Phase 4 prep (post-tag)

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T120a | Stripe sandbox billing flow | P1 | ⬜ |
| T125 | Tenant self-service API | P1 | ⬜ |
| T128 | Developer portal scaffold | P2 | ⬜ |

---

## Definition of done — Sprint 7 Tier 1

- [x] Migration 038 merged
- [x] Activity + unified dashboard APIs
- [x] Unified Workspace UI at `/workspace`
- [x] EIB unit tests PASS (5/5)
- [ ] All R1 emitters wired (T717–T719)
- [ ] Migration 038 applied on target DBs (T730)
- [ ] `audit-event-streams.ps1` exit 0 on live stack

## Definition of done — `v9.4.0-p3`

- [x] Gates 6–10 PASS
- [ ] Gate 11 **14/14** PASS (or OQ-9 waiver documented)
- [ ] `docs/qa/GATE-RESULTS-PHASE3.md` updated
- [ ] Constitution v1.2.3 Principle VIII reflects final gate state

---

*Tasks v2.0 — `/speckit.tasks` 2026-07-07*
