# Quick Start for Testers

**Repository:** https://github.com/waleedhewalla78-sudo/IPE-AISOP  
**Release tag:** `v7.0.0`

## 1. Clone and checkout

```powershell
git clone https://github.com/waleedhewalla78-sudo/IPE-AISOP.git
cd IPE-AISOP
git checkout v7.0.0
```

## 2. Start the backend stack

Requires **Docker Desktop** running.

```powershell
.\scripts\rel-demo-stack.ps1 -SkipBuild
```

First run without `-SkipBuild` may take 10–20 minutes (image build). Wait until Kong responds:

```powershell
Invoke-WebRequest http://localhost:8000/api/v1/health -UseBasicParsing
# Expect StatusCode 200
```

### Service health (direct ports)

| Service | Port | Health URL |
|---------|------|------------|
| Kong (API gateway) | 8000 | `http://localhost:8000/api/v1/health` |
| dpe-svc (auth, demand, MDR) | 8020 | `http://localhost:8020/api/v1/health` |
| mat-svc | 8002 | `http://localhost:8002/api/v1/health` |
| cap-svc | 8003 | `http://localhost:8003/api/v1/health` |
| fea-svc | 8004 | `http://localhost:8004/api/v1/health` |
| nlp-svc | 8007 | `http://localhost:8007/api/v1/health` |
| alert-svc | 8010 | `http://localhost:8010/api/v1/health` |

> There is no standalone `auth-svc` or `mdr-svc` — both live in **dpe-svc**.

## 3. Start the web UI (port 8082)

The demo Docker overlay does **not** include the React app. In a **second terminal**:

```powershell
cd apps\web
npm install
npm run dev
```

Open **http://localhost:8082/login**

Alternative (full stack + UI in one script):

```powershell
.\scripts\start-product.ps1 -SkipSeed
```

## 4. Demo credentials

| Role | Email | Password | Tenant header |
|------|-------|----------|---------------|
| Admin (primary demo) | `Ahmed@nour` | `admin` | See below |
| Admin (alternate) | `admin@demo.com` | `demo` | See below |

**Tenant ID** (for API calls): `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11`

Full walkthrough: [docs/FULL-DEMO-GUIDE.md](../FULL-DEMO-GUIDE.md)

## 5. Run automated verification (optional)

Already verified for v7.0.0; re-run to confirm your environment:

```powershell
.\scripts\run-full-demo.ps1 -ReportPath docs\final-regression-demo.txt
# Expected: 20/20 pass

.\scripts\run-chaos-scenarios.ps1
# Expected: 6/6 pass (evidence in docs/chaos/)
```

## 6. Test API directly

```powershell
$login = Invoke-RestMethod -Method POST `
  -Uri "http://localhost:8000/api/v1/auth/login" `
  -ContentType "application/json" `
  -Body '{"email":"Ahmed@nour","password":"admin"}'

$token = $login.data.access_token
$headers = @{
  Authorization = "Bearer $token"
  "X-Tenant-ID" = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
}

# Feasibility queue
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/feasibility/queue" -Headers $headers
```

## 7. Monitoring (optional)

When the ops overlay is running:

| Tool | URL | Notes |
|------|-----|-------|
| Grafana | http://localhost:3002 | Check `infrastructure/docker` for credentials |
| Prometheus | http://localhost:9091 | Metrics scrape |
| Loki | http://localhost:3100 | Log aggregation |

See [docs/ops-monitoring.md](../ops-monitoring.md)

## 8. Stop the system

```powershell
cd infrastructure\docker
docker compose -f docker-compose.yml -f docker-compose.demo.yml down
```

Stop the web UI with `Ctrl+C` in the frontend terminal.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Kong 502/503 | Wait 2–3 min; check `docker ps` — services should be healthy |
| Login fails | Re-run `.\scripts\seed-demo-client.ps1` |
| Port 8082 in use | Stop other Vite apps or change port in `apps/web/vite.config.ts` |
| Copilot 503 | Demo overlay disables external LLM; rule-based fallback should still respond |
