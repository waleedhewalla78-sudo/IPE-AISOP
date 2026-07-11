# IPE Release v9.2.0-planning

**Date:** 2026-07-11  
**Tag:** v9.2.0-planning  

## What's Included

- Docker Compose deployment (R1 profile, 8 app services + db/redis/kong)
- Environment configuration template
- Deployment runbook (step-by-step)
- Smoke test checklist
- Deployment validation script (`star-trans-validate.ps1`)
- Backup automation (Linux + Windows)
- Health monitoring (Linux + Windows)
- Star Trans demo data seed (SQL)
- `MANIFEST.md` — file list with SHA256 checksums

## Quick Start

1. Copy this directory to the target server
2. Copy `.env.template` to `.env` — fill in Odoo and database credentials
3. Ensure Release 1 images are available (`ipe-*:release1`) or build per runbook Step 3
4. `docker compose up -d`
5. `docker compose exec dpe-svc uv run alembic upgrade head`
6. Validate: `.\star-trans-validate.ps1` (or equivalent health curls)
7. Optional: load demo data:
   ```bash
   docker compose exec -T db psql -U ipe -d ipe < star-trans-seed.sql
   ```

## Commercial blockers (not in this archive)

- OQ-7 pricing / SOW send
- Live Odoo staging credentials
- Arabic native sign-off for `v9.1.1-r2`
