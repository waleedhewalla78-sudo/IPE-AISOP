# del-svc — Delay Analyst

## Endpoints

- `GET /api/v1/health` — Health check
- `GET /api/v1/ready` — Readiness (with DB check)
- `POST /api/v1/delay/classify` — Classify delay cause (Phase 1)
- `GET /api/v1/delay/report` — Delay trend report (Phase 1)
