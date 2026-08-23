[CmdletBinding()]
param(
    [ValidateRange(15, 300)]
    [int]$IdleSampleSeconds = 60,

    [ValidateRange(30, 300)]
    [int]$RecoveryTimeoutSeconds = 120,

    [string]$OutputRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $IsWindows) {
    throw 'Transport Supervisor resource/latency qualification supports Windows only.'
}
if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    throw 'LOCALAPPDATA is unavailable.'
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$HardKillQualification = Join-Path $PSScriptRoot 'transport-supervisor-qualification.ps1'
$LocalRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
$SupervisorScript = Join-Path $LocalRoot 'app\scripts\chat-platform-supervisor.ps1'
$TunnelExe = Join-Path $LocalRoot 'bin\tunnel-client.exe'
$HealthUrlFile = Join-Path $LocalRoot 'state\semantic-direct-health.url'

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $LocalRoot 'transport-supervisor-resource-latency-qualification'
}
$RunDir = Join-Path $OutputRoot ('run-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$HardKillRoot = Join-Path $RunDir 'hard-kill'
New-Item -ItemType Directory -Force -Path $HardKillRoot | Out-Null

function Write-Result {
    param([Parameter(Mandatory)] [string]$Name, [Parameter(Mandatory)] $Value)
    Write-Host "$Name=$Value"
}

function Get-ExactSupervisorProcesses {
    if (-not (Test-Path -LiteralPath $SupervisorScript -PathType Leaf)) { return @() }
    $scriptPattern = [regex]::Escape([System.IO.Path]::GetFullPath($SupervisorScript))
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

function Get-ProcessSample {
    param([Parameter(Mandatory)] [string]$Role, [Parameter(Mandatory)] [int]$ProcessId)

    $process = Get-Process -Id $ProcessId -ErrorAction Stop
    return [pscustomobject]@{
        role = $Role
        pid = $ProcessId
        sampled_at = (Get-Date).ToUniversalTime().ToString('o')
        cpu_seconds = [double]$process.CPU
        working_set_bytes = [long]$process.WorkingSet64
        private_memory_bytes = [long]$process.PrivateMemorySize64
    }
}

function Convert-ToUtcDateTime {
    param([Parameter(Mandatory)] $Value)

    if ($Value -is [datetime]) {
        $date = [datetime]$Value
        return $(if ($date.Kind -eq [DateTimeKind]::Unspecified) { [datetime]::SpecifyKind($date, [DateTimeKind]::Utc) } else { $date.ToUniversalTime() })
    }
    return [datetime]::Parse(
        [string]$Value,
        [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::RoundtripKind
    ).ToUniversalTime()
}

if (-not (Test-Path -LiteralPath $HardKillQualification -PathType Leaf)) {
    throw "Hard-kill qualification script is missing: $HardKillQualification"
}

$supervisors = @(Get-ExactSupervisorProcesses)
$tunnels = @(Get-DirectTunnelProcesses)
if ($supervisors.Count -ne 1) {
    throw "Expected exactly one running supervisor before idle measurement; found $($supervisors.Count)."
}
if ($tunnels.Count -ne 1) {
    throw "Expected exactly one running direct tunnel before idle measurement; found $($tunnels.Count)."
}

$supervisorPid = [int]$supervisors[0].ProcessId
$tunnelPid = [int]$tunnels[0].ProcessId
$processorCount = [int][Environment]::ProcessorCount

Write-Host '===== TRANSPORT SUPERVISOR: IDLE RESOURCE SAMPLE =====' -ForegroundColor Cyan
Write-Result 'IDLE_SAMPLE_SECONDS' $IdleSampleSeconds
Write-Result 'SUPERVISOR_PID_IDLE' $supervisorPid
Write-Result 'TUNNEL_PID_IDLE' $tunnelPid

$before = @(
    Get-ProcessSample -Role 'supervisor' -ProcessId $supervisorPid
    Get-ProcessSample -Role 'tunnel-client' -ProcessId $tunnelPid
)
$before | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $RunDir 'idle-before.json') -Encoding utf8

Start-Sleep -Seconds $IdleSampleSeconds

$currentSupervisors = @(Get-ExactSupervisorProcesses)
$currentTunnels = @(Get-DirectTunnelProcesses)
if ($currentSupervisors.Count -ne 1 -or [int]$currentSupervisors[0].ProcessId -ne $supervisorPid) {
    throw 'Supervisor PID changed during the idle measurement window.'
}
if ($currentTunnels.Count -ne 1 -or [int]$currentTunnels[0].ProcessId -ne $tunnelPid) {
    throw 'Tunnel PID changed during the idle measurement window.'
}

$after = @(
    Get-ProcessSample -Role 'supervisor' -ProcessId $supervisorPid
    Get-ProcessSample -Role 'tunnel-client' -ProcessId $tunnelPid
)
$after | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $RunDir 'idle-after.json') -Encoding utf8

$rows = @()
foreach ($start in $before) {
    $finish = @($after | Where-Object { $_.role -eq $start.role -and $_.pid -eq $start.pid })[0]
    $cpuDelta = [math]::Max(0.0, ([double]$finish.cpu_seconds - [double]$start.cpu_seconds))
    $singleCorePercent = ($cpuDelta / [double]$IdleSampleSeconds) * 100.0
    $machinePercent = $singleCorePercent / [double]$processorCount
    $rows += [pscustomobject]@{
        role = $start.role
        pid = $start.pid
        cpu_seconds_delta = [math]::Round($cpuDelta, 6)
        average_cpu_single_core_percent = [math]::Round($singleCorePercent, 4)
        average_cpu_machine_percent = [math]::Round($machinePercent, 4)
        working_set_bytes_after = [long]$finish.working_set_bytes
        private_memory_bytes_after = [long]$finish.private_memory_bytes
    }
}
$rows | Export-Csv -LiteralPath (Join-Path $RunDir 'idle-resources.csv') -NoTypeInformation -Encoding utf8

Write-Host '===== TRANSPORT SUPERVISOR: RECOVERY LATENCY SAMPLE =====' -ForegroundColor Cyan
& $HardKillQualification -RecoveryTimeoutSeconds $RecoveryTimeoutSeconds -OutputRoot $HardKillRoot

$hardKillRun = Get-ChildItem -LiteralPath $HardKillRoot -Directory -Filter 'run-*' |
    Sort-Object LastWriteTimeUtc -Descending |
    Select-Object -First 1
if ($null -eq $hardKillRun) {
    throw 'Hard-kill qualification produced no run directory.'
}

$summaryPath = Join-Path $hardKillRun.FullName 'summary.json'
$recoveryPath = Join-Path $hardKillRun.FullName 'recovery-after-recovery.json'
if (-not (Test-Path -LiteralPath $summaryPath -PathType Leaf)) {
    throw 'Hard-kill qualification did not produce summary.json.'
}
if (-not (Test-Path -LiteralPath $recoveryPath -PathType Leaf)) {
    throw 'Hard-kill qualification did not produce recovery-after-recovery.json.'
}

$hardKillSummary = Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json
$recovery = Get-Content -LiteralPath $recoveryPath -Raw | ConvertFrom-Json
if ([string]$hardKillSummary.result -ne 'PASSED') {
    throw 'Hard-kill qualification did not pass.'
}
if ([string]::IsNullOrWhiteSpace([string]$recovery.last_attempt_at) -or [string]::IsNullOrWhiteSpace([string]$recovery.last_success_at)) {
    throw 'Recovery receipt does not contain attempt/success timestamps.'
}

$attemptAt = Convert-ToUtcDateTime $recovery.last_attempt_at
$successAt = Convert-ToUtcDateTime $recovery.last_success_at
$transactionLatencyMs = [math]::Round(($successAt - $attemptAt).TotalMilliseconds, 3)
if ($transactionLatencyMs -lt 0) {
    throw 'Recovery receipt success timestamp predates attempt timestamp.'
}

$summary = [ordered]@{
    schema_version = 1
    result = 'PASSED'
    repo_head = (git -C $RepoRoot rev-parse HEAD).Trim()
    run_dir = $RunDir
    idle_sample_seconds = $IdleSampleSeconds
    processor_count = $processorCount
    idle_processes = $rows
    hard_kill_run_dir = $hardKillRun.FullName
    old_tunnel_pid = [int]$hardKillSummary.old_tunnel_pid
    new_tunnel_pid = [int]$hardKillSummary.new_tunnel_pid
    supervisor_pid_stable = [bool]$hardKillSummary.supervisor_pid_stable
    recovery_transaction_attempt_at = $attemptAt.ToString('o')
    recovery_transaction_success_at = $successAt.ToString('o')
    recovery_transaction_latency_ms = $transactionLatencyMs
    completed_at = (Get-Date).ToUniversalTime().ToString('o')
}
$summary | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $RunDir 'summary.json') -Encoding utf8

Write-Result 'TRANSPORT_SUPERVISOR_RESOURCE_LATENCY_QUALIFICATION_RESULT' 'PASSED'
foreach ($row in $rows) {
    $prefix = ([string]$row.role).ToUpperInvariant().Replace('-', '_')
    Write-Result "${prefix}_AVG_CPU_MACHINE_PERCENT" $row.average_cpu_machine_percent
    Write-Result "${prefix}_WORKING_SET_BYTES" $row.working_set_bytes_after
    Write-Result "${prefix}_PRIVATE_MEMORY_BYTES" $row.private_memory_bytes_after
}
Write-Result 'RECOVERY_TRANSACTION_LATENCY_MS' $transactionLatencyMs
Write-Result 'OLD_TUNNEL_PID' $summary['old_tunnel_pid']
Write-Result 'NEW_TUNNEL_PID' $summary['new_tunnel_pid']
Write-Result 'SUPERVISOR_PID_STABLE' $summary['supervisor_pid_stable']
Write-Result 'RESULT_DIR' $RunDir
