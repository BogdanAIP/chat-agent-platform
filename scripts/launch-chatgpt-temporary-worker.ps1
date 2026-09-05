[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TaskFile,
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{40}$')]
    [string]$ExpectedHead,
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$')]
    [string]$ParentTaskId = '',
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$')]
    [string]$SubgoalId = '',
    [ValidatePattern('^[a-z][a-z0-9._-]{0,63}$')]
    [string]$WorkerKind = 'researcher',
    [ValidatePattern('^[a-z][a-z0-9._-]{0,63}$')]
    [string]$ResultContractId = 'research-result-v1',
    [ValidateRange(60, 7200)]
    [int]$TimeoutSeconds = 1800,
    [switch]$ValidateOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-BytesSha256 {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)
    $hasher = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hash = $hasher.ComputeHash($Bytes)
        return ([System.BitConverter]::ToString($hash)).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $hasher.Dispose()
    }
}

function Get-ZipEntryBytes {
    param(
        [Parameter(Mandatory = $true)]$Archive,
        [Parameter(Mandatory = $true)][string]$EntryName
    )
    $entry = $Archive.GetEntry($EntryName)
    if ($null -eq $entry) { throw "Exact-head runtime archive is missing entry: $EntryName" }
    $stream = $entry.Open()
    $memory = [System.IO.MemoryStream]::new()
    try {
        $stream.CopyTo($memory)
        return ,$memory.ToArray()
    }
    finally {
        $memory.Dispose()
        $stream.Dispose()
    }
}

function Get-ZipEntrySha256 {
    param(
        [Parameter(Mandatory = $true)]$Archive,
        [Parameter(Mandatory = $true)][string]$EntryName
    )
    $bytes = Get-ZipEntryBytes -Archive $Archive -EntryName $EntryName
    return Get-BytesSha256 -Bytes $bytes
}

function Get-ZipEntryText {
    param(
        [Parameter(Mandatory = $true)]$Archive,
        [Parameter(Mandatory = $true)][string]$EntryName
    )
    $bytes = Get-ZipEntryBytes -Archive $Archive -EntryName $EntryName
    $utf8 = [System.Text.UTF8Encoding]::new($false, $true)
    return $utf8.GetString($bytes)
}

function Open-ReadShareOnly {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [System.IO.File]::Open(
        $Path,
        [System.IO.FileMode]::Open,
        [System.IO.FileAccess]::Read,
        [System.IO.FileShare]::Read
    )
}

function Write-JsonUtf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value
    )
    $json = $Value | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText($Path, $json + "`n", [System.Text.UTF8Encoding]::new($false))
}

function Get-LogText {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return '' }
    $raw = Get-Content -LiteralPath $Path -Raw -Encoding utf8
    if ($null -eq $raw) { return '' }
    return ([string]$raw).Trim()
}

function ConvertTo-WindowsCommandLineArgument {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Value)
    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') {
        return $Value
    }
    $escaped = [System.Text.RegularExpressions.Regex]::Replace(
        $Value,
        '(\\*)"',
        '$1$1\"'
    )
    $escaped = [System.Text.RegularExpressions.Regex]::Replace(
        $escaped,
        '(\\+)$',
        '$1$1'
    )
    return '"' + $escaped + '"'
}

function Invoke-SourceGate {
    param(
        [Parameter(Mandatory = $true)][string]$OutputPath,
        [Parameter(Mandatory = $true)][string]$Expected
    )
    $arguments = @(
        $SourceGatePath,
        '--repo-root', $RepoRoot,
        '--expected-head', $Expected,
        '--output', $OutputPath
    )
    foreach ($asset in $CriticalAssets) {
        $arguments += @('--asset', $asset)
    }
    & $Python.Source @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Agent Session source provenance gate failed with exit code $LASTEXITCODE."
    }
    $gate = Get-Content -LiteralPath $OutputPath -Raw -Encoding utf8 | ConvertFrom-Json
    if (
        [string]$gate.status -ne 'pass' -or
        [string]$gate.actual_head -cne $Expected -or
        -not [bool]$gate.working_tree_clean -or
        -not [bool]$gate.tracked_diff_empty -or
        -not [bool]$gate.untracked_empty
    ) {
        throw 'Agent Session source provenance did not prove a clean exact-head source tree.'
    }
    return $gate
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$ExpectedHead = $ExpectedHead.ToLowerInvariant()
$TaskFile = (Resolve-Path -LiteralPath $TaskFile).Path
if (-not (Test-Path -LiteralPath $TaskFile -PathType Leaf)) {
    throw "Task file is missing: $TaskFile"
}
$taskBytes = (Get-Item -LiteralPath $TaskFile).Length
if ($taskBytes -le 0 -or $taskBytes -gt 64000) {
    throw "Task file must contain 1..64000 bytes; actual=$taskBytes"
}
$taskText = [System.IO.File]::ReadAllText($TaskFile, [System.Text.UTF8Encoding]::new($false))
if ([string]::IsNullOrWhiteSpace($taskText)) { throw 'Task file must contain non-whitespace UTF-8 text.' }
$taskSha256 = Get-Sha256 -Path $TaskFile

