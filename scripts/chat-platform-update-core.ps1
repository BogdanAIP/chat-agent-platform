Set-StrictMode -Version Latest

$script:CapUpdateRepository = 'BogdanAIP/chat-agent-platform'
$script:CapUpdateBranch = 'main'
$script:CapUpdateOfficialRemote = 'https://github.com/BogdanAIP/chat-agent-platform.git'
$script:CapUpdateStateSchema = 1
$script:CapUpdateShaPattern = '^[0-9a-f]{40}$'

function Get-CapUpdateGitExecutable {
    $command = Get-Command 'git.exe' -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        $command = Get-Command 'git' -ErrorAction SilentlyContinue
    }
    if ($null -eq $command) {
        throw 'Git is required for Chat Agent Platform update checks.'
    }
    return [string]$command.Source
}

function Invoke-CapUpdateGit {
    param(
        [Parameter(Mandatory)] [string[]]$Arguments,
        [string]$WorkingDirectory,
        [switch]$AllowFailure
    )

    $git = Get-CapUpdateGitExecutable
    $allArguments = [System.Collections.Generic.List[string]]::new()
    if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) {
        $allArguments.Add('-C')
        $allArguments.Add($WorkingDirectory)
    }
    foreach ($argument in $Arguments) {
        $allArguments.Add([string]$argument)
    }

    $output = @(& $git @allArguments 2>&1)
    $exitCode = $LASTEXITCODE
    $text = ($output | Out-String).Trim()

    if ($exitCode -ne 0 -and -not $AllowFailure) {
        throw (
            "git {0} failed with exit code {1}: {2}" -f `
                ($Arguments -join ' '),
                $exitCode,
                $text
        )
    }

    return [pscustomobject]@{
        exit_code = $exitCode
        text = $text
    }
}

function Test-CapUpdateOfficialRemote {
    param([string]$RemoteUrl)

    if ([string]::IsNullOrWhiteSpace($RemoteUrl)) {
        return $false
    }

    $value = $RemoteUrl.Trim().TrimEnd('/')
    return (
        $value -ieq 'https://github.com/BogdanAIP/chat-agent-platform.git' -or
        $value -ieq 'https://github.com/BogdanAIP/chat-agent-platform' -or
        $value -ieq 'git@github.com:BogdanAIP/chat-agent-platform.git' -or
        $value -ieq 'ssh://git@github.com/BogdanAIP/chat-agent-platform.git'
    )
}

function Assert-CapUpdateSha {
    param(
        [Parameter(Mandatory)] [string]$Value,
        [Parameter(Mandatory)] [string]$Label
    )

    $normalized = $Value.Trim().ToLowerInvariant()
    if ($normalized -notmatch $script:CapUpdateShaPattern) {
        throw "$Label must be a 40-character lowercase commit SHA."
    }
    return $normalized
}

function Write-CapUpdateAtomicJson {
    param(
        [Parameter(Mandatory)] [string]$Path,
        [Parameter(Mandatory)] $Value
    )

    $parent = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $temporary = "$Path.new-$PID-$([guid]::NewGuid().ToString('N'))"
    try {
        $json = $Value | ConvertTo-Json -Depth 8
        [System.IO.File]::WriteAllText(
            $temporary,
            $json + [Environment]::NewLine,
            [System.Text.UTF8Encoding]::new($false)
        )
        Move-Item -LiteralPath $temporary -Destination $Path -Force
    }
    finally {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
    }
}

function New-CapUpdateState {
    param(
        [string]$InstalledCommitSha,
        [string]$InstalledAt,
        [ValidateSet('unknown', 'current', 'update_available', 'installing', 'blocked', 'error')]
        [string]$Status = 'unknown',
        [string]$TargetCommitSha,
        [string]$LastCheckedAt,
        [string]$LastError
    )

    $installed = if ([string]::IsNullOrWhiteSpace($InstalledCommitSha)) {
        $null
    }
    else {
        Assert-CapUpdateSha -Value $InstalledCommitSha -Label 'installed_commit_sha'
    }
    $target = if ([string]::IsNullOrWhiteSpace($TargetCommitSha)) {
        $null
    }
    else {
        Assert-CapUpdateSha -Value $TargetCommitSha -Label 'target_commit_sha'
    }

    return [ordered]@{
        schema_version = $script:CapUpdateStateSchema
        repository = $script:CapUpdateRepository
        branch = $script:CapUpdateBranch
        installed_commit_sha = $installed
        installed_at = if ([string]::IsNullOrWhiteSpace($InstalledAt)) { $null } else { $InstalledAt }
        status = $Status
        target_commit_sha = $target
        last_checked_at = if ([string]::IsNullOrWhiteSpace($LastCheckedAt)) { $null } else { $LastCheckedAt }
        last_error = if ([string]::IsNullOrWhiteSpace($LastError)) { $null } else { $LastError }
    }
}

function Read-CapUpdateState {
    param([Parameter(Mandatory)] [string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }

    try {
        $value = Get-Content -LiteralPath $Path -Raw -Encoding utf8 | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        throw "Update state is unreadable or invalid JSON: $Path"
    }

    $expected = @(
        'schema_version',
        'repository',
        'branch',
        'installed_commit_sha',
        'installed_at',
        'status',
        'target_commit_sha',
        'last_checked_at',
        'last_error'
    )
    $actual = @($value.PSObject.Properties.Name | Sort-Object)
    if (($actual -join "`n") -cne (@($expected | Sort-Object) -join "`n")) {
        throw 'Update state keys do not match the accepted schema.'
    }
    if ([int]$value.schema_version -ne $script:CapUpdateStateSchema) {
        throw 'Update state schema_version is unsupported.'
    }
    if ([string]$value.repository -cne $script:CapUpdateRepository) {
        throw 'Update state repository identity is invalid.'
    }
    if ([string]$value.branch -cne $script:CapUpdateBranch) {
        throw 'Update state branch identity is invalid.'
    }
    if ([string]$value.status -notin @(
        'unknown', 'current', 'update_available', 'installing', 'blocked', 'error'
    )) {
        throw 'Update state status is invalid.'
    }

    $installed = $value.installed_commit_sha
    if ($null -ne $installed) {
        $null = Assert-CapUpdateSha -Value ([string]$installed) -Label 'installed_commit_sha'
    }
    $target = $value.target_commit_sha
    if ($null -ne $target) {
        $null = Assert-CapUpdateSha -Value ([string]$target) -Label 'target_commit_sha'
    }

    return $value
}

function Publish-CapInstalledVersionFromSource {
    param(
        [Parameter(Mandatory)] [string]$RepoRoot,
        [Parameter(Mandatory)] [string]$StatePath
    )

    if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
        return $false
    }

    try {
        $remote = (Invoke-CapUpdateGit -WorkingDirectory $RepoRoot -Arguments @(
            'remote', 'get-url', 'origin'
        )).text
        if (-not (Test-CapUpdateOfficialRemote -RemoteUrl $remote)) {
            return $false
        }

        $head = Assert-CapUpdateSha `
            -Value (Invoke-CapUpdateGit -WorkingDirectory $RepoRoot -Arguments @(
                'rev-parse', 'HEAD'
            )).text `
            -Label 'source HEAD'
        $dirty = (Invoke-CapUpdateGit -WorkingDirectory $RepoRoot -Arguments @(
            'status', '--porcelain'
        )).text
        if (-not [string]::IsNullOrWhiteSpace($dirty)) {
            return $false
        }

        $now = [datetimeoffset]::UtcNow.ToString('o')
        $state = New-CapUpdateState `
            -InstalledCommitSha $head `
            -InstalledAt $now `
            -Status 'current' `
            -TargetCommitSha $head `
            -LastCheckedAt $now
        Write-CapUpdateAtomicJson -Path $StatePath -Value $state
        return $true
    }
    catch {
        return $false
    }
}

