[CmdletBinding()]
param(
    [string]$OutputRoot = (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage26\real-app-e2e'),
    [string]$EnvironmentRoot = (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage26\hot-runtime-env')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Flag {
    param([Parameter(Mandatory = $true)][string]$Name, [AllowNull()]$Value)
    $rendered = if ($null -eq $Value) { '<null>' } else { [string]$Value }
    Write-Host ("{0}={1}" -f $Name, $rendered)
}

function Test-DisposableRoot {
    param([Parameter(Mandatory = $true)][string]$Path)

    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
    $candidate = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    if ([string]::Equals($candidate, $tempRoot, [StringComparison]::OrdinalIgnoreCase)) {
        return $false
    }
    $prefix = $tempRoot + '\'
    if (-not $candidate.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        return $false
    }
    return ([IO.Path]::GetFileName($candidate) -like 'chat-agent-stage26e-vscode-*')
}

function Remove-DisposableRoot {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-DisposableRoot -Path $Path)) {
        throw "Refusing recursive cleanup outside the bounded Stage 26.2E TEMP root: $Path"
    }
    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
    }
}

function Resolve-VSCodeExecutable {
    $candidates = [System.Collections.Generic.List[string]]::new()

    $direct = Get-Command Code.exe -ErrorAction SilentlyContinue
    if ($null -ne $direct -and $direct.Source) {
        [void]$candidates.Add([string]$direct.Source)
    }

    $cli = Get-Command code.cmd -ErrorAction SilentlyContinue
    if ($null -ne $cli -and $cli.Source) {
        $binDir = Split-Path -Parent ([string]$cli.Source)
        $installDir = Split-Path -Parent $binDir
        [void]$candidates.Add((Join-Path $installDir 'Code.exe'))
    }

    foreach ($path in @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Microsoft VS Code\Code.exe'),
        (Join-Path $env:ProgramFiles 'Microsoft VS Code\Code.exe'),
        $(if (${env:ProgramFiles(x86)}) { Join-Path ${env:ProgramFiles(x86)} 'Microsoft VS Code\Code.exe' } else { $null })
    )) {
        if ($path) { [void]$candidates.Add([string]$path) }
    }

    foreach ($candidate in @($candidates | Select-Object -Unique)) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return $null
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$driverPath = Join-Path $PSScriptRoot 'stage26-vscode-real-app-e2e.py'
$observationPath = Join-Path $repoRoot 'runtime\windows\observation.py'
$actuationPath = Join-Path $repoRoot 'runtime\windows\actuation.py'
$verifierPath = Join-Path $repoRoot 'runtime\windows\verifier.py'
$guardPath = Join-Path $repoRoot 'runtime\windows\native_point_guard.py'
$resolverPath = Join-Path $repoRoot 'runtime\windows\window_scoped_uia.py'
foreach ($required in @($driverPath, $observationPath, $actuationPath, $verifierPath, $guardPath, $resolverPath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required Stage 26.2E asset is missing: $required"
    }
}

$pythonExe = Join-Path $EnvironmentRoot 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
    throw 'Persistent Stage 26 Windows runtime environment is missing. Run the accepted Stage 26.2A setup first.'
}

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$runDir = Join-Path $OutputRoot "vscode-$timestamp"
$appRoot = Join-Path $env:TEMP ("chat-agent-stage26e-vscode-" + [guid]::NewGuid().ToString('N'))
$driverResultPath = Join-Path $runDir 'vscode-real-app-result.json'
$resultPath = Join-Path $runDir 'result.json'
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$codeExe = Resolve-VSCodeExecutable
$result = [ordered]@{
    schema_version = 3
    qualification_kind = 'real-application-vscode-disposable-text-edit'
    project_head = $null
    code_exe = $codeExe
    app_root = $appRoot
    temp_containment_pass = $false
    application_discovery_pass = $false
    driver_pass = $false
    isolated_profile_pass = $false
    disposable_workspace_pass = $false
    window_binding_pass = $false
    desktop_observation_pass = $false
    focused_editor_precondition_pass = $false
    fresh_pre_action_state_pass = $false
    native_point_guard_pass = $false
    agent_loopback_pass = $false
    agent_auth_required_pass = $false
    legacy_capability_absent_pass = $false
    baseline_verification_status = $null
    mismatch_probe_verification_status = $null
    mismatch_probe_decision = $null
    mismatch_probe_zero_action_pass = $false
    guarded_keyboard_delivery_pass = $false
    keyboard_action_count = $null
    completion_verification_status = $null
    completion_verification_pass = $false
    current_state_verification_pass = $false
    workspace_expected_only_pass = $false
    application_cleanup_pass = $false
    cli_process_exit_pass = $false
    forced_cli_cleanup = $false
    app_root_cleanup_pass = $false
    rollback_pass = $false
    driver_source_sha256 = (Get-FileHash -LiteralPath $driverPath -Algorithm SHA256).Hash.ToLowerInvariant()
    observation_source_sha256 = (Get-FileHash -LiteralPath $observationPath -Algorithm SHA256).Hash.ToLowerInvariant()
    actuation_source_sha256 = (Get-FileHash -LiteralPath $actuationPath -Algorithm SHA256).Hash.ToLowerInvariant()
    verifier_source_sha256 = (Get-FileHash -LiteralPath $verifierPath -Algorithm SHA256).Hash.ToLowerInvariant()
    native_point_guard_source_sha256 = (Get-FileHash -LiteralPath $guardPath -Algorithm SHA256).Hash.ToLowerInvariant()
    resolver_source_sha256 = (Get-FileHash -LiteralPath $resolverPath -Algorithm SHA256).Hash.ToLowerInvariant()
    resolver_stats = $null
    driver_error = $null
    error = $null
    result_dir = $runDir
}

