[CmdletBinding()]
param(
    [string]$OutputRoot = (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage26\desktop-grounder-qualification'),
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
$driverPath = Join-Path $PSScriptRoot 'stage26-desktop-grounder-qualification.py'
$grounderPath = Join-Path $repoRoot 'runtime\windows\grounder.py'
$observationPath = Join-Path $repoRoot 'runtime\windows\observation.py'
$resolverPath = Join-Path $repoRoot 'runtime\windows\window_scoped_uia.py'
$fixturePath = Join-Path $PSScriptRoot 'stage26-windows-hot-runtime-fixture.ps1'
$visionRuntimePath = Join-Path $PSScriptRoot 'local-vision-runtime.ps1'
foreach ($required in @($driverPath, $grounderPath, $observationPath, $resolverPath, $fixturePath, $visionRuntimePath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required Stage 26.2C asset is missing: $required"
    }
}

$pythonExe = Join-Path $EnvironmentRoot 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    throw 'Persistent Stage 26 Windows runtime environment is missing. Run the accepted Stage 26.2A setup first.'
}

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$runDir = Join-Path $OutputRoot "grounder-$timestamp"
$fixtureStatePath = Join-Path $runDir 'fixture-state.json'
$readyPath = Join-Path $runDir 'grounder-ready.txt'
$closePath = Join-Path $runDir 'fixture-close.txt'
$driverResultPath = Join-Path $runDir 'desktop-grounder-result.json'
$resultPath = Join-Path $runDir 'result.json'
$windowTitle = "Chat Agent Platform Stage 26.2C Desktop Grounder $timestamp"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$fixtureProcess = $null
$fixtureKilled = $false
$visionStartedByHarness = $false
$visionRestored = $false
$visionStatusBefore = $null
$visionStatusDuring = $null

$result = [ordered]@{
    schema_version = 1
    project_head = $null
    production_grounder_path = $grounderPath
    production_observation_path = $observationPath
    production_resolver_path = $resolverPath
    vision_profile = $null
    vision_port = $null
    vision_started_by_harness = $false
    vision_ready_pass = $false
    vision_restored_pass = $false
    driver_pass = $false
    same_frame_binding_pass = $false
    coordinate_contract_pass = $false
    target_point_inside_uia_pass = $false
    target_evidence_binding_pass = $false
    absent_target_abstain_pass = $false
    stale_frame_rejection_pass = $false
    proposal_only_contract_pass = $false
    observer_source_sha256 = $null
    grounder_source_sha256 = $null
    driver_source_sha256 = $null
    proposal = $null
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
    Write-Host '===== STAGE 26.2C DESKTOP GROUNDER QUALIFICATION =====' -ForegroundColor Cyan
    Write-Host 'Proposal-only: exact-window pixels -> bounded proposal. No click/type/scroll is invoked.' -ForegroundColor Yellow

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
        throw 'Desktop grounder driver result is missing.'
    }
    $driver = Get-Content -LiteralPath $driverResultPath -Raw -Encoding utf8 | ConvertFrom-Json
    $result.driver_pass = [bool]$driver.pass
    $result.same_frame_binding_pass = [bool]$driver.same_frame_binding_pass
    $result.coordinate_contract_pass = [bool]$driver.coordinate_contract_pass
    $result.target_point_inside_uia_pass = [bool]$driver.target_point_inside_uia_pass
    $result.target_evidence_binding_pass = [bool]$driver.target_evidence_binding_pass
    $result.absent_target_abstain_pass = [bool]$driver.absent_target_abstain_pass
    $result.stale_frame_rejection_pass = [bool]$driver.stale_frame_rejection_pass
    $result.proposal_only_contract_pass = [bool]$driver.proposal_only_contract_pass
    $result.observer_source_sha256 = [string]$driver.observer_source_sha256
    $result.grounder_source_sha256 = [string]$driver.grounder_source_sha256
    $result.driver_source_sha256 = [string]$driver.driver_source_sha256
    $result.proposal = $driver.proposal
    $result.resolver_stats = $driver.resolver_stats
    $result.driver_error = $driver.error

    if ($driverExit -ne 0 -or -not $result.driver_pass) {
        $detail = if ($driver.error) { [string]$driver.error } else { "driver exit $driverExit" }
        throw "Stage 26.2C desktop grounder qualification failed: $detail"
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
    $result | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $resultPath -Encoding utf8
}

Write-Host ''
Write-Host '===== STAGE 26.2C DESKTOP GROUNDER RESULT =====' -ForegroundColor Cyan
Write-Flag 'RESULT_PATH' $resultPath
Write-Flag 'PROJECT_HEAD' $result.project_head
Write-Flag 'PRODUCTION_GROUNDER_PATH' $result.production_grounder_path
Write-Flag 'VISION_PROFILE' $result.vision_profile
Write-Flag 'VISION_PORT' $result.vision_port
Write-Flag 'VISION_STARTED_BY_HARNESS' $result.vision_started_by_harness
Write-Flag 'VISION_READY_PASS' $result.vision_ready_pass
Write-Flag 'VISION_RESTORED_PASS' $result.vision_restored_pass
Write-Flag 'SAME_FRAME_BINDING_PASS' $result.same_frame_binding_pass
Write-Flag 'COORDINATE_CONTRACT_PASS' $result.coordinate_contract_pass
Write-Flag 'TARGET_POINT_INSIDE_UIA_PASS' $result.target_point_inside_uia_pass
Write-Flag 'TARGET_EVIDENCE_BINDING_PASS' $result.target_evidence_binding_pass
Write-Flag 'ABSENT_TARGET_ABSTAIN_PASS' $result.absent_target_abstain_pass
Write-Flag 'STALE_FRAME_REJECTION_PASS' $result.stale_frame_rejection_pass
Write-Flag 'PROPOSAL_ONLY_CONTRACT_PASS' $result.proposal_only_contract_pass
if ($null -ne $result.resolver_stats) {
    foreach ($property in @($result.resolver_stats.PSObject.Properties | Sort-Object Name)) {
        Write-Flag ($property.Name.ToUpperInvariant()) $property.Value
    }
}
Write-Flag 'FIXTURE_KILLED' $result.fixture_killed
Write-Flag 'FIXTURE_CLEANUP_PASS' $result.fixture_cleanup_pass
Write-Flag 'DRIVER_ERROR' $result.driver_error
Write-Flag 'ERROR' $result.error

$accepted = [bool](
    $result.vision_ready_pass -and
    $result.vision_restored_pass -and
    $result.driver_pass -and
    $result.same_frame_binding_pass -and
    $result.coordinate_contract_pass -and
    $result.target_point_inside_uia_pass -and
    $result.target_evidence_binding_pass -and
    $result.absent_target_abstain_pass -and
    $result.stale_frame_rejection_pass -and
    $result.proposal_only_contract_pass -and
    $result.resolver_stats.desktop_fallback_calls -eq 0 -and
    $result.resolver_stats.window_binding_failures -eq 0 -and
    $result.resolver_stats.window_binding_ambiguities -eq 0 -and
    $result.fixture_cleanup_pass -and
    $null -eq $result.error
)
if ($accepted) {
    Write-Flag 'STAGE26_2C_DESKTOP_GROUNDER_RESULT' 'PASSED'
    exit 0
}
Write-Flag 'STAGE26_2C_DESKTOP_GROUNDER_RESULT' 'FAILED'
exit 1
