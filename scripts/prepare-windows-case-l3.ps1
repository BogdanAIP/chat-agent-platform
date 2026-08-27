[CmdletBinding()]
param(
    [string]$SourceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$ExpectedHead = '',
    [switch]$SkipBootstrap
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Utf8NoBom {
    param([Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][string]$Content)
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-InstalledAssetRecord {
    param(
        [Parameter(Mandatory = $true)][string]$SourcePath,
        [Parameter(Mandatory = $true)][string]$InstalledPath,
        [Parameter(Mandatory = $true)][string]$Name
    )
    if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) { throw "Source asset missing: $SourcePath" }
    if (-not (Test-Path -LiteralPath $InstalledPath -PathType Leaf)) { throw "Installed asset missing: $InstalledPath" }
    $sourceHash = Get-Sha256 -Path $SourcePath
    $installedHash = Get-Sha256 -Path $InstalledPath
    return [ordered]@{
        name = $Name
        source = $SourcePath
        installed = $InstalledPath
        source_sha256 = $sourceHash
        installed_sha256 = $installedHash
        match = ($sourceHash -ceq $installedHash)
    }
}

$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path
$actualHead = (& git.exe -C $SourceRoot rev-parse HEAD 2>$null | Select-Object -Last 1).Trim()
if ($LASTEXITCODE -ne 0 -or -not $actualHead) { throw 'Unable to resolve source HEAD.' }
if ($ExpectedHead -and $actualHead -ne $ExpectedHead) {
    throw "EXACT_HEAD_MISMATCH expected=$ExpectedHead actual=$actualHead"
}
if (-not $ExpectedHead) { $ExpectedHead = $actualHead }

$sourcePython = (Get-Command python.exe -ErrorAction Stop).Source
$pwsh = (Get-Command pwsh.exe -ErrorAction Stop).Source
$localRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
$appRoot = Join-Path $localRoot 'app'
$windowsPython = Join-Path $localRoot 'stage26\hot-runtime-env\venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $windowsPython -PathType Leaf)) {
    throw 'Accepted Stage 26 Windows Python 3.12 runtime is missing. Re-run the accepted Windows runtime setup before L3.'
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$runId = ([guid]::NewGuid().ToString('N').Substring(0, 8)).ToUpperInvariant()
$qualificationRoot = Join-Path $localRoot "stage26\windows-case-l3-$stamp-$runId"
$workspaceRoot = Join-Path $qualificationRoot 'workspace'
$fixtureRoot = Join-Path $qualificationRoot 'fixture-state'
New-Item -ItemType Directory -Force -Path $workspaceRoot, $fixtureRoot | Out-Null

$sourceProvenancePath = Join-Path $qualificationRoot 'source-provenance.json'
$installedProvenancePath = Join-Path $qualificationRoot 'installed-runtime-provenance.json'
$runtimeAttestationPath = Join-Path $qualificationRoot 'windows-runtime-attestation.json'
$sourceProvenanceGate = Join-Path $SourceRoot 'scripts\source-provenance-gate.py'
$runtimeAttestationScript = Join-Path $SourceRoot 'scripts\stage26-windows-runtime-attestation.py'
$lockPath = Join-Path $SourceRoot 'config\stage26-openadapt-lock.json'

$criticalAssets = @(
    'runtime/semantic-projection/bin/semantic-projection-launcher.mjs',
    'runtime/semantic-projection/bin/semantic-control-plane-projection.mjs',
    'runtime/semantic-projection/bin/semantic-projection.mjs',
    'runtime/control_plane/__init__.py',
    'runtime/control_plane/cli.py',
    'runtime/control_plane/verification.py',
    'runtime/control_plane/verified_workspace_artifact.py',
    'runtime/control_plane/windows_observation.py',
    'runtime/control_plane/windows_transition.py',
    'runtime/control_plane/windows_case_update.py',
    'runtime/windows/__init__.py',
    'runtime/windows/actuation.py',
    'runtime/windows/observation.py',
    'runtime/windows/verifier.py',
    'runtime/windows/window_scoped_uia.py',
    'scripts/bootstrap-chat-platform.ps1',
    'scripts/bootstrap-manager-runtime.ps1',
    'scripts/bootstrap-manager-lifecycle.ps1',
    'scripts/bootstrap-windows-procedure-runtime.ps1',
    'scripts/chat-platform.ps1',
    'scripts/semantic-direct-controller.ps1',
    'scripts/source-provenance-gate.py',
    'scripts/stage26-windows-runtime-attestation.py',
    'scripts/stage26-windows-case-desk-fixture.ps1',
    'scripts/prepare-windows-case-l3.ps1',
    'scripts/check-windows-case-l3.ps1'
)
$provenanceArgs = @(
    $sourceProvenanceGate,
    '--repo-root', $SourceRoot,
    '--expected-head', $ExpectedHead,
    '--output', $sourceProvenancePath
)
foreach ($asset in $criticalAssets) { $provenanceArgs += @('--asset', $asset) }
$provenanceArgs += @('--lockfile', 'config/stage26-openadapt-lock.json')

& $sourcePython @provenanceArgs
if ($LASTEXITCODE -ne 0) { throw 'Source Provenance Gate failed before Windows L3 preparation.' }
$sourceProvenance = Get-Content -LiteralPath $sourceProvenancePath -Raw -Encoding utf8 | ConvertFrom-Json
if (
    [string]$sourceProvenance.status -ne 'pass' -or
    [string]$sourceProvenance.actual_head -ne $ExpectedHead -or
    -not [bool]$sourceProvenance.working_tree_clean
) {
    throw 'Source Provenance Gate did not produce a clean exact-head PASS.'
}

if (-not $SkipBootstrap) {
    $bootstrap = Join-Path $SourceRoot 'scripts\bootstrap-chat-platform.ps1'
    & $pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $bootstrap
    if ($LASTEXITCODE -ne 0) { throw "bootstrap-chat-platform failed: $LASTEXITCODE" }
}

$installedMappings = @(
    @('runtime\semantic-projection\bin\semantic-projection-launcher.mjs', 'runtime\semantic-projection\bin\semantic-projection-launcher.mjs'),
    @('runtime\semantic-projection\bin\semantic-control-plane-projection.mjs', 'runtime\semantic-projection\bin\semantic-control-plane-projection.mjs'),
    @('runtime\semantic-projection\bin\semantic-projection.mjs', 'runtime\semantic-projection\bin\semantic-projection.mjs'),
    @('runtime\control_plane\cli.py', 'runtime\control_plane\cli.py'),
    @('runtime\control_plane\verification.py', 'runtime\control_plane\verification.py'),
    @('runtime\control_plane\windows_observation.py', 'runtime\control_plane\windows_observation.py'),
    @('runtime\control_plane\windows_transition.py', 'runtime\control_plane\windows_transition.py'),
    @('runtime\control_plane\windows_case_update.py', 'runtime\control_plane\windows_case_update.py'),
    @('runtime\windows\actuation.py', 'runtime\windows\actuation.py'),
    @('runtime\windows\observation.py', 'runtime\windows\observation.py'),
    @('runtime\windows\window_scoped_uia.py', 'runtime\windows\window_scoped_uia.py'),
    @('config\stage26-openadapt-lock.json', 'config\stage26-openadapt-lock.json'),
    @('scripts\chat-platform.ps1', 'scripts\chat-platform.ps1'),
    @('scripts\semantic-direct-controller.ps1', 'scripts\semantic-direct-controller.ps1')
)
$installedRecords = @()
foreach ($mapping in $installedMappings) {
    $sourcePath = Join-Path $SourceRoot ([string]$mapping[0])
    $installedPath = Join-Path $appRoot ([string]$mapping[1])
    $installedRecords += @(Get-InstalledAssetRecord -SourcePath $sourcePath -InstalledPath $installedPath -Name (([string]$mapping[0]).Replace('\', '/')))
}
$allInstalledMatch = @($installedRecords | Where-Object { -not [bool]$_.match }).Count -eq 0
$installedEvidence = [ordered]@{
    schema_version = 1
    exact_head = $ExpectedHead
    source_root = $SourceRoot
    installed_root = $appRoot
    all_match = $allInstalledMatch
    assets = $installedRecords
    captured_at = (Get-Date).ToUniversalTime().ToString('o')
}
Write-Utf8NoBom -Path $installedProvenancePath -Content (($installedEvidence | ConvertTo-Json -Depth 8) + "`n")
if (-not $allInstalledMatch) { throw 'Installed AppRoot bytes do not match the frozen source head.' }

& $windowsPython $runtimeAttestationScript --lock $lockPath --output $runtimeAttestationPath
if ($LASTEXITCODE -ne 0) { throw 'Installed Windows/OpenAdapt runtime attestation failed.' }
$runtimeAttestation = Get-Content -LiteralPath $runtimeAttestationPath -Raw -Encoding utf8 | ConvertFrom-Json
if ([string]$runtimeAttestation.status -ne 'pass' -or -not [bool]$runtimeAttestation.version_match) {
    throw 'Installed Windows/OpenAdapt runtime attestation did not PASS.'
}

$activeSessionRoot = Join-Path $localRoot 'stage26\windows-case-l3'
$activeSessionPath = Join-Path $activeSessionRoot 'active-session.json'
New-Item -ItemType Directory -Force -Path $activeSessionRoot | Out-Null
if (Test-Path -LiteralPath $activeSessionPath -PathType Leaf) {
    try {
        $old = Get-Content -LiteralPath $activeSessionPath -Raw -Encoding utf8 | ConvertFrom-Json
        $oldProcess = Get-Process -Id ([int]$old.fixture_pid) -ErrorAction SilentlyContinue
        if ($null -ne $oldProcess -and -not $oldProcess.HasExited) {
            throw "Another Windows Case Desk session is still active: run_id=$([string]$old.run_id) pid=$([int]$old.fixture_pid)"
        }
    }
    catch {
        if ($_.Exception.Message -like 'Another Windows Case Desk session*') { throw }
    }
    Remove-Item -LiteralPath $activeSessionPath -Force -ErrorAction SilentlyContinue
}

$baseSuffix = Get-Random -Minimum 2100 -Maximum 8900
$suffixes = @($baseSuffix, $baseSuffix + 1, $baseSuffix + 10, $baseSuffix + 11)
$targetIndex = Get-Random -Minimum 0 -Maximum $suffixes.Count
$targetSuffix = $suffixes[$targetIndex]
$targetId = "CASE-$RunId-$('{0:0000}' -f $targetSuffix)"
$requestedStatus = if ((Get-Random -Minimum 0 -Maximum 2) -eq 0) { 'Approved' } else { 'Needs Review' }
$expectedNote = "Reviewed by ordinary Chat $RunId"

$clients = @('Marina Volkova', 'Marina Volkova', 'Maria Volkova', 'Marina Volkov')
$statuses = @('Pending', 'Approved', 'Pending', 'Needs Review')
$cases = @()
for ($i = 0; $i -lt $suffixes.Count; $i += 1) {
    $caseId = "CASE-$RunId-$('{0:0000}' -f $suffixes[$i])"
    $cases += @([ordered]@{
        id = $caseId
        client = $clients[$i]
        status = if ($caseId -ceq $targetId) { 'Pending' } else { $statuses[$i] }
        notes = @("Imported record $RunId-$i")
    })
}
$cases = @($cases | Sort-Object { Get-Random })
$seed = [ordered]@{
    schema_version = 1
    run_id = $RunId
    target_id = $targetId
    expected = [ordered]@{
        status = $requestedStatus
        note = $expectedNote
    }
    cases = $cases
}
$seedPath = Join-Path $fixtureRoot 'seed.json'
$statePath = Join-Path $fixtureRoot 'state.json'
$auditPath = Join-Path $fixtureRoot 'audit.jsonl'
$readyPath = Join-Path $fixtureRoot 'ready.txt'
$closePath = Join-Path $fixtureRoot 'close.txt'
Write-Utf8NoBom -Path $seedPath -Content (($seed | ConvertTo-Json -Depth 8) + "`n")

$fixtureScript = Join-Path $SourceRoot 'scripts\stage26-windows-case-desk-fixture.ps1'
$fixtureArgs = @(
    '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-STA',
    '-File', $fixtureScript,
    '-SeedPath', $seedPath,
    '-StatePath', $statePath,
    '-AuditPath', $auditPath,
    '-ReadyPath', $readyPath,
    '-ClosePath', $closePath,
    '-RunId', $RunId
)
$fixtureProcess = Start-Process -FilePath $pwsh -ArgumentList $fixtureArgs -PassThru

try {
    $deadline = (Get-Date).AddSeconds(30)
    while (-not (Test-Path -LiteralPath $readyPath -PathType Leaf)) {
        $fixtureProcess.Refresh()
        if ($fixtureProcess.HasExited) { throw "Case Desk fixture exited early: $($fixtureProcess.ExitCode)" }
        if ((Get-Date) -gt $deadline) { throw 'Case Desk fixture did not become ready.' }
        Start-Sleep -Milliseconds 100
    }
    if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) { throw 'Case Desk initial state is missing.' }
    $initialState = Get-Content -LiteralPath $statePath -Raw -Encoding utf8 | ConvertFrom-Json
    if ([int]$initialState.save_count -ne 0 -or $null -ne $initialState.selected_case_id) {
        throw 'Case Desk did not start in a clean state.'
    }

    $createdAt = (Get-Date).ToUniversalTime()
    $activeSession = [ordered]@{
        schema_version = 1
        qualification_kind = 'windows-case-l3'
        run_id = $RunId
        fixture_pid = $fixtureProcess.Id
        window_name = "Case Desk $RunId"
        expected_head = $ExpectedHead
        created_at = $createdAt.ToString('o')
        expires_at = $createdAt.AddMinutes(30).ToString('o')
    }
    Write-Utf8NoBom -Path $activeSessionPath -Content (($activeSession | ConvertTo-Json -Depth 5) + "`n")

    if (-not $SkipBootstrap) {
        $platform = Join-Path $appRoot 'scripts\chat-platform.ps1'
        & $pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $platform -Action SetProfile -Profile semantic -FilesRoot $workspaceRoot -NoNotify
        if ($LASTEXITCODE -ne 0) { throw "SetProfile failed: $LASTEXITCODE" }
        & $pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $platform -Action Start -NoNotify
        if ($LASTEXITCODE -ne 0) { throw "Platform Start failed: $LASTEXITCODE" }
    }

    $task = "In the Case Desk window that is already open, update case $targetId for Marina Volkova. Add the internal note '$expectedNote', set its status to $requestedStatus, and save that case. Do not modify any other case. Verify the local execution result before reporting completion. The independent external Finish Gate will be checked after your work, so do not claim that external gate has passed."
    $challenge = @"
STAGE26_3B_WINDOWS_APPLICATION_L3
EXACT_HEAD=$ExpectedHead
RUN_ID=$RunId
TASK_BEGIN
$task
TASK_END
"@
    $challengePath = Join-Path $workspaceRoot 'stage26-3b-windows-application-l3.txt'
    Write-Utf8NoBom -Path $challengePath -Content ($challenge + "`n")

    $manifest = [ordered]@{
        schema_version = 1
        exact_head = $ExpectedHead
        run_id = $RunId
        qualification_root = $qualificationRoot
        workspace_root = $workspaceRoot
        fixture_root = $fixtureRoot
        seed_path = $seedPath
        state_path = $statePath
        audit_path = $auditPath
        ready_path = $readyPath
        close_path = $closePath
        source_provenance_path = $sourceProvenancePath
        installed_runtime_provenance_path = $installedProvenancePath
        runtime_attestation_path = $runtimeAttestationPath
        active_session_path = $activeSessionPath
        challenge_file = $challengePath
        target_case = $targetId
        expected_status = $requestedStatus
        expected_note = $expectedNote
        fixture_pid = $fixtureProcess.Id
    }
    $manifestPath = Join-Path $qualificationRoot 'gate-manifest.json'
    Write-Utf8NoBom -Path $manifestPath -Content (($manifest | ConvertTo-Json -Depth 8) + "`n")

    Write-Host 'STAGE26_3B_WINDOWS_APPLICATION_L3_PREP=PASS'
    Write-Host "EXACT_HEAD=$ExpectedHead"
    Write-Host "RUN_ID=$RunId"
    Write-Host "QUALIFICATION_ROOT=$qualificationRoot"
    Write-Host "CHAT_WORKSPACE_ROOT=$workspaceRoot"
    Write-Host "CHALLENGE_FILE=$challengePath"
    Write-Host "TARGET_CASE=$targetId"
    Write-Host "EXPECTED_STATUS=$requestedStatus"
    Write-Host "FIXTURE_PID=$($fixtureProcess.Id)"
    Write-Host 'SOURCE_PROVENANCE_GATE=PASS'
    Write-Host 'INSTALLED_RUNTIME_PROVENANCE=PASS'
    Write-Host 'WINDOWS_RUNTIME_ATTESTATION=PASS'
    Write-Host "OPENADAPT_VERSION_MATCH=$([bool]$runtimeAttestation.version_match)"
    Write-Host "OPENADAPT_INSTALLED_VERSION=$([string]$runtimeAttestation.installed_version)"
    Write-Host "OPENADAPT_WIN_AGENT_SERVER_SHA256=$([string]$runtimeAttestation.win_agent_server_sha256)"
    Write-Host 'INITIAL_FINISH_GATE=NOT_DONE'
    Write-Host 'CHAT_APP_REBIND_REQUIRED=True'
    Write-Host "CHECK_COMMAND=& '$($SourceRoot)\scripts\check-windows-case-l3.ps1' -QualificationRoot '$qualificationRoot'"
    Write-Host 'NOTE=fixture state, audit, active session details and external Finish Gate evidence are outside the Chat workspace.'
}
catch {
    try { Set-Content -LiteralPath $closePath -Value 'CLOSE' -Encoding ascii -ErrorAction SilentlyContinue } catch {}
    try {
        $fixtureProcess.Refresh()
        if (-not $fixtureProcess.HasExited) {
            $fixtureProcess.Kill($true)
            [void]$fixtureProcess.WaitForExit(5000)
        }
    }
    catch {}
    try {
        if (Test-Path -LiteralPath $activeSessionPath -PathType Leaf) {
            $active = Get-Content -LiteralPath $activeSessionPath -Raw -Encoding utf8 | ConvertFrom-Json
            if ([string]$active.run_id -ceq $RunId) { Remove-Item -LiteralPath $activeSessionPath -Force }
        }
    }
    catch {}
    throw
}
