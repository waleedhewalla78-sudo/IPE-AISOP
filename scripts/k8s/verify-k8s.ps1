# K8s verification (Windows) — Gate 7 helper
param([string]$Namespace = "ipe")

$ErrorActionPreference = "Continue"
Write-Host "=== IPE K8s Verification ==="

Write-Host "`n1. Pod Status"
kubectl get pods -n $Namespace -o wide

Write-Host "`n2. Services"
kubectl get svc -n $Namespace

Write-Host "`n3. Ingress"
kubectl get ingress -n $Namespace

$healthy = 0
$total = 0
foreach ($svc in @("dpe-svc", "fea-svc", "cap-svc", "mat-svc", "connector", "res-svc")) {
    $total++
    $pod = kubectl get pod -n $Namespace -l "app.kubernetes.io/name=$svc" `
        -o jsonpath='{.items[0].metadata.name}' 2>$null
    if ($pod) {
        $code = kubectl exec -n $Namespace $pod -- python -c `
            "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8001/api/v1/health', timeout=5).status)" `
            2>$null
        if (-not $code) {
            # try service-specific port from deployment
            $port = kubectl get deploy -n $Namespace $svc -o jsonpath='{.spec.template.spec.containers[0].ports[0].containerPort}' 2>$null
            if ($port) {
                $code = kubectl exec -n $Namespace $pod -- python -c `
                    "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:${port}/api/v1/health', timeout=5).status)" `
                    2>$null
            }
        }
        if ($code -eq "200") { $healthy++ }
        Write-Host "  $svc ($pod): $code"
    } else {
        Write-Host "  ${svc}: no pod"
    }
}

Write-Host "`nHealth summary: $healthy/$total pods returning 200"
if ($healthy -eq $total -and $total -gt 0) {
    Write-Host "GATE 7: PASS"
    exit 0
}
Write-Host "GATE 7: INCOMPLETE ($healthy/$total healthy)"
exit 1
