# res-svc — Resolution Recommender

## Endpoints

- `GET /api/v1/health` — Health check
- `GET /api/v1/ready` — Readiness (with DB check)
- `POST /api/v1/resolution/scenarios` — Generate resolution scenarios (Phase 1)
- `POST /api/v1/resolution/approve` — Approve a scenario (Phase 1)
