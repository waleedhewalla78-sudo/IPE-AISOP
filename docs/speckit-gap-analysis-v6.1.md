# Speckit Gap Analysis — v6.1.0 Baseline

**Date:** 2026-06-26  
**Baseline:** tag `v6.1.0` @ `51f41ec`  
**Program rollup:** **158 / 162 built (97.5%)** · **4 open**

---

## Summary

The four unbuilt Speckit tasks are **not missing product features**. They are **002 release-gate hygiene** items (git evidence + cancelled RC tag) plus **documentation checkbox drift** in tracker files. All V6 code tasks (004 T001–T054) and 003 (45/45) are complete. T055 (v6.0.0 tag) is **done in git** but still `[ ]` in `specs/004-ai-first-v6/tasks.md`.

| Feature | Total | Done | Open | % |
|---------|-------|------|------|---|
| 002 Release gates | 62 | 58 | **4** | 94% |
| 003 Autonomous V5 | 45 | 45 | 0 | 100% |
| 004 AI-first V6 | 55 | 55* | 0* | 100%* |
| **Program** | **162** | **158** | **4** | **97.5%** |

*T055 tagged `v6.0.0`; checkbox not synced.

---

## Open Items (4)

### SG-01 — T049 [002] Test/env alignment commit

| Field | Value |
|-------|-------|
| **Spec** | `specs/002-release-stabilization-gates/tasks.md` T049 |
| **Class** | **Implementable now** (hygiene) |
| **Description** | Commit test/env fixes: align JWT env, contracts across services |
| **Files** | `services/*/tests/`, `scripts/`, `.env.template`, `.env.example` |
| **Effort** | 2–4 h |
| **Blocks v7.0.0?** | No (Speckit checkbox only) |
| **Remediation** | Stage remaining test/env deltas; single commit per 002 plan |

### SG-02 — T050 [002] Docs reconciliation commit

| Field | Value |
|-------|-------|
| **Spec** | `specs/002-release-stabilization-gates/tasks.md` T050 |
| **Class** | **Implementable now** |
| **Description** | Reconcile READINESS scores, phase status, RELEASE_NOTES across specs |
| **Files** | `READINESS.md`, `specs/005-ipe-program-status/spec.md`, `RELEASE_NOTES.md`, `AGENTS.md` |
| **Effort** | 2 h |
| **Blocks v7.0.0?** | No |
| **Remediation** | Sync 97→100 readiness after P6–P11; mark T055 `[x]` in 004 tasks |

### SG-03 — T051 [002] Gate evidence structure commit

| Field | Value |
|-------|-------|
| **Spec** | `specs/002-release-stabilization-gates/tasks.md` T051 |
| **Class** | **Implementable now** |
| **Description** | Commit gate evidence folders + contract checklists under 002 |
| **Files** | `specs/002-release-stabilization-gates/evidence/`, `contracts/` |
| **Effort** | 1 h |
| **Remediation** | Link Wave 2A–3 evidence (`docs/k6-*`, `docs/chaos/`, `docs/wave3-regression.md`) from gate-2 README |

### SG-04 — T053 [002] Cancel v1.0.0-rc1 tag task

| Field | Value |
|-------|-------|
| **Spec** | `specs/002-release-stabilization-gates/tasks.md` T053 |
| **Class** | **Deprioritized** (superseded by v1.0.0 + v6.x tags) |
| **Description** | Create `v1.0.0-rc1` on Gate 2 green SHA |
| **Action** | Mark **cancelled** in tasks.md; no git tag needed |
| **Effort** | 5 min |
| **Blocks v7.0.0?** | No |

---

## Additional Tracker Drift (not counted in 162)

| ID | Status | Action |
|----|--------|--------|
| P-DOC-04 | Open in `tasks-release.md` | Mark SC-V6 live proven (20/20 + chaos verified) |
| REL-02–05 | Open in `tasks-release.md` | Mark complete (stack proven Wave 3) |
| W3-01–05 | Open in `005/tasks.md` | Mark complete (v6.1.0 tagged) |
| T055 checkbox | Open in `004/tasks.md` | Mark `[x]` — tag exists |
| POST-A/B/C/D | Open | **Post-v7 backlog** — not Speckit 162 |

---

## Blocked / Out of Scope for 162/162

| Item | ID | Reason |
|------|-----|--------|
| Keycloak live IdP | FR-P-13 / C-007 | No Azure AD/Okta sandbox |
| SAP/D365 live ERP | POST-B2/B3 | Customer ERP required |
| Stripe / mobile / WCAG | POST-D | Product scope v8+ |

---

## Path to 162/162 + 100/100 Readiness

| Step | Action | Outcome |
|------|--------|---------|
| P6-01 | Close T049 (env/test commit) | 159/162 |
| P6-02 | Close T050 (docs sync) | 160/162 |
| P6-03 | Close T051 (evidence links) | 161/162 |
| P6-04 | Cancel T053 + update tasks.md | **162/162** |
| P6-05 | Sync T055, P-DOC-04, W3, REL checkboxes | Readiness **100/100** (process) |

**Estimated effort:** 1 day (no net-new features).

---

## References

- `specs/005-ipe-program-status/spec.md` L175–176
- `specs/002-release-stabilization-gates/tasks.md` T049–T053
- `specs/004-ai-first-v6/tasks.md` T055
- `.specify/feature.json`
