# Collect Chaos Mesh recovery evidence for R4 release gate (Windows).
param(
    [string]$Namespace = $(if ($env:CHAOS_NAMESPACE) { $env:CHAOS_NAMESPACE } else { "ipe-platform" }),
    [string]$OutDir = "specs/003-autonomous-planning-v5/evidence/r4"
)

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$evidenceDir = Join-Path $repoRoot $OutDir
New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null
$report = Join-Path $evidenceDir "chaos-recovery-metrics.txt"

$lines = @(
    "IPE Chaos Recovery Evidence",
    "Generated: $((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))",
    "Namespace: $Namespace",
    "",
    "=== Pod status ==="
)

try {
    $lines += kubectl get pods -n $Namespace -o wide 2>$null
} catch {
    $lines += "(kubectl unavailable)"
}

$lines += "", "=== Recent chaos events ==="
try {
    $lines += kubectl get events -n $Namespace --sort-by=.lastTimestamp 2>$null | Select-Object -Last 40
} catch {
    $lines += "(events unavailable)"
}

$lines | Set-Content -Path $report -Encoding UTF8
Write-Host "Evidence written: $report"
