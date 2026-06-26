# IPE Deployment Guide

Docker Compose deployment for local demo and REL-PROD validation.

---

## Prerequisites

- Docker Desktop 4.x+
- 16 GB RAM recommended
- PowerShell 7+ (Windows) or bash

---

## Quick Start (Demo Stack)

```powershell
cd E:\AISOP\ipe
.\scripts\rel-demo-stack.ps1
```

Or manually:

```powershell
cd infrastructure\docker
docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d
docker compose run --rm migrate
```

---

## Environment Variables

Copy template and customize:

```powershell
copy .env.example .env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `IPE_DATABASE_URL` | Yes | PostgreSQL connection string |
| `IPE_JWT_SECRET_KEY` | Yes | JWT signing secret |
| `IPE_KAFKA_BOOTSTRAP_SERVERS` | Yes | Kafka broker list |
| `IPE_REDIS_URL` | Yes | Redis connection |
| `ANTHROPIC_API_KEY` | For copilot | LLM API key |
| `IPE_OTEL_EXPORTER_OTLP_ENDPOINT` | Optional | OpenTelemetry collector |

Full list: `.env.example`, `.env.template`

---

## Compose Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Base 14+ services + infra |
| `docker-compose.demo.yml` | Demo overlay (trimmed stack) |
| `docker-compose.monitoring.yml` | Loki + Prometheus + Grafana |
| `docker-compose.secrets.yml` | Production secrets overlay |

---

## Ports

See [architecture.md](architecture.md#port-map). Kong public API: **8000**.

---

## Migrations

```powershell
cd infrastructure\docker
docker compose run --rm migrate
```

Alembic versions: `migrations/versions/`

---

## Monitoring Stack

```powershell
.\scripts\run-monitoring-stack.ps1
```

See [ops-monitoring.md](ops-monitoring.md).

---

## Production Notes

- Use `docker-compose.secrets.yml` for sensitive values
- Enable TLS per [runbooks/tls-internal.md](runbooks/tls-internal.md)
- Rotate JWT per [runbooks/jwt-rotation.md](runbooks/jwt-rotation.md)
- Kubernetes manifests: `infrastructure/k8s/` (staging/production overlays)

---

## Verification

```powershell
docker compose ps
python scripts\run_demo.py --all
```

Expected: demo **20/20**, chaos **6/6**.

---

## Related

- [Runbooks](runbooks/deployment.md) — K8s/ArgoCD production path
- [Service Restart](runbooks/service-restart.md)
- [Disaster Recovery](runbooks/disaster-recovery.md)
