# Contract: Kong enterprise route

## Route
- **Path**: `/api/v1/enterprise`
- **Upstream**: `http://dpe-svc:8001` (same as other dpe routes in R2)
- **strip_path**: false
- **Plugins**: inherit service `ipe-tenant-strip` (R2)

## Smoke
```
GET  /api/v1/enterprise/agents
POST /api/v1/enterprise/...  (existing Phase 6 handlers)
```
Expect HTTP 200 via Kong :8000 (not 404).
