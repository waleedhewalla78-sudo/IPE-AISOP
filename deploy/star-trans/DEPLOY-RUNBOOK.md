# IPE Star Trans Deployment Runbook

**Version:** v9.2.0-planning — Release 1 Profile  
**Target:** Star Trans production environment  
**Est. time:** 2–4 hours (first deployment on clean server)

---

## Prerequisites

### Server Requirements
- **OS:** Ubuntu 22.04 LTS (preferred) or Windows Server 2022
- **RAM:** 8 GB minimum (16 GB recommended)
- **CPU:** 4 cores minimum
- **Disk:** 50 GB SSD (for DB, images, logs)
- **Network:** Outbound to `hub.docker.com`, inbound from Star Trans LAN for UI access

### Software
```bash
# Docker 24+ and Docker Compose v2
curl -fsSL https://get.docker.com | sudo bash
sudo usermod -aG docker $USER
# Log out and back in, then verify:
docker --version   # >= 24.0
docker compose version  # >= 2.0
```

### Odoo Access
- Odoo URL, database name, API user credentials (from Star Trans IT)
- Network path from IPE server to Odoo server (port 8069 open)

---

## Step 1: Copy Deployment Files

```bash
# On the IPE deployment server:
mkdir -p /opt/ipe-startrans
# Copy entire deploy/star-trans/ directory contents to /opt/ipe-startrans/
# Including: docker-compose.yml, .env.template, kong.star-trans.yml, this runbook

cd /opt/ipe-startrans
ls
# Expected: docker-compose.yml  .env.template  kong.star-trans.yml  DEPLOY-RUNBOOK.md  SMOKE-TEST.md
```

---

## Step 2: Configure Environment

```bash
cp .env.template .env
nano .env   # or use your preferred editor
```

**Required values to fill in:**
```
POSTGRES_USER=ipe
POSTGRES_PASSWORD=<strong-random-password>
POSTGRES_DB=ipe
DATABASE_URL=postgresql+asyncpg://ipe:<same-password>@db:5432/ipe
IPE_JWT_SECRET_KEY=<generate-with: openssl rand -hex 32>
ODOO_URL=http://<star-trans-odoo-server>:8069
ODOO_DB=<star-trans-db-name>
ODOO_USER=<api-username>
ODOO_PASSWORD=<api-password>
```

> **Important:** `docker compose` requires a `.env` file in this directory. Always `cp .env.template .env` before `docker compose up` or `docker compose config`.

**Generate a secure JWT key:**
```bash
openssl rand -hex 32
# Paste the output as IPE_JWT_SECRET_KEY in .env
```

---

## Step 3: Pull / Build Docker Images

> **Note:** Pre-built images must be provided by the IPE team.  
> If building from source, clone the IPE repository and build:

```bash
# If building from source (IPE team provides images alternatively):
git clone <IPE_REPO_URL> /opt/ipe-source
cd /opt/ipe-source
docker build -t ipe-dpe-svc:release1 -f services/dpe-svc/Dockerfile .
docker build -t ipe-fea-svc:release1 -f services/fea-svc/Dockerfile .
docker build -t ipe-res-svc:release1 -f services/res-svc/Dockerfile .
docker build -t ipe-cap-svc:release1 -f services/cap-svc/Dockerfile .
docker build -t ipe-mat-svc:release1 -f services/mat-svc/Dockerfile .
docker build -t ipe-connector:release1 -f services/connector/Dockerfile .
docker build -t ipe-web-ui:release1 --build-arg VITE_RELEASE_PROFILE=release1 -f apps/web/Dockerfile.release1 .
cd /opt/ipe-startrans
```

---

## Step 4: Start the Stack

```bash
cd /opt/ipe-startrans
docker compose up -d
```

Wait ~60 seconds for all services to become healthy:
```bash
docker compose ps
# All services should show "healthy" or "running"
```

---

## Step 5: Run Database Migrations

```bash
docker compose exec dpe-svc uv run alembic upgrade head
```

Expected output: `Running upgrade ... -> 049, S&OP process engine`  
(or whatever the latest migration is)

Verify:
```bash
docker compose exec dpe-svc uv run alembic current
# Should show: 049 (head)
```

---

## Step 6: Verify Service Health

Healthchecks in `docker-compose.yml` use `/api/v1/health` on each service.

