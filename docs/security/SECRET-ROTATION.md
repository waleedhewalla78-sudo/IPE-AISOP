# Secret Rotation Procedure

## Overview

IPE uses HashiCorp Vault for secret management with environment variable fallback.

When `VAULT_ENABLED=false` or `SECRETS_PROVIDER=env` (default in local/dev), secrets are read from Docker Compose env files (`infrastructure/docker/ipe-common.env`) and mounted key files. In production, enable Vault and treat env files as bootstrap-only.

| Mode | Config |
|------|--------|
| Vault (production) | `VAULT_ENABLED=true`, `SECRETS_PROVIDER=hashi_vault` |
| Env fallback (dev) | `VAULT_ENABLED=false`, `SECRETS_PROVIDER=env` |

Vault KV mount: **`ipe`** (see `VAULT_KV_MOUNT`). CLI paths below use `ipe/<secret>` (not `secret/ipe/...`).

Initial seed: `scripts/vault-init.sh`  
Dev rotation helper: `scripts/rotate-secrets.sh`

---

## Secret Categories

| Category | Vault path | Fallback location |
|----------|------------|-------------------|
| Database credentials | `ipe/database` | `IPE_DATABASE_URL`, `POSTGRES_PASSWORD` in compose |
| JWT signing keys | `ipe/jwt` (HS256 secret) | `config/keys/` (RS256 key pair) |
| Kafka credentials | `ipe/kafka` | `IPE_KAFKA_BOOTSTRAP_SERVERS` (plaintext in dev) |
| Keycloak client secret | `ipe/keycloak` | `KEYCLOAK_CLIENT_SECRET`, realm import JSON |
| Odoo credentials | `ipe/odoo` | `ODOO_*` env vars on `connector` |

---

## Rotation Procedures

### Database Password Rotation

1. **Verify current password** (Vault):
   ```bash
   export VAULT_ADDR=http://localhost:8200
   export VAULT_TOKEN=<admin-or-rotation-token>
   vault kv get -field=password ipe/database
   ```

2. **Generate and store new password** in Vault:
   ```bash
   NEW_PASS="$(openssl rand -base64 32)"
   vault kv patch ipe/database password="${NEW_PASS}"
   ```

3. **Apply in PostgreSQL**:
   ```sql
   ALTER USER ipe WITH PASSWORD '<new_password>';
   ```
   Release 1 DB runs as user `ipe` on database `ipe_test` (port `5433` on host).

4. **Rolling restart services** (one at a time, Release 1 example):
   ```bash
   cd infrastructure/docker
   for svc in dpe-svc fea-svc res-svc cap-svc connector; do
     docker compose -f docker-compose.release1.yml restart "$svc"
     sleep 15
     curl -sf "http://localhost:8000/api/v1/health" || curl -sf "http://localhost:${PORT}/api/v1/health"
   done
   ```
   Adjust health URLs per service port if bypassing Kong.

5. **Verify**: each service `/api/v1/health` (or `/health`) reports database connectivity (`db=up` / healthy pool).

6. **Update env fallback** (if not yet on Vault-only): sync `ipe-common.env` and `DATABASE_URL` in compose, then recreate containers.

---

### JWT Key Rotation (RS256)

IPE Release 1 uses RS256 with keys under `config/keys/`:

- `jwt-private.pem` — signing (dpe-svc only)
- `jwt-public.pem` — verification (all services, read-only mount)

1. **Generate new key pair**:
   ```bash
   cd config/keys
   openssl genrsa -out jwt-private.new.pem 4096
   openssl rsa -in jwt-private.new.pem -pubout -out jwt-public.new.pem
   chmod 600 jwt-private.new.pem
   ```

2. **Stage keys** (keep old keys for transition):
   ```bash
   cp jwt-private.pem jwt-private.old.pem
   cp jwt-public.pem jwt-public.old.pem
   mv jwt-private.new.pem jwt-private.pem
   mv jwt-public.new.pem jwt-public.pem
   ```

3. **Rolling restart all services** that mount JWT keys:
   ```bash
   cd infrastructure/docker
   docker compose -f docker-compose.release1.yml up -d --force-recreate \
     dpe-svc fea-svc res-svc cap-svc connector kong
   ```

4. **Token impact**: access tokens signed with the old private key fail verification after cutover. Acceptable if clients use refresh tokens or re-login. Default access TTL is 60 minutes (`IPE_JWT_ACCESS_TOKEN_EXPIRE_MINUTES`).

