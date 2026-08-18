[CmdletBinding()]
param(
    [string]$OutputRoot = (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage26\executor-qualification'),
    [int]$InteractionTimeoutSeconds = 120,
    [switch]$KeepEnvironment
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Flag {
    param([Parameter(Mandatory = $true)][string]$Name, [AllowNull()]$Value)
    $rendered = if ($null -eq $Value) { '<null>' } else { [string]$Value }
    Write-Host ("{0}={1}" -f $Name, $rendered)
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList,
        [Parameter(Mandatory = $true)][string]$Label
    )
    & $FilePath @ArgumentList
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) { throw "$Label failed with exit code $exitCode" }
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
    if ($null -eq $process) { throw "Failed to start qualification process: $FilePath" }
    return $process
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$lockPath = Join-Path $repoRoot 'config\stage26-openadapt-lock.json'
$driverPath = Join-Path $PSScriptRoot 'stage26-openadapt-windows-executor-driver.py'
$fixturePath = Join-Path $PSScriptRoot 'stage26-windows-capture-fixture.ps1'
foreach ($required in @($lockPath, $driverPath, $fixturePath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required Stage 26.1C asset is missing: $required"
    }
}

$lock = Get-Content -LiteralPath $lockPath -Raw -Encoding utf8 | ConvertFrom-Json
if ([int]$lock.schema_version -ne 1) { throw 'Unsupported OpenAdapt lock schema.' }
$flow = $lock.upstreams.openadapt_flow
$requiredPython = [string]$lock.python.required_major_minor

# Pinned Flow 1.31.0's win_agent imports these lazily at request time, but its
# [windows] extra currently declares only requests + pywin32. A clean target
# venv therefore needs the actual agent runtime substrate stated explicitly.
# Keep these exact so the physical acceptance run is reproducible instead of
# inheriting whatever happens to be installed globally on the operator host.
$windowsRuntimePins = [ordered]@{
    mss = '10.2.0'
    pyautogui = '0.9.54'
    uiautomation = '2.0.29'
}

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$runDir = Join-Path $OutputRoot "executor-$timestamp"
$venvDir = Join-Path $runDir 'venv'
$fixtureStatePath = Join-Path $runDir 'fixture-state.json'
$donePath = Join-Path $runDir 'fixture-done.txt'
$readyPath = Join-Path $runDir 'executor-ready.txt'
$closePath = Join-Path $runDir 'fixture-close.txt'
$driverResultPath = Join-Path $runDir 'driver-result.json'
$resultPath = Join-Path $runDir 'result.json'
$pinProbePath = Join-Path $runDir 'pin-probe.py'
$windowTitle = "Chat Agent Platform Stage 26.1C Executor Fixture $timestamp"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$chromeBefore = @(Get-Process chrome -ErrorAction SilentlyContinue).Count
$fixtureProcess = $null
$fixtureKilled = $false
$driverExit = $null
$driverResult = $null

$result = [ordered]@{
    schema_version = 1
    created_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    project_head = $null
    required_python = $requiredPython
    python_version = $null
    flow_expected_commit = [string]$flow.commit
    flow_installed_commit = $null
    flow_installed_version = $null
    flow_pin_pass = $false
    windows_runtime_expected = [ordered]@{
        mss = [string]$windowsRuntimePins.mss
        pyautogui = [string]$windowsRuntimePins.pyautogui
        uiautomation = [string]$windowsRuntimePins.uiautomation
    }
    windows_runtime_installed = $null
    windows_runtime_pin_pass = $false
    driver_exit_code = $null
    driver_pass = $false
    driver_error = $null
    agent_loopback_pass = $null
    agent_auth_required_pass = $null
    legacy_capability_absent_pass = $null
    legacy_route_404_pass = $null
    unauthorized_input_401_pass = $null
    command_field_rejected_pass = $null
    unsupported_action_rejected_pass = $null
    interactive_session_pass = $null
    stale_frame_refusal_pass = $null
    stale_context_refusal_pass = $null
    uia_unique_target_pass = $null
    fingerprint_bound_action_pass = $null
    guarded_keyboard_pass = $null
    guarded_coordinate_pass = $null
    guarded_scroll_pass = $null
    fixture_sequence_pass = $null
    unrelated_window_action_count = $null
    false_action_count = $null
    legacy_exec_enabled = $null
    windows_backend_allow_legacy_exec = $null
    delivered_operations = $null
    fixture_pid = $null
    fixture_killed = $false
    fixture_cleanup_pass = $false
    chrome_process_count_before = $chromeBefore
    chrome_process_count_after = $null
    chrome_survival_pass = $false
    environment_kept = [bool]$KeepEnvironment
    result_dir = $runDir
    error = $null
}

try {
    $projectHead = (& git.exe -C $repoRoot rev-parse HEAD 2>$null | Select-Object -Last 1).Trim()
    $result.project_head = $projectHead

    $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -eq $pyLauncher) { throw 'Windows Python launcher py.exe is required.' }
    $pythonProbe = & $pyLauncher.Source "-$requiredPython" -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Python $requiredPython is unavailable through py.exe." }
    $pythonVersion = (($pythonProbe | Select-Object -Last 1) -as [string]).Trim()
    if (-not $pythonVersion.StartsWith("$requiredPython.")) {
        throw "Resolved Python $pythonVersion does not match $requiredPython.x"
    }
    $result.python_version = $pythonVersion

    Invoke-Checked -FilePath $pyLauncher.Source -ArgumentList @("-$requiredPython", '-m', 'venv', $venvDir) -Label 'Create Stage 26.1C venv'
    $pythonExe = Join-Path $venvDir 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) { throw 'Qualification venv Python is missing.' }

    $flowSpec = "openadapt-flow[windows] @ git+https://github.com/$($flow.repository).git@$($flow.commit)"
    Invoke-Checked -FilePath $pythonExe -ArgumentList @(
        '-m', 'pip', 'install', '--disable-pip-version-check', '--no-input', $flowSpec
    ) -Label 'Install pinned openadapt-flow[windows]'

    $runtimeSpecs = @(
        "mss==$($windowsRuntimePins.mss)",
        "PyAutoGUI==$($windowsRuntimePins.pyautogui)",
        "uiautomation==$($windowsRuntimePins.uiautomation)"
    )
    Invoke-Checked -FilePath $pythonExe -ArgumentList @(
        '-m', 'pip', 'install', '--disable-pip-version-check', '--no-input',
        $runtimeSpecs[0], $runtimeSpecs[1], $runtimeSpecs[2]
    ) -Label 'Install pinned OpenAdapt Windows agent runtime dependencies'

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
    $pinOutput = & $pythonExe $pinProbePath 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Pinned OpenAdapt Flow direct_url/runtime dependency probe failed.' }
    $pin = (($pinOutput | Select-Object -Last 1) -as [string]) | ConvertFrom-Json
    $result.flow_installed_commit = [string]$pin.commit
    $result.flow_installed_version = [string]$pin.version
    $result.flow_pin_pass = [bool](
        $result.flow_installed_commit -eq [string]$flow.commit -and
        $result.flow_installed_version -eq [string]$flow.declared_version
    )
    if (-not $result.flow_pin_pass) {
        throw "Flow pin mismatch: $($result.flow_installed_version) / $($result.flow_installed_commit)"
    }

    $result.windows_runtime_installed = [ordered]@{
        mss = [string]$pin.windows_runtime.mss
        pyautogui = [string]$pin.windows_runtime.pyautogui
        uiautomation = [string]$pin.windows_runtime.uiautomation
    }
    $result.windows_runtime_pin_pass = [bool](
        $result.windows_runtime_installed.mss -eq [string]$windowsRuntimePins.mss -and
        $result.windows_runtime_installed.pyautogui -eq [string]$windowsRuntimePins.pyautogui -and
        $result.windows_runtime_installed.uiautomation -eq [string]$windowsRuntimePins.uiautomation
    )
    if (-not $result.windows_runtime_pin_pass) {
        throw "Windows runtime dependency pin mismatch."
    }

    Write-Host ''
    Write-Host '===== STAGE 26.1C BOUNDED WINDOWS EXECUTOR FIXTURE =====' -ForegroundColor Cyan
    Write-Host 'Откроется отдельное тестовое окно. На этот раз НИЧЕГО в нём не нажимайте.' -ForegroundColor Yellow
    Write-Host 'Typed Windows executor сам выполнит только безопасную последовательность внутри fixture.' -ForegroundColor Yellow
    Write-Host 'Не двигайте мышь и не переключайте окна до DONE, чтобы не нарушать freshness/focus проверки.' -ForegroundColor Yellow
    Write-Host 'Chrome и рабочие приложения тест не закрывает и не использует.' -ForegroundColor Yellow

    $pwshCommand = Get-Command pwsh.exe -ErrorAction Stop
    $fixtureArgs = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-STA',
        '-File', $fixturePath,
        '-StatePath', $fixtureStatePath,
        '-DonePath', $donePath,
        '-RecorderReadyPath', $readyPath,
        '-ClosePath', $closePath,
        '-WindowTitle', $windowTitle
    )
    $fixtureProcess = Start-ExactProcess -FilePath $pwshCommand.Source -ArgumentList $fixtureArgs
    $result.fixture_pid = $fixtureProcess.Id

    $fixtureDeadline = (Get-Date).AddSeconds(30)
    while (-not (Test-Path -LiteralPath $fixtureStatePath -PathType Leaf)) {
        $fixtureProcess.Refresh()
        if ($fixtureProcess.HasExited) { throw "Fixture exited before initialization (exit $($fixtureProcess.ExitCode))." }
        if ((Get-Date) -gt $fixtureDeadline) { throw 'Fixture did not initialize before timeout.' }
        Start-Sleep -Milliseconds 200
    }

    $driverArgs = @(
        $driverPath,
        '--run-dir', $runDir,
        '--fixture-state', $fixtureStatePath,
        '--recorder-ready', $readyPath,
        '--done', $donePath,
        '--timeout-seconds', [string]$InteractionTimeoutSeconds
    )
    & $pythonExe @driverArgs
    $driverExit = $LASTEXITCODE
    $result.driver_exit_code = $driverExit

    if (-not (Test-Path -LiteralPath $driverResultPath -PathType Leaf)) {
        throw "Driver result was not written: $driverResultPath"
    }
    $driverResult = Get-Content -LiteralPath $driverResultPath -Raw -Encoding utf8 | ConvertFrom-Json
    $result.driver_pass = [bool]$driverResult.pass
    $result.driver_error = $driverResult.error
    foreach ($field in @(
        'agent_loopback_pass', 'agent_auth_required_pass',
        'legacy_capability_absent_pass', 'legacy_route_404_pass',
        'unauthorized_input_401_pass', 'command_field_rejected_pass',
        'unsupported_action_rejected_pass', 'interactive_session_pass',
        'stale_frame_refusal_pass', 'stale_context_refusal_pass',
        'uia_unique_target_pass', 'fingerprint_bound_action_pass',
        'guarded_keyboard_pass', 'guarded_coordinate_pass', 'guarded_scroll_pass',
        'fixture_sequence_pass', 'unrelated_window_action_count', 'false_action_count',
        'legacy_exec_enabled', 'windows_backend_allow_legacy_exec', 'delivered_operations'
    )) {
        $result[$field] = $driverResult.$field
    }
    if ($driverExit -ne 0 -or -not $result.driver_pass) {
        $detail = if ($driverResult.error) { [string]$driverResult.error } else { "driver exit $driverExit" }
        throw "Stage 26.1C Windows executor driver failed: $detail"
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

    if (-not $KeepEnvironment) {
        if (Test-Path -LiteralPath $venvDir) {
            Remove-Item -LiteralPath $venvDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    $chromeAfter = @(Get-Process chrome -ErrorAction SilentlyContinue).Count
    $result.chrome_process_count_after = $chromeAfter
    $result.chrome_survival_pass = [bool]($chromeBefore -eq 0 -or $chromeAfter -gt 0)
    $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $resultPath -Encoding utf8
}

Write-Host ''
Write-Host '===== STAGE 26.1C WINDOWS EXECUTOR QUALIFICATION =====' -ForegroundColor Cyan
Write-Flag 'RESULT_PATH' $resultPath
Write-Flag 'PYTHON_VERSION' $result.python_version
Write-Flag 'FLOW_INSTALLED_COMMIT' $result.flow_installed_commit
Write-Flag 'FLOW_INSTALLED_VERSION' $result.flow_installed_version
Write-Flag 'FLOW_PIN_PASS' $result.flow_pin_pass
Write-Flag 'WINDOWS_RUNTIME_EXPECTED_MSS' $result.windows_runtime_expected.mss
Write-Flag 'WINDOWS_RUNTIME_EXPECTED_PYAUTOGUI' $result.windows_runtime_expected.pyautogui
Write-Flag 'WINDOWS_RUNTIME_EXPECTED_UIAUTOMATION' $result.windows_runtime_expected.uiautomation
if ($null -ne $result.windows_runtime_installed) {
    Write-Flag 'WINDOWS_RUNTIME_INSTALLED_MSS' $result.windows_runtime_installed.mss
    Write-Flag 'WINDOWS_RUNTIME_INSTALLED_PYAUTOGUI' $result.windows_runtime_installed.pyautogui
    Write-Flag 'WINDOWS_RUNTIME_INSTALLED_UIAUTOMATION' $result.windows_runtime_installed.uiautomation
}
else {
    Write-Flag 'WINDOWS_RUNTIME_INSTALLED_MSS' $null
    Write-Flag 'WINDOWS_RUNTIME_INSTALLED_PYAUTOGUI' $null
    Write-Flag 'WINDOWS_RUNTIME_INSTALLED_UIAUTOMATION' $null
}
Write-Flag 'WINDOWS_RUNTIME_PIN_PASS' $result.windows_runtime_pin_pass
Write-Flag 'DRIVER_PASS' $result.driver_pass
foreach ($name in @(
    'AGENT_LOOPBACK_PASS','AGENT_AUTH_REQUIRED_PASS','LEGACY_CAPABILITY_ABSENT_PASS',
    'LEGACY_ROUTE_404_PASS','UNAUTHORIZED_INPUT_401_PASS','COMMAND_FIELD_REJECTED_PASS',
    'UNSUPPORTED_ACTION_REJECTED_PASS','INTERACTIVE_SESSION_PASS','STALE_FRAME_REFUSAL_PASS',
    'STALE_CONTEXT_REFUSAL_PASS','UIA_UNIQUE_TARGET_PASS','FINGERPRINT_BOUND_ACTION_PASS',
    'GUARDED_KEYBOARD_PASS','GUARDED_COORDINATE_PASS','GUARDED_SCROLL_PASS','FIXTURE_SEQUENCE_PASS'
)) {
    $property = $name.ToLowerInvariant()
    Write-Flag $name $result[$property]
}
Write-Flag 'UNRELATED_WINDOW_ACTION_COUNT' $result.unrelated_window_action_count
Write-Flag 'FALSE_ACTION_COUNT' $result.false_action_count
Write-Flag 'LEGACY_EXEC_ENABLED' $result.legacy_exec_enabled
Write-Flag 'WINDOWS_BACKEND_ALLOW_LEGACY_EXEC' $result.windows_backend_allow_legacy_exec
Write-Flag 'DELIVERED_OPERATIONS' ($result.delivered_operations -join ',')
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
    $result.chrome_survival_pass -and
    $result.fixture_cleanup_pass -and
    $null -eq $result.error
)
if ($accepted) {
    Write-Flag 'STAGE26_1C_EXECUTOR_RESULT' 'PASSED'
    exit 0
}
Write-Flag 'STAGE26_1C_EXECUTOR_RESULT' 'FAILED'
exit 1