$git = Get-Command 'git.exe' -ErrorAction SilentlyContinue
if ($null -eq $git) { $git = Get-Command 'git' -ErrorAction Stop }
$actualHead = (& $git.Source -C $RepoRoot rev-parse HEAD).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $actualHead -cne $ExpectedHead) {
    throw "EXACT_HEAD_MISMATCH expected=$ExpectedHead actual=$actualHead"
}

$Python = Get-Command 'python.exe' -ErrorAction SilentlyContinue
if ($null -eq $Python) { $Python = Get-Command 'python' -ErrorAction Stop }
$SourceGatePath = Join-Path $RepoRoot 'scripts\source-provenance-gate.py'
if (-not (Test-Path -LiteralPath $SourceGatePath -PathType Leaf)) {
    throw "Source provenance gate is missing: $SourceGatePath"
}

$CriticalAssets = @(
    'runtime/control_plane/delegation_state.py',
    'runtime/agent_sessions/__init__.py',
    'runtime/agent_sessions/source_attestation.py',
    'runtime/agent_sessions/chatgpt_temporary.py',
    'runtime/agent_sessions/chatgpt_temporary_controller.py',
    'runtime/agent_sessions/chatgpt_temporary_extension/manifest.json',
    'runtime/agent_sessions/chatgpt_temporary_extension/execution_generation.js',
    'runtime/agent_sessions/chatgpt_temporary_extension/policy.js',
    'runtime/agent_sessions/chatgpt_temporary_extension/background.js',
    'runtime/agent_sessions/chatgpt_temporary_extension/content.js',
    'scripts/launch-chatgpt-temporary-worker.ps1',
    'scripts/source-provenance-gate.py'
)
foreach ($relative in $CriticalAssets) {
    $path = Join-Path $RepoRoot ($relative.Replace('/', '\'))
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required Agent Session runtime asset is missing: $relative"
    }
}

if (-not $ParentTaskId) { $ParentTaskId = "agent-session-l3-$($ExpectedHead.Substring(0, 12))" }
if (-not $SubgoalId) { $SubgoalId = "temporary-worker-$($taskSha256.Substring(0, 12))" }

$stateRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\agent-sessions\private-state'
$qualificationBase = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\agent-sessions\qualification'
New-Item -ItemType Directory -Force -Path $stateRoot | Out-Null
New-Item -ItemType Directory -Force -Path $qualificationBase | Out-Null
$operationKey = "$($ExpectedHead.Substring(0, 12))-$($taskSha256.Substring(0, 12))"
$outputRoot = Join-Path $qualificationBase $operationKey
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
$preProvenance = Join-Path $outputRoot 'source-provenance-before.json'
$postProvenance = Join-Path $outputRoot 'source-provenance-after.json'
$identityPath = Join-Path $outputRoot 'identity.json'
$runtimeAttestationPath = Join-Path $outputRoot 'expected-runtime-attestation.json'
$sourceExecutionPath = Join-Path $outputRoot 'source-execution-snapshot.json'
$taskCopyPath = Join-Path $outputRoot 'task.txt'
$controllerStdout = Join-Path $outputRoot 'controller.stdout.log'
$controllerStderr = Join-Path $outputRoot 'controller.stderr.log'
$preflightPath = Join-Path $outputRoot 'preflight.json'
$launchPath = Join-Path $outputRoot 'launch.json'
$resultPath = Join-Path $outputRoot 'result.json'
$runtimeArchivePath = Join-Path $outputRoot ("exact-head-runtime-$([Guid]::NewGuid().ToString('N')).zip")
$runtimeSnapshotRoot = Join-Path $outputRoot ("exact-head-source-$ExpectedHead")
$extensionPath = Join-Path $runtimeSnapshotRoot 'runtime\agent_sessions\chatgpt_temporary_extension'
$extensionArchivePrefix = 'runtime/agent_sessions/chatgpt_temporary_extension/'
$extensionAssetNames = @(
    'manifest.json',
    'execution_generation.js',
    'policy.js',
    'background.js',
    'content.js'
)

$null = Invoke-SourceGate -OutputPath $preProvenance -Expected $ExpectedHead

$identity = [ordered]@{
    parent_task_id = $ParentTaskId
    subgoal_id = $SubgoalId
    worker_kind = $WorkerKind
    worker_profile = 'fresh_readonly_worker_v1'
    task_sha256 = $taskSha256
    result_contract_id = $ResultContractId
}
Write-JsonUtf8NoBom -Path $identityPath -Value $identity
[System.IO.File]::WriteAllText($taskCopyPath, $taskText, [System.Text.UTF8Encoding]::new($false))
if ((Get-Sha256 -Path $taskCopyPath) -cne $taskSha256) { throw 'Task copy digest changed.' }

# Materialize the effectful runtime from the immutable reviewed Git tree. From
# this point the controller and expected extension hashes no longer trust
# mutable worktree bytes observed after the source gate.
& $git.Source -C $RepoRoot archive --format=zip --output=$runtimeArchivePath $ExpectedHead runtime
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $runtimeArchivePath -PathType Leaf)) {
    throw 'Failed to create exact-head runtime archive from the reviewed Git tree.'
}
$runtimeArchiveSha256 = Get-Sha256 -Path $runtimeArchivePath
$archive = [System.IO.Compression.ZipFile]::OpenRead($runtimeArchivePath)
try {
    $executionGenerationText = Get-ZipEntryText -Archive $archive -EntryName ($extensionArchivePrefix + 'execution_generation.js')
    $executionGenerationMatch = [regex]::Match(
        $executionGenerationText,
        'CAPChatGPTTemporaryExecutionGeneration\s*=\s*"([0-9a-f]{64})"'
    )
    if (-not $executionGenerationMatch.Success) {
        throw 'Exact-head extension execution generation marker is missing or invalid.'
    }
    $executionGeneration = $executionGenerationMatch.Groups[1].Value

    $runtimeAssets = [ordered]@{}
    foreach ($assetName in $extensionAssetNames) {
        $runtimeAssets[$assetName] = Get-ZipEntrySha256 -Archive $archive -EntryName ($extensionArchivePrefix + $assetName)
    }
}
finally {
    $archive.Dispose()
}

