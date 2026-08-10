param(
    [int]$Port = 3050,
    [string]$ConfigPath = (Join-Path $PSScriptRoot '..\runtime\mcp.json'),
    [string]$HealthServerName = 'sequential-thinking',
    [ValidateRange(10, 600)]
    [int]$ReadyTimeoutSeconds = 120
)

$ErrorActionPreference = 'Stop'
$pkg = '@1mcp/agent@0.34.4'
$config = (Resolve-Path $ConfigPath).Path

if ([string]::IsNullOrWhiteSpace($HealthServerName) -or $HealthServerName -notmatch '^[A-Za-z0-9._-]+$') {
    throw 'HealthServerName must be a non-empty MCP server name.'
}

Write-Host '=== Local MCP bridge ===' -ForegroundColor Cyan
Write-Host "1MCP   : $pkg"
Write-Host "Config : $config"
Write-Host "MCP    : http://127.0.0.1:$Port/mcp"
Write-Host "Health : $HealthServerName"

& npx.cmd -y $pkg serve --config $config --status *> $null
$statusCode = $LASTEXITCODE
if ($statusCode -eq 0) {
    Write-Host '1MCP is already running.' -ForegroundColor Yellow
}
elseif ($statusCode -in @(3,7)) {
    & npx.cmd -y $pkg serve `
        --config $config `
        --host 127.0.0.1 `
        --port $Port `
        --health-info-level minimal `
        --enable-async-loading `
        --background
    if ($LASTEXITCODE -ne 0) { throw '1MCP failed to start.' }
}
elseif ($statusCode -in @(4,5)) {
    Write-Host '1MCP is starting; waiting for readiness.' -ForegroundColor Yellow
}
else {
    throw "1MCP supervisor is unhealthy (status exit code $statusCode)."
}

$health = "http://127.0.0.1:$Port/health/mcp/$HealthServerName"
for ($attempt = 1; $attempt -le $ReadyTimeoutSeconds; $attempt++) {
    try {
        $result = Invoke-RestMethod -Method Get -Uri $health -TimeoutSec 5
        if ([string]$result.state -eq 'ready') {
            Write-Host 'LOCAL_BRIDGE_STATUS=ready' -ForegroundColor Green
            Write-Host "MCP_URL=http://127.0.0.1:$Port/mcp"
            Write-Host "HEALTH_SERVER=$HealthServerName"
            exit 0
        }
    }
    catch {}
    Start-Sleep -Seconds 1
}

throw "Local MCP server '$HealthServerName' did not become ready within $ReadyTimeoutSeconds seconds: $health"
