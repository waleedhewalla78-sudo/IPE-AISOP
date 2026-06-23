# Getting Started — IPE v1.0 (Demo)

Run the full Intelligent Planning Engine stack locally in a few minutes.

## Prerequisites

- Docker Desktop (with Compose)
- Node.js 20+ and npm
- Git Bash (optional, for seed script on Windows)

## Quick start (Windows)

```powershell
cd d:\AISOP\ipe
.\scripts\start-product.ps1
```

This will:

1. Start all backend services via Docker Compose
2. Run Alembic migrations
3. Load demo seed data (tenant, users, products, demands, work centers)
4. Start the web UI at **http://localhost:8082**

## Quick start (manual)

```powershell
cd infrastructure\docker
docker compose up -d
docker compose run --rm migrate

# Seed (from repo root, requires psql or bash)
$env:IPE_DATABASE_URL_SYNC = "postgresql://ipe:ipe_test_pass@localhost:5433/ipe_test"
bash scripts/seed-data.sh

cd ..\..\apps\web
npm install
npm run dev
```

Open **http://localhost:8082** in your browser.

## Demo login

| Email | Password | Role |
|-------|----------|------|
| `admin@demo.com` | `demo` | Admin |
| `planner@demo.com` | `demo` | Planner |

Development also accepts password `admin` for the same accounts.

## URLs

| Service | URL |
|---------|-----|
| Web UI | http://localhost:8082 |
| API Gateway (Kong) | http://localhost:8000 |
| PostgreSQL | localhost:5433 (db: `ipe_test`, user: `ipe`) |

## Main screens

After login, use the sidebar to navigate:

- **Control Tower** — KPIs, demand queue, bottlenecks
- **Schedule** — capacity and scheduling views
- **Resolution Center** — feasibility and resolution workflows
- **Copilot** — NLP assistant
- **Executive / War Room / AI Trust** — leadership and trust dashboards
- **Shop Floor / SCN Portal / MLOps / Onboarding / Admin**

See [docs/END-USER-GUIDE.md](docs/END-USER-GUIDE.md) for detailed walkthroughs.

## Verify backend health

```powershell
curl http://localhost:8000/api/v1/health
```

## Troubleshooting

**Login fails (401)**  
Ensure seed data ran and Docker stack is up. Re-run: `bash scripts/seed-data.sh`

**API returns 500 on data routes**  
Recreate app containers after env changes: `docker compose up -d --force-recreate dpe-svc kong`

**Port 5433 in use**  
Change Postgres host mapping in `infrastructure/docker/docker-compose.yml` or stop the conflicting service.

**Frontend cannot reach API**  
Vite proxies `/api` to Kong on port 8000. Ensure Kong is healthy: `docker compose ps`

## Stop the stack

```powershell
cd infrastructure\docker
docker compose down
```
