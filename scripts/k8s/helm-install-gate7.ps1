# Helm install only (images already in kind) - fixes namespace ownership
$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Chart = Join-Path $Root "helm\ipe"
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + `
    [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "Removing orphan ipe namespace (if any) ..."
kubectl delete namespace ipe --ignore-not-found --wait=true

Write-Host "Helm install with --create-namespace ..."
helm upgrade --install ipe $Chart -n ipe --create-namespace -f (Join-Path $Chart "values-dev.yaml") --wait --timeout 20m
if ($LASTEXITCODE -ne 0) {
    kubectl get pods -n ipe
    kubectl describe pods -n ipe | Select-Object -Last 100
    exit 1
}

kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgresql -n ipe --timeout=180s

$migrateDir = Join-Path $Root "migrations"
if (Test-Path $migrateDir) {
    $pf = Start-Process kubectl -ArgumentList @("port-forward","-n","ipe","svc/postgresql","15432:5432") -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 4
    Push-Location $migrateDir
    $env:DATABASE_URL = "postgresql://ipe:ipe_test_pass@127.0.0.1:15432/ipe_test"
    if (Get-Command uv -ErrorAction SilentlyContinue) { uv run alembic upgrade head }
    Pop-Location
    if ($pf -and -not $pf.HasExited) { Stop-Process -Id $pf.Id -Force -ErrorAction SilentlyContinue }
}

kubectl rollout restart deployment -n ipe dpe-svc fea-svc cap-svc mat-svc connector res-svc 2>$null
Start-Sleep -Seconds 30
kubectl get pods -n ipe
& (Join-Path $PSScriptRoot "verify-k8s.ps1")
