[CmdletBinding()]
param(
    [ValidateRange(15, 300)]
    [int]$DisconnectDetectTimeoutSeconds = 120,

    [ValidateRange(15, 300)]
    [int]$OfflineObservationSeconds = 45,

    [ValidateRange(30, 600)]
    [int]$ReconnectTimeoutSeconds = 180,

    [string]$OutputRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $IsWindows) {
    throw 'Transport Supervisor network qualification supports Windows only.'
}
if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    throw 'LOCALAPPDATA is unavailable.'
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Installer = Join-Path $PSScriptRoot 'install-chat-platform-supervisor.ps1'
$LocalRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
$Manager = Join-Path $LocalRoot 'app\scripts\chat-platform.ps1'
$Supervisor = Join-Path $LocalRoot 'app\scripts\chat-platform-supervisor.ps1'
$OwnerFile = Join-Path $LocalRoot 'state\manager-owner.json'
$HealthUrlFile = Join-Path $LocalRoot 'state\semantic-direct-health.url'
$SupervisorStateFile = Join-Path $LocalRoot 'state\supervisor.json'
$RecoveryStateFile = Join-Path $LocalRoot 'state\supervisor-recovery.json'
$SupervisorLogFile = Join-Path $LocalRoot 'logs\supervisor.log'
$TunnelExe = Join-Path $LocalRoot 'bin\tunnel-client.exe'
$TaskName = 'Chat Agent Platform Transport Supervisor'

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $LocalRoot 'transport-supervisor-network-qualification'
}
$RunDir = Join-Path $OutputRoot ('run-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Write-Result {
    param([Parameter(Mandatory)] [string]$Name, [Parameter(Mandatory)] $Value)
    Write-Host "$Name=$Value"
}

function Save-JsonEvidence {
    param([Parameter(Mandatory)] [string]$Name, [Parameter(Mandatory)] $Value)
    $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $RunDir "$Name.json") -Encoding utf8
}

function Invoke-BoundedManagerProcess {
    param(
        [ValidateSet('Start', 'Stop', 'Status')]
        [string]$Action,
        [ValidateRange(5, 300)]
        [int]$TimeoutSeconds
    )

    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    $captureOutput = ($Action -eq 'Status')
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pwsh
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $captureOutput
    $startInfo.RedirectStandardError = $captureOutput

    foreach ($argument in @(
        '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', $Manager, '-Action', $Action, '-NoNotify'
    )) {
        $startInfo.ArgumentList.Add([string]$argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) {
            throw "Manager $Action could not be started."
        }

        $stdoutTask = if ($captureOutput) { $process.StandardOutput.ReadToEndAsync() } else { $null }
        $stderrTask = if ($captureOutput) { $process.StandardError.ReadToEndAsync() } else { $null }
        $timeoutMilliseconds = [int]($TimeoutSeconds * 1000)

        if (-not $process.WaitForExit($timeoutMilliseconds)) {
            try { $process.Kill($true) } catch {}
            try { $process.WaitForExit(5000) | Out-Null } catch {}
            throw "Manager $Action timed out after $TimeoutSeconds seconds."
        }

        $process.WaitForExit()
        return [pscustomobject]@{
            exit_code = $process.ExitCode
            stdout = if ($captureOutput) { $stdoutTask.GetAwaiter().GetResult() } else { '' }
            stderr = if ($captureOutput) { $stderrTask.GetAwaiter().GetResult() } else { '' }
        }
    }
    finally {
        $process.Dispose()
    }
}

function Invoke-ManagerStatus {
    $result = Invoke-BoundedManagerProcess -Action Status -TimeoutSeconds 30
    if ([int]$result.exit_code -ne 0) {
        $diagnostic = (([string]$result.stderr + "`n" + [string]$result.stdout).Trim())
        throw "Manager status failed: $diagnostic"
    }
    try {
        return ([string]$result.stdout | ConvertFrom-Json -ErrorAction Stop)
    }
    catch {
        throw "Manager status returned invalid JSON: $([string]$result.stdout)"
    }
}

