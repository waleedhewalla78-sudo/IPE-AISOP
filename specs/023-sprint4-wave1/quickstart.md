# Quickstart — Spec 023 Sprint 4 Wave 1

```powershell
cd E:\AISOP\ipe
copy .env.template .env   # if needed
# Generate Fernet key:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Set IPE_ENCRYPTION_KEY in .env

# Apply migration (DB up)
$env:IPE_DATABASE_URL_SYNC = "postgresql://ipe:ipe_test_pass@127.0.0.1:5433/ipe_test"
cd migrations; uv run alembic upgrade head

# Tests
cd ..\services\connector; uv run pytest tests/test_erp_connections.py -q
cd ..\dpe-svc; uv run pytest tests/test_otd_analytics.py -q
```

UI: Platform/Admin → Odoo Connections; Command Center → OTD Dashboard.
