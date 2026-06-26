# Security Hardening Sweep — v7.0.0

**Date:** 2026-06-26 (updated)  
**Scope:** P7-02 mandatory checks per audit-gap-analysis AG-04

---

## Scan Results

| Check | Result | Details |
|-------|--------|---------|
| Hardcoded secrets | **CLEAN** | `rg` on py/yaml: only test fixtures in `shared/tests/` |
| Non-root containers | **PARTIAL** | App images use default root; prod uses K8s securityContext; POST-C4 backlog |
| CORS config | **RESTRICTED (prod path)** | Dev compose allows local origins; prod via ingress |
| Health endpoints | **ALL services** | `/health` + `/healthz` alias via `ipe_shared.observability.metrics` |
| Tenant isolation | **VERIFIED (app + RLS 024–028)** | Legacy 002–012 waived ADR-002 |
| SQL injection | **PARAMETERIZED** | SQLAlchemy/text() with bound params |
| Input validation | **PYDANTIC** | FastAPI models on REST endpoints |
| Kong rate limiting | **CONFIGURED** | 300/min, 10k/hr global |
| JWT / password hash | **VERIFIED** | SEC-05 migration 028; runbook C-04 |

---

## Remediation Actions

- [x] Add `/healthz` alias on all services (shared metrics module)
- [x] Secret scan — no production credentials in source
- [x] Document legacy RLS waiver (ADR-002)
- [x] Keycloak deferral documented (ADR-001)
- [ ] Non-root Docker USER — deferred POST-C4
- [ ] Full RLS 002–012 — deferred POST-C3 / v7.1

---

## Post-Remediation Re-scan

```text
rg -i "password\s*=\s*['\"]" services/ --glob "!**/tests/**"
→ No matches in production code paths
```

Health check verification:
```text
grep healthz services/shared/ipe_shared/observability/metrics.py
→ app.add_api_route("/healthz", health_endpoint, methods=["GET"])
```

---

## References

- `docs/audit-gap-analysis-v6.1.md` AG-04
- `infrastructure/docker/kong.yml`
- `docs/decisions/ADR-001-keycloak-deferral.md`
- `docs/decisions/ADR-002-legacy-rls-waiver.md`