function Invoke-ManagerMutation {
    param([ValidateSet('Start', 'Stop')] [string]$Action)
    $timeoutSeconds = if ($Action -eq 'Start') { 150 } else { 60 }
    $result = Invoke-BoundedManagerProcess -Action $Action -TimeoutSeconds $timeoutSeconds
    if ([int]$result.exit_code -ne 0) {
        throw "Manager $Action failed with exit code $($result.exit_code)."
    }
}

function Get-DirectTunnelProcesses {
    if (-not (Test-Path -LiteralPath $TunnelExe -PathType Leaf)) { return @() }
    $expectedExe = [System.IO.Path]::GetFullPath($TunnelExe)
    $healthPattern = [regex]::Escape($HealthUrlFile)
    return @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                if ($_.Name -ne 'tunnel-client.exe') { return $false }
                $actualExe = [string]$_.ExecutablePath
                $commandLine = [string]$_.CommandLine
                if ([string]::IsNullOrWhiteSpace($actualExe) -or [string]::IsNullOrWhiteSpace($commandLine)) { return $false }
                try { $actualExe = [System.IO.Path]::GetFullPath($actualExe) } catch { return $false }
                return (
                    $actualExe -ieq $expectedExe -and
                    $commandLine -match '(?i)--mcp\.command' -and
                    $commandLine -match $healthPattern
                )
            }
    )
}

function Get-ExactSupervisorProcesses {
    if (-not (Test-Path -LiteralPath $Supervisor -PathType Leaf)) { return @() }
    $scriptPattern = [regex]::Escape([System.IO.Path]::GetFullPath($Supervisor))
    return @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Name -eq 'pwsh.exe' -and
                -not [string]::IsNullOrWhiteSpace([string]$_.CommandLine) -and
                [string]$_.CommandLine -match $scriptPattern -and
                [string]$_.CommandLine -match '(?i)(?:^|\s)-Action\s+Run(?:\s|$)'
            }
    )
}

function Wait-ForExactSupervisor {
    param(
        [ValidateSet('Running', 'Stopped')]
        [string]$State,
        [ValidateRange(1, 60)]
        [int]$TimeoutSeconds = 15
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $count = @(Get-ExactSupervisorProcesses).Count
        if ($State -eq 'Running' -and $count -eq 1) { return $true }
        if ($State -eq 'Stopped' -and $count -eq 0) { return $true }
        Start-Sleep -Milliseconds 250
    }
    return $false
}

function Start-QualificationSupervisor {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    if ([string]$task.TaskName -ne $TaskName) {
        throw 'Qualification supervisor Scheduled Task is unavailable.'
    }
    Start-ScheduledTask -TaskName $TaskName
    if (-not (Wait-ForExactSupervisor -State Running -TimeoutSeconds 15)) {
        throw 'Qualification supervisor did not start as exactly one process.'
    }
}

function Stop-QualificationSupervisor {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -ne $task) {
        try { Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue } catch {}
    }
    if (-not (Wait-ForExactSupervisor -State Stopped -TimeoutSeconds 15)) {
        throw 'Qualification supervisor did not stop before desired-state restoration.'
    }
}

function Read-SupervisorState {
    if (-not (Test-Path -LiteralPath $SupervisorStateFile -PathType Leaf)) { return $null }
    try { return (Get-Content -LiteralPath $SupervisorStateFile -Raw | ConvertFrom-Json) } catch { return $null }
}

function Read-RecoveryState {
    if (-not (Test-Path -LiteralPath $RecoveryStateFile -PathType Leaf)) { return $null }
    try { return (Get-Content -LiteralPath $RecoveryStateFile -Raw | ConvertFrom-Json) } catch { return $null }
}

if (-not (Test-Path -LiteralPath $Manager -PathType Leaf)) {
    throw "Installed manager is missing: $Manager"
}

$desiredStateBefore = if (Test-Path -LiteralPath $OwnerFile -PathType Leaf) { 'running' } else { 'stopped' }
$installAttempted = $false
$qualificationPassed = $false
$supervisorStarted = $false

