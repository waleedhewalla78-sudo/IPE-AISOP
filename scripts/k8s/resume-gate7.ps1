# Resume Gate 7 after kind cluster exists (skip cluster create)
param([string]$ClusterName = "ipe-dev")

$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Chart = Join-Path $Root "helm\ipe"
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + `
    [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "Building and loading images ..."
& (Join-Path $PSScriptRoot "build-kind-images.ps1") -ClusterName $ClusterName
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Helm install ..."
helm upgrade --install ipe $Chart -n ipe --create-namespace -f (Join-Path $Chart "values-dev.yaml") --wait --timeout 15m
if ($LASTEXITCODE -ne 0) {
    kubectl get pods -n ipe
    exit 1
}

kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgresql -n ipe --timeout=180s

$migrateDir = Join-Path $Root "migrations"
if (Test-Path $migrateDir) {
    Write-Host "Running migrations ..."
    $pf = Start-Process kubectl -ArgumentList @("port-forward","-n","ipe","svc/postgresql","15432:5432") -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 4
    Push-Location $migrateDir
    $env:DATABASE_URL = "postgresql://ipe:ipe_test_pass@127.0.0.1:15432/ipe_test"
    if (Get-Command uv -ErrorAction SilentlyContinue) { uv run alembic upgrade head }
    elseif (Get-Command alembic -ErrorAction SilentlyContinue) { alembic upgrade head }
    Pop-Location
    if ($pf -and -not $pf.HasExited) { Stop-Process -Id $pf.Id -Force -ErrorAction SilentlyContinue }
}

kubectl rollout restart deployment -n ipe dpe-svc fea-svc cap-svc mat-svc connector res-svc
kubectl rollout status deployment -n ipe dpe-svc --timeout=300s

& (Join-Path $PSScriptRoot "verify-k8s.ps1")
