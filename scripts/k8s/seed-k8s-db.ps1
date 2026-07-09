# Seed/migrate K8s PostgreSQL for Gate 8 parity (T164)
# Usage: .\scripts\k8s\seed-k8s-db.ps1 [-Namespace ipe]

param(
    [string]$Namespace = "ipe",
    [int]$LocalPort = 15432
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "=== T164: K8s DB migrate + seed (namespace=$Namespace) ===" -ForegroundColor Cyan

$pf = Start-Process kubectl -ArgumentList @(
    "port-forward", "-n", $Namespace, "svc/postgresql", "${LocalPort}:5432"
) -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 4

try {
    $env:DATABASE_URL = "postgresql://ipe:ipe_test_pass@127.0.0.1:${LocalPort}/ipe_test"
    $env:IPE_DATABASE_URL = "postgresql+asyncpg://ipe:ipe_test_pass@127.0.0.1:${LocalPort}/ipe_test"

    Push-Location (Join-Path $Root "migrations")
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv run alembic upgrade head
    } elseif (Get-Command alembic -ErrorAction SilentlyContinue) {
        alembic upgrade head
    } else {
        throw "Install uv or alembic to run migrations"
    }
    Pop-Location

    $seedSh = Join-Path $Root "scripts\seed-data.sh"
    $content = Get-Content $seedSh -Raw
    if ($content -match "(?s)<<'SQL'\r?\n(.*)\r?\nSQL") {
        $sql = "CREATE EXTENSION IF NOT EXISTS pgcrypto;`n" + $Matches[1]
        $sql | kubectl exec -i -n $Namespace deploy/postgresql -- psql -U ipe -d ipe_test -v ON_ERROR_STOP=1
    }

    $demoSql = Join-Path $Root "scripts\seed-demo-client.sql"
    if (Test-Path $demoSql) {
        Get-Content $demoSql -Raw | kubectl exec -i -n $Namespace deploy/postgresql -- psql -U ipe -d ipe_test -v ON_ERROR_STOP=1
    }

    Write-Host "Restarting app deployments..." -ForegroundColor Yellow
    kubectl rollout restart deployment -n $Namespace dpe-svc fea-svc cap-svc mat-svc connector res-svc
    kubectl rollout status deployment -n $Namespace dpe-svc --timeout=180s

    Write-Host "K8s DB migrate + seed complete." -ForegroundColor Green
} finally {
    if ($null -ne $pf -and -not $pf.HasExited) {
        Stop-Process -Id $pf.Id -Force -ErrorAction SilentlyContinue
    }
}
