# Star Trans — 180-Minute Hybrid Demo Runbook

**Client:** Star Trans — Electrical Transformer Technology  
**Audience:** Mixed (CEO / Ops Director + production planners + IT)  
**Mode:** **Hybrid** — live Odoo sync opener + seeded 32/32 depth + Copilot live  
**Release 1 path:** **13/13 integration steps verified** on 9-service stack (see [RELEASE1-DEMO-STATUS.md](./RELEASE1-DEMO-STATUS.md)). Full 32/32 + Copilot agents requires hybrid stack below.  
**Duration:** **180 minutes** (3 hours)  
**Environment:** Local laptop · http://localhost:8082  
**Login:** `Ahmed@nour` / `admin`  
**Web profile:** **Full** (`npm run dev` — do **not** set `release1` for Copilot + v8 acts)

---

## Quick reference card (keep visible)

| Item | Value |
|------|-------|
| **Hero at-risk MOs (seed)** | MO-ST-001 (copper ~52%), MO-ST-007 (CRGO ~45%) |
| **Hero live Odoo MOs** | erp_mo_id `9` TR-500, `10` TR-1000 (~82.5%, material) |
| **Products** | Distribution Transformer 500 kVA, Pad-Mount 250 kVA, Power 50 MVA |
| **Work centers** | Winding Station, Core & Coil Assembly, Tank Fabrication & Test Bay |
| **Customers** | Great Lakes Utility (Tier 1), Midwest Grid Co |
| **Suppliers** | Midwest Copper Supply, CRGO Steel International |
| **One-line value** | Red rows = revenue at risk, scored **before** the shift starts |
| **Honesty line** | Enterprise SSO + full ERP publish = Phase 2; today = planning intelligence |

---

## Preparation timeline

### T-120 — One-shot hybrid prep

```powershell
cd E:\AISOP\ipe

# Ensure Odoo Windows service is running (for Act 0)
# http://localhost:8069 — database starttrans1

.\scripts\prepare-startrans-demo-hybrid.ps1
```

**Pass criteria:**
- Script completes without exit 1
- `docs\demo-data\startrans-pre-demo.txt` ends with **32/32 PASS**
- Copilot pre-warm OK (or note backup plan)

**If Odoo is down:** re-run with `-SkipOdooSync` — Act 0 uses narrated backup slides.

### T-60 — Web UI + browser

```powershell
cd E:\AISOP\ipe\apps\web
npm run dev
```

- Open **incognito** window → http://localhost:8082/login  
- Log in once; confirm Planning Hub loads  
- Open second tab: Odoo http://localhost:8069 (for Act 0 write-back peek if needed)

### T-30 — Presenter smoke (10 min)

| # | Check | Pass |
|---|--------|:----:|
| 1 | Control Tower → MO-ST-001 visible, score ~52 | ☐ |
| 2 | Resolution → MO-ST-001 → ≥3 scenarios | ☐ |
| 3 | Schedule → Refresh → Gantt renders | ☐ |
| 4 | POST sync (optional) → live MOs in queue | ☐ |
| 5 | Copilot → Query 1 from cheat sheet < 90s | ☐ |
| 6 | Executive → OTD chart loads | ☐ |
| 7 | `project-plan-startrans-w12.xlsx` exists | ☐ |

### T-5 — Room setup

- [ ] HDMI / screen share tested  
- [ ] Copilot cheat sheet open: [STARTRANS-COPILOT-CHEATSHEET.md](./STARTRANS-COPILOT-CHEATSHEET.md)  
- [ ] Hero card (top of this doc) on second monitor or printed  
- [ ] Phone on silent; Docker Desktop running  
- [ ] Water; confirm 15-min break at ~1:15  

---

## 180-minute run of show

**Pacing:** ~15 min exec framing · ~100 min hands-on · 15 min break · ~50 min exec + close · 10 min buffer  

