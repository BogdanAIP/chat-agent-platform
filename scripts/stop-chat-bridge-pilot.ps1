param(
    [int]$FunnelPort = 8443
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$configPath = Join-Path $repoRoot 'runtime/bridge-pilot/mcp.json'
$oneMcpPackage = '@1mcp/agent@0.34.4'

$npx = Get-Command npx.cmd -ErrorAction SilentlyContinue
if (-not $npx) {
    $npx = Get-Command npx -ErrorAction SilentlyContinue
}
if (-not $npx) {
    throw 'npx is not available on PATH.'
}

$tailscale = Get-Command tailscale.exe -ErrorAction SilentlyContinue
if (-not $tailscale) {
    $tailscale = Get-Command tailscale -ErrorAction SilentlyContinue
}
if (-not $tailscale) {
    throw 'Tailscale CLI is not available on PATH.'
}

Write-Host "Disabling only Tailscale Funnel HTTPS :$FunnelPort ..."
& $tailscale.Source funnel --https=$FunnelPort off
if ($LASTEXITCODE -ne 0) {
    throw "Failed to disable Funnel HTTPS :$FunnelPort."
}

if (Test-Path -LiteralPath $configPath -PathType Leaf) {
    Write-Host 'Stopping only the 1MCP runtime selected by the bridge-pilot config...'
    & $npx.Source -y $oneMcpPackage serve --config $configPath --stop
    if ($LASTEXITCODE -notin @(0, 3)) {
        throw "1MCP stop returned unexpected exit code $LASTEXITCODE."
    }
}

Write-Host 'BRIDGE_PILOT_STATUS=stopped'
Write-Host 'The existing Funnel on HTTPS 443 was not modified.'
