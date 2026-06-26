# ADR-001: Defer Keycloak Live IdP Integration to v8.0.0

**Status:** Accepted  
**Date:** 2026-06-26  
**Deciders:** IPE Engineering  
**Related:** FR-P-13, C-007, TASK-C-007

---

## Context

FR-P-13 requires live Keycloak SAML/SCIM validation against enterprise IdPs (Azure AD, Okta). Finding **C-007** blocks completion because:

1. No Azure AD / Okta sandbox credentials are available in the development environment.
2. Full Keycloak realm federation requires dedicated infrastructure (Keycloak server, TLS certs, IdP metadata exchange).
3. Demo and production-readiness paths already use **JWT auth** via `dpe-svc` with Kong JWT plugin — proven by demo 20/20 and chaos 6/6.

Current auth stack:

- Login: `POST /api/v1/auth/login` (dpe-svc)
- Kong validates JWT on all public routes
- Tenant isolation via JWT claims + PostgreSQL RLS (migrations 024–027)
- Password storage: `{SHA-256}` + hex digest (SEC-05, migration 028)

---

## Decision

**Defer full Keycloak live IdP integration to v8.0.0.** For v7.0.0:

- Continue JWT demo auth as the supported authentication path.
- Document migration path in this ADR and `docs/runbooks/jwt-rotation.md`.
- Mark FR-P-13 as **deferred** (13/14 FR-P for v7.0.0).
- Speckit readiness remains **100/100** on built tasks; FR-P enterprise gate documented as deferred.

---

## Consequences

### Positive

- v7.0.0 ships on schedule without external IdP dependency.
- No false claim of SAML/SCIM production verification.
- Clear v8.0.0 scope for enterprise sales.

### Negative

- Enterprise customers requiring SSO must wait for v8.0.0 or use JWT bridge.
- Audit score for IdP dimension capped until v8 (mitigated by ADR + JWT hardening).

---

## Migration Path (v8.0.0)

| Step | Effort | Description |
|------|--------|-------------|
| 1 | 1 d | Add `keycloak` service to docker-compose with realm `ipe` |
| 2 | 1 d | Configure OIDC client; export JWKS URL |
| 3 | 1 d | Kong JWT plugin → Keycloak JWKS endpoint |
| 4 | 2 d | SAML IdP federation (Azure AD test tenant) |
| 5 | 1 d | SCIM user provisioning smoke test |
| 6 | 1 d | E2E SSO flow test + update Speckit FR-P-13 |

**Prerequisites:** Azure AD or Okta sandbox app registration, DNS/TLS for Keycloak.

---

## References

- `specs/001-production-readiness-convergence/tasks.md` TASK-C-007
- `specs/005-ipe-program-status/spec.md` FR-P-13
- `docs/runbooks/jwt-rotation.md`
- `docs/audit-gap-analysis-v6.1.md` AG-01
