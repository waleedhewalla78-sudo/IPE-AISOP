# Cross-Artifact Analysis — Spec 015 Enterprise Production Readiness

**Date**: 2026-07-05  
**Analyzer**: `/speckit.analyze` (refresh)  
**Sources synthesized**:
- `IPE_Enterprise_Deployment_Roadmap (4).md` (36-week Phases 0–4)
- `PHASE3-VERIFICATION-PROMPT (3).md`
- `IPE-Phase4-Proposal (1).docx`
- `IPE-Phase5-Proposal-Gap-Audit.docx`
- `IPE_v8.2.0_Gap_Closure_Action_Plan (5).md`
- `IPE_v8_Upgrade_Proposal_SAP_Gap_Analysis (4).md` — Tier 1–3 → Phase 5 Stream B
- Repo artifacts: constitution v1.2.2, spec v1.3, plan v2.1, tasks v2.3, `docs/qa/GATE-RESULTS-PHASE3.md`

---

## 1. Executive summary

| Dimension | Assessment |
|-----------|------------|
| **Constitution compliance** | ✅ Phases 0–2 align with Principles I–VIII; Phase 3 gate discipline active |
| **Spec ↔ Plan alignment** | ✅ High — same phase map, gate numbering, tech stack |
| **Spec ↔ Tasks coverage** | 🟡 Phase 3 gates 6–7, 10 PASS; 8–9, 11 pending; Phase 4/5 tasks incomplete |
| **Roadmap ↔ Executed program** | 🟡 Naming mismatch documented; many roadmap “gaps” already closed in v9.3.0-p2 |
| **Phase 4 proposal ↔ Spec** | ✅ FR-015-40–45 map 1:1 to T120a–T128 |
| **Phase 5 proposal ↔ Spec** | 🔴 Phase 5 not in spec v1.1 — **added in spec v1.2** |
| **Overall program status** | **Phase 2 complete** (`v9.3.0-p2`); **Phase 3 ~70%** (Gates 6–8, 10 PASS); **Phase 4 0%**; **Phase 5 0%** |

**Recommendation**: Close Phase 3 (Gates 8–9, 11, tag `v9.4.0-p3`) before starting Phase 4 engineering. Phase 5 streams A–C depend on Phase 4 GTM baseline.

---

## 2. Phase naming map (critical)

External **Enterprise Deployment Roadmap** phases ≠ internal **Spec 015** phases in scope only:

| Roadmap doc (36-week) | Spec 015 program | Tag / evidence | Status |
|----------------------|------------------|----------------|--------|
| Phase 0 Security | Enterprise Phase 0 | Option B B1–B5 | ✅ |
| Phase 1 K8s/Obs/CI | Phase 1 + 2 (compose-first) | `v9.3.0-p2`, Gates 1–5 | ✅ |
| Phase 2 ERP parity | Phase 3 Stream 2 (scaffolds) | Gate 10 | 🔄 scaffold only |
| Phase 3 Scale/Compliance | Phase 3 Streams 1, 3 | Gates 6–11 | 🔄 ~70% |
| Phase 4 GTM | Phase 4 | `v10.0.0-e4` TBD | ⬜ |
| *(not in Spec 015 v1.1)* | **Phase 5** (Gap Audit doc) | post-GTM | ⬜ proposed |

Roadmap items **SEC-001–016**, **GO-001–030**, **TD-001–010**, and **v8 SAP gap matrix** span Phases 3–5 and are tracked in Phase 5 audit, not all in original Spec 015 four-phase plan.

---

## 3. Gate verification matrix

| Gate | Constitution VIII | tasks.md | GATE-RESULTS | Roadmap v4 | Status |
|------|-------------------|----------|--------------|------------|--------|
| 1 Observability | Required pre-p2 | T081 ✅ | Gate 1 scripts | OBS cluster | ✅ |
| 2 Security | Required pre-p2 | T082 ✅ | verify-gate2 | SEC partial | ✅ |
| 3 Multi-tenant | Required pre-p2 | T083 ✅ | verify-gate3 | — | ✅ |
| 4 Odoo sync | Required pre-p2 | T084 ✅ | verify-gate4 | ERP | ✅ |
| 5 E2E R1+R2 | Required pre-p2 | T085 ✅ | 14/14 + 5/5 | — | ✅ |
| 6 Helm lint | Required pre-p3 | T150 ✅ | PASS 2026-07-04 | INF/K8s | ✅ |
| 7 kind deploy | Required pre-p3 | T151 ✅ | 6/6 pods 200 | INF/K8s | ✅ |
| 8 Compose–K8s parity | Required pre-p3 | T152 ✅ | PASS 2026-07-05 | INF/K8s | ✅ |
| 9 HPA smoke | Required pre-p3 | T153 ⬜ | PENDING | Scale | ⬜ |
| 10 ERP scaffolds | Required pre-p3 | T154 ✅ | pytest PASS | ERP expand | ✅ |
| 11 R1 on K8s | Required pre-p3 | T155 ⬜ | PENDING | Demo | ⬜ |

