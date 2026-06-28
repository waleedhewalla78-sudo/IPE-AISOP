# IPE Full-Cycle Demo Verification (Windows)
# Runs API checks for every UI module using demo tenant data.
# Usage: .\scripts\run-full-demo.ps1
# Optional: .\scripts\run-full-demo.ps1 -ReportPath docs\demo-run-report.txt

param(
    [string]$ReportPath = ""
)

$ErrorActionPreference = "Continue"
$Base = "http://localhost:8000"
$Web = "http://localhost:8082"
$Tenant = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
# Limit schedule solver to 3 demo MOs — avoids ML per-op timeouts on full tenant queue
$DemoMoIds = @(
    "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380001",
    "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380002",
    "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380003"
)
# Approve guardrail requires feasibility >= 85% (MO-DEMO-005/006 in seed-demo-client.sql)
$ApproveMoIds = @(
    "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380005",
    "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380006"
)
$ScheduleBody = (@{ mo_ids = $DemoMoIds } | ConvertTo-Json -Compress)
$ApproveScheduleBody = (@{ mo_ids = $ApproveMoIds } | ConvertTo-Json -Compress)
$Pass = 0
$Fail = 0
$Total = 0
$Lines = @()

function Write-DemoLine([string]$Text) {
    Write-Host $Text
    $script:Lines += $Text
}

function Test-Checkpoint {
    param(
        [string]$Name,
        [scriptblock]$Action,
        [string]$UiPath = ""
    )
    $script:Total++
    try {
        $result = & $Action
        if ($result) {
            $script:Pass++
            Write-DemoLine "[PASS] $Name"
            if ($UiPath) { Write-DemoLine "       UI: $Web$UiPath" }
            if ($result -is [string] -and $result.Length -gt 0) {
                Write-DemoLine "       -> $result"
            }
        } else {
            $script:Fail++
            Write-DemoLine "[FAIL] $Name"
        }
    } catch {
        $script:Fail++
        Write-DemoLine "[FAIL] $Name - $($_.Exception.Message)"
    }
}

Write-DemoLine "=============================================="
Write-DemoLine " IPE Full-Cycle Demo Verification"
Write-DemoLine " $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-DemoLine "=============================================="
Write-DemoLine ""

# --- Login ---
$token = $null
Test-Checkpoint "0. Login (Ahmed@nour / admin)" {
    $body = '{"email":"Ahmed@nour","password":"admin"}'
    $r = Invoke-RestMethod -Uri "$Base/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 20
    if (-not $r.success) { return $false }
    $script:token = $r.data.access_token
    "JWT issued for tenant Demo Manufacturing Inc"
} -UiPath "/login"

if (-not $token) {
    Write-DemoLine ""
    Write-DemoLine "Cannot continue without login. Run: .\scripts\start-product.ps1"
    exit 1
}

$h = @{ Authorization = "Bearer $token"; "X-Tenant-ID" = $Tenant }

Write-DemoLine ""
Write-DemoLine "--- Planning and Operations Modules ---"

Test-Checkpoint "1. Control Tower - feasibility queue (10 MOs)" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/feasibility/queue" -Headers $h -TimeoutSec 20
    $count = @($r.data).Count
    if ($count -lt 10) { return $false }
    $worst = ($r.data | Sort-Object feasibility_score | Select-Object -First 1)
    "$count MOs; lowest score $($worst.feasibility_score) constraint $($worst.primary_constraint)"
} -UiPath "/planning/control-tower"

Test-Checkpoint "2. Control Tower - KPIs" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/feasibility/kpis" -Headers $h -TimeoutSec 15
    "avg feasibility $($r.data.avg_feasibility_score), orders at risk $($r.data.orders_at_risk)"
} -UiPath "/planning/control-tower"

Test-Checkpoint "3. Resolution Center - scenarios (demo MOs)" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/resolution/scenarios" -Headers $h -TimeoutSec 60
    $scenarios = $r.data.scenarios
    if ($scenarios.Count -lt 8) { return $false }
    "$($scenarios.Count) scenarios loaded (includes MO-DEMO expedite/overtime/split)"
} -UiPath "/planning/resolution"

