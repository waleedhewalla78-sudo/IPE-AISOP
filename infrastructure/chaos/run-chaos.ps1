# Chaos Mesh experiment runner for IPE staging (Windows).
# Prerequisites: kubectl configured for staging cluster, Chaos Mesh CRDs installed.
param(
    [string]$Namespace = $(if ($env:CHAOS_NAMESPACE) { $env:CHAOS_NAMESPACE } else { "ipe-platform" })
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== IPE Chaos Mesh Experiments ==="
Write-Host "Namespace: $Namespace"
Write-Host ""

function Apply-Experiment {
    param([string]$Name, [string]$File)
    Write-Host "Applying: $Name..."
    try {
        kubectl apply -f $File -n $Namespace 2>$null | Out-Null
        Write-Host "  OK Applied"
        return $true
    } catch {
        Write-Host "  Skipped (namespace or CRD not found)"
        return $false
    }
}

$experiments = @(
    @("kafka-pod-kill", "$ScriptDir\kafka-pod-kill.yaml"),
    @("postgres-failover", "$ScriptDir\postgres-failover.yaml"),
    @("redis-pod-kill", "$ScriptDir\redis-pod-kill.yaml"),
    @("kafka-network-partition", "$ScriptDir\kafka-network-partition.yaml"),
    @("cpu-pressure", "$ScriptDir\cpu-pressure.yaml")
)

$applied = 0
foreach ($exp in $experiments) {
    if (Apply-Experiment -Name $exp[0] -File $exp[1]) { $applied++ }
    Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "=== Applied $applied / $($experiments.Count) experiments ==="
Write-Host "Monitor: kubectl get pods -n $Namespace"
Write-Host "Evidence: .\infrastructure\chaos\collect-evidence.ps1"