**Tag policy**: `v9.4.0-p3` blocked until Gates 8, 9, 11 PASS (Principle VIII).

---

## 4. Phase 3 gap audit (P3-01–P3-16 vs codebase)

| ID | Item | Doc claim | Actual (2026-07-04) | Delta |
|----|------|-----------|---------------------|-------|
| P3-01 | Helm lint | Not run | ✅ `verify-gate6.ps1` | **Closed** |
| P3-02 | kind deploy | Not run | ✅ cluster `ipe-dev` | **Closed** |
| P3-03 | Pod/SVC verify | Pending | ✅ 8/8 Running | **Closed** |
| P3-04 | Parity test | Pending | ⬜ compose stack unstable (connector health / kong) | **Open** |
| P3-05 | HPA smoke | Pending | ⬜ | **Open** |
| P3-06 | Gates 6–7 | Pending | ✅ | **Closed** |
| P3-07 | Gate 8 | Pending | ⬜ | **Open** |
| P3-08 | Gate 9 | Pending | ⬜ | **Open** |
| P3-09 | Gate 11 (R1 K8s) | Pending | ⬜ | **Open** |
| P3-10 | Phase 3 sign-off | Pending | ⬜ | **Open** |
| P3-11 | Tag v9.4.0-p3 | Blocked | ⬜ by design | **Open** |
| P3-12 | Bitnami subcharts | Deferred | compose-first in dev values | **Deferred to P4 SaaS** |
| P3-13–14 | SAP/D365 live | No sandbox | scaffold + tests ✅ | **By design (Principle VII)** |
| P3-15 | Registry in sync API | Pending | registry exists; dispatch TBD | **Open P5** |
| P3-16 | Git commit Track A/B | Pending | ✅ commit `62efff5` | **Closed** |

**Phase 3 completion**: ~70% — Gates 6, 7, 8, 10 PASS; 9, 11 pending.

---

## 5. Phase 4 coverage (GTM proposal ↔ spec ↔ tasks)

| Deliverable (Phase 4 doc) | FR ID | Task ID | Issues | Status |
|---------------------------|-------|---------|--------|--------|
| Self-service onboarding (<60 min) | FR-015-40 | T120a | — | ⬜ |
| Terraform/Pulumi SaaS (<30 min) | — | T127 | — | ⬜ |
| API developer portal (<10 min) | FR-015-42 | T122a | — | ⬜ |
| Stripe metered billing | FR-015-41 | T121a | — | ⬜ |
| Mobile-responsive web | — | T128a (new) | — | ⬜ |
| Knowledge base 90% deflect | FR-015-44 | T125 | — | ⬜ |
| Python + JS SDKs | FR-015-43 | T123, T124 | — | ⬜ |
| Customer health dashboard | FR-015-45 | T126 | — | ⬜ |
| On-prem Ansible/air-gap | — | T128 | — | ⬜ |

**Dependencies (Phase 4 doc §4.1)**: Phase 3 ≥75% — **met for Helm/kind**; parity + Gate 11 still required before SaaS offer.

**Ambiguities (AD-01–AD-10 from Phase 4 doc)** — resolved in clarify session 2026-07-04-b:

| AD | Topic | Resolution |
|----|-------|------------|
| AD-01 | Sprint breakdown missing | Added T170–T179 in tasks v2.2 |
| AD-02 | Stripe account | External; block T121a until sandbox keys |
| AD-03 | Docs platform (GitBook/ReadMe) | GitBook preferred; T125 |
| AD-04 | Mobile framework | Responsive Vite/Tailwind first; native app out of scope |
| AD-05 | Partner program | Phase 5 Stream C |
| AD-06 | Pricing tiers | OQ-7 commercial sign-off |
| AD-07 | Terraform vs Pulumi | Terraform primary (`infra/terraform/`) |
| AD-08 | Onboarding UX wireframes | PM deliverable before T120a |
| AD-09 | Marketing site | Out of engineering scope |
| AD-10 | Support staffing | Business ops; not spec 015 |

---

## 6. Phase 5 coverage (Gap Audit doc)

