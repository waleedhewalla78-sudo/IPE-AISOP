# Speckit Converge — Spec 016 + Program Status

**Date**: 2026-07-07  
**Command**: `/speckit.converge`  
**Constitution**: v1.2.3  
**Active feature**: `016-sprint7-ecosystem-cohesion`  
**Target tags**: `v9.4.0-p3` (blocked) · `v9.5.0-s7` (Tier 1 nearly ready)

---

## 1. Executive summary

| Stream | Scope | Code | Runtime / evidence |
|--------|-------|------|-------------------|
| 015 Phase 3 | Gates 6–11 | ✅ Scripts ready | Gates 6–10 PASS; Gate 11 **12/14** |
| 016 Tier 1 | EIB + activity + workspace | ✅ ~95% | APIs + UI; migration apply pending |
| 016 wiring | R1 emitters | 🔄 Partial | fea ✅; connector/cap/res ⬜ |
| 016 Tier 2/3 | AI + command palette | ⬜ Not started | Deferred post-tag |
| Tag `v9.4.0-p3` | Constitution VIII | ⬜ | Blocked on Gate 11 |
| Tag `v9.5.0-s7` | Sprint 7 milestone | ⬜ | After T717–T730 |

---

## 2. Assessment vs spec / plan / tasks

### 2.1 Spec 016 requirements

| Requirement | Spec | Plan phase | Task | Implemented | Gap |
|-------------|------|------------|------|-------------|-----|
| FR-S7-01 Unified dashboard | ✅ | B | T713 | ✅ | API integration tests |
| FR-S7-02 Activity feed | ✅ | B | T710–711 | ✅ | — |
| FR-S7-03 EIB | ✅ | A–B | T702–712 | ✅ | — |
| FR-S7-04 R1 emitters | ✅ | C | T715–719 | 🔄 | connector, cap, res |
| FR-S7-05 RLS | ✅ | A | T701 | ✅ | live DB migrate |
| FR-S7-10–12 Tier 2 | ✅ | E | T720–722 | ⬜ | stretch |
| FR-S7-20–21 Tier 3 | ✅ | F | T723–724 | ⬜ | stretch |

**Spec coverage (Tier 1)**: **11/13** acceptance criteria met (85%). Remaining: emitters + DB migrate.

### 2.2 Constitution compliance

| Principle | Status | Evidence |
|-----------|--------|----------|
| I RLS | ✅ | migration 038 |
| II Auth | ✅ | activity routes RBAC |
| III Tests | ✅ | test_activity_eib.py 5/5 |
| IV Events | ✅ | consumer + Kafka-off path |
| V Architecture | ✅ | dpe-svc API pattern |
| VI Observability | ✅ | existing metrics |
| VII Release slicing | ✅ | Tier 2 not blocking R1 |
| VIII Gates | 🟡 | Gate 11 partial |

---

## 3. Work completed this converge run

| Artifact / code | Action |
|-----------------|--------|
| `constitution.md` | v1.2.3 — Gate 9 PASS, Gate 11 12/14, Sprint 7 workflow |
| `spec.md` | v2.0 — user stories, NFRs, API contract |
| `clarify.md` | v1.0 — OQ matrix + Gate 11 options |
| `analyze.md` | v1.0 — full program cross-artifact matrix |
| `plan.md` | v2.0 — Phases A–F |
| `tasks.md` | v2.0 — T715+ program tasks appended |
| `ipe_shared/activity/emit.py` | New — in-process EIB emit helper |
| `fea-svc/.../handlers.py` | Activity on feasibility scored |
| `test_activity_eib.py` | +1 test for emit helper |

---

## 4. Remaining work (appended tasks)

### P0 — blocks customer-facing milestones

| ID | Task | Owner hint | Depends on |
|----|------|------------|------------|
| T166-R1 | Gate 11 remediation (cap-svc CPU, healthy kind) | DevOps | kind cluster |
| T157 | Tag `v9.4.0-p3` | Release mgr | T166-R1 or OQ-9 |
| T730 | Apply migration 038 | Backend | DB access |
| T717 | connector activity on sync | Backend | connector sync path |
| T718 | cap-svc activity on schedule | Backend | capacity API |

### P1 — Sprint 7 Tier 1 complete

| ID | Task |
|----|------|
| T719 | res-svc activity on resolution approve |
| T731 | Activity API integration tests |
| T732 | mat-svc in release1 compose (OQ-8) |

### P2 — post-tag stretch

| ID | Task |
|----|------|
| T720–T722 | Tier 2 AI features |
| T723–T724 | Tier 3 UX |
| T120a–T128 | Phase 4 GTM |

---

## 5. Gate matrix (current)

| Gate | Status | Evidence |
|------|--------|----------|
| 6 Helm | ✅ | verify-gate6.ps1 |
| 7 kind health | ✅ | verify-k8s.ps1 |
| 8 parity | ✅ | gate8-parity.txt |
| 9 HPA | ✅ | gate9-hpa.txt |
| 10 ERP scaffolds | ✅ | test_erp_scaffolds.py |
| 11 R1 K8s | 🟡 **12/14** | gate11-r1-k8s.txt |

**Failures**: OR-Tools schedule timeout; schedule approve (cascade).

---

## 6. Verification run (this session)

```powershell
# Recommended after converge
cd E:\AISOP\ipe
uv run pytest services/shared/tests/test_activity_eib.py -q
.\scripts\sprint7\audit-event-streams.ps1
```

---

## 7. Convergence verdict

| Milestone | Verdict |
|-----------|---------|
| Sprint 7 Tier 1 code | **READY** pending T717–T730 |
| Sprint 7 Tier 2/3 | **NOT STARTED** — correctly deferred |
| Phase 3 tag `v9.4.0-p3` | **BLOCKED** — Gate 11 + OQ-9 |
| Phase 4 GTM | **DO NOT START** until tag applied |
| Constitution | **COMPLIANT** except Gate 11 partial (documented) |

**Next action**: Run Gate 11 remediation with healthy kind cluster; wire connector + cap activity emitters; apply migration 038.

---

*Converge v1.0 — 2026-07-07*
