# IPE — Intelligent Planning Engine

AI-driven production planning platform. ERP-agnostic. Odoo-first.

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

## Architecture

See [docs/architecture/system-overview.md](docs/architecture/system-overview.md)

## Services

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
| Frontend | 3000 | http://localhost:3000 |
| Kafka UI | 8080 | http://localhost:8080 |
| Grafana | 3000 | http://localhost:3000 |
| Prometheus | 9090 | http://localhost:9090 |

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