**131 gaps** catalogued in Phase 5 doc; mapped to three streams:

| Stream | Scope | Spec FR (new) | Priority |
|--------|-------|---------------|----------|
| A — Compliance | SOC 2 Type II path, GDPR hardening, WCAG 2.1 AA | FR-015-50–52 | P1 after P4 |
| B — Platform maturity | Event sourcing, CQRS, GraphQL, S&OP workflow, Copilot prod | FR-015-53–56 | P2 |
| C — Ecosystem | Live SAP/D365, partner program, advanced analytics | FR-015-57–59 | P2 (customer-triggered) |

**Overlap with Phase 3 deferred items**: T090a–T094 (GDPR, WCAG, SOC2, 500 VU) → **Phase 5 Stream A**, not Phase 3 close-out.

**Roadmap SEC-001–016**: Partially satisfied by Phase 0 (Keycloak, Vault, TLS, audit). Remaining: MFA (T007), pen-test (T010), WAF, SIEM — **Phase 5 Stream A**.

**v8 SAP gap matrix** (Copilot, demand sensing, scenario workbench, multi-echelon ATP): **product roadmap**, not Spec 015 gate blockers — tracked as FR-015-53–56 in Phase 5.

---

## 7. Constitution compliance check

| Principle | Phase 3 status | Violations / notes |
|-----------|----------------|-------------------|
| I RLS | ✅ | No new migrations without RLS in Phase 3 |
| II Auth | ✅ | K8s dev uses same JWT patterns |
| III Tests | ✅ | Gate 10 tests present |
| IV Events | 🟡 | R1 K8s profile omits Kafka — documented degraded health |
| V API consistency | ✅ | Parity script validates structure |
| VI Observability | ✅ | `/metrics` on deployed pods |
| VII Customer-first | ✅ | Star Trans compose-first; K8s not required for R1 |
| VIII Gate verification | 🟡 | Gates 8–9, 11 lack PASS evidence |

---

## 8. Star Trans / Track B

| Artifact | Path | Status |
|----------|------|--------|
| Deployment guide | `docs/customer/star-trans/` | ✅ |
| SOW input | ✅ | ⬜ signature blocked |
| UAT plan | ✅ | ⬜ execution blocked (Odoo staging) |
| Field mapping | ✅ | Odoo 17 primary |
| Training curriculum | ✅ | — |

**Business track independent of Gate 11** — R1 go-live on compose, not K8s (Principle VII).

---

## 9. Risk register (top 5)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gate 8 blocked by compose health (Kafka/Vault deps in R1) | Delays v9.4.0-p3 | R1 profile: disable Kafka probe in health for parity run; or use `values-release1` K8s-only comparison |
| Phase 4 doc stale (25% Phase 3) | Planning drift | This analyze + spec v1.2 refresh |
| 131 Phase 5 gaps overwhelm team | Scope creep | Stream A only after P4; B/C customer-triggered |
| OQ-7 pricing unsigned | Blocks SOW | Engineering continues; commercial parallel |
| SAP/D365 live without sandbox | False readiness | Keep scaffold; Gate 10 sufficient until customer #2 |

---

## 10. Recommended next actions

1. **Gate 8**: Fix compose R1 health (Kafka optional) → run `test-compose-k8s-parity.py`
2. **Gate 9**: `values-prod.yaml` HPA + k6 CPU load
3. **Gate 11**: `demo-http.ps1` with `K8S_BASE=http://localhost/api/v1`
4. **Tag** `v9.4.0-p3` only after 1–3 PASS
5. **Phase 4**: Create issues T170–T179; begin T120a after Gate 11
6. **Phase 5**: Backlog only — no engineering until Phase 4 milestone

---

## 11. v8 SAP Gap Analysis → Phase 5 mapping

| v8 Upgrade | Tier | Spec FR | Phase |
|------------|------|---------|-------|
| U1 AI Copilot + role agents | 1 | FR-015-54 | 5B |
| U2 Demand sensing | 1 | FR-015-55 | 5B |
| U3 Scenario workbench | 1 | FR-015-55 | 5B |
| U4 Supply orchestration | 2 | FR-015-55a | 5B |
| U5 Order management | 2 | FR-015-55a | 5B |
| U6 Predictive maintenance | 2 | FR-015-55b | 5B |
| U7 Product design AI | 3 | FR-015-55b | 5B |
| U8 Responsible procurement | 3 | FR-015-59 | 5C |

**Not Phase 3 blockers.** R1 ships without these; competitive parity is post-GTM.

---

*Analysis version 1.1 — `/speckit.analyze` 2026-07-05*