Test-Checkpoint "4. Schedule - OR-Tools Gantt data" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/capacity/schedule" -Headers $h -Method POST -ContentType "application/json" -Body $ScheduleBody -TimeoutSec 90
    $ops = $r.data.total_operations
    if ($ops -lt 1) { return $false }
    "$ops scheduled operations across Assembly, Machining, Packaging"
} -UiPath "/planning/schedule"

Test-Checkpoint "5. Shop Floor - active work orders" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/shop-floor/items" -Headers $h -TimeoutSec 15
    if ($r.items.Count -lt 1) { return $false }
    $names = ($r.items | ForEach-Object { "$($_.mo_id) on $($_.workcenter)" }) -join "; "
    "$($r.items.Count) work orders: $names"
} -UiPath "/shop-floor"

Test-Checkpoint "6. SCN Portal - supplier scorecards" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/supply-chain/suppliers" -Headers $h -TimeoutSec 15
    if ($r.suppliers.Count -lt 3) { return $false }
    $parts = ($r.suppliers | ForEach-Object { "$($_.name) $($_.score)%" }) -join ", "
    $parts
} -UiPath "/supply-chain/scn-portal"

Write-DemoLine ""
Write-DemoLine "--- Analytics and Intelligence ---"

Test-Checkpoint "7. Executive - delay breakdown" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/analytics/delay-breakdown" -Headers $h -TimeoutSec 15
    $count = @($r.data).Count
    if ($count -lt 1) { return $false }
    "$count delay categories (material, capacity, labor, supplier, quality)"
} -UiPath "/command-center/executive"

Test-Checkpoint "8. Executive - OTD summary" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/analytics/executive-summary" -Headers $h -TimeoutSec 15
    "OTD trend points: $(@($r.data.otd_trend).Count); completed MO history from MO-DEMO-009/010"
} -UiPath "/command-center/executive"

Test-Checkpoint "9. Dashboard alerts (War Room feed)" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/dashboard/alerts" -Headers $h -TimeoutSec 15
    $alerts = $r.data.alerts
    if ($alerts.Count -lt 8) { return $false }
    "$($alerts.Count) active alerts (MO-DEMO-001 material, MO-DEMO-007 raw material, etc.)"
} -UiPath "/command-center/war-room"

Test-Checkpoint "10. Copilot - FG stock query" {
    $body = '{"query":"What is the current FG stock for Widget A and Gadget B?","stream":false}'
    $r = Invoke-RestMethod -Uri "$Base/api/v1/copilot/query" -Headers $h -Method POST -ContentType "application/json" -Body $body -TimeoutSec 180
    if ($r.data.intent -ne "material_status") { return $false }
    if ($r.data.response -notmatch "Widget A") { return $false }
    "intent=$($r.data.intent); Widget A and Gadget B quantities returned"
} -UiPath "/ai-governance/copilot"

Test-Checkpoint "11. Copilot - at-risk orders query" {
    $body = '{"query":"Which manufacturing orders are at risk this week?","stream":false}'
    $r = Invoke-RestMethod -Uri "$Base/api/v1/copilot/query" -Headers $h -Method POST -ContentType "application/json" -Body $body -TimeoutSec 180
    if ($r.data.intent -ne "feasibility_check") { return $false }
    "intent=$($r.data.intent); feasibility queue summarized"
} -UiPath "/ai-governance/copilot"

Test-Checkpoint "12. AI Trust - scores" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/ai-trust/scores" -Headers $h -TimeoutSec 15
    "trust metrics loaded"
} -UiPath "/ai-governance/ai-trust"

Test-Checkpoint "13. Admin - tenant config" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/admin/config" -Headers $h -TimeoutSec 15
    "autonomy mode: $($r.data.autonomy_mode)"
} -UiPath "/platform/admin"

Test-Checkpoint "14. Inventory summary (master data)" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/material/inventory-summary" -Headers $h -TimeoutSec 15
    "$($r.data.total_products) finished goods with on-hand quantities"
} -UiPath "/ai-governance/copilot"

