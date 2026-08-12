param(
    [int]$Port = 3050,
    [string]$ConfigPath = (Join-Path $PSScriptRoot '..\runtime\mcp.json'),
    [string]$HealthServerName = 'sequential-thinking',
    [ValidateRange(10, 600)]
    [int]$ReadyTimeoutSeconds = 120,
    [switch]$ForegroundWorker,
    [string]$WorkerLogPath
)

$ErrorActionPreference = 'Stop'
$pkg = '@1mcp/agent@0.34.4'
$config = (Resolve-Path $ConfigPath).Path
$runtimeScope = Split-Path -Parent $config
$logsDir = Join-Path $runtimeScope 'logs'
$serverLog = Join-Path $logsDir 'server.log'
$launcherLog = if ([string]::IsNullOrWhiteSpace($WorkerLogPath)) {
    Join-Path $logsDir 'launcher.log'
}
else {
    $WorkerLogPath
}

if ([string]::IsNullOrWhiteSpace($HealthServerName) -or $HealthServerName -notmatch '^[A-Za-z0-9._-]+$') {
    throw 'HealthServerName must be a non-empty MCP server name.'
}

New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

if ($ForegroundWorker) {
    # Windows UI wrapper: keep 1MCP in normal foreground mode inside this
    # deliberately hidden pwsh process. 1MCP's own --background implementation
    # uses a detached Node child which creates a visible console on Windows.
    # Runtime Scope PID/status/stop semantics remain owned by 1MCP itself.
    try {
        & npx.cmd -y $pkg serve `
            --config $config `
            --transport http `
            --host 127.0.0.1 `
            --port $Port `
            --health-info-level minimal `
            --enable-async-loading `
            --log-file $serverLog `
            *>> $launcherLog

        exit $LASTEXITCODE
    }
    catch {
        $_ | Out-String | Add-Content -LiteralPath $launcherLog -Encoding utf8
        exit 1
    }
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
    if ($IsWindows) {
        $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
        $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
        $startInfo.FileName = $pwsh
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true

        foreach ($argument in @(
            '-NoLogo',
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-File', $PSCommandPath,
            '-Port', [string]$Port,
            '-ConfigPath', $config,
            '-HealthServerName', $HealthServerName,
            '-ReadyTimeoutSeconds', [string]$ReadyTimeoutSeconds,
            '-ForegroundWorker',
            '-WorkerLogPath', $launcherLog
        )) {
            $startInfo.ArgumentList.Add([string]$argument)
        }

        $worker = [System.Diagnostics.Process]::new()
        $worker.StartInfo = $startInfo
        try {
            if (-not $worker.Start()) {
                throw 'Failed to start hidden 1MCP worker host.'
            }
            Write-Host "1MCP hidden worker host started. PID=$($worker.Id)" -ForegroundColor DarkGray
        }
        finally {
            $worker.Dispose()
        }
    }
    else {
        & npx.cmd -y $pkg serve `
            --config $config `
            --host 127.0.0.1 `
            --port $Port `
            --health-info-level minimal `
            --enable-async-loading `
            --background
        if ($LASTEXITCODE -ne 0) { throw '1MCP failed to start.' }
    }
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
            return
        }
    }
    catch {}
    Start-Sleep -Seconds 1
}

$tail = ''
if (Test-Path -LiteralPath $launcherLog) {
    try {
        $tail = (
            Get-Content -LiteralPath $launcherLog -Tail 20 -ErrorAction Stop |
                Out-String
        ).Trim()
    }
    catch {}
}

if ([string]::IsNullOrWhiteSpace($tail)) {
    throw "Local MCP server '$HealthServerName' did not become ready within $ReadyTimeoutSeconds seconds: $health"
}

throw "Local MCP server '$HealthServerName' did not become ready within $ReadyTimeoutSeconds seconds: $health. $tail"
