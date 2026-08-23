[CmdletBinding()]
param(
    [ValidateSet('Run', 'Reconcile', 'Status')]
    [string]$Action = 'Status',

    [string]$ManagerCommandPath,

    [ValidateRange(2, 300)]
    [int]$LoopIntervalSeconds = 10,

    [switch]$NoRecovery
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    throw 'LOCALAPPDATA is unavailable.'
}

$LocalRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
$StateDir = Join-Path $LocalRoot 'state'
$LogDir = Join-Path $LocalRoot 'logs'
$OwnerFile = Join-Path $StateDir 'manager-owner.json'
$DesiredStateFile = Join-Path $StateDir 'desired-state.json'
$SupervisorStateFile = Join-Path $StateDir 'supervisor.json'
$RecoveryStateFile = Join-Path $StateDir 'supervisor-recovery.json'
$ChatGptE2EFile = Join-Path $StateDir 'chatgpt-e2e.json'
$SupervisorLog = Join-Path $LogDir 'supervisor.log'
$DefaultManagerCommandPath = Join-Path $PSScriptRoot 'chat-platform.ps1'
$InstalledDirectControllerPath = Join-Path $LocalRoot 'app\scripts\semantic-direct-controller.ps1'

$SupervisorMutexName = 'Local\ChatAgentPlatformTransportSupervisor'
$ManagerOperationMutexName = 'Local\ChatAgentPlatformControllerOperation'
$ManagerOperationMutexTimeoutMilliseconds = 30000
$ManagerStatusTimeoutMilliseconds = 20000
$ControllerMutationTimeoutMilliseconds = 90000
$BurstBackoffSeconds = @(0, 2, 10, 30)
$SlowRetrySeconds = 300
$WaitProbeSeconds = 60
$MaxBurstAttempts = $BurstBackoffSeconds.Count
$ChatGptReceiptFreshnessSeconds = 600

function Initialize-SupervisorDirectories {
    foreach ($path in @($StateDir, $LogDir)) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
    }
}

function ConvertTo-UtcIsoString {
    param($Value)

    if ($null -eq $Value) { return $null }

    if ($Value -is [datetimeoffset]) {
        return ([datetimeoffset]$Value).ToUniversalTime().ToString('o')
    }

    if ($Value -is [datetime]) {
        $date = [datetime]$Value
        if ($date.Kind -eq [DateTimeKind]::Unspecified) {
            $date = [datetime]::SpecifyKind($date, [DateTimeKind]::Utc)
        }
        else {
            $date = $date.ToUniversalTime()
        }
        return $date.ToString('o')
    }

    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) { return $null }

    try {
        $date = [datetime]::Parse(
            $text,
            [Globalization.CultureInfo]::InvariantCulture,
            [Globalization.DateTimeStyles]::RoundtripKind
        )
    }
    catch {
        # Legacy supervisor state could contain a culture-formatted UTC wall
        # clock after ConvertFrom-Json materialized an ISO string as DateTime.
        # The state schema defines these timestamps as UTC, so an unspecified
        # legacy value must be repaired as UTC rather than reinterpreted as local.
        $date = [datetime]::Parse($text, [Globalization.CultureInfo]::CurrentCulture)
    }

    if ($date.Kind -eq [DateTimeKind]::Unspecified) {
        $date = [datetime]::SpecifyKind($date, [DateTimeKind]::Utc)
    }
    else {
        $date = $date.ToUniversalTime()
    }
    return $date.ToString('o')
}

function Write-AtomicJson {
    param(
        [Parameter(Mandatory)] [string]$Path,
        [Parameter(Mandatory)] $Value,
        [ValidateRange(2, 20)] [int]$Depth = 8
    )

    $temporary = "$Path.new-$PID"
    try {
        $Value | ConvertTo-Json -Depth $Depth | Set-Content -LiteralPath $temporary -Encoding utf8

        # Readers such as qualification may have the previous file open for a
        # very short interval on Windows. Retry only the atomic replacement;
        # never rerun the operation that produced the state being published.
        for ($attempt = 1; $attempt -le 20; $attempt++) {
            try {
                Move-Item -LiteralPath $temporary -Destination $Path -Force
                return
            }
            catch {
                if ($attempt -eq 20) { throw }
                Start-Sleep -Milliseconds 50
            }
        }
    }
    finally {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
    }
}

