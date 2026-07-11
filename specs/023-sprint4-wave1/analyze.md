# Cross-Artifact Analysis — Spec 023 + Whole Project Status

**Date:** 2026-07-11  
**Constitution:** 1.2.8  
**Active feature:** `ipe/specs/023-sprint4-wave1`  
**Sources:** constitution, PRODUCT-STATUS, Specs 017/020/021/022/023, open GH issues, WIP tree

---

## 1. Executive verdict

| Dimension | Assessment |
|-----------|------------|
| Spec 022 eng | **COMPLETE** (smoke 15/15; validate residuals #70–#72 OPEN) |
| Spec 023 scope | **Clear** — Odoo Config v2 + OTD polish; COM out of scope |
| Constitution | **1.2.8** PATCH — 023 active; honesty rule intact |
| Wave 1 eng | **In progress** — substantial WIP already in working tree |
| Commercial | **OPEN** — OQ-7, OQ-1, PH1-02, G-R2-04, OQ-9 signatures |
| Consistency (pre-tasks) | Spec ↔ clarify aligned; plan/tasks filled next then refreshed below |

**Proceed with plan → tasks → implement on engineering track. Do not close COM items.**

---

## 2. Whole project status (detailed)

### 2.1 Speckit feature timeline

| Spec | Status | Evidence |
|------|--------|----------|
| 015 Enterprise | Phase 3 tag `v9.4.0-p3` | Gates 6–10 PASS; Gate 11 12/14 + OQ-9 waiver |
| 016 Sprint 7 | DONE | Emitters T717–719; migration 038 |
| 017 First release | Phase 0 DONE; Wave 1 partial→023 | W1-01/02 DONE; W1-03..08 via 023 |
| 018 R2 | Eng gates PASS; G-R2-04 HOLD | `v9.1.1-r2` not cut |
| 019 Converge | DONE | |
| 020 Planning intel | ENG COMPLETE | Migrations 044–049 |
| 021 Release closure | ENG COMPLETE | `v9.2.0-planning` @ b04434d |
| 022 Sprint 3 golive | ENG COMPLETE | Deploy/validate/smoke/docs; #70–72 residual |
| **023 Sprint 4 W1** | **ACTIVE** | This feature |

### 2.2 Release / tag policy

| Tag | Status |
|-----|--------|
| v9.2.0-planning | APPLIED |
| v9.4.0-p3 | RELEASED |
| v9.1.1-r2 | **HOLD** (G-R2-04) |
| v9.1.0-r2 | STALE — **never push** |

### 2.3 Open GitHub (non-exhaustive)

| Issues | Meaning |
|--------|---------|
| #50 | Commercial blockers umbrella — KEEP OPEN |
| #70–#72 | Spec 022 converge residuals |
| #37–#38, #42–#46 | Wave 2/3 defer — out of 023 scope |
| #15–#26 | Enterprise backlog — out of 023 scope |

### 2.4 Commercial OPEN (MUST remain)

| Item | Owner | Blocks |
|------|-------|--------|
| OQ-7 pricing | Waleed | SOW send |
| OQ-1 Odoo 17 vs 19 | Customer IT | Version confirm only (connector dual) |
| PH1-01 SOW send | COM | Depends OQ-7 |
| PH1-02 Odoo staging | Ops/IT | Live sync UAT |
| G-R2-04 Arabic native QA | Native reviewer | `v9.1.1-r2` |
| OQ-9 Gate 11 signatures | Waleed | Human sign section |

### 2.5 WIP already present (023 implement should finish, not rewrite)

- Migration `050_erp_connections.py`, models, Fernet crypto, ERP API/service/schemas/tests
- `OdooConnectionsPage.tsx` + `erpConnectionsApi.ts`
- `otd_aggregator.py` + OTD API/dashboard/i18n edits
- Env templates mention `IPE_ENCRYPTION_KEY`
- Checklist: `ipe/tasks/sprint4-todo.md`

---

## 3. Constitution compliance (023)

| Principle | Risk | Mitigation |
|-----------|------|------------|
| I RLS | New tables | Migration 050 `_rls()` |
| II Auth | Open APIs | `require_roles(["admin"])` on mutations |
| III Tests | Behavior change | `test_erp_connections.py`, `test_otd_analytics.py` |
| V Ports/routes | Router register | connector `router.py` includes erp_connections |
| VI Sync obs | Test/sync logs | `cdm_erp_connection_log` |
| VII Honesty | Fake COM | FR-010 / US-3 |
| Secrets | Password in git | Encrypted column; env key only |

**Gate:** PASS for planning.

---

## 4. Spec ↔ Plan ↔ Tasks consistency

*(Refreshed after `/speckit.tasks`)*

| Check | Result |
|-------|--------|
| Every FR mapped to ≥1 task | PASS (see tasks.md T001+) |
| US-1 → Group A tasks | PASS |
| US-2 → Group B tasks | PASS |
| US-3 → Closure tasks | PASS |
| US-4 → optional residual tasks | PASS (T-R1..) |
| COM tasks not auto-complete | PASS (HUMAN section) |
| No Wave 2/3 in 023 tasks | PASS |
| Duplicates vs #31–#36 (017) | Prefer close/comment 017 issues when 023 supersedes |

---

## 5. Coverage gaps / remediation

| Gap | Severity | Action |
|-----|----------|--------|
| Downloads Sprint4 prompts missing | Low | Used `tasks/sprint4-todo.md` |
| #70–#72 may remain | Med | Best-effort; honest OPEN |
| KMS key file diffs in dpe-svc | Low | Do not commit churn unless intentional |
| Root `.specify/feature.json` vs ipe path | Med | Point active feature to `ipe/specs/023-sprint4-wave1` |

---

## 6. Recommendation

Execute `/speckit.plan` → `/speckit.tasks` → `/speckit.taskstoissues` → `/speckit.implement` → `/speckit.converge` on Spec 023 engineering only.