function Initialize-CapUpdateCacheRepository {
    param(
        [Parameter(Mandatory)] [string]$CacheRepo,
        [Parameter(Mandatory)] [string]$RemoteUrl
    )

    $parent = Split-Path -Parent $CacheRepo
    New-Item -ItemType Directory -Force -Path $parent | Out-Null

    if (-not (Test-Path -LiteralPath $CacheRepo -PathType Container)) {
        $null = Invoke-CapUpdateGit -Arguments @('init', '--bare', $CacheRepo)
        $null = Invoke-CapUpdateGit -WorkingDirectory $CacheRepo -Arguments @(
            'remote', 'add', 'origin', $RemoteUrl
        )
    }

    $bare = (Invoke-CapUpdateGit -WorkingDirectory $CacheRepo -Arguments @(
        'rev-parse', '--is-bare-repository'
    )).text
    if ($bare -cne 'true') {
        throw 'Update cache repository is not a bare Git repository.'
    }

    $actualRemote = (Invoke-CapUpdateGit -WorkingDirectory $CacheRepo -Arguments @(
        'remote', 'get-url', 'origin'
    )).text
    if ($actualRemote.Trim() -cne $RemoteUrl.Trim()) {
        throw 'Update cache origin does not match the fixed update source.'
    }
}

function Sync-CapUpdateMain {
    param(
        [Parameter(Mandatory)] [string]$CacheRepo,
        [Parameter(Mandatory)] [string]$RemoteUrl
    )

    Initialize-CapUpdateCacheRepository -CacheRepo $CacheRepo -RemoteUrl $RemoteUrl
    $null = Invoke-CapUpdateGit -WorkingDirectory $CacheRepo -Arguments @(
        'fetch',
        '--atomic',
        '--prune',
        'origin',
        '+refs/heads/main:refs/remotes/origin/main'
    )

    $target = (Invoke-CapUpdateGit -WorkingDirectory $CacheRepo -Arguments @(
        'rev-parse', 'refs/remotes/origin/main^{commit}'
    )).text
    return (Assert-CapUpdateSha -Value $target -Label 'remote main')
}

