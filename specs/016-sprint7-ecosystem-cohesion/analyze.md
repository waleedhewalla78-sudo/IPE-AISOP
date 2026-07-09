# Cross-Artifact Analysis — IPE Program (015 + 016 + PRD)

**Date**: 2026-07-07  
**Analyzer**: `/speckit.analyze`  
**Constitution**: v1.2.3  
**Sources synthesized**:
- `ipe/.specify/memory/constitution.md` v1.2.3
- `ipe/docs/PRD-IPE-AUTHORITATIVE.md` (2026-07-07)
- `ipe/specs/015-enterprise-production-readiness/` (spec, plan, tasks, converge-phase3-close)
- `ipe/specs/016-sprint7-ecosystem-cohesion/` (spec, plan, tasks, clarify)
- `ipe/docs/qa/GATE-RESULTS-PHASE3.md`
- `ipe/READINESS.md`

---

## 1. Executive summary

| Dimension | Assessment |
|-----------|------------|
| **Constitution compliance** | ✅ Phases 0–2 closed; Phase 3 gates 6–10 PASS; Gate 11 partial |
| **PRD ↔ Spec 016 alignment** | ✅ High — Unified Workspace, EIB, activity feed documented in both |
| **Spec 016 ↔ Tasks coverage** | 🟡 Tier 1 **100%** (T701–T714); Tier 2 **0%**; integration wiring **partial** (T715+) |
| **Spec 015 ↔ Gate evidence** | 🟡 Tag `v9.4.0-p3` blocked on Gate 11 (12/14) |
| **Roadmap ↔ Executed program** | 🟡 Sprint 7 Tier 1 ahead of Phase 3 tag; acceptable per clarify CL-S7-07 |
| **Overall program status** | **Phase 2 complete** (`v9.3.0-p2`); **Phase 3 ~92%**; **Sprint 7 Tier 1 ~95%**; **Phase 4 0%** |

**Recommendation**: Complete Gate 11 remediation (or OQ-9 decision), apply migration 038 on live DB, finish R1 activity emitters (T715–T718), then tag `v9.4.0-p3` before Phase 4 GTM engineering.

---

## 2. Program phase map

| Track | Spec | Tag target | Status | Blocker |
|-------|------|------------|--------|---------|
| Enterprise P2 | 015 Phase 0–2 | `v9.3.0-p2` | ✅ Complete | — |
| Enterprise P3 | 015 Phase 3 | `v9.4.0-p3` | 🔄 92% | Gate 11 12/14 |
| Sprint 7 cohesion | 016 | `v9.5.0-s7` | 🔄 Tier 1 done | Service emitters + migration apply |
| Phase 4 GTM | 015 Phase 4 | `v10.0.0-e4` | ⬜ Not started | Requires `v9.4.0-p3` |
| Phase 5 maturity | 015 Phase 5 | TBD | ⬜ Proposed | Post-GTM |

---

## 3. Gate verification matrix (authoritative)

| Gate | Constitution VIII | tasks.md (015) | GATE-RESULTS | Evidence file | Status |
|------|-------------------|----------------|--------------|---------------|--------|
| 1 Observability | Pre-p2 | T081 ✅ | PASS | scripts | ✅ |
| 2 Security | Pre-p2 | T082 ✅ | PASS | verify-gate2 | ✅ |
| 3 Multi-tenant | Pre-p2 | T083 ✅ | PASS | verify-gate3 | ✅ |
| 4 Odoo sync | Pre-p2 | T084 ✅ | PASS | verify-gate4 | ✅ |
| 5 E2E R1+R2 | Pre-p2 | T085 ✅ | 14/14 + 5/5 | demo scripts | ✅ |
| 6 Helm lint | Pre-p3 | T150 ✅ | PASS | verify-gate6 | ✅ |
| 7 kind deploy | Pre-p3 | T151 ✅ | PASS | verify-k8s | ✅ |
| 8 Compose–K8s parity | Pre-p3 | T152 ✅ | PASS | gate8-parity.txt | ✅ |
| 9 HPA smoke | Pre-p3 | T165 ✅ | PASS | gate9-hpa.txt | ✅ |
| 10 ERP scaffolds | Pre-p3 | T153 ✅ | PASS | test_erp_scaffolds | ✅ |
| 11 R1 K8s demo | Pre-p3 | T166 🔄 | **12/14** | gate11-r1-k8s.txt | 🟡 PARTIAL |

**Gate 11 failures**: Step 10 OR-Tools schedule (300s timeout); Step 11 schedule approve (depends on 10).

---

## 4. Spec 016 coverage matrix

