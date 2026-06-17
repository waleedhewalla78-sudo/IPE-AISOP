#!/usr/bin/env bash
set -euo pipefail

echo "=== IPE Development Setup ==="

command -v python3.12 >/dev/null 2>&1 || { echo "Python 3.12 required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js 20+ required"; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo "pnpm 9+ required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker required"; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "uv required: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }

cp -n .env.example .env 2>/dev/null || true
cp -n apps/web/.env.example apps/web/.env.development 2>/dev/null || true

echo "Installing frontend dependencies..."
pnpm install

echo "Installing Python dependencies..."
for dir in services/shared services/dpe-svc services/mat-svc services/cap-svc services/fea-svc services/res-svc services/del-svc services/nlp-svc; do
    echo "  Setting up $dir..."
    cd "$dir"
    uv sync
    cd - >/dev/null
done

echo "Starting Docker infrastructure..."
docker compose -f infrastructure/docker/docker-compose.yml up -d

echo "Waiting for Postgres to be ready..."
until docker compose -f infrastructure/docker/docker-compose.yml exec -T postgres pg_isready -U ipe 2>/dev/null; do
    sleep 1
done

echo "Running database migrations..."
cd migrations && uv run alembic upgrade head && cd ..

echo "Installing pre-commit hooks..."
uv run pre-commit install

echo ""
echo "=== Setup Complete ==="
echo "Run 'make dev' to start all services"
