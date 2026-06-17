# nlp-svc — Copilot Interface

## Endpoints

- `GET /api/v1/health` — Health check
- `GET /api/v1/ready` — Readiness (with DB check)
- `POST /api/v1/copilot/query` — Natural language query (Phase 1, SSE streaming)
