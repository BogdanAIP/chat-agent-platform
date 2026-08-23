[CmdletBinding()]
param(
    [ValidateRange(30, 600)]
    [int]$ResumeReadyTimeoutSeconds = 240,

    [ValidateRange(5, 120)]
    [int]$MinimumSleepEvidenceSeconds = 10,

    [string]$OutputRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $IsWindows) {
    throw 'Transport Supervisor sleep/resume qualification supports Windows only.'
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
    $OutputRoot = Join-Path $LocalRoot 'transport-supervisor-sleep-resume-qualification'
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

function Get-NormalizedPowerEvents {
    param([Parameter(Mandatory)] [datetime]$StartTime)

    $events = @(
        Get-WinEvent -FilterHashtable @{ LogName = 'System'; StartTime = $StartTime } -ErrorAction SilentlyContinue |
            Where-Object {
                (
                    $_.ProviderName -eq 'Microsoft-Windows-Kernel-Power' -and
                    [int]$_.Id -in @(42, 107, 506, 507)
                ) -or
                (
                    $_.ProviderName -eq 'Microsoft-Windows-Power-Troubleshooter' -and
                    [int]$_.Id -eq 1
                )
            } |
            Sort-Object TimeCreated
    )

    return @(
        foreach ($event in $events) {
            [pscustomobject]@{
                time_created = $event.TimeCreated.ToUniversalTime().ToString('o')
                provider = [string]$event.ProviderName
                event_id = [int]$event.Id
                record_id = [long]$event.RecordId
            }
        }
    )
}

function Get-SleepResumeEvidence {
    param(
        [Parameter(Mandatory)] [datetime]$PromptTime,
        [Parameter(Mandatory)] [datetime]$ConfirmedResumeTime
    )

    $events = @(Get-NormalizedPowerEvents -StartTime $PromptTime.AddSeconds(-2))
    $promptUtc = $PromptTime.ToUniversalTime()
    $confirmedUtc = $ConfirmedResumeTime.ToUniversalTime()

    $classicEnter = @($events | Where-Object { $_.provider -eq 'Microsoft-Windows-Kernel-Power' -and $_.event_id -eq 42 })
    $classicExit = @($events | Where-Object {
        ($_.provider -eq 'Microsoft-Windows-Kernel-Power' -and $_.event_id -eq 107) -or
        ($_.provider -eq 'Microsoft-Windows-Power-Troubleshooter' -and $_.event_id -eq 1)
    })
    $modernEnter = @($events | Where-Object { $_.provider -eq 'Microsoft-Windows-Kernel-Power' -and $_.event_id -eq 506 })
    $modernExit = @($events | Where-Object { $_.provider -eq 'Microsoft-Windows-Kernel-Power' -and $_.event_id -eq 507 })

    foreach ($mode in @('classic', 'modern-standby')) {
        $enters = if ($mode -eq 'classic') { $classicEnter } else { $modernEnter }
        $exits = if ($mode -eq 'classic') { $classicExit } else { $modernExit }

        foreach ($enter in $enters) {
            $enterAt = [datetime]::Parse([string]$enter.time_created).ToUniversalTime()
            if ($enterAt -lt $promptUtc.AddSeconds(-2)) { continue }

            foreach ($exit in $exits) {
                $exitAt = [datetime]::Parse([string]$exit.time_created).ToUniversalTime()
                if ($exitAt -le $enterAt) { continue }
                if ($exitAt -gt $confirmedUtc.AddMinutes(2)) { continue }

                $durationSeconds = ($exitAt - $enterAt).TotalSeconds
                if ($durationSeconds -lt $MinimumSleepEvidenceSeconds) { continue }

                return [pscustomobject]@{
                    verified = $true
                    mode = $mode
                    enter_event = $enter
                    resume_event = $exit
                    sleep_evidence_seconds = [math]::Round($durationSeconds, 3)
                    events = $events
                }
            }
        }
    }

    return [pscustomobject]@{
        verified = $false
        mode = 'unverified'
        enter_event = $null
        resume_event = $null
        sleep_evidence_seconds = 0
        events = $events
    }
}

if (-not (Test-Path -LiteralPath $Manager -PathType Leaf)) {
    throw "Installed manager is missing: $Manager"
}

$desiredStateBefore = if (Test-Path -LiteralPath $OwnerFile -PathType Leaf) { 'running' } else { 'stopped' }
$installAttempted = $false
$qualificationPassed = $false
$supervisorStarted = $false

try {
    Write-Host '===== TRANSPORT SUPERVISOR: PHYSICAL SLEEP / RESUME QUALIFICATION =====' -ForegroundColor Cyan
    Write-Host 'This harness NEVER initiates sleep, hibernate, shutdown, reboot, or changes power settings.' -ForegroundColor Yellow
    Write-Host 'You will put Windows to sleep manually when prompted.' -ForegroundColor Yellow

    $powerCfgPath = (Get-Command 'powercfg.exe' -ErrorAction Stop).Source
    $powerCfgText = (& $powerCfgPath /a 2>&1 | Out-String).Trim()
    $powerCfgText | Set-Content -LiteralPath (Join-Path $RunDir 'powercfg-a.txt') -Encoding utf8

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
        throw "Sleep/resume qualification requires semantic/direct profile. Current profile=$($baseline.settings.profile)"
    }

    if (-not [bool]$baseline.runtime_ready -or -not [bool]$baseline.openai_ready) {
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
        throw 'Baseline did not become fully ready before sleep/resume qualification.'
    }
    Save-JsonEvidence -Name 'healthy-baseline' -Value $healthy

    if (-not (Test-Path -LiteralPath $OwnerFile -PathType Leaf)) {
        throw 'Sleep/resume qualification requires desired running state before suspend.'
    }
    $ownerBefore = Get-Content -LiteralPath $OwnerFile -Raw | ConvertFrom-Json
    Save-JsonEvidence -Name 'owner-before-sleep' -Value $ownerBefore

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
        throw 'Supervisor did not publish a clean baseline receipt before sleep.'
    }

    Save-JsonEvidence -Name 'supervisor-before-sleep' -Value $baselineSupervisorReceipt
    Save-JsonEvidence -Name 'recovery-before-sleep' -Value $baselineRecoveryReceipt
    $recoveriesBefore = [int]$baselineRecoveryReceipt.total_recoveries

    $sleepPromptAt = Get-Date
    Write-Host ''
    Write-Host 'ACTION REQUIRED: put Windows into REAL Sleep now.' -ForegroundColor Cyan
    Write-Host 'Use Start -> Power -> Sleep (or your normal physical Sleep action).' -ForegroundColor Yellow
    Write-Host "Keep the machine asleep for at least $MinimumSleepEvidenceSeconds seconds, then wake/unlock it." -ForegroundColor Yellow
    Write-Host 'After wake, restore normal network connectivity and any required VPN/proxy path before pressing Enter.' -ForegroundColor Yellow
    Write-Host 'Confirm the external path is usable; do NOT manually restart Chat Agent Platform.' -ForegroundColor Yellow
    Write-Host 'Do NOT close this PowerShell window.' -ForegroundColor Yellow
    Read-Host 'After Windows and the required external network/VPN/proxy path have resumed, press Enter here' | Out-Null
    $resumeConfirmedAt = Get-Date

    $powerEvidence = Get-SleepResumeEvidence -PromptTime $sleepPromptAt -ConfirmedResumeTime $resumeConfirmedAt
    Save-JsonEvidence -Name 'power-events' -Value $powerEvidence
    if (-not [bool]$powerEvidence.verified) {
        throw 'A real Windows sleep/resume transition was not verified in the System event log.'
    }

    if (-not (Test-Path -LiteralPath $OwnerFile -PathType Leaf)) {
        throw 'Desired running owner state disappeared across sleep/resume.'
    }
    $ownerAfter = Get-Content -LiteralPath $OwnerFile -Raw | ConvertFrom-Json
    Save-JsonEvidence -Name 'owner-after-resume' -Value $ownerAfter
    if ([string]$ownerAfter.controller_path -ne [string]$ownerBefore.controller_path) {
        throw 'Manager controller ownership changed across sleep/resume.'
    }

    $postSupervisors = @(Get-ExactSupervisorProcesses)
    if ($postSupervisors.Count -ne 1) {
        throw "Expected exactly one supervisor after resume; found $($postSupervisors.Count)."
    }
    if ([int]$postSupervisors[0].ProcessId -ne $supervisorPid) {
        throw "Supervisor PID changed across ordinary Windows sleep/resume: before=$supervisorPid after=$([int]$postSupervisors[0].ProcessId)."
    }

    $resumeSamples = @()
    $resumedHealthy = $null
    $resumeDeadline = (Get-Date).AddSeconds($ResumeReadyTimeoutSeconds)
    while ((Get-Date) -lt $resumeDeadline) {
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
            $resumeSamples += $sample

            if (
                [bool]$status.runtime_ready -and
                [bool]$status.openai_ready -and
                $currentSupervisors.Count -eq 1 -and
                [int]$currentSupervisors[0].ProcessId -eq $supervisorPid -and
                $currentTunnels.Count -eq 1
            ) {
                $resumedHealthy = $status
                break
            }
        }
        catch {}
        Start-Sleep -Seconds 1
    }
    $resumeSamples | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $RunDir 'resume-samples.json') -Encoding utf8

    if ($null -eq $resumedHealthy) {
        $lastSample = if ($resumeSamples.Count -gt 0) { $resumeSamples[-1] } else { $null }
        if ($null -ne $lastSample) {
            throw "Healthy state did not return automatically within $ResumeReadyTimeoutSeconds seconds after resume. Last sample: runtime_ready=$($lastSample.runtime_ready), openai_ready=$($lastSample.openai_ready), health_code=$($lastSample.health_code), recovery_action=$($lastSample.recovery_action), remote_tunnel_status=$($lastSample.remote_tunnel_status), control_plane_poll_fresh=$($lastSample.control_plane_poll_fresh), supervisor_pid=$($lastSample.supervisor_pid), tunnel_pid=$($lastSample.tunnel_pid), recovery_total=$($lastSample.recovery_total)."
        }
        throw "Healthy state did not return automatically within $ResumeReadyTimeoutSeconds seconds after resume and no sample was captured."
    }
    Save-JsonEvidence -Name 'manager-after-resume' -Value $resumedHealthy

    $postRecovery = $null
    $postSupervisor = $null
    $postTunnels = @()
    $receiptSettleDeadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $receiptSettleDeadline) {
        $candidateRecovery = Read-RecoveryState
        $candidateSupervisor = Read-SupervisorState
        $candidateTunnels = @(Get-DirectTunnelProcesses)

        if (
            $null -ne $candidateRecovery -and
            $null -ne $candidateSupervisor -and
            $candidateTunnels.Count -eq 1 -and
            [int]$candidateSupervisor.supervisor_pid -eq $supervisorPid
        ) {
            $candidateTunnelPid = [int]$candidateTunnels[0].ProcessId
            $candidateDelta = [int]$candidateRecovery.total_recoveries - $recoveriesBefore
            if ($candidateDelta -lt 0 -or $candidateDelta -gt 1) {
                throw "Sleep/resume caused an unexpected recovery count delta: $candidateDelta. Expected 0 or 1."
            }

            $candidateHealthy = (
                [string]$candidateSupervisor.supervisor_state -eq 'healthy' -and
                [string]$candidateSupervisor.health_code -eq 'READY' -and
                [string]$candidateSupervisor.recovery_action -eq 'none'
            )
            $coherentSeamless = (
                $candidateHealthy -and
                $candidateDelta -eq 0 -and
                $candidateTunnelPid -eq $tunnelPid
            )
            $coherentRecovery = (
                $candidateHealthy -and
                $candidateDelta -eq 1 -and
                $candidateTunnelPid -ne $tunnelPid -and
                [int]$candidateRecovery.consecutive_attempts -eq 0 -and
                -not [string]::IsNullOrWhiteSpace([string]$candidateRecovery.last_success_at)
            )

            if ($coherentSeamless -or $coherentRecovery) {
                $postRecovery = $candidateRecovery
                $postSupervisor = $candidateSupervisor
                $postTunnels = $candidateTunnels
                break
            }
        }
        Start-Sleep -Milliseconds 500
    }

    if ($null -eq $postRecovery -or $null -eq $postSupervisor -or $postTunnels.Count -ne 1) {
        throw 'Post-resume process and recovery receipts did not settle into a coherent state within 30 seconds.'
    }

    $recoveriesAfter = [int]$postRecovery.total_recoveries
    $recoveryDelta = $recoveriesAfter - $recoveriesBefore
    $postTunnelPid = [int]$postTunnels[0].ProcessId
    $resumeMode = if ($recoveryDelta -eq 0) { 'seamless' } else { 'bounded_recovery' }

    if ($resumeMode -eq 'seamless' -and $postTunnelPid -ne $tunnelPid) {
        throw 'Tunnel PID changed after resume without a committed supervisor recovery receipt.'
    }
    if ($resumeMode -eq 'bounded_recovery' -and $postTunnelPid -eq $tunnelPid) {
        throw 'Recovery count increased after resume but tunnel PID did not change.'
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
        throw 'Supervisor heartbeat did not advance after Windows resume.'
    }

    Save-JsonEvidence -Name 'supervisor-after-resume' -Value $postSupervisor
    Save-JsonEvidence -Name 'recovery-after-resume' -Value $postRecovery

    $summary = [ordered]@{
        schema_version = 1
        result = 'PASSED'
        repo_head = (git -C $RepoRoot rev-parse HEAD).Trim()
        run_dir = $RunDir
        desired_state_before = $desiredStateBefore
        desired_state_after = if (Test-Path -LiteralPath $OwnerFile -PathType Leaf) { 'running' } else { 'stopped' }
        power_event_mode = [string]$powerEvidence.mode
        sleep_evidence_seconds = [double]$powerEvidence.sleep_evidence_seconds
        supervisor_pid = $supervisorPid
        supervisor_pid_stable = $true
        old_tunnel_pid = $tunnelPid
        new_tunnel_pid = $postTunnelPid
        resume_mode = $resumeMode
        recovery_receipt_total_before = $recoveriesBefore
        recovery_receipt_total_after = $recoveriesAfter
        recovery_count_delta = $recoveryDelta
        resume_runtime_ready = [bool]$resumedHealthy.runtime_ready
        resume_openai_ready = [bool]$resumedHealthy.openai_ready
        supervisor_heartbeat_verified = $heartbeatAdvanced
        sleep_prompted_at = $sleepPromptAt.ToUniversalTime().ToString('o')
        resume_confirmed_at = $resumeConfirmedAt.ToUniversalTime().ToString('o')
        completed_at = (Get-Date).ToUniversalTime().ToString('o')
    }
    Save-JsonEvidence -Name 'summary' -Value $summary
    $qualificationPassed = $true

    Write-Result 'TRANSPORT_SUPERVISOR_SLEEP_RESUME_QUALIFICATION_RESULT' 'PASSED'
    Write-Result 'POWER_EVENT_MODE' $summary['power_event_mode']
    Write-Result 'SLEEP_EVIDENCE_SECONDS' $summary['sleep_evidence_seconds']
    Write-Result 'SUPERVISOR_PID' $supervisorPid
    Write-Result 'SUPERVISOR_PID_STABLE' $summary['supervisor_pid_stable']
    Write-Result 'OLD_TUNNEL_PID' $tunnelPid
    Write-Result 'NEW_TUNNEL_PID' $postTunnelPid
    Write-Result 'RESUME_MODE' $resumeMode
    Write-Result 'RECOVERY_TOTAL_BEFORE' $recoveriesBefore
    Write-Result 'RECOVERY_TOTAL_AFTER' $recoveriesAfter
    Write-Result 'RECOVERY_COUNT_DELTA' $recoveryDelta
    Write-Result 'RESUME_RUNTIME_READY' $summary['resume_runtime_ready']
    Write-Result 'RESUME_OPENAI_READY' $summary['resume_openai_ready']
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
        try {
            $failurePowerEvidence = Get-SleepResumeEvidence -PromptTime $sleepPromptAt -ConfirmedResumeTime (Get-Date)
            Save-JsonEvidence -Name 'power-events-failure' -Value $failurePowerEvidence
        }
        catch {}
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