```bash
# Kong gateway (proxy on host port 8000; Kong admin is on host 8444)
curl http://localhost:8000/

# Direct service checks (match compose healthcheck paths)
curl http://localhost:8001/api/v1/health  # dpe-svc
curl http://localhost:8004/api/v1/health  # fea-svc
curl http://localhost:8005/api/v1/health  # res-svc
curl http://localhost:8009/api/v1/health  # connector
curl http://localhost:8002/api/v1/health  # mat-svc
curl http://localhost:8003/api/v1/health  # cap-svc
```

Or run the packaged validator from the IPE repo:
```powershell
.\scripts\star-trans-validate.ps1
```

---

## Step 7: Configure Odoo Connection

The connector is pre-configured via `.env`. Verify the connection:

```bash
# Trigger a connectivity test (returns Odoo server info)
curl http://localhost:8009/api/v1/sync/status
```

If the Odoo connection fails:
- Verify `ODOO_URL` in `.env` is reachable from the server
- Verify `ODOO_USER` has API access in Odoo
- Check connector logs: `docker compose logs connector --tail 50`

---

## Step 8: Trigger First Sync

```bash
# Full sync: products, BOMs, MOs, work centres, demand, supply
curl -X POST http://localhost:8009/api/v1/sync/run \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "default"}'
```

Monitor sync progress:
```bash
curl http://localhost:8009/api/v1/sync/status
# Wait for: {"status": "completed", "synced_entities": {...}}
```

The first sync may take 5–30 minutes depending on Odoo data volume.

---

## Step 9: Access the Web UI

Open a browser and navigate to:
```
http://<server-ip>:8082
```

Default credentials (change after first login):
- Username: `admin@ipe.local`
- Password: `admin`

**Verify:**
- Control Tower shows Manufacturing Orders
- Navigation includes: Control Tower, Planning, Copilot (if R2 enabled)
- Arabic language toggle works (top-right user menu)

---

## Step 10: Seed Demo Data (Optional)

If Star Trans Odoo is not yet connected or for initial testing / UAT demos:

```bash
# From deploy/star-trans/ (copy seed SQL next to compose, or mount from repo):
# Seed file location in repo: docs/demo-data/star-trans-seed.sql
docker compose exec -T db psql -U ipe -d ipe < star-trans-seed.sql

# From IPE repo root (Linux/macOS):
# docker compose -f deploy/star-trans/docker-compose.yml exec -T db \
#   psql -U ipe -d ipe < docs/demo-data/star-trans-seed.sql

# From IPE repo root (Windows PowerShell):
# Get-Content docs/demo-data/star-trans-seed.sql -Raw |
#   docker compose -f deploy/star-trans/docker-compose.yml exec -T db psql -U ipe -d ipe
```

See `docs/demo-data/STARTRANS-DEMO-GUIDE.md` for demo narrative after seeding.

---

## Step 11: Post-Deployment Verification

Run the smoke test checklist:
```bash
# See SMOKE-TEST.md for full checklist
```

---

## Troubleshooting

### Service not starting
```bash
docker compose logs <service-name> --tail 100
```

### Database connection error
- Check `DATABASE_URL` in `.env`
- Verify `POSTGRES_PASSWORD` matches in both `POSTGRES_PASSWORD` and `DATABASE_URL`

### Odoo sync fails with 401/403
- Verify `ODOO_USER` credentials in Odoo admin panel
- Ensure API access is enabled for the user

### Kong 404 on all routes
- Check `kong.star-trans.yml` is mounted correctly
- Verify backend service URLs in Kong config match service names

### Out of memory
- Reduce concurrent services or increase server RAM to 16 GB
- Disable non-critical services (mat-svc can be disabled for R1 minimal)

---

## Maintenance

### Update IPE images
```bash
docker compose pull   # if using registry
# OR rebuild from source, then:
docker compose up -d --build
docker compose exec dpe-svc uv run alembic upgrade head
```

### View logs
```bash
docker compose logs -f connector        # Sync logs
docker compose logs -f dpe-svc --tail 50  # Core service
```

### Backup database
```bash
# Ad-hoc dump
docker compose exec -T db pg_dump -U ipe -Fc ipe > ipe-backup-$(date +%Y%m%d).dump

# Or use packaged automation (7-day retention):
# Linux:   scripts/backup/ipe-backup.sh /var/backups/ipe
# Windows: scripts/backup/ipe-backup.ps1 -BackupDir C:\ipe\backups
```

### Stop stack
```bash
docker compose down   # stops containers, keeps data
docker compose down -v  # WARNING: also deletes database volumes
```
