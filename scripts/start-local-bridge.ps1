param(
    [int]$Port = 3050,
    [string]$ConfigPath = (Join-Path $PSScriptRoot '..\runtime\mcp.json')
)

$ErrorActionPreference = 'Stop'
$pkg = '@1mcp/agent@0.34.4'
$config = (Resolve-Path $ConfigPath).Path

Write-Host '=== Local MCP bridge ===' -ForegroundColor Cyan
Write-Host "1MCP   : $pkg"
Write-Host "Config : $config"
Write-Host "MCP    : http://127.0.0.1:$Port/mcp"

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

$health = "http://127.0.0.1:$Port/health/mcp/sequential-thinking"
for ($attempt = 1; $attempt -le 60; $attempt++) {
    try {
        $result = Invoke-RestMethod -Method Get -Uri $health -TimeoutSec 5
        if ([string]$result.state -eq 'ready') {
            Write-Host 'LOCAL_BRIDGE_STATUS=ready' -ForegroundColor Green
            Write-Host "MCP_URL=http://127.0.0.1:$Port/mcp"
            Write-Host 'EXPECTED_TOOL=sequential_thinking'
            exit 0
        }
    }
    catch {}
    Start-Sleep -Seconds 1
}

throw "Local MCP did not become ready: $health"
