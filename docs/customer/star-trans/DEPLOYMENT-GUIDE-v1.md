# Star Trans Deployment Guide — IPE Release 1

**Version:** 1.0  
**Customer:** Star Trans — Electrical Transformers (Egypt / MENA)  
**Profile:** Release 1 (8-service compose)  
**Target VM:** 8 GB RAM  
**Last updated:** 2026-07-04

---

## 1. Prerequisites

| Requirement | Specification |
|-------------|---------------|
| Host OS | Windows Server 2019+ **or** Ubuntu 22.04 LTS |
| RAM | **8 GB minimum** (16 GB recommended) |
| Disk | 40 GB free |
| Container runtime | Docker Desktop **4.25+** (Windows) or Docker Engine **24+** (Linux) |
| ERP | Odoo **17 or 19** with **Manufacturing**, **Sales**, and **Purchase** modules installed |
| Network | VM must reach Odoo (same host or LAN/VPN) |
| Ports (host) | **8082** (web UI), **8000** (Kong HTTP), **8443** (Kong HTTPS), **5433** (PostgreSQL published for ops) |

Optional enterprise features (SSO, Vault, Prometheus/Grafana) are available when using the full enterprise overlay; Release 1 MVP can run with local auth and env-based secrets.

---

## 2. Installation Steps

### Windows (PowerShell)

```powershell
# Step 1: Create project directory
mkdir C:\IPE
cd C:\IPE

# Step 2: Copy release package (provided by IPE team)
# Contains: docker-compose.release1.yml, .env, scripts/, config/, infrastructure/

# Step 3: Configure environment
# Edit .env with customer-specific values:
#   IPE_TENANT_NAME=StarTrans
#   ODOO_URL=http://<odoo-host>:8069
#   ODOO_DB=<customer-db-name>
#   ODOO_USERNAME=<odoo-user>
#   ODOO_PASSWORD=<odoo-password>

# Step 4: Start stack (from package root that contains infrastructure/docker)
cd infrastructure\docker
docker compose -f docker-compose.release1.yml up -d

# Step 5: Verify health
curl.exe http://localhost:8000/api/v1/health

# Step 6: Open web UI
# Browser: http://localhost:8082
# Default login: provided by IPE team (e.g. admin@ipe.example.com / <provided-password>)
```

### Linux

```bash
mkdir -p /opt/ipe && cd /opt/ipe
# Extract release package, edit .env
cd infrastructure/docker
docker compose -f docker-compose.release1.yml up -d
curl -sf http://localhost:8000/api/v1/health
```

**Expected health response:** `"status":"healthy"` (or `degraded` only if optional deps are down).

---

## 3. Odoo Integration Setup

### 3.1 Connection parameters

| Parameter | Example | Notes |
|-----------|---------|-------|
| Odoo URL | `http://host.docker.internal:8069` | Use host gateway when Odoo runs on the VM host |
| Database | `starttrans1` | Customer staging DB name |
| Username | planner email or API user | Needs MRP read/write for activate |
| Password | (secure) | Prefer Vault in enterprise profile |

### 3.2 Configure from IPE Admin (recommended)

1. Log in to IPE web UI as **admin**.
2. Open **Admin → Odoo / ERP** (or equivalent Release 1 admin tab).
3. Enter URL, database, username, password; save (password stored encrypted / Vault when enabled).
4. Run **Connection test** — expect work centers / products count &gt; 0.
5. Run **Full sync**.

### 3.3 Field mapping

Complete `ODOO-FIELD-MAPPING-WORKSHEET.md` **before** go-live if Star Trans uses custom fields. Standard MRP fields map automatically.

### 3.4 First sync verification

| Check | Expected |
|-------|----------|
| Sync status API | `status=success` |
| Control Tower queue | Customer MOs visible |
| Data quality flags | Prefer **0** open P0 flags on go-live MOs |
| MDR composite (demo MOs) | ≥ 70% for schedule gate |

### 3.5 Control Tower after sync (expected)

- Feasibility queue lists manufacturing orders from Odoo.
- Scores and constraint labels (e.g. material shortage) appear on at-risk MOs.
- KPI strip shows at-risk count and average score.

*(Screenshots: attach customer-specific captures during UAT.)*

---

## 4. User Accounts Setup

| Role | Typical use |
|------|-------------|
| **admin** | ERP config, sync, tenant settings |
| **planner** | Control Tower, Resolution, Schedule |
| **manager** | Approve schedules, oversee planners |
| **supervisor** | Shop-floor / execution views (if enabled) |
| **executive** | Command Center / OTD dashboards |

**Password policy (recommended):** minimum 12 characters, rotate every 90 days, no shared accounts for planners.

Create planner accounts via admin UI or Keycloak (enterprise profile). Assign roles before training.

---

## 5. Daily Operations

### 5.1 Planner morning workflow

1. **Login** → web UI (`http://localhost:8082` or HTTPS `:8443`).
2. **Control Tower** — review at-risk MOs and feasibility scores.
3. **Resolution** — open scenarios for critical MOs; apply preferred trade-off.
4. **Schedule** — generate OR-Tools schedule; review Gantt.
5. **Approve** — persist schedule; **Activate** write-back to Odoo when ready.

### 5.2 Sync status monitoring

- Admin / sync status bar: last run time and entity counts.
- Re-run partial sync after large Odoo changes (new MOs, BOM updates).

### 5.3 Backup procedure

```bash
# Example — PostgreSQL dump from published port 5433
pg_dump -h localhost -p 5433 -U ipe ipe_test | gzip > ipe_backup_$(date +%Y%m%d).sql.gz
```

Store backups off-VM; retain per customer policy.

### 5.4 Troubleshooting

| Symptom | Action |
|---------|--------|
| Health timeout | `docker compose ps`; restart unhealthy services |
| Sync fails / work_centers=0 | Check Odoo URL from container network; credentials; Odoo up |
| API rate limit (429) | Wait 1 minute; avoid load tests on production VM |
| Schedule gate fails | Raise MDR (BOM/routing/inventory completeness) |
| Activate fails | Ensure MO has `erp_mo_id` and AI suggested dates |

---

## 6. Architecture Diagram

```text
┌─────────────┐     HTTPS/HTTP      ┌──────────┐
│   Browser   │ ──────────────────► │   Kong   │
│  :8082 UI   │                     │ :8000/8443│
└─────────────┘                     └────┬─────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
              ▼                          ▼                          ▼
        ┌──────────┐              ┌──────────┐              ┌──────────┐
        │ dpe-svc  │              │ fea-svc  │              │ cap-svc  │
        │ (auth,   │              │ (feasib. │              │ (OR-Tools│
        │  admin)  │              │  queue)  │              │ schedule)│
        └────┬─────┘              └────┬─────┘              └────┬─────┘
             │                         │                         │
             └────────────┬────────────┴────────────┬────────────┘
                          ▼                         ▼
                   ┌────────────┐            ┌────────────┐
                   │ PostgreSQL │            │ connector  │──XML-RPC──► Odoo
                   │  (+ RLS)   │◄───────────│  (sync)    │            :8069
                   └────────────┘            └────────────┘
```

**Release 1 core path:** Browser → Kong → dpe / fea / cap / connector → PostgreSQL ↔ Odoo.

---

## Support

- Training: `docs/implementation/R1-TRAINING-CURRICULUM.md`
- UAT: `docs/customer/star-trans/UAT-TEST-PLAN.md`
- SOW inputs: `docs/customer/star-trans/SOW-INPUT.md`

*IPE Engineering — Release 1 customer package*
