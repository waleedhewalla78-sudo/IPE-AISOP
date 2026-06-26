# Ops Monitoring — REL-PROD Wave 2D

**Date:** 2026-06-26  
**Stack:** Demo overlay + monitoring overlay  
**Purpose:** Close audit R-08 (log aggregation) and ops readiness gap for v6.1.0

## Components

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3002 | `admin` / `ipe_admin` |
| **Prometheus** | http://localhost:9091 | — |
| **Loki** | http://localhost:3100 | — |

## Quick Start

```powershell
cd E:\AISOP\ipe

# 1. Ensure demo app stack is up
.\scripts\rel-demo-stack.ps1 -SkipBuild

# 2. Start monitoring overlay
.\scripts\run-monitoring-stack.ps1

# 3. Verify
.\scripts\run-monitoring-stack.ps1 -VerifyOnly
```

Compose files used:

```text
docker-compose.yml + docker-compose.demo.yml + docker-compose.monitoring.yml
```

## What It Provides

- **Prometheus** scrapes `/metrics` on all demo microservices + Kong admin (`kong:8001`)
- **Loki** stores container logs via **Promtail** (Docker socket discovery)
- **Grafana** provisions Prometheus + Loki datasources and **IPE REL-PROD Overview** dashboard

## Dashboards

| Dashboard | UID | Metrics |
|-----------|-----|---------|
| IPE REL-PROD Overview | `ipe-rel-prod-overview` | `ipe_http_requests_total`, latency histogram, Loki logs |
| IPE Service Health | `ipe-service-health` | Legacy panel queries (may need metric rename) |

## Files

| Path | Role |
|------|------|
| `infrastructure/docker/docker-compose.monitoring.yml` | Overlay services |
| `infrastructure/monitoring/prometheus.demo.yml` | Scrape config (demo hostnames) |
| `infrastructure/monitoring/loki-config.yaml` | Loki single-node config |
| `infrastructure/monitoring/promtail-config.yml` | Docker log shipping |
| `infrastructure/monitoring/grafana-datasources.yml` | Prometheus + Loki |
| `scripts/run-monitoring-stack.ps1` | Start + verify |

## Evidence

- Verification log: `docs/ops-monitoring-verify.txt`
- Run after k6 or chaos to correlate metrics + logs

## Known Limits (MVP)

- No Alertmanager routing (rules file present but not wired)
- Kong `/metrics` may 404 unless admin plugin enabled — app service targets are primary
- Promtail requires Docker socket access (Docker Desktop on Windows)
- TLS/mTLS not configured (C-03 remains open for production)

## Audit Impact

Closes **R-08** (no log aggregation) at MVP level. Estimated **+2 points** (~89 → **~91/100**).