if (-not (Test-Path -LiteralPath $runtimeSnapshotRoot -PathType Container)) {
    [System.IO.Compression.ZipFile]::ExtractToDirectory($runtimeArchivePath, $runtimeSnapshotRoot)
}
if (-not (Test-Path -LiteralPath $extensionPath -PathType Container)) {
    throw 'Exact-head extension snapshot is missing after runtime materialization.'
}

$expectedExtensionFiles = @($extensionAssetNames | Sort-Object)
$actualExtensionFiles = @(
    Get-ChildItem -LiteralPath $extensionPath -File -Recurse -Force |
        ForEach-Object { [System.IO.Path]::GetRelativePath($extensionPath, $_.FullName).Replace('\', '/') } |
        Sort-Object
)
if (($actualExtensionFiles -join "`n") -cne ($expectedExtensionFiles -join "`n")) {
    throw 'Exact-head extension snapshot contains missing or unexpected files.'
}
foreach ($assetName in $extensionAssetNames) {
    $snapshotAsset = Join-Path $extensionPath $assetName
    if ((Get-Sha256 -Path $snapshotAsset) -cne [string]$runtimeAssets[$assetName]) {
        throw "Exact-head extension snapshot does not match archived source: $assetName"
    }
}

$expectedRuntimeAttestation = [ordered]@{
    schema_version = 1
    adapter_id = 'chatgpt-temporary'
    expected_head = $ExpectedHead
    execution_generation = $executionGeneration
    assets = $runtimeAssets
}
Write-JsonUtf8NoBom -Path $runtimeAttestationPath -Value $expectedRuntimeAttestation

$sourceExecution = [ordered]@{
    schema_version = 1
    expected_head = $ExpectedHead
    runtime_source = 'git-archive-exact-head'
    runtime_archive_path = $runtimeArchivePath
    runtime_archive_sha256 = $runtimeArchiveSha256
    python_mode = 'isolated-zipimport'
    controller_module = 'runtime.agent_sessions.chatgpt_temporary_controller'
    extension_snapshot_path = $extensionPath
    extension_assets = $runtimeAssets
}
Write-JsonUtf8NoBom -Path $sourceExecutionPath -Value $sourceExecution

Write-Host "CAP_AGENT_SESSION_EXACT_HEAD=$ExpectedHead" -ForegroundColor Cyan
Write-Host "CAP_AGENT_SESSION_TASK_SHA256=$taskSha256"
Write-Host "CAP_AGENT_SESSION_EXTENSION_PATH=$extensionPath" -ForegroundColor Cyan
Write-Host "CAP_AGENT_SESSION_RUNTIME_ARCHIVE=$runtimeArchivePath"
Write-Host "CAP_AGENT_SESSION_RUNTIME_ARCHIVE_SHA256=$runtimeArchiveSha256"
Write-Host "CAP_AGENT_SESSION_SOURCE_EXECUTION_SNAPSHOT=$sourceExecutionPath"
Write-Host "CAP_AGENT_SESSION_EXECUTION_GENERATION=$executionGeneration" -ForegroundColor Cyan
Write-Host "CAP_AGENT_SESSION_EXPECTED_EXTENSION_ATTESTATION=$runtimeAttestationPath"
Write-Host "CAP_AGENT_SESSION_OUTPUT_DIR=$outputRoot"
Write-Host "CAP_AGENT_SESSION_STATE_ROOT=$stateRoot"
Write-Host 'CAP_AGENT_SESSION_PROFILE=fresh_readonly_worker_v1'

if ($ValidateOnly) {
    Write-Host 'CAP_AGENT_SESSION_VALIDATE_ONLY=PASS' -ForegroundColor Green
    return
}

# Controller projection files are not durable authority. Remove every stale
# projection so neither preflight nor terminal-readback can inherit old bytes.
Remove-Item -LiteralPath $controllerStdout, $controllerStderr, $preflightPath, $launchPath, $resultPath -Force -ErrorAction SilentlyContinue

$sourceLocks = [System.Collections.Generic.List[System.IDisposable]]::new()
$controller = $null
try {
    # Keep the selected source immutable for the effectful authority window.
    # FileShare.Read permits Python/Chrome reads while denying new write/delete
    # access to the exact archive and unpacked extension files.
    $null = $sourceLocks.Add((Open-ReadShareOnly -Path $runtimeArchivePath))
    if ((Get-Sha256 -Path $runtimeArchivePath) -cne $runtimeArchiveSha256) {
        throw 'Exact-head runtime archive changed before controller execution.'
    }
    foreach ($assetName in $extensionAssetNames) {
        $snapshotAsset = Join-Path $extensionPath $assetName
        $null = $sourceLocks.Add((Open-ReadShareOnly -Path $snapshotAsset))
        if ((Get-Sha256 -Path $snapshotAsset) -cne [string]$runtimeAssets[$assetName]) {
            throw "Exact-head extension snapshot changed before browser authority: $assetName"
        }
    }
    foreach ($inputPath in @($identityPath, $taskCopyPath, $runtimeAttestationPath)) {
        $null = $sourceLocks.Add((Open-ReadShareOnly -Path $inputPath))
    }
    if ((Get-Sha256 -Path $taskCopyPath) -cne $taskSha256) {
        throw 'Task copy changed before isolated controller execution.'
    }

    # -I removes the current directory/user-site/PYTHON* influence. -S avoids
    # site initialization, -B prevents bytecode writes, and only the exact Git
    # archive is inserted as the project import root.
    $pythonBootstrap = 'import runpy,sys;archive=sys.argv.pop(1);sys.path.insert(0,archive);runpy.run_module("runtime.agent_sessions.chatgpt_temporary_controller",run_name="__main__")'
    $controllerArgs = @(
        '-I',
        '-B',
        '-S',
        '-c', $pythonBootstrap,
        $runtimeArchivePath,
        '--identity-json', $identityPath,
        '--task-file', $taskCopyPath,
        '--runtime-attestation-json', $runtimeAttestationPath,
        '--state-root', $stateRoot,
        '--output-dir', $outputRoot,
        '--port', '3078',
        '--timeout-seconds', [string]$TimeoutSeconds
    )
    $controllerArgumentLine = (($controllerArgs | ForEach-Object {
        ConvertTo-WindowsCommandLineArgument -Value ([string]$_)
    }) -join ' ')
    $controller = Start-Process `
        -FilePath $Python.Source `
        -ArgumentList $controllerArgumentLine `
        -WorkingDirectory $outputRoot `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput $controllerStdout `
        -RedirectStandardError $controllerStderr

    $healthUri = 'http://127.0.0.1:3078/health'
    $phase = ''
    for ($attempt = 0; $attempt -lt 75; $attempt++) {
        if ($controller.HasExited) { break }
        try {
            $health = Invoke-RestMethod -Method Get -Uri $healthUri -TimeoutSec 2
            if (
                [string]$health.adapter_id -eq 'chatgpt-temporary' -and
                [string]$health.status -in @('preflight', 'ready')
            ) {
                $phase = [string]$health.status
                break
            }
        }
        catch {}
        Start-Sleep -Milliseconds 200
    }

    $terminalSnapshotReady = $false
    if (-not $phase -and $controller.HasExited) {
        $terminalSnapshotReady = (
            $controller.ExitCode -eq 0 -and
            (Test-Path -LiteralPath $launchPath -PathType Leaf) -and
            (Test-Path -LiteralPath $resultPath -PathType Leaf)
        )
    }
    if (-not $phase -and -not $terminalSnapshotReady) {
        $stderr = Get-LogText -Path $controllerStderr
        throw "Temporary worker controller did not become ready. $stderr"
    }

    if ($phase -eq 'preflight') {
        if (-not (Test-Path -LiteralPath $preflightPath -PathType Leaf)) {
            throw 'Controller entered preflight without fresh preflight.json.'
        }
        $preflight = Get-Content -LiteralPath $preflightPath -Raw -Encoding utf8 | ConvertFrom-Json
        if ([string]$preflight.adapter_id -ne 'chatgpt-temporary') { throw 'Unexpected adapter in preflight evidence.' }
        if ([string]$preflight.expected_runtime_head -cne $ExpectedHead) { throw 'Preflight runtime HEAD mismatch.' }
        if ([string]$preflight.execution_generation -cne $executionGeneration) { throw 'Preflight execution-generation mismatch.' }
        if ([string]$preflight.delegation_id -notmatch '^[0-9a-f]{64}$' -or [string]$preflight.delivery_id -notmatch '^[0-9a-f]{64}$') {
            throw 'Preflight correlation ids are invalid.'
        }
        $preflightUrl = [string]$preflight.preflight_url
        if ($preflightUrl -notmatch '^https://chatgpt\.com/\?cap_agent_preflight=1#cap_preflight_id=[0-9a-f]{64}$') {
            throw 'Preflight URL is not the bounded neutral bootstrap shape.'
        }
        if ($preflightUrl -match 'cap_run_id|cap_delegation_id|cap_delivery_id|prompt=|temporary-chat') {
            throw 'Preflight URL contains task/private launch material.'
        }
        Write-Host 'CAP_AGENT_SESSION_PREFLIGHT=opening-neutral-bootstrap' -ForegroundColor Cyan
        Write-Host "CAP_AGENT_SESSION_PREFLIGHT_PATH=$preflightPath"
        Start-Process $preflightUrl

        $ready = $false
        for ($attempt = 0; $attempt -lt 150; $attempt++) {
            if ($controller.HasExited) { break }
            try {
                $health = Invoke-RestMethod -Method Get -Uri $healthUri -TimeoutSec 2
                if (
                    [string]$health.status -eq 'ready' -and
                    [string]$health.adapter_id -eq 'chatgpt-temporary' -and
                    (Test-Path -LiteralPath $launchPath -PathType Leaf)
                ) {
                    $ready = $true
                    break
                }
            }
            catch {}
            Start-Sleep -Milliseconds 200
        }
        if (-not $ready) {
            $stderr = Get-LogText -Path $controllerStderr
            throw "Temporary worker preflight did not commit the task launch. $stderr"
        }
        $phase = 'ready'
        Write-Host 'CAP_AGENT_SESSION_PREFLIGHT=PASS' -ForegroundColor Green
    }

    if ($terminalSnapshotReady) {
        Write-Host 'CAP_AGENT_SESSION_CONTROLLER=terminal-readback' -ForegroundColor Cyan
    }

    if (-not (Test-Path -LiteralPath $launchPath -PathType Leaf)) { throw 'Controller did not write launch.json.' }
    $launch = Get-Content -LiteralPath $launchPath -Raw -Encoding utf8 | ConvertFrom-Json
    if ([string]$launch.adapter_id -ne 'chatgpt-temporary') { throw 'Unexpected adapter in launch evidence.' }
    if ([string]$launch.expected_runtime_head -cne $ExpectedHead) { throw 'Controller runtime-attestation head mismatch.' }
    if ([string]$launch.execution_generation -cne $executionGeneration) { throw 'Controller execution-generation mismatch.' }
    if ([string]$launch.prompt_sha256 -notmatch '^[0-9a-f]{64}$') { throw 'Launch prompt digest is invalid.' }
    if ([string]$launch.delegation_id -notmatch '^[0-9a-f]{64}$' -or [string]$launch.delivery_id -notmatch '^[0-9a-f]{64}$') {
        throw 'Launch correlation ids are invalid.'
    }
    $taskLaunchUrl = [string]$launch.launch_url
    if ($taskLaunchUrl -match 'cap_run_id=[^&#]*' -and $taskLaunchUrl -match [regex]::Escape([string]$launch.delegation_id)) {
        # The legacy fragment key carries only an opaque live handle. The private
        # controller run capability is never emitted in launch.json or the URL.
        $launchJsonText = Get-Content -LiteralPath $launchPath -Raw -Encoding utf8
        if ($launchJsonText -match '"run_id"') { throw 'Launch projection leaked private run_id.' }
    }

    Write-Host "CAP_AGENT_SESSION_DELEGATION_ID=$($launch.delegation_id)" -ForegroundColor Cyan
    Write-Host "CAP_AGENT_SESSION_DELIVERY_ID=$($launch.delivery_id)"
    Write-Host "CAP_AGENT_SESSION_LAUNCH_NOW=$([bool]$launch.launch_now)"
    if ([bool]$launch.launch_now) {
        Write-Host 'CAP_AGENT_SESSION_TASK_NAVIGATION_OWNER=preflight-tab' -ForegroundColor Cyan
    }
    else {
        Write-Host 'CAP_AGENT_SESSION_TASK_NAVIGATION=blocked-existing-delegation' -ForegroundColor Yellow
    }

    # The launcher never opens the task-bearing URL. The same neutral preflight
    # tab that owns the live MV3 handoff performs location.replace(task_url)
    # only after commit acknowledgement/reconciliation. launch.json remains
    # qualification evidence, not a second physical browser-launch authority.

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path -LiteralPath $resultPath -PathType Leaf) {
            $result = Get-Content -LiteralPath $resultPath -Raw -Encoding utf8 | ConvertFrom-Json
            if ([string]$result.delegation_id -cne [string]$launch.delegation_id) { throw 'Result delegation correlation mismatch.' }
            if ([string]$result.delivery_id -cne [string]$launch.delivery_id) { throw 'Result delivery correlation mismatch.' }
            if ([string]$result.payload_sha256 -notmatch '^[0-9a-f]{64}$') { throw 'Result payload digest is invalid.' }
            if ([string]$result.status -notin @('COMPLETED', 'ABSTAIN', 'ERROR')) { throw 'Result worker status is invalid.' }
            if ([string]$result.status -ne 'COMPLETED') {
                throw "Physical qualification requires COMPLETED worker result; actual=$($result.status)"
            }

            $null = Invoke-SourceGate -OutputPath $postProvenance -Expected $ExpectedHead
            Write-Host "CAP_AGENT_SESSION_RESULT_STATUS=$($result.status)" -ForegroundColor Green
            Write-Host "CAP_AGENT_SESSION_RESULT_SHA256=$($result.payload_sha256)"
            Write-Host "CAP_AGENT_SESSION_RESULT_PATH=$resultPath"
            Write-Host "CAP_AGENT_SESSION_SOURCE_PROVENANCE_BEFORE=$preProvenance"
            Write-Host "CAP_AGENT_SESSION_SOURCE_PROVENANCE_AFTER=$postProvenance"
            Write-Host "CAP_AGENT_SESSION_SOURCE_EXECUTION_SNAPSHOT=$sourceExecutionPath"
            Write-Host 'CAP_AGENT_SESSION_PHYSICAL=PASS' -ForegroundColor Green
            return
        }
        if ($controller.HasExited) { break }
        Start-Sleep -Seconds 1
    }

    $stderr = Get-LogText -Path $controllerStderr
    throw "Temporary worker qualification ended without durable terminal result. Output=$outputRoot $stderr"
}
finally {
    if ($null -ne $controller) {
        if (-not $controller.HasExited) {
            Stop-Process -Id $controller.Id -Force -ErrorAction SilentlyContinue
        }
        $controller.Dispose()
    }
    for ($index = $sourceLocks.Count - 1; $index -ge 0; $index--) {
        $sourceLocks[$index].Dispose()
    }
}
