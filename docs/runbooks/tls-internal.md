# Runbook: TLS for Internal Microservices (C-03)

**Audit finding:** C-03 — internal service-to-service traffic uses plain HTTP in the demo overlay.  
**Scope:** cap-svc, mat-svc, dpe-svc, nlp-svc, alert-svc, fea-svc, res-svc, del-svc, connector, Kong gateway.  
**Last updated:** 2026-06-26 (Wave 3 / v6.1.0)

---

## 1. Architecture options

| Mode | Use when | Client → Kong | Kong → services |
|------|----------|---------------|-----------------|
| **Termination at Kong** | Demo, staging, most prod | HTTPS | HTTP (Docker network) |
| **End-to-end TLS** | Regulated prod, zero-trust | HTTPS | HTTPS (mTLS optional) |
| **Passthrough** | Custom cert per service | HTTPS | TLS not terminated by Kong |

**Recommended default:** TLS **termination at Kong** + HTTP on the internal Docker/K8s network. Enable mTLS (Istio/Linkerd) in Phase 6 hardening.

---

## 2. Certificate generation

### 2.1 Development (self-signed)

```powershell
cd E:\AISOP\ipe\infrastructure\certs
openssl req -x509 -nodes -days 825 -newkey rsa:2048 `
  -keyout ipe-dev.key -out ipe-dev.crt `
  -subj "/CN=localhost/O=IPE/C=US"
```

Mount into Kong:

```yaml
# docker-compose.monitoring.yml or kong service override
volumes:
  - ../certs/ipe-dev.crt:/etc/kong/certs/tls.crt:ro
  - ../certs/ipe-dev.key:/etc/kong/certs/tls.key:ro
```

### 2.2 Production (Let's Encrypt / Vault)

| Source | Procedure |
|--------|-----------|
| **Let's Encrypt** | cert-manager `Certificate` CR → `secretName: ipe-kong-tls` in `ipe-platform` namespace |
| **HashiCorp Vault** | `vault write pki/issue/ipe common_name=api.customer.com ttl=720h` → sync to K8s Secret |
| **AWS ACM** | ALB/NLB terminates TLS; Kong receives HTTP on target group (same as demo pattern) |

Rotation: renew at **≤30 days** before expiry; cert-manager auto-renews at 2/3 lifetime.

---

## 3. Kong listener configuration

### 3.1 TLS termination (HTTPS on :8443)

Add to `infrastructure/docker/kong.yml` environment or compose:

```yaml
services:
  kong:
    environment:
      KONG_PROXY_LISTEN: "0.0.0.0:8000, 0.0.0.0:8443 ssl"
      KONG_SSL_CERT: /etc/kong/certs/tls.crt
      KONG_SSL_CERT_KEY: /etc/kong/certs/tls.key
    ports:
      - "8000:8000"
      - "8443:8443"
```

### 3.2 TLS passthrough (no termination at Kong)

```yaml
# Route with protocol tls_passthrough — Kong forwards encrypted stream
routes:
  - name: cap-svc-tls-passthrough
    protocols: ["tls"]
    snis: ["cap.internal.ipe.local"]
    service: cap-svc
```

Use when each microservice terminates its own TLS (uncommon for IPE demo).

### 3.3 Internal service HTTPS (optional per-service)

Enable Uvicorn TLS in service `Dockerfile` CMD:

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003", \
     "--ssl-keyfile", "/certs/service.key", "--ssl-certfile", "/certs/service.crt"]
```

Update Kong upstream URLs: `https://cap-svc:8003`.

---

## 4. Verification steps

### 4.1 Kong HTTPS listener

```powershell
curl.exe -vk https://localhost:8443/api/v1/health
# Expect: 200 or routed 401/404 (not connection refused)
```

### 4.2 Certificate chain

```powershell
openssl s_client -connect localhost:8443 -servername localhost </dev/null 2>$null |
  openssl x509 -noout -subject -dates -issuer
```

### 4.3 Internal service (when HTTPS enabled)

```powershell
curl.exe --cacert infrastructure/certs/ipe-dev.crt https://cap-svc:8003/api/v1/health
```

### 4.4 Demo regression after TLS change

```powershell
cd E:\AISOP\ipe
$env:IPE_API_BASE = "https://localhost:8443"
.\scripts\run-full-demo.ps1 -ReportPath docs\demo-run-report-tls.txt
```

---

## 5. Rotation procedure

1. Generate new cert/key pair (§2).
2. Deploy to Kong Secret/volume **before** expiry.
3. Rolling restart Kong: `docker compose restart kong` (zero downtime if two Kong replicas in K8s).
4. Verify §4.1–4.2.
5. Revoke old cert at CA if applicable.

**Dual-cert window:** Mount `tls.crt` + `tls-next.crt`; Kong 3.x supports multiple certs via SNI — use during cutover in production.

---

## 6. Rollback

| Step | Action |
|------|--------|
| 1 | Revert Kong env to `KONG_PROXY_LISTEN: 0.0.0.0:8000` (HTTP only) |
| 2 | `docker compose up -d kong` |
| 3 | Confirm demo: `.\scripts\run-full-demo.ps1` → **20/20** |
| 4 | Document incident in `docs/runbooks/incident-response.md` |

If only internal mTLS failed: disable Istio `PeerAuthentication` STRICT → PERMISSIVE, redeploy affected namespace.

---

## 7. Service port reference

| Service | Internal port | Health path |
|---------|---------------|-------------|
| dpe-svc | 8001 | `/api/v1/health` |
| mat-svc | 8002 | `/api/v1/health` |
| cap-svc | 8003 | `/api/v1/health` |
| fea-svc | 8004 | `/api/v1/health` |
| res-svc | 8005 | `/api/v1/health` |
| del-svc | 8006 | `/api/v1/health` |
| nlp-svc | 8007 | `/api/v1/health` |
| alert-svc | 8010 | `/api/v1/health` |
| Kong | 8000 / 8443 | `/` (admin 8001) |

---

## 8. Related artifacts

- `infrastructure/docker/docker-compose.yml` — service definitions
- `infrastructure/docker/kong.yml` — route matrix
- `infrastructure/k8s/istio/peer-authentication.yaml` — mTLS policy (staging/prod)
- Audit: `audit/v2/06-database-verification.md` (SEC-01 companion)