| Requirement | spec.md | plan.md | tasks.md | Code | Tests | UI |
|-------------|---------|---------|----------|------|-------|-----|
| FR-S7-01 Unified dashboard | ✅ | Phase B | T713 ✅ | unified_dashboard.py | ⬜ API test | UnifiedWorkspacePage ✅ |
| FR-S7-02 Activity feed | ✅ | Phase B | T710–T711 ✅ | activity.py | test_activity_eib ✅ | Workspace feed ✅ |
| FR-S7-03 EIB normalizer | ✅ | Phase A | T702–T703 ✅ | eib.py | 5 unit tests ✅ | — |
| FR-S7-03 Kafka consumer | ✅ | Phase B | T712 ✅ | eib_handler.py | ⬜ integration | — |
| FR-S7-03 Service emitters | clarify CL-S7-03 | Phase D | T715–T718 🔄 | emit.py + fea handler | 1 new test | — |
| FR-S7-04 Pattern discovery | ✅ Tier 2 | Phase C | T720 ⬜ | — | — | — |
| FR-S7-05 Anomaly alerting | ✅ Tier 2 | Phase C | T721 ⬜ | — | — | — |
| FR-S7-06 Role insights | ✅ Tier 2 | Phase C | T722 ⬜ | — | — | — |
| FR-S7-07 Command palette | ✅ Tier 3 | — | T723 ⬜ | — | — | — |
| FR-S7-08 Notification triage | ✅ Tier 3 | — | T724 ⬜ | — | — | — |
| Migration 038 RLS | ✅ | Phase A | T701 ✅ | 038_sprint7_activity_events.py | ⬜ migrate on live DB | — |
| Event audit script | ✅ | Phase A | T704 ✅ | audit-event-streams.ps1 | evidence/ | — |

---

## 5. Cross-artifact consistency findings

### 5.1 Aligned ✅

- Constitution IV (Kafka optional) ↔ spec 016 §3 Kafka-off POST path
- Constitution I (RLS) ↔ migration 038 `cdm_activity_event` policies
- PRD §9 Unified Workspace ↔ route `/workspace` + T714
- PRD §12 EIB ↔ `ipe_shared/events/eib.py` topic constants
- Gate scripts referenced in constitution ↔ GATE-RESULTS-PHASE3.md

### 5.2 Drift 🟡

| Issue | Artifacts | Resolution |
|-------|-----------|------------|
| mat-svc in R1 compose | Constitution V vs compose file | Task T732; OQ-8 |
| feature.json stale | `.specify/feature.json` says phase_3 not_started | Update to 92% + gate 11 partial |
| READINESS score 100 vs Gate 11 | READINESS.md vs GATE-RESULTS | READINESS is product completeness; gates are enterprise track |
| Odoo version | spec 013 (17) vs dev (19) | OQ-1 |

### 5.3 Gaps 🔴

| Gap | Severity | Task |
|-----|----------|------|
| Gate 11 14/14 | **P0** | T166-R1, OQ-9 |
| Migration 038 not applied on all envs | P1 | T730 |
| connector/cap/res activity emitters | P1 | T715–T717 |
| Tier 2 AI features | P2 | T720–T722 |
| UI route RBAC | P2 | Phase 5 / OQ-3 |

---

## 6. Test & evidence inventory

| Suite | Count | Status |
|-------|-------|--------|
| `test_activity_eib.py` | 5 | ✅ PASS |
| `audit-event-streams.ps1` | 7 checks | ✅ (offline) |
| Gate 11 K8s demo | 12/14 | 🟡 |
| R1 HTTPS demo (compose) | 14/14 | ✅ (prior) |
| k6 SLO + stress | PASS | ✅ (Phase 2) |

---

## 7. Constitution compliance checklist (016 implement)

| Principle | 016 status | Notes |
|-----------|------------|-------|
| I RLS | ✅ | Migration 038 |
| II Auth | ✅ | Activity POST requires planner/admin/manager |
| III Tests | ✅ | Unit tests on EIB + emit |
| IV Events | ✅ | Kafka consumer + direct ingest |
| V Service arch | ✅ | dpe-svc API layer |
| VI Observability | ✅ | Existing /metrics on dpe-svc |
| VII Release slicing | ✅ | Tier 2 does not block R1 |
| VIII Gates | 🟡 | Sprint 7 does not waive Gate 11 |

---

## 8. Recommended execution order

1. **T730** — `alembic upgrade head` (038) on compose + K8s DB
2. **T715–T718** — Wire activity emitters (connector, cap, res; fea ✅)
3. **T166-R1** — Gate 11 remediation (cap-svc CPU / cluster health)
4. **T157** — Tag `v9.4.0-p3` after 14/14 or OQ-9 waiver
5. **T720+** — Tier 2 stretch (post-tag)
6. **Phase 4** — Stripe, tenant API, developer portal (issues #25, #26)

---

*Analyze v1.0 — full program rollup 2026-07-07*