5. **Cleanup**: after **24h** (max refresh/access TTL window), remove `jwt-private.old.pem` and `jwt-public.old.pem`.

6. **HS256 fallback** (legacy/dev): rotate `ipe/jwt` secret via Vault and restart `dpe-svc`:
   ```bash
   vault kv patch ipe/jwt secret="$(openssl rand -base64 48)"
   ```

---

### Kafka Credentials Rotation

> Dev stack uses PLAINTEXT Kafka with no SASL. Use this procedure when SASL/TLS is enabled in production.

1. **Store new credentials** in Vault:
   ```bash
   vault kv patch ipe/kafka \
     username="ipe-kafka" \
     password="<new_password>" \
     bootstrap_servers="kafka:9092"
   ```

2. **Update Kafka broker** user/password (cluster-specific — ACL or SCRAM).

3. **Rolling restart** Kafka-consuming/producing services:
   ```bash
   for svc in dpe-svc connector fea-svc res-svc cap-svc; do
     docker compose -f docker-compose.release1.yml restart "$svc"
     sleep 20
   done
   ```

4. **Verify**: consumer lag stable in Grafana (`ipe-kafka-consumer-lag`), no auth errors in service logs.

---

### Keycloak Client Secret Rotation

1. **Read current secret** (Vault):
   ```bash
   vault kv get ipe/keycloak
   ```

2. **Rotate in Keycloak Admin** (or API):
   - Realm: `ipe`
   - Client: `ipe-platform` / `ipe-web`
   - Credentials → Regenerate secret

3. **Patch Vault**:
   ```bash
   vault kv patch ipe/keycloak \
     client_secret="<new_secret>" \
     admin_password="<unchanged_or_new>"
   ```

4. **Update env fallback**: `KEYCLOAK_CLIENT_SECRET` in compose/secrets overlay.

5. **Restart** `keycloak` (if realm reload needed) and services using Keycloak token exchange (`dpe-svc`, `web-ui`).

6. **Verify**: login flow via `http://localhost:8082` → Keycloak → API token issuance.

---

### Odoo Credentials Rotation

1. **Patch Vault**:
   ```bash
   vault kv patch ipe/odoo \
     password="<new_password>" \
     url="${ODOO_URL:-http://host.docker.internal:8069}"
   ```

2. **Update Odoo** user password on the ERP side.

3. **Restart connector**:
   ```bash
   docker compose -f docker-compose.release1.yml restart connector
   ```

4. **Verify**: `GET /api/v1/sync/odoo/status` or connector health; confirm sync scheduler runs without auth errors.

---

### Vault Token Rotation

Service tokens should use least-privilege policies (not the dev root token).

1. **Create new token**:
   ```bash
   vault token create -policy=ipe-service -ttl=72h -format=json
   ```

2. **Update `VAULT_TOKEN`** in Docker Compose, Kubernetes secrets, or `ipe-common.env` (bootstrap only).

3. **Rolling restart** all Vault-enabled services.

4. **Revoke old token**:
   ```bash
   vault token revoke <old_token_accessor_or_id>
   ```

5. **Verify**: `vault kv get ipe/database` succeeds from a service pod/container with the new token.

---

## Automation (Future)

| Area | Target approach |
|------|-----------------|
| Database | Vault dynamic secrets (PostgreSQL engine, auto-rotating creds) |
| TLS | cert-manager for ingress/Kong certificate rotation |
| Keycloak | Client secret rotation via Admin API + Vault sync job |
| JWT | Automated keygen + staged rollout with dual `jwt-public` keys |
| Audit | Log rotation events to `ipe.audit.v3` Kafka topic |

---

## Checklist (Production Rotation)

- [ ] Maintenance window communicated
- [ ] Current secrets backed up / version noted in Vault (`vault kv metadata get ipe/database`)
- [ ] New secret written to Vault before infra change
- [ ] Database/broker/IdP updated to match
- [ ] Rolling restarts completed one service at a time
- [ ] Health checks green (`/api/v1/health`, Prometheus `up`, Grafana dashboards)
- [ ] Old credentials/tokens revoked after verification window
- [ ] Runbook entry logged in change management system

---

## Related Files

| File | Purpose |
|------|---------|
| `scripts/vault-init.sh` | Seed KV secrets (dev) |
| `scripts/rotate-secrets.sh` | Manual DB + JWT secret rotation (dev) |
| `infrastructure/docker/ipe-common.env` | Env fallback |
| `config/keys/jwt-*.pem` | RS256 key material |
| `services/shared/ipe_shared/vault_loader.py` | Runtime secret resolution |
