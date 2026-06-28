# Plan — 008 v8 Phase 2

```
Kong :8000
├── supply-svc:8060   /api/v1/supply/*
├── order-svc:8070    /api/v1/orders/*
└── equipment-svc:8061 /api/v1/equipment/*, /api/v1/maintenance/*
```

Reuse Phase 1 scaffold pattern (demand-svc/rec-svc template).

## Deploy

1. `alembic upgrade head` (030)
2. `docker compose up -d --build supply-svc order-svc equipment-svc kong`
3. Web dev server for new hub tabs
