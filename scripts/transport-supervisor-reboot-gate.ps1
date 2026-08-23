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
    throw 'Transport Supervisor reboot/logon gate supports Windows only.'
}
if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    throw 'LOCALAPPDATA is unavailable.'
}

$Core = Join-Path $PSScriptRoot 'transport-supervisor-reboot-qualification.ps1'
$Installer = Join-Path $PSScriptRoot 'install-chat-platform-supervisor.ps1'
$LocalRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
$Manager = Join-Path $LocalRoot 'app\scripts\chat-platform.ps1'
$OwnerFile = Join-Path $LocalRoot 'state\manager-owner.json'

foreach ($required in @($Core, $Installer, $Manager)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required reboot qualification asset is missing: $required"
    }
}

function Invoke-ManagerMutation {
    param([ValidateSet('Start', 'Stop')] [string]$Action)

    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pwsh
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
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
        $timeoutMilliseconds = if ($Action -eq 'Start') { 150000 } else { 60000 }
        if (-not $process.WaitForExit($timeoutMilliseconds)) {
            try { $process.Kill($true) } catch {}
            try { $process.WaitForExit(5000) | Out-Null } catch {}
            throw "Manager $Action timed out."
        }
        $process.WaitForExit()
        if ([int]$process.ExitCode -ne 0) {
            throw "Manager $Action failed with exit code $($process.ExitCode)."
        }
    }
    finally {
        $process.Dispose()
    }
}

function Invoke-CoreProcess {
    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pwsh
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $false

    foreach ($argument in @(
        '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', $Core,
        '-Phase', $Phase,
        '-ReadyTimeoutSeconds', [string]$ReadyTimeoutSeconds
    )) {
        $startInfo.ArgumentList.Add([string]$argument)
    }
    if (-not [string]::IsNullOrWhiteSpace($RunDir)) {
        $startInfo.ArgumentList.Add('-RunDir')
        $startInfo.ArgumentList.Add([string]$RunDir)
    }
    if (-not [string]::IsNullOrWhiteSpace($OutputRoot)) {
        $startInfo.ArgumentList.Add('-OutputRoot')
        $startInfo.ArgumentList.Add([string]$OutputRoot)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) {
            throw 'Reboot qualification core could not be started.'
        }

        $timeoutMilliseconds = [int](($ReadyTimeoutSeconds + 180) * 1000)
        if (-not $process.WaitForExit($timeoutMilliseconds)) {
            try { $process.Kill($true) } catch {}
            try { $process.WaitForExit(5000) | Out-Null } catch {}
            throw "Reboot qualification core timed out after $([int]($ReadyTimeoutSeconds + 180)) seconds."
        }
        $process.WaitForExit()

        if ([int]$process.ExitCode -ne 0) {
            throw "Reboot qualification core failed with exit code $($process.ExitCode)."
        }
    }
    finally {
        $process.Dispose()
    }
}

if ($Phase -eq 'Verify') {
    Write-Host 'REBOOT_GATE_MODE=verify-observational'
    Invoke-CoreProcess
    exit 0
}

$desiredStateBefore = if (Test-Path -LiteralPath $OwnerFile -PathType Leaf) { 'running' } else { 'stopped' }
$preparePassed = $false

try {
    Write-Host 'REBOOT_GATE_MODE=prepare-bootstrap'
    Write-Host 'Installing the qualification transport health surface before baseline evaluation.' -ForegroundColor Yellow
    & $Installer -NoStart

    Invoke-CoreProcess
    $preparePassed = $true
    Write-Host 'REBOOT_GATE_PREPARE_RESULT=PASSED' -ForegroundColor Green
}
catch {
    $failure = $_
    Write-Host 'REBOOT_GATE_PREPARE_ROLLBACK=True' -ForegroundColor Yellow
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
    Write-Host 'REBOOT_GATE_PREPARE_RESULT=FAILED' -ForegroundColor Red
    throw $failure
}