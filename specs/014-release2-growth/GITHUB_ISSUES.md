# GitHub Issues — Release 2 Commercial Growth (014)

**Generated**: 2026-07-01 via `/speckit.taskstoissues`  
**Feature**: `specs/014-release2-growth`  
**Milestone**: `v9.1.0-r2`  
**Labels**: `release2`, `P0`, `014`

**Prerequisites**: `gh auth login`; git remote configured; safe.directory set for `E:/AISOP/ipe`.

```powershell
cd E:\AISOP\ipe
git -c safe.directory=E:/AISOP/ipe remote get-url origin
# Create issues manually or extend scripts/create-release-issues.ps1
```

---

## Epic: IPE v9.1.0-r2 — Commercial Growth

| Issue | Title | Task IDs | Priority |
|-------|-------|----------|----------|
| R2-EPIC | Release 2 — Agentic planning + Outcomes + Copilot Lite | All | P0 |

---

## Stream A — Auto-propose resolution

**Title**: `T110-T115: Auto-propose resolution scenarios after Odoo sync rescore`

**Labels**: `release2`, `P0`, `connector`, `res-svc`

**Body**:

```markdown
## Summary
When connector rescores MOs after Odoo sync, call res-svc to propose scenarios for MOs below tenant threshold (default 75%).

## Tasks
- [ ] T110 connector `_auto_propose_scenarios()` in sync_engine
- [ ] T111 tenant config `auto_propose_threshold`
- [ ] T112 fix res-svc Kafka handler mo_id field
- [ ] T113 dedupe by (mo_id, strategy)
- [ ] T114 unit/integration test
- [ ] T115 RES_SVC_URL in release1 compose

## Acceptance
After sync, MO-ST-001 has ≥3 proposed scenarios without manual POST.

## References
- specs/014-release2-growth/plan.md §1.1
- FR-R2-01
```

---

## Stream B — Outcomes dashboard

**Title**: `T120-T122: Customer Outcomes dashboard for Release 1 profile`

**Labels**: `release2`, `P0`, `web-ui`, `executive`

**Body**:

```markdown
## Summary
Command Center Outcomes tab: OTD baseline, ROI metrics, sync health, baseline capture.

## Tasks
- [ ] T120 OutcomesPage.tsx
- [ ] T121 baseline capture + ar i18n
- [ ] T122 router + hub tab (release1 visible)

## Acceptance
CEO can capture OTD baseline in 2 clicks; page loads on 8 GB VM stack.

## References
- FR-R2-03, FR-R2-04
- SC-R2-04
```

---

## Stream C — Copilot Lite

**Title**: `T140-T142: Planner Copilot Lite (structured, no Ollama required)`

**Labels**: `release2`, `P1`, `dpe-svc`, `copilot`

**Body**:

```markdown
## Summary
Keyword intent router in dpe-svc; collapsible panel on Control Tower.

## Intents
at_risk_mos, mo_detail, scenario_list, sync_status, schedule_summary

## Acceptance
Structured path < 3s; works without nlp-svc in release1 compose.

## References
- FR-R2-06, FR-R2-07
```

---

## Stream D — Odoo write-back

**Title**: `T150-T153: Odoo chatter notification on scenario approve`

**Labels**: `release2`, `P1`, `connector`, `odoo`

**Body**:

```markdown
## Summary
Approved resolution scenarios post mail.message to Odoo MO.

## Tasks
- [ ] T150 connector resolution-notify endpoint
- [ ] T151 res-svc approve hook
- [ ] T152 feature flag default false
- [ ] T153 mock Odoo test

## Acceptance
Approve scenario → chatter visible on Odoo MO (UAT).

## References
- FR-R2-08
```

---

## Closure

**Title**: `T160-T161: Release 2 demo script + R1 regression`

**Labels**: `release2`, `P0`, `demo`

**Body**:

```markdown
## Summary
- scripts/run-release2-demo.ps1 → 5/5 PASS
- scripts/run-release1-integration-demo.ps1 → 13/13 PASS (no regression)

## References
- SC-R2-01, SC-R2-06
```

---

## Issue creation command template

```powershell
gh issue create --title "T110-T115: Auto-propose resolution scenarios after Odoo sync rescore" `
  --label "release2,P0" `
  --body-file specs/014-release2-growth/issues/stream-a.md
```

*Note: Run `gh issue list` before create to avoid duplicates on re-run.*
