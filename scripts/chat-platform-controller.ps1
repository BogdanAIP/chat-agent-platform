[CmdletBinding()]
param(
    [ValidateSet("Install", "Start", "Stop", "Toggle", "Status", "SetProfile")]
    [string]$Action = "Status",

    [ValidateSet("reference", "files-readonly", "browser-isolated")]
    [string]$Profile,

    [string]$FilesRoot,

    [switch]$NoNotify
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot

$LocalRoot = Join-Path $env:LOCALAPPDATA "ChatAgentPlatform"
$BinDir = Join-Path $LocalRoot "bin"
$TunnelDir = Join-Path $LocalRoot "tunnel"
$SecretDir = Join-Path $LocalRoot "secrets"
$StateDir = Join-Path $LocalRoot "state"
$LogDir = Join-Path $LocalRoot "logs"

$SettingsFile = Join-Path $StateDir "settings.json"
$SecretFile = Join-Path $SecretDir "control-plane-api-key.dpapi"

$TunnelExe = Join-Path $BinDir "tunnel-client.exe"
$TunnelProfile = Join-Path $TunnelDir "local-1mcp.yaml"

$TunnelStdout = Join-Path $LogDir "tunnel-stdout.log"
$TunnelStderr = Join-Path $LogDir "tunnel-stderr.log"
$ControllerLog = Join-Path $LogDir "controller.log"

$StartChatScript = Join-Path $RepoRoot "scripts\start-chat-profile.ps1"
$StopChatScript = Join-Path $RepoRoot "scripts\stop-chat-profile.ps1"
$StatusChatScript = Join-Path $RepoRoot "scripts\status-chat-profile.ps1"


function Initialize-LocalDirectories {
    foreach ($path in @(
        $LocalRoot,
        $BinDir,
        $TunnelDir,
        $SecretDir,
        $StateDir,
        $LogDir
    )) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
    }
}


function Write-ControllerLog {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )

    Initialize-LocalDirectories

    $line = "{0} [{1}] {2}" -f `
        (Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffK"),
        $Level,
        $Message

    Add-Content `
        -LiteralPath $ControllerLog `
        -Value $line `
        -Encoding utf8
}


