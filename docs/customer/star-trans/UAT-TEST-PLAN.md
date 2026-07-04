# UAT Test Plan — Star Trans Release 1

## Objective

Validate IPE Release 1 meets customer acceptance criteria on live (staging) Odoo data.

## Pre-conditions

- [ ] IPE deployed on customer VM
- [ ] Odoo staging accessible from IPE VM
- [ ] Test MOs created in Odoo (min **5** MOs across **3** products)
- [ ] BOMs and routing configured in Odoo for test products
- [ ] Planner champion account created

## Test Cases

### TC-01: Odoo Data Sync

| Step | Action | Expected |
|------|--------|----------|
| 1 | Admin triggers full sync | Sync completes with `status=success` |
| 2 | Check Control Tower | MOs from Odoo visible in queue |
| 3 | Check sync status bar | Shows correct entity counts |

### TC-02: Feasibility Scoring

| Step | Action | Expected |
|------|--------|----------|
| 1 | Review MO scores in Control Tower | All synced MOs have feasibility score |
| 2 | Check MDR score | Composite ≥ **70%** for schedule-eligible MOs |

### TC-03: Resolution Scenarios

| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "Resolve" on at-risk MO | Scenarios displayed with cost/delivery |
| 2 | Compare 2 scenarios | Trade-off visible |

### TC-04: Schedule Generation

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to Schedule | Gantt chart renders |
| 2 | Click "Generate Schedule" | Solver completes **&lt; 90s** |
| 3 | Review Gantt | Operations on correct work centers |

### TC-05: Schedule Approval + Odoo Write-back

| Step | Action | Expected |
|------|--------|----------|
| 1 | Select MOs, click "Approve" | Schedule persists |
| 2 | Trigger Odoo activate | MO dates updated in Odoo |
| 3 | Verify in Odoo | `date_start` / `date_finished` match IPE |

### TC-06: Daily Workflow Simulation

| Step | Action | Expected |
|------|--------|----------|
| 1 | Login as planner | Dashboard loads |
| 2 | Review Control Tower | At-risk MOs identified |
| 3 | Resolve one MO | Scenario applied |
| 4 | Generate schedule | Gantt shows updated plan |
| 5 | Approve and activate | Odoo updated |

### TC-07: Executive Dashboard

| Step | Action | Expected |
|------|--------|----------|
| 1 | Login as executive | Command Center loads |
| 2 | Review OTD trend | Data displays |

## Sign-Off Criteria

- All TC-01 through TC-07: **PASS**
- No **P0** bugs
- Planner champion confirms workflow is usable
- Executive confirms dashboard provides value

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Planner champion | | | |
| Customer IT | | | |
| IPE Engineering | | | |
| Executive sponsor | | | |