function Write-SupervisorLog {
    param(
        [Parameter(Mandatory)] [string]$Message,
        [ValidateSet('INFO', 'WARN', 'ERROR')] [string]$Level = 'INFO'
    )

    Initialize-SupervisorDirectories
    $line = '{0} [{1}] {2}' -f (Get-Date).ToUniversalTime().ToString('o'), $Level, $Message
    Add-Content -LiteralPath $SupervisorLog -Value $line -Encoding utf8
}

function Get-EffectiveManagerCommandPath {
    $candidate = if (-not [string]::IsNullOrWhiteSpace($ManagerCommandPath)) {
        $ManagerCommandPath
    }
    else {
        $DefaultManagerCommandPath
    }

    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "Manager command is unavailable: $candidate"
    }
    return [System.IO.Path]::GetFullPath($candidate)
}

function Invoke-BoundedPowerShell {
    param(
        [Parameter(Mandatory)] [string]$ScriptPath,
        [Parameter(Mandatory)] [string[]]$Arguments,
        [ValidateRange(100, 180000)] [int]$TimeoutMilliseconds,
        [bool]$CaptureOutput = $true
    )

    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    $info = [System.Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $pwsh
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $CaptureOutput
    $info.RedirectStandardError = $CaptureOutput

    foreach ($argument in @('-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $ScriptPath)) {
        $info.ArgumentList.Add([string]$argument)
    }
    foreach ($argument in $Arguments) {
        $info.ArgumentList.Add([string]$argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $info

    try {
        if (-not $process.Start()) {
            return [pscustomobject]@{ exit_code = -1; timed_out = $false; stdout = ''; stderr = 'process_start_failed' }
        }

        $stdoutTask = if ($CaptureOutput) { $process.StandardOutput.ReadToEndAsync() } else { $null }
        $stderrTask = if ($CaptureOutput) { $process.StandardError.ReadToEndAsync() } else { $null }
        if (-not $process.WaitForExit($TimeoutMilliseconds)) {
            try { $process.Kill($true) } catch {}
            $process.WaitForExit()
            return [pscustomobject]@{
                exit_code = -1
                timed_out = $true
                stdout = if ($CaptureOutput) { $stdoutTask.GetAwaiter().GetResult() } else { '' }
                stderr = if ($CaptureOutput) { $stderrTask.GetAwaiter().GetResult() } else { '' }
            }
        }

        $process.WaitForExit()
        return [pscustomobject]@{
            exit_code = $process.ExitCode
            timed_out = $false
            stdout = if ($CaptureOutput) { $stdoutTask.GetAwaiter().GetResult() } else { '' }
            stderr = if ($CaptureOutput) { $stderrTask.GetAwaiter().GetResult() } else { '' }
        }
    }
    finally {
        $process.Dispose()
    }
}

function Get-ManagerStatus {
    $commandPath = Get-EffectiveManagerCommandPath
    $result = Invoke-BoundedPowerShell `
        -ScriptPath $commandPath `
        -Arguments @('-Action', 'Status', '-NoNotify') `
        -TimeoutMilliseconds $ManagerStatusTimeoutMilliseconds `
        -CaptureOutput $true

    if ($result.timed_out) {
        throw 'Manager status timed out.'
    }
    if ($result.exit_code -ne 0) {
        throw "Manager status failed with exit code $($result.exit_code)."
    }

    try {
        return ([string]$result.stdout | ConvertFrom-Json -ErrorAction Stop)
    }
    catch {
        throw 'Manager status returned invalid JSON.'
    }
}

function Get-ManagerOwner {
    if (-not (Test-Path -LiteralPath $OwnerFile -PathType Leaf)) {
        return $null
    }

    try {
        $owner = Get-Content -LiteralPath $OwnerFile -Raw | ConvertFrom-Json
        if (
            $null -eq $owner.PSObject.Properties['controller_path'] -or
            [string]::IsNullOrWhiteSpace([string]$owner.controller_path)
        ) {
            throw 'controller_path missing'
        }
        return $owner
    }
    catch {
        throw 'manager-owner.json is invalid.'
    }
}

function Save-LegacyDesiredStateMigration {
    param(
        [Parameter(Mandatory)]
        [ValidateSet('running', 'stopped')]
        [string]$DesiredState
    )

    Write-AtomicJson -Path $DesiredStateFile -Value ([ordered]@{
        schema_version = 1
        desired_state = $DesiredState
        source = 'legacy_migration'
        updated_at = (Get-Date).ToUniversalTime().ToString('o')
    })
}

function Get-PersistedDesiredState {
    if (-not (Test-Path -LiteralPath $DesiredStateFile -PathType Leaf)) {
        $legacyOwner = Get-ManagerOwner
        $legacyState = if ($null -ne $legacyOwner) { 'running' } else { 'stopped' }
        Save-LegacyDesiredStateMigration -DesiredState $legacyState
    }

    try {
        $state = Get-Content -LiteralPath $DesiredStateFile -Raw | ConvertFrom-Json
        if (
            $null -eq $state.PSObject.Properties['desired_state'] -or
            [string]$state.desired_state -notin @('running', 'stopped')
        ) {
            throw 'desired_state missing or unsupported'
        }
        return $state
    }
    catch {
        throw 'desired-state.json is invalid.'
    }
}

function Get-DesiredState {
    $intent = Get-PersistedDesiredState
    $owner = Get-ManagerOwner
    return [pscustomobject]@{
        desired_state = [string]$intent.desired_state
        owner = $owner
        source = if ($null -ne $intent.PSObject.Properties['source']) { [string]$intent.source } else { 'persistent' }
    }
}

function Get-RecoveryState {
    if (-not (Test-Path -LiteralPath $RecoveryStateFile -PathType Leaf)) {
        return [pscustomobject]@{
            consecutive_attempts = 0
            total_recoveries = 0
            next_retry_at = $null
            last_attempt_at = $null
            last_success_at = $null
            last_health_code = $null
            last_action = $null
        }
    }

    try {
        $state = Get-Content -LiteralPath $RecoveryStateFile -Raw | ConvertFrom-Json
        foreach ($name in @('consecutive_attempts', 'total_recoveries')) {
            if ($null -eq $state.PSObject.Properties[$name]) { throw "$name missing" }
        }
        return [pscustomobject]@{
            consecutive_attempts = [int]$state.consecutive_attempts
            total_recoveries = [int]$state.total_recoveries
            next_retry_at = ConvertTo-UtcIsoString $state.next_retry_at
            last_attempt_at = ConvertTo-UtcIsoString $state.last_attempt_at
            last_success_at = ConvertTo-UtcIsoString $state.last_success_at
            last_health_code = if ($null -ne $state.PSObject.Properties['last_health_code']) { [string]$state.last_health_code } else { $null }
            last_action = if ($null -ne $state.PSObject.Properties['last_action']) { [string]$state.last_action } else { $null }
        }
    }
    catch {
        return [pscustomobject]@{
            consecutive_attempts = $MaxBurstAttempts
            total_recoveries = 0
            next_retry_at = (Get-Date).ToUniversalTime().AddSeconds($SlowRetrySeconds).ToString('o')
            last_attempt_at = $null
            last_success_at = $null
            last_health_code = 'RECOVERY_STATE_INVALID'
            last_action = 'wait_and_probe'
        }
    }
}

function Save-RecoveryState {
    param(
        [ValidateRange(0, 1000000)] [int]$ConsecutiveAttempts,
        [ValidateRange(0, 100000000)] [int]$TotalRecoveries,
        $NextRetryAt,
        $LastAttemptAt,
        $LastSuccessAt,
        [string]$LastHealthCode,
        [string]$LastAction
    )

    Write-AtomicJson -Path $RecoveryStateFile -Value ([ordered]@{
        schema_version = 1
        consecutive_attempts = $ConsecutiveAttempts
        total_recoveries = $TotalRecoveries
        next_retry_at = ConvertTo-UtcIsoString $NextRetryAt
        last_attempt_at = ConvertTo-UtcIsoString $LastAttemptAt
        last_success_at = ConvertTo-UtcIsoString $LastSuccessAt
        last_health_code = $LastHealthCode
        last_action = $LastAction
        updated_at = (Get-Date).ToUniversalTime().ToString('o')
    })
}

function Reset-ConsecutiveRecoveryState {
    $current = Get-RecoveryState
    Save-RecoveryState `
        -ConsecutiveAttempts 0 `
        -TotalRecoveries ([int]$current.total_recoveries) `
        -NextRetryAt $null `
        -LastAttemptAt $current.last_attempt_at `
        -LastSuccessAt $current.last_success_at `
        -LastHealthCode $null `
        -LastAction 'none'
}

function Test-RecoveryDue {
    param(
        [Parameter(Mandatory)] $RecoveryState,
        [Parameter(Mandatory)] [string]$CurrentAction
    )

    # A wait-only delay belongs to the remote/observation failure class that
    # produced it. A newly observed local restart requirement must not inherit
    # that delay. Backoff created by a failed restart_runtime attempt remains
    # authoritative and therefore still protects against restart storms.
    if (
        $CurrentAction -eq 'restart_runtime' -and
        [string]$RecoveryState.last_action -eq 'wait_and_probe'
    ) {
        return $true
    }

    if ([string]::IsNullOrWhiteSpace([string]$RecoveryState.next_retry_at)) {
        return $true
    }

    try {
        $next = [datetime]::Parse([string]$RecoveryState.next_retry_at).ToUniversalTime()
        return ((Get-Date).ToUniversalTime() -ge $next)
    }
    catch {
        return $true
    }
}

function Get-NextRecoveryDelaySeconds {
    param([ValidateRange(1, 1000000)] [int]$AttemptNumber)

    if ($AttemptNumber -le $MaxBurstAttempts) {
        return [int]$BurstBackoffSeconds[$AttemptNumber - 1]
    }

    # Long-lived recovery must never become permanently disabled. A small
    # process-local jitter prevents synchronized retry storms after outages.
    return ($SlowRetrySeconds + (Get-Random -Minimum 0 -Maximum 31))
}

function Get-ChatGptRouteState {
    if (-not (Test-Path -LiteralPath $ChatGptE2EFile -PathType Leaf)) {
        return [pscustomobject]@{ status = 'not_checked'; last_at = $null }
    }

    try {
        $receipt = Get-Content -LiteralPath $ChatGptE2EFile -Raw | ConvertFrom-Json
        if ([string]$receipt.status -notin @('pass', 'fail')) { throw 'invalid status' }
        $lastAt = [datetime]::Parse([string]$receipt.checked_at).ToUniversalTime()
        $age = ((Get-Date).ToUniversalTime() - $lastAt).TotalSeconds
        return [pscustomobject]@{
            status = if ($age -le $ChatGptReceiptFreshnessSeconds) { [string]$receipt.status } else { 'stale' }
            last_at = $lastAt.ToString('o')
        }
    }
    catch {
        return [pscustomobject]@{ status = 'stale'; last_at = $null }
    }
}

function Normalize-ManagerHealth {
    param([Parameter(Mandatory)] $Status)

    $binding = if ($null -ne $Status.PSObject.Properties['tunnel_binding']) {
        [string]$Status.tunnel_binding
    }
    else { 'unknown' }

    if ($null -ne $Status.PSObject.Properties['health_code']) {
        return [pscustomobject]@{
            binding = $binding
            code = [string]$Status.health_code
            recovery_action = if ($null -ne $Status.PSObject.Properties['recovery_action']) { [string]$Status.recovery_action } else { 'none' }
            runtime_ready = if ($null -ne $Status.PSObject.Properties['runtime_ready']) { [bool]$Status.runtime_ready } else { ([bool]$Status.mcp_ready -and [bool]$Status.tunnel_ready) }
            openai_ready = if ($null -ne $Status.PSObject.Properties['openai_ready']) { [bool]$Status.openai_ready } else { $false }
        }
    }

    $ready = (
        [int]$Status.active_count -eq 1 -and
        [bool]$Status.mcp_ready -and
        [bool]$Status.tunnel_ready
    )
    return [pscustomobject]@{
        binding = $binding
        code = if ($ready) { 'READY' } elseif ([bool]$Status.tunnel_running -or [int]$Status.active_count -gt 0) { 'LOCAL_RUNTIME_UNHEALTHY' } else { 'LOCAL_TUNNEL_NOT_RUNNING' }
        recovery_action = if ($ready) { 'none' } else { 'restart_runtime' }
        runtime_ready = $ready
        openai_ready = $false
    }
}

function Assert-OwnedDirectControllerPath {
    param([Parameter(Mandatory)] [string]$ControllerPath)

    $expected = [System.IO.Path]::GetFullPath($InstalledDirectControllerPath)
    $actual = [System.IO.Path]::GetFullPath($ControllerPath)
    if ($actual -ine $expected) {
        throw "Supervisor refuses non-installed direct controller ownership: $actual"
    }
    if (-not (Test-Path -LiteralPath $actual -PathType Leaf)) {
        throw "Owned direct controller is missing: $actual"
    }
    return $actual
}

function Invoke-OwnedDirectControllerAction {
    param(
        [Parameter(Mandatory)] [string]$ControllerPath,
        [ValidateSet('Start', 'Stop')] [string]$ControllerAction
    )

    $result = Invoke-BoundedPowerShell `
        -ScriptPath $ControllerPath `
        -Arguments @('-Action', $ControllerAction, '-NoNotify') `
        -TimeoutMilliseconds $ControllerMutationTimeoutMilliseconds `
        -CaptureOutput $false

    if ($result.timed_out) {
        throw "Direct controller $ControllerAction timed out."
    }
    if ($result.exit_code -ne 0) {
        throw "Direct controller $ControllerAction failed with exit code $($result.exit_code)."
    }
}

function Invoke-DirectRuntimeRecovery {
    param([Parameter(Mandatory)] $Owner)

    $controllerPath = Assert-OwnedDirectControllerPath -ControllerPath ([string]$Owner.controller_path)
    $mutex = New-Object System.Threading.Mutex($false, $ManagerOperationMutexName)
    $acquired = $false

    try {
        try {
            $acquired = $mutex.WaitOne($ManagerOperationMutexTimeoutMilliseconds)
        }
        catch [System.Threading.AbandonedMutexException] {
            $acquired = $true
        }

        if (-not $acquired) {
            throw 'Manager lifecycle mutex is busy.'
        }

        # Re-read persistent intent and runtime ownership only after serialization.
        # If the user requested Stop while we were waiting, fail closed instead of
        # resurrecting against the new desired state even if an owner receipt remains.
        $currentIntent = Get-PersistedDesiredState
        if ([string]$currentIntent.desired_state -ne 'running') {
            throw 'Desired state changed before recovery; explicit Stop wins.'
        }

        $currentOwner = Get-ManagerOwner
        if ($null -eq $currentOwner) {
            throw 'Manager owner disappeared before recovery; explicit Stop wins.'
        }
        $currentPath = Assert-OwnedDirectControllerPath -ControllerPath ([string]$currentOwner.controller_path)
        if ($currentPath -ine $controllerPath) {
            throw 'Manager owner changed before recovery.'
        }

        Invoke-OwnedDirectControllerAction -ControllerPath $controllerPath -ControllerAction Stop

        # manager-owner.json remains the runtime-ownership receipt while the
        # platform-owned direct runtime is replaced. desired-state.json remains
        # the independent user intent and is never rewritten by recovery.
        Invoke-OwnedDirectControllerAction -ControllerPath $controllerPath -ControllerAction Start
    }
    finally {
        if ($acquired) {
            try { $mutex.ReleaseMutex() } catch {}
        }
        $mutex.Dispose()
    }
}

function New-SupervisorSnapshot {
    param(
        [Parameter(Mandatory)] [string]$DesiredState,
        [Parameter(Mandatory)] [string]$SupervisorState,
        [Parameter(Mandatory)] [string]$HealthCode,
        [Parameter(Mandatory)] [string]$RecoveryAction,
        $ManagerStatus,
        $RecoveryState,
        [string]$ErrorCode
    )

    $route = Get-ChatGptRouteState
    $profile = $null
    $binding = $null
    $runtimeReady = $false
    $openAiReady = $false
    $mcpReady = $false
    $tunnelReady = $false
    $remoteStatus = $null
    $pollFresh = $false

    if ($null -ne $ManagerStatus) {
        if ($null -ne $ManagerStatus.PSObject.Properties['settings']) { $profile = [string]$ManagerStatus.settings.profile }
        if ($null -ne $ManagerStatus.PSObject.Properties['tunnel_binding']) { $binding = [string]$ManagerStatus.tunnel_binding }
        if ($null -ne $ManagerStatus.PSObject.Properties['runtime_ready']) { $runtimeReady = [bool]$ManagerStatus.runtime_ready }
        else { $runtimeReady = ([bool]$ManagerStatus.mcp_ready -and [bool]$ManagerStatus.tunnel_ready) }
        $mcpReady = [bool]$ManagerStatus.mcp_ready
        $tunnelReady = [bool]$ManagerStatus.tunnel_ready
        if ($null -ne $ManagerStatus.PSObject.Properties['openai_ready']) { $openAiReady = [bool]$ManagerStatus.openai_ready }
        if ($null -ne $ManagerStatus.PSObject.Properties['remote_tunnel_status']) { $remoteStatus = [string]$ManagerStatus.remote_tunnel_status }
        if ($null -ne $ManagerStatus.PSObject.Properties['control_plane_poll_fresh']) { $pollFresh = [bool]$ManagerStatus.control_plane_poll_fresh }
    }

    return [ordered]@{
        schema_version = 1
        supervisor_pid = $PID
        desired_state = $DesiredState
        supervisor_state = $SupervisorState
        health_code = $HealthCode
        recovery_action = $RecoveryAction
        error_code = $ErrorCode
        profile = $profile
        tunnel_binding = $binding
        runtime_ready = $runtimeReady
        mcp_ready = $mcpReady
        tunnel_local_ready = $tunnelReady
        openai_control_ready = $openAiReady
        remote_tunnel_status = $remoteStatus
        control_plane_poll_fresh = $pollFresh
        chatgpt_route_status = [string]$route.status
        last_chatgpt_e2e_at = $route.last_at
        recovery = if ($null -ne $RecoveryState) {
            [ordered]@{
                consecutive_attempts = [int]$RecoveryState.consecutive_attempts
                total_recoveries = [int]$RecoveryState.total_recoveries
                next_retry_at = ConvertTo-UtcIsoString $RecoveryState.next_retry_at
                last_attempt_at = ConvertTo-UtcIsoString $RecoveryState.last_attempt_at
                last_success_at = ConvertTo-UtcIsoString $RecoveryState.last_success_at
            }
        }
        else { $null }
        observed_at = (Get-Date).ToUniversalTime().ToString('o')
    }
}

function Save-SupervisorSnapshot {
    param([Parameter(Mandatory)] $Snapshot)
    Write-AtomicJson -Path $SupervisorStateFile -Value $Snapshot
}

function Invoke-ReconcileOnce {
    Initialize-SupervisorDirectories

    $desired = $null
    try {
        $desired = Get-DesiredState
    }
    catch {
        $recovery = Get-RecoveryState
        $snapshot = New-SupervisorSnapshot `
            -DesiredState 'unknown' `
            -SupervisorState 'blocked' `
            -HealthCode 'MANAGER_OWNER_INVALID' `
            -RecoveryAction 'blocked' `
            -ManagerStatus $null `
            -RecoveryState $recovery `
            -ErrorCode 'MANAGER_OWNER_INVALID'
        Save-SupervisorSnapshot -Snapshot $snapshot
        Write-SupervisorLog 'persistent desired/owner state is invalid; fail closed' 'ERROR'
        return $snapshot
    }

    $status = $null
    try {
        $status = Get-ManagerStatus
    }
    catch {
        $recovery = Get-RecoveryState
        $snapshot = New-SupervisorSnapshot `
            -DesiredState ([string]$desired.desired_state) `
            -SupervisorState 'degraded' `
            -HealthCode 'MANAGER_STATUS_FAILED' `
            -RecoveryAction 'wait_and_probe' `
            -ManagerStatus $null `
            -RecoveryState $recovery `
            -ErrorCode 'MANAGER_STATUS_FAILED'
        Save-SupervisorSnapshot -Snapshot $snapshot
        Write-SupervisorLog 'manager status failed; no destructive recovery attempted' 'WARN'
        return $snapshot
    }

    if ([string]$desired.desired_state -eq 'stopped') {
        $unexpectedActive = ([int]$status.active_count -gt 0 -or [bool]$status.tunnel_running)
        $recovery = Get-RecoveryState
        if ($unexpectedActive) {
            $snapshot = New-SupervisorSnapshot `
                -DesiredState 'stopped' `
                -SupervisorState 'blocked' `
                -HealthCode 'UNOWNED_RUNTIME_ACTIVE' `
                -RecoveryAction 'blocked' `
                -ManagerStatus $status `
                -RecoveryState $recovery `
                -ErrorCode 'UNOWNED_RUNTIME_ACTIVE'
            Save-SupervisorSnapshot -Snapshot $snapshot
            Write-SupervisorLog 'runtime active against desired stopped state; fail closed' 'ERROR'
            return $snapshot
        }

        Reset-ConsecutiveRecoveryState
        $recovery = Get-RecoveryState
        $snapshot = New-SupervisorSnapshot `
            -DesiredState 'stopped' `
            -SupervisorState 'stopped' `
            -HealthCode 'STOPPED' `
            -RecoveryAction 'none' `
            -ManagerStatus $status `
            -RecoveryState $recovery
        Save-SupervisorSnapshot -Snapshot $snapshot
        return $snapshot
    }

    $health = Normalize-ManagerHealth -Status $status
    $recovery = Get-RecoveryState

    if ([bool]$health.runtime_ready -and [string]$health.recovery_action -eq 'none') {
        Reset-ConsecutiveRecoveryState
        $recovery = Get-RecoveryState
        $snapshot = New-SupervisorSnapshot `
            -DesiredState 'running' `
            -SupervisorState 'healthy' `
            -HealthCode ([string]$health.code) `
            -RecoveryAction 'none' `
            -ManagerStatus $status `
            -RecoveryState $recovery
        Save-SupervisorSnapshot -Snapshot $snapshot
        return $snapshot
    }

    if ([string]$health.recovery_action -eq 'blocked') {
        $snapshot = New-SupervisorSnapshot `
            -DesiredState 'running' `
            -SupervisorState 'blocked' `
            -HealthCode ([string]$health.code) `
            -RecoveryAction 'blocked' `
            -ManagerStatus $status `
            -RecoveryState $recovery `
            -ErrorCode ([string]$health.code)
        Save-SupervisorSnapshot -Snapshot $snapshot
        Write-SupervisorLog "blocked health=$($health.code); local restart suppressed" 'ERROR'
        return $snapshot
    }

    if ([string]$health.recovery_action -eq 'wait_and_probe') {
        $nextRetry = (Get-Date).ToUniversalTime().AddSeconds($WaitProbeSeconds).ToString('o')
        Save-RecoveryState `
            -ConsecutiveAttempts ([int]$recovery.consecutive_attempts) `
            -TotalRecoveries ([int]$recovery.total_recoveries) `
            -NextRetryAt $nextRetry `
            -LastAttemptAt $recovery.last_attempt_at `
            -LastSuccessAt $recovery.last_success_at `
            -LastHealthCode ([string]$health.code) `
            -LastAction 'wait_and_probe'
        $recovery = Get-RecoveryState
        $snapshot = New-SupervisorSnapshot `
            -DesiredState 'running' `
            -SupervisorState 'degraded' `
            -HealthCode ([string]$health.code) `
            -RecoveryAction 'wait_and_probe' `
            -ManagerStatus $status `
            -RecoveryState $recovery
        Save-SupervisorSnapshot -Snapshot $snapshot
        return $snapshot
    }

    if ([string]$health.binding -ne 'direct-stdio') {
        $snapshot = New-SupervisorSnapshot `
            -DesiredState 'running' `
            -SupervisorState 'degraded' `
            -HealthCode 'SUPERVISOR_RECOVERY_UNSUPPORTED_BINDING' `
            -RecoveryAction 'wait_and_probe' `
            -ManagerStatus $status `
            -RecoveryState $recovery `
            -ErrorCode 'SUPERVISOR_RECOVERY_UNSUPPORTED_BINDING'
        Save-SupervisorSnapshot -Snapshot $snapshot
        return $snapshot
    }

    if ($NoRecovery) {
        $snapshot = New-SupervisorSnapshot `
            -DesiredState 'running' `
            -SupervisorState 'degraded' `
            -HealthCode ([string]$health.code) `
            -RecoveryAction 'restart_runtime' `
            -ManagerStatus $status `
            -RecoveryState $recovery
        Save-SupervisorSnapshot -Snapshot $snapshot
        return $snapshot
    }

    if (-not (Test-RecoveryDue -RecoveryState $recovery -CurrentAction ([string]$health.recovery_action))) {
        $snapshot = New-SupervisorSnapshot `
            -DesiredState 'running' `
            -SupervisorState 'backoff' `
            -HealthCode ([string]$health.code) `
            -RecoveryAction 'restart_runtime' `
            -ManagerStatus $status `
            -RecoveryState $recovery
        Save-SupervisorSnapshot -Snapshot $snapshot
        return $snapshot
    }

    $attemptNumber = [int]$recovery.consecutive_attempts + 1
    $attemptAt = (Get-Date).ToUniversalTime().ToString('o')
    Write-SupervisorLog "recovery attempt=$attemptNumber health=$($health.code)"

    $post = $null
    $postHealth = $null
    try {
        Invoke-DirectRuntimeRecovery -Owner $desired.owner
        $post = Get-ManagerStatus
        $postHealth = Normalize-ManagerHealth -Status $post
        if (-not [bool]$postHealth.runtime_ready) {
            throw "runtime remained unready: $($postHealth.code)"
        }
    }
    catch {
        $failureType = $_.Exception.GetType().Name
        $delay = Get-NextRecoveryDelaySeconds -AttemptNumber $attemptNumber
        $nextRetry = (Get-Date).ToUniversalTime().AddSeconds($delay).ToString('o')
        Save-RecoveryState `
            -ConsecutiveAttempts $attemptNumber `
            -TotalRecoveries ([int]$recovery.total_recoveries) `
            -NextRetryAt $nextRetry `
            -LastAttemptAt $attemptAt `
            -LastSuccessAt $recovery.last_success_at `
            -LastHealthCode ([string]$health.code) `
            -LastAction 'restart_runtime'
        $recovery = Get-RecoveryState
        $snapshot = New-SupervisorSnapshot `
            -DesiredState 'running' `
            -SupervisorState 'backoff' `
            -HealthCode ([string]$health.code) `
            -RecoveryAction 'restart_runtime' `
            -ManagerStatus $status `
            -RecoveryState $recovery `
            -ErrorCode 'RECOVERY_ATTEMPT_FAILED'
        Save-SupervisorSnapshot -Snapshot $snapshot
        Write-SupervisorLog "recovery failed attempt=$attemptNumber phase=runtime error_type=$failureType next_retry=$nextRetry" 'WARN'
        return $snapshot
    }

    # Runtime recovery is now complete. Publication errors must not be turned
    # into another destructive restart of an already-ready runtime.
    $total = [int]$recovery.total_recoveries + 1
    $successAt = (Get-Date).ToUniversalTime().ToString('o')
    try {
        Save-RecoveryState `
            -ConsecutiveAttempts 0 `
            -TotalRecoveries $total `
            -NextRetryAt $null `
            -LastAttemptAt $attemptAt `
            -LastSuccessAt $successAt `
            -LastHealthCode ([string]$postHealth.code) `
            -LastAction 'restart_runtime'
        $recovery = Get-RecoveryState
        $postSupervisorState = if ([string]$postHealth.recovery_action -eq 'none') { 'healthy' } else { 'degraded' }
        $snapshot = New-SupervisorSnapshot `
            -DesiredState 'running' `
            -SupervisorState $postSupervisorState `
            -HealthCode ([string]$postHealth.code) `
            -RecoveryAction ([string]$postHealth.recovery_action) `
            -ManagerStatus $post `
            -RecoveryState $recovery
        Save-SupervisorSnapshot -Snapshot $snapshot
        Write-SupervisorLog "recovery succeeded attempt=$attemptNumber health=$($postHealth.code)"
        return $snapshot
    }
    catch {
        $publicationType = $_.Exception.GetType().Name
        Write-SupervisorLog "recovery publication failed attempt=$attemptNumber error_type=$publicationType" 'WARN'
        throw
    }
}

function Get-SupervisorStatus {
    Initialize-SupervisorDirectories
    if (-not (Test-Path -LiteralPath $SupervisorStateFile -PathType Leaf)) {
        return [pscustomobject]@{
            schema_version = 1
            desired_state = 'unknown'
            supervisor_state = 'not_started'
            health_code = 'SUPERVISOR_NOT_STARTED'
            recovery_action = 'none'
            observed_at = $null
        }
    }

    try {
        return Get-Content -LiteralPath $SupervisorStateFile -Raw | ConvertFrom-Json
    }
    catch {
        return [pscustomobject]@{
            schema_version = 1
            desired_state = 'unknown'
            supervisor_state = 'blocked'
            health_code = 'SUPERVISOR_STATE_INVALID'
            recovery_action = 'blocked'
            observed_at = $null
        }
    }
}

function Run-SupervisorLoop {
    Initialize-SupervisorDirectories
    $mutex = New-Object System.Threading.Mutex($false, $SupervisorMutexName)
    $acquired = $false

    try {
        try {
            $acquired = $mutex.WaitOne(0)
        }
        catch [System.Threading.AbandonedMutexException] {
            $acquired = $true
        }

        if (-not $acquired) {
            Write-Host 'TRANSPORT_SUPERVISOR=already-running'
            return
        }

        Write-SupervisorLog "supervisor started pid=$PID interval=$LoopIntervalSeconds"
        while ($true) {
            try {
                $null = Invoke-ReconcileOnce
            }
            catch {
                $recovery = Get-RecoveryState
                $snapshot = New-SupervisorSnapshot `
                    -DesiredState 'unknown' `
                    -SupervisorState 'degraded' `
                    -HealthCode 'SUPERVISOR_OBSERVATION_FAILED' `
                    -RecoveryAction 'wait_and_probe' `
                    -ManagerStatus $null `
                    -RecoveryState $recovery `
                    -ErrorCode 'SUPERVISOR_OBSERVATION_FAILED'
                Save-SupervisorSnapshot -Snapshot $snapshot
                Write-SupervisorLog "reconcile exception=$($_.Exception.GetType().Name)" 'WARN'
            }
            Start-Sleep -Seconds $LoopIntervalSeconds
        }
    }
    finally {
        if ($acquired) {
            try { $mutex.ReleaseMutex() } catch {}
        }
        $mutex.Dispose()
    }
}

Initialize-SupervisorDirectories

switch ($Action) {
    'Status' {
        Get-SupervisorStatus | ConvertTo-Json -Depth 8
    }
    'Reconcile' {
        Invoke-ReconcileOnce | ConvertTo-Json -Depth 8
    }
    'Run' {
        Run-SupervisorLoop
    }
}