| Time | Duration | Segment | Primary audience | Route / action |
|------|----------|---------|------------------|----------------|
| 0:00 | 15 min | **Welcome & framing** | All | Slides or verbal: pain → IPE thesis → hybrid agenda |
| 0:15 | 20 min | **Act 0 — Live Odoo → IPE** | IT + planners | Hybrid sync story |
| 0:35 | 20 min | **Act 1 — Problem visibility** | All | Control Tower deep dive |
| 0:55 | 20 min | **Act 2 — Resolve & schedule** | Planners (+ exec observe) | Resolution + Schedule |
| 1:15 | 15 min | **☕ Break** | — | — |
| 1:30 | 20 min | **Act 3 — Planning loop (v8)** | Planners | Demand, Scenarios, Supply |
| 1:50 | 25 min | **Act 4 — Copilot live** | All | AI & Governance → Copilot |
| 2:15 | 20 min | **Act 5 — Executive view** | C-suite | Executive, War Room, Cost of Chaos |
| 2:35 | 10 min | **Act 6 — Differentiators** | C-suite | Quality, Sustainability |
| 2:45 | 15 min | **Roadmap & next steps** | All | UAT, pricing, Q&A buffer |

---

## Act 0 — Live Odoo → IPE (20 min) · Hybrid opener

**Goal:** Prove production path before seeded depth. IT must see real sync; exec must hear “your ERP, not a spreadsheet duplicate.”

### Talking points (exec, 3 min)

> “We’ll start with your Odoo manufacturing orders appearing in IPE within one sync cycle. The richer scenario data you’ll see next is representative of your product mix — UAT will use only your live master data.”

### Steps (presenter, 12 min)

1. **Show Odoo** (browser tab): Manufacturing → MOs for TR-500 / TR-1000  
2. **IPE login** → Planning → Control Tower  
3. **Point out SyncStatusBar** if visible (full profile may use manual sync API instead — run sync from PowerShell if needed):

```powershell
# Only if queue doesn't show live MOs
$login = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body '{"email":"Ahmed@nour","password":"admin"}'
$h = @{ Authorization = "Bearer $($login.data.access_token)"; "X-Tenant-ID" = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11" }
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/sync/run" -Method POST -ContentType "application/json" -Body '{"entity":"all"}' -Headers $h -TimeoutSec 300
```

4. **Refresh Control Tower** — show MOs with `erp_mo_id` 9 and 10, feasibility ~82.5, constraint `material`  
5. **Data quality** — show zero flags on synced MOs (Admin or sync API)  
6. **Do NOT live-demo write-back** unless rehearsed — say: “Approve flow updates Odoo dates — we’ll validate in UAT.”

### Contingency — Odoo fails

| Symptom | Action | Say |
|---------|--------|-----|
| Sync error / Odoo down | Skip to Act 1 immediately | “Odoo staging is offline — the seeded data shows identical workflow on representative transformer MOs.” |
| Only 2 MOs in queue | Pair with Act 1 MO-ST-001 | “Production sync brings all active MOs; demo seed shows full at-risk portfolio.” |
| Sync slow (>60s) | Narrate while waiting | “Typical 15-min scheduled sync; manual run for demo.” |

---

## Act 1 — Problem visibility (20 min)

**Route:** `/planning/control-tower`

### For executives (8 min)

- KPI cards: avg feasibility, orders at risk, bottlenecks  
- **MO-ST-001** — Distribution Transformer 500 kVA — **~52%** — **material_shortage** (copper)  
- **Line:** “Red rows are revenue at risk — scored before the shift starts, not after the line stops.”

### For planners (10 min)

- Sort queue by feasibility (lowest first)  
- Compare **MO-ST-001** vs **MO-ST-007** (CRGO + test capacity ~45%)  
- Click **Resolve** on MO-ST-001 → tee up Act 2  
- Optional: WebSocket mention — “Queue updates live as scores change.”

### Objection handlers

