[CmdletBinding()]
param(
    [ValidateSet('Check', 'Update')]
    [string]$Action = 'Check',
    [ValidatePattern('^[0-9a-f]{32}$')]
    [string]$RequestId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$CorePath = Join-Path $PSScriptRoot 'chat-platform-update-core.ps1'
if (-not (Test-Path -LiteralPath $CorePath -PathType Leaf)) {
    throw "Update core is missing: $CorePath"
}
. $CorePath

$LocalRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
$StateDir = Join-Path $LocalRoot 'state'
$StatePath = Join-Path $StateDir 'platform-update.json'
$ResultPath = Join-Path $StateDir 'platform-update-result.json'
$RequestDir = Join-Path $StateDir 'platform-update-requests'
$script:RequestResultPath = if ([string]::IsNullOrWhiteSpace($RequestId)) {
    $null
}
else {
    Join-Path $RequestDir "$RequestId.updater.json"
}
$CacheRoot = Join-Path $LocalRoot 'update-cache'
$CacheRepo = Join-Path $CacheRoot 'repo.git'
$WorktreeRoot = Join-Path $CacheRoot 'worktrees'
$LogDir = Join-Path $LocalRoot 'logs'
$LogPath = Join-Path $LogDir 'update.log'
$DesiredStatePath = Join-Path $StateDir 'desired-state.json'
$InstalledManagerPath = Join-Path $LocalRoot 'app\scripts\chat-platform.ps1'
$RemoteUrl = $script:CapUpdateOfficialRemote
$MutexName = 'Local\ChatAgentPlatformUpdateOperation'
$MutexTimeoutMilliseconds = 30000
$ProcessTimeoutMilliseconds = 900000
$TargetContinuityBlockedReason = 'target_missing_self_update_contract'

if (-not [string]::IsNullOrWhiteSpace($RequestId) -and $Action -ne 'Update') {
    throw 'RequestId is valid only with Action=Update.'
}

foreach ($directory in @($StateDir, $RequestDir, $CacheRoot, $WorktreeRoot, $LogDir)) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
}

function Write-CapUpdateLog {
    param([Parameter(Mandatory)] [string]$Message)

    $line = '{0} {1}' -f [datetimeoffset]::UtcNow.ToString('o'), $Message
    Add-Content -LiteralPath $LogPath -Value $line -Encoding utf8
}

function Write-CapUpdateResult {
    param(
        [Parameter(Mandatory)] [string]$Status,
        [string]$InstalledCommitSha,
        [string]$TargetCommitSha,
        [string]$Reason,
        [bool]$Restarted = $false
    )

    $result = [ordered]@{
        schema_version = 1
        request_id = if ([string]::IsNullOrWhiteSpace($RequestId)) { $null } else { $RequestId }
        process_id = $PID
        action = $Action.ToLowerInvariant()
        status = $Status
        repository = $script:CapUpdateRepository
        branch = $script:CapUpdateBranch
        installed_commit_sha = if ([string]::IsNullOrWhiteSpace($InstalledCommitSha)) { $null } else { $InstalledCommitSha }
        target_commit_sha = if ([string]::IsNullOrWhiteSpace($TargetCommitSha)) { $null } else { $TargetCommitSha }
        restarted = $Restarted
        reason = if ([string]::IsNullOrWhiteSpace($Reason)) { $null } else { $Reason }
        completed_at = [datetimeoffset]::UtcNow.ToString('o')
        state_path = $StatePath
        log_path = $LogPath
    }
    if (-not [string]::IsNullOrWhiteSpace($script:RequestResultPath)) {
        Write-CapUpdateAtomicJson -Path $script:RequestResultPath -Value $result
    }
    Write-CapUpdateAtomicJson -Path $ResultPath -Value $result
    $result | ConvertTo-Json -Compress -Depth 5
}

function Get-CapDesiredRunning {
    if (-not (Test-Path -LiteralPath $DesiredStatePath -PathType Leaf)) {
        return $false
    }
    try {
        $state = Get-Content -LiteralPath $DesiredStatePath -Raw -Encoding utf8 | ConvertFrom-Json -ErrorAction Stop
        if ($null -eq $state.PSObject.Properties['desired_state']) {
            throw 'desired_state is missing'
        }
        $desired = [string]$state.desired_state
        if ($desired -notin @('running', 'stopped')) {
            throw "unsupported desired_state '$desired'"
        }
        return ($desired -eq 'running')
    }
    catch {
        throw "Persistent desired state is invalid; refusing update before quiesce: $($_.Exception.Message)"
    }
}