function Show-PlatformNotification {
    param(
        [string]$Title,
        [string]$Message,
        [ValidateSet("Info", "Warning", "Error")]
        [string]$Kind = "Info"
    )

    if ($NoNotify) {
        return
    }

    try {
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing

        $notify = New-Object System.Windows.Forms.NotifyIcon
        $notify.Icon = [System.Drawing.SystemIcons]::Application
        $notify.Visible = $true
        $notify.BalloonTipTitle = $Title
        $notify.BalloonTipText = $Message

        switch ($Kind) {
            "Warning" {
                $notify.BalloonTipIcon = `
                    [System.Windows.Forms.ToolTipIcon]::Warning
            }
            "Error" {
                $notify.BalloonTipIcon = `
                    [System.Windows.Forms.ToolTipIcon]::Error
            }
            default {
                $notify.BalloonTipIcon = `
                    [System.Windows.Forms.ToolTipIcon]::Info
            }
        }

        $notify.ShowBalloonTip(3500)
        Start-Sleep -Milliseconds 3800
        $notify.Dispose()
    }
    catch {
        Write-ControllerLog `
            -Level "WARN" `
            -Message "Notification failed: $($_.Exception.Message)"
    }
}


function Get-Settings {
    Initialize-LocalDirectories

    if (-not (Test-Path $SettingsFile)) {
        return [pscustomobject]@{
            profile = "reference"
            files_root = $null
            tunnel_profile = "local-1mcp"
        }
    }

    return (
        Get-Content `
            -LiteralPath $SettingsFile `
            -Raw |
        ConvertFrom-Json
    )
}


function Save-Settings {
    param(
        [Parameter(Mandatory)]
        $Settings
    )

    Initialize-LocalDirectories

    $Settings |
        ConvertTo-Json -Depth 5 |
        Set-Content `
            -LiteralPath $SettingsFile `
            -Encoding utf8
}


function Get-ChatProfileStatus {
    $profiles = @(
        "reference",
        "files-readonly",
        "browser-isolated"
    )

    $runningProfiles = @()

    foreach ($name in $profiles) {
        $runtimeRoot = Join-Path `
            $RepoRoot `
            "runtime\chat-profiles"

        $profileDir = Join-Path `
            $runtimeRoot `
            $name

        $pidFile = Join-Path `
            $profileDir `
            "server.pid"

        if (-not (Test-Path $pidFile)) {
            continue
        }

        try {
            $state = (
                Get-Content `
                    -LiteralPath $pidFile `
                    -Raw `
                    -ErrorAction Stop |
                ConvertFrom-Json `
                    -ErrorAction Stop
            )
        }
        catch {
            continue
        }

        [int]$pidValue = 0

        if (
            $null -eq $state.pid -or
            -not [int]::TryParse(
                [string]$state.pid,
                [ref]$pidValue
            )
        ) {
            continue
        }

        try {
            $process = Get-Process `
                -Id $pidValue `
                -ErrorAction Stop

            if (-not $process.HasExited) {
                $runningProfiles += $name
            }
        }
        catch {
            continue
        }
    }

    $runningProfiles = @($runningProfiles)

    $activeProfile = $null

    if ($runningProfiles.Count -eq 1) {
        $activeProfile = $runningProfiles[0]
    }

    return [pscustomobject]@{
        active_count = $runningProfiles.Count
        active_profile = $activeProfile
    }
}
function Get-TunnelProcesses {
    return @(
        Get-CimInstance Win32_Process `
            -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -eq "tunnel-client.exe" -and
            $_.CommandLine -match '--profile\s+local-1mcp'
        }
    )
}


function Test-TunnelRunning {
    $processes = @(
        Get-TunnelProcesses
    )

    return ($processes.Count -gt 0)
}
function Protect-ApiKey {
    Initialize-LocalDirectories

    $secure = Read-Host `
        "Вставь CONTROL_PLANE_API_KEY — ввод скрыт" `
        -AsSecureString

    if ($secure.Length -eq 0) {
        throw "API key is empty."
    }

    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)

    $plain = $null
    $plainBytes = $null
    $protectedBytes = $null

    try {
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)

        $plainBytes = [Text.Encoding]::UTF8.GetBytes($plain)

        $protectedBytes = `
            [Security.Cryptography.ProtectedData]::Protect(
                $plainBytes,
                $null,
                [Security.Cryptography.DataProtectionScope]::CurrentUser
            )

        [Convert]::ToBase64String($protectedBytes) |
            Set-Content `
                -LiteralPath $SecretFile `
                -Encoding ascii
    }
    finally {
        if ($plainBytes) {
            [Array]::Clear(
                $plainBytes,
                0,
                $plainBytes.Length
            )
        }

        if ($protectedBytes) {
            [Array]::Clear(
                $protectedBytes,
                0,
                $protectedBytes.Length
            )
        }

        $plain = $null

        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}


function Get-DecryptedApiKey {
    if (-not (Test-Path $SecretFile)) {
        throw @"
Tunnel API key is not configured.
Run:
.\scripts\chat-platform-controller.ps1 -Action Install
"@
    }

    $encoded = (
        Get-Content `
            -LiteralPath $SecretFile `
            -Raw
    ).Trim()

    $protectedBytes = [Convert]::FromBase64String($encoded)

    try {
        $plainBytes = `
            [Security.Cryptography.ProtectedData]::Unprotect(
                $protectedBytes,
                $null,
                [Security.Cryptography.DataProtectionScope]::CurrentUser
            )

        try {
            return [Text.Encoding]::UTF8.GetString($plainBytes)
        }
        finally {
            [Array]::Clear(
                $plainBytes,
                0,
                $plainBytes.Length
            )
        }
    }
    finally {
        [Array]::Clear(
            $protectedBytes,
            0,
            $protectedBytes.Length
        )
    }
}


