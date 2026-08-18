[CmdletBinding()]
param(
    [string]$OutputRoot = (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage26\capture-qualification'),
    [int]$InteractionTimeoutSeconds = 240,
    [switch]$KeepEnvironment
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Flag {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [AllowNull()]$Value
    )
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
    if ($exitCode -ne 0) {
        throw "$Label failed with exit code $exitCode"
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$lockPath = Join-Path $repoRoot 'config\stage26-openadapt-lock.json'
$driverPath = Join-Path $PSScriptRoot 'stage26-openadapt-capture-driver.py'
$fixturePath = Join-Path $PSScriptRoot 'stage26-windows-capture-fixture.ps1'

foreach ($required in @($lockPath, $driverPath, $fixturePath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required Stage 26.1B asset is missing: $required"
    }
}

$lock = Get-Content -LiteralPath $lockPath -Raw -Encoding utf8 | ConvertFrom-Json
if ([int]$lock.schema_version -ne 1) {
    throw "Unsupported OpenAdapt lock schema: $($lock.schema_version)"
}
$flow = $lock.upstreams.openadapt_flow
$capture = $lock.upstreams.openadapt_capture
$requiredPython = [string]$lock.python.required_major_minor

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$runDir = Join-Path $OutputRoot "capture-$timestamp"
$venvDir = Join-Path $runDir 'venv'
$fixtureStatePath = Join-Path $runDir 'fixture-state.json'
$donePath = Join-Path $runDir 'fixture-done.txt'
$recorderReadyPath = Join-Path $runDir 'recorder-ready.txt'
$closePath = Join-Path $runDir 'fixture-close.txt'
$driverResultPath = Join-Path $runDir 'driver-result.json'
$resultPath = Join-Path $runDir 'result.json'
$pinProbePath = Join-Path $runDir 'pin-probe.py'
$windowTitle = "Chat Agent Platform Stage 26.1B Capture Fixture $timestamp"

New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$chromeBefore = @(Get-Process chrome -ErrorAction SilentlyContinue).Count
$fixtureProcess = $null
$fixtureKilled = $false
$driverExit = $null
$pythonVersion = $null
$flowInstalledCommit = $null
$flowInstalledVersion = $null
$captureInstalledCommit = $null
$captureInstalledVersion = $null
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
    capture_expected_commit = [string]$capture.commit
    capture_installed_commit = $null
    capture_installed_version = $null
    window_title = $windowTitle
    fixture_pid = $null
    fixture_killed = $false
    driver_exit_code = $null
    driver_pass = $false
    raw_capture_dir = $null
    recording_dir = $null
    bundle_dir = $null
    flow_event_kinds = $null
    structural_event_count = $null
    window_scope_pass = $null
    required_kinds_pass = $null
    expected_text_pass = $null
    expected_key_pass = $null
    uia_evidence_pass = $null
    fixture_sequence_pass = $null
    compile_pass = $null
    replay_execution = $null
    bounded_replay_refusal = $null
    raw_artifact_containment_pass = $false
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
    if ($null -eq $pyLauncher) {
        throw 'Windows Python launcher py.exe is required.'
    }
    $pythonProbe = & $pyLauncher.Source "-$requiredPython" -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python $requiredPython is not available through py.exe."
    }
    $pythonVersion = (($pythonProbe | Select-Object -Last 1) -as [string]).Trim()
    if (-not $pythonVersion.StartsWith("$requiredPython.")) {
        throw "Resolved Python $pythonVersion does not match $requiredPython.x"
    }
    $result.python_version = $pythonVersion

    Invoke-Checked -FilePath $pyLauncher.Source -ArgumentList @("-$requiredPython", '-m', 'venv', $venvDir) -Label 'Create Stage 26.1B venv'
    $pythonExe = Join-Path $venvDir 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
        throw "Qualification venv Python was not created: $pythonExe"
    }

    $captureSpec = "openadapt-capture @ git+https://github.com/$($capture.repository).git@$($capture.commit)"
    $flowSpec = "openadapt-flow[windows] @ git+https://github.com/$($flow.repository).git@$($flow.commit)"

    Invoke-Checked -FilePath $pythonExe -ArgumentList @(
        '-m', 'pip', 'install', '--disable-pip-version-check', '--no-input', $captureSpec
    ) -Label 'Install pinned openadapt-capture'
    Invoke-Checked -FilePath $pythonExe -ArgumentList @(
        '-m', 'pip', 'install', '--disable-pip-version-check', '--no-input', $flowSpec
    ) -Label 'Install pinned openadapt-flow[windows]'

    $pinProbe = @'
import json
from importlib import metadata

def info(name):
    dist = metadata.distribution(name)
    direct = json.loads(dist.read_text('direct_url.json') or '{}')
    return {
        'version': metadata.version(name),
        'commit': (direct.get('vcs_info') or {}).get('commit_id'),
    }
print(json.dumps({'flow': info('openadapt-flow'), 'capture': info('openadapt-capture')}))
'@
    Set-Content -LiteralPath $pinProbePath -Value $pinProbe -Encoding utf8
    $pinOutput = & $pythonExe $pinProbePath 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw 'Pinned OpenAdapt direct_url probe failed.'
    }
    $pin = (($pinOutput | Select-Object -Last 1) -as [string]) | ConvertFrom-Json
    $flowInstalledCommit = [string]$pin.flow.commit
    $flowInstalledVersion = [string]$pin.flow.version
    $captureInstalledCommit = [string]$pin.capture.commit
    $captureInstalledVersion = [string]$pin.capture.version
    $result.flow_installed_commit = $flowInstalledCommit
    $result.flow_installed_version = $flowInstalledVersion
    $result.capture_installed_commit = $captureInstalledCommit
    $result.capture_installed_version = $captureInstalledVersion

    if ($flowInstalledCommit -ne [string]$flow.commit -or $flowInstalledVersion -ne [string]$flow.declared_version) {
        throw "Flow pin mismatch: $flowInstalledVersion / $flowInstalledCommit"
    }
    if ($captureInstalledCommit -ne [string]$capture.commit -or $captureInstalledVersion -ne [string]$capture.declared_version) {
        throw "Capture pin mismatch: $captureInstalledVersion / $captureInstalledCommit"
    }

    Write-Host ''
    Write-Host '===== STAGE 26.1B HUMAN INPUT FIXTURE =====' -ForegroundColor Cyan
    Write-Host 'Откроется отдельное тестовое окно. Дождитесь READY внутри окна.' -ForegroundColor Yellow
    Write-Host 'Затем выполните в нём шаги 1→5. Не кликайте другие окна до DONE.' -ForegroundColor Yellow
    Write-Host 'Рабочие приложения и обычный Chrome тест не закрывает.' -ForegroundColor Yellow

    $fixtureArgs = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-STA',
        '-File', $fixturePath,
        '-StatePath', $fixtureStatePath,
        '-DonePath', $donePath,
        '-RecorderReadyPath', $recorderReadyPath,
        '-ClosePath', $closePath,
        '-WindowTitle', $windowTitle
    )
    $fixtureProcess = Start-Process -FilePath 'pwsh.exe' -ArgumentList $fixtureArgs -PassThru
    $result.fixture_pid = $fixtureProcess.Id

    $fixtureDeadline = (Get-Date).AddSeconds(30)
    while (-not (Test-Path -LiteralPath $fixtureStatePath -PathType Leaf)) {
        if ($fixtureProcess.HasExited) {
            throw "Fixture process exited before creating state (exit $($fixtureProcess.ExitCode))."
        }
        if ((Get-Date) -gt $fixtureDeadline) {
            throw 'Fixture window did not initialize before timeout.'
        }
        Start-Sleep -Milliseconds 200
        $fixtureProcess.Refresh()
    }

    $driverArgs = @(
        $driverPath,
        '--run-dir', $runDir,
        '--window-title', $windowTitle,
        '--fixture-state', $fixtureStatePath,
        '--done', $donePath,
        '--recorder-ready', $recorderReadyPath,
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
    foreach ($field in @(
        'raw_capture_dir', 'recording_dir', 'bundle_dir', 'flow_event_kinds',
        'structural_event_count', 'window_scope_pass', 'required_kinds_pass',
        'expected_text_pass', 'expected_key_pass', 'uia_evidence_pass',
        'fixture_sequence_pass', 'compile_pass', 'replay_execution',
        'bounded_replay_refusal'
    )) {
        $result[$field] = $driverResult.$field
    }

    $containmentRoot = [System.IO.Path]::GetFullPath($runDir).TrimEnd('\') + '\'
    $contained = $true
    foreach ($pathValue in @($driverResult.raw_capture_dir, $driverResult.recording_dir, $driverResult.bundle_dir)) {
        $full = [System.IO.Path]::GetFullPath([string]$pathValue)
        if (-not $full.StartsWith($containmentRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            $contained = $false
        }
    }
    $result.raw_artifact_containment_pass = $contained

    if ($driverExit -ne 0 -or -not [bool]$driverResult.pass) {
        $detail = if ($driverResult.error) { [string]$driverResult.error } else { "driver exit $driverExit" }
        throw "Stage 26.1B capture driver failed: $detail"
    }
    if (-not $contained) {
        throw 'Capture/recording/bundle escaped the qualification run directory.'
    }
}
catch {
    $result.error = $_.Exception.Message
}
finally {
    try {
        Set-Content -LiteralPath $closePath -Value 'CLOSE' -Encoding ascii -ErrorAction SilentlyContinue
    }
    catch {}

    if ($null -ne $fixtureProcess) {
        try {
            $fixtureProcess.Refresh()
            if (-not $fixtureProcess.HasExited) {
                [void]$fixtureProcess.WaitForExit(5000)
                $fixtureProcess.Refresh()
            }
            if (-not $fixtureProcess.HasExited) {
                # Qualification-owned fixture only. Never enumerate/kill user apps.
                $fixtureProcess.Kill($true)
                $fixtureKilled = $true
                [void]$fixtureProcess.WaitForExit(5000)
            }
        }
        catch {
            if ($null -eq $result.error) {
                $result.error = "Fixture cleanup failed: $($_.Exception.Message)"
            }
        }
    }
    $result.fixture_killed = $fixtureKilled

    if (-not $KeepEnvironment -and (Test-Path -LiteralPath $venvDir)) {
        Remove-Item -LiteralPath $venvDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    $chromeAfter = @(Get-Process chrome -ErrorAction SilentlyContinue).Count
    $result.chrome_process_count_after = $chromeAfter
    $result.chrome_survival_pass = [bool]($chromeBefore -eq 0 -or $chromeAfter -gt 0)

    $result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $resultPath -Encoding utf8
}

Write-Host ''
Write-Host '===== STAGE 26.1B WINDOWS CAPTURE QUALIFICATION =====' -ForegroundColor Cyan
foreach ($name in @(
    'RESULT_PATH', 'PYTHON_VERSION', 'FLOW_INSTALLED_COMMIT', 'FLOW_INSTALLED_VERSION',
    'CAPTURE_INSTALLED_COMMIT', 'CAPTURE_INSTALLED_VERSION', 'DRIVER_PASS',
    'FLOW_EVENT_KINDS', 'STRUCTURAL_EVENT_COUNT', 'WINDOW_SCOPE_PASS',
    'REQUIRED_KINDS_PASS', 'EXPECTED_TEXT_PASS', 'EXPECTED_KEY_PASS',
    'UIA_EVIDENCE_PASS', 'FIXTURE_SEQUENCE_PASS', 'COMPILE_PASS',
    'REPLAY_EXECUTION', 'BOUNDED_REPLAY_REFUSAL', 'RAW_ARTIFACT_CONTAINMENT_PASS',
    'CHROME_PROCESS_COUNT_BEFORE', 'CHROME_PROCESS_COUNT_AFTER',
    'CHROME_SURVIVAL_PASS', 'FIXTURE_KILLED', 'ERROR'
)) {
    switch ($name) {
        'RESULT_PATH' { Write-Flag $name $resultPath }
        'PYTHON_VERSION' { Write-Flag $name $result.python_version }
        default { Write-Flag $name $result[$name.ToLower()] }
    }
}

$accepted = [bool](
    $result.driver_pass -and
    $result.raw_artifact_containment_pass -and
    $result.chrome_survival_pass -and
    $null -eq $result.error
)
if ($accepted) {
    Write-Flag 'STAGE26_1B_CAPTURE_RESULT' 'PASSED'
    exit 0
}
Write-Flag 'STAGE26_1B_CAPTURE_RESULT' 'FAILED'
exit 1