function Invoke-CapPwshProcess {
    param(
        [Parameter(Mandatory)] [string]$ScriptPath,
        [string[]]$Arguments = @(),
        [Parameter(Mandatory)] [string]$Label,
        [int]$TimeoutMilliseconds = $ProcessTimeoutMilliseconds,
        [bool]$CaptureOutput = $true
    )

    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pwsh
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $CaptureOutput
    $startInfo.RedirectStandardError = $CaptureOutput
    foreach ($argument in @(
        '-NoLogo',
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $ScriptPath
    )) {
        $startInfo.ArgumentList.Add([string]$argument)
    }
    foreach ($argument in $Arguments) {
        $startInfo.ArgumentList.Add([string]$argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    $stdoutTask = $null
    $stderrTask = $null
    try {
        if (-not $process.Start()) {
            throw "Could not start $Label."
        }
        if ($CaptureOutput) {
            $stdoutTask = $process.StandardOutput.ReadToEndAsync()
            $stderrTask = $process.StandardError.ReadToEndAsync()
        }
        if (-not $process.WaitForExit($TimeoutMilliseconds)) {
            try { $process.Kill($true) } catch {}
            try { $process.WaitForExit(5000) | Out-Null } catch {}
            throw "$Label exceeded the update process timeout."
        }

        if ($CaptureOutput) {
            $stdout = $stdoutTask.GetAwaiter().GetResult()
            $stderr = $stderrTask.GetAwaiter().GetResult()
            if (-not [string]::IsNullOrWhiteSpace($stdout)) {
                Write-CapUpdateLog "$Label stdout:`n$stdout"
            }
            if (-not [string]::IsNullOrWhiteSpace($stderr)) {
                Write-CapUpdateLog "$Label stderr:`n$stderr"
            }
        }
        else {
            Write-CapUpdateLog "$Label exited code=$($process.ExitCode) without pipe capture"
        }

        if ($process.ExitCode -ne 0) {
            throw "$Label failed with exit code $($process.ExitCode)."
        }
    }
    finally {
        $process.Dispose()
    }
}

function Test-CapTargetPlatformUpdateProcedureContract {
    param([Parameter(Mandatory)] [string]$WorktreePath)

    $platformPath = Join-Path $WorktreePath 'runtime\control_plane\platform_update.py'
    $cliPath = Join-Path $WorktreePath 'runtime\control_plane\cli.py'
    $semanticPath = Join-Path $WorktreePath 'runtime\semantic-projection\bin\semantic-control-plane-projection.mjs'
    $bootstrapManagerPath = Join-Path $WorktreePath 'scripts\bootstrap-manager-runtime.ps1'
    $targetCorePath = Join-Path $WorktreePath 'scripts\chat-platform-update-core.ps1'

    foreach ($path in @($platformPath, $cliPath, $semanticPath, $bootstrapManagerPath, $targetCorePath)) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            return $false
        }
    }

    $pythonCommand = Get-Command 'python.exe' -ErrorAction SilentlyContinue
    if ($null -eq $pythonCommand) {
        $pythonCommand = Get-Command 'python' -ErrorAction SilentlyContinue
    }
    if ($null -eq $pythonCommand) {
        return $false
    }

    $pythonValidator = @'
import ast
import importlib.util
import json
import pathlib
import sys
import tempfile
from datetime import datetime, timedelta, timezone

root = pathlib.Path(sys.argv[1])
platform_path = root / "runtime" / "control_plane" / "platform_update.py"
cli_path = root / "runtime" / "control_plane" / "cli.py"

def parse(path):
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

def module_constant(tree, name):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    if isinstance(node.value, ast.Constant):
                        return node.value.value
    return None

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

platform_tree = parse(platform_path)
if module_constant(platform_tree, "PROCEDURE_ID") != "platform_update_v1":
    raise SystemExit(10)

platform_functions = {
    node.name: node
    for node in platform_tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
for required in (
    "_request_update",
    "_status",
    "_updater_result_path",
    "_correlated_updater_result",
    "run_platform_update",
):
    if required not in platform_functions:
        raise SystemExit(11)

run_function = platform_functions["run_platform_update"]
action_sets = []
for node in ast.walk(run_function):
    if isinstance(node, ast.Set):
        values = {
            item.value
            for item in node.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        }
        if values:
            action_sets.append(values)
if {"check", "request_update", "status"} not in action_sets:
    raise SystemExit(12)

cli_tree = parse(cli_path)
imports = [
    node
    for node in cli_tree.body
    if isinstance(node, ast.ImportFrom)
    and node.module == "runtime.control_plane.platform_update"
]
if len(imports) != 1:
    raise SystemExit(20)
imported = {alias.asname or alias.name for alias in imports[0].names}
if "PLATFORM_UPDATE_PROCEDURE_ID" not in imported or "run_platform_update" not in imported:
    raise SystemExit(21)

dispatch = next(
    (
        node
        for node in cli_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_dispatch_registered_procedure"
    ),
    None,
)
if dispatch is None:
    raise SystemExit(22)
has_platform_compare = False
has_platform_call = False
for node in ast.walk(dispatch):
    if isinstance(node, ast.Compare):
        names = {
            child.id
            for child in ast.walk(node)
            if isinstance(child, ast.Name)
        }
        if "PLATFORM_UPDATE_PROCEDURE_ID" in names and "procedure" in names:
            has_platform_compare = True
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_platform_update"
    ):
        has_platform_call = True
if not has_platform_compare or not has_platform_call:
    raise SystemExit(23)

# Behaviorally qualify the future target's request-correlated status implementation.
spec = importlib.util.spec_from_file_location("cap_target_platform_update", platform_path)
if spec is None or spec.loader is None:
    raise SystemExit(30)
target = importlib.util.module_from_spec(spec)
spec.loader.exec_module(target)

with tempfile.TemporaryDirectory(prefix="cap-update-target-qualification-") as temporary:
    local = pathlib.Path(temporary)
    root_state = local / "ChatAgentPlatform" / "state"
    requests = root_state / "platform-update-requests"
    requests.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)

    request_id = "1" * 32
    accepted = now - timedelta(seconds=2)
    write_json(
        requests / f"{request_id}.request.json",
        {
            "schema_version": 1,
            "request_id": request_id,
            "status": "accepted",
            "accepted_at": accepted.isoformat(),
            "repository": "BogdanAIP/chat-agent-platform",
            "branch": "main",
        },
    )
    # Deliberately contradictory global result: request reconciliation must ignore it.
    write_json(
        root_state / "platform-update-result.json",
        {
            "schema_version": 1,
            "request_id": "f" * 32,
            "process_id": 9999,
            "action": "update",
            "status": "updated",
            "completed_at": now.isoformat(),
        },
    )
    write_json(
        requests / f"{request_id}.updater.json",
        {
            "schema_version": 1,
            "request_id": request_id,
            "process_id": 7001,
            "action": "update",
            "status": "current",
            "completed_at": now.isoformat(),
        },
    )
    recovered = target.run_platform_update(
        {
            "procedure": "platform_update_v1",
            "action": "status",
            "request_id": request_id,
        },
        local_app_data=local,
    )
    receipt = recovered.get("receipt")
    if (
        recovered.get("status") != "completed"
        or not isinstance(receipt, dict)
        or receipt.get("correlation_verified") is not True
        or receipt.get("recovered_by_status") is not True
        or receipt.get("updater_process_id") != 7001
        or receipt.get("updater_result", {}).get("request_id") != request_id
    ):
        raise SystemExit(31)

    pending_id = "2" * 32
    pending_accepted = datetime.now(timezone.utc)
    write_json(
        requests / f"{pending_id}.request.json",
        {
            "schema_version": 1,
            "request_id": pending_id,
            "status": "accepted",
            "accepted_at": pending_accepted.isoformat(),
            "repository": "BogdanAIP/chat-agent-platform",
            "branch": "main",
        },
    )
    pending = target.run_platform_update(
        {
            "procedure": "platform_update_v1",
            "action": "status",
            "request_id": pending_id,
        },
        local_app_data=local,
    )
    if pending.get("status") != "pending" or pending.get("receipt") is not None:
        raise SystemExit(32)

    expired_id = "3" * 32
    write_json(
        requests / f"{expired_id}.request.json",
        {
            "schema_version": 1,
            "request_id": expired_id,
            "status": "accepted",
            "accepted_at": "2000-01-01T00:00:00+00:00",
            "repository": "BogdanAIP/chat-agent-platform",
            "branch": "main",
        },
    )
    expired = target.run_platform_update(
        {
            "procedure": "platform_update_v1",
            "action": "status",
            "request_id": expired_id,
        },
        local_app_data=local,
    )
    if (
        expired.get("status") != "manual_recovery_required"
        or expired.get("reason") != "request_specific_updater_result_unavailable"
        or expired.get("receipt") is not None
    ):
        raise SystemExit(33)