| Question | Response |
|----------|----------|
| “Is this our data?” | Act 0 showed live Odoo MOs; MO-ST-* is representative transformer portfolio for depth. UAT = Odoo only. |
| “Why two MO types in queue?” | Live sync + demo seed coexist in hybrid prep; production uses Odoo IDs only. |
| “Can we trust the score?” | Five gates: demand, BOM, material, capacity, labor — shadow mode, human approves. |

---

## Act 2 — Resolve & schedule (20 min)

### Resolution Center (10 min) — `/planning/resolution`

Select **MO-ST-001**. Walk three scenarios:

1. Expedite copper PO — Midwest Copper Supply  
2. Substitute wire gauge  
3. Split coil batches  

**Ops line:** “Each option has cost vs delivery impact — planner chooses, AI recommends.”  
**Exec line:** “Structured decisions, auditable — not WhatsApp firefighting.”

### Schedule (10 min) — `/planning/schedule`

1. **Refresh** — OR-Tools Gantt (Winding → Core & Coil → Test Bay)  
2. **Upload Project Plan** (collapsed panel, top-right):  
   - Create new plan → `project-plan-startrans-w12.xlsx` → Upload  
   - View → **Uploaded project plan** → `PLAN-STARTRANS-W12`  
3. **Say:** “When ERP sync lags, planners upload this week’s Excel — same as MS Project exports today.”

### Contingency

| Issue | Fix |
|-------|-----|
| Solver timeout | Use uploaded plan view only |
| Upload fails | MO_ID must be MO-ST-*; WC WC001–WC003 |
| Empty Gantt | Re-run Schedule Refresh; check cap-svc container |

---

## ☕ Break (15 min) — 1:15–1:30

Reset browser tabs to Control Tower. Pre-run Copilot Query 1 in background if Act 4 was slow in smoke test.

---

## Act 3 — Planning loop v8 (20 min)

| Page | Route | Action | Talking point |
|------|-------|--------|---------------|
| Demand | `/planning/demand` | Run sense cycle | Forecast from utility order history |
| Scenarios | `/planning/scenarios` | Create “CRGO delay +5d” → Simulate | Sandbox before committing |
| Supply | `/supply-chain/supply-planning` | View network map | Chicago, Houston, Dallas DC, Minneapolis winding |
| Orders (optional) | `/supply-chain/orders` | Create order + ATP | Customer promise vs inventory |

**Exec wrap (2 min):** “This is the S&OP loop — sense demand, simulate disruption, check network — without leaving IPE.”

---

## Act 4 — Copilot live (25 min)

**Route:** `/ai-governance/copilot`  
**Cheat sheet:** [STARTRANS-COPILOT-CHEATSHEET.md](./STARTRANS-COPILOT-CHEATSHEET.md)

### Setup (3 min)

- Confirm **planner** agent role in dropdown  
- **Say:** “Shadow mode — Copilot reads Star Trans data; planners approve every action.”

### Live queries (15 min — wait full response each, ~30–90s)

| # | Query | Purpose |
|---|-------|---------|
| 0 | `What is the current FG stock for Distribution Transformer 500 kVA?` | Pre-warm (if not done T-30) |
| 1 | `Which manufacturing orders are at risk this week?` | Feasibility triage |
| 2 | `What is blocking MO-ST-001?` | Copper / material story |
| 3 | `Show bottleneck work centers` | Capacity narrative |
| 4 (optional) | `What is the current FG stock for Distribution Transformer 500 kVA and Pad-Mount Transformer 250 kVA?` | Material status intent |

### Role switch demo (5 min) — mixed audience

- Switch agent to **executive** → ask: “Summarize orders at risk and financial exposure this week.”  
- **Say:** “Same data, different lens — planner gets actions, executive gets summary.”

### Copilot backup plan

1. Show `startrans-pre-demo.txt` CP10–11 section  
2. **Say:** “LLM runs locally for data privacy — API path validated; we’ll retry.”  
3. Pivot to Resolution Center (Act 2 recap) — same story without NL

### Do NOT ask Copilot

