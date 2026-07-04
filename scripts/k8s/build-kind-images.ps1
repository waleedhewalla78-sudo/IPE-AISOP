# Build Release 1 service images and load into kind cluster
param(
    [string]$ClusterName = "ipe-dev",
    [string]$Tag = "dev",
    [string]$Registry = "ipe"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

$Services = @(
    "dpe-svc",
    "fea-svc",
    "cap-svc",
    "mat-svc",
    "connector",
    "res-svc"
)

foreach ($svc in $Services) {
    $image = "${Registry}/${svc}:${Tag}"
    $dockerfile = Join-Path $Root "services\$svc\Dockerfile"
    if (-not (Test-Path $dockerfile)) {
        Write-Warning "Skip $svc - Dockerfile not found"
        continue
    }
    Write-Host "Building $image ..."
    docker build -t $image -f $dockerfile $Root
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Loading $image into kind cluster $ClusterName ..."
    kind load docker-image $image --name $ClusterName
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "All images built and loaded."
