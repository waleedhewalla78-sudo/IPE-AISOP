# Speckit Converge — Spec 017 First Release Plan

**Date**: 2026-07-10  
**Constitution**: v1.2.4  
**Tag**: `v9.4.0-p3` @ `4629119` · HEAD `ad494e0`

---

## 1. Verdict

| Stream | Spec | Code | Tests | Issues |
|--------|------|------|-------|--------|
| Phase 0 | ✅ | ✅ | 20/20 + gates | Closed |
| Phase 1 UAT | ✅ spec | ⬜ | — | Commercial block |
| Wave 1 Copilot | ✅ | ✅ | 12/12 | #30 closed |
| Wave 1 Odoo/OTD | ✅ | ⬜ | — | #31–#36 open |
| Wave 2–3 | ✅ | ⬜ | — | #37–#46 open |
| Carry-over | ✅ | partial | — | T731/T732 |

**Phase 0: 100%** · **Wave 1: 25%** · **Phase 1: 0%** · **Program: ~35%**

**Phase 0 UAT verdict**: **PASS**  
**Program verdict**: **PROCEED Wave 1** — escalate Phase 1 commercial in parallel

---

## 2. Constitution checklist

| Principle | Status |
|-----------|--------|
| I RLS | ✅ 038 applied |
| II Auth | ✅ Copilot protected + 401 |
| III Tests | ✅ emitters + smoke |
| IV Events | ✅ R1 Kafka optional |
| V API | ✅ R1 deploy set |
| VI Observability | ✅ Gates 1, 6–7 |
| VII Customer-first | 🟡 Phase 1 Arabic pending |
| VIII Gates | ✅ OQ-9 satisfied |

---

## 3. Closed this converge

| ID | Was | Now |
|----|-----|-----|
| C-01 #30 Copilot smoke | Open | ✅ 12/12 |
| C-02 T730 | Open | ✅ Applied |
| C-03 OQ-9 | Open | ✅ §6 template |
| C-04 #27 | Open | ✅ WON'T FIX infra |
| C-05 Tag | Open | ✅ v9.4.0-p3 |
| C-07 GATE-RESULTS | Open | ✅ Updated |

---

## 4. Appended tasks (converge — new)

| ID | Task | Priority | Issue |
|----|------|----------|-------|
| C-08 | Push 6 commits to origin | P0 | — |
| C-09 | Restabilize kind cluster | P0 | ops |
| C-10 | Update `wave1-readiness.md` | P2 | ✅ Done 2026-07-10 |
| C-11 | Regenerate UAT docx from corrections | P2 | — |
| C-12 | OQ-9 stakeholder names | P2 | #28 |
| C-13 | T731 activity API integration tests | P1 | — |
| C-14 | T732 mat-svc release1 compose | P1 | OQ-8 |
| C-15 | FR-R1-05 stock.quant (Phase 1) | P0 | new |
| C-16 | FR-R1-16 OTD baseline API (Phase 1) | P0 | overlaps #35 |

---

## 5. Next action

1. `git push origin master`
2. **W1-03** Odoo Config v2 ([#31](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/31))
3. Escalate Phase 1 SOW + Odoo staging

---

*Converge v2.0 — `/speckit.converge` 2026-07-10*
