# IPE API Reference

Unified REST API index. All public routes go through **Kong** at `http://localhost:8000` unless noted.

**Authentication:** JWT Bearer token (except `POST /api/v1/auth/login`).  
**Rate limit:** 300 req/min, 10,000 req/hr per consumer (Kong global plugin).  
**Tenant:** Injected as `X-Tenant-ID` header from JWT claim `tenant_id`.

---

## Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/login` | None | Login; returns JWT |
| GET | `/api/v1/auth/me` | JWT | Current user profile |

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"Ahmed@nour","password":"admin"}'
```

---

## dpe-svc (Demand, MDR, CTP)

| Prefix | Auth | Docs |
|--------|------|------|
| `/api/v1/demand` | JWT | [dpe-svc.md](api/dpe-svc.md) |
| `/api/v1/dashboard` | JWT | Control tower KPIs |
| `/api/v1/ctp` | JWT | Capable-to-promise |
| `/api/v1/sop` | JWT | S&OP workflows |
| `/api/v1/cost-accounting` | JWT | Activity-based costing |
| `/api/v1/financial` | JWT | Financial views |
| `/api/v1/edge` | JWT | Edge analytics |

---

## mat-svc (Material)

| Prefix | Auth | Docs |
|--------|------|------|
| `/api/v1/material` | JWT | [mat-svc.md](api/mat-svc.md) |

Key endpoints: `GET /material/requirements`, `POST /material/check-availability`

---

## cap-svc (Capacity & Schedule)

| Prefix | Auth | Docs |
|--------|------|------|
| `/api/v1/capacity` | JWT | [cap-svc.md](api/cap-svc.md) |

Key endpoints: `POST /capacity/solve`, `POST /capacity/schedule/approve`, `GET /capacity/cpm/cascade`

---

## fea-svc (Feasibility)

| Prefix | Auth | Docs |
|--------|------|------|
| `/api/v1/feasibility` | JWT | [fea-svc.md](api/fea-svc.md) |

---

## res-svc, del-svc, rec-svc

| Service | Prefix | Docs |
|---------|--------|------|
| res-svc | `/api/v1/resolution` | [res-svc.md](api/res-svc.md) |
| del-svc | `/api/v1/delay`, `/api/v1/quality` | [del-svc.md](api/del-svc.md) |
| rec-svc | `/api/v1/reconciliation` | — |

---

## nlp-svc (Copilot)

| Prefix | Auth | Docs |
|--------|------|------|
| `/api/v1/copilot` | JWT | [nlp-svc.md](api/nlp-svc.md) |
| `/api/v1/nlp` | JWT | NLP utilities |

---

## alert-svc (War Room)

| Prefix | Auth | Docs |
|--------|------|------|
| `/api/v1/alert` | JWT | Alerts |
| `/api/v1/war-room` | JWT | Chaos recovery |

---

## Health Checks

Each service exposes `/healthz` (direct port, not via Kong):

```bash
curl http://localhost:8001/healthz  # dpe-svc
curl http://localhost:8003/healthz  # cap-svc
```

---

## OpenAPI

Interactive Swagger UI per service:

| Service | URL |
|---------|-----|
| dpe-svc | http://localhost:8001/docs |
| mat-svc | http://localhost:8002/docs |
| cap-svc | http://localhost:8003/docs |

---

## Kong Route Source

Authoritative route definitions: `infrastructure/docker/kong.yml`

Per-service detail: `docs/api/*.md`
