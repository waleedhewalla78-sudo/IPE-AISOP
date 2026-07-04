# Gate 6 — Helm lint and template render (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Chart = Join-Path $Root "helm\ipe"

if (-not (Get-Command helm -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: helm not found. Install Helm 3.14+ and re-run."
    exit 1
}

Write-Host "=== Gate 6: Helm lint + template ==="
helm lint $Chart -f (Join-Path $Chart "values-release1.yaml")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

helm lint $Chart -f (Join-Path $Chart "values-prod.yaml")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

helm lint $Chart -f (Join-Path $Chart "values-dev.yaml")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

helm template ipe $Chart -f (Join-Path $Chart "values-release1.yaml") | Out-Null
helm template ipe $Chart -f (Join-Path $Chart "values-prod.yaml") | Out-Null
helm template ipe $Chart -f (Join-Path $Chart "values-dev.yaml") | Out-Null

Write-Host "GATE 6: PASS"
