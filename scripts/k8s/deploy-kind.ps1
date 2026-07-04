# Deploy IPE to local kind cluster (Gate 7)
param(
    [string]$ClusterName = "ipe-dev"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$Chart = Join-Path $Root "helm\ipe"

function Ensure-Tool($name, $wingetId) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Host "Installing $name via winget..."
        winget install $wingetId --accept-package-agreements --accept-source-agreements
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + `
            [System.Environment]::GetEnvironmentVariable("Path", "User")
    }
}

Ensure-Tool "helm" "Helm.Helm"
Ensure-Tool "kind" "Kubernetes.kind"
Ensure-Tool "kubectl" "Kubernetes.kubectl"
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + `
    [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "=== Gate 6 (pre-check) ==="
& (Join-Path $PSScriptRoot "verify-gate6.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$clusterList = kind get clusters 2>&1 | Where-Object { $_ -is [string] -and $_ -notmatch "No kind clusters" }
$ErrorActionPreference = $prevEap
$clusters = @()
if ($clusterList) {
    $clusters = @($clusterList | Where-Object { $_ -and $_.ToString().Trim() -ne "" })
}
if ($clusters -notcontains $ClusterName) {
    Write-Host "Creating kind cluster $ClusterName ..."
    $kindConfig = @"
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
        protocol: TCP
      - containerPort: 443
        hostPort: 443
        protocol: TCP
"@
    $kindConfig | kind create cluster --name $ClusterName --config=-
}

Write-Host "Installing ingress-nginx ..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod `
    --selector=app.kubernetes.io/component=controller --timeout=180s

Write-Host "Building and loading images ..."
& (Join-Path $PSScriptRoot "build-kind-images.ps1") -ClusterName $ClusterName
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Helm install ..."
helm upgrade --install ipe $Chart -n ipe --create-namespace -f (Join-Path $Chart "values-dev.yaml") --wait --timeout 10m
if ($LASTEXITCODE -ne 0) {
    Write-Host "Helm install failed - dumping pod status"
    kubectl get pods -n ipe
    exit 1
}

Write-Host "Waiting for PostgreSQL ..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgresql -n ipe --timeout=120s

$migrateDir = Join-Path $Root "migrations"
if (Test-Path $migrateDir) {
    Write-Host "Running database migrations via port-forward ..."
    $pf = Start-Process -FilePath "kubectl" -ArgumentList @(
        "port-forward", "-n", "ipe", "svc/postgresql", "15432:5432"
    ) -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 4
    Push-Location $migrateDir
    $env:DATABASE_URL = "postgresql://ipe:ipe_test_pass@127.0.0.1:15432/ipe_test"
    if (Get-Command alembic -ErrorAction SilentlyContinue) {
        alembic upgrade head
    }
    elseif (Get-Command uv -ErrorAction SilentlyContinue) {
        uv run alembic upgrade head
    }
    else {
        Write-Warning "alembic not found - run make migrate manually"
    }
    Pop-Location
    if ($null -ne $pf -and -not $pf.HasExited) {
        Stop-Process -Id $pf.Id -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Restarting app pods after migration ..."
kubectl rollout restart deployment -n ipe dpe-svc fea-svc cap-svc mat-svc connector res-svc
kubectl rollout status deployment -n ipe dpe-svc --timeout=180s

Write-Host "=== Gate 7 verification ==="
kubectl get pods -n ipe
& (Join-Path $PSScriptRoot "verify-k8s.ps1")
