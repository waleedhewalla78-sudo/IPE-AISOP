# Quickstart — Spec 029 Productionization

```powershell
cd E:\AISOP\ipe

# 1. Apply migrations (head includes 068 RLS + 069 MPS/MRP)
$env:IPE_DATABASE_URL_SYNC = "postgresql://ipe:ipe_dev_pass@localhost:5432/ipe_dev"
cd migrations; alembic upgrade head; cd ..

# 2. Unit tests (Andon persist + stage-gate + plan persist)
uv run --directory services/dpe-svc pytest services/dpe-svc/tests/test_phase7_operations.py services/dpe-svc/tests/test_phase7_api.py services/dpe-svc/tests/test_spec029_productionization.py -q

# 3. R2 stack + Kong enterprise smoke
docker compose -f infrastructure/docker/docker-compose.release2.yml up -d
# After healthy:
curl -s -H "Authorization: Bearer $TOKEN" -H "X-Tenant-ID: a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11" http://localhost:8000/api/v1/enterprise/agents

# 4. Validate residuals (when stack healthy)
.\scripts\star-trans-validate.ps1 -DpePort 8020 -ConnectorPort 8016
```

COM blockers remain OPEN — do not claim live Odoo or Arabic sign-off.
