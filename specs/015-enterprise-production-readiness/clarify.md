# Clarify — 015 Enterprise Production Readiness

**Date**: 2026-06-24  
**Feature**: `015-enterprise-production-readiness`

---

## Resolved decisions

| ID | Question | Decision | Rationale |
|----|----------|----------|-----------|
| OQ-015-1 | Enterprise vs R2 priority? | **Finish 014 first**, then 015 Phase 0 | Star Trans revenue path; enterprise blocks multi-tenant SaaS |
| OQ-015-2 | Single tag or phased? | **Phased milestones** `v10.0.0-e0` … `e4` | 36-week program; no big-bang |
| OQ-015-3 | K8s target? | **EKS primary**, k3s for on-prem doc | Roadmap INF-001; Helm chart exists |
| OQ-015-4 | IdP default? | **Keycloak** (self-hosted) + Azure AD recipe | Scaffold in 011; customers bring own IdP |
| OQ-015-5 | Vault vs AWS SM? | **Both** via `SECRETS_PROVIDER` | `secrets_manager.py` already dual-stub |
| OQ-015-6 | SAP vs D365 first? | **SAP S/4** (Phase 3) before D365 | Gap analysis U-05; manufacturing ICP |
| OQ-015-7 | Break R1 compose? | **No** — enterprise overlays separate compose/helm | `docker-compose.release1.yml` frozen |
| OQ-015-8 | Audit log gap in roadmap? | **Closed** — roadmap predates migration 021 | `cdm_audit_log` append-only exists; update checklist |
| OQ-015-9 | v8.2.0 gap plan status? | **Complete** for P1/P2 code | Remaining = POST-B activation (this spec) |
| OQ-015-10 | Managed SaaS (014 Stream E)? | **Moved to 015 Phase 4** FR-015-40/41 | Aligns with enterprise roadmap Phase 4 |

---

## Open items (need stakeholder input)

| ID | Question | Default if silent |
|----|----------|-------------------|
| OQ-015-11 | SOC 2 auditor vendor? | Defer to Phase 3 kickoff |
| OQ-015-12 | Premium SLA tier (99.9%)? | Document only until Phase 2 observability live |
| OQ-015-13 | Air-gapped on-prem customer in pipeline? | Ansible guide without implementation |

---

*Clarify version 1.0 — `/speckit.clarify`*
