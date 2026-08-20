[CmdletBinding()]
param(
    [string]$OutputRoot = (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage26\desktop-routing-qualification'),
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

function Invoke-VisionRuntimeJson {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][ValidateSet('Start','Stop','Status','Touch')][string]$Action
    )
    try {
        $raw = @(& $Path -Action $Action 2>&1)
    }
    catch {
        throw "Vision runtime $Action failed: $($_.Exception.Message)"
    }
    return (($raw -join [Environment]::NewLine) | ConvertFrom-Json)
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$driverPath = Join-Path $PSScriptRoot 'stage26-desktop-routing-qualification.py'
$routerPath = Join-Path $repoRoot 'runtime\windows\routing.py'
$guardPath = Join-Path $repoRoot 'runtime\windows\native_point_guard.py'
$grounderPath = Join-Path $repoRoot 'runtime\windows\grounder.py'
$observationPath = Join-Path $repoRoot 'runtime\windows\observation.py'
$actuationPath = Join-Path $repoRoot 'runtime\windows\actuation.py'
$resolverPath = Join-Path $repoRoot 'runtime\windows\window_scoped_uia.py'
$fixturePath = Join-Path $PSScriptRoot 'stage26-windows-hot-runtime-fixture.ps1'
$visionRuntimePath = Join-Path $PSScriptRoot 'local-vision-runtime.ps1'
foreach ($required in @(
    $driverPath, $routerPath, $guardPath, $grounderPath, $observationPath,
    $actuationPath, $resolverPath, $fixturePath, $visionRuntimePath
)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required Stage 26.2D asset is missing: $required"
    }
}

$pythonExe = Join-Path $EnvironmentRoot 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    throw 'Persistent Stage 26 Windows runtime environment is missing. Run the accepted Stage 26.2A setup first.'
}

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$runDir = Join-Path $OutputRoot "routing-$timestamp"
$fixtureStatePath = Join-Path $runDir 'fixture-state.json'
$readyPath = Join-Path $runDir 'routing-ready.txt'
$closePath = Join-Path $runDir 'fixture-close.txt'
$driverResultPath = Join-Path $runDir 'desktop-routing-result.json'
$resultPath = Join-Path $runDir 'result.json'
$windowTitle = "Chat Agent Platform Stage 26.2D Routing $timestamp"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$fixtureProcess = $null
$fixtureKilled = $false
$visionStartedByHarness = $false
$visionRestored = $false

$result = [ordered]@{
    schema_version = 2
    project_head = $null
    production_router_path = $routerPath
    production_native_point_guard_path = $guardPath
    production_grounder_path = $grounderPath
    production_observation_path = $observationPath
    production_actuation_path = $actuationPath
    production_resolver_path = $resolverPath
    vision_profile = $null
    vision_port = $null
    vision_started_by_harness = $false
    vision_ready_pass = $false
    vision_restored_pass = $false
    driver_pass = $false
    agent_loopback_pass = $false
    agent_auth_required_pass = $false
    legacy_capability_absent_pass = $false
    native_point_guard_preflight_pass = $false
    native_point_guard_wrong_window_refusal_pass = $false
    native_point_guard_delivery_pass = $false
    vision_disabled_abstain_pass = $false
    role_conflict_abstain_pass = $false
    negative_zero_action_pass = $false
    positive_visual_route_pass = $false
    fresh_reobservation_pass = $false
    guarded_click_receipt_pass = $false
    fixture_start_postcondition_pass = $false
    fixture_no_extra_mutation_pass = $false
    single_action_pass = $false
    structural_executor_calls = $null
    coordinate_executor_calls = $null
    grounder_calls = $null
    router_source_sha256 = $null
    native_point_guard_source_sha256 = $null
    observer_source_sha256 = $null
    grounder_source_sha256 = $null
    actuation_source_sha256 = $null
    driver_source_sha256 = $null
    screenshot_paths = $null
    screenshot_sha256 = $null
    resolver_stats = $null
    fixture_pid = $null
    fixture_killed = $false
    fixture_cleanup_pass = $false
    driver_error = $null
    error = $null
    result_dir = $runDir
}

