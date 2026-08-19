[CmdletBinding()]
param(
    [string]$OutputRoot = (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage26\desktop-observation-qualification'),
    [string]$EnvironmentRoot = (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage26\hot-runtime-env')
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
$driverPath = Join-Path $PSScriptRoot 'stage26-desktop-observation-qualification.py'
$observationPath = Join-Path $repoRoot 'runtime\windows\observation.py'
$resolverPath = Join-Path $repoRoot 'runtime\windows\window_scoped_uia.py'
$fixturePath = Join-Path $PSScriptRoot 'stage26-windows-hot-runtime-fixture.ps1'
$lockPath = Join-Path $repoRoot 'config\stage26-openadapt-lock.json'
foreach ($required in @($driverPath, $observationPath, $resolverPath, $fixturePath, $lockPath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required Stage 26.2B asset is missing: $required"
    }
}

$venvDir = Join-Path $EnvironmentRoot 'venv'
$pythonExe = Join-Path $venvDir 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    throw 'Persistent Stage 26 Windows runtime environment is missing. Run Stage 26.2A qualification first.'
}

$lock = Get-Content -LiteralPath $lockPath -Raw -Encoding utf8 | ConvertFrom-Json
$flow = $lock.upstreams.openadapt_flow
$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$runDir = Join-Path $OutputRoot "observation-$timestamp"
$fixtureStatePath = Join-Path $runDir 'fixture-state.json'
$readyPath = Join-Path $runDir 'observer-ready.txt'
$closePath = Join-Path $runDir 'fixture-close.txt'
$driverResultPath = Join-Path $runDir 'desktop-observation-result.json'
$resultPath = Join-Path $runDir 'result.json'
$pinProbePath = Join-Path $runDir 'pin-probe.py'
$windowTitle = "Chat Agent Platform Stage 26.2B Desktop Observation $timestamp"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$fixtureProcess = $null
$fixtureKilled = $false
$chromeBefore = @(Get-Process chrome -ErrorAction SilentlyContinue).Count

$result = [ordered]@{
    schema_version = 1
    project_head = $null
    production_observation_path = $observationPath
    production_resolver_path = $resolverPath
    environment_reused = $true
    flow_pin_pass = $false
    windows_runtime_pin_pass = $false
    driver_pass = $false
    same_identity_pass = $false
    control_contract_pass = $false
    screenshot_digest_pass = $false
    freshness_contract_pass = $false
    bounded_control_count_pass = $false
    observation_only_pass = $false
    resolver_stats = $null
    action_count = $null
    false_action_count = $null
    unrelated_window_action_count = $null
    fixture_pid = $null
    fixture_killed = $false
    fixture_cleanup_pass = $false
    chrome_process_count_before = $chromeBefore
    chrome_process_count_after = $null
    chrome_survival_pass = $false
    driver_error = $null
    error = $null
    result_dir = $runDir
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
        [string]$probe.windows_runtime.uiautomation -eq '2.0.29'
    )
    if (-not $result.flow_pin_pass -or -not $result.windows_runtime_pin_pass) {
        throw 'Persistent Stage 26 Windows runtime environment pins drifted.'
    }

    Write-Host ''
    Write-Host '===== STAGE 26.2B DESKTOP OBSERVATION QUALIFICATION =====' -ForegroundColor Cyan
    Write-Host 'Read-only fixture observation. No clicks, typing or scrolling are performed.' -ForegroundColor Yellow

    $pwsh = Get-Command pwsh.exe -ErrorAction Stop
    $fixtureArgs = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-STA',
        '-File', $fixturePath,
        '-StatePath', $fixtureStatePath,
        '-RecorderReadyPath', $readyPath,
        '-ClosePath', $closePath,
        '-TotalCycles', '3',
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

    & $pythonExe $driverPath `
        '--run-dir' $runDir `
        '--fixture-state' $fixtureStatePath `
        '--recorder-ready' $readyPath
    $driverExit = $LASTEXITCODE

    if (-not (Test-Path -LiteralPath $driverResultPath -PathType Leaf)) {
        throw 'Desktop observation driver result is missing.'
    }
    $driver = Get-Content -LiteralPath $driverResultPath -Raw -Encoding utf8 | ConvertFrom-Json
    $result.driver_pass = [bool]$driver.pass
    $result.same_identity_pass = [bool]$driver.same_identity_pass
    $result.control_contract_pass = [bool]$driver.control_contract_pass
    $result.screenshot_digest_pass = [bool]$driver.screenshot_digest_pass
    $result.freshness_contract_pass = [bool]$driver.freshness_contract_pass
    $result.bounded_control_count_pass = [bool]$driver.bounded_control_count_pass
    $result.observation_only_pass = [bool]$driver.observation_only_pass
    $result.resolver_stats = $driver.resolver_stats
    $result.action_count = $driver.action_count
    $result.false_action_count = $driver.false_action_count
    $result.unrelated_window_action_count = $driver.unrelated_window_action_count
    $result.driver_error = $driver.error

    if ($driverExit -ne 0 -or -not $result.driver_pass) {
        $detail = if ($driver.error) { [string]$driver.error } else { "driver exit $driverExit" }
        throw "Stage 26.2B desktop observation qualification failed: $detail"
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
Write-Host '===== STAGE 26.2B DESKTOP OBSERVATION RESULT =====' -ForegroundColor Cyan
Write-Flag 'RESULT_PATH' $resultPath
Write-Flag 'PROJECT_HEAD' $result.project_head
Write-Flag 'PRODUCTION_OBSERVATION_PATH' $result.production_observation_path
Write-Flag 'PRODUCTION_RESOLVER_PATH' $result.production_resolver_path
Write-Flag 'ENVIRONMENT_REUSED' $result.environment_reused
Write-Flag 'FLOW_PIN_PASS' $result.flow_pin_pass
Write-Flag 'WINDOWS_RUNTIME_PIN_PASS' $result.windows_runtime_pin_pass
Write-Flag 'SAME_IDENTITY_PASS' $result.same_identity_pass
Write-Flag 'CONTROL_CONTRACT_PASS' $result.control_contract_pass
Write-Flag 'SCREENSHOT_DIGEST_PASS' $result.screenshot_digest_pass
Write-Flag 'FRESHNESS_CONTRACT_PASS' $result.freshness_contract_pass
Write-Flag 'BOUNDED_CONTROL_COUNT_PASS' $result.bounded_control_count_pass
Write-Flag 'OBSERVATION_ONLY_PASS' $result.observation_only_pass
if ($null -ne $result.resolver_stats) {
    foreach ($property in @($result.resolver_stats.PSObject.Properties | Sort-Object Name)) {
        Write-Flag ($property.Name.ToUpperInvariant()) $property.Value
    }
}
Write-Flag 'ACTION_COUNT' $result.action_count
Write-Flag 'FALSE_ACTION_COUNT' $result.false_action_count
Write-Flag 'UNRELATED_WINDOW_ACTION_COUNT' $result.unrelated_window_action_count
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
    $result.same_identity_pass -and
    $result.control_contract_pass -and
    $result.screenshot_digest_pass -and
    $result.freshness_contract_pass -and
    $result.bounded_control_count_pass -and
    $result.observation_only_pass -and
    $result.resolver_stats.desktop_fallback_calls -eq 0 -and
    $result.resolver_stats.window_binding_failures -eq 0 -and
    $result.resolver_stats.window_binding_ambiguities -eq 0 -and
    $result.action_count -eq 0 -and
    $result.false_action_count -eq 0 -and
    $result.unrelated_window_action_count -eq 0 -and
    $result.chrome_survival_pass -and
    $result.fixture_cleanup_pass -and
    $null -eq $result.error
)
if ($accepted) {
    Write-Flag 'STAGE26_2B_DESKTOP_OBSERVATION_RESULT' 'PASSED'
    exit 0
}
Write-Flag 'STAGE26_2B_DESKTOP_OBSERVATION_RESULT' 'FAILED'
exit 1
