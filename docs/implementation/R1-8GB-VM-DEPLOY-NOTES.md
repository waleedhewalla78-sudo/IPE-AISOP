# Release 1 — 8 GB Windows VM Deploy Notes (T037)

**Target**: Single VM for Star Trans on-prem PoC  
**Compose**: `infrastructure/docker/docker-compose.release1.yml` (9 services incl. web-ui)

---

## Minimum specs

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 8 GB | 12 GB |
| CPU | 4 vCPU | 4+ vCPU |
| Disk | 40 GB free | 60 GB SSD |
| OS | Windows Server 2019+ or Ubuntu 22.04 | |

---

## Expected RAM (approximate)

| Service | RAM |
|---------|-----|
| PostgreSQL 16 | 512 MB – 1 GB |
| Redis 7 | 64 MB |
| dpe-svc | 256 MB |
| fea-svc | 256 MB |
| cap-svc | 512 MB |
| connector | 256 MB |
| Kong | 256 MB |
| web-ui (nginx) | 64 MB |
| **Total containers** | **~2.5 – 3.5 GB** |
| OS + Docker Desktop overhead | 2 – 3 GB |

**8 GB is tight but viable** if Odoo runs on a separate host (recommended). Do not co-locate Odoo + full IPE stack on 8 GB.

---

## Deploy steps (Windows)

```powershell
cd E:\AISOP\ipe
.\scripts\deploy-release1.ps1
cd migrations
$env:IPE_DATABASE_URL_SYNC = "postgresql://ipe:ipe_test_pass@localhost:5433/ipe_test"
uv run alembic upgrade head
cd ..
.\scripts\release1-smoke.ps1
```

Web UI: `http://localhost:8082` (compose web-ui) or host dev with `VITE_RELEASE_PROFILE=release1`.

---

## Validation checklist

- [ ] All 9 containers `healthy` within 10 minutes
- [ ] `release1-smoke.ps1` all PASS
- [ ] Login + Control Tower loads in Arabic
- [ ] Odoo sync completes (requires Odoo reachable from connector)
- [ ] VM RAM sustained under 85% during sync

---

*Generated for speckit T037 — manual sign-off required per deployment.*
