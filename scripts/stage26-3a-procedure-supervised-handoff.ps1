[CmdletBinding()]
param(
    [ValidateSet('Start', 'Stop', 'Status')]
    [string]$Action = 'Status',

    [string]$FilesRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    throw 'LOCALAPPDATA is unavailable.'
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$localRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
$stateDir = Join-Path $localRoot 'state'
$desiredStateFile = Join-Path $stateDir 'desired-state.json'
$installedManager = Join-Path $localRoot 'app\scripts\chat-platform.ps1'
$directHarness = Join-Path $PSScriptRoot 'stage26-3a-procedure-direct-tunnel.ps1'
$handoffStateFile = Join-Path $stateDir 'stage26-3a-procedure-supervised-handoff.json'

function Initialize-StateDirectory {
    New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
}

function Get-PersistentDesiredState {
    if (-not (Test-Path -LiteralPath $desiredStateFile -PathType Leaf)) {
        throw "Accepted persistent desired state is missing: $desiredStateFile"
    }

    try {
        $state = Get-Content -LiteralPath $desiredStateFile -Raw | ConvertFrom-Json
    }
    catch {
        throw "Persistent desired state is invalid: $($_.Exception.Message)"
    }

    if (
        $null -eq $state.PSObject.Properties['desired_state'] -or
        [string]$state.desired_state -notin @('running', 'stopped')
    ) {
        throw 'Persistent desired state is missing a supported desired_state value.'
    }

    return [string]$state.desired_state
}

function Get-HandoffState {
    if (-not (Test-Path -LiteralPath $handoffStateFile -PathType Leaf)) {
        return $null
    }

    try {
        $state = Get-Content -LiteralPath $handoffStateFile -Raw | ConvertFrom-Json
    }
    catch {
        throw "Stage 26.3A handoff state is invalid: $($_.Exception.Message)"
    }

    if (
        $null -eq $state.PSObject.Properties['previous_desired_state'] -or
        [string]$state.previous_desired_state -notin @('running', 'stopped')
    ) {
        throw 'Stage 26.3A handoff state has no supported previous_desired_state.'
    }

    return $state
}

function Save-HandoffState {
    param(
        [Parameter(Mandatory)]
        [ValidateSet('preparing', 'running')]
        [string]$Phase,

        [Parameter(Mandatory)]
        [ValidateSet('running', 'stopped')]
        [string]$PreviousDesiredState,

        [Parameter(Mandatory)]
        [string]$QualificationFilesRoot
    )

    Initialize-StateDirectory
    $temporary = "$handoffStateFile.new-$PID"
    $payload = [ordered]@{
        schema_version = 1
        phase = $Phase
        previous_desired_state = $PreviousDesiredState
        files_root = $QualificationFilesRoot
        repo_root = $repoRoot
        updated_at = (Get-Date).ToUniversalTime().ToString('o')
    }

    try {
        $payload |
            ConvertTo-Json -Depth 4 |
            Set-Content -LiteralPath $temporary -Encoding utf8
        Move-Item -LiteralPath $temporary -Destination $handoffStateFile -Force
    }
    finally {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-InstalledManagerAction {
    param(
        [Parameter(Mandatory)]
        [ValidateSet('Start', 'Stop')]
        [string]$ManagerAction
    )

    if (-not (Test-Path -LiteralPath $installedManager -PathType Leaf)) {
        throw "Accepted installed manager is missing: $installedManager"
    }

    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    & $pwsh `
        -NoLogo `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $installedManager `
        -Action $ManagerAction `
        -NoNotify
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        throw "Installed Chat Agent Platform manager $ManagerAction failed with exit code $code."
    }
}

function Invoke-DirectHarness {
    param(
        [Parameter(Mandatory)]
        [ValidateSet('Start', 'Stop', 'Status')]
        [string]$DirectAction,

        [string]$QualificationFilesRoot
    )

    if (-not (Test-Path -LiteralPath $directHarness -PathType Leaf)) {
        throw "Stage 26.3A direct tunnel harness is missing: $directHarness"
    }

    if ($DirectAction -eq 'Start') {
        & $directHarness -Action Start -FilesRoot $QualificationFilesRoot
    }
    else {
        & $directHarness -Action $DirectAction
    }
}

function Restore-AcceptedPlatform {
    param(
        [Parameter(Mandatory)]
        [ValidateSet('running', 'stopped')]
        [string]$PreviousDesiredState
    )

    if ($PreviousDesiredState -eq 'running') {
        Invoke-InstalledManagerAction -ManagerAction Start
        Write-Host 'STAGE26_3A_PLATFORM_RESTORE=running'
    }
    else {
        Invoke-InstalledManagerAction -ManagerAction Stop
        Write-Host 'STAGE26_3A_PLATFORM_RESTORE=stopped'
    }
}

function Start-SupervisedQualification {
    Initialize-StateDirectory

    if ([string]::IsNullOrWhiteSpace($FilesRoot)) {
        throw 'Start requires -FilesRoot.'
    }
    if (-not (Test-Path -LiteralPath $FilesRoot -PathType Container)) {
        throw "FilesRoot must be an existing directory: $FilesRoot"
    }
    if ($null -ne (Get-HandoffState)) {
        throw 'A Stage 26.3A supervised handoff receipt already exists. Run -Action Stop before starting another qualification route.'
    }

    $resolvedFilesRoot = (Resolve-Path -LiteralPath $FilesRoot).Path
    $previousDesiredState = Get-PersistentDesiredState

    # Persist the rollback intent before changing accepted platform desired state.
    # If setup is interrupted, a later -Action Stop can still restore user intent.
    Save-HandoffState `
        -Phase preparing `
        -PreviousDesiredState $previousDesiredState `
        -QualificationFilesRoot $resolvedFilesRoot

    try {
        # Public manager Stop participates in the accepted lifecycle mutex and
        # writes desired_state=stopped. The supervisor may remain alive, but it
        # is no longer authorized to resurrect the production direct tunnel
        # while the qualification route temporarily owns the persistent tunnel id.
        Invoke-InstalledManagerAction -ManagerAction Stop

        Invoke-DirectHarness `
            -DirectAction Start `
            -QualificationFilesRoot $resolvedFilesRoot

        Save-HandoffState `
            -Phase running `
            -PreviousDesiredState $previousDesiredState `
            -QualificationFilesRoot $resolvedFilesRoot

        Write-Host "STAGE26_3A_PREVIOUS_DESIRED_STATE=$previousDesiredState"
        Write-Host 'STAGE26_3A_SUPERVISED_HANDOFF=ready'
    }
    catch {
        $failure = $_.Exception.Message
        try { Invoke-DirectHarness -DirectAction Stop } catch {}

        $restoreFailure = $null
        try {
            Restore-AcceptedPlatform -PreviousDesiredState $previousDesiredState
        }
        catch {
            $restoreFailure = $_.Exception.Message
        }

        Remove-Item -LiteralPath $handoffStateFile -Force -ErrorAction SilentlyContinue

        if (-not [string]::IsNullOrWhiteSpace($restoreFailure)) {
            throw "Stage 26.3A supervised handoff failed: $failure; accepted platform restore also failed: $restoreFailure"
        }
        throw "Stage 26.3A supervised handoff failed: $failure"
    }
}

function Stop-SupervisedQualification {
    Initialize-StateDirectory
    $handoff = Get-HandoffState

    # Killing the qualification-owned route is safe even when the handoff
    # receipt is absent; restoration without a receipt is deliberately refused.
    Invoke-DirectHarness -DirectAction Stop

    if ($null -eq $handoff) {
        Write-Host 'STAGE26_3A_SUPERVISED_HANDOFF=stopped-no-restore-receipt'
        return
    }

    $previousDesiredState = [string]$handoff.previous_desired_state
    Restore-AcceptedPlatform -PreviousDesiredState $previousDesiredState
    Remove-Item -LiteralPath $handoffStateFile -Force -ErrorAction SilentlyContinue
    Write-Host 'STAGE26_3A_SUPERVISED_HANDOFF=stopped'
}

function Get-SupervisedQualificationStatus {
    Initialize-StateDirectory
    $handoff = Get-HandoffState
    $directRaw = (@(Invoke-DirectHarness -DirectAction Status) | Out-String).Trim()
    try {
        $direct = $directRaw | ConvertFrom-Json
    }
    catch {
        throw "Stage 26.3A direct harness returned invalid status JSON: $directRaw"
    }

    [ordered]@{
        schema_version = 1
        handoff_present = ($null -ne $handoff)
        handoff_phase = if ($null -ne $handoff) { [string]$handoff.phase } else { $null }
        previous_desired_state = if ($null -ne $handoff) { [string]$handoff.previous_desired_state } else { $null }
        current_desired_state = Get-PersistentDesiredState
        qualification_running = [bool]$direct.running
        qualification_ready = [bool]$direct.ready
        qualification_pid = $direct.pid
        tunnel_id = $direct.tunnel_id
        files_root = $direct.files_root
        procedure_state_root = $direct.procedure_state_root
    }
}

switch ($Action) {
    'Start' { Start-SupervisedQualification }
    'Stop' { Stop-SupervisedQualification }
    'Status' { Get-SupervisedQualificationStatus | ConvertTo-Json -Depth 4 }
}