try {
    $result.project_head = (& git.exe -C $repoRoot rev-parse HEAD 2>$null | Select-Object -Last 1).Trim()

    Write-Host ''
    Write-Host '===== STAGE 26.2D WINDOWS VISION ROUTING QUALIFICATION =====' -ForegroundColor Cyan
    Write-Host 'One guarded visual fallback click after fresh exact-window re-observation.' -ForegroundColor Yellow
    Write-Host 'Foreground/hit-test guard is checked before any coordinate mutation.' -ForegroundColor Yellow
    Write-Host 'Do not move, cover, click or type into the fixture during the run.' -ForegroundColor Yellow

    $visionStatusBefore = Invoke-VisionRuntimeJson -Path $visionRuntimePath -Action 'Status'
    if ([bool]$visionStatusBefore.conflict) {
        throw 'Vision runtime ownership conflict; refusing qualification.'
    }
    if (-not [bool]$visionStatusBefore.ready) {
        $visionStatusDuring = Invoke-VisionRuntimeJson -Path $visionRuntimePath -Action 'Start'
        $visionStartedByHarness = $true
    }
    else {
        $visionStatusDuring = Invoke-VisionRuntimeJson -Path $visionRuntimePath -Action 'Touch'
    }
    $result.vision_started_by_harness = $visionStartedByHarness
    $result.vision_profile = [string]$visionStatusDuring.profile
    $result.vision_port = [int]$visionStatusDuring.port
    $result.vision_ready_pass = [bool](
        [bool]$visionStatusDuring.ready -and
        -not [bool]$visionStatusDuring.conflict -and
        [string]$visionStatusDuring.profile -eq 'lfm25-vl-450m-f16' -and
        [int]$visionStatusDuring.port -eq 3068
    )
    if (-not $result.vision_ready_pass) {
        throw 'Reviewed local vision runtime is not ready on the expected profile/port.'
    }

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
        throw 'Desktop routing driver result is missing.'
    }
    $driver = Get-Content -LiteralPath $driverResultPath -Raw -Encoding utf8 | ConvertFrom-Json
    $result.driver_pass = [bool]$driver.pass
    foreach ($name in @(
        'agent_loopback_pass', 'agent_auth_required_pass', 'legacy_capability_absent_pass',
        'native_point_guard_preflight_pass', 'native_point_guard_wrong_window_refusal_pass',
        'native_point_guard_delivery_pass', 'vision_disabled_abstain_pass',
        'role_conflict_abstain_pass', 'negative_zero_action_pass', 'positive_visual_route_pass',
        'fresh_reobservation_pass', 'guarded_click_receipt_pass',
        'fixture_start_postcondition_pass', 'fixture_no_extra_mutation_pass', 'single_action_pass'
    )) {
        $result[$name] = [bool]$driver.$name
    }
    foreach ($name in @(
        'structural_executor_calls', 'coordinate_executor_calls', 'grounder_calls',
        'router_source_sha256', 'native_point_guard_source_sha256', 'observer_source_sha256',
        'grounder_source_sha256', 'actuation_source_sha256', 'driver_source_sha256',
        'screenshot_paths', 'screenshot_sha256', 'resolver_stats'
    )) {
        $result[$name] = $driver.$name
    }
    $result.driver_error = $driver.error

    if ($driverExit -ne 0 -or -not $result.driver_pass) {
        $detail = if ($driver.error) { [string]$driver.error } else { "driver exit $driverExit" }
        throw "Stage 26.2D routing qualification failed: $detail"
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

    try {
        if ($visionStartedByHarness) {
            $after = Invoke-VisionRuntimeJson -Path $visionRuntimePath -Action 'Stop'
            $visionRestored = -not [bool]$after.running
        }
        else {
            $after = Invoke-VisionRuntimeJson -Path $visionRuntimePath -Action 'Touch'
            $visionRestored = [bool]$after.ready
        }
    }
    catch {
        if ($null -eq $result.error) { $result.error = "Vision runtime restore failed: $($_.Exception.Message)" }
    }
    $result.vision_restored_pass = $visionRestored
    $result | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $resultPath -Encoding utf8
}

