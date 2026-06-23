# Quick health check for local IPE product
# Usage: .\scripts\check-product.ps1

$ErrorActionPreference = "Continue"
$ok = $true

function Test-Url($label, $url) {
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
        Write-Host "[OK] $label - HTTP $($r.StatusCode) - $url" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] $label - $url" -ForegroundColor Red
        Write-Host "       $($_.Exception.Message)" -ForegroundColor DarkRed
        $script:ok = $false
    }
}

Write-Host "=== IPE Product Health Check ===" -ForegroundColor Cyan

Test-Url "Web UI" "http://localhost:8082/login"
Test-Url "API Gateway" "http://localhost:8000/api/v1/health"

try {
    $body = '{"email":"admin@demo.com","password":"demo"}'
    $r = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" -Method POST `
        -ContentType "application/json" -Body $body -TimeoutSec 20
    if ($r.success) {
        Write-Host "[OK] Login API - admin@demo.com" -ForegroundColor Green
        $token = $r.data.access_token
        $h = @{ Authorization = "Bearer $token" }
        $queue = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/feasibility/queue" -Headers $h -TimeoutSec 15
        $qCount = if ($queue.data) { $queue.data.Count } elseif ($queue.items) { $queue.items.Count } else { 0 }
        if ($qCount -ge 10) {
            Write-Host "[OK] Demo data - $qCount MOs in feasibility queue" -ForegroundColor Green
        } else {
            Write-Host "[WARN] Demo data - only $qCount MOs in queue (expected 10). Run .\scripts\seed-demo-client.ps1" -ForegroundColor Yellow
        }
        try {
            $sf = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/shop-floor/items" -Headers $h -TimeoutSec 10
            $sfCount = if ($sf.items) { $sf.items.Count } else { 0 }
            Write-Host "[OK] Shop Floor API - $sfCount active work orders" -ForegroundColor Green
        } catch {
            Write-Host "[WARN] Shop Floor API - recreate Kong: docker compose -f infrastructure\docker up -d --force-recreate kong" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[FAIL] Login API - success=false" -ForegroundColor Red
        $ok = $false
    }
} catch {
    Write-Host "[FAIL] Login API - http://localhost:8000/api/v1/auth/login" -ForegroundColor Red
    Write-Host "       $($_.Exception.Message)" -ForegroundColor DarkRed
    Write-Host "       Try: docker compose build dpe-svc; docker compose up -d dpe-svc kong" -ForegroundColor Yellow
    $ok = $false
}

if ($ok) {
    Write-Host ""
    Write-Host "Product ready: http://localhost:8082/login (admin@demo.com / demo)" -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "Fix: .\scripts\start-product.ps1" -ForegroundColor Yellow
exit 1
