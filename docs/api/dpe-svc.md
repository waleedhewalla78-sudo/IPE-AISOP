# dpe-svc — Demand & Priority Engine

## Endpoints

- `GET /api/v1/health` — Health check
- `GET /api/v1/ready` — Readiness (with DB check)
- `POST /api/v1/demand/classify` — Classify demand lines (Phase 1)
- `GET /api/v1/demand/queue` — Get prioritized demand queue (Phase 1)