'@

    & $pythonCommand.Source -c $pythonValidator $WorktreePath *> $null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    $nodeCommand = Get-Command 'node.exe' -ErrorAction SilentlyContinue
    if ($null -eq $nodeCommand) {
        $nodeCommand = Get-Command 'node' -ErrorAction SilentlyContinue
    }
    if ($null -eq $nodeCommand) {
        return $false
    }
    & $nodeCommand.Source --check $semanticPath *> $null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    try {
        $semanticSource = Get-Content -LiteralPath $semanticPath -Raw -Encoding utf8 -ErrorAction Stop
        $bootstrapManagerSource = Get-Content -LiteralPath $bootstrapManagerPath -Raw -Encoding utf8 -ErrorAction Stop
    }
    catch {
        return $false
    }

    $targetUpdaterPath = Join-Path $WorktreePath 'scripts\chat-platform-update.ps1'
    if (-not (Test-Path -LiteralPath $targetUpdaterPath -PathType Leaf)) {
        return $false
    }

    $targetTokens = $null
    $targetParseErrors = $null
    $targetUpdaterAst = [System.Management.Automation.Language.Parser]::ParseFile(
        $targetUpdaterPath,
        [ref]$targetTokens,
        [ref]$targetParseErrors
    )
    if ($null -eq $targetUpdaterAst -or @($targetParseErrors).Count -ne 0) {
        return $false
    }

    $writeResultFunction = $targetUpdaterAst.Find(
        {
            param($node)
            $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
                $node.Name -ceq 'Write-CapUpdateResult'
        },
        $true
    )
    if ($null -eq $writeResultFunction) {
        return $false
    }

    $writeBody = $writeResultFunction.Body.Extent.Text
    $requestWrite = 'Write-CapUpdateAtomicJson -Path $script:RequestResultPath -Value $result'
    $globalWrite = 'Write-CapUpdateAtomicJson -Path $ResultPath -Value $result'
    $requestWriteIndex = $writeBody.IndexOf($requestWrite, [System.StringComparison]::Ordinal)
    $globalWriteIndex = $writeBody.IndexOf($globalWrite, [System.StringComparison]::Ordinal)
    if (
        $requestWriteIndex -lt 0 -or
        $globalWriteIndex -lt 0 -or
        $requestWriteIndex -ge $globalWriteIndex -or
        -not $writeBody.Contains('request_id = if ([string]::IsNullOrWhiteSpace($RequestId))')
    ) {
        return $false
    }

    $writeResultCalls = @(
        $targetUpdaterAst.FindAll(
            {
                param($node)
                $node -is [System.Management.Automation.Language.CommandAst] -and
                    $node.GetCommandName() -ceq 'Write-CapUpdateResult'
            },
            $true
        )
    )
    if ($writeResultCalls.Count -lt 1) {
        return $false
    }

    $coreTokens = $null
    $coreParseErrors = $null
    $targetCoreAst = [System.Management.Automation.Language.Parser]::ParseFile(
        $targetCorePath,
        [ref]$coreTokens,
        [ref]$coreParseErrors
    )
    if ($null -eq $targetCoreAst -or @($coreParseErrors).Count -ne 0) {
        return $false
    }
    $atomicWriterFunction = $targetCoreAst.Find(
        {
            param($node)
            $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
                $node.Name -ceq 'Write-CapUpdateAtomicJson'
        },
        $true
    )
    if ($null -eq $atomicWriterFunction) {
        return $false
    }

    # Execute only the future target's bounded result writer + atomic JSON primitive
    # against isolated temp files. Never execute the target updater's top-level update path.
    $probeRoot = Join-Path ([System.IO.Path]::GetTempPath()) (
        'cap-update-result-contract-' + [guid]::NewGuid().ToString('N')
    )
    $probeScriptPath = Join-Path $probeRoot 'probe.ps1'
    $probeRequestPath = Join-Path $probeRoot 'request.updater.json'
    $probeGlobalPath = Join-Path $probeRoot 'global.json'
    $probeStatePath = Join-Path $probeRoot 'state.json'
    $probeLogPath = Join-Path $probeRoot 'update.log'
    $probeRequestId = '4' * 32
    $quote = {
        param([string]$Value)
        return "'" + $Value.Replace("'", "''") + "'"
    }

    try {
        New-Item -ItemType Directory -Force -Path $probeRoot | Out-Null
        $probeSource = @(
            'Set-StrictMode -Version Latest'
            '$ErrorActionPreference = ''Stop'''
            $atomicWriterFunction.Extent.Text
            $writeResultFunction.Extent.Text
            ('$RequestId = ' + (& $quote $probeRequestId))
            '$Action = ''Update'''
            '$script:CapUpdateRepository = ''BogdanAIP/chat-agent-platform'''
            '$script:CapUpdateBranch = ''main'''
            ('$StatePath = ' + (& $quote $probeStatePath))
            ('$LogPath = ' + (& $quote $probeLogPath))
            ('$ResultPath = ' + (& $quote $probeGlobalPath))
            ('$script:RequestResultPath = ' + (& $quote $probeRequestPath))
            'Write-CapUpdateResult -Status ''current'' -InstalledCommitSha (''a'' * 40) -TargetCommitSha (''a'' * 40) | Out-Null'
        ) -join [Environment]::NewLine
        [System.IO.File]::WriteAllText(
            $probeScriptPath,
            $probeSource + [Environment]::NewLine,
            [System.Text.UTF8Encoding]::new($false)
        )

        $probePwsh = Get-Command 'pwsh.exe' -ErrorAction SilentlyContinue
        if ($null -eq $probePwsh) {
            $probePwsh = Get-Command 'pwsh' -ErrorAction SilentlyContinue
        }
        if ($null -eq $probePwsh) {
            return $false
        }
        & $probePwsh.Source -NoLogo -NoProfile -ExecutionPolicy Bypass -File $probeScriptPath *> $null
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
        if (
            -not (Test-Path -LiteralPath $probeRequestPath -PathType Leaf) -or
            -not (Test-Path -LiteralPath $probeGlobalPath -PathType Leaf)
        ) {
            return $false
        }

        $requestResult = Get-Content -LiteralPath $probeRequestPath -Raw -Encoding utf8 |
            ConvertFrom-Json -ErrorAction Stop
        $globalResult = Get-Content -LiteralPath $probeGlobalPath -Raw -Encoding utf8 |
            ConvertFrom-Json -ErrorAction Stop
        foreach ($result in @($requestResult, $globalResult)) {
            if (
                [string]$result.request_id -cne $probeRequestId -or
                [string]$result.action -cne 'update' -or
                [string]$result.status -cne 'current' -or
                [string]$result.repository -cne 'BogdanAIP/chat-agent-platform' -or
                [string]$result.branch -cne 'main' -or
                [int]$result.process_id -le 0
            ) {
                return $false
            }
        }
        if ([int]$requestResult.process_id -ne [int]$globalResult.process_id) {
            return $false
        }
    }
    catch {
        return $false
    }
    finally {
        Remove-Item -LiteralPath $probeRoot -Recurse -Force -ErrorAction SilentlyContinue
    }

    foreach ($marker in @(
        "const PLATFORM_UPDATE_PROCEDURE = 'platform_update_v1';",
        "action: z.enum(['check', 'request_update', 'status'])",
        'platform_update_v1 status requires request_id',
        'request_id is valid only for platform_update_v1 status',
        'platformUpdateProcedureSchema'
    )) {
        if (-not $semanticSource.Contains($marker)) {
            return $false
        }
    }

    foreach ($marker in @(
        "'platform_update.py'",
        "'cli.py'",
        "'bin/semantic-control-plane-projection.mjs'",
        'Assert-ChatInstalledSixToolSemanticRuntime'
    )) {
        if (-not $bootstrapManagerSource.Contains($marker)) {
            return $false
        }
    }

    return $true
}


