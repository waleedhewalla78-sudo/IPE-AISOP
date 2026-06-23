#!/usr/bin/env python3
"""Run Alembic migrations against Docker database.

Usage:
    python scripts/run_migrations.py [--downgrade N] [--upgrade N]

Environment variables:
    DATABASE_URL: PostgreSQL connection string (default: docker-compose db)
"""

import os
import subprocess
import sys

def main():
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://ipe:ipe_test_pass@localhost:5432/ipe_test"
    )

    os.environ["DATABASE_URL_SYNC"] = database_url.replace("+asyncpg", "")
    os.environ["IPE_DATABASE_URL_SYNC"] = database_url.replace("+asyncpg", "")
    os.environ["IPE_DATABASE_URL"] = database_url

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    migrations_dir = os.path.join(project_root, "migrations")

    if len(sys.argv) > 1:
        target = sys.argv[1]
        if target.startswith("--downgrade"):
            steps = sys.argv[2] if len(sys.argv) > 2 else "1"
            cmd = ["uv", "run", "alembic", "-x", f"db_url={database_url}", "downgrade", f"-{steps}"]
        elif target.startswith("--upgrade"):
            steps = sys.argv[2] if len(sys.argv) > 2 else "head"
            cmd = ["uv", "run", "alembic", "-x", f"db_url={database_url}", "upgrade", steps]
        else:
            cmd = ["uv", "run", "alembic", "-x", f"db_url={database_url}", "upgrade", "head"]
    else:
        cmd = ["uv", "run", "alembic", "upgrade", "head"]

    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {migrations_dir}")
    print(f"Database URL: {database_url.replace(database_url.split('@')[0], '***')}")

    result = subprocess.run(cmd, cwd=migrations_dir, env={**os.environ})
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()