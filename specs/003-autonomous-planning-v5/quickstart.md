# Quickstart: V5.0 Convergence Verification

## Prerequisites

```powershell
cd d:\AISOP\ipe
.\scripts\start-product.ps1
docker compose -f infrastructure\docker run --rm migrate
docker compose -f infrastructure\docker up -d --build cap-svc dpe-svc
```

## R1 Closed Loop

1. Login http://localhost:8082 — `Ahmed@nour` / `admin`
2. Open **Schedule** → **Regenerate schedule**
3. Select MOs on Gantt → **Approve**
4. Refresh page — approved times persist (GET `/capacity/schedule/active`)
5. Verify API: `POST /api/v1/capacity/schedule/approve`

## R2 Planner UX

- Use **Optimization controls** sliders on Schedule page
- Read **Why this schedule?** explainability panel
- Heuristic fallback triggers when CP-SAT times out (large models)

## R3 MDR Gate

- `GET /api/v1/demand/mdr/dashboard` — composite score ≥70% required for scheduling
- Routes: `/quality`, `/sustainability`, `/compliance`

## Tests

```powershell
cd services\cap-svc
uv run pytest tests/test_priority_resolver.py tests/test_heuristic_scheduler.py tests/test_api_schedule_approve.py -q
```
