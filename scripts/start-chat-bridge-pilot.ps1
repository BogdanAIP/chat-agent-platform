param(
    [string]$PublicOrigin = 'https://id182019.tailc0abda.ts.net:8443',
    [int]$LocalPort = 3050,
    [int]$FunnelPort = 8443
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$configPath = Join-Path $repoRoot 'runtime/bridge-pilot/mcp.json'
$oneMcpPackage = '@1mcp/agent@0.34.4'

if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "Bridge pilot config is missing: $configPath"
}

$npx = Get-Command npx.cmd -ErrorAction SilentlyContinue
if (-not $npx) {
    $npx = Get-Command npx -ErrorAction SilentlyContinue
}
if (-not $npx) {
    throw 'npx is not available on PATH. Install/repair Node.js before starting the bridge pilot.'
}

$tailscale = Get-Command tailscale.exe -ErrorAction SilentlyContinue
if (-not $tailscale) {
    $tailscale = Get-Command tailscale -ErrorAction SilentlyContinue
}
if (-not $tailscale) {
    throw 'Tailscale CLI is not available on PATH.'
}

Write-Host '=== Chat-to-Local Bridge pilot ==='
Write-Host "Repository : $repoRoot"
Write-Host "1MCP       : $oneMcpPackage"
Write-Host "Config     : $configPath"
Write-Host "Local MCP  : http://127.0.0.1:$LocalPort/mcp"
Write-Host "Public MCP : $PublicOrigin/mcp"
Write-Host ''
Write-Warning 'This pilot intentionally has no MCP authentication. It exposes ONLY the harmless official Sequential Thinking reference server. Do not add filesystem, shell, browser, application-control, secrets, or other privileged MCP servers to this pilot config.'
Write-Host ''

# Verify the pinned runtime can be resolved before changing Funnel configuration.
& $npx.Source -y $oneMcpPackage --version
if ($LASTEXITCODE -ne 0) {
    throw "Failed to resolve $oneMcpPackage."
}

# Runtime Scope is selected by the exact --config path. Re-running this script does
# not touch unrelated 1MCP runtimes.
& $npx.Source -y $oneMcpPackage serve --config $configPath --status *> $null
$statusExit = $LASTEXITCODE

if ($statusExit -ne 0) {
    Write-Host 'Starting 1MCP background runtime...'
    & $npx.Source -y $oneMcpPackage serve `
        --config $configPath `
        --host 127.0.0.1 `
        --port $LocalPort `
        --external-url $PublicOrigin `
        --filter pilot `
        --health-info-level minimal `
        --enable-async-loading `
        --background
    if ($LASTEXITCODE -ne 0) {
        throw '1MCP failed to start.'
    }
}
else {
    Write-Host '1MCP pilot runtime is already running.'
}

$localHealth = "http://127.0.0.1:$LocalPort/health"
$serverHealth = "http://127.0.0.1:$LocalPort/health/mcp/sequential-thinking"
$ready = $false
for ($attempt = 1; $attempt -le 30; $attempt++) {
    try {
        $health = Invoke-RestMethod -Method Get -Uri $localHealth -TimeoutSec 5
        $server = Invoke-RestMethod -Method Get -Uri $serverHealth -TimeoutSec 5
        if ([string]$server.state -eq 'ready') {
            $ready = $true
            break
        }
    }
    catch {
        # The supervisor may be ready before the stdio reference server finishes loading.
    }
    Start-Sleep -Seconds 1
}
if (-not $ready) {
    throw "1MCP started, but sequential-thinking did not become ready. Check: $serverHealth"
}

Write-Host 'Local 1MCP and Sequential Thinking are ready.'

# Funnel supports multiple independent HTTPS listeners. 8443 is deliberately used
# so the already-working 443 route is not changed by this pilot.
Write-Host "Publishing only HTTPS :$FunnelPort -> 127.0.0.1:$LocalPort ..."
& $tailscale.Source funnel --bg --https=$FunnelPort $LocalPort
if ($LASTEXITCODE -ne 0) {
    throw 'Tailscale Funnel failed to publish the pilot runtime.'
}

$publicHealth = "$PublicOrigin/health"
$publicReady = $false
for ($attempt = 1; $attempt -le 20; $attempt++) {
    try {
        $null = Invoke-RestMethod -Method Get -Uri $publicHealth -TimeoutSec 10
        $publicReady = $true
        break
    }
    catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $publicReady) {
    throw "Funnel was configured, but public health is not reachable: $publicHealth"
}

Write-Host ''
Write-Host 'BRIDGE_PILOT_STATUS=ready'
Write-Host "MCP_URL=$PublicOrigin/mcp"
Write-Host "PUBLIC_HEALTH=$publicHealth"
Write-Host "LOCAL_HEALTH=$localHealth"
Write-Host 'EXPECTED_TOOL=sequential_thinking'
Write-Host ''
Write-Host 'The existing Funnel on HTTPS 443 was not modified.'
Write-Host 'After the ChatGPT test, stop this unauthenticated pilot with:'
Write-Host '  .\scripts\stop-chat-bridge-pilot.ps1'