Write-Host ''
Write-Host '===== STAGE 26.2D WINDOWS VISION ROUTING RESULT =====' -ForegroundColor Cyan
foreach ($name in @(
    'RESULT_PATH','PROJECT_HEAD','VISION_PROFILE','VISION_PORT','VISION_STARTED_BY_HARNESS',
    'VISION_READY_PASS','VISION_RESTORED_PASS','AGENT_LOOPBACK_PASS','AGENT_AUTH_REQUIRED_PASS',
    'LEGACY_CAPABILITY_ABSENT_PASS','NATIVE_POINT_GUARD_PREFLIGHT_PASS',
    'NATIVE_POINT_GUARD_WRONG_WINDOW_REFUSAL_PASS','NATIVE_POINT_GUARD_DELIVERY_PASS',
    'VISION_DISABLED_ABSTAIN_PASS','ROLE_CONFLICT_ABSTAIN_PASS','NEGATIVE_ZERO_ACTION_PASS',
    'POSITIVE_VISUAL_ROUTE_PASS','FRESH_REOBSERVATION_PASS','GUARDED_CLICK_RECEIPT_PASS',
    'FIXTURE_START_POSTCONDITION_PASS','FIXTURE_NO_EXTRA_MUTATION_PASS','SINGLE_ACTION_PASS',
    'STRUCTURAL_EXECUTOR_CALLS','COORDINATE_EXECUTOR_CALLS','GROUNDER_CALLS',
    'NATIVE_POINT_GUARD_SOURCE_SHA256','FIXTURE_KILLED','FIXTURE_CLEANUP_PASS','DRIVER_ERROR','ERROR'
)) {
    switch ($name) {
        'RESULT_PATH' { Write-Flag $name $resultPath }
        default {
            $key = $name.ToLowerInvariant()
            Write-Flag $name $result[$key]
        }
    }
}
if ($null -ne $result.resolver_stats) {
    foreach ($property in @($result.resolver_stats.PSObject.Properties | Sort-Object Name)) {
        Write-Flag ($property.Name.ToUpperInvariant()) $property.Value
    }
}
Write-Flag 'SCREENSHOT_SHA256_JSON' (($result.screenshot_sha256 | ConvertTo-Json -Compress))

$accepted = [bool](
    $result.vision_ready_pass -and
    $result.vision_restored_pass -and
    $result.driver_pass -and
    $result.agent_loopback_pass -and
    $result.agent_auth_required_pass -and
    $result.legacy_capability_absent_pass -and
    $result.native_point_guard_preflight_pass -and
    $result.native_point_guard_wrong_window_refusal_pass -and
    $result.native_point_guard_delivery_pass -and
    $result.vision_disabled_abstain_pass -and
    $result.role_conflict_abstain_pass -and
    $result.negative_zero_action_pass -and
    $result.positive_visual_route_pass -and
    $result.fresh_reobservation_pass -and
    $result.guarded_click_receipt_pass -and
    $result.fixture_start_postcondition_pass -and
    $result.fixture_no_extra_mutation_pass -and
    $result.single_action_pass -and
    $result.resolver_stats.desktop_fallback_calls -eq 0 -and
    $result.resolver_stats.window_binding_failures -eq 0 -and
    $result.resolver_stats.window_binding_ambiguities -eq 0 -and
    $result.fixture_cleanup_pass -and
    $null -eq $result.error
)
if ($accepted) {
    Write-Flag 'STAGE26_2D_WINDOWS_VISION_ROUTING_RESULT' 'PASSED'
    exit 0
}
Write-Flag 'STAGE26_2D_WINDOWS_VISION_ROUTING_RESULT' 'FAILED'
exit 1
