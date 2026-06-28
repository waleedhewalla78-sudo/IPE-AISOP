# Production Deployment Blockers — Resolution Status

**Product:** IPE v7.0.0  
**Date:** 2026-06-27  
**Status:** All items **resolved for staging**; **deferred for production** with documented ADRs.

---

## Summary

| Severity | Count | Staging | Production |
|----------|-------|---------|------------|
| P0 | 2 | ✅ Waived (demo JWT) | ❌ Required |
| P1 | 2 | ✅ Mock acceptable | ❌ Required |
| P2 | 2 | ✅ N/A | Planned POST-* |

**Staging/UAT verdict:** ✅ **GO** — use demo seed + local JWT.  
**Production verdict:** ❌ **NO-GO** until P0/P1 customer infra is provisioned.

---

## P0 — Must have for production

### C-007 · Enterprise SSO (Keycloak / SAML / SCIM)

| Field | Value |
|-------|-------|
| **Issue** | No live IdP integration tested |
| **Staging resolution** | Local JWT auth (`POST /api/v1/auth/login`) — validated in E2E QA |
| **Production resolution** | **Deferred to v8.0.0** per ADR-001 |
| **Customer action** | Provide Azure AD / Okta / Keycloak realm |
| **Code status** | SCIM routes scaffolded in scn-svc; Keycloak config placeholders exist |

### SEC-P0 · JWT signing secret

| Field | Value |
|-------|-------|
| **Issue** | `ipe-common.env` uses dev placeholder secret |
| **Staging resolution** | Acceptable for local/demo tenants |
| **Production resolution** | Inject via secrets manager; see `docs/runbooks/jwt-rotation.md` |
| **Customer action** | Set `IPE_JWT_SECRET` in vault; run rotation runbook |

---

## P1 — Required before paid production

### BILL-P1 · Stripe live billing

| Field | Value |
|-------|-------|
| **Issue** | `StripeMockService` in demo |
| **Staging resolution** | Mock endpoints functional for UAT |
| **Production resolution** | Wire live Stripe keys + webhook endpoint |
| **Customer action** | Stripe account, products, webhook URL |

### RLS-P1 · Row-level security gaps

| Field | Value |
|-------|-------|
| **Issue** | 22 legacy tables without RLS policies |
| **Staging resolution** | ADR-002 waiver; single-tenant demo validated |
| **Production resolution** | POST-C3 migration sprint |
| **Customer action** | Security review sign-off on waiver or fund RLS sprint |

---

## P2 — Post-launch / customer-specific

### ERP-P2 · Live ERP connectors (Odoo / SAP / D365)

| Field | Value |
|-------|-------|
| **Staging** | Connector service healthy; mock Odoo in test compose |
| **Production** | Customer ERP credentials + network allowlist |

### OPS-P2 · Non-root containers

| Field | Value |
|-------|-------|
| **Staging** | N/A |
| **Production** | POST-C4 backlog |

---

## Closed engineering issues (not production blockers)

| ID | Issue | Resolution |
|----|-------|------------|
| E1 | Copilot 503 | OpenRouter + Ollama integration |
| E2 | Ollama DNS fallback | Skip unconfigured providers |
| E3 | Intent classify on "hi" | Fallback to `general` |
| E4 | del-svc mock env | Removed dead var |
| E5 | CopilotPanel tenant header | JWT tenant extraction |
| E6 | Kong Copilot timeout | 300s upstream timeout on nlp-svc |
| E7 | Tool chat empty error | Ollama timeout 300s + error messages |

---

## Sign-off checklist for production GO

- [ ] ADR-001 Keycloak cutover plan approved
- [ ] Production JWT secret in vault
- [ ] Stripe live mode configured
- [ ] RLS waiver signed OR POST-C3 complete
- [ ] Customer ERP connector tested
- [ ] k6 load test at target VU (200 VU POST-A)
- [ ] Monitoring overlay deployed (Grafana/Loki)

---

*For current product capabilities and demo readiness, see `docs/PRODUCT-STATUS.md`.*
