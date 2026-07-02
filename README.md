# IPE — Intelligent Planning Engine

AI-driven production planning platform. ERP-agnostic. Odoo-first.

**Version:** v8.2.0 (full platform) · Release 1 → v9.0.0-r1 (Odoo customer profile)  
**Status:** 32/32 demo · 870+ tests · Star Trans Odoo UAT in progress

## Documentation

| Document | Audience |
|----------|----------|
| [**Comprehensive PRD (as-is)**](docs/PRD-IPE-COMPREHENSIVE-AS-IS.md) | Product, engineering, stakeholders — authoritative spec |
| [**Executive one-pager**](docs/PRD-IPE-EXECUTIVE-ONE-PAGER.md) | Leadership — 5-minute overview |
| [Product status](docs/PRODUCT-STATUS.md) | Feature matrix & validation |
| [Readiness](READINESS.md) | Deployment readiness score |
| [Architecture](docs/architecture.md) | Services, ports, event mesh |
| [API reference](docs/api-reference.md) | Endpoint index |
| [Odoo integration](docs/integration/ODOO-LOCAL-SETUP.md) | Release 1 ERP setup |
| [Release 1 spec](specs/013-release1-odoo-mena/spec.md) | Star Trans scope |

## Quick Start

```bash
# 1. Clone and setup
git clone <repo-url> && cd ipe
make setup

# 2. Start infrastructure
make docker-up

# 3. Run migrations
make migrate

# 4. Start all services
make dev
```

### Release 1 (Star Trans / Odoo — 8 services, 8 GB VM)

```powershell
cd E:\AISOP\ipe
.\scripts\deploy-release1.ps1
.\scripts\setup-odoo-integration.ps1
cd apps\web; $env:VITE_RELEASE_PROFILE='release1'; npm run dev
```

Web UI: http://localhost:8082 · API gateway: http://localhost:8000

## Services (full stack)

| Service | Port | Docs |
|---------|------|------|
| dpe-svc | 8001 | http://localhost:8001/docs |
| mat-svc | 8002 | http://localhost:8002/docs |
| cap-svc | 8003 | http://localhost:8003/docs |
| fea-svc | 8004 | http://localhost:8004/docs |
| res-svc | 8005 | http://localhost:8005/docs |
| del-svc | 8006 | http://localhost:8006/docs |
| nlp-svc | 8007 | http://localhost:8007/docs |
| rec-svc | 8008 | http://localhost:8008/docs |
| connector | 8009 | http://localhost:8009/docs |
| alert-svc | 8010 | http://localhost:8010/docs |
| Frontend (Vite) | 8082 | http://localhost:8082 |
| Kong gateway | 8000 | http://localhost:8000 |
| Kafka UI | 8080 | http://localhost:8080 |
| PostgreSQL | 5433 | localhost:5433 (ipe_test) |

## Production Secrets

In production, sensitive variables must NOT be passed as plaintext environment
variables. Use Docker secrets with the included overlay:

```bash
# 1. Create secret files
mkdir -p infrastructure/docker/secrets
echo "your-jwt-secret" > infrastructure/docker/secrets/jwt_secret_key.txt
echo "sk-ant-xxxx" > infrastructure/docker/secrets/anthropic_api_key.txt
echo "postgresql+asyncpg://..." > infrastructure/docker/secrets/database_url.txt
echo "redis://..." > infrastructure/docker/secrets/redis_url.txt
echo "kafka:9092" > infrastructure/docker/secrets/kafka_bootstrap_servers.txt

# 2. Deploy with secrets overlay
docker compose \
  -f infrastructure/docker/docker-compose.yml \
  -f infrastructure/docker/docker-compose.secrets.yml \
  up -d
```

Each service reads secrets via `_FILE`-suffixed environment variables
(e.g., `IPE_DATABASE_URL_FILE=/run/secrets/ipe_database_url`).
The `ipe_shared.config.Settings` class supports both plain env vars and
`_FILE` overrides. If the `_FILE` variable is set, its contents are read
from the file path.

For local development without Docker Swarm, secrets are not required —
the base `docker-compose.yml` uses default dev credentials.
