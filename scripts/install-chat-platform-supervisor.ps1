[CmdletBinding()]
param(
    [switch]$Uninstall,
    [switch]$NoStart
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $IsWindows) {
    throw 'Transport Supervisor installer currently supports Windows only.'
}
if ($PSVersionTable.PSEdition -ne 'Core' -or $PSVersionTable.PSVersion.Major -lt 7) {
    throw 'PowerShell 7 or newer is required.'
}
if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    throw 'LOCALAPPDATA is unavailable.'
}
if ([string]::IsNullOrWhiteSpace($env:WINDIR)) {
    throw 'WINDIR is unavailable.'
}

$TaskName = 'Chat Agent Platform Transport Supervisor'
$TrayTaskName = 'Chat Agent Platform Status Indicator'
$ManagerMutexName = 'Local\ChatAgentPlatformControllerOperation'
$ManagerMutexTimeoutMilliseconds = 30000

$LocalRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
$AppScriptsDir = Join-Path $LocalRoot 'app\scripts'
$StateDir = Join-Path $LocalRoot 'state'
$BackupDir = Join-Path $StateDir 'transport-supervisor-backup'
$InstalledManager = Join-Path $AppScriptsDir 'chat-platform.ps1'
$InstalledDirectController = Join-Path $AppScriptsDir 'semantic-direct-controller.ps1'
$InstalledSupervisor = Join-Path $AppScriptsDir 'chat-platform-supervisor.ps1'
$InstalledSupervisorLauncher = Join-Path $AppScriptsDir 'chat-platform-supervisor-launcher.vbs'
$InstalledHealthHelper = Join-Path $AppScriptsDir 'tunnel-reliability-health.ps1'
$InstalledTray = Join-Path $AppScriptsDir 'chat-platform-tray.ps1'
$DirectControllerBackup = Join-Path $BackupDir 'semantic-direct-controller.ps1'

$SourceDirectController = Join-Path $PSScriptRoot 'semantic-direct-controller.ps1'
$SourceSupervisor = Join-Path $PSScriptRoot 'chat-platform-supervisor.ps1'
$SourceSupervisorLauncher = Join-Path $PSScriptRoot 'chat-platform-supervisor-launcher.vbs'
$SourceHealthHelper = Join-Path $PSScriptRoot 'tunnel-reliability-health.ps1'

function Get-PwshPath {
    return (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
}

function Get-WscriptPath {
    $path = Join-Path $env:WINDIR 'System32\wscript.exe'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "wscript.exe is unavailable: $path"
    }
    return [System.IO.Path]::GetFullPath($path)
}

function Stop-ExactSupervisorProcess {
    if (-not (Test-Path -LiteralPath $InstalledSupervisor -PathType Leaf)) {
        return
    }

    $scriptPattern = [regex]::Escape([System.IO.Path]::GetFullPath($InstalledSupervisor))
    foreach ($process in @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Name -eq 'pwsh.exe' -and
                -not [string]::IsNullOrWhiteSpace([string]$_.CommandLine) -and
                [string]$_.CommandLine -match $scriptPattern -and
                [string]$_.CommandLine -match '(?i)(?:^|\s)-Action\s+Run(?:\s|$)'
            }
    )) {
        Stop-Process -Id ([int]$process.ProcessId) -Force -ErrorAction SilentlyContinue
    }
}

function Stop-SupervisorTaskIfPresent {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -ne $task) {
        try { Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue } catch {}
    }
    Stop-ExactSupervisorProcess
}

function Stop-ExactTrayProcess {
    if (-not (Test-Path -LiteralPath $InstalledTray -PathType Leaf)) {
        return
    }

    $scriptPattern = [regex]::Escape([System.IO.Path]::GetFullPath($InstalledTray))
    foreach ($process in @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Name -eq 'pwsh.exe' -and
                -not [string]::IsNullOrWhiteSpace([string]$_.CommandLine) -and
                [string]$_.CommandLine -match $scriptPattern
            }
    )) {
        Stop-Process -Id ([int]$process.ProcessId) -Force -ErrorAction SilentlyContinue
    }
}

function Stop-TrayTaskIfPresent {
    $task = Get-ScheduledTask -TaskName $TrayTaskName -ErrorAction SilentlyContinue
    if ($null -ne $task) {
        try { Stop-ScheduledTask -TaskName $TrayTaskName -ErrorAction SilentlyContinue } catch {}
    }
    Stop-ExactTrayProcess
}

