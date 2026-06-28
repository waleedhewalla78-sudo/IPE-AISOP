# Plan — 009 v8 Phase 3

```
Kong :8000
├── material-svc:8090     /api/v1/materials/*, /api/v1/design/*
└── procurement-svc:8100  /api/v1/suppliers/*, /api/v1/procurement/*
```

## Schema (031)

- `cdm_engineering_material`, `cdm_design_recommendation`, `cdm_design_rule`
- `cdm_procurement_spend`, `cdm_procurement_compliance_check`
- `cdm_supplier` + esg_score, risk_tier, category

## Deploy

1. `alembic upgrade head` (031)
2. `docker compose up -d --build material-svc procurement-svc kong`
3. Web dev server for new hub tabs