try {
    $result.project_head = (& git.exe -C $repoRoot rev-parse HEAD 2>$null | Select-Object -Last 1).Trim()
    $result.temp_containment_pass = Test-DisposableRoot -Path $appRoot
    if (-not $result.temp_containment_pass) {
        throw 'Generated Stage 26.2E application root is outside the bounded TEMP namespace.'
    }

    $result.application_discovery_pass = [bool](
        $codeExe -and
        (Test-Path -LiteralPath $codeExe -PathType Leaf) -and
        ([IO.Path]::GetFileName($codeExe) -ieq 'Code.exe')
    )
    if (-not $result.application_discovery_pass) {
        throw 'VS Code Code.exe was not found in PATH or standard install locations.'
    }

    Write-Host ''
    Write-Host '===== STAGE 26.2E VS CODE REAL APPLICATION E2E =====' -ForegroundColor Cyan
    Write-Host 'This run opens an isolated VS Code profile and a disposable file under TEMP.' -ForegroundColor Yellow
    Write-Host 'It may type one unique marker into that disposable file after all guards pass.' -ForegroundColor Yellow
    Write-Host 'Do not switch windows, type, click, or cover the isolated VS Code window during the run.' -ForegroundColor Yellow

    & $pythonExe $driverPath `
        '--run-dir' $runDir `
        '--app-root' $appRoot `
        '--code-exe' $codeExe
    $driverExit = $LASTEXITCODE

    if (-not (Test-Path -LiteralPath $driverResultPath -PathType Leaf)) {
        throw 'Stage 26.2E driver result is missing.'
    }
    $driver = Get-Content -LiteralPath $driverResultPath -Raw -Encoding utf8 | ConvertFrom-Json
    $result.driver_pass = [bool]$driver.pass
    foreach ($name in @(
        'temp_containment_pass', 'isolated_profile_pass', 'disposable_workspace_pass',
        'window_binding_pass', 'desktop_observation_pass', 'focused_editor_precondition_pass',
        'fresh_pre_action_state_pass', 'native_point_guard_pass', 'agent_loopback_pass',
        'agent_auth_required_pass', 'legacy_capability_absent_pass', 'mismatch_probe_zero_action_pass',
        'guarded_keyboard_delivery_pass', 'completion_verification_pass',
        'current_state_verification_pass', 'workspace_expected_only_pass',
        'application_cleanup_pass', 'cli_process_exit_pass', 'forced_cli_cleanup',
        'app_root_cleanup_pass', 'rollback_pass'
    )) {
        $result[$name] = [bool]$driver.$name
    }
    foreach ($name in @(
        'baseline_verification_status', 'mismatch_probe_verification_status',
        'mismatch_probe_decision', 'keyboard_action_count', 'completion_verification_status',
        'resolver_stats'
    )) {
        $result[$name] = $driver.$name
    }
    $result.driver_error = $driver.error

    if ($driverExit -ne 0 -or -not $result.driver_pass) {
        $detail = if ($driver.error) { [string]$driver.error } else { "driver exit $driverExit" }
        throw "Stage 26.2E VS Code qualification failed: $detail"
    }
}
catch {
    $result.error = $_.Exception.Message
}
finally {
    try {
        Remove-DisposableRoot -Path $appRoot
    }
    catch {
        if ($null -eq $result.error) {
            $result.error = "Outer disposable-root cleanup failed: $($_.Exception.Message)"
        }
    }
    $result.app_root_cleanup_pass = -not (Test-Path -LiteralPath $appRoot)
    $result.rollback_pass = [bool](
        $result.application_cleanup_pass -and
        $result.cli_process_exit_pass -and
        -not $result.forced_cli_cleanup -and
        $result.app_root_cleanup_pass
    )
    $result | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $resultPath -Encoding utf8
}

Write-Host ''
Write-Host '===== STAGE 26.2E VS CODE REAL APPLICATION E2E RESULT =====' -ForegroundColor Cyan
foreach ($name in @(
    'RESULT_PATH','PROJECT_HEAD','CODE_EXE','APP_ROOT','TEMP_CONTAINMENT_PASS',
    'APPLICATION_DISCOVERY_PASS','DRIVER_PASS','ISOLATED_PROFILE_PASS','DISPOSABLE_WORKSPACE_PASS',
    'WINDOW_BINDING_PASS','DESKTOP_OBSERVATION_PASS','FOCUSED_EDITOR_PRECONDITION_PASS',
    'FRESH_PRE_ACTION_STATE_PASS','NATIVE_POINT_GUARD_PASS','AGENT_LOOPBACK_PASS',
    'AGENT_AUTH_REQUIRED_PASS','LEGACY_CAPABILITY_ABSENT_PASS','BASELINE_VERIFICATION_STATUS',
    'MISMATCH_PROBE_VERIFICATION_STATUS','MISMATCH_PROBE_DECISION','MISMATCH_PROBE_ZERO_ACTION_PASS',
    'GUARDED_KEYBOARD_DELIVERY_PASS','KEYBOARD_ACTION_COUNT','COMPLETION_VERIFICATION_STATUS',
    'COMPLETION_VERIFICATION_PASS','CURRENT_STATE_VERIFICATION_PASS','WORKSPACE_EXPECTED_ONLY_PASS',
    'APPLICATION_CLEANUP_PASS','CLI_PROCESS_EXIT_PASS','FORCED_CLI_CLEANUP','APP_ROOT_CLEANUP_PASS',
    'ROLLBACK_PASS','DRIVER_SOURCE_SHA256','OBSERVATION_SOURCE_SHA256','ACTUATION_SOURCE_SHA256',
    'VERIFIER_SOURCE_SHA256','NATIVE_POINT_GUARD_SOURCE_SHA256','RESOLVER_SOURCE_SHA256',
    'DRIVER_ERROR','ERROR'
)) {
    switch ($name) {
        'RESULT_PATH' { Write-Flag $name $resultPath }
        default { Write-Flag $name $result[$name.ToLowerInvariant()] }
    }
}
if ($null -ne $result.resolver_stats) {
    foreach ($property in @($result.resolver_stats.PSObject.Properties | Sort-Object Name)) {
        Write-Flag ($property.Name.ToUpperInvariant()) $property.Value
    }
}

$accepted = [bool](
    $result.temp_containment_pass -and
    $result.application_discovery_pass -and
    $result.driver_pass -and
    $result.isolated_profile_pass -and
    $result.disposable_workspace_pass -and
    $result.window_binding_pass -and
    $result.desktop_observation_pass -and
    $result.focused_editor_precondition_pass -and
    $result.fresh_pre_action_state_pass -and
    $result.native_point_guard_pass -and
    $result.agent_loopback_pass -and
    $result.agent_auth_required_pass -and
    $result.legacy_capability_absent_pass -and
    [string]$result.baseline_verification_status -eq 'pass' -and
    [string]$result.mismatch_probe_verification_status -eq 'fail' -and
    [string]$result.mismatch_probe_decision -eq 'abstain' -and
    $result.mismatch_probe_zero_action_pass -and
    $result.guarded_keyboard_delivery_pass -and
    [int]$result.keyboard_action_count -eq 1 -and
    [string]$result.completion_verification_status -eq 'pass' -and
    $result.completion_verification_pass -and
    $result.current_state_verification_pass -and
    $result.workspace_expected_only_pass -and
    $result.application_cleanup_pass -and
    $result.cli_process_exit_pass -and
    -not $result.forced_cli_cleanup -and
    $result.app_root_cleanup_pass -and
    $result.rollback_pass -and
    $null -eq $result.error
)
if ($accepted) {
    Write-Flag 'STAGE26_2E_REAL_APPLICATION_E2E_RESULT' 'PASSED'
    exit 0
}
Write-Flag 'STAGE26_2E_REAL_APPLICATION_E2E_RESULT' 'FAILED'
exit 1