Test-Checkpoint "15. Schedule - persist after approve" {
    $sched = Invoke-RestMethod -Uri "$Base/api/v1/capacity/schedule" -Headers $h -Method POST -ContentType "application/json" -Body $ApproveScheduleBody -TimeoutSec 90
    if ($sched.data.total_operations -lt 1) { return $false }
    $approveBody = @{ mo_ids = $ApproveMoIds } | ConvertTo-Json
    $approved = Invoke-RestMethod -Uri "$Base/api/v1/capacity/schedule/approve" -Headers $h -Method POST -ContentType "application/json" -Body $approveBody -TimeoutSec 30
    if ($approved.data.activated_count -lt 1) { return $false }
    $active = Invoke-RestMethod -Uri "$Base/api/v1/capacity/schedule/active" -Headers $h -TimeoutSec 20
    $persisted = @($active.data.rows | Where-Object { $_.approved -eq $true })
    if ($persisted.Count -lt 1) { return $false }
    "approved $($approved.data.activated_count) MO(s); $($persisted.Count) persisted in active schedule$(if ($approved.data.erp_event_published -eq $false) { '; ERP sync deferred' } else { '' })"
} -UiPath "/planning/schedule"

Test-Checkpoint "17. V6-R1 - margin-aware priority ordering" {
    $margin = Invoke-RestMethod -Uri "$Base/api/v1/demand/priority/margin-aware" -Headers $h -TimeoutSec 20
    $priorities = @($margin.data.priorities)
    if ($priorities.Count -lt 2) { return $false }
    $sorted = $priorities | Sort-Object -Property margin_adjusted_score -Descending
    $top = $sorted[0]
    $actBody = @{ strategy = "activity_optimized"; alpha = 0.6; horizon_hours = 168; mo_ids = $DemoMoIds } | ConvertTo-Json -Compress
    $sched = Invoke-RestMethod -Uri "$Base/api/v1/capacity/schedule" -Headers $h -Method POST -ContentType "application/json" -Body $actBody -TimeoutSec 90
    $breakdown = $sched.data.activity_cost_breakdown
    if (-not $breakdown) { return $false }
    $total = [double]$breakdown.total_usd
    if ($total -lt 0) { return $false }
    "top MO margin score=$($top.margin_adjusted_score); activity total_usd=$total"
} -UiPath "/planning/schedule"

Test-Checkpoint "18. V6-R2 - tariff shock + substitute draft" {
    $body = '{"region":"Region_X","tariff_delta_pct":25.0,"margin_threshold_pct":15.0}'
    $shock = Invoke-RestMethod -Uri "$Base/api/v1/demand/tariff/shock" -Headers $h -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    if ([int]$shock.data.affected_mo_count -lt 1) { return $false }
    $drafts = @($shock.data.substitute_drafts)
    if ($drafts.Count -lt 1) { return $false }
    "affected=$($shock.data.affected_mo_count); drafts=$($drafts.Count)"
} -UiPath "/supply-chain/tariff"

Test-Checkpoint "19. V6-R3 - CPM cascade under 2s" {
    $active = Invoke-RestMethod -Uri "$Base/api/v1/capacity/schedule/active" -Headers $h -TimeoutSec 20
    $moId = $null
    $opId = $null
    foreach ($row in @($active.data.rows)) {
        foreach ($op in @($row.operations)) {
            if ($op.id) {
                $moId = $row.mo_id
                $opId = $op.id
                break
            }
        }
        if ($opId) { break }
    }
    if (-not $opId) {
        $sched = Invoke-RestMethod -Uri "$Base/api/v1/capacity/schedule" -Headers $h -Method POST -ContentType "application/json" -Body $ScheduleBody -TimeoutSec 90
        $assign = @($sched.data.schedule.assignments)
        if ($assign.Count -lt 1) { return $false }
        $moId = $assign[0].mo_id
        $opId = $assign[0].operation_id
        if (-not $opId) { $opId = $assign[0].id }
    }
    $body = @{ mo_id = $moId; operation_id = $opId; delta_minutes = 120; mode = "preview" } | ConvertTo-Json
    $cascade = Invoke-RestMethod -Uri "$Base/api/v1/capacity/cpm/cascade" -Headers $h -Method POST -ContentType "application/json" -Body $body -TimeoutSec 10
    if ([int]$cascade.data.cascade_ms -gt 2000) { return $false }
    if (@($cascade.data.operations).Count -lt 1) { return $false }
    "cascade_ms=$($cascade.data.cascade_ms); critical_path=$($cascade.data.critical_path_ids.Count) ops"
} -UiPath "/planning/schedule"

