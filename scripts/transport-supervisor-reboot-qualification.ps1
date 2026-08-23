[CmdletBinding()]
param(
    [ValidateSet('Prepare', 'Verify')]
    [string]$Phase = 'Prepare',

    [ValidateRange(30, 600)]
    [int]$ReadyTimeoutSeconds = 300,

    [string]$RunDir,

    [string]$OutputRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $IsWindows) {
    throw 'Transport Supervisor reboot/logon qualification supports Windows only.'
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
    $OutputRoot = Join-Path $LocalRoot 'transport-supervisor-reboot-qualification'
}
$PendingFile = Join-Path $OutputRoot 'pending.json'
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

function Write-Result {
    param([Parameter(Mandatory)] [string]$Name, [Parameter(Mandatory)] $Value)
    Write-Host "$Name=$Value"
}

function Save-JsonEvidence {
    param(
        [Parameter(Mandatory)] [string]$Directory,
        [Parameter(Mandatory)] [string]$Name,
        [Parameter(Mandatory)] $Value
    )
    $Value |
        ConvertTo-Json -Depth 12 |
        Set-Content -LiteralPath (Join-Path $Directory "$Name.json") -Encoding utf8
}

function Write-AtomicJson {
    param(
        [Parameter(Mandatory)] [string]$Path,
        [Parameter(Mandatory)] $Value
    )

    $parent = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $temporary = "$Path.new-$PID"
    try {
        $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $temporary -Encoding utf8
        Move-Item -LiteralPath $temporary -Destination $Path -Force
    }
    finally {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
    }
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

function Get-ProcessCreationUtc {
    param([Parameter(Mandatory)] $Process)

    $value = $Process.CreationDate
    if ($null -eq $value) { return $null }
    try {
        if ($value -is [datetime]) {
            return ([datetime]$value).ToUniversalTime()
        }
        return ([Management.ManagementDateTimeConverter]::ToDateTime([string]$value)).ToUniversalTime()
    }
    catch {
        return $null
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

function Get-BootTimeUtc {
    $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
    return ([datetime]$os.LastBootUpTime).ToUniversalTime()
}

function Get-TaskEvidence {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction Stop
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $logonTriggers = @(
        $task.Triggers |
            Where-Object { $_.CimClass.CimClassName -eq 'MSFT_TaskLogonTrigger' }
    )

    return [pscustomobject]@{
        task_name = [string]$task.TaskName
        task_state = [string]$task.State
        principal_user_id = [string]$task.Principal.UserId
        principal_logon_type = [string]$task.Principal.LogonType
        principal_run_level = [string]$task.Principal.RunLevel
        current_identity = $identity
        logon_trigger_count = $logonTriggers.Count
        logon_trigger_users = @($logonTriggers | ForEach-Object { [string]$_.UserId })
        action_execute = if ($task.Actions.Count -gt 0) { [string]$task.Actions[0].Execute } else { $null }
        action_arguments = if ($task.Actions.Count -gt 0) { [string]$task.Actions[0].Arguments } else { $null }
        last_run_time = if ($info.LastRunTime.Year -gt 1900) { $info.LastRunTime.ToUniversalTime().ToString('o') } else { $null }
        last_task_result = [long]$info.LastTaskResult
        missed_runs = [long]$info.NumberOfMissedRuns
    }
}

function Assert-TaskContract {
    param([Parameter(Mandatory)] $Evidence)

    if ([string]$Evidence.task_name -ne $TaskName) {
        throw 'Supervisor Scheduled Task name mismatch.'
    }
    if ([int]$Evidence.logon_trigger_count -ne 1) {
        throw "Expected exactly one current-user logon trigger; found $($Evidence.logon_trigger_count)."
    }
    if ([string]$Evidence.principal_user_id -ne [string]$Evidence.current_identity) {
        throw 'Supervisor Scheduled Task principal does not match the current Windows identity.'
    }
    if (@($Evidence.logon_trigger_users) -notcontains [string]$Evidence.current_identity) {
        throw 'Supervisor Scheduled Task logon trigger does not target the current Windows identity.'
    }
    if ([string]$Evidence.action_arguments -notmatch '(?i)-Action\s+Run') {
        throw 'Supervisor Scheduled Task action does not run the supervisor reconcile loop.'
    }
}

function Resolve-VerifyRunDir {
    if (-not [string]::IsNullOrWhiteSpace($RunDir)) {
        return [System.IO.Path]::GetFullPath($RunDir)
    }
    if (-not (Test-Path -LiteralPath $PendingFile -PathType Leaf)) {
        throw "No pending reboot qualification exists: $PendingFile"
    }
    $pending = Get-Content -LiteralPath $PendingFile -Raw | ConvertFrom-Json
    if (
        $null -eq $pending.PSObject.Properties['run_dir'] -or
        [string]::IsNullOrWhiteSpace([string]$pending.run_dir)
    ) {
        throw 'Pending reboot qualification is missing run_dir.'
    }
    return [System.IO.Path]::GetFullPath([string]$pending.run_dir)
}

if (-not (Test-Path -LiteralPath $Manager -PathType Leaf)) {
    throw "Installed manager is missing: $Manager"
}

if ($Phase -eq 'Prepare') {
    $RunDir = Join-Path $OutputRoot ('run-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

    Write-Host '===== TRANSPORT SUPERVISOR: PHYSICAL REBOOT / LOGON QUALIFICATION — PREPARE =====' -ForegroundColor Cyan
    Write-Host 'This harness NEVER initiates reboot, shutdown, sleep, hibernate, or changes power settings.' -ForegroundColor Yellow
    Write-Host 'After PREPARE succeeds, you will reboot Windows manually.' -ForegroundColor Yellow

    $repoHead = (git -C $RepoRoot rev-parse HEAD).Trim()
    if ([string]::IsNullOrWhiteSpace($repoHead)) {
        throw 'Could not resolve qualification repository HEAD.'
    }
    $scriptHash = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
    $bootBefore = Get-BootTimeUtc
    $preparedAt = (Get-Date).ToUniversalTime()

    $baseline = Invoke-ManagerStatus
    if ([string]$baseline.settings.profile -notin @('semantic', 'semantic-direct')) {
        throw "Reboot qualification requires semantic/direct profile. Current profile=$($baseline.settings.profile)"
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
        throw 'Baseline did not become fully ready before reboot qualification.'
    }
    Save-JsonEvidence -Directory $RunDir -Name 'healthy-before-reboot' -Value $healthy

    if (-not (Test-Path -LiteralPath $OwnerFile -PathType Leaf)) {
        throw 'Reboot qualification requires desired running owner state before reboot.'
    }
    $ownerBefore = Get-Content -LiteralPath $OwnerFile -Raw | ConvertFrom-Json
    Save-JsonEvidence -Directory $RunDir -Name 'owner-before-reboot' -Value $ownerBefore

    & $Installer

    $taskBefore = Get-TaskEvidence
    Assert-TaskContract -Evidence $taskBefore
    Save-JsonEvidence -Directory $RunDir -Name 'task-before-reboot' -Value $taskBefore

    $supervisorDeadline = (Get-Date).AddSeconds(30)
    $supervisors = @()
    while ((Get-Date) -lt $supervisorDeadline) {
        $supervisors = @(Get-ExactSupervisorProcesses)
        if ($supervisors.Count -eq 1) { break }
        Start-Sleep -Milliseconds 500
    }
    if ($supervisors.Count -ne 1) {
        throw "Expected exactly one supervisor before reboot; found $($supervisors.Count)."
    }
    $tunnels = @(Get-DirectTunnelProcesses)
    if ($tunnels.Count -ne 1) {
        throw "Expected exactly one direct tunnel before reboot; found $($tunnels.Count)."
    }

    $supervisorBeforeCreation = Get-ProcessCreationUtc -Process $supervisors[0]
    $tunnelBeforeCreation = Get-ProcessCreationUtc -Process $tunnels[0]
    $recoveryBefore = Read-RecoveryState
    $supervisorReceiptBefore = Read-SupervisorState
    if ($null -eq $recoveryBefore -or $null -eq $supervisorReceiptBefore) {
        throw 'Supervisor did not publish baseline reboot qualification receipts.'
    }

    Save-JsonEvidence -Directory $RunDir -Name 'supervisor-before-reboot' -Value $supervisorReceiptBefore
    Save-JsonEvidence -Directory $RunDir -Name 'recovery-before-reboot' -Value $recoveryBefore

    $prepare = [ordered]@{
        schema_version = 1
        phase = 'prepared'
        repo_head = $repoHead
        qualification_script_sha256 = $scriptHash
        run_dir = $RunDir
        prepared_at = $preparedAt.ToString('o')
        boot_time_before = $bootBefore.ToString('o')
        desired_state_before = 'running'
        owner_controller_path = [string]$ownerBefore.controller_path
        owner_started_at = [string]$ownerBefore.started_at
        supervisor_pid_before = [int]$supervisors[0].ProcessId
        supervisor_created_before = if ($null -ne $supervisorBeforeCreation) { $supervisorBeforeCreation.ToString('o') } else { $null }
        tunnel_pid_before = [int]$tunnels[0].ProcessId
        tunnel_created_before = if ($null -ne $tunnelBeforeCreation) { $tunnelBeforeCreation.ToString('o') } else { $null }
        recovery_total_before = [int]$recoveryBefore.total_recoveries
    }
    Save-JsonEvidence -Directory $RunDir -Name 'prepare' -Value $prepare
    Write-AtomicJson -Path $PendingFile -Value $prepare

    Write-Result 'TRANSPORT_SUPERVISOR_REBOOT_QUALIFICATION_PREPARE' 'PASSED'
    Write-Result 'EXACT_PREPARED_HEAD' $repoHead
    Write-Result 'BOOT_TIME_BEFORE' $prepare['boot_time_before']
    Write-Result 'SUPERVISOR_PID_BEFORE' $prepare['supervisor_pid_before']
    Write-Result 'TUNNEL_PID_BEFORE' $prepare['tunnel_pid_before']
    Write-Result 'RECOVERY_TOTAL_BEFORE' $prepare['recovery_total_before']
    Write-Result 'RESULT_DIR' $RunDir
    Write-Host ''
    Write-Host 'ACTION REQUIRED: manually restart Windows now.' -ForegroundColor Cyan
    Write-Host 'After logon, restore any required external VPN/proxy/network path.' -ForegroundColor Yellow
    Write-Host 'Do NOT manually start/restart Chat Agent Platform.' -ForegroundColor Yellow
    Write-Host 'Then run this qualification again with -Phase Verify from the same exact tested source.' -ForegroundColor Yellow
    exit 0
}

$RunDir = Resolve-VerifyRunDir
if (-not (Test-Path -LiteralPath $RunDir -PathType Container)) {
    throw "Prepared reboot qualification directory is missing: $RunDir"
}

$verifyStartedAt = (Get-Date).ToUniversalTime()
$prepareFile = Join-Path $RunDir 'prepare.json'
if (-not (Test-Path -LiteralPath $prepareFile -PathType Leaf)) {
    throw "Prepared reboot qualification receipt is missing: $prepareFile"
}
$prepare = Get-Content -LiteralPath $prepareFile -Raw | ConvertFrom-Json

Write-Host '===== TRANSPORT SUPERVISOR: PHYSICAL REBOOT / LOGON QUALIFICATION — VERIFY =====' -ForegroundColor Cyan
Write-Host 'VERIFY is observational: it does not start or restart Chat Agent Platform.' -ForegroundColor Yellow

try {
    $repoHead = (git -C $RepoRoot rev-parse HEAD).Trim()
    if ([string]$prepare.repo_head -ne $repoHead) {
        throw "Qualification source HEAD changed across reboot: prepared=$($prepare.repo_head) verify=$repoHead"
    }
    $scriptHash = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
    if ([string]$prepare.qualification_script_sha256 -ne $scriptHash) {
        throw 'Qualification script changed across reboot.'
    }

    $bootBefore = [datetime]::Parse([string]$prepare.boot_time_before).ToUniversalTime()
    $preparedAt = [datetime]::Parse([string]$prepare.prepared_at).ToUniversalTime()
    $bootAfter = Get-BootTimeUtc
    if ($bootAfter -le $bootBefore.AddSeconds(1)) {
        throw "A new Windows boot was not proven. boot_before=$($bootBefore.ToString('o')) boot_after=$($bootAfter.ToString('o'))"
    }
    if ($bootAfter -le $preparedAt) {
        throw 'Windows boot time is not later than the qualification prepare timestamp.'
    }

    Save-JsonEvidence -Directory $RunDir -Name 'boot-after-reboot' -Value ([ordered]@{
        boot_time_before = $bootBefore.ToString('o')
        boot_time_after = $bootAfter.ToString('o')
        verify_started_at = $verifyStartedAt.ToString('o')
        reboot_verified = $true
    })

    if (-not (Test-Path -LiteralPath $OwnerFile -PathType Leaf)) {
        throw 'Desired running owner state disappeared across Windows reboot.'
    }
    $ownerAfter = Get-Content -LiteralPath $OwnerFile -Raw | ConvertFrom-Json
    Save-JsonEvidence -Directory $RunDir -Name 'owner-after-logon' -Value $ownerAfter
    if ([string]$ownerAfter.controller_path -ne [string]$prepare.owner_controller_path) {
        throw 'Manager controller ownership changed across reboot/logon.'
    }
    if ([string]$ownerAfter.started_at -ne [string]$prepare.owner_started_at) {
        throw 'Manager owner receipt was recreated instead of surviving reboot.'
    }

    $taskAfter = Get-TaskEvidence
    Assert-TaskContract -Evidence $taskAfter
    Save-JsonEvidence -Directory $RunDir -Name 'task-after-logon' -Value $taskAfter
    if ([string]::IsNullOrWhiteSpace([string]$taskAfter.last_run_time)) {
        throw 'Supervisor Scheduled Task has no post-logon LastRunTime.'
    }
    $taskLastRun = [datetime]::Parse([string]$taskAfter.last_run_time).ToUniversalTime()
    if ($taskLastRun -lt $bootAfter.AddSeconds(-2)) {
        throw 'Supervisor Scheduled Task LastRunTime predates the verified reboot.'
    }
    if ($taskLastRun -gt $verifyStartedAt.AddMinutes(1)) {
        throw 'Supervisor Scheduled Task LastRunTime is inconsistent with the post-logon verification window.'
    }

    $supervisorsAtVerifyStart = @(Get-ExactSupervisorProcesses)
    if ($supervisorsAtVerifyStart.Count -ne 1) {
        throw "Expected exactly one supervisor already running after logon before VERIFY mutations; found $($supervisorsAtVerifyStart.Count)."
    }
    $supervisorProcess = $supervisorsAtVerifyStart[0]
    $supervisorCreation = Get-ProcessCreationUtc -Process $supervisorProcess
    if ($null -eq $supervisorCreation) {
        throw 'Could not resolve post-logon supervisor process creation time.'
    }
    if ($supervisorCreation -lt $bootAfter.AddSeconds(-2)) {
        throw 'Post-logon supervisor process creation time predates the verified reboot.'
    }
    if ($supervisorCreation -gt $verifyStartedAt.AddSeconds(5)) {
        throw 'Supervisor was not already running when post-logon VERIFY began.'
    }

    $samples = @()
    $ready = $null
    $readyTunnel = $null
    $readySupervisor = $null
    $readyRecovery = $null
    $deadline = (Get-Date).AddSeconds($ReadyTimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $status = Invoke-ManagerStatus
            $supervisors = @(Get-ExactSupervisorProcesses)
            $tunnels = @(Get-DirectTunnelProcesses)
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
                supervisor_process_count = $supervisors.Count
                supervisor_pid = if ($supervisors.Count -eq 1) { [int]$supervisors[0].ProcessId } else { $null }
                tunnel_process_count = $tunnels.Count
                tunnel_pid = if ($tunnels.Count -eq 1) { [int]$tunnels[0].ProcessId } else { $null }
                supervisor_state = if ($null -ne $s) { [string]$s.supervisor_state } else { $null }
                recovery_total = if ($null -ne $r) { [int]$r.total_recoveries } else { $null }
                consecutive_attempts = if ($null -ne $r) { [int]$r.consecutive_attempts } else { $null }
            }
            $samples += $sample

            if (
                [bool]$status.runtime_ready -and
                [bool]$status.openai_ready -and
                $supervisors.Count -eq 1 -and
                [int]$supervisors[0].ProcessId -eq [int]$supervisorProcess.ProcessId -and
                $tunnels.Count -eq 1 -and
                $null -ne $s -and
                $null -ne $r -and
                [string]$s.supervisor_state -eq 'healthy' -and
                [string]$s.health_code -eq 'READY' -and
                [string]$s.recovery_action -eq 'none' -and
                [int]$r.consecutive_attempts -eq 0
            ) {
                $ready = $status
                $readyTunnel = $tunnels[0]
                $readySupervisor = $s
                $readyRecovery = $r
                break
            }
        }
        catch {}
        Start-Sleep -Seconds 1
    }
    $samples | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $RunDir 'post-logon-samples.json') -Encoding utf8

    if ($null -eq $ready -or $null -eq $readyTunnel -or $null -eq $readySupervisor -or $null -eq $readyRecovery) {
        $lastSample = if ($samples.Count -gt 0) { $samples[-1] } else { $null }
        if ($null -ne $lastSample) {
            throw "Healthy state did not return automatically within $ReadyTimeoutSeconds seconds after logon. Last sample: runtime_ready=$($lastSample.runtime_ready), openai_ready=$($lastSample.openai_ready), health_code=$($lastSample.health_code), recovery_action=$($lastSample.recovery_action), supervisor_pid=$($lastSample.supervisor_pid), tunnel_pid=$($lastSample.tunnel_pid), recovery_total=$($lastSample.recovery_total)."
        }
        throw "Healthy state did not return automatically within $ReadyTimeoutSeconds seconds after logon and no sample was captured."
    }

    $tunnelCreation = Get-ProcessCreationUtc -Process $readyTunnel
    if ($null -eq $tunnelCreation) {
        throw 'Could not resolve post-reboot tunnel process creation time.'
    }
    if ($tunnelCreation -lt $bootAfter.AddSeconds(-2)) {
        throw 'Post-reboot tunnel process creation time predates the verified reboot.'
    }

    $recoveryBefore = [int]$prepare.recovery_total_before
    $recoveryAfter = [int]$readyRecovery.total_recoveries
    $recoveryDelta = $recoveryAfter - $recoveryBefore
    if ($recoveryDelta -lt 0 -or $recoveryDelta -gt 1) {
        throw "Reboot/logon caused unexpected recovery-count delta $recoveryDelta; expected 0 or 1."
    }

    $heartbeatAt = [string]$readySupervisor.observed_at
    $heartbeatAdvanced = $false
    $heartbeatDeadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $heartbeatDeadline) {
        Start-Sleep -Seconds 1
        $heartbeat = Read-SupervisorState
        $currentSupervisors = @(Get-ExactSupervisorProcesses)
        if (
            $null -ne $heartbeat -and
            $currentSupervisors.Count -eq 1 -and
            [int]$currentSupervisors[0].ProcessId -eq [int]$supervisorProcess.ProcessId -and
            [int]$heartbeat.supervisor_pid -eq [int]$supervisorProcess.ProcessId -and
            [string]$heartbeat.observed_at -ne $heartbeatAt
        ) {
            $heartbeatAdvanced = $true
            $readySupervisor = $heartbeat
            break
        }
    }
    if (-not $heartbeatAdvanced) {
        throw 'Supervisor heartbeat did not advance after reboot/logon recovery.'
    }

    Save-JsonEvidence -Directory $RunDir -Name 'manager-after-logon' -Value $ready
    Save-JsonEvidence -Directory $RunDir -Name 'supervisor-after-logon' -Value $readySupervisor
    Save-JsonEvidence -Directory $RunDir -Name 'recovery-after-logon' -Value $readyRecovery

    $summary = [ordered]@{
        schema_version = 1
        result = 'PASSED'
        repo_head = $repoHead
        run_dir = $RunDir
        prepared_at = $preparedAt.ToString('o')
        verify_started_at = $verifyStartedAt.ToString('o')
        boot_time_before = $bootBefore.ToString('o')
        boot_time_after = $bootAfter.ToString('o')
        reboot_verified = $true
        desired_state_before = [string]$prepare.desired_state_before
        desired_state_after = if (Test-Path -LiteralPath $OwnerFile -PathType Leaf) { 'running' } else { 'stopped' }
        owner_receipt_survived = $true
        task_logon_trigger_verified = $true
        task_last_run_after_boot = $true
        supervisor_pid_before = [int]$prepare.supervisor_pid_before
        supervisor_pid_after = [int]$supervisorProcess.ProcessId
        supervisor_created_after_boot = $true
        tunnel_pid_before = [int]$prepare.tunnel_pid_before
        tunnel_pid_after = [int]$readyTunnel.ProcessId
        tunnel_created_after_boot = $true
        recovery_total_before = $recoveryBefore
        recovery_total_after = $recoveryAfter
        recovery_count_delta = $recoveryDelta
        runtime_ready_after_logon = [bool]$ready.runtime_ready
        openai_ready_after_logon = [bool]$ready.openai_ready
        supervisor_heartbeat_verified = $heartbeatAdvanced
        completed_at = (Get-Date).ToUniversalTime().ToString('o')
    }
    Save-JsonEvidence -Directory $RunDir -Name 'summary' -Value $summary
    Remove-Item -LiteralPath $PendingFile -Force -ErrorAction SilentlyContinue

    Write-Result 'TRANSPORT_SUPERVISOR_REBOOT_LOGON_QUALIFICATION_RESULT' 'PASSED'
    Write-Result 'EXACT_TESTED_HEAD' $repoHead
    Write-Result 'REBOOT_VERIFIED' $summary['reboot_verified']
    Write-Result 'BOOT_TIME_BEFORE' $summary['boot_time_before']
    Write-Result 'BOOT_TIME_AFTER' $summary['boot_time_after']
    Write-Result 'DESIRED_STATE_AFTER' $summary['desired_state_after']
    Write-Result 'TASK_LOGON_TRIGGER_VERIFIED' $summary['task_logon_trigger_verified']
    Write-Result 'TASK_LAST_RUN_AFTER_BOOT' $summary['task_last_run_after_boot']
    Write-Result 'SUPERVISOR_CREATED_AFTER_BOOT' $summary['supervisor_created_after_boot']
    Write-Result 'TUNNEL_CREATED_AFTER_BOOT' $summary['tunnel_created_after_boot']
    Write-Result 'RECOVERY_COUNT_DELTA' $summary['recovery_count_delta']
    Write-Result 'RUNTIME_READY_AFTER_LOGON' $summary['runtime_ready_after_logon']
    Write-Result 'OPENAI_READY_AFTER_LOGON' $summary['openai_ready_after_logon']
    Write-Result 'SUPERVISOR_HEARTBEAT_VERIFIED' $summary['supervisor_heartbeat_verified']
    Write-Result 'RESULT_DIR' $RunDir
}
catch {
    $failure = $_
    try {
        Save-JsonEvidence -Directory $RunDir -Name 'failure' -Value ([ordered]@{
            schema_version = 1
            result = 'FAILED'
            repo_head = if ($null -ne $prepare.PSObject.Properties['repo_head']) { [string]$prepare.repo_head } else { $null }
            error_type = $failure.Exception.GetType().Name
            error_message = $failure.Exception.Message
            failed_at = (Get-Date).ToUniversalTime().ToString('o')
        })
        if (Test-Path -LiteralPath $SupervisorStateFile -PathType Leaf) {
            Copy-Item -LiteralPath $SupervisorStateFile -Destination (Join-Path $RunDir 'supervisor-failure.json') -Force
        }
        if (Test-Path -LiteralPath $RecoveryStateFile -PathType Leaf) {
            Copy-Item -LiteralPath $RecoveryStateFile -Destination (Join-Path $RunDir 'recovery-failure.json') -Force
        }
        if (Test-Path -LiteralPath $SupervisorLogFile -PathType Leaf) {
            Get-Content -LiteralPath $SupervisorLogFile -Tail 250 |
                Set-Content -LiteralPath (Join-Path $RunDir 'supervisor-log-tail.txt') -Encoding utf8
        }
        try {
            $taskFailure = Get-TaskEvidence
            Save-JsonEvidence -Directory $RunDir -Name 'task-failure' -Value $taskFailure
        }
        catch {}
    }
    catch {}
    throw $failure
}
