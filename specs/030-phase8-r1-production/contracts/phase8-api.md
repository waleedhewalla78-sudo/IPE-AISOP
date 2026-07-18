# Contracts — Spec 030 Phase 8 APIs

Base: `/api/v1/phase8` (Kong `r2-phase8` / `st-phase8` → dpe-svc)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/ai-status` | Ollama health + amber banner flags |
| GET | `/agents` | Catalog A1–A20 honesty notes |
| POST | `/role-check` | AgentRoleContext gate |
| POST | `/write-back` | Propose (default dry_run) |
| POST | `/write-back/{id}/approve` | Approve; live gated by flag |
| GET | `/write-back` | List tenant entries |
| POST | `/narratives/feasibility` | Explanation (Ollama or rule-based) |
| POST | `/narratives/resolution` | Scenario narrative by role |
| POST | `/agents/a18/split` | Multi-site stub |
| POST | `/agents/a19/retrain` | Learning stub |
| GET | `/agents/a20/monitor` | Exception monitor stub |
| GET | `/export/risk-queue.csv` | CT export |
| GET | `/export/mps.csv` | MPS export |

Auth: Bearer JWT + `X-Tenant-ID` (same as other dpe routes).