function Test-CapTargetSelfUpdateContract {
    param([Parameter(Mandatory)] [string]$WorktreePath)

    if (-not (Test-Path -LiteralPath $WorktreePath -PathType Container)) {
        return $false
    }

    $requirements = @(
        [pscustomobject]@{
            path = 'scripts\bootstrap-chat-platform.ps1'
            markers = @(
                'chat-platform-tray-update.ps1',
                'chat-platform-update-core.ps1',
                'chat-platform-update.ps1',
                'MAIN_UPDATE_UI=tray-more-menu',
                'MAIN_UPDATER_INSTALLED=True'
            )
        },
        [pscustomobject]@{
            path = 'scripts\chat-platform-tray.ps1'
            markers = @('chat-platform-tray-update.ps1', 'Register-CapUpdateTrayMenu')
        },
        [pscustomobject]@{
            path = 'scripts\chat-platform-tray-update.ps1'
            markers = @(
                'Register-CapUpdateTrayMenu',
                "'-Action', 'Update'",
                'platform-update-result.json',
                'ExpectedProcessId',
                'completed_at'
            )
        },
        [pscustomobject]@{
            path = 'scripts\chat-platform-update-core.ps1'
            markers = @('CapUpdateOfficialRemote', 'CapUpdateBranch', 'Sync-CapUpdateMain')
        },
        [pscustomobject]@{
            path = 'scripts\chat-platform-update.ps1'
            markers = @(
                'CapUpdateOfficialRemote',
                'New-CapUpdateWorktree',
                'Publish-CapInstalledVersionFromSource',
                'process_id = $PID',
                'platform-update-requests',
                'request_id = if',
                'if (-not $acquired)',
                'unowned_error=',
                'refusing update before quiesce',
                'pre-update-platform-stop',
                'update-recovery-platform-start'
            )
        }
    )

    foreach ($requirement in $requirements) {
        $path = Join-Path $WorktreePath ([string]$requirement.path)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            return $false
        }

        try {
            $text = Get-Content -LiteralPath $path -Raw -Encoding utf8 -ErrorAction Stop
        }
        catch {
            return $false
        }

        foreach ($marker in @($requirement.markers)) {
            if (-not $text.Contains([string]$marker)) {
                return $false
            }
        }
    }

    if (-not (Test-CapTargetPlatformUpdateProcedureContract -WorktreePath $WorktreePath)) {
        return $false
    }

    return $true
}


