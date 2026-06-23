# IPE Platform — Admin Guide

**Version:** 1.0.0  
**Last Updated:** June 2026

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Architecture Overview](#2-architecture-overview)
3. [System Installation & Startup](#3-system-installation--startup)
4. [Configuration & Settings](#4-configuration--settings)
5. [User & Role Management](#5-user--role-management)
6. [API Gateway (Kong)](#6-api-gateway-kong)
7. [Authentication & Security](#7-authentication--security)
8. [Database Management](#8-database-management)
9. [Kafka Event Mesh](#9-kafka-event-mesh)
10. [Service Management](#10-service-management)
11. [Monitoring & Observability](#11-monitoring--observability)
12. [Compliance & Audit](#12-compliance--audit)
13. [ML Model Management](#13-ml-model-management)
14. [ERP Integration (Connector)](#14-erp-integration-connector)
15. [Backup & Recovery](#15-backup--recovery)
16. [Troubleshooting](#16-troubleshooting)
17. [API Reference Quick Reference](#17-api-reference-quick-reference)
18. [Index](#18-index)

---

## 1. Introduction

### Purpose

This guide covers system administration tasks for the IPE platform, including:

- Installation and startup procedures
- System configuration and security settings
- User management and access control
- Database, messaging, and infrastructure management
- Monitoring, compliance, and troubleshooting

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Linux (Ubuntu 20.04+), macOS, Windows with WSL2 | Ubuntu 22.04 LTS |
| **Docker** | 20.10+ | 24.0+ |
| **Docker Compose** | v2.0+ | v2.20+ |
| **RAM** | 8 GB | 16 GB |
| **Disk** | 50 GB free | 100 GB SSD |
| **CPU** | 4 cores | 8 cores |
| **Network** | Internet for image pulls | Stable connection |

### Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| API Gateway | Kong | 3.7 |
| Identity | Keycloak | Latest |
| Database | PostgreSQL | 16 |
| Cache | Redis | 7 |
| Messaging | Apache Kafka | 7.7 |
| Schema Registry | Confluent Schema Registry | 7.7 |
| Observability | OpenTelemetry + Jaeger + Prometheus + Grafana | Latest |
| ML Tracking | MLflow | Latest |
| Orchestration | Docker Compose | v2 |
| Container Images | Python 3.12-slim, uv | — |

---

## 2. Architecture Overview

### Service Map

```
                         ┌─────────────────────┐
                         │   Kong API Gateway   │
                         │      :8000           │
                         │ JWT · Rate Limit     │
                         │ CORS · Correlation   │
                         └─────────┬───────────┘
                                   │
        ┌──────────┬───────────┬───┴───┬───────────┬──────────┐
        │          │           │       │           │          │
   ┌────▼───┐ ┌───▼────┐ ┌───▼───┐ ┌─▼─────┐ ┌──▼───┐ ┌───▼────┐
   │dpe-svc │ │mat-svc │ │cap-svc│ │fea-svc│ │res-svc│ │del-svc │
   │:8020   │ │:8002   │ │:8003  │ │:8004  │ │:8005  │ │:8006   │
   └────────┘ └────────┘ └───────┘ └───────┘ └───────┘ └────────┘
        │          │           │       │           │          │
   ┌────▼───┐ ┌───▼────┐ ┌───▼───┐ ┌─▼─────┐ ┌──▼───┐ ┌───▼────┐
   │nlp-svc │ │rec-svc │ │alert- │ │sustain│ │quality│ │scn-svc │
   │:8007   │ │:8008   │ │svc    │ │svc    │ │svc   │ │:8014   │
   └────────┘ └────────┘ │:8010  │ │:8012  │ │:8013 │ └────────┘
                         └───────┘ └───────┘ └──────┘
   ┌──────────┐ ┌───────────┐
   │network-  │ │ml-svc     │
   │svc :8015 │ │:8016      │
   └──────────┘ └───────────┘
        │
┌───────▼──────────────────────────────────────────────┐
│  PostgreSQL · Redis · Kafka · Schema Registry        │
│  Keycloak · Jaeger · OTel Collector · Prometheus     │
│  Grafana · MLflow · ArgoCD                           │
└──────────────────────────────────────────────────────┘
```

### Port Map

| Service | Internal Port | External Port | Health Endpoint |
|---------|--------------|---------------|-----------------|
| Kong Gateway | 8000 | 8000 | `GET /` |
| dpe-svc | 8001 | 8020 | `GET /api/v1/health` |
| mat-svc | 8002 | 8002 | `GET /api/v1/health` |
| cap-svc | 8003 | 8003 | `GET /api/v1/health` |
| fea-svc | 8004 | 8004 | `GET /api/v1/health` |
| res-svc | 8005 | 8005 | `GET /api/v1/health` |
| del-svc | 8006 | 8006 | `GET /api/v1/health` |
| nlp-svc | 8007 | 8007 | `GET /api/v1/health` |
| rec-svc | 8008 | 8008 | `GET /api/v1/health` |
| connector | 8009 | 8011 | `GET /api/v1/health` |
| alert-svc | 8010 | 8010 | `GET /api/v1/health` |
| sustain-svc | 8012 | 8012 | `GET /api/v1/health` |
| quality-svc | 8013 | 8013 | `GET /api/v1/health` |
| scn-svc | 8014 | 8014 | `GET /api/v1/health` |
| network-svc | 8015 | 8015 | `GET /api/v1/health` |
| ml-svc | 8016 | 8016 | `GET /api/v1/health` |
| PostgreSQL | 5432 | 5432 | — |
| Redis | 6379 | 6380 | — |
| Kafka | 9092 | 9092 | — |
| Zookeeper | 2181 | — | — |
| Keycloak | 8180 | 8180 | — |
| Jaeger | 16686 | 16686 | `GET /` |
| Prometheus | 9091 | 9091 | `GET /-/healthy` |
| Grafana | 3002 | 3002 | `GET /api/health` |
| MLflow | 5000 | 5000 | `GET /health` |

---

## 3. System Installation & Startup

### 3.1 Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose (if not included)
sudo apt install docker-compose-plugin

# Verify
docker --version
docker compose version
```

### 3.2 Clone and Build

```bash
# Clone the repository
git clone <repository-url> ipe
cd ipe

# Build all service images
docker compose -f infrastructure/docker/docker-compose.yml build
```

### 3.3 Start Infrastructure First

```bash
# Start databases, messaging, and cache
docker compose -f infrastructure/docker/docker-compose.yml up -d \
  db zookeeper kafka redis

# Wait for health checks
docker compose -f infrastructure/docker/docker-compose.yml ps
# Wait until db and redis show "healthy"
```

### 3.4 Run Database Migrations

```bash
# Start the migration service
docker compose -f infrastructure/docker/docker-compose.yml up -d migrate

# Verify migrations applied
docker compose -f infrastructure/docker/docker-compose.yml logs migrate
# Should see: "Upgrade complete" or similar success message
```

### 3.5 Start Application Services

```bash
# Start all application services
docker compose -f infrastructure/docker/docker-compose.yml up -d \
  dpe-svc mat-svc cap-svc fea-svc res-svc del-svc nlp-svc \
  rec-svc alert-svc sustain-svc quality-svc scn-svc network-svc \
  connector ml-svc

# Start the API gateway
docker compose -f infrastructure/docker/docker-compose.yml up -d kong

# Start observability stack
docker compose -f infrastructure/docker/docker-compose.yml up -d \
  otel-collector jaeger keycloak mlflow
```

### 3.6 Seed Sample Data

```bash
# Load reference data (tenants, products, suppliers, work centers)
bash scripts/seed-data.sh
```

### 3.7 Verify Installation

```bash
# Check all services are healthy
docker compose -f infrastructure/docker/docker-compose.yml ps

# Test health endpoints
curl -s http://localhost:8020/api/v1/health | jq .
curl -s http://localhost:8002/api/v1/health | jq .

# Test Kong gateway
curl -s -H "X-Tenant-ID: a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11" \
  http://localhost:8000/api/v1/health | jq .

# Run the demo walkthrough
bash scripts/demo_walkthrough.sh
```

### 3.8 Stopping the System

```bash
# Stop all services (preserves data)
docker compose -f infrastructure/docker/docker-compose.yml down

# Stop and remove volumes (WARNING: deletes all data)
docker compose -f infrastructure/docker/docker-compose.yml down -v
```

---

## 4. Configuration & Settings

### 4.1 Environment Variables

All settings use the `IPE_` prefix. Set via environment variables or `.env` file.

**Critical Settings (must configure for production):**

| Variable | Default | Description |
|----------|---------|-------------|
| `IPE_JWT_SECRET_KEY` | `""` | HMAC signing key for JWT tokens. **Required in production.** Generate with: `openssl rand -hex 32` |
| `IPE_DATABASE_URL` | `postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev` | PostgreSQL connection string |
| `IPE_KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker addresses |
| `IPE_REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `IPE_ENVIRONMENT` | `development` | Set to `production` for live deployments |

**Optional Settings:**

| Variable | Default | Description |
|----------|---------|-------------|
| `IPE_KEYCLOAK_URL` | `""` | Keycloak server URL for SSO |
| `IPE_ANTHROPIC_API_KEY` | `""` | Anthropic Claude API key for NLP copilot |
| `IPE_SENTRY_DSN` | `""` | Sentry error tracking DSN |
| `IPE_PAGERDUTY_ROUTING_KEY` | `""` | PagerDuty integration key |
| `IPE_ALERTMANAGER_URL` | `""` | Alertmanager URL |
| `IPE_OTEL_EXPORTER_OTLP_ENDPOINT` | `""` | OpenTelemetry collector endpoint |
| `IPE_OTEL_TRACING_ENABLED` | `True` | Enable distributed tracing |
| `IPE_OTEL_LOGGING_ENABLED` | `True` | Enable structured logging |
| `IPE_JWT_USE_JWKS` | `False` | Enable JWKS-based token validation |
| `IPE_JWT_JWKS_URL` | `""` | JWKS endpoint URL |
| `IPE_JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token TTL |
| `IPE_JWT_REFRESH_TOKEN_EXPIRE_MINUTES` | `1440` | Refresh token TTL (24h) |

### 4.2 Docker Compose Environment

The `docker-compose.yml` passes environment variables to each container. Key overrides:

```yaml
# Example: Setting JWT secret in docker-compose.yml
environment:
  - IPE_JWT_SECRET_KEY=${IPE_JWT_SECRET_KEY:-change-me-in-production}
  - IPE_DATABASE_URL=postgresql+asyncpg://ipe:ipe_dev_pass@db:5432/ipe_dev
  - IPE_KAFKA_BOOTSTRAP_SERVERS=kafka:9092
  - IPE_REDIS_URL=redis://redis:6379/0
```

### 4.3 Tenant Configuration

Each tenant has configurable settings accessible via the Admin page or API:

**Priority Weights** (used by demand classification):

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| `customer_margin` | 0.25 | 0–1 | Weight for customer margin importance |
| `urgency` | 0.30 | 0–1 | Weight for due date urgency |
| `strategic` | 0.15 | 0–1 | Weight for strategic product classification |
| `penalty` | 0.10 | 0–1 | Weight for late delivery penalty |

**Feasibility Thresholds:**

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| `auto_confirm_threshold` | 90 | 0–100 | Score above which MOs auto-confirm |
| `planner_threshold` | 70 | 0–100 | Score above which MOs go to planner queue |

**Autonomy Mode:**

| Mode | Behavior |
|------|----------|
| **Shadow** | AI makes recommendations only; no automatic actions |
| **Suggest** | AI suggests actions; planner must approve |
| **Autonomous** | AI takes automatic action on high-confidence decisions |

### 4.4 Admin Console (UI)

Navigate to `/admin` in the web interface:

**Configuration Tab:**
- Adjust priority weights with number inputs (0–1, step 0.01)
- Set feasibility thresholds (0–100)
- Toggle autonomy mode (Shadow / Suggest / Autonomous)
- Click **Save Configuration** to apply

**Data Quality Tab:**
- View BOM Completeness percentage
- View Lead Time Accuracy percentage
- View Inventory Record Accuracy percentage
- Each metric shows a badge: Good / Needs Review / Critical

### 4.5 Admin Console (API)

```bash
# Get current configuration
curl -s -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: $TENANT_ID" \
  http://localhost:8000/api/v1/admin/config | jq .

# Update configuration
curl -s -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: $TENANT_ID" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/admin/config \
  -d '{
    "priority_weights": {"customer_margin": 0.30, "urgency": 0.35},
    "autonomy_mode": "suggest"
  }' | jq .

# Get data quality report
curl -s -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-ID: $TENANT_ID" \
  http://localhost:8000/api/v1/admin/data-quality | jq .
```

---

## 5. User & Role Management

### 5.1 RBAC Roles

| Role | Permissions | Typical Users |
|------|------------|---------------|
| `admin` | read, write, approve, admin, delete, run_solver, cost_optimize, manage_users | System administrators |
| `planner` | read, write, approve, run_solver, cost_optimize, view_copilot, run_scenario | Production planners |
| `supervisor` | read, acknowledge_disruption, view_schedule, view_copilot | Shop floor supervisors |
| `auditor` | read, view_audit_logs, view_kpis, view_scenarios | Compliance auditors |
| `manager` | read, write, approve, run_solver, cost_optimize | Operations managers |
| `operator` | read, write_own | Shop floor operators |
| `executive` | read, view_kpis | C-level executives |

### 5.2 Keycloak User Management

IPE uses Keycloak for identity management. Access the Keycloak admin console:

```bash
# Keycloak admin URL
open http://localhost:8180

# Default admin credentials
# Username: admin
# Password: admin (change in production!)
```

**Creating a New User:**

1. Log in to Keycloak admin console
2. Select the `ipe` realm
3. Go to **Users** → **Add User**
4. Fill in: Username, Email, First Name, Last Name
5. Click **Create**
6. Go to **Credentials** tab → Set password
7. Go to **Role Mappings** tab → Assign realm role (admin, planner, etc.)
8. The user can now log in to IPE

### 5.3 SCIM 2.0 Provisioning

IPE supports SCIM 2.0 for automated user provisioning from identity providers (Azure AD, Okta):

**Available SCIM Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/scim/v2/Users` | List users |
| POST | `/api/v1/scim/v2/Users` | Create user |
| GET | `/api/v1/scim/v2/Users/{id}` | Get user |
| PUT | `/api/v1/scim/v2/Users/{id}` | Update user |
| DELETE | `/api/v1/scim/v2/Users/{id}` | Delete user |
| GET | `/api/v1/scim/v2/Groups` | List groups |
| POST | `/api/v1/scim/v2/Groups` | Create group |

**Example: Create user via SCIM**

```bash
curl -X POST http://localhost:8000/api/v1/scim/v2/Users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
    "userName": "planner1",
    "emails": [{"value": "planner1@company.com", "primary": true}],
    "name": {"givenName": "Jane", "familyName": "Doe"},
    "active": true
  }'
```

### 5.4 JWT Token Structure

Tokens contain these claims:

```json
{
  "sub": "user-uuid",
  "tenant_id": "tenant-uuid",
  "role": "planner",
  "type": "access",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "unique-token-id",
  "iss": "keycloak-url",
  "aud": "ipe-platform"
}
```

### 5.5 Demo JWT (Development)

For testing without Keycloak:

```bash
# Generate a demo JWT
curl -s http://localhost:8000/api/v1/keycloak/demo-jwt/admin | jq .

# Use the token in requests
TOKEN=$(curl -s http://localhost:8000/api/v1/keycloak/demo-jwt/admin | jq -r .token)
curl -H "Authorization: Bearer $TOKEN" \
     -H "X-Tenant-ID: a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11" \
     http://localhost:8000/api/v1/demand/queue
```

---

## 6. API Gateway (Kong)

### 6.1 Kong Configuration

Kong is configured declaratively via `infrastructure/docker/kong.yml`.

**Global Plugins:**

| Plugin | Configuration | Purpose |
|--------|--------------|---------|
| `rate-limiting` | 300 req/min, 10,000 req/hr, `local` policy | Prevent abuse |
| `request-transformer` | Strip `X-Tenant-ID` from client | Security: tenant ID comes from JWT only |
| `correlation-id` | `X-Correlation-ID` header, UUID generator | Distributed tracing |
| `jwt` | `claims_to_verify: ["exp"]` | Token validation on all routes |

### 6.2 Route Configuration

Each service has routes defined in Kong. Example route structure:

```yaml
services:
  - name: dpe-svc
    url: http://dpe-svc:8001
    routes:
      - name: dpe-demand
        paths: ["/api/v1/demand"]
        plugins:
          - name: jwt
            config:
              claims_to_verify: [exp]
          - name: request-transformer
            config:
              add:
                headers: ["X-Tenant-ID:$(jwt_claim_tenant_id)"]
```

### 6.3 Adding a New Route

To add a route for a new service:

1. Edit `infrastructure/docker/kong.yml`
2. Add the service definition:

```yaml
- name: new-svc
  url: http://new-svc:8020
  routes:
    - name: new-svc-route
      paths: ["/api/v1/new-feature"]
      plugins:
        - name: jwt
          config:
            claims_to_verify: [exp]
        - name: request-transformer
          config:
            add:
              headers: ["X-Tenant-ID:$(jwt_claim_tenant_id)"]
```

3. Rebuild and restart Kong:

```bash
docker compose -f infrastructure/docker/docker-compose.yml up -d kong
```

### 6.4 Rate Limiting Tuning

Adjust rate limits in `kong.yml`:

```yaml
plugins:
  - name: rate-limiting
    config:
      minute: 500      # Increase for high-traffic
      hour: 20000
      policy: local     # Use "redis" for distributed rate limiting
```

For distributed rate limiting with Redis:

```yaml
plugins:
  - name: rate-limiting
    config:
      minute: 500
      hour: 20000
      policy: redis
      redis_host: redis
      redis_port: 6379
```

---

## 7. Authentication & Security

### 7.1 Authentication Flow

```
User → LoginForm → POST /api/v1/auth/login
     → Keycloak validates credentials
     → Returns JWT access_token + refresh_token
     → Frontend stores in localStorage
     → All API requests include: Authorization: Bearer <token>
     → Kong validates JWT signature and expiry
     → Kong injects X-Tenant-ID from JWT claim
     → Backend validates role permissions
```

### 7.2 JWT Token Management

**Access Token:** Valid for 60 minutes (configurable)
**Refresh Token:** Valid for 24 hours (configurable)

**Token refresh flow:**
1. Frontend detects 401 response
2. Attempts refresh with refresh_token
3. If refresh succeeds, updates stored tokens
4. If refresh fails, redirects to login

### 7.3 JWKS Support (Production)

For production with external identity providers:

```bash
# Enable JWKS mode
IPE_JWT_USE_JWKS=True
IPE_JWT_JWKS_URL=https://your-keycloak.com/realms/ipe/protocol/openid-connect/certs
```

When JWKS is enabled:
- Tokens are validated using RS256 (asymmetric)
- Public keys are fetched from the JWKS endpoint
- Keys are cached with TTL for performance

### 7.4 Edge Gateway Authentication

For IoT and edge devices:

| Header | Description |
|--------|-------------|
| `X-API-Key` | API key for the edge device |
| `X-Gateway-ID` | Gateway identifier |
| `X-SSL-Client-Cert` | Client certificate (mTLS) |
| `X-SSL-Client-Verify` | Must be `SUCCESS` |

### 7.5 mTLS Configuration (Istio)

For Kubernetes deployments with Istio service mesh:

```yaml
# PeerAuthentication - enforce strict mTLS
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: ipe-platform
spec:
  mtls:
    mode: STRICT

# DestinationRule - use ISTIO_MUTUAL TLS
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: default
  namespace: ipe-platform
spec:
  host: "*.ipe-platform.svc.cluster.local"
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
```

### 7.6 CORS Configuration

CORS is restricted to specific origins:

```yaml
# In each service's main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8082"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
)
```

---

## 8. Database Management

### 8.1 PostgreSQL Connection

```bash
# Connect to PostgreSQL
docker exec -it docker-db-1 psql -U ipe -d ipe_dev

# Connection string
postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev
```

### 8.2 Alembic Migrations

```bash
# Run all pending migrations
docker compose -f infrastructure/docker/docker-compose.yml up -d migrate

# Or run manually
cd migrations
alembic upgrade head

# Check current migration version
alembic current

# Rollback one migration
alembic downgrade -1

# Create a new migration
alembic revision --autogenerate -m "description of changes"
```

### 8.3 Migration Files

Migration files are in `migrations/versions/`:

| Migration | Description |
|-----------|-------------|
| 001 | Initial schema (all core tables with RLS) |
| 002–003 | Schema refinements |
| 007 | Energy cost columns (work center, shift) |
| 008 | Plant, transfer route, transport fleet tables |
| 009 | Quality event table |
| 010 | Emission factor, material carbon, transport emission tables |
| 011 | Financial projection table |
| 013 | User table enhancements |
| 014 | Location table |
| 016 | S&OP forecast and plan tables |
| 017 | SOC 2 compliance tables |
| 018 | GDPR DSAR and consent tables |
| 019 | Alert incident table |
| 020 | Tenant ID on maintenance window |
| 021 | Audit log immutability (REVOKE + trigger) |

### 8.4 Row-Level Security (RLS)

All tables with `tenant_id` have RLS policies:

```sql
-- Policy: tenant isolation
CREATE POLICY tenant_isolation ON cdm_manufacturing_order
  USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
```

**How it works:**
1. Each database session sets `app.current_tenant_id` via `SET LOCAL`
2. The RLS policy filters rows to only show data for that tenant
3. Cross-tenant data access is impossible at the database level

**Verify RLS is active:**

```sql
-- Check policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE schemaname = 'public';

-- Count tables with RLS
SELECT COUNT(*) FROM pg_tables
WHERE schemaname = 'public'
  AND tablename LIKE 'cdm_%'
  AND tablename IN (
    SELECT tablename FROM pg_policies
    WHERE schemaname = 'public'
  );
```

### 8.5 Backup Procedures

```bash
# Backup database
docker exec docker-db-1 pg_dump -U ipe ipe_dev > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20260621.sql | docker exec -i docker-db-1 psql -U ipe -d ipe_dev

# Automated daily backup (add to crontab)
0 2 * * * docker exec docker-db-1 pg_dump -U ipe ipe_dev > /backups/ipe_$(date +\%Y\%m\%d).sql
```

---

## 9. Kafka Event Mesh

### 9.1 Topic Overview

| Topic | Producer | Consumer | Purpose |
|-------|----------|----------|---------|
| `ipe.demand.created` | connector | dpe-svc | New demand from ERP |
| `ipe.demand.classified` | dpe-svc | mat-svc | Priority-scored demand |
| `ipe.mo.material_scored` | mat-svc | fea-svc | Material availability result |
| `ipe.supply.delay_detected` | mat-svc | alert-svc | Supply delay alert |
| `ipe.mo.feasibility_scored` | fea-svc | res-svc, WS | Feasibility score result |
| `ipe.mo.capacity_scored` | cap-svc | — | Capacity scoring |
| `ipe.resolution.proposed` | res-svc | — | Resolution scenario proposed |
| `ipe.resolution.approved` | res-svc | connector | Resolution approved, sync to ERP |
| `ipe.delay.logged` | del-svc | — | Delay event logged |
| `ipe.quality.event_created` | del-svc | — | Quality event created |
| `ipe.copilot.queried` | nlp-svc | — | Copilot query logged |
| `ipe.iot.telemetry` | cap-svc | — | IoT telemetry data |
| `ipe.po.suggested` | mat-svc | connector | PO suggestion to ERP |
| `ipe.reconciliation.completed` | rec-svc | — | Reconciliation completed |
| `ipe.inventory.changed` | mat-svc | dpe-svc | Inventory change notification |

### 9.2 Schema Registry

Avro schemas are registered at `http://localhost:8081`:

```bash
# List registered subjects
curl -s http://localhost:8081/subjects | jq .

# Check a specific schema
curl -s http://localhost:8081/subjects/ipe.demand.created-value/versions/latest | jq .

# Register a new schema
curl -X POST http://localhost:8081/subjects/ipe.new.event-value/versions \
  -H "Content-Type: application/json" \
  -d '{
    "schema": "{\"type\":\"record\",\"name\":\"NewEvent\",\"fields\":[{\"name\":\"tenant_id\",\"type\":\"string\"}]}"
  }'
```

### 9.3 Creating a New Topic

```bash
# Create topic with 6 partitions
docker exec docker-kafka-1 kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic ipe.new.topic \
  --partitions 6 \
  --replication-factor 1

# List all topics
docker exec docker-kafka-1 kafka-topics --list \
  --bootstrap-server localhost:9092

# Describe a topic
docker exec docker-kafka-1 kafka-topics --describe \
  --bootstrap-server localhost:9092 \
  --topic ipe.demand.created
```

### 9.4 Monitoring Kafka

- **Kafka UI**: `http://localhost:8080` — web-based topic and consumer group monitoring
- **Prometheus metrics**: Kafka exporter metrics at `:9308/metrics`

### 9.5 DLQ (Dead Letter Queue)

Failed event processing publishes to `ipe.dlq.{service_name}`:

```bash
# Monitor DLQ messages
docker exec docker-kafka-1 kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic ipe.dlq.dpe-svc \
  --from-beginning
```

---

## 10. Service Management

### 10.1 Starting Individual Services

```bash
# Start a specific service
docker compose -f infrastructure/docker/docker-compose.yml up -d dpe-svc

# Restart a service
docker compose -f infrastructure/docker/docker-compose.yml restart dpe-svc

# Stop a service
docker compose -f infrastructure/docker/docker-compose.yml stop dpe-svc

# View service logs
docker compose -f infrastructure/docker/docker-compose.yml logs -f dpe-svc

# View last 100 lines
docker compose -f infrastructure/docker/docker-compose.yml logs --tail=100 dpe-svc
```

### 10.2 Rebuilding a Service

After code changes:

```bash
# Rebuild a single service
docker compose -f infrastructure/docker/docker-compose.yml build dpe-svc

# Rebuild without cache
docker compose -f infrastructure/docker/docker-compose.yml build --no-cache dpe-svc

# Restart with new image
docker compose -f infrastructure/docker/docker-compose.yml up -d dpe-svc
```

### 10.3 Service Health Checks

Each service has a Docker health check configured:

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8001/api/v1/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 15s
```

**Check health status:**

```bash
docker compose -f infrastructure/docker/docker-compose.yml ps
# Look for "healthy" status
```

### 10.4 Resource Limits

Add resource limits to prevent a single service from consuming all resources:

```yaml
# In docker-compose.yml
services:
  dpe-svc:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## 11. Monitoring & Observability

### 11.1 OpenTelemetry

IPE uses OpenTelemetry for unified tracing, metrics, and logging.

**Setup:**

```python
# In each service's main.py
from ipe_shared.observability import setup_observability

app = create_app()
setup_observability(app, service_name="dpe-svc")
```

**What it instruments:**
- FastAPI HTTP requests/responses
- HTTPX outgoing requests
- Redis operations
- AsyncPG database queries
- Custom business spans

### 11.2 Jaeger (Distributed Tracing)

Access at: `http://localhost:16686`

- View distributed traces across services
- Search by service name, operation, duration
- Analyze latency bottlenecks

### 11.3 Prometheus (Metrics)

Access at: `http://localhost:9091`

**Key metrics:**

| Metric | Description |
|--------|-------------|
| `http_requests_total` | Total HTTP requests |
| `http_request_duration_seconds` | Request latency histogram |
| `kafka_messages_produced_total` | Messages produced |
| `kafka_messages_consumed_total` | Messages consumed |
| `db_query_duration_seconds` | Database query latency |
| `redis_operation_duration_seconds` | Redis operation latency |

### 11.4 Grafana (Dashboards)

Access at: `http://localhost:3002`

**Pre-built dashboards:**
- Service overview (request rate, error rate, latency)
- Kafka consumer lag
- Database connection pool
- k6 load test results

### 11.5 Alerting

IPE integrates with:

- **PagerDuty**: For critical alerts
- **Alertmanager**: For Prometheus alert rules

**Configure PagerDuty:**

```bash
IPE_PAGERDUTY_ROUTING_KEY=your-routing-key
```

**Trigger a PagerDuty incident:**

```bash
curl -X POST http://localhost:8000/api/v1/incidents/pagerduty \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "Production line 3 down",
    "severity": "critical",
    "source": "ipe",
    "component": "cap-svc"
  }'
```

---

## 12. Compliance & Audit

### 12.1 SOC 2 Compliance

**View SOC 2 control status:**

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/compliance/soc2/summary | jq .
```

**Response:**
```json
{
  "total_controls": 21,
  "implemented": 18,
  "coverage_pct": 85.7,
  "principles": {
    "security": {"total": 8, "implemented": 7},
    "availability": {"total": 4, "implemented": 4},
    "processing_integrity": {"total": 3, "implemented": 3},
    "confidentiality": {"total": 3, "implemented": 2},
    "privacy": {"total": 3, "implemented": 2}
  }
}
```

### 12.2 GDPR DSAR Management

**Create a Data Subject Access Request:**

```bash
curl -X POST http://localhost:8000/api/v1/dsar/requests \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "user-12345",
    "request_type": "access",
    "description": "Data subject access request"
  }'
```

**Process a DSAR:**

```bash
# Start processing
curl -X POST http://localhost:8000/api/v1/dsar/requests/{id}/process

# Complete processing
curl -X POST http://localhost:8000/api/v1/dsar/requests/{id}/complete

# Deny with reason
curl -X POST "http://localhost:8000/api/v1/dsar/requests/{id}/deny?reason=Request+invalid"
```

### 12.3 Audit Log

The audit log is **append-only** — records cannot be modified or deleted:

```bash
# View audit events
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/compliance/audit/events | jq .

# Verify immutability (UPDATE/DELETE will fail)
UPDATE cdm_audit_log SET action = 'tampered' WHERE id = 1;
-- ERROR: permission denied for table cdm_audit_log
```

### 12.4 Data Retention Policies

| Entity Type | Retention | Action |
|-------------|-----------|--------|
| audit_log | 7 years | Archive |
| delay_event | 3 years | Delete |
| mdr_score | 2 years | Delete |
| demand_line | 5 years | Archive |
| manufacturing_order | 5 years | Archive |
| gdpr_dsar_request | 30 days | Delete |
| gdpr_consent | 7 years | Archive |

**Enforce retention:**

```bash
curl -X POST http://localhost:8000/api/v1/compliance/retention/enforce \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_type": "delay_event"}'
```

### 12.5 KMS (Key Management)

```bash
# Create a KMS key
curl -X POST http://localhost:8000/api/v1/kms/keys \
  -H "Content-Type: application/json" \
  -d '{"key_id": "ipe-production-key", "algorithm": "AES-256"}'

# Encrypt data
curl -X POST http://localhost:8000/api/v1/kms/encrypt \
  -H "Content-Type: application/json" \
  -d '{"key_id": "ipe-production-key", "plaintext": "sensitive-data"}'

# Decrypt data
curl -X POST http://localhost:8000/api/v1/kms/decrypt \
  -H "Content-Type: application/json" \
  -d '{"key_id": "ipe-production-key", "ciphertext": "..."}'

# Rotate key
curl -X POST http://localhost:8000/api/v1/kms/keys/ipe-production-key/rotate
```

### 12.6 FDA 21 CFR Part 11 (E-Signatures)

```bash
# Sign a record
curl -X POST http://localhost:8000/api/v1/part11/sign \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-uuid",
    "meaning": "approval",
    "record_content": "Manufacturing batch record for MO-001"
  }'

# Verify a signature
curl http://localhost:8000/api/v1/part11/verify/{signature_id}
```

---

## 13. ML Model Management

### 13.1 MLflow

Access at: `http://localhost:5000`

- Track model experiments
- Store model artifacts
- Compare model versions
- Deploy models

### 13.2 Model Drift Detection

```bash
# Check for data drift
curl -X POST http://localhost:8000/api/v1/ml/drift/check \
  -H "Content-Type: application/json" \
  -d '{
    "reference": [0.1, 0.2, 0.3, 0.4, 0.5],
    "current": [0.15, 0.25, 0.35, 0.45, 0.55],
    "model_id": "duration-predictor"
  }'
```

**PSI Interpretation:**
- PSI < 0.1: No significant drift
- PSI 0.1–0.25: Moderate drift — monitor
- PSI > 0.25: Significant drift — retrain model

### 13.3 Shadow ROI Validation

```bash
# Compare AI vs Manual performance
curl -X POST http://localhost:8000/api/v1/ml/roi/validate \
  -H "Content-Type: application/json" \
  -d '{
    "manual_otd_pct": 78.5,
    "ai_otd_pct": 92.3,
    "manual_cost": 150000,
    "ai_cost": 120000
  }'
```

### 13.4 Feature Store

```bash
# Set a feature value
curl -X POST http://localhost:8000/api/v1/ml/features/set \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "supplier_reliability",
    "entity_key": "supplier_id",
    "entity_value": "SUP-001",
    "value": 0.95
  }'

# Get feature stats
curl http://localhost:8000/api/v1/ml/features/stats
```

---

## 14. ERP Integration (Connector)

### 14.1 Odoo Sync

```bash
# Sync data from Odoo
curl -X POST http://localhost:8000/api/v1/connector/sync/run \
  -H "Content-Type: application/json" \
  -d '{
    "odoo_url": "http://odoo:8069",
    "odoo_db": "ipe_demo",
    "odoo_username": "admin",
    "odoo_password": "admin",
    "entity": "all"
  }'
```

### 14.2 Activate AI Schedule in ERP

After approving a schedule, push it back to Odoo:

```bash
curl -X POST http://localhost:8000/api/v1/connector/sync/odoo/activate \
  -H "Content-Type: application/json" \
  -d '{
    "mo_ids": ["mo-uuid-1", "mo-uuid-2"],
    "odoo_url": "http://odoo:8069",
    "odoo_db": "ipe_demo",
    "odoo_username": "admin",
    "odoo_password": "admin"
  }'
```

### 14.3 HMAC Webhook Receiver

External systems can trigger IPE actions via HMAC-signed webhooks:

```bash
# Generate HMAC signature
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

# Send webhook
curl -X POST http://localhost:8000/api/v1/connector/ipe/action \
  -H "Content-Type: application/json" \
  -H "X-IPE-Signature: $SIGNATURE" \
  -H "X-Tenant-ID: tenant-uuid" \
  -d '{"action": "confirm_mo", "mo_id": "mo-uuid"}'
```

---

## 15. Backup & Recovery

### 15.1 Database Backup

```bash
# Full backup
docker exec docker-db-1 pg_dump -U ipe -Fc ipe_dev > backup.dump

# Restore from backup
docker exec -i docker-db-1 pg_restore -U ipe -d ipe_dev < backup.dump
```

### 15.2 Kafka Backup

```bash
# Export topic data
docker exec docker-kafka-1 kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic ipe.demand.created \
  --from-beginning \
  --timeout-ms 5000 > demand_events.json
```

### 15.3 Configuration Backup

```bash
# Backup Kong configuration
docker exec docker-kong-1 cat /opt/kong/kong.yml > kong_backup.yml

# Backup Keycloak realm
curl -s http://localhost:8180/admin/realms/ipe > keycloak_realm.json
```

### 15.4 Disaster Recovery Procedure

1. **Stop all services**: `docker compose down`
2. **Restore database**: `pg_restore` from latest backup
3. **Restore Kafka topics**: Re-produce events or restore from snapshot
4. **Start infrastructure**: `docker compose up -d db kafka redis`
5. **Run migrations**: `docker compose up -d migrate`
6. **Start application services**: `docker compose up -d`
7. **Verify health**: `bash scripts/demo_walkthrough.sh`

---

## 16. Troubleshooting

### 16.1 Common Issues

| Issue | Symptoms | Resolution |
|-------|----------|------------|
| **Kong won't start** | `kong-1 Exited (255)` | Check port 8000 isn't in use; verify `kong.yml` syntax |
| **Services can't connect to DB** | `Connection refused` errors | Ensure `db` container is healthy; check `depends_on` |
| **JWT validation fails** | 401 on all requests | Verify `IPE_JWT_SECRET_KEY` is set; check token expiry |
| **Kafka consumer lag** | Events not processing | Check consumer group status; restart affected service |
| **WebSocket disconnects** | Real-time updates stop | Check `fea-svc` health; verify WebSocket URL |
| **Keycloak unreachable** | SSO login fails | Ensure `keycloak` container is running on port 8180 |
| **Redis connection error** | Caching/idempotency fails | Check Redis is on port 6380 (not 6379, conflict with nexus) |
| **Migration fails** | `alembic upgrade head` errors | Check DB connectivity; review migration file for syntax |

### 16.2 Diagnostic Commands

```bash
# Check all container status
docker compose -f infrastructure/docker/docker-compose.yml ps

# Check specific service logs
docker compose -f infrastructure/docker/docker-compose.yml logs -f dpe-svc

# Check database connections
docker exec docker-db-1 psql -U ipe -c "SELECT COUNT(*) FROM pg_stat_activity;"

# Check Kafka topics
docker exec docker-kafka-1 kafka-topics --list --bootstrap-server localhost:9092

# Check consumer groups
docker exec docker-kafka-1 kafka-consumer-groups --list --bootstrap-server localhost:9092

# Check Redis
docker exec docker-redis-1 redis-cli ping

# Test Kong route
curl -v http://localhost:8000/api/v1/health

# Check Kong plugins
curl -s http://localhost:8001/plugins | jq .
```

### 16.3 Log Levels

Adjust log verbosity per service:

```bash
# Set log level for a service
docker compose -f infrastructure/docker/docker-compose.yml exec dpe-svc \
  bash -c "export LOG_LEVEL=DEBUG && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001"
```

### 16.4 Performance Tuning

**Database:**

```sql
-- Check slow queries
SELECT query, calls, mean_time, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check connection pool
SELECT COUNT(*) FROM pg_stat_activity WHERE datname = 'ipe_dev';
```

**Redis:**

```bash
# Check memory usage
docker exec docker-redis-1 redis-cli info memory | grep used_memory_human

# Check connected clients
docker exec docker-redis-1 redis-cli info clients | grep connected_clients
```

---

## 17. API Reference Quick Reference

### Authentication

```bash
# All requests require:
Authorization: Bearer <jwt_token>
X-Tenant-ID: <tenant-uuid>
```

### Standard Response Shape

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "total": 100,
    "offset": 0,
    "limit": 50,
    "processing_time_ms": 42
  }
}
```

### XAI (Explainable AI) Response

```json
{
  "xai_explanation": {
    "constraints": ["Material shortage for C1"],
    "assumptions": ["Lead time = 7 days"],
    "confidence_score": 0.85,
    "contributing_factors": {
      "material_availability": 0.45,
      "capacity_utilization": 0.30,
      "labor_availability": 0.25
    }
  }
}
```

### Key Endpoints by Category

**Demand Management:**
- `POST /api/v1/demand/classify` — Priority scoring
- `GET /api/v1/demand/queue` — Priority queue

**Material:**
- `POST /api/v1/material/probabilistic-atp` — Monte Carlo ATP
- `POST /api/v1/material/ctp` — Capable-to-Promise

**Capacity:**
- `POST /api/v1/capacity/schedule` — CP-SAT scheduling
- `POST /api/v1/capacity/cost-optimized` — Multi-objective scheduling
- `POST /api/v1/capacity/green-schedule` — Carbon-aware scheduling

**Feasibility:**
- `POST /api/v1/feasibility/score` — 5-gate scoring
- `GET /api/v1/feasibility/queue` — Risk queue

**Resolution:**
- `POST /api/v1/resolution/scenarios` — Generate scenarios
- `POST /api/v1/resolution/approve` — Approve scenario

**Compliance:**
- `GET /api/v1/compliance/soc2/summary` — SOC 2 status
- `POST /api/v1/dsar/requests` — GDPR DSAR
- `GET /api/v1/compliance/audit/events` — Audit log

**ML/AI:**
- `POST /api/v1/copilot/query` — NLP copilot
- `POST /api/v1/predict/duration` — Duration prediction
- `POST /api/v1/ml/drift/check` — Drift detection

**Financial:**
- `POST /api/v1/cost-accounting/full` — Full P&L
- `POST /api/v1/sop/forecast` — S&OP ingestion
- `POST /api/v1/financial/project` — Financial projection

---

## 18. Index

| Topic | Section |
|-------|---------|
| API Gateway (Kong) | 6 |
| Architecture overview | 2 |
| Authentication flow | 7.1 |
| Backup procedures | 15 |
| Configuration settings | 4 |
| CORS configuration | 7.6 |
| DAG pipelines (Airflow) | Admin Guide §9 |
| Database management | 8 |
| Disaster recovery | 15.4 |
| DLQ monitoring | 9.5 |
| Edge gateway auth | 7.4 |
| Environment variables | 4.1 |
| Feature flags | API Ref |
| GDPR DSAR | 12.2 |
| Health checks | 10.3 |
| Istio mTLS | 7.5 |
| JWT structure | 5.4 |
| Kafka topics | 9.1 |
| Keycloak setup | 5.2 |
| Kong configuration | 6.1 |
| ML model management | 13 |
| MLflow | 13.1 |
| Monitoring (Grafana) | 11.4 |
| Monitoring (Jaeger) | 11.2 |
| Monitoring (Prometheus) | 11.3 |
| OpenTelemetry | 11.1 |
| Password management | 5.2 |
| Performance tuning | 16.4 |
| PostgreSQL | 8.1 |
| Rate limiting | 6.4 |
| RBAC roles | 5.1 |
| Redis | — |
| Resource limits | 10.4 |
| RLS policies | 8.4 |
| SCIM provisioning | 5.3 |
| Schema registry | 9.2 |
| Seed data | 3.6 |
| Service management | 10 |
| SOC 2 compliance | 12.1 |
| Starting the system | 3 |
| System requirements | 1.2 |
| Tenant configuration | 4.3 |
| Troubleshooting | 16 |
| User management | 5 |
| WebSocket configuration | — |
| XAI responses | 17 |
