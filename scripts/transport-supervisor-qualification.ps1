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
$HealthUrlFile = Join-Path $LocalRoot 'state\semantic-direct-health.url'
$SupervisorStateFile = Join-Path $LocalRoot 'state\supervisor.json'
$RecoveryStateFile = Join-Path $LocalRoot 'state\supervisor-recovery.json'
$TunnelExe = Join-Path $LocalRoot 'bin\tunnel-client.exe'

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $LocalRoot 'transport-supervisor-qualification'
}
$RunDir = Join-Path $OutputRoot ('run-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Write-Result {
    param([Parameter(Mandatory)] [string]$Name, [Parameter(Mandatory)] $Value)
    Write-Host "$Name=$Value"
}

function Invoke-ManagerStatus {
    $output = @(
        & pwsh.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $Manager -Action Status -NoNotify 2>&1
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Manager status failed: $($output -join ' ')"
    }
    return ($output | Out-String | ConvertFrom-Json -ErrorAction Stop)
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

function Save-JsonEvidence {
    param([Parameter(Mandatory)] [string]$Name, [Parameter(Mandatory)] $Value)
    $Value | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $RunDir "$Name.json") -Encoding utf8
}

Write-Host '===== TRANSPORT SUPERVISOR: INSTALL QUALIFICATION BUILD =====' -ForegroundColor Cyan
& $Installer
if ($LASTEXITCODE -ne 0) {
    throw "Supervisor installer failed with exit code $LASTEXITCODE."
}

if (-not (Test-Path -LiteralPath $Manager -PathType Leaf)) {
    throw "Installed manager is missing: $Manager"
}

$baseline = Invoke-ManagerStatus
Save-JsonEvidence -Name 'manager-before-start' -Value $baseline

if ([string]$baseline.settings.profile -notin @('semantic', 'semantic-direct')) {
    throw "Physical supervisor qualification requires the configured semantic/direct profile. Current profile=$($baseline.settings.profile)"
}

if (-not [bool]$baseline.runtime_ready) {
    Write-Host 'Starting configured semantic runtime...' -ForegroundColor Yellow
    & pwsh.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $Manager -Action Start -NoNotify
    if ($LASTEXITCODE -ne 0) {
        throw "Manager Start failed with exit code $LASTEXITCODE."
    }
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

$supervisors = @(Get-ExactSupervisorProcesses)
if ($supervisors.Count -ne 1) {
    throw "Expected exactly one supervisor process; found $($supervisors.Count)."
}

$tunnelProcesses = @(Get-DirectTunnelProcesses)
if ($tunnelProcesses.Count -ne 1) {
    throw "Expected exactly one direct tunnel process; found $($tunnelProcesses.Count)."
}
$oldTunnelPid = [int]$tunnelProcesses[0].ProcessId
$oldSupervisorPid = [int]$supervisors[0].ProcessId

Write-Host "Injecting owned tunnel-client process failure PID=$oldTunnelPid" -ForegroundColor Yellow
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
if (Test-Path -LiteralPath $SupervisorStateFile -PathType Leaf) {
    Copy-Item -LiteralPath $SupervisorStateFile -Destination (Join-Path $RunDir 'supervisor-after-recovery.json') -Force
}
if (Test-Path -LiteralPath $RecoveryStateFile -PathType Leaf) {
    Copy-Item -LiteralPath $RecoveryStateFile -Destination (Join-Path $RunDir 'recovery-after-recovery.json') -Force
}

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

$summary = [ordered]@{
    schema_version = 1
    result = 'PASSED'
    repo_head = (git -C $RepoRoot rev-parse HEAD).Trim()
    run_dir = $RunDir
    old_supervisor_pid = $oldSupervisorPid
    old_tunnel_pid = $oldTunnelPid
    new_tunnel_pid = $newTunnelPid
    tunnel_pid_changed = ($newTunnelPid -ne $oldTunnelPid)
    supervisor_pid_stable = (@(Get-ExactSupervisorProcesses).Count -eq 1 -and [int]@(Get-ExactSupervisorProcesses)[0].ProcessId -eq $oldSupervisorPid)
    runtime_ready_after_recovery = [bool]$recovered.runtime_ready
    health_code_after_recovery = [string]$recovered.health_code
    openai_control_ready_after_recovery = [bool]$recovered.openai_ready
    completed_at = (Get-Date).ToUniversalTime().ToString('o')
}
Save-JsonEvidence -Name 'summary' -Value $summary

Write-Result 'TRANSPORT_SUPERVISOR_QUALIFICATION_RESULT' 'PASSED'
Write-Result 'OLD_TUNNEL_PID' $oldTunnelPid
Write-Result 'NEW_TUNNEL_PID' $newTunnelPid
Write-Result 'TUNNEL_PID_CHANGED' $summary.tunnel_pid_changed
Write-Result 'SUPERVISOR_PID_STABLE' $summary.supervisor_pid_stable
Write-Result 'RUNTIME_READY_AFTER_RECOVERY' $summary.runtime_ready_after_recovery
Write-Result 'HEALTH_CODE_AFTER_RECOVERY' $summary.health_code_after_recovery
Write-Result 'OPENAI_CONTROL_READY_AFTER_RECOVERY' $summary.openai_control_ready_after_recovery
Write-Result 'RESULT_DIR' $RunDir