function Save-CapDecisionState {
    param(
        [Parameter(Mandatory)] $Decision,
        [string]$ErrorText
    )

    $currentState = Read-CapUpdateState -Path $StatePath
    $installedAt = if ($null -eq $currentState) { $null } else { [string]$currentState.installed_at }
    $status = [string]$Decision.status
    $lastError = $ErrorText
    if ($status -eq 'blocked' -and [string]::IsNullOrWhiteSpace($lastError)) {
        $lastError = 'remote_main_not_fast_forward'
    }
    $state = New-CapUpdateState `
        -InstalledCommitSha ([string]$Decision.installed_commit_sha) `
        -InstalledAt $installedAt `
        -Status $status `
        -TargetCommitSha ([string]$Decision.target_commit_sha) `
        -LastCheckedAt ([datetimeoffset]::UtcNow.ToString('o')) `
        -LastError $lastError
    Write-CapUpdateAtomicJson -Path $StatePath -Value $state
}

$mutex = New-Object System.Threading.Mutex($false, $MutexName)
$acquired = $false
$exitCode = 1
$worktree = $null
$wasRunning = $false
$platformStopAttempted = $false
$platformRestarted = $false

try {
    try {
        $acquired = $mutex.WaitOne($MutexTimeoutMilliseconds)
    }
    catch [System.Threading.AbandonedMutexException] {
        $acquired = $true
    }
    if (-not $acquired) {
        throw 'Another Chat Agent Platform update operation is still running.'
    }

    Remove-Item -LiteralPath $ResultPath -Force -ErrorAction SilentlyContinue
    Write-CapUpdateLog "action=$Action begin"
    $current = Read-CapUpdateState -Path $StatePath
    $decision = Get-CapUpdateDecision `
        -CacheRepo $CacheRepo `
        -RemoteUrl $RemoteUrl `
        -CurrentState $current
    Save-CapDecisionState -Decision $decision

    if ($Action -eq 'Check') {
        Write-CapUpdateLog "check status=$($decision.status) target=$($decision.target_commit_sha)"
        Write-CapUpdateResult `
            -Status ([string]$decision.status) `
            -InstalledCommitSha ([string]$decision.installed_commit_sha) `
            -TargetCommitSha ([string]$decision.target_commit_sha) `
            -Reason $(if ([string]$decision.status -eq 'blocked') { 'remote_main_not_fast_forward' } else { $null })
        $exitCode = if ([string]$decision.status -eq 'blocked') { 3 } else { 0 }
    }
    elseif ([string]$decision.status -eq 'current') {
        Write-CapUpdateLog 'update skipped because the installed commit is current'
        Write-CapUpdateResult `
            -Status 'current' `
            -InstalledCommitSha ([string]$decision.installed_commit_sha) `
            -TargetCommitSha ([string]$decision.target_commit_sha)
        $exitCode = 0
    }
    elseif ([string]$decision.status -eq 'blocked') {
        Write-CapUpdateLog 'update blocked because remote main is not a fast-forward from the installed commit'
        Write-CapUpdateResult `
            -Status 'blocked' `
            -InstalledCommitSha ([string]$decision.installed_commit_sha) `
            -TargetCommitSha ([string]$decision.target_commit_sha) `
            -Reason 'remote_main_not_fast_forward'
        $exitCode = 3
    }
    else {
        $wasRunning = Get-CapDesiredRunning
        $installing = New-CapUpdateState `
            -InstalledCommitSha ([string]$decision.installed_commit_sha) `
            -InstalledAt $(if ($null -eq $current) { $null } else { [string]$current.installed_at }) `
            -Status 'installing' `
            -TargetCommitSha ([string]$decision.target_commit_sha) `
            -LastCheckedAt ([datetimeoffset]::UtcNow.ToString('o'))
        Write-CapUpdateAtomicJson -Path $StatePath -Value $installing

        $worktree = New-CapUpdateWorktree `
            -CacheRepo $CacheRepo `
            -WorktreeRoot $WorktreeRoot `
            -TargetCommitSha ([string]$decision.target_commit_sha)

        if (-not (Test-CapTargetSelfUpdateContract -WorktreePath $worktree)) {
            Write-CapUpdateLog "update blocked reason=$TargetContinuityBlockedReason target=$($decision.target_commit_sha)"
            throw [System.InvalidOperationException]::new($TargetContinuityBlockedReason)
        }

        $bootstrap = Join-Path $worktree 'scripts\bootstrap-chat-platform.ps1'
        if (-not (Test-Path -LiteralPath $bootstrap -PathType Leaf)) {
            throw 'The exact main worktree does not contain the accepted bootstrap script.'
        }

        if (-not (Test-Path -LiteralPath $InstalledManagerPath -PathType Leaf)) {
            throw 'Installed manager command is missing before update quiesce.'
        }

        Write-CapUpdateLog "quiesce platform before bootstrap was_running=$wasRunning"
        $platformStopAttempted = $true
        Invoke-CapPwshProcess `
            -ScriptPath $InstalledManagerPath `
            -Arguments @('-Action', 'Stop', '-NoNotify') `
            -Label 'pre-update-platform-stop' `
            -TimeoutMilliseconds 120000 `
            -CaptureOutput:$false

        Write-CapUpdateLog "install target=$($decision.target_commit_sha) source=$worktree"
        Invoke-CapPwshProcess -ScriptPath $bootstrap -Label 'bootstrap-chat-platform'

        $receiptRecorded = Publish-CapInstalledVersionFromSource `
            -RepoRoot $worktree `
            -StatePath $StatePath
        if (-not $receiptRecorded) {
            throw 'Could not reconcile the installed version from the exact target worktree.'
        }

        $installed = Read-CapUpdateState -Path $StatePath
        if (
            $null -eq $installed -or
            [string]$installed.status -ne 'current' -or
            [string]$installed.installed_commit_sha -cne [string]$decision.target_commit_sha
        ) {
            throw 'Bootstrap completed without a matching exact installed-version receipt.'
        }

        $restarted = $false
        if ($wasRunning) {
            if (-not (Test-Path -LiteralPath $InstalledManagerPath -PathType Leaf)) {
                throw 'Updated manager command is missing after installation.'
            }
            Invoke-CapPwshProcess `
                -ScriptPath $InstalledManagerPath `
                -Arguments @('-Action', 'Start', '-NoNotify') `
                -Label 'updated-platform-start' `
                -TimeoutMilliseconds 120000 `
                -CaptureOutput:$false
            $platformRestarted = $true
            $restarted = $true
        }

        Write-CapUpdateLog "update success target=$($decision.target_commit_sha) restarted=$restarted"
        Write-CapUpdateResult `
            -Status 'updated' `
            -InstalledCommitSha ([string]$decision.target_commit_sha) `
            -TargetCommitSha ([string]$decision.target_commit_sha) `
            -Restarted:$restarted
        $exitCode = 0
    }
}
catch {
    $message = $_.Exception.Message
    Write-CapUpdateLog "error=$message"

    if ($platformStopAttempted -and $wasRunning -and -not $platformRestarted) {
        try {
            if (-not (Test-Path -LiteralPath $InstalledManagerPath -PathType Leaf)) {
                throw 'Installed manager command is missing during update recovery.'
            }
            Write-CapUpdateLog 'recovery restart begin'
            Invoke-CapPwshProcess `
                -ScriptPath $InstalledManagerPath `
                -Arguments @('-Action', 'Start', '-NoNotify') `
                -Label 'update-recovery-platform-start' `
                -TimeoutMilliseconds 120000 `
                -CaptureOutput:$false
            $platformRestarted = $true
            Write-CapUpdateLog 'recovery restart success'
        }
        catch {
            Write-CapUpdateLog "recovery_restart_error=$($_.Exception.Message)"
        }
    }

    if (-not $acquired) {
        # A process that never acquired the updater mutex is not update-state
        # authority. In particular, it must not overwrite the active owner's
        # state or terminal result while reporting a duplicate/busy failure.
        Write-CapUpdateLog "unowned_error=$message"
        $exitCode = 2
    }
    elseif ($message -ceq $TargetContinuityBlockedReason) {
        try {
            $state = Read-CapUpdateState -Path $StatePath
            $blockedState = New-CapUpdateState `
                -InstalledCommitSha $(if ($null -eq $state) { $null } else { [string]$state.installed_commit_sha }) `
                -InstalledAt $(if ($null -eq $state) { $null } else { [string]$state.installed_at }) `
                -Status 'blocked' `
                -TargetCommitSha $(if ($null -eq $state) { $null } else { [string]$state.target_commit_sha }) `
                -LastCheckedAt ([datetimeoffset]::UtcNow.ToString('o')) `
                -LastError $TargetContinuityBlockedReason
            Write-CapUpdateAtomicJson -Path $StatePath -Value $blockedState
        }
        catch {
            Write-CapUpdateLog "could_not_persist_blocked_state=$($_.Exception.Message)"
        }

        Write-CapUpdateResult `
            -Status 'blocked' `
            -InstalledCommitSha $(if ($null -eq $decision) { $null } else { [string]$decision.installed_commit_sha }) `
            -TargetCommitSha $(if ($null -eq $decision) { $null } else { [string]$decision.target_commit_sha }) `
            -Reason $TargetContinuityBlockedReason
        $exitCode = 4
    }
    else {
        try {
            $state = Read-CapUpdateState -Path $StatePath
            if ($null -ne $state) {
                $errorState = New-CapUpdateState `
                    -InstalledCommitSha ([string]$state.installed_commit_sha) `
                    -InstalledAt ([string]$state.installed_at) `
                    -Status 'error' `
                    -TargetCommitSha ([string]$state.target_commit_sha) `
                    -LastCheckedAt ([datetimeoffset]::UtcNow.ToString('o')) `
                    -LastError $message
                Write-CapUpdateAtomicJson -Path $StatePath -Value $errorState
            }
        }
        catch {
            Write-CapUpdateLog "could_not_persist_error_state=$($_.Exception.Message)"
        }
        Write-CapUpdateResult -Status 'error' -Reason $message -Restarted:$platformRestarted
        $exitCode = 1
    }
}
finally {
    if ($acquired -and -not [string]::IsNullOrWhiteSpace($worktree)) {
        try {
            Remove-CapUpdateWorktree -CacheRepo $CacheRepo -WorktreePath $worktree
        }
        catch {
            Write-CapUpdateLog "worktree_cleanup_error=$($_.Exception.Message)"
        }
    }
    if ($acquired) {
        try { $mutex.ReleaseMutex() } catch {}
    }
    $mutex.Dispose()
}

exit $exitCode
