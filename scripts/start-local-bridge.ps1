param(
    [int]$Port = 3050,
    [string]$ConfigPath = (Join-Path $PSScriptRoot '..\runtime\mcp.json'),
    [string]$HealthServerName = 'sequential-thinking',
    [string]$OneMcpPackage = '@1mcp/agent@0.34.4',
    [switch]$RuntimeReadyOnly,
    [switch]$EnableLazyLoading,
    [switch]$DisableAsyncLoading,
    [string]$InternalTools,
    [ValidateRange(10, 600)]
    [int]$ReadyTimeoutSeconds = 120
)

$ErrorActionPreference = 'Stop'

if ($OneMcpPackage -notmatch '^@1mcp/agent@[0-9A-Za-z.+-]+$') {
    throw 'OneMcpPackage must be an exact @1mcp/agent version.'
}

$pkg = $OneMcpPackage
$config = (Resolve-Path $ConfigPath).Path
$runtimeScope = Split-Path -Parent $config
$logsDir = Join-Path $runtimeScope 'logs'
$serverLog = Join-Path $logsDir 'server.log'
$launcherLog = Join-Path $logsDir 'launcher.log'
$windowsLauncher = Join-Path $logsDir 'hidden-1mcp-worker.cmd'

if (-not $RuntimeReadyOnly) {
    if ([string]::IsNullOrWhiteSpace($HealthServerName) -or $HealthServerName -notmatch '^[A-Za-z0-9._-]+$') {
        throw 'HealthServerName must be a non-empty MCP server name.'
    }
}

if (-not [string]::IsNullOrWhiteSpace($InternalTools) -and $InternalTools -notmatch '^[A-Za-z0-9_,.-]+$') {
    throw 'InternalTools must be a comma-separated 1MCP internal tool/category list.'
}

New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

function Get-RuntimeFeatureArguments {
    $arguments = [System.Collections.Generic.List[string]]::new()

    if (-not $DisableAsyncLoading) {
        $arguments.Add('--enable-async-loading')
    }
    if ($EnableLazyLoading) {
        $arguments.Add('--enable-lazy-loading')
    }
    if (-not [string]::IsNullOrWhiteSpace($InternalTools)) {
        # 1MCP 0.35 pre-releases use two gates for internal tools: the
        # top-level enable flag authorizes execution, while --internal-tools
        # constrains the tool surface advertised to the MCP client. Always
        # pass both together so selected management tools are functional
        # without publishing the broader installation/edit/discovery set.
        $arguments.Add('--enable-internal-tools')
        $arguments.Add('--internal-tools')
        $arguments.Add($InternalTools)
    }

    return $arguments
}

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
    $featureParts = @()
    foreach ($argument in (Get-RuntimeFeatureArguments)) {
        if ($argument -match '^[A-Za-z0-9_,.=-]+$') {
            $featureParts += $argument
        }
        else {
            $featureParts += ('"{0}"' -f $argument.Replace('"', '""'))
        }
    }
    $featureText = ($featureParts -join ' ')

    $lines = @(
        '@echo off',
        ('call "{0}" -y "{1}" serve --config "{2}" --transport http --host 127.0.0.1 --port {3} --health-info-level minimal {4} --log-file "{5}" >> "{6}" 2>&1' -f `
            $npx,
            $pkg,
            $config,
            $Port,
            $featureText,
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

$healthLabel = if ($RuntimeReadyOnly) { '1mcp-runtime' } else { $HealthServerName }

Write-Host '=== Local MCP bridge ===' -ForegroundColor Cyan
Write-Host "1MCP   : $pkg"
Write-Host "Config : $config"
Write-Host "MCP    : http://127.0.0.1:$Port/mcp"
Write-Host "Health : $healthLabel"
Write-Host "Lazy   : $([bool]$EnableLazyLoading)"
Write-Host "Async  : $(-not [bool]$DisableAsyncLoading)"
if (-not [string]::IsNullOrWhiteSpace($InternalTools)) {
    Write-Host "Internal: $InternalTools"
}

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
        $serveArgs = [System.Collections.Generic.List[string]]::new()
        foreach ($argument in @(
            '-y', $pkg, 'serve',
            '--config', $config,
            '--host', '127.0.0.1',
            '--port', [string]$Port,
            '--health-info-level', 'minimal'
        )) {
            $serveArgs.Add([string]$argument)
        }
        foreach ($argument in (Get-RuntimeFeatureArguments)) {
            $serveArgs.Add([string]$argument)
        }
        $serveArgs.Add('--background')

        & npx.cmd @serveArgs
        if ($LASTEXITCODE -ne 0) { throw '1MCP failed to start.' }
    }
}
elseif ($statusCode -in @(4,5)) {
    Write-Host '1MCP is starting; waiting for readiness.' -ForegroundColor Yellow
}
else {
    throw "1MCP supervisor is unhealthy (status exit code $statusCode)."
}

if ($RuntimeReadyOnly) {
    $health = "http://127.0.0.1:$Port/health/ready"
    for ($attempt = 1; $attempt -le $ReadyTimeoutSeconds; $attempt++) {
        try {
            $response = Invoke-WebRequest -Method Get -Uri $health -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Host 'LOCAL_BRIDGE_STATUS=ready' -ForegroundColor Green
                Write-Host "MCP_URL=http://127.0.0.1:$Port/mcp"
                Write-Host 'HEALTH_MODE=runtime'
                return
            }
        }
        catch {}
        Start-Sleep -Seconds 1
    }
}
else {
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
    throw "Local MCP runtime did not become ready within $ReadyTimeoutSeconds seconds: $health"
}

throw "Local MCP runtime did not become ready within $ReadyTimeoutSeconds seconds: $health. $tail"