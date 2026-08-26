[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ExpectedHead,
    [string]$OutputRoot = (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage26\windows-verification-qualification'),
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
$actualHead = (& git.exe -C $repoRoot rev-parse HEAD 2>$null | Select-Object -Last 1).Trim()
if (-not $actualHead) { throw 'Unable to resolve repository HEAD.' }
if ($actualHead -ne $ExpectedHead) {
    throw "EXACT_HEAD_MISMATCH expected=$ExpectedHead actual=$actualHead"
}

# Independent launcher-side preflight before any project Python qualification
# code runs. The reusable SourceProvenanceGate below repeats this check and
# additionally binds the critical local files to expected Git blobs + SHA-256.
$statusPorcelain = @(& git.exe -C $repoRoot status --porcelain=v1 --untracked-files=all 2>$null)
if ($LASTEXITCODE -ne 0) { throw 'Unable to inspect source working-tree status.' }
$statusPorcelain = @($statusPorcelain | Where-Object { $_ -and $_.Trim() })
if ($statusPorcelain.Count -ne 0) {
    throw "SOURCE_TREE_DIRTY before qualification: $($statusPorcelain -join ' | ')"
}

$sourceProvenanceGatePath = Join-Path $PSScriptRoot 'source-provenance-gate.py'
$driverPath = Join-Path $PSScriptRoot 'stage26-windows-verification-qualification.py'
$fixturePath = Join-Path $PSScriptRoot 'stage26-windows-hot-runtime-fixture.ps1'
$observationPath = Join-Path $repoRoot 'runtime\windows\observation.py'
$adapterPath = Join-Path $repoRoot 'runtime\control_plane\windows_observation.py'
$transitionPath = Join-Path $repoRoot 'runtime\control_plane\windows_transition.py'
foreach ($required in @($sourceProvenanceGatePath, $driverPath, $fixturePath, $observationPath, $adapterPath, $transitionPath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required Windows verification asset is missing: $required"
    }
}

$pythonExe = Join-Path $EnvironmentRoot 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    throw 'Persistent Stage 26 Windows runtime environment is missing. Run the accepted Stage 26.2A setup first.'
}

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$runDir = Join-Path $OutputRoot "windows-verification-$timestamp"
$sourceProvenancePath = Join-Path $runDir 'source-provenance.json'
$fixtureStatePath = Join-Path $runDir 'fixture-state.json'
$readyPath = Join-Path $runDir 'verifier-ready.txt'
$closePath = Join-Path $runDir 'fixture-close.txt'
$driverResultPath = Join-Path $runDir 'windows-verification-result.json'
$resultPath = Join-Path $runDir 'result.json'
$windowTitle = "Chat Agent Platform Stage 26.3B Windows Verification $timestamp"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$fixtureProcess = $null
$fixtureKilled = $false
$result = [ordered]@{
    schema_version = 1
    project_head = $actualHead
    source_provenance_pass = $false
    source_provenance_path = $sourceProvenancePath
    source_provenance = $null
    driver_pass = $false
    same_live_identity_pass = $false
    kernel_pass_status = $null
    kernel_pass_reason = $null
    wrong_postcondition_status = $null
    process_generation_drift_status = $null
    hwnd_drift_status = $null
    stale_observation_status = $null
    identity_drift_fail_pass = $false
    wrong_postcondition_fail_pass = $false
    stale_unknown_pass = $false
    resolver_stats = $null
    fixture_pid = $null
    fixture_killed = $false
    fixture_cleanup_pass = $false
    driver_error = $null
    error = $null
    result_dir = $runDir
}

try {
    Write-Host ''
    Write-Host '===== STAGE 26.3B WINDOWS SHARED-KERNEL VERIFICATION QUALIFICATION =====' -ForegroundColor Cyan
    Write-Host 'The fixture is observation-only for this gate; no Windows mutation is needed.' -ForegroundColor Yellow

    $criticalAssets = @(
        'scripts/source-provenance-gate.py',
        'scripts/stage26-windows-verification-qualification.ps1',
        'scripts/stage26-windows-verification-qualification.py',
        'scripts/stage26-windows-hot-runtime-fixture.ps1',
        'runtime/control_plane/__init__.py',
        'runtime/control_plane/verification.py',
        'runtime/control_plane/windows_observation.py',
        'runtime/control_plane/windows_transition.py',
        'runtime/windows/__init__.py',
        'runtime/windows/actuation.py',
        'runtime/windows/verifier.py',
        'runtime/windows/observation.py',
        'runtime/windows/window_scoped_uia.py'
    )
    $relevantLockfiles = @(
        'config/stage26-openadapt-lock.json'
    )
    $provenanceArgs = @(
        $sourceProvenanceGatePath,
        '--repo-root', $repoRoot,
        '--expected-head', $ExpectedHead,
        '--output', $sourceProvenancePath
    )
    foreach ($asset in $criticalAssets) { $provenanceArgs += @('--asset', $asset) }
    foreach ($lockfile in $relevantLockfiles) { $provenanceArgs += @('--lockfile', $lockfile) }

    & $pythonExe @provenanceArgs
    $provenanceExit = $LASTEXITCODE
    if (-not (Test-Path -LiteralPath $sourceProvenancePath -PathType Leaf)) {
        throw 'Source provenance result was not written.'
    }
    $provenance = Get-Content -LiteralPath $sourceProvenancePath -Raw -Encoding utf8 | ConvertFrom-Json
    $result.source_provenance = $provenance
    $result.source_provenance_pass = [bool](
        $provenanceExit -eq 0 -and
        [string]$provenance.status -eq 'pass' -and
        [bool]$provenance.working_tree_clean -and
        [bool]$provenance.tracked_diff_empty -and
        [bool]$provenance.untracked_empty -and
        [string]$provenance.actual_head -eq $ExpectedHead
    )
    if (-not $result.source_provenance_pass) {
        throw "SOURCE_PROVENANCE_GATE failed: $([string]$provenance.reason)"
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
        throw 'Windows verification driver result is missing.'
    }
    $driver = Get-Content -LiteralPath $driverResultPath -Raw -Encoding utf8 | ConvertFrom-Json
    $result.driver_pass = [bool]$driver.pass
    $result.same_live_identity_pass = [bool]$driver.same_live_identity_pass
    $result.kernel_pass_status = [string]$driver.kernel_pass_status
    $result.kernel_pass_reason = [string]$driver.kernel_pass_reason
    $result.wrong_postcondition_status = [string]$driver.wrong_postcondition_status
    $result.process_generation_drift_status = [string]$driver.process_generation_drift_status
    $result.hwnd_drift_status = [string]$driver.hwnd_drift_status
    $result.stale_observation_status = [string]$driver.stale_observation_status
    $result.identity_drift_fail_pass = [bool]$driver.identity_drift_fail_pass
    $result.wrong_postcondition_fail_pass = [bool]$driver.wrong_postcondition_fail_pass
    $result.stale_unknown_pass = [bool]$driver.stale_unknown_pass
    $result.resolver_stats = $driver.resolver_stats
    $result.driver_error = $driver.error

    if ($driverExit -ne 0 -or -not $result.driver_pass) {
        $detail = if ($driver.error) { [string]$driver.error } else { "driver exit $driverExit" }
        throw "Stage 26.3B Windows verification qualification failed: $detail"
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
    $result | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $resultPath -Encoding utf8
}

$resolverStatsPass = [bool](
    $null -ne $result.resolver_stats -and
    $result.resolver_stats.desktop_fallback_calls -eq 0 -and
    $result.resolver_stats.window_binding_failures -eq 0 -and
    $result.resolver_stats.window_binding_ambiguities -eq 0
)
$accepted = [bool](
    $result.source_provenance_pass -and
    $result.driver_pass -and
    $result.same_live_identity_pass -and
    $result.kernel_pass_status -eq 'pass' -and
    $result.kernel_pass_reason -eq 'expected_effect_verified' -and
    $result.wrong_postcondition_status -eq 'fail' -and
    $result.process_generation_drift_status -eq 'fail' -and
    $result.hwnd_drift_status -eq 'fail' -and
    $result.stale_observation_status -eq 'unknown' -and
    $result.identity_drift_fail_pass -and
    $result.wrong_postcondition_fail_pass -and
    $result.stale_unknown_pass -and
    $resolverStatsPass -and
    $result.fixture_cleanup_pass -and
    $null -eq $result.error
)

Write-Host ''
Write-Host '===== STAGE 26.3B WINDOWS VERIFICATION RESULT =====' -ForegroundColor Cyan
Write-Flag 'RESULT_PATH' $resultPath
Write-Flag 'EXACT_HEAD' $result.project_head
Write-Flag 'SOURCE_PROVENANCE_PATH' $result.source_provenance_path
Write-Flag 'SOURCE_PROVENANCE_GATE' $(if ($result.source_provenance_pass) { 'PASS' } else { 'FAIL' })
if ($null -ne $result.source_provenance) {
    Write-Flag 'WORKING_TREE_CLEAN' $result.source_provenance.working_tree_clean
    Write-Flag 'TRACKED_DIFF_EMPTY' $result.source_provenance.tracked_diff_empty
    Write-Flag 'UNTRACKED_EMPTY' $result.source_provenance.untracked_empty
}
Write-Flag 'FIXTURE_PID' $result.fixture_pid
Write-Flag 'SAME_LIVE_IDENTITY_PASS' $result.same_live_identity_pass
Write-Flag 'KERNEL_PASS_STATUS' $result.kernel_pass_status
Write-Flag 'KERNEL_PASS_REASON' $result.kernel_pass_reason
Write-Flag 'WRONG_POSTCONDITION_STATUS' $result.wrong_postcondition_status
Write-Flag 'PROCESS_GENERATION_DRIFT_STATUS' $result.process_generation_drift_status
Write-Flag 'HWND_DRIFT_STATUS' $result.hwnd_drift_status
Write-Flag 'STALE_OBSERVATION_STATUS' $result.stale_observation_status
Write-Flag 'IDENTITY_DRIFT_FAIL_PASS' $result.identity_drift_fail_pass
Write-Flag 'WRONG_POSTCONDITION_FAIL_PASS' $result.wrong_postcondition_fail_pass
Write-Flag 'STALE_UNKNOWN_PASS' $result.stale_unknown_pass
if ($null -ne $result.resolver_stats) {
    foreach ($property in @($result.resolver_stats.PSObject.Properties | Sort-Object Name)) {
        Write-Flag ($property.Name.ToUpperInvariant()) $property.Value
    }
}
Write-Flag 'FIXTURE_KILLED' $result.fixture_killed
Write-Flag 'FIXTURE_CLEANUP_PASS' $result.fixture_cleanup_pass
Write-Flag 'DRIVER_ERROR' $result.driver_error
Write-Flag 'ERROR' $result.error
Write-Flag 'STAGE26_3B_WINDOWS_VERIFICATION_RESULT' $(if ($accepted) { 'PASSED' } else { 'FAILED' })

if (-not $accepted) { exit 1 }
exit 0
