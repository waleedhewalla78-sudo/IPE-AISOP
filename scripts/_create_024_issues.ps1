$ErrorActionPreference = "Continue"
Set-Location "E:\AISOP\ipe"

$existing = gh issue list --state all --limit 200 --json number,title | ConvertFrom-Json
$have = @{}
foreach ($i in $existing) {
  if ($i.title -match '\bT(\d{3})\b') { $have[$Matches[1]] = $i.number }
}

$tasks = @(
  @{ id = "101"; title = "T101: [024] Verify Alembic chain 050-059 absorb (schema spine)"; body = "Spec 024 Phase 1. Verify migrations 051-059 peer-absorbed; 055 ALTER only." },
  @{ id = "103"; title = "T103: [024] Point feature.json + AGENTS.md at Spec 024 / constitution 1.3.0"; body = "Spec 024 T003 feature pointers." },
  @{ id = "105"; title = "T105: [024] Extend SupplierScore ORM for migration 055 columns"; body = "Spec 024 T005." },
  @{ id = "110"; title = "T110: [024] PredictiveRiskScorer + GET /feasibility/predict/{mo_id}"; body = "Spec 024 US1 / T010-T013." },
  @{ id = "115"; title = "T115: [024] RootCauseAnalyzer + GET /feasibility/root-cause/{mo_id}"; body = "Spec 024 US2 / T015-T017." },
  @{ id = "118"; title = "T118: [024] Exception lifecycle API acknowledge/resolve"; body = "Spec 024 T018-T019." },
  @{ id = "121"; title = "T121: [024] SmartBatcher + CapacityAuction + unit tests"; body = "Spec 024 US3 / T021-T023." },
  @{ id = "130"; title = "T130: [024] AgentOrchestrator dry-run chain + activity logging"; body = "Spec 024 US5 / T030-T031." },
  @{ id = "126"; title = "T126: [024] upload-svc compose/Kong residual"; body = "Spec 024 US4 / T026-T028 - service exists; wire compose residual." },
  @{ id = "133"; title = "T133: [024] Update PRODUCT-STATUS for Ops Phase 3 + Phase 4/5 backlog"; body = "Spec 024 T033-T034." },
  @{ id = "140"; title = "T140: [HUMAN][024] OQ-7 pricing - blocks SOW send"; body = "COM OPEN. Do not auto-close." },
  @{ id = "141"; title = "T141: [HUMAN][024] OQ-1 Odoo 17 vs 19 confirmation"; body = "COM OPEN." },
  @{ id = "142"; title = "T142: [HUMAN][024] PH1-02 live Odoo staging"; body = "COM OPEN." },
  @{ id = "143"; title = "T143: [HUMAN][024] G-R2-04 Arabic native QA then v9.1.1-r2"; body = "Never push stale v9.1.0-r2. COM OPEN." },
  @{ id = "144"; title = "T144: [024] Re-run star-trans-validate when Docker up (issues 70/72)"; body = "Ops residual. Leave OPEN if stack down." },
  @{ id = "150"; title = "T150: [BACKLOG][024] Phase 4 M1-M6 Command modules"; body = "Premium Proposal backlog." },
  @{ id = "151"; title = "T151: [BACKLOG][024] Agents A8-A12"; body = "Phase 4 backlog." },
  @{ id = "153"; title = "T153: [BACKLOG][024] Phase 5 Planning Cockpit / MPS / MRP / ATP"; body = "Planning-Command-Deep backlog." }
)

$created = New-Object System.Collections.Generic.List[object]
foreach ($t in $tasks) {
  if ($have.ContainsKey($t.id)) {
    Write-Output "SKIP T$($t.id) already #$($have[$t.id])"
    $created.Add([pscustomobject]@{ task = "T$($t.id)"; number = $have[$t.id]; status = "exists" })
    continue
  }
  $url = gh issue create --title $t.title --body $t.body 2>&1 | Out-String
  $url = $url.Trim()
  Write-Output "CREATED $url"
  if ($url -match '/issues/(\d+)') {
    $created.Add([pscustomobject]@{ task = "T$($t.id)"; number = $Matches[1]; status = "created"; url = $url })
  }
}

$created | ConvertTo-Json | Set-Content "specs\024-phase3-ops-intelligence\_issues_created.json"
Write-Output "DONE count=$($created.Count)"
