param(
    [string]$ConfigPath = (Join-Path $PSScriptRoot '..\runtime\mcp.json')
)

$ErrorActionPreference = 'Stop'
$pkg = '@1mcp/agent@0.34.4'
$config = (Resolve-Path $ConfigPath).Path

& npx.cmd -y $pkg serve --config $config --stop
if ($LASTEXITCODE -eq 0) {
    Write-Host 'LOCAL_BRIDGE_STATUS=stopped' -ForegroundColor Green
    exit 0
}
if ($LASTEXITCODE -eq 3) {
    Write-Host 'LOCAL_BRIDGE_STATUS=stopped (already stopped)' -ForegroundColor Green
    exit 0
}
throw "1MCP stop failed with exit code $LASTEXITCODE."
