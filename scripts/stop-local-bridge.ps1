param(
    [string]$ConfigPath = (Join-Path $PSScriptRoot '..\runtime\mcp.json')
)

$ErrorActionPreference = 'Stop'
$pkg = '@1mcp/agent@0.34.4'
$config = (Resolve-Path $ConfigPath).Path

& npx.cmd -y $pkg serve --config $config --stop
$stopCode = $LASTEXITCODE
if ($stopCode -eq 0) {
    Write-Host 'LOCAL_BRIDGE_STATUS=stopped' -ForegroundColor Green
    exit 0
}
if ($stopCode -in @(3, 7)) {
    Write-Host "LOCAL_BRIDGE_STATUS=stopped (already stopped, exit $stopCode)" -ForegroundColor Green
    exit 0
}
throw "1MCP stop failed with exit code $stopCode."
