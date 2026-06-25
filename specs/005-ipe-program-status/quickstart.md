# Quickstart: IPE v6.0.0 Release Verification

**Feature**: `005-ipe-program-status` | **Updated**: 2026-06-25  
**Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

---

## Prerequisites

- Docker Desktop running (≥8 GB RAM recommended)
- `E:\AISOP\ipe\.env` from `.env.template`
- Ports free: **8000** (Kong), **8082** (web), **5432**, **6380** (Redis host), **9092**
- Git safe directory: `git -c safe.directory=E:/AISOP` (if ownership warning)

---

## Path A — Lean demo stack (recommended)

```powershell
cd E:\AISOP\ipe
.\scripts\rel-demo-stack.ps1
```

Flags:

```powershell
.\scripts\rel-demo-stack.ps1 -SkipBuild   # images already built
.\scripts\rel-demo-stack.ps1 -SkipSeed    # seed already applied
.\scripts\rel-demo-stack.ps1 -DemoOnly    # stack up; demo only
```

**Expected exit gates**:

| Step | Verification |
|------|--------------|
| Infra | db, redis, kafka, zookeeper healthy |
| Build | 13 app services + Kong images |
| Migrate | Alembic head = **027** |
| Seed | Demo tenant + V6 data |
| Demo | `docs/demo-run-report-v6.txt` → **20/20** |

**Login**: `Ahmed@nour` / `admin` (demo script) · UI also accepts `admin@demo.com` / `demo`

---

## Path B — Full compose (optional, slower)

```powershell
cd E:\AISOP\ipe\infrastructure\docker
docker compose -f docker-compose.yml up -d
cd ..\..
.\scripts\seed-demo-client.ps1
.\scripts\run-full-demo.ps1 -ReportPath docs\demo-run-report-v6.txt
```

Note: Full stack may pull Ollama (~500MB) and Airflow — use Path A for release gates.

---

## Backend verification (REL-TEST)

```powershell
cd E:\AISOP\ipe
.\scripts\launch-verify.ps1
```

**Expected**: `10 passed, 0 failed`  
**Evidence**: `specs/004-ai-first-v6/evidence/rv-02-launch-verify.txt`

---

## Frontend (optional UI walkthrough)

```powershell
cd E:\AISOP\ipe\apps\web
npm install
npm run dev
```

Open http://localhost:8082/login

---

## V6 checkpoint smoke (manual)

| CP | Endpoint / action | Pass criteria |
|----|-------------------|---------------|
| 17 | `GET /demand/priority/margin-aware` | Ordered MOs + activity breakdown |
| 18 | Tariff shock POST | `affected_mo_count ≥ 1` + substitute draft |
| 19 | CPM cascade on schedule MO | `cascade_ms ≤ 2000` |
| 20 | Maintenance telemetry + chaos | Block published; ≥3 chaos $ categories |

---

## Tag v6.0.0 (requires approval)

Only after **20/20 demo** + stakeholder sign-off:

```powershell
git -c safe.directory=E:/AISOP tag -a v6.0.0 -m "IPE v6.0.0 — AI-First Strategic Reassessment"
```

Mark **T055** in `specs/004-ai-first-v6/tasks.md`.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| V6 routes 404 | Rebuild stack; confirm Kong + dpe/mat/cap-svc running |
| CP4/15 timeout | Use demo overlay; ensure cap-svc image rebuilt |
| Docker daemon hang | Restart Docker Desktop; retry `-SkipBuild` if images exist |
| Postgres not ready | Wait 120s; check `docker-db-1` health |
