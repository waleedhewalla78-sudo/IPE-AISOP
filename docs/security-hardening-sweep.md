# Security Hardening Sweep — v7.0.0

**Date:** 2026-06-26  
**Scope:** Pre-release security checklist (P7-02)

---

## Checklist Results

| Item | Status | Evidence |
|------|--------|----------|
| Tenant isolation (CDM RLS) | ✅ Partial | Migrations 024–027; demo JWT + `X-Tenant-ID` |
| Kong rate limiting | ✅ | 300/min, 10k/hr global (`kong.yml`) |
| No hardcoded secrets | ✅ Clean | `rg` scan: only test fixtures in `shared/tests/` |
| Non-root containers | ⚠️ Partial | App Dockerfiles use default root; airflow uses `USER airflow` |
| Health endpoints | ✅ | `/health` on all services via `ipe_shared.observability.metrics` |
| CORS prod config | ⚠️ Dev default | Wildcard acceptable for demo; prod uses K8s ingress rules |
| SQL injection protection | ✅ | SQLAlchemy parameterized queries throughout |
| Input validation | ✅ | Pydantic models on REST endpoints |
| JWT rotation documented | ✅ | `docs/runbooks/jwt-rotation.md` |
| TLS internal documented | ✅ | `docs/runbooks/tls-internal.md` |
| Password hashing | ✅ | `{SHA-256}` + migration 028 |
| Secrets in compose | ⚠️ Dev only | Default dev creds in compose; prod uses secrets overlay |

---

## Secret Scan

```text
rg -i "password\s*=\s*['\"]" --glob "!*.md" services/
→ Only test fixtures: shared/tests/test_schemas.py, test_auth_models.py
```

**Action:** No production secrets in tracked source. `.kms_keys/` is gitignored.

---

## Kong Public Endpoints

All routes except `POST /api/v1/auth/login` require JWT (`kong.yml` per-service plugins).

---

## Recommendations (post-v7)

1. Add `USER appuser` to service Dockerfiles (POST-C4)
2. Enable `docker-compose.secrets.yml` in staging
3. Complete legacy RLS on migrations 002–012 (POST-C3)
4. Keycloak SSO — v8.0.0 per ADR-001

---

## References

- `infrastructure/docker/kong.yml`
- `infrastructure/docker/docker-compose.secrets.yml`
- `docs/decisions/ADR-001-keycloak-deferral.md`
