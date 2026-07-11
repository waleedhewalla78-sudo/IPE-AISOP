# IPE Star Trans Smoke Test Checklist

**Version:** v9.2.0-planning — Release 1 Profile  
**Run after:** Initial deployment or after any update

---

## Pre-conditions
- Docker stack is running: `docker compose ps` — all services Up
- Browser accessible to `http://<server-ip>:8082`
- At least one Odoo sync completed (`GET /api/v1/sync/status` shows `completed`)

---

## 1. Infrastructure Checks

```bash
# All containers healthy
docker compose ps
```
- [ ] `db` — Up, healthy
- [ ] `redis` — Up, healthy
- [ ] `dpe-svc` — Up, healthy
- [ ] `fea-svc` — Up
- [ ] `res-svc` — Up
- [ ] `cap-svc` — Up
- [ ] `mat-svc` — Up
- [ ] `connector` — Up, healthy
- [ ] `kong` — Up
- [ ] `web-ui` — Up

---

## 2. API Health Checks

```bash
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
```
- [ ] Kong gateway responds `{"status": "ok"}`

```bash
for port in 8001 8002 8003 8004 8005 8009; do
  echo "Port $port:"; curl -s http://localhost:$port/api/v1/health; echo
done
```
- [ ] dpe-svc (8001) — `{"status": "ok"}`
- [ ] mat-svc (8002) — `{"status": "ok"}`
- [ ] cap-svc (8003) — `{"status": "ok"}`
- [ ] fea-svc (8004) — `{"status": "ok"}`
- [ ] res-svc (8005) — `{"status": "ok"}`
- [ ] connector (8009) — `{"status": "ok"}`

---

## 3. Database Checks

```bash
docker compose exec db pg_isready -U ipe -d ipe
```
- [ ] DB responds: `accepting connections`

```bash
docker compose exec dpe-svc uv run alembic current
```
- [ ] Alembic shows: `049 (head)` or current latest migration

---

## 4. Odoo Connector Checks

```bash
curl -s http://localhost:8009/api/v1/sync/status
```
- [ ] Status shows `completed` or `idle` (not `error`)
- [ ] `synced_entities` contains product, work_centre, bom counts

```bash
# Trigger incremental sync
curl -X POST http://localhost:8009/api/v1/sync/run
```
- [ ] Sync initiates without error

---

## 5. Web UI Checks

Open browser: `http://<server-ip>:8082`

- [ ] Login page loads (no blank screen, no JS error)
- [ ] Login with `admin@ipe.local` / `admin` succeeds
- [ ] Control Tower page loads with Manufacturing Orders list
- [ ] MOs are visible (synced from Odoo)
- [ ] Filter by status works
- [ ] MO detail opens on click

---

## 6. Arabic Language Check

- [ ] Click user profile (top-right) → Language → Arabic
- [ ] Page reloads with Arabic text
- [ ] RTL layout renders correctly (text right-aligned, nav mirrored)
- [ ] Control Tower labels appear in Arabic
- [ ] No garbled characters

---

## 7. Feasibility & Resolution Checks

- [ ] At least one MO shows feasibility score
- [ ] Resolution suggestions visible for constrained MOs
- [ ] "Propose" action available in UI

---

## 8. Capacity Check

```bash
curl -s http://localhost:8003/api/v1/capacity/utilization | python3 -m json.tool
```
- [ ] Returns capacity data (not 500 error)

---

## 9. Kong Routing Check

```bash
# Health via Kong (not direct)
curl -s http://localhost:8000/api/v1/health
curl -s http://localhost:8000/api/v1/feasibility/queue 2>&1 | python3 -m json.tool
```
- [ ] Kong routes requests to backend services
- [ ] No 502/504 gateway errors

---

## 10. Performance Spot-Check

```bash
# Time a critical endpoint
time curl -s http://localhost:8000/api/v1/health > /dev/null
```
- [ ] Health endpoint responds in < 200ms

---

## Pass / Fail Summary

| Check | Pass | Fail | Notes |
|-------|------|------|-------|
| Infrastructure (all containers up) | | | |
| API health (all 6 services) | | | |
| Database (pg_isready + alembic) | | | |
| Odoo sync (completed status) | | | |
| Web UI (login + MO list) | | | |
| Arabic language toggle | | | |
| Feasibility (scores visible) | | | |
| Capacity (API responds) | | | |
| Kong routing | | | |
| Performance (< 200ms health) | | | |

**Overall Result:** PASS / FAIL  
**Date:** ___________  
**Tester:** ___________  
**Notes:** 

---

## If Smoke Test Fails

1. Check container logs: `docker compose logs <service> --tail 50`
2. Verify `.env` values are correct
3. Check database migrations: `docker compose exec dpe-svc uv run alembic current`
4. Verify Odoo connectivity: `curl http://localhost:8009/api/v1/sync/status`
5. Contact IPE support with log output
