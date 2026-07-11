# IPE Open Questions — Resolution Status

**Document:** IPE-OQ-STATUS-v1  
**Updated:** 2026-07-11  
**Sprint:** 2 of 3  
**Maintainer:** Waleed Hewalla (COM items) / Engineering Lead (ENG items)

---

## Resolution Status Table

| OQ | Question | Status | Resolution | Engineering Impact | Owner |
|---|---|---|---|---|---|
| OQ-1 | Canonical Odoo version (17 or 19)? | **OPEN** | Recommend Odoo 19. IPE connector validated locally against Odoo 19. Odoo 17 fallback exists in mapper (field name aliases for `date_planned_start` vs `date_start`). Confirm with Star Trans IT before Week 1. | Low — connector handles both automatically via `normalize_mo_mapped()`. Zero code changes needed for either version. | COM — confirm with Star Trans IT during Pre-Engagement call |
| OQ-2 | Demo SQL overlay in production? | **RESOLVED** | No. Production environment uses Odoo live sync only. Star Trans SQL seed data (`seed-startrans-overlay.sql`) is explicitly disabled in the production `.env` by setting `DEMO_SEED_ENABLED=false`. This is binding policy — no engineer should apply seed SQL to production. | Resolved in Sprint 1 deployment package. `DEPLOY-RUNBOOK.md` documents the policy. | ENG — Done |
| OQ-3 | UI route-level RBAC? | **OPEN** | Recommended resolution: defer to Release 2. Star Trans is a single-tenant deployment with local JWT authentication. The current JWT-based role system (`planner`, `manager`, `executive`, `admin`) provides sufficient access control for R1. Full Keycloak SSO + route-level RBAC is the Release 2 roadmap item (ADR-001). | Low for R1. Medium for Release 2 multi-tenant. No engineering work needed to defer. | COM — formal decision needed; currently operating on recommendation-to-defer |
| OQ-4 | Tag v8.2.0 and update CHANGELOG? | **RESOLVED** | CHANGELOG updated in Sprint 1. All release tags current. v9.2.0-planning tagged. | Done — no further action. | ENG — Done |
| OQ-5 | Formal MAPE/triage-time baseline measurement? | **RESOLVED** | FR-R1-16 OTD baseline API built and deployed (`GET /api/v1/otd/baseline`). Forecast quality engine implemented and tested (v9.2.0-planning). OTD baseline will be captured from Odoo historical data on Day 20 (go-live + 4 days). MAPE baseline deferred — not applicable to R1 which uses OR-Tools scheduling, not statistical forecasting. | Engineering complete. No further work needed for R1. | ENG — Done |
| OQ-6 | Copilot session retention and GDPR compliance? | **DEFERRED** | AI Copilot is not included in Release 1 Star Trans deployment (`VITE_RELEASE_PROFILE=r1` excludes Copilot UI). GDPR session retention question applies only when Copilot is enabled for a multi-tenant European deployment (Phase 2). Anthropic Claude API used under enterprise data protection agreement — customer data not used for training. | No engineering action required before R2. Decision needed before enabling Copilot for any EU tenant. | COM — Phase 2 decision |
| OQ-7 | Commercial pricing? | **OPEN — BLOCKING** | Waleed must decide exact pricing before the SOW can be sent to Star Trans. The SOW currently contains `[AMOUNT — to be confirmed by Waleed]` placeholders. Reference range from existing implementation playbook: Annual Licence $18K–$30K USD; Implementation $12K–$25K USD. Waleed must pick specific numbers and remove placeholders from `docs/customer/star-trans/IPE-Star-Trans-SOW-v1.md`. | Zero engineering impact — pricing is a commercial decision only. | COM — BLOCKING: Waleed must decide before SOW is sent |
| OQ-8 | Second prospect and parallel customer pipeline? | **OPEN** | Waleed must name 5 target companies for Customer 2+ pipeline. Recommended profile: Egyptian manufacturing companies with Odoo 17 or 19, 50–500 employees, active MRP usage, Arabic-speaking planning team. Transformer or industrial equipment sectors preferred (similar to Star Trans). | Zero engineering impact. Customer 2 deployment would use the same `deploy/star-trans/` package with different `.env` configuration. No code changes needed unless Customer 2 has unique requirements. | COM — Waleed must name companies |
| OQ-9 | Gate 11 waiver acceptance? | **RESOLVED** | 12 of 14 Gate 11 checks PASSED. Two failures documented as infrastructure resource contention (Kubernetes memory limits under test, not product logic failures). Waiver documented in `docs/demo-data/gate11-oq9-waiver.md`. Waiver requires stakeholder signatures (Section 6.2 of waiver document). Engineering assessment: the 2 infrastructure failures do not represent product-level defects and do not affect Star Trans R1 deployment which runs on Docker Compose, not Kubernetes. | No additional engineering work. Waiver document needs COM stakeholder signatures before R1 go-live sign-off. | COM — collect signatures on gate11-oq9-waiver.md |

---

## Summary Status

Three OQs remain **OPEN**: OQ-1 (Odoo version confirmation — requires Star Trans IT call), OQ-7 (pricing — requires Waleed decision), and OQ-8 (Customer 2 prospects — requires Waleed to name companies). OQ-3 has a recommended resolution (defer RBAC to Release 2) but requires a formal commercial decision before it can be marked RESOLVED. **OQ-7 is the only item blocking the SOW from being sent to Star Trans** — all engineering work is complete and the SOW document is otherwise ready at `docs/customer/star-trans/IPE-Star-Trans-SOW-v1.md`.

---

## Action Items (Priority Order)

| Priority | Action | Owner | Deadline |
|---|---|---|---|
| 🔴 BLOCKING | Decide pricing (OQ-7) and update SOW with exact amounts | Waleed | Before SOW send |
| 🟡 HIGH | Confirm Odoo version with Star Trans IT (OQ-1) | Waleed / Star Trans IT | Pre-Engagement call |
| 🟡 HIGH | Collect signatures on gate11-oq9-waiver.md (OQ-9) | Waleed | Before go-live |
| 🟠 MEDIUM | Formally decide on RBAC deferral (OQ-3) | Waleed | Before SOW send (affects support terms) |
| 🟢 LOW | Name 5 Customer 2 prospects (OQ-8) | Waleed | Before Sprint 3 |

---

## Version History

| Version | Date | Changes |
|---|---|---|
| v1.0 | 2026-07-11 | Initial document — Sprint 2 completion; all 9 OQs documented |

---

*Source documents: `docs/customer/star-trans/SOW-STATUS.md`, `docs/integration/ODOO-19-FIELD-MAPPING.md`, `docs/demo-data/gate11-oq9-waiver.md`, `deploy/star-trans/DEPLOY-RUNBOOK.md`*
