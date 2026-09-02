[CmdletBinding()]
param(
    [ValidateSet('Check', 'Update')]
    [string]$Action = 'Check'
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

foreach ($directory in @($StateDir, $CacheRoot, $WorktreeRoot, $LogDir)) {
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

    [ordered]@{
        schema_version = 1
        action = $Action.ToLowerInvariant()
        status = $Status
        repository = $script:CapUpdateRepository
        branch = $script:CapUpdateBranch
        installed_commit_sha = if ([string]::IsNullOrWhiteSpace($InstalledCommitSha)) { $null } else { $InstalledCommitSha }
        target_commit_sha = if ([string]::IsNullOrWhiteSpace($TargetCommitSha)) { $null } else { $TargetCommitSha }
        restarted = $Restarted
        reason = if ([string]::IsNullOrWhiteSpace($Reason)) { $null } else { $Reason }
        state_path = $StatePath
        log_path = $LogPath
    } | ConvertTo-Json -Compress -Depth 5
}

function Get-CapDesiredRunning {
    if (-not (Test-Path -LiteralPath $DesiredStatePath -PathType Leaf)) {
        return $false
    }
    try {
        $state = Get-Content -LiteralPath $DesiredStatePath -Raw -Encoding utf8 | ConvertFrom-Json -ErrorAction Stop
        return ([string]$state.desired_state -eq 'running')
    }
    catch {
        return $false
    }
}

function Invoke-CapPwshProcess {
    param(
        [Parameter(Mandatory)] [string]$ScriptPath,
        [string[]]$Arguments = @(),
        [Parameter(Mandatory)] [string]$Label,
        [int]$TimeoutMilliseconds = $ProcessTimeoutMilliseconds
    )

    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pwsh
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
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
    try {
        if (-not $process.Start()) {
            throw "Could not start $Label."
        }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutMilliseconds)) {
            try { $process.Kill($true) } catch {}
            try { $process.WaitForExit(5000) | Out-Null } catch {}
            throw "$Label exceeded the update process timeout."
        }
        $stdout = $stdoutTask.GetAwaiter().GetResult()
        $stderr = $stderrTask.GetAwaiter().GetResult()
        if (-not [string]::IsNullOrWhiteSpace($stdout)) {
            Write-CapUpdateLog "$Label stdout:`n$stdout"
        }
        if (-not [string]::IsNullOrWhiteSpace($stderr)) {
            Write-CapUpdateLog "$Label stderr:`n$stderr"
        }
        if ($process.ExitCode -ne 0) {
            throw "$Label failed with exit code $($process.ExitCode)."
        }
    }
    finally {
        $process.Dispose()
    }
}

function Save-CapDecisionState {
    param(
        [Parameter(Mandatory)] $Decision,
        [string]$ErrorText
    )

    $current = Read-CapUpdateState -Path $StatePath
    $installedAt = if ($null -eq $current) { $null } else { [string]$current.installed_at }
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
        return
    }

    if ([string]$decision.status -eq 'current') {
        Write-CapUpdateLog 'update skipped because the installed commit is current'
        Write-CapUpdateResult `
            -Status 'current' `
            -InstalledCommitSha ([string]$decision.installed_commit_sha) `
            -TargetCommitSha ([string]$decision.target_commit_sha)
        $exitCode = 0
        return
    }
    if ([string]$decision.status -eq 'blocked') {
        Write-CapUpdateLog 'update blocked because remote main is not a fast-forward from the installed commit'
        Write-CapUpdateResult `
            -Status 'blocked' `
            -InstalledCommitSha ([string]$decision.installed_commit_sha) `
            -TargetCommitSha ([string]$decision.target_commit_sha) `
            -Reason 'remote_main_not_fast_forward'
        $exitCode = 3
        return
    }

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
    $bootstrap = Join-Path $worktree 'scripts\bootstrap-chat-platform.ps1'
    if (-not (Test-Path -LiteralPath $bootstrap -PathType Leaf)) {
        throw 'The exact main worktree does not contain the accepted bootstrap script.'
    }

    Write-CapUpdateLog "install target=$($decision.target_commit_sha) source=$worktree"
    Invoke-CapPwshProcess -ScriptPath $bootstrap -Label 'bootstrap-chat-platform'

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
            -TimeoutMilliseconds 120000
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
catch {
    $message = $_.Exception.Message
    Write-CapUpdateLog "error=$message"
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
    Write-CapUpdateResult -Status 'error' -Reason $message
    $exitCode = 1
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