- “Connect to SAP” (not live)  
- “Create production order in ERP” (deferred)  
- “Widget A” (old demo names)

---

## Act 5 — Executive view (20 min)

| Page | Route | Highlight | Time |
|------|-------|-----------|------|
| Command dashboard | `/command-center/dashboard` | Alert summary | 3 min |
| Executive | `/command-center/executive` | OTD trend, delay by cause | 8 min |
| War Room | `/command-center/war-room` | Active alerts, recovery options | 6 min |
| Cost of Chaos | `/command-center/cost-of-chaos` | 7d USD breakdown | 3 min |

**C-suite close line:** “One session — OTD, root cause, and dollar exposure — without waiting for month-end.”

---

## Act 6 — Differentiators (10 min)

| Page | Route | Highlight |
|------|-------|-----------|
| Sustainability | `/ai-governance/sustainability` | ESG score, carbon tCO2e |
| Quality | `/ai-governance/quality` | Defect rate, FPY trend |
| AI Trust (optional) | `/ai-governance/ai-trust` | Shadow mode adoption metrics |

**Say:** “32 validated checkpoints; ERP hardening and SSO on roadmap — today proves integrated planning.”

---

## Roadmap & close (15 min)

### Suggested talking track

| Topic | Message |
|-------|---------|
| **UAT** | 2–4 weeks; Odoo as sole source of truth; planner training (Arabic) |
| **Release 1** | 8-service deploy on 8GB VM; $18K–30K/yr signal (confirm with sales) |
| **Phase 2** | Copilot in production nav, demand/scenario, Keycloak, encrypted creds |
| **Support** | WhatsApp escalation in contract (MENA differentiator) |
| **Leave-behind** | [Executive one-pager](../PRD-IPE-EXECUTIVE-ONE-PAGER.md) |

### Q&A buffer (10 min)

See objection table in Act 1 +:

| Objection | Response |
|-----------|----------|
| vs Kinaxis / SAP IBP | “We compete with Excel + Odoo for your first step — feasibility before the shift, weeks not months to value.” |
| AI replacing planners | “Shadow mode — AI recommends; your team approves. Copilot is a reader, not an autopilot.” |
| Data security | “On-prem option; LLM local via Ollama; production creds in vault (R1.1).” |

---

## Audience-specific focus guide

| When this person speaks… | Emphasize… | Skip / shorten… |
|--------------------------|------------|-----------------|
| CEO / Ops Director | Acts 0 framing, 1 KPIs, 5 War Room, roadmap pricing | Schedule upload details |
| Production planner | Acts 1–2, 3 demand/scenario, 4 Copilot queries 1–3 | Sustainability |
| IT / ERP admin | Act 0 sync, data quality flags, honesty on XML-RPC vs REST addon | Copilot role switch |
| Finance | Resolution cost/delivery, Cost of Chaos, executive P&L | Shop floor |

---

## Emergency reference

| Issue | Command / fix |
|-------|----------------|
| Empty Control Tower | `.\scripts\seed-startrans-demo.ps1` |
| Full reset | `.\scripts\prepare-startrans-demo-hybrid.ps1` |
| Login fails | Same as above |
| Copilot 503 | Check Ollama `:11434` or `docker ps` for ollama container |
| Kong 502 | `docker compose -f infrastructure\docker\docker-compose.yml up -d --force-recreate kong` |
| Odoo auth fail | User `whewalla@gmail.com` / `admin`, DB `starttrans1` |

---

## Post-demo checklist

- [ ] Capture client questions for UAT backlog  
- [ ] Note whether Act 0 (Odoo) or Act 4 (Copilot) caused friction  
- [ ] Send executive one-pager + training curriculum outline  
- [ ] Schedule UAT kickoff (SOW, Odoo staging creds, planner accounts)  
- [ ] Do **not** leave demo credentials on client machines unless agreed  

---

*Star Trans · 180 min · Hybrid · Mixed audience · Copilot in · 2026-06-30*