try {
    Write-Host '===== TRANSPORT SUPERVISOR: NETWORK DISCONNECT / RECONNECT QUALIFICATION =====' -ForegroundColor Cyan
    Write-Host 'This harness NEVER disables adapters, changes firewall rules, or changes VPN state.' -ForegroundColor Yellow
    Write-Host 'You will perform the physical network disconnect/reconnect when prompted.' -ForegroundColor Yellow

    $installAttempted = $true
    & $Installer -NoStart

    if (@(Get-ExactSupervisorProcesses).Count -ne 0) {
        throw 'Qualification installer -NoStart unexpectedly left a supervisor process running.'
    }

    foreach ($entry in @(
        @($SupervisorStateFile, 'preexisting-supervisor.json'),
        @($RecoveryStateFile, 'preexisting-recovery.json')
    )) {
        if (Test-Path -LiteralPath $entry[0] -PathType Leaf) {
            Copy-Item -LiteralPath $entry[0] -Destination (Join-Path $RunDir $entry[1]) -Force
            Remove-Item -LiteralPath $entry[0] -Force
        }
    }

    $baseline = Invoke-ManagerStatus
    Save-JsonEvidence -Name 'manager-before-start' -Value $baseline
    if ([string]$baseline.settings.profile -notin @('semantic', 'semantic-direct')) {
        throw "Network qualification requires semantic/direct profile. Current profile=$($baseline.settings.profile)"
    }

    if (-not [bool]$baseline.runtime_ready) {
        Invoke-ManagerMutation -Action Stop
        Invoke-ManagerMutation -Action Start
    }

    $readyDeadline = (Get-Date).AddSeconds(90)
    $healthy = $null
    while ((Get-Date) -lt $readyDeadline) {
        $candidate = Invoke-ManagerStatus
        if (
            [bool]$candidate.runtime_ready -and
            [bool]$candidate.openai_ready -and
            [int]$candidate.tunnel_process_count -eq 1
        ) {
            $healthy = $candidate
            break
        }
        Start-Sleep -Seconds 1
    }
    if ($null -eq $healthy) {
        throw 'Baseline did not become fully ready before network qualification.'
    }
    Save-JsonEvidence -Name 'healthy-baseline' -Value $healthy

    Start-QualificationSupervisor
    $supervisorStarted = $true

    $supervisors = @(Get-ExactSupervisorProcesses)
    $tunnels = @(Get-DirectTunnelProcesses)
    if ($supervisors.Count -ne 1 -or $tunnels.Count -ne 1) {
        throw "Expected one supervisor and one direct tunnel at baseline; found supervisor=$($supervisors.Count), tunnel=$($tunnels.Count)."
    }
    $supervisorPid = [int]$supervisors[0].ProcessId
    $tunnelPid = [int]$tunnels[0].ProcessId

    $baselineReceiptDeadline = (Get-Date).AddSeconds(30)
    $baselineSupervisorReceipt = $null
    $baselineRecoveryReceipt = $null
    while ((Get-Date) -lt $baselineReceiptDeadline) {
        $s = Read-SupervisorState
        $r = Read-RecoveryState
        if (
            $null -ne $s -and $null -ne $r -and
            [int]$s.supervisor_pid -eq $supervisorPid -and
            [bool]$s.runtime_ready -and
            [int]$r.consecutive_attempts -eq 0
        ) {
            $baselineSupervisorReceipt = $s
            $baselineRecoveryReceipt = $r
            break
        }
        Start-Sleep -Milliseconds 500
    }
    if ($null -eq $baselineSupervisorReceipt -or $null -eq $baselineRecoveryReceipt) {
        throw 'Supervisor did not publish a clean baseline receipt.'
    }

    Save-JsonEvidence -Name 'supervisor-before-disconnect' -Value $baselineSupervisorReceipt
    Save-JsonEvidence -Name 'recovery-before-disconnect' -Value $baselineRecoveryReceipt
    $recoveriesBefore = [int]$baselineRecoveryReceipt.total_recoveries

    Write-Host ''
    Write-Host 'ACTION REQUIRED: physically disconnect external network now.' -ForegroundColor Cyan
    Write-Host 'For example, disconnect Wi-Fi/Ethernet or the upstream connection. Do NOT stop Chat Agent Platform processes.' -ForegroundColor Yellow
    Read-Host 'After the computer is actually offline, press Enter here' | Out-Null
    $disconnectConfirmedAt = (Get-Date).ToUniversalTime().ToString('o')

    $offlineDetected = $null
    $offlineDeadline = (Get-Date).AddSeconds($DisconnectDetectTimeoutSeconds)
    while ((Get-Date) -lt $offlineDeadline) {
        try {
            $status = Invoke-ManagerStatus
            if (
                [bool]$status.runtime_ready -and
                (-not [bool]$status.openai_ready)
            ) {
                $offlineDetected = $status
                break
            }
        }
        catch {}
        Start-Sleep -Seconds 1
    }
    if ($null -eq $offlineDetected) {
        throw "Remote/control-plane loss was not observed within $DisconnectDetectTimeoutSeconds seconds while local runtime stayed ready."
    }
    Save-JsonEvidence -Name 'offline-detected' -Value $offlineDetected

    $offlineSamples = @()
    $offlineEnd = (Get-Date).AddSeconds($OfflineObservationSeconds)
    while ((Get-Date) -lt $offlineEnd) {
        $currentSupervisors = @(Get-ExactSupervisorProcesses)
        $currentTunnels = @(Get-DirectTunnelProcesses)
        $s = Read-SupervisorState
        $r = Read-RecoveryState
        $offlineSamples += [pscustomobject]@{
            observed_at = (Get-Date).ToUniversalTime().ToString('o')
            supervisor_process_count = $currentSupervisors.Count
            supervisor_pid = if ($currentSupervisors.Count -eq 1) { [int]$currentSupervisors[0].ProcessId } else { $null }
            tunnel_process_count = $currentTunnels.Count
            tunnel_pid = if ($currentTunnels.Count -eq 1) { [int]$currentTunnels[0].ProcessId } else { $null }
            supervisor_state = if ($null -ne $s) { [string]$s.supervisor_state } else { $null }
            health_code = if ($null -ne $s) { [string]$s.health_code } else { $null }
            recovery_action = if ($null -ne $s) { [string]$s.recovery_action } else { $null }
            runtime_ready = if ($null -ne $s) { [bool]$s.runtime_ready } else { $false }
            consecutive_attempts = if ($null -ne $r) { [int]$r.consecutive_attempts } else { $null }
            total_recoveries = if ($null -ne $r) { [int]$r.total_recoveries } else { $null }
        }

        if (
            $currentSupervisors.Count -ne 1 -or
            [int]$currentSupervisors[0].ProcessId -ne $supervisorPid
        ) {
            throw 'Supervisor process changed or disappeared during offline observation.'
        }
        if (
            $currentTunnels.Count -ne 1 -or
            [int]$currentTunnels[0].ProcessId -ne $tunnelPid
        ) {
            throw 'Direct tunnel process churned during transient network loss.'
        }
        if ($null -ne $r -and [int]$r.total_recoveries -ne $recoveriesBefore) {
            throw 'Supervisor performed runtime recovery during transient network loss.'
        }
        Start-Sleep -Seconds 2
    }
    $offlineSamples | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $RunDir 'offline-samples.json') -Encoding utf8

    Write-Host ''
    Write-Host 'OFFLINE OBSERVATION PASSED: no supervisor/tunnel PID churn and no recovery-count increase.' -ForegroundColor Green
    Write-Host 'ACTION REQUIRED: restore the external network now.' -ForegroundColor Cyan
    Write-Host 'If OpenAI access on this machine depends on a VPN or proxy, restore that same path too before pressing Enter.' -ForegroundColor Yellow
    Read-Host 'After connectivity is restored, press Enter here' | Out-Null
    $reconnectConfirmedAt = (Get-Date).ToUniversalTime().ToString('o')

    $reconnected = $null
    $reconnectSamples = @()
    $reconnectDeadline = (Get-Date).AddSeconds($ReconnectTimeoutSeconds)
    while ((Get-Date) -lt $reconnectDeadline) {
        try {
            $status = Invoke-ManagerStatus
            $currentSupervisors = @(Get-ExactSupervisorProcesses)
            $currentTunnels = @(Get-DirectTunnelProcesses)
            $s = Read-SupervisorState
            $r = Read-RecoveryState

            $sample = [pscustomobject]@{
                observed_at = (Get-Date).ToUniversalTime().ToString('o')
                runtime_ready = [bool]$status.runtime_ready
                openai_ready = [bool]$status.openai_ready
                health_code = if ($null -ne $status.PSObject.Properties['health_code']) { [string]$status.health_code } else { $null }
                recovery_action = if ($null -ne $status.PSObject.Properties['recovery_action']) { [string]$status.recovery_action } else { $null }
                remote_tunnel_status = if ($null -ne $status.PSObject.Properties['remote_tunnel_status']) { [string]$status.remote_tunnel_status } else { $null }
                control_plane_poll_fresh = if ($null -ne $status.PSObject.Properties['control_plane_poll_fresh']) { [bool]$status.control_plane_poll_fresh } else { $false }
                supervisor_process_count = $currentSupervisors.Count
                supervisor_pid = if ($currentSupervisors.Count -eq 1) { [int]$currentSupervisors[0].ProcessId } else { $null }
                tunnel_process_count = $currentTunnels.Count
                tunnel_pid = if ($currentTunnels.Count -eq 1) { [int]$currentTunnels[0].ProcessId } else { $null }
                supervisor_state = if ($null -ne $s) { [string]$s.supervisor_state } else { $null }
                recovery_total = if ($null -ne $r) { [int]$r.total_recoveries } else { $null }
                consecutive_attempts = if ($null -ne $r) { [int]$r.consecutive_attempts } else { $null }
            }
            $reconnectSamples += $sample

            if (
                [bool]$status.runtime_ready -and
                [bool]$status.openai_ready -and
                $currentSupervisors.Count -eq 1 -and
                [int]$currentSupervisors[0].ProcessId -eq $supervisorPid -and
                $currentTunnels.Count -eq 1
            ) {
                $reconnected = $status
                break
            }
        }
        catch {}
        Start-Sleep -Seconds 1
    }
    $reconnectSamples | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $RunDir 'reconnect-samples.json') -Encoding utf8
    if ($null -eq $reconnected) {
        $lastSample = if ($reconnectSamples.Count -gt 0) { $reconnectSamples[-1] } else { $null }
        if ($null -ne $lastSample) {
            throw "Healthy state did not return automatically within $ReconnectTimeoutSeconds seconds after reconnect. Last sample: runtime_ready=$($lastSample.runtime_ready), openai_ready=$($lastSample.openai_ready), health_code=$($lastSample.health_code), recovery_action=$($lastSample.recovery_action), remote_tunnel_status=$($lastSample.remote_tunnel_status), control_plane_poll_fresh=$($lastSample.control_plane_poll_fresh), supervisor_pid=$($lastSample.supervisor_pid), tunnel_pid=$($lastSample.tunnel_pid), recovery_total=$($lastSample.recovery_total)."
        }
        throw "Healthy state did not return automatically within $ReconnectTimeoutSeconds seconds after reconnect and no reconnect sample was captured."
    }
    Save-JsonEvidence -Name 'manager-after-reconnect' -Value $reconnected

    $postRecovery = Read-RecoveryState
    $postSupervisor = Read-SupervisorState
    $postTunnels = @(Get-DirectTunnelProcesses)
    if ($null -eq $postRecovery -or $null -eq $postSupervisor) {
        throw 'Supervisor receipts are missing after reconnect.'
    }
    if ($postTunnels.Count -ne 1) {
        throw "Expected exactly one direct tunnel after reconnect; found $($postTunnels.Count)."
    }
    if ([int]$postSupervisor.supervisor_pid -ne $supervisorPid) {
        throw 'Supervisor PID changed across network reconnect.'
    }

    $recoveriesAfter = [int]$postRecovery.total_recoveries
    $recoveryDelta = $recoveriesAfter - $recoveriesBefore
    if ($recoveryDelta -lt 0 -or $recoveryDelta -gt 1) {
        throw "Reconnect caused an unexpected recovery count delta: $recoveryDelta. Expected 0 or 1."
    }

    $postTunnelPid = [int]$postTunnels[0].ProcessId
    $reconnectMode = if ($recoveryDelta -eq 0) { 'seamless' } else { 'bounded_recovery' }

    if ($reconnectMode -eq 'seamless') {
        if ($postTunnelPid -ne $tunnelPid) {
            throw 'Tunnel PID changed without a committed supervisor recovery receipt.'
        }
    }
    else {
        if ($postTunnelPid -eq $tunnelPid) {
            throw 'Recovery count increased but tunnel PID did not change.'
        }
        if ([string]$postSupervisor.supervisor_state -ne 'healthy') {
            throw 'Bounded reconnect recovery did not end in healthy supervisor state.'
        }
        if ([string]$postSupervisor.health_code -ne 'READY') {
            throw 'Bounded reconnect recovery did not end in READY health.'
        }
        if ([string]$postSupervisor.recovery_action -ne 'none') {
            throw 'Bounded reconnect recovery left a pending recovery action.'
        }
        if ([int]$postRecovery.consecutive_attempts -ne 0) {
            throw 'Bounded reconnect recovery left non-zero consecutive attempts.'
        }
        if ([string]::IsNullOrWhiteSpace([string]$postRecovery.last_success_at)) {
            throw 'Bounded reconnect recovery did not publish last_success_at.'
        }
    }

    $heartbeatAt = [string]$postSupervisor.observed_at
    $heartbeatAdvanced = $false
    $heartbeatDeadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $heartbeatDeadline) {
        Start-Sleep -Seconds 1
        $heartbeat = Read-SupervisorState
        $currentSupervisors = @(Get-ExactSupervisorProcesses)
        if (
            $null -ne $heartbeat -and
            $currentSupervisors.Count -eq 1 -and
            [int]$currentSupervisors[0].ProcessId -eq $supervisorPid -and
            [int]$heartbeat.supervisor_pid -eq $supervisorPid -and
            [string]$heartbeat.observed_at -ne $heartbeatAt
        ) {
            $heartbeatAdvanced = $true
            $postSupervisor = $heartbeat
            break
        }
    }
    if (-not $heartbeatAdvanced) {
        throw 'Supervisor heartbeat did not advance after network reconnect.'
    }

    Save-JsonEvidence -Name 'supervisor-after-reconnect' -Value $postSupervisor
    Save-JsonEvidence -Name 'recovery-after-reconnect' -Value $postRecovery

    $desiredStateRestored = 'running'
    if ($desiredStateBefore -eq 'stopped') {
        Stop-QualificationSupervisor
        $supervisorStarted = $false
        Invoke-ManagerMutation -Action Stop
        Start-QualificationSupervisor
        $supervisorStarted = $true
        $desiredStateRestored = 'stopped'
    }

    $summary = [ordered]@{
        schema_version = 2
        result = 'PASSED'
        repo_head = (git -C $RepoRoot rev-parse HEAD).Trim()
        run_dir = $RunDir
        desired_state_before = $desiredStateBefore
        desired_state_restored = $desiredStateRestored
        supervisor_pid = $supervisorPid
        old_tunnel_pid = $tunnelPid
        new_tunnel_pid = $postTunnelPid
        reconnect_mode = $reconnectMode
        disconnect_confirmed_at = $disconnectConfirmedAt
        reconnect_confirmed_at = $reconnectConfirmedAt
        offline_health_code = [string]$offlineDetected.health_code
        offline_runtime_ready = [bool]$offlineDetected.runtime_ready
        offline_openai_ready = [bool]$offlineDetected.openai_ready
        offline_observation_seconds = $OfflineObservationSeconds
        supervisor_pid_stable = $true
        tunnel_pid_stable = ($postTunnelPid -eq $tunnelPid)
        recovery_receipt_total_before = $recoveriesBefore
        recovery_receipt_total_after = $recoveriesAfter
        recovery_count_delta = $recoveryDelta
        reconnect_runtime_ready = [bool]$reconnected.runtime_ready
        reconnect_openai_ready = [bool]$reconnected.openai_ready
        supervisor_heartbeat_verified = $heartbeatAdvanced
        completed_at = (Get-Date).ToUniversalTime().ToString('o')
    }
    Save-JsonEvidence -Name 'summary' -Value $summary
    $qualificationPassed = $true

    Write-Result 'TRANSPORT_SUPERVISOR_NETWORK_QUALIFICATION_RESULT' 'PASSED'
    Write-Result 'SUPERVISOR_PID' $supervisorPid
    Write-Result 'OLD_TUNNEL_PID' $tunnelPid
    Write-Result 'NEW_TUNNEL_PID' $postTunnelPid
    Write-Result 'RECONNECT_MODE' $reconnectMode
    Write-Result 'SUPERVISOR_PID_STABLE' $summary['supervisor_pid_stable']
    Write-Result 'TUNNEL_PID_STABLE' $summary['tunnel_pid_stable']
    Write-Result 'RECOVERY_TOTAL_BEFORE' $summary['recovery_receipt_total_before']
    Write-Result 'RECOVERY_TOTAL_AFTER' $summary['recovery_receipt_total_after']
    Write-Result 'RECOVERY_COUNT_DELTA' $summary['recovery_count_delta']
    Write-Result 'OFFLINE_RUNTIME_READY' $summary['offline_runtime_ready']
    Write-Result 'OFFLINE_OPENAI_READY' $summary['offline_openai_ready']
    Write-Result 'RECONNECT_RUNTIME_READY' $summary['reconnect_runtime_ready']
    Write-Result 'RECONNECT_OPENAI_READY' $summary['reconnect_openai_ready']
    Write-Result 'SUPERVISOR_HEARTBEAT_VERIFIED' $summary['supervisor_heartbeat_verified']
    Write-Result 'RESULT_DIR' $RunDir
}
catch {
    $failure = $_
    try {
        [ordered]@{
            schema_version = 1
            result = 'FAILED'
            desired_state_before = $desiredStateBefore
            supervisor_started = $supervisorStarted
            error_type = $failure.Exception.GetType().Name
            error_message = $failure.Exception.Message
            failed_at = (Get-Date).ToUniversalTime().ToString('o')
        } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $RunDir 'failure.json') -Encoding utf8
    }
    catch {}

    try {
        if (Test-Path -LiteralPath $SupervisorStateFile -PathType Leaf) {
            Copy-Item -LiteralPath $SupervisorStateFile -Destination (Join-Path $RunDir 'supervisor-failure.json') -Force
        }
        if (Test-Path -LiteralPath $RecoveryStateFile -PathType Leaf) {
            Copy-Item -LiteralPath $RecoveryStateFile -Destination (Join-Path $RunDir 'recovery-failure.json') -Force
        }
        if (Test-Path -LiteralPath $SupervisorLogFile -PathType Leaf) {
            Get-Content -LiteralPath $SupervisorLogFile -Tail 200 |
                Set-Content -LiteralPath (Join-Path $RunDir 'supervisor-log-tail.txt') -Encoding utf8
        }
    }
    catch {}

    if ($installAttempted -and -not $qualificationPassed) {
        try { & $Installer -Uninstall | Out-Host } catch {}
        try {
            if ($desiredStateBefore -eq 'running') {
                Invoke-ManagerMutation -Action Stop
                Invoke-ManagerMutation -Action Start
            }
            else {
                Invoke-ManagerMutation -Action Stop
            }
        }
        catch {}
    }

    throw $failure
}
