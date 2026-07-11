# Clarifications — Spec 023 Sprint 4 Wave 1

**Date:** 2026-07-11  
**Method:** Full ambiguity scan against constitution 1.2.8 + `tasks/sprint4-todo.md` + Spec 017 Wave 1 + Spec 022 residuals.  
**Mode:** Non-interactive (pipeline: do not stop for approval). Answers encoded into `spec.md` Clarifications table.

---

## Coverage map

| Category | Status | Notes |
|----------|--------|-------|
| Functional scope | Clear | Groups A (Odoo Config) + B (OTD) + Closure docs |
| Out of scope | Clear | COM blockers, Wave 2/3, nexus-social |
| Personas | Clear | Admin (config), Manager (OTD), Program owner (status) |
| Data model | Clear | Migration 050 + existing 039 OTD snapshot |
| Auth/RBAC | Clear | Admin for mutations; tenant_ctx required |
| Encryption | Clear | Fernet + `IPE_ENCRYPTION_KEY` |
| Live Odoo | Clear | Unit tests mock; PH1-02 stays COM SKIP |
| #70–#72 | Partial | Best-effort; honesty if incomplete |
| Performance | Clear | Test-connection ~5s target |
| i18n | Clear | EN+AR keys; G-R2-04 still COM |

---

## Questions answered (≤5)

### Q1 — Relationship to Spec 017?
**Decision:** Spec 023 is the Speckit vehicle to **finish** Spec 017 W1-03..W1-08 engineering. Do not recreate 017. Update 017 status rows when SC-005 met.

### Q2 — Must #70–#72 close in this sprint?
**Decision:** Attempt during implement (seed queue, write-back route doc/fix, re-validate). If Docker/COM blocks, leave GitHub issues OPEN with Spec 023 comment — do not fake PASS.

### Q3 — Multi-entity Odoo (W1-05) depth?
**Decision:** Support multiple stored connections; enforce **one active** Odoo per tenant via partial unique index. Full config versioning/rollback API is nice-to-have; audit log satisfies MVP versioning trail for Wave 1.

### Q4 — Sync-now semantics?
**Decision:** `POST .../sync-now` invokes existing connector sync for the connection (or queues same path). No new Kafka topic required for R1 profile (`IPE_KAFKA_BOOTSTRAP_SERVERS` may be empty).

### Q5 — OTD already marked done in 017?
**Decision:** Prior W1-07/08 baseline exists; Spec 023 still requires aggregator polish, tests, dashboard/i18n/nav completion per `sprint4-todo.md` Group B — mark DONE only after B tasks verified.

---

## Residual risks (accepted)

- Parallel Sprint 4 agent may race on same WIP files — Speckit artifacts are source of intent; merge carefully.
- Downloads `SPRINT4-*-PROMPT.md` unavailable this run — scope taken from `ipe/tasks/sprint4-todo.md` + Spec 017 + WIP comments.
