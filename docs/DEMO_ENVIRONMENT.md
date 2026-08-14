# IPE Star Trans Demo Environment

**Demo date:** Monday 18 Aug 2026 (morning)  
**Audience:** Star Trans  
**Product:** IPE planning / Control Tower / Schedule / Copilot  

---

## Required environment

| Item | Requirement |
|------|-------------|
| OS | Windows 10/11 or macOS (Docker Desktop required) |
| Browser | Chrome or Edge latest (not IE) |
| Resolution | **1920×1080** minimum (Control Tower + dual-rail needs width) |
| Zoom | 100% |
| Network | Local stack; no customer VPN required for lab demo |

---

## Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin / demo lead | `admin@deploy.com` | `deploy` |
| Planner | `planner@deploy.com` | `deploy` |
| Legacy lab | `Ahmed@nour` | `admin` |

UI: `http://localhost:8082`  
API (Kong): `http://localhost:8000`

---

## Bring-up (from `ipe/`)

```powershell
cd ipe
copy .env.template .env   # if missing
docker compose -f infrastructure/docker/docker-compose.release2.yml up -d
# Wait until kong + web-ui + dpe healthy
.\scripts\seed-startrans-demo.ps1   # or seed-data + seed-demo-client + overlay
# Optional hygiene if old Widget names linger:
Get-Content scripts\purge-widget-fixtures.sql -Raw | docker exec -i docker-db-1 psql -U ipe -d ipe_test
```

Validate:

```powershell
.\scripts\check-product.ps1
.\scripts\star-trans-validate.ps1 -DpePort 8020 -ConnectorPort 8016
```

---

## Pre-demo checklist (T-30 min)

- [ ] R2 containers Up: kong `:8000`, web-ui `:8082`, dpe, mat, cap, fea, res, connector  
- [ ] Login as `admin@deploy.com` / `deploy` succeeds → lands on Today or Control Tower  
- [ ] Today greeting shows a **human name** (never a UUID)  
- [ ] Control Tower MO queue has no **Widget A / Widget B** product names  
- [ ] No **1/1/1970** dates — empty due dates show **Not set**  
- [ ] Unscored MOs sit under collapsible **Needs data**, not the main risk queue  
- [ ] No **AI autonomy: 0** vanity tile — Copilot actions / dash instead  
- [ ] Schedule page loads without hanging on Auto Schedule  
- [ ] Copilot opens from AI domain; Agents A1–A17 visible  
- [ ] Screenshots folder ready: `docs/star-trans-demo-screenshots/`  

---

## Screenshot targets

1. Today / Workspace (greeting + KPIs)  
2. Control Tower (MO risk queue)  
3. Needs data panel (if any unscored)  
4. Schedule (Gantt / Auto Schedule idle)  
5. Resolution Center  
6. Copilot with an agent selected  

Save PNGs under `docs/star-trans-demo-screenshots/` with clear names (`01-today.png`, …).

---

## Rollback / stop

```powershell
docker compose -f infrastructure/docker/docker-compose.release2.yml stop
```

Do **not** force-reseed mid-demo.
