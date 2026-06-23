# Client Demo Guide — IPE v1.0

> **Full walkthrough:** See **[FULL-DEMO-GUIDE.md](./FULL-DEMO-GUIDE.md)** for the complete 12-module demo with numbered steps, expected outputs, and presenter scripts.
>
> **Automated verification:** `.\scripts\run-full-demo.ps1 -ReportPath docs\demo-run-report.txt`

Use this script for a **20-minute live demo** with a client. All data is pre-loaded for tenant **Demo Manufacturing Inc**.

## Before the meeting

```powershell
cd d:\AISOP\ipe
.\scripts\start-product.ps1
# Or if stack already running:
.\scripts\seed-data.ps1
.\scripts\seed-demo-client.ps1
docker compose -f infrastructure\docker build dpe-svc
docker compose -f infrastructure\docker up -d dpe-svc
docker compose -f infrastructure\docker up -d --force-recreate kong
```

Open **http://localhost:8082/login** — sign in as **`admin@demo.com`** / **`demo`**.

Verify: `.\scripts\check-product.ps1`

---

## Demo narrative (20 min)

### 1. Control Tower (3 min) — `/control-tower`

**Story:** “Morning production health at a glance.”

- Point to **KPI cards** — feasibility average, bottlenecks, orders at risk
- **MO Risk Queue** — 10 demo orders sorted by risk (red = MO-DEMO-001 at 52%, MO-DEMO-007 at 45%)
- **Bottleneck map** — Assembly Line 1 and Machining Center under pressure
- Click **Resolve** on a red row → jumps to Resolution Center

**Talking point:** AI scores every MO for material, capacity, and labor — shadow mode means planners approve all actions.

---

### 2. Resolution Center (4 min) — `/resolution-center`

**Story:** “Turn constraints into actionable scenarios.”

- Select **MO-DEMO-001** (Widget A — material shortage)
- Show **3 scenarios**: expedite PO, substitute material, split MO
- Compare **cost vs delivery impact** and business score
- Select **MO-DEMO-002** — approved “alternate work center” scenario already on file

**Talking point:** Each scenario is scored for business impact; planners pick the best trade-off, not the AI alone.

---

### 3. Schedule (3 min) — `/schedule`

**Story:** “Constraint-aware scheduling with OR-Tools.”

- Click **Refresh** to load Gantt from live MOs + routing
- Show operations across **Assembly Line 1**, **Machining Center**, **Packaging**
- Discuss AI-suggested vs planned bars (when solver returns assignments)

**Talking point:** Schedule respects BOM routing, work center capacity, and due dates.

---

### 4. Executive Dashboard (3 min) — `/executive`

**Story:** “Leadership view — OTD, delays, inventory value.”

- **OTD trend** from completed MOs (MO-DEMO-009, MO-DEMO-010)
- **Delay breakdown** by cause: material, capacity, labor, supplier
- **Planning accuracy** and inventory value from seeded history

---

### 5. War Room + AI Trust (2 min)

- **War Room** `/war-room` — disruption aggregation
- **AI Trust** `/ai-trust` — model transparency and adoption metrics

---

### 6. Shop Floor + SCN Portal (2 min)

- **Shop Floor** `/shop-floor` — live work orders (MO-DEMO-001 assembly, MO-DEMO-005 machining)
- **SCN Portal** `/scn-portal` — supplier scorecards (Parts R Us 95%, QuickShip 75% at risk)

---

### 7. Copilot (2 min) — `/copilot`

Try asking:
- “Which orders are at risk this week?”
- “What is blocking MO-DEMO-001?”
- “Show bottleneck work centers”

---

### 8. Close (1 min)

**Key messages:**
- End-to-end: demand → feasibility → resolution → schedule
- Shadow mode = trust before autonomy
- 85/100 deployment readiness; production IdP (Keycloak) on roadmap

---

## Demo data reference

| Entity | Count | IDs |
|--------|-------|-----|
| Manufacturing orders | 10 | MO-DEMO-001 … MO-DEMO-010 |
| At-risk MOs (score < 70) | 3 | MO-DEMO-001, 007, 008 |
| Resolution scenarios | 8 | Material, capacity, overtime strategies |
| Delay events | 8 | material, capacity, labor, supplier, quality |
| Customers | 3 | Acme Corp, Globex, Initech |
| Work centers | 3 | Assembly Line 1, Machining Center, Packaging |

---

## Troubleshooting during demo

| Issue | Fix |
|-------|-----|
| Empty Control Tower queue | Run `.\scripts\seed-demo-client.ps1` |
| Empty Resolution Center | Same — scenarios are in DB |
| Schedule blank | Ensure MOs exist; click Refresh |
| Shop Floor empty | Run `.\scripts\seed-demo-client.ps1`, rebuild dpe-svc, then `docker compose -f infrastructure\docker up -d --force-recreate kong` |
| Login fails | `.\scripts\check-product.ps1` |
