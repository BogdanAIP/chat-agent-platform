[CmdletBinding()]
param(
    [ValidateRange(30, 300)]
    [int]$RecoveryTimeoutSeconds = 120,

    [string]$OutputRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $IsWindows) {
    throw 'Transport Supervisor physical qualification supports Windows only.'
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
    $OutputRoot = Join-Path $LocalRoot 'transport-supervisor-qualification'
}
$RunDir = Join-Path $OutputRoot ('run-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Write-Result {
    param([Parameter(Mandatory)] [string]$Name, [Parameter(Mandatory)] $Value)
    Write-Host "$Name=$Value"
}

function ConvertTo-UtcDateTime {
    param([Parameter(Mandatory)] $Value)

    if ($Value -is [datetimeoffset]) {
        return ([datetimeoffset]$Value).UtcDateTime
    }

    if ($Value -is [datetime]) {
        $date = [datetime]$Value
        if ($date.Kind -eq [DateTimeKind]::Unspecified) {
            return [datetime]::SpecifyKind($date, [DateTimeKind]::Utc)
        }
        return $date.ToUniversalTime()
    }

    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) {
        throw 'Timestamp is empty.'
    }

    try {
        $date = [datetime]::Parse(
            $text,
            [Globalization.CultureInfo]::InvariantCulture,
            [Globalization.DateTimeStyles]::RoundtripKind
        )
    }
    catch {
        # Legacy supervisor receipts could contain a culture-formatted UTC wall
        # clock after PowerShell materialized an ISO JSON string as DateTime.
        $date = [datetime]::Parse($text, [Globalization.CultureInfo]::CurrentCulture)
    }

    if ($date.Kind -eq [DateTimeKind]::Unspecified) {
        return [datetime]::SpecifyKind($date, [DateTimeKind]::Utc)
    }
    return $date.ToUniversalTime()
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
        $diagnostic = (([string]$result.stderr + "`n" + [string]$result.stdout).Trim())
        throw "Manager $Action failed: $diagnostic"
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

function Save-JsonEvidence {
    param([Parameter(Mandatory)] [string]$Name, [Parameter(Mandatory)] $Value)
    $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $RunDir "$Name.json") -Encoding utf8
}

if (-not (Test-Path -LiteralPath $Manager -PathType Leaf)) {
    throw "Installed manager is missing: $Manager"
}

$desiredStateBefore = if (Test-Path -LiteralPath $OwnerFile -PathType Leaf) { 'running' } else { 'stopped' }
$preInstallStatus = Invoke-ManagerStatus
Save-JsonEvidence -Name 'manager-pre-install' -Value $preInstallStatus

if ([string]$preInstallStatus.settings.profile -notin @('semantic', 'semantic-direct')) {
    throw "Physical supervisor qualification requires the configured semantic/direct profile. Current profile=$($preInstallStatus.settings.profile)"
}

$installAttempted = $false
$qualificationPassed = $false
$supervisorStarted = $false

