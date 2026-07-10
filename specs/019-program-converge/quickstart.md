# Quickstart: 019-program-converge

## Prerequisites

```powershell
cd E:\AISOP\ipe
# Prefer not to tear down if another QA agent is using the stack
```

## Validate compose includes mat-svc

```powershell
docker compose -f infrastructure/docker/docker-compose.release2.yml config --services
# Expect: mat-svc among services
```

## Unit tests (no stack required)

```powershell
uv run --directory services/scenario-svc pytest services/scenario-svc/tests/test_api.py -q
uv run --directory services/mock-odoo-api pytest services/mock-odoo-api/tests -q
```

## Manual promote check (stack up)

```powershell
# Obtain local JWT via existing login / demo-http.ps1 -AuthMode local
# POST /api/v1/scenario/{id}/promote via Kong :8000
```

## Expected

- Promote returns `status: promoted`
- Workbench shows Promote button (EN/AR)
- mock search_read stock.quant non-empty
