# Clarification Record — Spec 016 Sprint 7 Ecosystem Cohesion

**Date**: 2026-07-07  
**Command**: `/speckit.clarify`  
**Constitution**: v1.2.3  
**Product reference**: `docs/PRD-IPE-AUTHORITATIVE.md` §1.6 (OQ-*)

---

## 1. Purpose

Resolve underspecified areas before Tier 2 engineering and Phase 3 tag close-out. Decisions marked **DECIDED** are binding for `/speckit.plan` and `/speckit.tasks`. Items marked **OPEN** require stakeholder sign-off.

---

## 2. Sprint 7 scope clarifications

| ID | Question | Resolution | Status |
|----|----------|------------|--------|
| CL-S7-01 | Where does the activity store live? | **dpe-svc** API + shared `cdm_activity_event` table; no new microservice in Sprint 7 | DECIDED |
| CL-S7-02 | Kafka-off (R1) activity path? | Services MAY POST `/api/v1/activity/events` OR call `record_activity_event` in-process when sharing DB session (Constitution IV) | DECIDED |
| CL-S7-03 | Which tools must emit events for Tier 1 "done"? | **connector** (sync), **fea-svc** (score), **cap-svc** (schedule), **res-svc** (resolution approve) — minimum R1 quartet | DECIDED |
| CL-S7-04 | Unified dashboard data sources? | Aggregate existing dpe/fea KPIs + `cdm_activity_event` feed; no new OLAP store | DECIDED |
| CL-S7-05 | Default landing route? | `/workspace` (Unified Workspace) for release1 and full profiles | DECIDED |
| CL-S7-06 | Tier 2 pattern discovery input? | Activity stream + existing MO/feasibility tables; batch job in dpe-svc, not real-time ML | DECIDED |
| CL-S7-07 | Email ↔ PM sync (roadmap §3)? | **Deferred Sprint 8** — requires Microsoft Graph / Google Workspace partner APIs | DECIDED |
| CL-S7-08 | Activity retention policy? | Follow `ipe_shared/retention` defaults; audit_log 7yr; activity events inherit **2yr** until OQ-6 formal policy | PROVISIONAL |

---

## 3. Program-level open questions (from PRD)

| ID | Topic | Recommendation | Impact if unresolved | Status |
|----|-------|----------------|----------------------|--------|
| OQ-1 | Odoo 17 vs 19 canonical for R1 | **Odoo 17** for customer SOW; 19 allowed in dev with mapper version flag | Field mapping drift in install guide | OPEN |
| OQ-2 | Demo SQL overlay vs Odoo-only truth | **Odoo wins** on master data (Constitution VII); SQL seed for dev/K8s gates only | Customer data trust | DECIDED (constitution) |
| OQ-3 | UI route-level RBAC | Enforce in **Phase 5** (spec 015 Stream C); Sprint 7 does not block on this | Unauthorized UI access | OPEN — deferred |
| OQ-4 | When to tag v8.2.0 | Separate from enterprise track; tag when CHANGELOG + READINESS reconciled | Marketing version confusion | OPEN |
| OQ-5 | MAPE / triage baseline study | Instrument in ROI dashboard (013); no gate blocker | Success metrics unmeasured | OPEN |
| OQ-6 | Copilot / activity retention GDPR | Apply retention service to `cdm_activity_event` in Phase 5 | Compliance gap | OPEN |
| OQ-7 | R1 pricing $18K–30K/yr | Commercial sign-off required before SOW | Sales misalignment | OPEN |
| OQ-8 | mat-svc in R1 compose | **Include mat-svc** — Constitution V is canonical; reconcile `docker-compose.release1.yml` | Deploy doc drift | OPEN — action T732 |
| OQ-9 | Gate 11 **12/14** vs **14/14** for `v9.4.0-p3` | **Default: 14/14** per Constitution VIII; waiver requires written stakeholder exception referencing cap-svc kind CPU limits | Tag policy | OPEN — blocking |

---

## 4. Gate 11 remediation options (OQ-9)

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| A | Increase cap-svc CPU/memory in kind Helm values; re-run `verify-gate11.ps1` | Clean 14/14 evidence | Requires healthy cluster |
| B | Port-forward directly to cap-svc (bypass ingress timeout) | Faster solver path | Evidence not ingress-realistic |
| C | Stakeholder waiver: accept 12/14 with documented OR-Tools kind limitation | Unblocks tag | Violates strict Constitution VIII |
| D | Mock schedule step in gate script for kind-only profile | Artificial PASS | Not recommended |

**Recommended path**: Option A first; if still timeout after 2 runs, escalate Option C with amendment to Constitution VIII PATCH.

---

## 5. Assumptions validated

| Assumption | Validated by |
|------------|--------------|
| R1 profile has Kafka disabled | `IPE_KAFKA_BOOTSTRAP_SERVERS=""` in compose + Helm |
| Activity table needs RLS | Migration 038 + constitution Principle I |
| EIB normalizer handles `ipe.*` topics | `test_activity_eib.py` (5 tests) |
| Unified Workspace consumes live API | `UnifiedWorkspacePage.tsx` + `/dashboard/unified` |

---

## 6. Next decisions required (stakeholder)

1. **OQ-9** — Gate 11 waiver or remediation budget (blocks `v9.4.0-p3`)
2. **OQ-1** — Odoo version for Star Trans install guide
3. **OQ-8** — Confirm mat-svc in customer compose file

---

*Clarify v1.0 — Sprint 7 kickoff 2026-07-07*