try {
    Write-Host '===== TRANSPORT SUPERVISOR: INSTALL QUALIFICATION BUILD =====' -ForegroundColor Cyan
    $installAttempted = $true

    # Install/register first, but deliberately do not start the supervisor yet.
    # The baseline lifecycle mutation must run without the supervisor competing
    # for the public manager mutex. This prevents a qualification-only race.
    # This is a PowerShell script invocation: with ErrorActionPreference=Stop,
    # failures propagate as terminating errors. Do not inspect LASTEXITCODE here;
    # it is a native-process status variable and may be unset under StrictMode.
    & $Installer -NoStart

    if (@(Get-ExactSupervisorProcesses).Count -ne 0) {
        throw 'Qualification installer -NoStart unexpectedly left a supervisor process running.'
    }

    # Qualification state is isolated from earlier physical attempts. Preserve
    # the old receipts as evidence, then remove them before the test supervisor
    # starts so backoff counters and success timestamps cannot leak across runs.
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

    if (-not [bool]$baseline.runtime_ready) {
        Write-Host 'Resetting an unhealthy/stopped semantic runtime before the fault-injection baseline...' -ForegroundColor Yellow
        Invoke-ManagerMutation -Action Stop
        Invoke-ManagerMutation -Action Start
    }

    $readyDeadline = (Get-Date).AddSeconds(90)
    $healthy = $null
    while ((Get-Date) -lt $readyDeadline) {
        $candidate = Invoke-ManagerStatus
        if ([bool]$candidate.runtime_ready -and [int]$candidate.tunnel_process_count -eq 1) {
            $healthy = $candidate
            break
        }
        Start-Sleep -Seconds 1
    }
    if ($null -eq $healthy) {
        throw 'Baseline direct semantic runtime did not become runtime-ready before fault injection.'
    }
    Save-JsonEvidence -Name 'healthy-baseline' -Value $healthy

    Write-Host 'Starting supervisor only after the direct semantic baseline is healthy...' -ForegroundColor Yellow
    Start-QualificationSupervisor
    $supervisorStarted = $true

    $supervisors = @(Get-ExactSupervisorProcesses)
    if ($supervisors.Count -ne 1) {
        throw "Expected exactly one supervisor process; found $($supervisors.Count)."
    }
    $oldSupervisorPid = [int]$supervisors[0].ProcessId

    # Require one healthy supervisor reconciliation before injecting the fault.
    # This proves the loop is alive and guarantees a clean recovery counter.
    $supervisorBaselineReceipt = $null
    $recoveryBaselineReceipt = $null
    $supervisorBaselineDeadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $supervisorBaselineDeadline) {
        if (
            (Test-Path -LiteralPath $SupervisorStateFile -PathType Leaf) -and
            (Test-Path -LiteralPath $RecoveryStateFile -PathType Leaf)
        ) {
            try {
                $candidateSupervisorBaseline = Get-Content -LiteralPath $SupervisorStateFile -Raw | ConvertFrom-Json
                $candidateRecoveryBaseline = Get-Content -LiteralPath $RecoveryStateFile -Raw | ConvertFrom-Json
                if (
                    [int]$candidateSupervisorBaseline.supervisor_pid -eq $oldSupervisorPid -and
                    [bool]$candidateSupervisorBaseline.runtime_ready -and
                    [int]$candidateRecoveryBaseline.total_recoveries -eq 0 -and
                    [int]$candidateRecoveryBaseline.consecutive_attempts -eq 0
                ) {
                    $supervisorBaselineReceipt = $candidateSupervisorBaseline
                    $recoveryBaselineReceipt = $candidateRecoveryBaseline
                    break
                }
            }
            catch {}
        }
        Start-Sleep -Milliseconds 500
    }

    if ($null -eq $supervisorBaselineReceipt -or $null -eq $recoveryBaselineReceipt) {
        throw 'Supervisor did not publish a clean healthy baseline before fault injection.'
    }

    Copy-Item -LiteralPath $SupervisorStateFile -Destination (Join-Path $RunDir 'supervisor-before-fault.json') -Force
    Copy-Item -LiteralPath $RecoveryStateFile -Destination (Join-Path $RunDir 'recovery-before-fault.json') -Force
    $recoveryCountBeforeFault = [int]$recoveryBaselineReceipt.total_recoveries

    $tunnelProcesses = @(Get-DirectTunnelProcesses)
    if ($tunnelProcesses.Count -ne 1) {
        throw "Expected exactly one direct tunnel process; found $($tunnelProcesses.Count)."
    }
    $oldTunnelPid = [int]$tunnelProcesses[0].ProcessId

    Write-Host "Injecting owned tunnel-client process failure PID=$oldTunnelPid" -ForegroundColor Yellow
    $faultInjectedAt = (Get-Date).ToUniversalTime()
    Stop-Process -Id $oldTunnelPid -Force -ErrorAction Stop

    $recovered = $null
    $newTunnelPid = $null
    $deadline = (Get-Date).AddSeconds($RecoveryTimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 1
        try {
            $status = Invoke-ManagerStatus
            $currentTunnel = @(Get-DirectTunnelProcesses)
            $currentSupervisor = @(Get-ExactSupervisorProcesses)
            if (
                [bool]$status.runtime_ready -and
                $currentTunnel.Count -eq 1 -and
                [int]$currentTunnel[0].ProcessId -ne $oldTunnelPid -and
                $currentSupervisor.Count -eq 1 -and
                [int]$currentSupervisor[0].ProcessId -eq $oldSupervisorPid
            ) {
                $recovered = $status
                $newTunnelPid = [int]$currentTunnel[0].ProcessId
                break
            }
        }
        catch {}
    }

    if ($null -eq $recovered) {
        if (Test-Path -LiteralPath $SupervisorStateFile -PathType Leaf) {
            Copy-Item -LiteralPath $SupervisorStateFile -Destination (Join-Path $RunDir 'supervisor-failure.json') -Force
        }
        throw "Supervisor did not recover the killed direct tunnel within $RecoveryTimeoutSeconds seconds."
    }

    Save-JsonEvidence -Name 'manager-after-recovery' -Value $recovered

    # A replacement tunnel plus a live supervisor PID is insufficient evidence.
    # Require the supervisor to finish its own recovery transaction and publish
    # both machine-readable state files after the injected fault.
    $supervisorReceipt = $null
    $recoveryReceipt = $null
    $receiptDeadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $receiptDeadline) {
        if (
            (Test-Path -LiteralPath $SupervisorStateFile -PathType Leaf) -and
            (Test-Path -LiteralPath $RecoveryStateFile -PathType Leaf)
        ) {
            try {
                $candidateSupervisorReceipt = Get-Content -LiteralPath $SupervisorStateFile -Raw | ConvertFrom-Json
                $candidateRecoveryReceipt = Get-Content -LiteralPath $RecoveryStateFile -Raw | ConvertFrom-Json
                $observedAt = ConvertTo-UtcDateTime $candidateSupervisorReceipt.observed_at
                $lastSuccessAt = ConvertTo-UtcDateTime $candidateRecoveryReceipt.last_success_at
                if (
                    [int]$candidateSupervisorReceipt.supervisor_pid -eq $oldSupervisorPid -and
                    [bool]$candidateSupervisorReceipt.runtime_ready -and
                    [int]$candidateRecoveryReceipt.total_recoveries -gt $recoveryCountBeforeFault -and
                    $observedAt -ge $faultInjectedAt -and
                    $lastSuccessAt -ge $faultInjectedAt
                ) {
                    $supervisorReceipt = $candidateSupervisorReceipt
                    $recoveryReceipt = $candidateRecoveryReceipt
                    break
                }
            }
            catch {}
        }
        Start-Sleep -Milliseconds 500
    }

    if ($null -eq $supervisorReceipt -or $null -eq $recoveryReceipt) {
        throw 'Supervisor did not publish a verified post-recovery receipt.'
    }

    # Prove the long-lived loop is still responsive after the recovery receipt.
    # The next reconciliation cycle must update supervisor.json while the exact
    # same supervisor PID remains authoritative.
    $firstObservedAt = ConvertTo-UtcDateTime $supervisorReceipt.observed_at
    $supervisorHeartbeatVerified = $false
    $heartbeatDeadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $heartbeatDeadline) {
        Start-Sleep -Seconds 1
        try {
            $heartbeat = Get-Content -LiteralPath $SupervisorStateFile -Raw | ConvertFrom-Json
            $heartbeatObservedAt = ConvertTo-UtcDateTime $heartbeat.observed_at
            $heartbeatSupervisors = @(Get-ExactSupervisorProcesses)
            if (
                $heartbeatSupervisors.Count -eq 1 -and
                [int]$heartbeatSupervisors[0].ProcessId -eq $oldSupervisorPid -and
                [int]$heartbeat.supervisor_pid -eq $oldSupervisorPid -and
                $heartbeatObservedAt -gt $firstObservedAt
            ) {
                $supervisorHeartbeatVerified = $true
                $supervisorReceipt = $heartbeat
                $recoveryReceipt = Get-Content -LiteralPath $RecoveryStateFile -Raw | ConvertFrom-Json
                break
            }
        }
        catch {}
    }

    if (-not $supervisorHeartbeatVerified) {
        throw 'Supervisor heartbeat did not advance after recovery.'
    }

    Copy-Item -LiteralPath $SupervisorStateFile -Destination (Join-Path $RunDir 'supervisor-after-recovery.json') -Force
    Copy-Item -LiteralPath $RecoveryStateFile -Destination (Join-Path $RunDir 'recovery-after-recovery.json') -Force

    $resourceRows = @()
    foreach ($process in @(Get-ExactSupervisorProcesses)) {
        $p = Get-Process -Id ([int]$process.ProcessId) -ErrorAction Stop
        $resourceRows += [pscustomobject]@{
            role = 'supervisor'
            pid = $p.Id
            working_set_bytes = $p.WorkingSet64
            private_memory_bytes = $p.PrivateMemorySize64
            cpu_seconds = $p.CPU
        }
    }
    foreach ($process in @(Get-DirectTunnelProcesses)) {
        $p = Get-Process -Id ([int]$process.ProcessId) -ErrorAction Stop
        $resourceRows += [pscustomobject]@{
            role = 'tunnel-client'
            pid = $p.Id
            working_set_bytes = $p.WorkingSet64
            private_memory_bytes = $p.PrivateMemorySize64
            cpu_seconds = $p.CPU
        }
    }
    $resourceRows | Export-Csv -LiteralPath (Join-Path $RunDir 'resources.csv') -NoTypeInformation -Encoding utf8

    $currentSupervisors = @(Get-ExactSupervisorProcesses)
    $supervisorPidStable = (
        $currentSupervisors.Count -eq 1 -and
        [int]$currentSupervisors[0].ProcessId -eq $oldSupervisorPid
    )

    $desiredStateRestored = 'running'
    if ($desiredStateBefore -eq 'stopped') {
        # Stop the qualification supervisor before the explicit lifecycle
        # mutation, then restart it in idle mode after the owner is removed.
        Stop-QualificationSupervisor
        $supervisorStarted = $false
        Invoke-ManagerMutation -Action Stop
        Start-QualificationSupervisor
        $supervisorStarted = $true
        $desiredStateRestored = 'stopped'
    }

    $summary = [ordered]@{
        schema_version = 1
        result = 'PASSED'
        repo_head = (git -C $RepoRoot rev-parse HEAD).Trim()
        run_dir = $RunDir
        desired_state_before = $desiredStateBefore
        desired_state_restored = $desiredStateRestored
        old_supervisor_pid = $oldSupervisorPid
        old_tunnel_pid = $oldTunnelPid
        new_tunnel_pid = $newTunnelPid
        tunnel_pid_changed = ($newTunnelPid -ne $oldTunnelPid)
        supervisor_pid_stable = $supervisorPidStable
        supervisor_receipt_verified = ($null -ne $supervisorReceipt)
        supervisor_heartbeat_verified = $supervisorHeartbeatVerified
        recovery_receipt_total_before_fault = $recoveryCountBeforeFault
        recovery_receipt_total_recoveries = [int]$recoveryReceipt.total_recoveries
        runtime_ready_after_recovery = [bool]$recovered.runtime_ready
        health_code_after_recovery = [string]$recovered.health_code
        openai_control_ready_after_recovery = [bool]$recovered.openai_ready
        completed_at = (Get-Date).ToUniversalTime().ToString('o')
    }
    Save-JsonEvidence -Name 'summary' -Value $summary

    $qualificationPassed = $true

    Write-Result 'TRANSPORT_SUPERVISOR_QUALIFICATION_RESULT' 'PASSED'
    Write-Result 'OLD_TUNNEL_PID' $oldTunnelPid
    Write-Result 'NEW_TUNNEL_PID' $newTunnelPid
    Write-Result 'TUNNEL_PID_CHANGED' $summary['tunnel_pid_changed']
    Write-Result 'SUPERVISOR_PID_STABLE' $summary['supervisor_pid_stable']
    Write-Result 'SUPERVISOR_RECEIPT_VERIFIED' $summary['supervisor_receipt_verified']
    Write-Result 'SUPERVISOR_HEARTBEAT_VERIFIED' $summary['supervisor_heartbeat_verified']
    Write-Result 'RECOVERY_RECEIPT_TOTAL_BEFORE_FAULT' $summary['recovery_receipt_total_before_fault']
    Write-Result 'RECOVERY_RECEIPT_TOTAL_RECOVERIES' $summary['recovery_receipt_total_recoveries']
    Write-Result 'RUNTIME_READY_AFTER_RECOVERY' $summary['runtime_ready_after_recovery']
    Write-Result 'HEALTH_CODE_AFTER_RECOVERY' $summary['health_code_after_recovery']
    Write-Result 'OPENAI_CONTROL_READY_AFTER_RECOVERY' $summary['openai_control_ready_after_recovery']
    Write-Result 'DESIRED_STATE_BEFORE' $summary['desired_state_before']
    Write-Result 'DESIRED_STATE_RESTORED' $summary['desired_state_restored']
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

    # Capture live supervisor evidence before uninstall stops the test process.
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
        try {
            & $Installer -Uninstall | Out-Host
        }
        catch {
            Write-Warning "Qualification rollback could not uninstall supervisor assets: $($_.Exception.Message)"
        }

        try {
            if ($desiredStateBefore -eq 'running') {
                Invoke-ManagerMutation -Action Stop
                Invoke-ManagerMutation -Action Start
            }
            else {
                Invoke-ManagerMutation -Action Stop
            }
        }
        catch {
            Write-Warning "Qualification rollback could not restore the pre-test desired state: $($_.Exception.Message)"
        }
    }

    throw $failure
}
