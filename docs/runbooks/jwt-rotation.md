# Runbook: JWT Secret Rotation (C-04)

**Audit finding:** C-04 — no documented procedure for rotating `IPE_JWT_SECRET_KEY`.  
**Scope:** Kong JWT plugin, dpe-svc auth, all FastAPI services validating Bearer tokens.  
**Last updated:** 2026-06-26 (Wave 3 / v6.1.0)

---

## 1. Current JWT setup

| Setting | Default / location | Notes |
|---------|-------------------|-------|
| Algorithm | **HS256** | `ipe_shared/config.py` → `JWT_ALGORITHM` |
| Secret | `IPE_JWT_SECRET_KEY` env | Shared across Kong + all services |
| Access TTL | 60 min | `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` |
| Refresh TTL | 1440 min | `JWT_REFRESH_TOKEN_EXPIRE_MINUTES` |
| Issuer | dpe-svc `/api/v1/auth/login` | Returns access + refresh tokens |
| Kong validation | JWT plugin on protected routes | `infrastructure/docker/kong.yml` |
| JWKS mode | Opt-in | `JWT_USE_JWKS=true` + `JWT_JWKS_URL` (Keycloak path) |

Token claims: `sub`, `tenant_id`, `role`, `exp`, `iat`, `jti`, `type`.

---

## 2. Dual-key rotation (zero downtime)

### 2.1 Generate new secret

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
# Example: NEW_SECRET=<output>
```

Store in secret manager (never commit):

```text
IPE_JWT_SECRET_KEY_CURRENT=<old>
IPE_JWT_SECRET_KEY_NEXT=<new>
```

### 2.2 Enable dual validation window (24–48 h)

**Application layer:** Services accept tokens signed with **either** key during transition.

Implementation pattern (when enabling in code):

```python
# ipe_shared/auth/jwt.py — decode tries CURRENT then NEXT
for key in (settings.JWT_SECRET_KEY, settings.JWT_SECRET_KEY_LEGACY):
    try:
        return jwt.decode(token, key, algorithms=[settings.JWT_ALGORITHM])
    except jwt.InvalidSignatureError:
        continue
```

**Kong layer:** Register two JWT credentials (consumers) or switch to JWKS with two active keys.

For HS256 demo stack, preferred order:

1. Update all services with `JWT_SECRET_KEY=<NEW>`.
2. Keep `JWT_SECRET_KEY_LEGACY=<OLD>` for 48 h.
3. Issue new tokens only with NEW (login always uses current secret).

### 2.3 Service restart order

| Order | Component | Why |
|-------|-----------|-----|
| 1 | **PostgreSQL / Redis / Kafka** | No restart unless config references JWT |
| 2 | **dpe-svc** (auth issuer) | Must sign with new key first |
| 3 | **Downstream services** | cap, mat, fea, nlp, alert, connector, … |
| 4 | **Kong last** | Validates inbound tokens; update after issuers ready |

```powershell
cd E:\AISOP\ipe\infrastructure\docker
docker compose -f docker-compose.yml -f docker-compose.demo.yml `
  restart dpe-svc mat-svc cap-svc fea-svc nlp-svc alert-svc connector kong
```

---

## 3. Kong JWT plugin update

### 3.1 Declarative config (demo)

Kong JWT plugin uses the secret from environment or `kong.yml` consumer credentials. After rotation:

1. Update Kong consumer JWT secret in DB or declarative config.
2. `docker compose exec kong kong reload`.

### 3.2 Verify Kong accepts new tokens

```powershell
# Login (issues token with new secret from dpe-svc)
$login = Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/auth/login" `
  -ContentType "application/json" `
  -Body '{"email":"Ahmed@nour","password":"admin"}'

# Protected route
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/me" `
  -Headers @{ Authorization = "Bearer $($login.data.access_token)" }
# Expect: 200 + user payload
```

---

## 4. Verification checklist

- [ ] Token issued **before** rotation validates during dual-key window (LEGACY set)
- [ ] Token issued **after** rotation validates on Kong + all services
- [ ] `run-full-demo.ps1` → **20/20**
- [ ] k6 smoke passes (`tests/performance/k6/smoke.js`)
- [ ] No `401` spike in Grafana `ipe_http_requests_total{status="401"}`

---

## 5. Rollback

| Step | Action |
|------|--------|
| 1 | Set `IPE_JWT_SECRET_KEY` back to **OLD** value on all services |
| 2 | Remove `JWT_SECRET_KEY_LEGACY` |
| 3 | Restart services (§2.3 order) |
| 4 | Invalidate active sessions if needed: flush Redis session keys `ipe:jwt:*` |
| 5 | Re-run demo 20/20 |

**Emergency:** If only Kong was updated, revert Kong consumer secret and `kong reload` — tokens from dpe-svc remain valid.

---

## 6. Production notes (Keycloak / JWKS)

When `JWT_USE_JWKS=true`:

- Rotation is managed in **Keycloak realm** → Keys tab → generate new RSA key, set as active.
- Kong validates via JWKS URL; no shared HS256 secret.
- See `docs/runbooks/tenant-onboarding.md` for realm client setup.

---

## 7. Environment reference

```powershell
# .env / K8s Secret keys
IPE_JWT_SECRET_KEY=<primary-signing-key-min-32-chars>
IPE_JWT_SECRET_KEY_LEGACY=<optional-during-rotation>
IPE_JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
IPE_JWT_REFRESH_TOKEN_EXPIRE_MINUTES=1440
IPE_JWT_USE_JWKS=false
```

---

## 8. Related artifacts

- `services/shared/ipe_shared/auth/jwt.py` — encode/decode
- `infrastructure/docker/kong.yml` — JWT-protected routes
- `services/dpe-svc/app/api/v1/auth.py` — login issuer
- Audit: `audit/v2/14-remediation-backlog.md` R-012