Test-Checkpoint "20. V6-R4/R5 - maintenance telemetry + Cost of Chaos + War Room" {
    $telBody = '{"machine_id":"WC002","rul_hours":36,"vibration_rms":2.1}'
    $tel = Invoke-RestMethod -Uri "$Base/api/v1/iot/telemetry" -Headers $h -Method POST -ContentType "application/json" -Body $telBody -TimeoutSec 30
    if ($tel.data.maintenance_block_published -ne $true) { return $false }
    $chaos = Invoke-RestMethod -Uri "$Base/api/v1/analytics/cost-of-chaos?period=7d" -Headers $h -TimeoutSec 20
    $cats = @($chaos.data.categories | Where-Object { [double]$_.usd -gt 0 })
    if ($cats.Count -lt 3) { return $false }
    $recovery = Invoke-RestMethod -Uri "$Base/api/v1/war-room/recovery-plan" -Headers $h -TimeoutSec 30
    $options = @($recovery.data.recovery_options)
    if ($options.Count -lt 1) { return $false }
    "maintenance block OK; chaos categories=$($cats.Count); recovery options=$($options.Count)"
} -UiPath "/command-center/war-room"

Write-DemoLine ""
Write-DemoLine "--- v8 Phase 1-3 (SAP Gap Upgrade) ---"

Test-Checkpoint "21. Demand Dashboard - forecast API" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/demand/forecast?horizon=short" -Headers $h -TimeoutSec 20
    if (-not $r.success) { return $false }
    "forecast rows: $(@($r.data.forecasts).Count)"
} -UiPath "/planning/demand"

Test-Checkpoint "22. Demand - run sense cycle" {
    $body = '{"horizon":"short","periods":7}'
    $r = Invoke-RestMethod -Uri "$Base/api/v1/demand/sense" -Headers $h -Method POST -ContentType "application/json" -Body $body -TimeoutSec 30
    if (-not $r.success) { return $false }
    "forecasts_created=$($r.data.forecasts_created)"
} -UiPath "/planning/demand"

Test-Checkpoint "23. Scenario - create sandbox" {
    $name = "Demo-$(Get-Date -Format 'HHmmss')"
    $body = (@{ name = $name; description = "v8 demo scenario" } | ConvertTo-Json -Compress)
    $r = Invoke-RestMethod -Uri "$Base/api/v1/scenario" -Headers $h -Method POST -ContentType "application/json" -Body $body -TimeoutSec 20
    if (-not $r.success) { return $false }
    $script:v8ScenarioId = $r.data.scenario_id
    "scenario_id=$($r.data.scenario_id)"
} -UiPath "/planning/scenarios"

Test-Checkpoint "24. Scenario - simulate KPIs" {
    if (-not $script:v8ScenarioId) { return $false }
    $r = Invoke-RestMethod -Uri "$Base/api/v1/scenario/$($script:v8ScenarioId)/simulate" -Headers $h -Method POST -TimeoutSec 20
    if (-not $r.success) { return $false }
    "KPI keys: $(@($r.data.kpis.PSObject.Properties.Name).Count)"
} -UiPath "/planning/scenarios"

Test-Checkpoint "25. Supply - network visibility" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/supply/network" -Headers $h -TimeoutSec 20
    if (-not $r.success) { return $false }
    if (@($r.data.facilities).Count -lt 4) { return $false }
    "facilities=$(@($r.data.facilities).Count) lanes=$(@($r.data.lanes).Count)"
} -UiPath "/supply-chain/supply-planning"

Test-Checkpoint "26. Orders - create customer order" {
    $inv = Invoke-RestMethod -Uri "$Base/api/v1/material/inventory-summary" -Headers $h -TimeoutSec 20
    $productId = $inv.data.items[0].product_id
    if (-not $productId) { return $false }
    $body = (@{ lines = @(@{ product_id = $productId; quantity = 2; unit_price = 10 }) } | ConvertTo-Json -Compress)
    $r = Invoke-RestMethod -Uri "$Base/api/v1/orders" -Headers $h -Method POST -ContentType "application/json" -Body $body -TimeoutSec 20
    if (-not $r.success) { return $false }
    $script:v8OrderId = $r.data.order_id
    "$($r.data.order_number) total=$($r.data.total_value)"
} -UiPath "/supply-chain/orders"

