#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../migrations"

echo "Running database migrations..."
uv run alembic upgrade head
echo "Migrations complete."
