# Service Restart Runbook

Ordered restart procedure for the IPE demo/production stack. Restart **gateway first** after auth changes (see `jwt-rotation.md`).

---

## Demo Stack (docker-compose.demo.yml)

**Working directory:** `infrastructure/docker`

### Full Stack Restart

```powershell
docker compose -f docker-compose.yml -f docker-compose.demo.yml down
docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d
```

Wait until all health checks pass (`docker compose ps`).

### Ordered Partial Restart

Use when rolling config changes without full downtime:

| Order | Service | Container pattern | Notes |
|-------|---------|-------------------|-------|
| 1 | Kong | `docker-kong-1` | Gateway; picks up route/plugin changes |
| 2 | dpe-svc | `docker-dpe-svc-1` | Auth, MDR, demand |
| 3 | mat-svc | `docker-mat-svc-1` | Material / ATP |
| 4 | cap-svc | `docker-cap-svc-1` | Capacity / schedule |
| 5 | fea-svc | `docker-fea-svc-1` | Feasibility gates |
| 6 | res-svc | `docker-res-svc-1` | Resolution |
| 7 | del-svc | `docker-del-svc-1` | Delay |
| 8 | nlp-svc | `docker-nlp-svc-1` | Copilot |
| 9 | rec-svc | `docker-rec-svc-1` | Recommendations |
| 10 | alert-svc | `docker-alert-svc-1` | War room / alerts |
| 11 | connector | `docker-connector-1` | ERP adapter |
| 12 | Frontend | `docker-frontend-1` | React SPA |

```powershell
# Example: restart Kong then dpe-svc
docker restart docker-kong-1
Start-Sleep -Seconds 5
docker restart docker-dpe-svc-1
```

### Infrastructure (restart only if needed)

| Service | When to restart |
|---------|-----------------|
| db (PostgreSQL) | After migration; **causes brief outage** |
| kafka / zookeeper | Consumer lag or broker errors |
| redis | Cache corruption |
| migrate | Run once: `docker compose run --rm migrate` |

---

## Post-Restart Verification

```powershell
# Health checks via Kong
curl http://localhost:8000/api/v1/healthz

# Demo smoke (subset)
python scripts\run_demo.py --checkpoints 1,5,10,20
```

---

## Related Runbooks

- [JWT Rotation](jwt-rotation.md)
- [TLS Internal](tls-internal.md)
- [Disaster Recovery](disaster-recovery.md)
- [Incident Response](incident-response.md)