function Protect-RepositoryLocalConfig {
    $gitDir = Join-Path $RepoRoot ".git"

    if (-not (Test-Path $gitDir)) {
        return
    }

    $excludeFile = Join-Path $gitDir "info\exclude"
    $rule = "config/openai-tunnel-client/"

    $existing = @()

    if (Test-Path $excludeFile) {
        $existing = @(Get-Content $excludeFile)
    }

    if ($existing -notcontains $rule) {
        Add-Content `
            -LiteralPath $excludeFile `
            -Value $rule `
            -Encoding utf8
    }
}


function Install-DesktopShortcut {
    $desktop = [Environment]::GetFolderPath("Desktop")

    $shortcutPath = Join-Path `
        $desktop `
        "Chat Agent Platform.lnk"

    $pwsh = (
        Get-Command `
            "pwsh.exe" `
            -ErrorAction Stop
    ).Source

    $trayScript = Join-Path `
        $RepoRoot `
        "scripts\chat-platform-tray.ps1"

    if (-not (Test-Path $trayScript)) {
        throw "Tray controller not found: $trayScript"
    }

    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)

    $shortcut.TargetPath = $pwsh

    $shortcut.Arguments = (
        '-NoLogo -NoProfile -ExecutionPolicy Bypass ' +
        '-WindowStyle Hidden ' +
        '-File "{0}"' -f $trayScript
    )

    $shortcut.WorkingDirectory = $RepoRoot

    $shortcut.IconLocation = (
        "{0}\System32\shell32.dll,44" -f $env:SystemRoot
    )

    $shortcut.Description = `
        "Chat Agent Platform — индикатор и ВКЛ/ВЫКЛ"

    $shortcut.Save()

    return $shortcutPath
}
function Install-Platform {
    Initialize-LocalDirectories
    Protect-RepositoryLocalConfig

    $repoTunnelExe = Join-Path `
        $RepoRoot `
        "runtime\openai-tunnel-client\tunnel-client.exe"

    $repoTunnelProfile = Join-Path `
        $RepoRoot `
        "config\openai-tunnel-client\local-1mcp.yaml"

    #
    # tunnel-client binary
    #
    # Installation must remain safe while the tunnel is running.
    # Windows locks the active executable, so never overwrite an
    # identical binary and defer replacement when a different version
    # is currently in use.
    #

    $binarySource = "local-existing"

    if (Test-Path $repoTunnelExe) {

        if (Test-Path $TunnelExe) {

            $repoBinaryHash = (
                Get-FileHash `
                    -LiteralPath $repoTunnelExe `
                    -Algorithm SHA256
            ).Hash

            $localBinaryHash = (
                Get-FileHash `
                    -LiteralPath $TunnelExe `
                    -Algorithm SHA256
            ).Hash

            if ($repoBinaryHash -eq $localBinaryHash) {
                $binarySource = "local-existing-identical"
            }
            else {
                $runningTunnel = @(
                    Get-TunnelProcesses
                )

                if ($runningTunnel.Count -gt 0) {
                    $binarySource = "local-running-update-deferred"

                    Write-ControllerLog `
                        -Level "WARN" `
                        -Message (
                            "A newer/different tunnel-client binary exists " +
                            "in the repository, but the installed binary is " +
                            "currently running. Update deferred until stopped."
                        )
                }
                else {
                    Copy-Item `
                        -LiteralPath $repoTunnelExe `
                        -Destination $TunnelExe `
                        -Force

                    $installedHash = (
                        Get-FileHash `
                            -LiteralPath $TunnelExe `
                            -Algorithm SHA256
                    ).Hash

                    if ($repoBinaryHash -ne $installedHash) {
                        throw "Tunnel binary copy verification failed."
                    }

                    $binarySource = "repository-updated"
                }
            }
        }
        else {
            Copy-Item `
                -LiteralPath $repoTunnelExe `
                -Destination $TunnelExe `
                -Force

            $repoBinaryHash = (
                Get-FileHash `
                    -LiteralPath $repoTunnelExe `
                    -Algorithm SHA256
            ).Hash

            $installedHash = (
                Get-FileHash `
                    -LiteralPath $TunnelExe `
                    -Algorithm SHA256
            ).Hash

            if ($repoBinaryHash -ne $installedHash) {
                throw "Tunnel binary installation verification failed."
            }

            $binarySource = "repository-installed"
        }
    }
    elseif (-not (Test-Path $TunnelExe)) {
        throw @"
tunnel-client.exe is unavailable both in the repository
and in the persistent local installation:

$TunnelExe
"@
    }

    #
    # Tunnel profile
    #
    # %LOCALAPPDATA% is authoritative after first migration.
    # Never overwrite an existing working profile from Git.
    #

    $profileSource = "local-existing"

    if (-not (Test-Path $TunnelProfile)) {

        if (-not (Test-Path $repoTunnelProfile)) {
            throw @"
Tunnel profile is not configured.

Persistent location:
$TunnelProfile

Repository-local profile may be used only for first migration:
$repoTunnelProfile
"@
        }

        Copy-Item `
            -LiteralPath $repoTunnelProfile `
            -Destination $TunnelProfile `
            -Force

        $sourceHash = (
            Get-FileHash `
                -LiteralPath $repoTunnelProfile `
                -Algorithm SHA256
        ).Hash

        $destHash = (
            Get-FileHash `
                -LiteralPath $TunnelProfile `
                -Algorithm SHA256
        ).Hash

        if ($sourceHash -ne $destHash) {
            throw "Tunnel profile migration verification failed."
        }

        $profileSource = "migrated-from-repository"
    }

    #
    # Persistent user settings / secret
    #

    if (-not (Test-Path $SettingsFile)) {
        Save-Settings ([pscustomobject]@{
            profile = "reference"
            files_root = $null
            tunnel_profile = "local-1mcp"
        })
    }

    if (-not (Test-Path $SecretFile)) {
        Protect-ApiKey
    }

    #
    # Desktop entry always points to the tray controller.
    #

    $shortcut = Install-DesktopShortcut

    Write-ControllerLog `
        "Platform installation completed. Shortcut=$shortcut"

    Write-Host ""
    Write-Host "CHAT_PLATFORM_INSTALL=OK" -ForegroundColor Green
    Write-Host "LOCAL_ROOT=$LocalRoot"
    Write-Host "TUNNEL_PROFILE=$TunnelProfile"
    Write-Host "TUNNEL_PROFILE_SOURCE=$profileSource"
    Write-Host "TUNNEL_BINARY=$TunnelExe"
    Write-Host "TUNNEL_BINARY_SOURCE=$binarySource"
    Write-Host "SECRET_STORED_WITH_DPAPI=True"
    Write-Host "DESKTOP_SHORTCUT=$shortcut"
    Write-Host "DEFAULT_PROFILE=$((Get-Settings).profile)"

    Show-PlatformNotification `
        -Title "Chat Agent Platform" `
        -Message "Установка и локальная конфигурация готовы."
}
function Start-ChatProfile {
    $settings = Get-Settings

    $desiredProfile = $settings.profile

    if (-not [string]::IsNullOrWhiteSpace($Profile)) {
        $desiredProfile = $Profile
    }

    Write-ControllerLog `
        "Starting Chat profile: $desiredProfile"

    if ($desiredProfile -eq "files-readonly") {
        $root = $FilesRoot

        if ([string]::IsNullOrWhiteSpace($root)) {
            $root = $settings.files_root
        }

        if ([string]::IsNullOrWhiteSpace($root)) {
            throw @"
files-readonly requires a configured FilesRoot.
Use:
.\scripts\chat-platform-controller.ps1 -Action SetProfile -Profile files-readonly -FilesRoot "C:\path"
"@
        }

        $output = @(
            & $StartChatScript `
                -Profile files-readonly `
                -FilesRoot $root `
                2>&1
        )
    }
    else {
        $output = @(
            & $StartChatScript `
                -Profile $desiredProfile `
                2>&1
        )
    }

    foreach ($line in $output) {
        Write-ControllerLog "profile: $line"
    }

    Start-Sleep -Seconds 1

    $status = Get-ChatProfileStatus

    if (
        $null -eq $status -or
        $status.active_count -lt 1
    ) {
        throw "Chat profile did not become active."
    }

    return $status
}


function Start-Tunnel {
    if (Test-TunnelRunning) {
        Write-ControllerLog "Tunnel already running."
        return
    }

    if (-not (Test-Path $TunnelExe)) {
        throw "Installed tunnel-client missing: $TunnelExe"
    }

    if (-not (Test-Path $TunnelProfile)) {
        throw "Installed tunnel profile missing: $TunnelProfile"
    }

    $apiKey = Get-DecryptedApiKey

    try {
        $env:CONTROL_PLANE_API_KEY = $apiKey

        Remove-Item `
            $TunnelStdout, $TunnelStderr `
            -Force `
            -ErrorAction SilentlyContinue

        $arguments = (
            'run --profile local-1mcp --profile-dir "{0}"' -f `
            $TunnelDir
        )

        $process = Start-Process `
            -FilePath $TunnelExe `
            -ArgumentList $arguments `
            -WindowStyle Hidden `
            -RedirectStandardOutput $TunnelStdout `
            -RedirectStandardError $TunnelStderr `
            -PassThru
    }
    finally {
        Remove-Item `
            Env:CONTROL_PLANE_API_KEY `
            -ErrorAction SilentlyContinue

        $apiKey = $null
    }

    Start-Sleep -Seconds 4

    if ($process.HasExited) {
        $tail = ""

        if (Test-Path $TunnelStderr) {
            $tail = (
                Get-Content `
                    -LiteralPath $TunnelStderr `
                    -Tail 20 |
                Out-String
            ).Trim()
        }

        throw "Tunnel exited with code $($process.ExitCode). $tail"
    }

    Write-ControllerLog `
        "Tunnel started. PID=$($process.Id)"
}


function Stop-Tunnel {
    $processes = Get-TunnelProcesses

    foreach ($process in $processes) {
        try {
            Stop-Process `
                -Id $process.ProcessId `
                -Force `
                -ErrorAction Stop

            Write-ControllerLog `
                "Tunnel stopped. PID=$($process.ProcessId)"
        }
        catch {
            Write-ControllerLog `
                -Level "WARN" `
                -Message (
                    "Could not stop tunnel PID={0}: {1}" -f `
                    $process.ProcessId,
                    $_.Exception.Message
                )
        }
    }
}


