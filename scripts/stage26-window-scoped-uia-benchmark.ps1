[CmdletBinding()]
param(
    [string]$OutputRoot = (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage26\window-scoped-uia-benchmark'),
    [string]$EnvironmentRoot = (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage26\hot-runtime-env'),
    [ValidateRange(0, 10)][int]$WarmupCycles = 2,
    [ValidateRange(3, 50)][int]$MeasuredCycles = 10
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Flag {
    param([Parameter(Mandatory = $true)][string]$Name, [AllowNull()]$Value)
    $rendered = if ($null -eq $Value) { '<null>' } else { [string]$Value }
    Write-Host ("{0}={1}" -f $Name, $rendered)
}

function Start-ExactProcess {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList
    )
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $FilePath
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $false
    foreach ($arg in $ArgumentList) { [void]$psi.ArgumentList.Add([string]$arg) }
    $process = [System.Diagnostics.Process]::Start($psi)
    if ($null -eq $process) { throw "Failed to start process: $FilePath" }
    return $process
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$driverPath = Join-Path $PSScriptRoot 'stage26-window-scoped-uia-benchmark.py'
$resolverPath = Join-Path $PSScriptRoot 'stage26-window-scoped-uia-resolver.py'
$fixturePath = Join-Path $PSScriptRoot 'stage26-windows-hot-runtime-fixture.ps1'
$lockPath = Join-Path $repoRoot 'config\stage26-openadapt-lock.json'
foreach ($required in @($driverPath, $resolverPath, $fixturePath, $lockPath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required Stage 26.1E asset is missing: $required"
    }
}

$venvDir = Join-Path $EnvironmentRoot 'venv'
$pythonExe = Join-Path $venvDir 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    throw 'Stage 26.1D persistent benchmark environment is missing. Run Stage 26.1D first.'
}

$lock = Get-Content -LiteralPath $lockPath -Raw -Encoding utf8 | ConvertFrom-Json
$flow = $lock.upstreams.openadapt_flow
$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$runDir = Join-Path $OutputRoot "benchmark-$timestamp"
$fixtureStatePath = Join-Path $runDir 'fixture-state.json'
$readyPath = Join-Path $runDir 'executor-ready.txt'
$closePath = Join-Path $runDir 'fixture-close.txt'
$driverResultPath = Join-Path $runDir 'window-scoped-result.json'
$resultPath = Join-Path $runDir 'result.json'
$pinProbePath = Join-Path $runDir 'pin-probe.py'
$windowTitle = "Chat Agent Platform Stage 26.1E Window Scoped UIA $timestamp"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$totalCycles = $WarmupCycles + $MeasuredCycles
$fixtureProcess = $null
$fixtureKilled = $false
$chromeBefore = @(Get-Process chrome -ErrorAction SilentlyContinue).Count

$result = [ordered]@{
    schema_version = 1
    project_head = $null
    warmup_cycles = $WarmupCycles
    measured_cycles = $MeasuredCycles
    total_cycles = $totalCycles
    environment_reused = $true
    flow_pin_pass = $false
    windows_runtime_pin_pass = $false
    driver_pass = $false
    agent_process_reused = $false
    fixture_process_reused = $false
    resolver_stats = $null
    summary = $null
    unrelated_window_action_count = $null
    false_action_count = $null
    fixture_pid = $null
    fixture_killed = $false
    fixture_cleanup_pass = $false
    chrome_process_count_before = $chromeBefore
    chrome_process_count_after = $null
    chrome_survival_pass = $false
    result_dir = $runDir
    driver_error = $null
    error = $null
}

$pinProbe = @'
import json
from importlib import metadata

dist = metadata.distribution('openadapt-flow')
direct = json.loads(dist.read_text('direct_url.json') or '{}')
print(json.dumps({
    'version': metadata.version('openadapt-flow'),
    'commit': (direct.get('vcs_info') or {}).get('commit_id'),
    'windows_runtime': {
        'mss': metadata.version('mss'),
        'pyautogui': metadata.version('PyAutoGUI'),
        'uiautomation': metadata.version('uiautomation'),
    },
}))
'@
Set-Content -LiteralPath $pinProbePath -Value $pinProbe -Encoding utf8

try {
    $result.project_head = (& git.exe -C $repoRoot rev-parse HEAD 2>$null | Select-Object -Last 1).Trim()

    $probeOutput = & $pythonExe $pinProbePath 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Persistent environment pin probe failed.' }
    $probe = (($probeOutput | Select-Object -Last 1) -as [string]) | ConvertFrom-Json
    $result.flow_pin_pass = [bool](
        [string]$probe.commit -eq [string]$flow.commit -and
        [string]$probe.version -eq [string]$flow.declared_version
    )
    $result.windows_runtime_pin_pass = [bool](
        [string]$probe.windows_runtime.mss -eq '10.2.0' -and
        [string]$probe.windows_runtime.pyautogui -eq '0.9.54' -and
        [string]$probe.windows_runtime.uiautomation -eq '2.0.29'
    )
    if (-not $result.flow_pin_pass -or -not $result.windows_runtime_pin_pass) {
        throw 'Persistent Stage 26.1D environment pins drifted.'
    }

    Write-Host ''
    Write-Host '===== STAGE 26.1E WINDOW-SCOPED UIA BENCHMARK =====' -ForegroundColor Cyan
    Write-Host "Warmup cycles: $WarmupCycles | measured cycles: $MeasuredCycles" -ForegroundColor Yellow
    Write-Host 'Ничего не трогайте до DONE.' -ForegroundColor Yellow
    Write-Host 'Executor и fixture не перезапускаются между циклами.' -ForegroundColor Yellow

    $pwsh = Get-Command pwsh.exe -ErrorAction Stop
    $fixtureArgs = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-STA',
        '-File', $fixturePath,
        '-StatePath', $fixtureStatePath,
        '-RecorderReadyPath', $readyPath,
        '-ClosePath', $closePath,
        '-TotalCycles', [string]$totalCycles,
        '-WindowTitle', $windowTitle
    )
    $fixtureProcess = Start-ExactProcess -FilePath $pwsh.Source -ArgumentList $fixtureArgs
    $result.fixture_pid = $fixtureProcess.Id

    $deadline = (Get-Date).AddSeconds(30)
    while (-not (Test-Path -LiteralPath $fixtureStatePath -PathType Leaf)) {
        $fixtureProcess.Refresh()
        if ($fixtureProcess.HasExited) { throw "Fixture exited early ($($fixtureProcess.ExitCode))." }
        if ((Get-Date) -gt $deadline) { throw 'Fixture did not initialize.' }
        Start-Sleep -Milliseconds 100
    }

    $driverArgs = @(
        $driverPath,
        '--run-dir', $runDir,
        '--fixture-state', $fixtureStatePath,
        '--recorder-ready', $readyPath,
        '--warmup-cycles', [string]$WarmupCycles,
        '--measured-cycles', [string]$MeasuredCycles
    )
    & $pythonExe @driverArgs
    $driverExit = $LASTEXITCODE

    if (-not (Test-Path -LiteralPath $driverResultPath -PathType Leaf)) {
        throw 'Window-scoped driver result is missing.'
    }
    $driver = Get-Content -LiteralPath $driverResultPath -Raw -Encoding utf8 | ConvertFrom-Json
    $result.driver_pass = [bool]$driver.pass
    $result.agent_process_reused = [bool]$driver.agent_process_reused
    $result.fixture_process_reused = [bool]$driver.fixture_process_reused
    $result.resolver_stats = $driver.resolver_stats
    $result.summary = $driver.summary
    $result.unrelated_window_action_count = $driver.unrelated_window_action_count
    $result.false_action_count = $driver.false_action_count
    $result.driver_error = $driver.error

    if ($driverExit -ne 0 -or -not $result.driver_pass) {
        $detail = if ($driver.error) { [string]$driver.error } else { "driver exit $driverExit" }
        throw "Stage 26.1E window-scoped benchmark failed: $detail"
    }
}
catch {
    $result.error = $_.Exception.Message
}
finally {
    try { Set-Content -LiteralPath $closePath -Value 'CLOSE' -Encoding ascii -ErrorAction SilentlyContinue } catch {}
    if ($null -ne $fixtureProcess) {
        try {
            $fixtureProcess.Refresh()
            if (-not $fixtureProcess.HasExited) {
                [void]$fixtureProcess.WaitForExit(5000)
                $fixtureProcess.Refresh()
            }
            if (-not $fixtureProcess.HasExited) {
                $fixtureProcess.Kill($true)
                $fixtureKilled = $true
                [void]$fixtureProcess.WaitForExit(5000)
            }
        }
        catch {
            if ($null -eq $result.error) { $result.error = "Fixture cleanup failed: $($_.Exception.Message)" }
        }
    }
    $result.fixture_killed = $fixtureKilled
    $result.fixture_cleanup_pass = -not $fixtureKilled
    $chromeAfter = @(Get-Process chrome -ErrorAction SilentlyContinue).Count
    $result.chrome_process_count_after = $chromeAfter
    $result.chrome_survival_pass = [bool]($chromeBefore -eq 0 -or $chromeAfter -gt 0)
    $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $resultPath -Encoding utf8
}

Write-Host ''
Write-Host '===== STAGE 26.1E WINDOW-SCOPED RESULT =====' -ForegroundColor Cyan
Write-Flag 'RESULT_PATH' $resultPath
Write-Flag 'PROJECT_HEAD' $result.project_head
Write-Flag 'ENVIRONMENT_REUSED' $result.environment_reused
Write-Flag 'FLOW_PIN_PASS' $result.flow_pin_pass
Write-Flag 'WINDOWS_RUNTIME_PIN_PASS' $result.windows_runtime_pin_pass
Write-Flag 'AGENT_PROCESS_REUSED' $result.agent_process_reused
Write-Flag 'FIXTURE_PROCESS_REUSED' $result.fixture_process_reused
if ($null -ne $result.resolver_stats) {
    foreach ($property in @($result.resolver_stats.PSObject.Properties | Sort-Object Name)) {
        Write-Flag ($property.Name.ToUpperInvariant()) $property.Value
    }
}
if ($null -ne $result.summary) {
    foreach ($property in @($result.summary.PSObject.Properties | Sort-Object Name)) {
        $metric = $property.Name.ToUpperInvariant()
        if ($metric.EndsWith('_MS')) { $metric = $metric.Substring(0, $metric.Length - 3) }
        Write-Flag ($metric + '_P50_MS') $property.Value.p50_ms
        Write-Flag ($metric + '_P95_MS') $property.Value.p95_ms
    }
}
Write-Flag 'UNRELATED_WINDOW_ACTION_COUNT' $result.unrelated_window_action_count
Write-Flag 'FALSE_ACTION_COUNT' $result.false_action_count
Write-Flag 'CHROME_PROCESS_COUNT_BEFORE' $result.chrome_process_count_before
Write-Flag 'CHROME_PROCESS_COUNT_AFTER' $result.chrome_process_count_after
Write-Flag 'CHROME_SURVIVAL_PASS' $result.chrome_survival_pass
Write-Flag 'FIXTURE_KILLED' $result.fixture_killed
Write-Flag 'FIXTURE_CLEANUP_PASS' $result.fixture_cleanup_pass
Write-Flag 'DRIVER_ERROR' $result.driver_error
Write-Flag 'ERROR' $result.error

$accepted = [bool](
    $result.flow_pin_pass -and
    $result.windows_runtime_pin_pass -and
    $result.driver_pass -and
    $result.agent_process_reused -and
    $result.fixture_process_reused -and
    $result.resolver_stats.desktop_fallback_calls -eq 0 -and
    $result.unrelated_window_action_count -eq 0 -and
    $result.false_action_count -eq 0 -and
    $result.chrome_survival_pass -and
    $result.fixture_cleanup_pass -and
    $null -eq $result.error
)
if ($accepted) {
    Write-Flag 'STAGE26_1E_WINDOW_SCOPED_RESULT' 'PASSED'
    exit 0
}
Write-Flag 'STAGE26_1E_WINDOW_SCOPED_RESULT' 'FAILED'
exit 1
