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
$runtimeScope = Split-Path -Parent $config
$logsDir = Join-Path $runtimeScope 'logs'
$serverLog = Join-Path $logsDir 'server.log'
$launcherLog = Join-Path $logsDir 'launcher.log'
$windowsLauncher = Join-Path $logsDir 'hidden-1mcp-worker.cmd'

if ([string]::IsNullOrWhiteSpace($HealthServerName) -or $HealthServerName -notmatch '^[A-Za-z0-9._-]+$') {
    throw 'HealthServerName must be a non-empty MCP server name.'
}

New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

function Start-HiddenWindowsWorker {
    $npx = (Get-Command 'npx.cmd' -ErrorAction Stop).Source
    $cmd = if (-not [string]::IsNullOrWhiteSpace($env:ComSpec)) {
        $env:ComSpec
    }
    else {
        (Get-Command 'cmd.exe' -ErrorAction Stop).Source
    }

    # Invoke npx from an explicitly CREATE_NO_WINDOW cmd.exe. Hiding only an
    # outer pwsh process is insufficient on Windows because a later npx.cmd /
    # node console process may allocate a visible terminal of its own.
    $lines = @(
        '@echo off',
        ('call "{0}" -y "{1}" serve --config "{2}" --transport http --host 127.0.0.1 --port {3} --health-info-level minimal --enable-async-loading --log-file "{4}" >> "{5}" 2>&1' -f `
            $npx,
            $pkg,
            $config,
            $Port,
            $serverLog,
            $launcherLog),
        'exit /b %ERRORLEVEL%'
    )
    Set-Content -LiteralPath $windowsLauncher -Value $lines -Encoding ascii

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $cmd
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.WorkingDirectory = $runtimeScope
    $startInfo.ArgumentList.Add('/d')
    $startInfo.ArgumentList.Add('/c')
    $startInfo.ArgumentList.Add($windowsLauncher)

    $worker = [System.Diagnostics.Process]::new()
    $worker.StartInfo = $startInfo
    try {
        if (-not $worker.Start()) {
            throw 'Failed to start hidden 1MCP worker process.'
        }
        Write-Host "1MCP hidden cmd worker started. PID=$($worker.Id)" -ForegroundColor DarkGray
    }
    finally {
        $worker.Dispose()
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
        Start-HiddenWindowsWorker
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