function Test-CapUpdateFastForward {
    param(
        [Parameter(Mandatory)] [string]$CacheRepo,
        [Parameter(Mandatory)] [string]$InstalledCommitSha,
        [Parameter(Mandatory)] [string]$TargetCommitSha
    )

    $installed = Assert-CapUpdateSha -Value $InstalledCommitSha -Label 'installed commit'
    $target = Assert-CapUpdateSha -Value $TargetCommitSha -Label 'target commit'

    $object = Invoke-CapUpdateGit -WorkingDirectory $CacheRepo -Arguments @(
        'cat-file', '-e', "$installed`^{commit}"
    ) -AllowFailure
    if ($object.exit_code -ne 0) {
        throw 'Installed commit is not present in the verified update cache.'
    }

    $result = Invoke-CapUpdateGit -WorkingDirectory $CacheRepo -Arguments @(
        'merge-base', '--is-ancestor', $installed, $target
    ) -AllowFailure
    if ($result.exit_code -eq 0) {
        return $true
    }
    if ($result.exit_code -eq 1) {
        return $false
    }
    throw "Could not verify update ancestry: $($result.text)"
}

function New-CapUpdateWorktree {
    param(
        [Parameter(Mandatory)] [string]$CacheRepo,
        [Parameter(Mandatory)] [string]$WorktreeRoot,
        [Parameter(Mandatory)] [string]$TargetCommitSha
    )

    $target = Assert-CapUpdateSha -Value $TargetCommitSha -Label 'target commit'
    New-Item -ItemType Directory -Force -Path $WorktreeRoot | Out-Null
    $name = 'main-{0}-{1}' -f $target.Substring(0, 12), ([guid]::NewGuid().ToString('N').Substring(0, 8))
    $path = Join-Path $WorktreeRoot $name
    if (Test-Path -LiteralPath $path) {
        throw "Generated update worktree path already exists: $path"
    }

    $null = Invoke-CapUpdateGit -WorkingDirectory $CacheRepo -Arguments @(
        'worktree', 'add', '--detach', $path, $target
    )

    $actual = Assert-CapUpdateSha `
        -Value (Invoke-CapUpdateGit -WorkingDirectory $path -Arguments @(
            'rev-parse', 'HEAD'
        )).text `
        -Label 'update worktree HEAD'
    if ($actual -cne $target) {
        throw "Update worktree HEAD mismatch: expected=$target actual=$actual"
    }
    $dirty = (Invoke-CapUpdateGit -WorkingDirectory $path -Arguments @(
        'status', '--porcelain'
    )).text
    if (-not [string]::IsNullOrWhiteSpace($dirty)) {
        throw 'Update worktree is not clean.'
    }

    return $path
}

function Remove-CapUpdateWorktree {
    param(
        [Parameter(Mandatory)] [string]$CacheRepo,
        [string]$WorktreePath
    )

    if ([string]::IsNullOrWhiteSpace($WorktreePath)) {
        return
    }

    $null = Invoke-CapUpdateGit -WorkingDirectory $CacheRepo -Arguments @(
        'worktree', 'remove', '--force', $WorktreePath
    ) -AllowFailure
    $null = Invoke-CapUpdateGit -WorkingDirectory $CacheRepo -Arguments @(
        'worktree', 'prune'
    ) -AllowFailure
}

function Get-CapUpdateDecision {
    param(
        [Parameter(Mandatory)] [string]$CacheRepo,
        [Parameter(Mandatory)] [string]$RemoteUrl,
        $CurrentState
    )

    $target = Sync-CapUpdateMain -CacheRepo $CacheRepo -RemoteUrl $RemoteUrl
    $installed = if ($null -eq $CurrentState -or $null -eq $CurrentState.installed_commit_sha) {
        $null
    }
    else {
        Assert-CapUpdateSha -Value ([string]$CurrentState.installed_commit_sha) -Label 'installed commit'
    }

    if ($null -ne $installed -and $installed -ceq $target) {
        return [pscustomobject]@{
            status = 'current'
            installed_commit_sha = $installed
            target_commit_sha = $target
        }
    }

    if ($null -ne $installed) {
        $fastForward = Test-CapUpdateFastForward `
            -CacheRepo $CacheRepo `
            -InstalledCommitSha $installed `
            -TargetCommitSha $target
        if (-not $fastForward) {
            return [pscustomobject]@{
                status = 'blocked'
                installed_commit_sha = $installed
                target_commit_sha = $target
            }
        }
    }

    return [pscustomobject]@{
        status = 'update_available'
        installed_commit_sha = $installed
        target_commit_sha = $target
    }
}
