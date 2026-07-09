# Shared HTTP helpers for R1/R2 demo scripts (HTTP + HTTPS with dev TLS).

function Enable-DemoTlsBypass {
    param([string]$BaseUrl)
    if ($BaseUrl -notmatch '^https://') { return }
    if ($PSVersionTable.PSVersion.Major -ge 7) { return }
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
}

function Invoke-IpeDemoRequestCurl {
    param(
        [string]$Method = "GET",
        [string]$Uri,
        [hashtable]$Headers = @{},
        [string]$Body = $null,
        [int]$TimeoutSec = 30
    )
    $curlArgs = @("-sk", "--max-time", "$TimeoutSec", "-X", $Method)
    foreach ($key in $Headers.Keys) { $curlArgs += @("-H", "$key`: $($Headers[$key])") }
    $tmpBody = $null
    if ($Body) {
        $tmpBody = [System.IO.Path]::GetTempFileName()
        [System.IO.File]::WriteAllText($tmpBody, $Body)
        $curlArgs += @("-H", "Content-Type: application/json", "--data-binary", "@$tmpBody")
    }
    $curlArgs += $Uri
    try {
        $raw = & curl.exe @curlArgs 2>$null
    } finally {
        if ($tmpBody -and (Test-Path $tmpBody)) { Remove-Item $tmpBody -Force }
    }
    if (-not $raw) { throw "curl returned empty response for $Uri" }
    return ($raw | ConvertFrom-Json)
}

function Invoke-IpeDemoRequest {
    param(
        [string]$Method = "GET",
        [string]$Uri,
        [hashtable]$Headers = @{},
        [string]$Body = $null,
        [int]$TimeoutSec = 30,
        [int]$MaxRetries = 3,
        [string]$BaseUrl = ""
    )
    if ($Uri -match '^https://' -and $PSVersionTable.PSVersion.Major -lt 7) {
        return Invoke-IpeDemoRequestCurl -Method $Method -Uri $Uri -Headers $Headers -Body $Body -TimeoutSec $TimeoutSec
    }
    $skipCert = $Uri -match '^https://' -and $PSVersionTable.PSVersion.Major -ge 7
    $attempt = 0
    while ($true) {
        $attempt++
        try {
            $params = @{
                Method      = $Method
                Uri         = $Uri
                Headers     = $Headers
                TimeoutSec  = $TimeoutSec
                ErrorAction = "Stop"
            }
            if ($Body) { $params.ContentType = "application/json"; $params.Body = $Body }
            if ($skipCert) { $params.SkipCertificateCheck = $true }
            return Invoke-RestMethod @params
        } catch {
            $status = $null
            $respBody = $null
            if ($_.Exception.Response) {
                $status = [int]$_.Exception.Response.StatusCode
                try {
                    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                    $respBody = $reader.ReadToEnd()
                    $reader.Close()
                } catch { $respBody = $_.Exception.Message }
            } else {
                $respBody = $_.Exception.Message
            }
            if ($status -in 500, 502, 504 -and $attempt -lt $MaxRetries) {
                Start-Sleep -Seconds 5
                continue
            }
            throw [System.Exception]::new("HTTP $status : $respBody", $_.Exception)
        }
    }
}

function Get-IpeAuthMode {
    param(
        [string]$BaseUrl,
        [int]$TimeoutSec = 10
    )
    try {
        $info = Invoke-IpeDemoRequest -Uri "$BaseUrl/api/v1/auth/info" -TimeoutSec $TimeoutSec -BaseUrl $BaseUrl
        if ($info.data.mode) { return $info.data.mode }
    } catch {
        # Fall back to workstation env when target stack auth/info is unreachable.
    }
    $ipeRoot = Split-Path $PSScriptRoot -Parent
    $envPath = Join-Path $ipeRoot "infrastructure\docker\ipe-common.env"
    if ((Test-Path $envPath) -and ((Get-Content $envPath -Raw) -match 'AUTH_MODE=keycloak')) {
        return "keycloak"
    }
    return "local"
}

function Get-IpeDemoJwt {
    param(
        [string]$BaseUrl,
        [string]$Email = "Ahmed@nour",
        [string]$Password = "admin",
        [string]$KeycloakUrl = "http://localhost:8180",
        [string]$AuthMode = "",
        [int]$TimeoutSec = 30
    )

    $authMode = if ($AuthMode) { $AuthMode } else { Get-IpeAuthMode -BaseUrl $BaseUrl -TimeoutSec $TimeoutSec }

    if ($authMode -eq "keycloak") {
        $realm = Invoke-RestMethod -Uri "$KeycloakUrl/realms/ipe/.well-known/openid-configuration" -TimeoutSec $TimeoutSec
        $tokenBody = 'grant_type=password&client_id=ipe-web&username=admin@ipe.example.com&password=' + $Password
        $tokenResp = Invoke-RestMethod -Method POST -Uri $realm.token_endpoint `
            -ContentType "application/x-www-form-urlencoded" -Body $tokenBody -TimeoutSec $TimeoutSec
        if (-not $tokenResp.access_token) { throw "Keycloak password grant returned no access_token" }
        return $tokenResp.access_token
    }

    $loginBody = (@{ email = $Email; password = $Password } | ConvertTo-Json -Compress)
    $login = Invoke-IpeDemoRequest -Method POST -Uri "$BaseUrl/api/v1/auth/login" `
        -Body $loginBody -TimeoutSec $TimeoutSec -BaseUrl $BaseUrl
    if (-not $login.data.access_token) { throw "Local login returned no access_token" }
    return $login.data.access_token
}

# Backward-compatible alias (Invoke-DemoRequest omitted — conflicts with wrapper functions in demo scripts)
Set-Alias -Name Get-DemoJwt -Value Get-IpeDemoJwt -Scope Script -Force