function Copy-VerifiedFile {
    param(
        [Parameter(Mandatory)] [string]$Source,
        [Parameter(Mandatory)] [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw "Supervisor source asset is missing: $Source"
    }

    $parent = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $temporary = "$Destination.new-$PID"

    try {
        Copy-Item -LiteralPath $Source -Destination $temporary -Force
        $sourceHash = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
        $copyHash = (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash
        if ($sourceHash -ne $copyHash) {
            throw "Supervisor asset copy verification failed: $Source"
        }
        Move-Item -LiteralPath $temporary -Destination $Destination -Force
    }
    finally {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
    }
}

function Assert-PowerShellParses {
    param([Parameter(Mandatory)] [string]$Path)

    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $Path,
        [ref]$tokens,
        [ref]$errors
    ) | Out-Null
    if ($errors.Count -ne 0) {
        throw "$Path has PowerShell syntax errors: $($errors -join '; ')"
    }
}

function Invoke-WithManagerMutex {
    param([Parameter(Mandatory)] [scriptblock]$Body)

    $mutex = New-Object System.Threading.Mutex($false, $ManagerMutexName)
    $acquired = $false
    try {
        try {
            $acquired = $mutex.WaitOne($ManagerMutexTimeoutMilliseconds)
        }
        catch [System.Threading.AbandonedMutexException] {
            $acquired = $true
        }
        if (-not $acquired) {
            throw 'Another Chat Agent Platform lifecycle operation is still running.'
        }
        & $Body
    }
    finally {
        if ($acquired) {
            try { $mutex.ReleaseMutex() } catch {}
        }
        $mutex.Dispose()
    }
}

function Backup-InstalledDirectControllerIfNeeded {
    if (-not (Test-Path -LiteralPath $InstalledDirectController -PathType Leaf)) {
        return
    }
    if (Test-Path -LiteralPath $DirectControllerBackup -PathType Leaf) {
        return
    }

    $installedHash = (Get-FileHash -LiteralPath $InstalledDirectController -Algorithm SHA256).Hash
    $sourceHash = (Get-FileHash -LiteralPath $SourceDirectController -Algorithm SHA256).Hash
    if ($installedHash -eq $sourceHash) {
        return
    }

    New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
    Copy-VerifiedFile -Source $InstalledDirectController -Destination $DirectControllerBackup
    Write-Host "TRANSPORT_SUPERVISOR_CONTROLLER_BACKUP=$DirectControllerBackup"
}

function Restore-DirectControllerBackupIfPresent {
    if (-not (Test-Path -LiteralPath $DirectControllerBackup -PathType Leaf)) {
        return $false
    }

    Copy-VerifiedFile -Source $DirectControllerBackup -Destination $InstalledDirectController
    Remove-Item -LiteralPath $DirectControllerBackup -Force
    if (Test-Path -LiteralPath $BackupDir -PathType Container) {
        $remaining = @(Get-ChildItem -LiteralPath $BackupDir -Force -ErrorAction SilentlyContinue)
        if ($remaining.Count -eq 0) {
            Remove-Item -LiteralPath $BackupDir -Force -ErrorAction SilentlyContinue
        }
    }
    return $true
}

function Install-SupervisorAssets {
    if (-not (Test-Path -LiteralPath $InstalledManager -PathType Leaf)) {
        throw "Installed Chat Agent Platform manager is missing: $InstalledManager. Run bootstrap first."
    }
    if (-not (Test-Path -LiteralPath $InstalledTray -PathType Leaf)) {
        throw "Installed Chat Agent Platform tray is missing: $InstalledTray. Run bootstrap first."
    }

    foreach ($source in @($SourceDirectController, $SourceSupervisor, $SourceHealthHelper)) {
        Assert-PowerShellParses -Path $source
    }
    Assert-PowerShellParses -Path $InstalledTray
    if (-not (Test-Path -LiteralPath $SourceSupervisorLauncher -PathType Leaf)) {
        throw "Supervisor launcher source asset is missing: $SourceSupervisorLauncher"
    }

    Invoke-WithManagerMutex {
        Backup-InstalledDirectControllerIfNeeded
        Copy-VerifiedFile -Source $SourceDirectController -Destination $InstalledDirectController
        Copy-VerifiedFile -Source $SourceSupervisor -Destination $InstalledSupervisor
        Copy-VerifiedFile -Source $SourceSupervisorLauncher -Destination $InstalledSupervisorLauncher
        Copy-VerifiedFile -Source $SourceHealthHelper -Destination $InstalledHealthHelper
    }

    foreach ($pair in @(
        @($SourceDirectController, $InstalledDirectController),
        @($SourceSupervisor, $InstalledSupervisor),
        @($SourceSupervisorLauncher, $InstalledSupervisorLauncher),
        @($SourceHealthHelper, $InstalledHealthHelper)
    )) {
        $sourceHash = (Get-FileHash -LiteralPath $pair[0] -Algorithm SHA256).Hash
        $installedHash = (Get-FileHash -LiteralPath $pair[1] -Algorithm SHA256).Hash
        if ($sourceHash -ne $installedHash) {
            throw "Installed supervisor asset hash mismatch: $($pair[1])"
        }
    }
}

function Get-InteractiveTaskPrincipal {
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    if ([string]::IsNullOrWhiteSpace($identity)) {
        throw 'Could not resolve the current Windows user identity.'
    }

    return New-ScheduledTaskPrincipal `
        -UserId $identity `
        -LogonType Interactive `
        -RunLevel Limited
}

function Get-LongRunningTaskSettings {
    return New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -ExecutionTimeLimit ([TimeSpan]::Zero)
}

function Register-SupervisorTask {
    $pwsh = Get-PwshPath
    $wscript = Get-WscriptPath
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    if ([string]::IsNullOrWhiteSpace($identity)) {
        throw 'Could not resolve the current Windows user identity.'
    }

    $arguments = @(
        '//B',
        '//Nologo',
        ('"{0}"' -f $InstalledSupervisorLauncher),
        ('"{0}"' -f $pwsh),
        ('"{0}"' -f $InstalledSupervisor)
    ) -join ' '

    $action = New-ScheduledTaskAction -Execute $wscript -Argument $arguments
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity
    $principal = Get-InteractiveTaskPrincipal
    $settings = Get-LongRunningTaskSettings

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description 'Keeps the Chat Agent Platform Secure MCP transport healthy in the current user context.' `
        -Force | Out-Null

    $registered = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    if ([string]$registered.TaskName -ne $TaskName) {
        throw 'Supervisor Scheduled Task registration verification failed.'
    }
}

function Register-TrayTask {
    $pwsh = Get-PwshPath
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    if ([string]::IsNullOrWhiteSpace($identity)) {
        throw 'Could not resolve the current Windows user identity.'
    }

    $arguments = @(
        '-NoLogo',
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-WindowStyle', 'Hidden',
        '-File', ('"{0}"' -f $InstalledTray),
        '-NoConsoleHost'
    ) -join ' '

    $action = New-ScheduledTaskAction -Execute $pwsh -Argument $arguments
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity
    $principal = Get-InteractiveTaskPrincipal
    $settings = Get-LongRunningTaskSettings

    Register-ScheduledTask `
        -TaskName $TrayTaskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description 'Shows the current Chat Agent Platform route, readiness and qualification state.' `
        -Force | Out-Null

    $registered = Get-ScheduledTask -TaskName $TrayTaskName -ErrorAction Stop
    if ([string]$registered.TaskName -ne $TrayTaskName) {
        throw 'Status Indicator Scheduled Task registration verification failed.'
    }
}

function Uninstall-Supervisor {
    Stop-SupervisorTaskIfPresent
    Stop-TrayTaskIfPresent

    if ($null -ne (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue)) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    if ($null -ne (Get-ScheduledTask -TaskName $TrayTaskName -ErrorAction SilentlyContinue)) {
        Unregister-ScheduledTask -TaskName $TrayTaskName -Confirm:$false
    }

    $restored = [bool](Invoke-WithManagerMutex {
        $didRestore = Restore-DirectControllerBackupIfPresent
        Remove-Item -LiteralPath $InstalledSupervisor -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $InstalledSupervisorLauncher -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $InstalledHealthHelper -Force -ErrorAction SilentlyContinue
        return $didRestore
    })

    Write-Host 'TRANSPORT_SUPERVISOR_INSTALL=removed'
    Write-Host 'CHAT_PLATFORM_STATUS_INDICATOR=removed'
    Write-Host "TRANSPORT_SUPERVISOR_CONTROLLER_RESTORED=$restored"
}

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

if ($Uninstall) {
    Uninstall-Supervisor
    exit 0
}

Stop-SupervisorTaskIfPresent
Stop-TrayTaskIfPresent
Install-SupervisorAssets
Register-SupervisorTask
Register-TrayTask

if (-not $NoStart) {
    Start-ScheduledTask -TaskName $TaskName
    Start-ScheduledTask -TaskName $TrayTaskName
    Start-Sleep -Milliseconds 500
}

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
$trayTask = Get-ScheduledTask -TaskName $TrayTaskName -ErrorAction Stop
Write-Host 'TRANSPORT_SUPERVISOR_INSTALL=ok'
Write-Host "TRANSPORT_SUPERVISOR_TASK=$($task.TaskName)"
Write-Host "TRANSPORT_SUPERVISOR_STATE=$($task.State)"
Write-Host "TRANSPORT_SUPERVISOR_SCRIPT=$InstalledSupervisor"
Write-Host "TRANSPORT_SUPERVISOR_LAUNCHER=$InstalledSupervisorLauncher"
Write-Host "TRANSPORT_SUPERVISOR_DIRECT_CONTROLLER=$InstalledDirectController"
Write-Host 'CHAT_PLATFORM_STATUS_INDICATOR=installed'
Write-Host "CHAT_PLATFORM_STATUS_INDICATOR_TASK=$($trayTask.TaskName)"
Write-Host "CHAT_PLATFORM_STATUS_INDICATOR_STATE=$($trayTask.State)"
Write-Host "CHAT_PLATFORM_STATUS_INDICATOR_SCRIPT=$InstalledTray"