function Stop-ChatProfile {
    $status = Get-ChatProfileStatus

    if (
        $null -eq $status -or
        $status.active_count -eq 0
    ) {
        Write-ControllerLog "No active Chat profile."
        return
    }

    $active = [string]$status.active_profile

    $command = Get-Command $StopChatScript

    if (
        $command.Parameters.ContainsKey("Profile") -and
        -not [string]::IsNullOrWhiteSpace($active)
    ) {
        $output = @(
            & $StopChatScript `
                -Profile $active `
                2>&1
        )
    }
    else {
        $output = @(
            & $StopChatScript 2>&1
        )
    }

    foreach ($line in $output) {
        Write-ControllerLog "profile-stop: $line"
    }
}


function Start-Platform {
    Initialize-LocalDirectories

    $status = Start-ChatProfile
    Start-Tunnel

    $active = [string]$status.active_profile

    Write-ControllerLog `
        "Platform started. ActiveProfile=$active"

    Write-Host "CHAT_PLATFORM_STATUS=running"
    Write-Host "ACTIVE_PROFILE=$active"
    Write-Host "TUNNEL_RUNNING=True"

    Show-PlatformNotification `
        -Title "Chat Agent Platform — ВКЛ" `
        -Message "Профиль: $active"
}


function Stop-Platform {
    Stop-Tunnel
    Stop-ChatProfile

    Write-ControllerLog "Platform stopped."

    Write-Host "CHAT_PLATFORM_STATUS=stopped"

    Show-PlatformNotification `
        -Title "Chat Agent Platform — ВЫКЛ" `
        -Message "Локальный MCP и Secure MCP Tunnel остановлены."
}


function Get-PlatformStatus {
    $chat = Get-ChatProfileStatus
    $tunnel = Test-TunnelRunning

    $active = $null
    $activeCount = 0

    if ($null -ne $chat) {
        $active = $chat.active_profile
        $activeCount = $chat.active_count
    }

    return [pscustomobject]@{
        tunnel_running = $tunnel
        active_profile = $active
        active_count = $activeCount
        local_root = $LocalRoot
        settings = Get-Settings
    }
}


function Set-PlatformProfile {
    if ([string]::IsNullOrWhiteSpace($Profile)) {
        throw "-Profile is required for SetProfile."
    }

    $settings = Get-Settings

    $settings.profile = $Profile

    if ($Profile -eq "files-readonly") {
        if ([string]::IsNullOrWhiteSpace($FilesRoot)) {
            throw "-FilesRoot is required for files-readonly."
        }

        $resolved = (
            Resolve-Path `
                -LiteralPath $FilesRoot
        ).Path

        $settings.files_root = $resolved
    }

    Save-Settings $settings

    Write-ControllerLog `
        "Default profile changed to $Profile"

    Write-Host "DEFAULT_PROFILE=$Profile"

    if ($Profile -eq "files-readonly") {
        Write-Host "FILES_ROOT=$($settings.files_root)"
    }
}


try {
    switch ($Action) {
        "Install" {
            Install-Platform
        }

        "Start" {
            Start-Platform
        }

        "Stop" {
            Stop-Platform
        }

        "Toggle" {
            $state = Get-PlatformStatus

            if (
                $state.tunnel_running -or
                $state.active_count -gt 0
            ) {
                Stop-Platform
            }
            else {
                Start-Platform
            }
        }

        "Status" {
            $state = Get-PlatformStatus
            $state | ConvertTo-Json -Depth 6

            $mode = if (
                $state.tunnel_running -and
                $state.active_count -gt 0
            ) {
                "Работает"
            }
            elseif (
                $state.tunnel_running -or
                $state.active_count -gt 0
            ) {
                "Частично запущено"
            }
            else {
                "Выключено"
            }

            Show-PlatformNotification `
                -Title "Chat Agent Platform" `
                -Message $mode
        }

        "SetProfile" {
            Set-PlatformProfile
        }
    }
}
catch {
    Write-ControllerLog `
        -Level "ERROR" `
        -Message $_.Exception.ToString()

    Show-PlatformNotification `
        -Title "Chat Agent Platform — ошибка" `
        -Message $_.Exception.Message `
        -Kind Error

    Write-Error $_
    exit 1
}
