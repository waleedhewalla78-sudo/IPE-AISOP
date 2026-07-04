# Gate Results — Phase 3 (2026-07-04)

| Gate | Result | Evidence |
|------|--------|----------|
| Gate 6 — Helm lint/template | **PASS** | `scripts/k8s/verify-gate6.ps1` — release1, prod, dev values |
| Gate 7 — kind deploy + health | **PASS** | kind cluster `ipe-dev`; 6/6 R1 pods `/health` 200; ingress `http://localhost/api/v1/health` |
| Gate 8 — Compose–K8s parity | **PENDING** | Compose stack not running; run `docker compose -f infrastructure/docker/docker-compose.release1.yml up -d` then `python scripts/k8s/test-compose-k8s-parity.py` |
| Gate 9 — HPA smoke | **PENDING** | Requires prod values + load |
| Gate 10 — ERP scaffolds | **PASS** | `tests/test_erp_scaffolds.py` |
| Gate 11 — R1 demo on K8s | **PENDING** | Adapt `demo-http.ps1` to `K8S_BASE=http://localhost/api/v1` |

## Gate 7 notes

- Fixed: Helm namespace ownership (`--create-namespace`), `UV_CACHE_DIR=/tmp` for non-root containers, `IPE_*` env prefix in deployments.
- K8s ingress returns `status: degraded` (Kafka absent in dev profile) but HTTP 200 — acceptable for R1 profile.

## Tag policy

**Do not tag `v9.4.0-p3`** until Gates 8–9 and 11 PASS.
