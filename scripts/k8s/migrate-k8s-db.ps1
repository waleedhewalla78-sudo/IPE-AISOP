# Gate 8 prerequisite - migrate + seed K8s PostgreSQL (T164)
# Usage: .\scripts\k8s\migrate-k8s-db.ps1 [-Seed]

param(
    [switch]$Seed,
    [string]$Namespace = "ipe",
    [int]$LocalPort = 15432
)

$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $Root

Write-Host "=== K8s DB migrate (namespace: $Namespace) ==="

kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgresql -n $Namespace --timeout=120s

$pf = Start-Process -FilePath "kubectl" -ArgumentList @(
    "port-forward", "-n", $Namespace, "svc/postgresql", "${LocalPort}:5432"
) -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 4

try {
    $env:IPE_DATABASE_URL_SYNC = "postgresql://ipe:ipe_test_pass@127.0.0.1:${LocalPort}/ipe_test"
    $env:DATABASE_URL = $env:IPE_DATABASE_URL_SYNC

    Push-Location (Join-Path $Root "migrations")
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv run alembic upgrade head
    }
    elseif (Get-Command alembic -ErrorAction SilentlyContinue) {
        alembic upgrade head
    }
    else {
        throw "Install uv or alembic to run migrations"
    }
    Pop-Location

    if ($Seed) {
        Write-Host "=== Seeding demo tenant data ==="
        if (Get-Command bash -ErrorAction SilentlyContinue) {
            bash scripts/seed-data.sh
        }
        else {
            Write-Warning "bash not found - run scripts/seed-data.sh manually with IPE_DATABASE_URL_SYNC set"
        }
    }

    Write-Host "=== Restarting app deployments ==="
    kubectl rollout restart deployment -n $Namespace dpe-svc fea-svc cap-svc connector res-svc mat-svc
    kubectl rollout status deployment -n $Namespace dpe-svc --timeout=180s

    Write-Host "PASS: K8s DB migrate complete"
}
finally {
    if ($null -ne $pf -and -not $pf.HasExited) {
        Stop-Process -Id $pf.Id -Force -ErrorAction SilentlyContinue
    }
}
