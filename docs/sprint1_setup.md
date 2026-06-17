# Sprint 1 Setup Guide

## Prerequisites
- Docker Desktop (8GB+ RAM allocated)
- Python 3.12, `uv`, `pnpm`, Node 20+

## Quick Start

```bash
# 1. Install dependencies
make setup

# 2. Start infrastructure (Postgres 16, Kafka, Redis, Schema Registry, Nginx)
make docker-up

# 3. Apply CDM schema, roles, and safe RLS policies
make migrate

# 4. Load seed data (clean + dirty tenants for MDR/RLS testing)
make seed

# 5. Start all FastAPI services and React frontend
make dev
```

## Database Migrations
The CDM schema (19 tables) is managed via Alembic:
```bash
make migrate          # Apply pending migrations
cd migrations && alembic history  # List history
cd migrations && alembic downgrade -1  # Rollback one step
```

## Testing
```bash
make test             # All unit tests + coverage
make lint             # Ruff + ESLint
cd services/shared && uv run pytest tests/integration/ -v  # RLS isolation tests
```

## MDR Gating
- BOM completeness threshold: >= 80%
- Lead time accuracy threshold: >= 60%
- Clean tenant A: passes both gates
- Dirty tenant B: triggers MDR_GATE_FAILED on `/api/v1/demand/classify`
