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

function Write-JsonUtf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value
    )
    $json = $Value | ConvertTo-Json -Depth 8
    [System.IO.File]::WriteAllText($Path, $json + "`n", [System.Text.UTF8Encoding]::new($false))
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
    'runtime/agent_sessions/chatgpt_temporary.py',
    'runtime/agent_sessions/chatgpt_temporary_controller.py',
    'runtime/agent_sessions/chatgpt_temporary_extension/manifest.json',
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
$taskCopyPath = Join-Path $outputRoot 'task.txt'
$controllerStdout = Join-Path $outputRoot 'controller.stdout.log'
$controllerStderr = Join-Path $outputRoot 'controller.stderr.log'
$launchPath = Join-Path $outputRoot 'launch.json'
$resultPath = Join-Path $outputRoot 'result.json'

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

$extensionPath = Join-Path $RepoRoot 'runtime\agent_sessions\chatgpt_temporary_extension'
Write-Host "CAP_AGENT_SESSION_EXACT_HEAD=$ExpectedHead" -ForegroundColor Cyan
Write-Host "CAP_AGENT_SESSION_TASK_SHA256=$taskSha256"
Write-Host "CAP_AGENT_SESSION_EXTENSION_PATH=$extensionPath" -ForegroundColor Cyan
Write-Host "CAP_AGENT_SESSION_OUTPUT_DIR=$outputRoot"
Write-Host "CAP_AGENT_SESSION_STATE_ROOT=$stateRoot"
Write-Host 'CAP_AGENT_SESSION_PROFILE=fresh_readonly_worker_v1'

if ($ValidateOnly) {
    Write-Host 'CAP_AGENT_SESSION_VALIDATE_ONLY=PASS' -ForegroundColor Green
    return
}

Remove-Item -LiteralPath $controllerStdout, $controllerStderr -Force -ErrorAction SilentlyContinue
$controllerArgs = @(
    '-m', 'runtime.agent_sessions.chatgpt_temporary_controller',
    '--identity-json', $identityPath,
    '--task-file', $taskCopyPath,
    '--state-root', $stateRoot,
    '--output-dir', $outputRoot,
    '--port', '3078',
    '--timeout-seconds', [string]$TimeoutSeconds
)
$controller = Start-Process `
    -FilePath $Python.Source `
    -ArgumentList $controllerArgs `
    -WorkingDirectory $RepoRoot `
    -PassThru `
    -WindowStyle Hidden `
    -RedirectStandardOutput $controllerStdout `
    -RedirectStandardError $controllerStderr

try {
    $ready = $false
    $healthUri = 'http://127.0.0.1:3078/health'
    for ($attempt = 0; $attempt -lt 75; $attempt++) {
        if ($controller.HasExited) { break }
        try {
            $health = Invoke-RestMethod -Method Get -Uri $healthUri -TimeoutSec 2
            if (
                [string]$health.status -eq 'ready' -and
                [string]$health.adapter_id -eq 'chatgpt-temporary'
            ) {
                $ready = $true
                break
            }
        }
        catch {}
        Start-Sleep -Milliseconds 200
    }
    if (-not $ready) {
        $stderr = if (Test-Path -LiteralPath $controllerStderr) { (Get-Content -LiteralPath $controllerStderr -Raw -Encoding utf8).Trim() } else { '' }
        throw "Temporary worker controller did not become ready. $stderr"
    }
    if (-not (Test-Path -LiteralPath $launchPath -PathType Leaf)) { throw 'Controller did not write launch.json.' }
    $launch = Get-Content -LiteralPath $launchPath -Raw -Encoding utf8 | ConvertFrom-Json
    if ([string]$launch.adapter_id -ne 'chatgpt-temporary') { throw 'Unexpected adapter in launch evidence.' }
    if ([string]$launch.prompt_sha256 -notmatch '^[0-9a-f]{64}$') { throw 'Launch prompt digest is invalid.' }
    if ([string]$launch.delegation_id -notmatch '^[0-9a-f]{64}$' -or [string]$launch.delivery_id -notmatch '^[0-9a-f]{64}$') {
        throw 'Launch correlation ids are invalid.'
    }

    Write-Host "CAP_AGENT_SESSION_DELEGATION_ID=$($launch.delegation_id)" -ForegroundColor Cyan
    Write-Host "CAP_AGENT_SESSION_DELIVERY_ID=$($launch.delivery_id)"
    Write-Host "CAP_AGENT_SESSION_LAUNCH_NOW=$([bool]$launch.launch_now)"
    if ([bool]$launch.launch_now) {
        Write-Host 'CAP_AGENT_SESSION_LAUNCHING=fresh-temporary-chat' -ForegroundColor Cyan
        Start-Process ([string]$launch.launch_url)
    }
    else {
        Write-Host 'CAP_AGENT_SESSION_LAUNCHING=blocked-existing-delegation-monitor-only' -ForegroundColor Yellow
    }

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path -LiteralPath $resultPath -PathType Leaf) {
            $result = Get-Content -LiteralPath $resultPath -Raw -Encoding utf8 | ConvertFrom-Json
            if ([string]$result.delegation_id -cne [string]$launch.delegation_id) { throw 'Result delegation correlation mismatch.' }
            if ([string]$result.delivery_id -cne [string]$launch.delivery_id) { throw 'Result delivery correlation mismatch.' }
            if ([string]$result.payload_sha256 -notmatch '^[0-9a-f]{64}$') { throw 'Result payload digest is invalid.' }
            if ([string]$result.status -notin @('COMPLETED', 'ABSTAIN', 'ERROR')) { throw 'Result worker status is invalid.' }

            $null = Invoke-SourceGate -OutputPath $postProvenance -Expected $ExpectedHead
            Write-Host "CAP_AGENT_SESSION_RESULT_STATUS=$($result.status)" -ForegroundColor Green
            Write-Host "CAP_AGENT_SESSION_RESULT_SHA256=$($result.payload_sha256)"
            Write-Host "CAP_AGENT_SESSION_RESULT_PATH=$resultPath"
            Write-Host "CAP_AGENT_SESSION_SOURCE_PROVENANCE_BEFORE=$preProvenance"
            Write-Host "CAP_AGENT_SESSION_SOURCE_PROVENANCE_AFTER=$postProvenance"
            Write-Host 'CAP_AGENT_SESSION_PHYSICAL=PASS' -ForegroundColor Green
            return
        }
        if ($controller.HasExited) { break }
        Start-Sleep -Seconds 1
    }

    $stderr = if (Test-Path -LiteralPath $controllerStderr) { (Get-Content -LiteralPath $controllerStderr -Raw -Encoding utf8).Trim() } else { '' }
    throw "Temporary worker qualification ended without durable terminal result. Output=$outputRoot $stderr"
}
finally {
    if (-not $controller.HasExited) {
        Stop-Process -Id $controller.Id -Force -ErrorAction SilentlyContinue
    }
    $controller.Dispose()
}