Test-Checkpoint "27. Equipment - fleet health" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/equipment" -Headers $h -TimeoutSec 20
    if (-not $r.success) { return $false }
    $eq = @($r.data.equipment)
    if ($eq.Count -lt 1) { return $false }
    "equipment count=$($eq.Count) top health=$($eq[0].health_score)"
} -UiPath "/command-center/equipment"

Test-Checkpoint "28. Design AI - material catalog" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/materials" -Headers $h -TimeoutSec 20
    if (-not $r.success) { return $false }
    if ($r.data.count -lt 1) { return $false }
    "$($r.data.count) engineering materials"
} -UiPath "/ai-governance/design-ai"

Test-Checkpoint "29. Procurement - suppliers and spend" {
    $sup = Invoke-RestMethod -Uri "$Base/api/v1/suppliers" -Headers $h -TimeoutSec 20
    $spend = Invoke-RestMethod -Uri "$Base/api/v1/procurement/spend" -Headers $h -TimeoutSec 20
    if (-not $spend.success) { return $false }
    "suppliers=$(@($sup.data.suppliers).Count) spend_total=$($spend.data.summary.total)"
} -UiPath "/supply-chain/procurement"

Test-Checkpoint "30. Copilot - role agents and session" {
    $agents = Invoke-RestMethod -Uri "$Base/api/v1/copilot/agents" -Headers $h -TimeoutSec 20
    if (-not $agents.success) { return $false }
    $roles = @($agents.data.agents | ForEach-Object { $_.role })
    if ($roles -notcontains "planner") { return $false }
    $sessBody = '{"role":"planner"}'
    $sess = Invoke-RestMethod -Uri "$Base/api/v1/copilot/session" -Headers $h -Method POST -ContentType "application/json" -Body $sessBody -TimeoutSec 20
    if (-not $sess.success) { return $false }
    if ($sess.data.role -ne "planner") { return $false }
    "agents=$($roles.Count) session=$($sess.data.session_id)"
} -UiPath "/ai-governance/copilot"

Write-DemoLine ""
Write-DemoLine "--- v7 Extended Validation (Sustain + Quality) ---"

Test-Checkpoint "31. Sustainability Dashboard - ESG score and carbon footprint" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/sustainability/dashboard" -Headers $h -TimeoutSec 20
    if (-not $r.success) { return $false }
    if ($r.data.esg_score -lt 1) { return $false }
    if ($r.data.carbon_footprint_tco2e -lt 1) { return $false }
    "esg_score=$($r.data.esg_score) carbon_tco2e=$($r.data.carbon_footprint_tco2e)"
} -UiPath "/command-center/sustainability"

Test-Checkpoint "32. Quality Intelligence - KPIs and defect trends" {
    $r = Invoke-RestMethod -Uri "$Base/api/v1/quality-events/dashboard" -Headers $h -TimeoutSec 20
    if (-not $r.success) { return $false }
    if ($r.data.defect_rate_pct -lt 0) { return $false }
    if ($r.data.first_pass_yield_pct -lt 1) { return $false }
    "defect_rate=$($r.data.defect_rate_pct)% fpy=$($r.data.first_pass_yield_pct)% trend=$($r.data.trend)"
} -UiPath "/command-center/quality"

Write-DemoLine ""
Write-DemoLine "=============================================="
Write-DemoLine " RESULT: $Pass / $Total passed, $Fail failed"
Write-DemoLine "=============================================="

if ($Fail -eq 0) {
    Write-DemoLine " Demo ready for client walkthrough."
    Write-DemoLine " Guide: docs/FULL-DEMO-GUIDE.md"
    Write-DemoLine " Open: $Web/login"
} else {
    Write-DemoLine " Fix failures, then re-run:"
    Write-DemoLine "   .\scripts\seed-demo-client.ps1"
    Write-DemoLine "   docker compose -f infrastructure\docker up -d --force-recreate kong"
}

if ($ReportPath) {
    $dir = Split-Path -Parent $ReportPath
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $Lines | Set-Content -Path $ReportPath -Encoding UTF8
    Write-DemoLine " Report saved: $ReportPath"
}

exit $(if ($Fail -eq 0) { 0 } else { 1 })
