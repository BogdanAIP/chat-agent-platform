[CmdletBinding()]
param(
    [ValidateSet("Install", "Start", "Stop", "Toggle", "Status", "SetProfile")]
    [string]$Action = "Status",

    [ValidateSet("reference", "files-readonly", "browser-isolated", "semantic", "adaptive")]
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
$TunnelHealthUrlFile = Join-Path $StateDir "tunnel-health.url"

$TunnelExe = Join-Path $BinDir "tunnel-client.exe"
$TunnelProfile = Join-Path $TunnelDir "local-1mcp.yaml"

$TunnelStdout = Join-Path $LogDir "tunnel-stdout.log"
$TunnelStderr = Join-Path $LogDir "tunnel-stderr.log"
$ControllerLog = Join-Path $LogDir "controller.log"

$StartLocalBridgeScript = Join-Path $RepoRoot "scripts\start-local-bridge.ps1"
$StartChatScript = Join-Path $RepoRoot "scripts\start-chat-profile.ps1"
$StartSemanticScript = Join-Path $RepoRoot "scripts\start-semantic-profile.ps1"
$StopChatScript = Join-Path $RepoRoot "scripts\stop-chat-profile.ps1"
$StatusChatScript = Join-Path $RepoRoot "scripts\status-chat-profile.ps1"
$SemanticRuntimeHelper = Join-Path $RepoRoot "scripts\semantic-projection-runtime.ps1"


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

    $settings = (
        Get-Content `
            -LiteralPath $SettingsFile `
            -Raw |
        ConvertFrom-Json
    )

    $supportedProfiles = @(
        "reference",
        "files-readonly",
        "browser-isolated",
        "semantic",
        "adaptive"
    )
    if (
        $null -eq $settings.PSObject.Properties["profile"] -or
        $supportedProfiles -notcontains [string]$settings.profile
    ) {
        throw "Settings contain an unsupported profile."
    }

    $filesRoot = if ($null -ne $settings.PSObject.Properties["files_root"]) {
        $settings.files_root
    }
    else {
        $null
    }
    $tunnelProfile = if ($null -ne $settings.PSObject.Properties["tunnel_profile"]) {
        [string]$settings.tunnel_profile
    }
    else {
        "local-1mcp"
    }

    return [pscustomobject]@{
        profile = [string]$settings.profile
        files_root = $filesRoot
        tunnel_profile = $tunnelProfile
    }
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
    $pwsh = (
        Get-Command `
            "pwsh.exe" `
            -ErrorAction Stop
    ).Source

    $output = @(
        & $pwsh `
            -NoLogo `
            -NoProfile `
            -File $StatusChatScript `
            2>&1
    )

    if ($LASTEXITCODE -ne 0) {
        throw (
            "Chat profile status failed with exit code {0}: {1}" -f `
            $LASTEXITCODE,
            (($output | Out-String).Trim())
        )
    }

    try {
        return (
            $output |
                Out-String |
                ConvertFrom-Json `
                    -ErrorAction Stop
        )
    }
    catch {
        throw (
            "Chat profile status returned invalid JSON: {0}" -f `
            (($output | Out-String).Trim())
        )
    }
}


function Test-ChatProfileReady {
    param(
        [Parameter(Mandatory)]
        $Status,

        [Parameter(Mandatory)]
        [ValidateSet("reference", "files-readonly", "browser-isolated", "semantic", "adaptive")]
        [string]$ProfileName
    )

    if (
        $null -eq $Status -or
        $Status.active_count -ne 1 -or
        [string]$Status.active_profile -ne $ProfileName
    ) {
        return $false
    }

    $matchingScopes = @(
        $Status.scopes |
            Where-Object {
                [string]$_.profile -eq $ProfileName
            }
    )

    return (
        $matchingScopes.Count -eq 1 -and
        [bool]$matchingScopes[0].running -and
        [string]$matchingScopes[0].health_state -eq "ready"
    )
}


function Get-TunnelProcesses {
    if (-not (Test-Path $TunnelExe)) {
        return @()
    }

    $expectedExe = [System.IO.Path]::GetFullPath($TunnelExe)
    $escapedTunnelDir = [regex]::Escape($TunnelDir)
    $profilePattern = `
        '(?i)(?:^|\s)--profile\s+local-1mcp(?=\s|$)'
    $profileDirPattern = `
        ('(?i)(?:^|\s)--profile-dir\s+"{0}"(?=\s|$)' -f `
            $escapedTunnelDir)

    return @(
        Get-CimInstance Win32_Process `
            -ErrorAction SilentlyContinue |
        Where-Object {
            if ($_.Name -ne "tunnel-client.exe") {
                return $false
            }

            $actualExe = [string]$_.ExecutablePath
            $commandLine = [string]$_.CommandLine

            if (
                [string]::IsNullOrWhiteSpace($actualExe) -or
                [string]::IsNullOrWhiteSpace($commandLine)
            ) {
                return $false
            }

            try {
                $actualExe = [System.IO.Path]::GetFullPath($actualExe)
            }
            catch {
                return $false
            }

            return (
                $actualExe -ieq $expectedExe -and
                $commandLine -match $profilePattern -and
                $commandLine -match $profileDirPattern
            )
        }
    )
}


function Test-TunnelRunning {
    return (@(Get-TunnelProcesses).Count -gt 0)
}


function Get-TunnelHealthBaseUrl {
    if (-not (Test-Path $TunnelHealthUrlFile)) {
        return $null
    }

    try {
        $url = (
            Get-Content `
                -LiteralPath $TunnelHealthUrlFile `
                -Raw `
                -ErrorAction Stop
        ).Trim().TrimEnd("/")

        if ($url -notmatch '^https?://127\.0\.0\.1(?::\d+)?$') {
            return $null
        }

        return $url
    }
    catch {
        return $null
    }
}


function Test-TunnelReady {
    if (-not (Test-TunnelRunning)) {
        return $false
    }

    $baseUrl = Get-TunnelHealthBaseUrl

    if ([string]::IsNullOrWhiteSpace($baseUrl)) {
        return $false
    }

    try {
        $response = Invoke-WebRequest `
            -Uri "$baseUrl/readyz" `
            -Method Get `
            -TimeoutSec 2 `
            -ErrorAction Stop

        return ($response.StatusCode -eq 200)
    }
    catch {
        return $false
    }
}


function Wait-TunnelReady {
    param(
        [ValidateRange(1, 120)]
        [int]$TimeoutSeconds = 45
    )

    for ($attempt = 1; $attempt -le $TimeoutSeconds; $attempt++) {
        if (Test-TunnelReady) {
            return $true
        }

        if (-not (Test-TunnelRunning)) {
            return $false
        }

        Start-Sleep -Seconds 1
    }

    return $false
}


function Get-TunnelErrorTail {
    if (-not (Test-Path $TunnelStderr)) {
        return ""
    }

    try {
        return (
            Get-Content `
                -LiteralPath $TunnelStderr `
                -Tail 20 `
                -ErrorAction Stop |
            Out-String
        ).Trim()
    }
    catch {
        return ""
    }
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
            [Array]::Clear($plainBytes, 0, $plainBytes.Length)
        }

        if ($protectedBytes) {
            [Array]::Clear($protectedBytes, 0, $protectedBytes.Length)
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
            [Array]::Clear($plainBytes, 0, $plainBytes.Length)
        }
    }
    finally {
        [Array]::Clear($protectedBytes, 0, $protectedBytes.Length)
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
    $shortcutPath = Join-Path $desktop "Chat Agent Platform.lnk"

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
            elseif (Test-TunnelRunning) {
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

    if (-not (Test-Path -LiteralPath $SemanticRuntimeHelper -PathType Leaf)) {
        throw "Semantic projection runtime helper is missing: $SemanticRuntimeHelper"
    }

    . $SemanticRuntimeHelper
    $semanticEntry = Get-SemanticProjectionEntryPath `
        -RepoRoot $RepoRoot `
        -EnsureDependencies

    if (-not (Test-Path -LiteralPath $semanticEntry -PathType Leaf)) {
        throw "Semantic projection entrypoint preparation failed: $semanticEntry"
    }

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
    Write-Host "SEMANTIC_RUNTIME_READY=True"
    Write-Host "SEMANTIC_ENTRY=$semanticEntry"
    Write-Host "SECRET_STORED_WITH_DPAPI=True"
    Write-Host "DESKTOP_SHORTCUT=$shortcut"
    Write-Host "DEFAULT_PROFILE=$((Get-Settings).profile)"

    Show-PlatformNotification `
        -Title "Chat Agent Platform" `
        -Message "Установка и локальная конфигурация готовы."
}


function Start-ChatProfile {
    $settings = Get-Settings
    $desiredProfile = [string]$settings.profile

    if (-not [string]::IsNullOrWhiteSpace($Profile)) {
        $desiredProfile = $Profile
    }

    $existing = Get-ChatProfileStatus

    if (
        Test-ChatProfileReady `
            -Status $existing `
            -ProfileName $desiredProfile
    ) {
        Write-ControllerLog `
            "Chat profile already active and ready: $desiredProfile"

        return $existing
    }

    if (
        $existing.active_count -gt 0
    ) {
        Write-ControllerLog `
            -Level "WARN" `
            -Message (
                "Chat profile state is active but not ready for {0}; " +
                "restarting profile runtime."
            ) -f $desiredProfile
    }

    Write-ControllerLog `
        "Starting Chat profile: $desiredProfile"

    if ($desiredProfile -eq "reference") {
        $stopOutput = @(& $StopChatScript 2>&1)
        foreach ($line in $stopOutput) {
            Write-ControllerLog "profile-stop: $line"
        }

        $output = @(
            & $StartLocalBridgeScript 2>&1
        )
    }
    elseif ($desiredProfile -eq "semantic") {
        $root = $FilesRoot

        if ([string]::IsNullOrWhiteSpace($root)) {
            $root = [string]$settings.files_root
        }

        if ([string]::IsNullOrWhiteSpace($root)) {
            throw @"
semantic requires a configured FilesRoot.
Use:
.\scripts\chat-platform-controller.ps1 -Action SetProfile -Profile semantic -FilesRoot "C:\path"
"@
        }

        $output = @(
            & $StartSemanticScript `
                -FilesRoot $root `
                2>&1
        )
    }
    elseif ($desiredProfile -in @("files-readonly", "adaptive")) {
        $root = $FilesRoot

        if ([string]::IsNullOrWhiteSpace($root)) {
            $root = [string]$settings.files_root
        }

        if ([string]::IsNullOrWhiteSpace($root)) {
            throw @"
$desiredProfile requires a configured FilesRoot.
Use:
.\scripts\chat-platform-controller.ps1 -Action SetProfile -Profile $desiredProfile -FilesRoot "C:\path"
"@
        }

        $output = @(
            & $StartChatScript `
                -Profile $desiredProfile `
                -FilesRoot $root `
                2>&1
        )
    }
    elseif ($desiredProfile -eq "browser-isolated") {
        $output = @(
            & $StartChatScript `
                -Profile browser-isolated `
                2>&1
        )
    }
    else {
        throw "Unsupported Chat profile in settings: $desiredProfile"
    }

    foreach ($line in $output) {
        Write-ControllerLog "profile: $line"
    }

    Start-Sleep -Seconds 1
    $status = Get-ChatProfileStatus

    if (
        -not (
            Test-ChatProfileReady `
                -Status $status `
                -ProfileName $desiredProfile
        )
    ) {
        throw (
            "Chat profile did not become ready: {0}" -f `
            $desiredProfile
        )
    }

    return $status
}


function Start-Tunnel {
    if (Test-TunnelRunning) {
        if (Test-TunnelReady) {
            Write-ControllerLog "Tunnel already running and ready."
            return
        }

        Write-ControllerLog `
            -Level "WARN" `
            -Message "Tunnel is running but not ready; restarting it."

        Stop-Tunnel
    }

    if (-not (Test-Path $TunnelExe)) {
        throw "Installed tunnel-client missing: $TunnelExe"
    }

    if (-not (Test-Path $TunnelProfile)) {
        throw "Installed tunnel profile missing: $TunnelProfile"
    }

    Remove-Item `
        $TunnelStdout, $TunnelStderr, $TunnelHealthUrlFile `
        -Force `
        -ErrorAction SilentlyContinue

    $apiKey = Get-DecryptedApiKey
    $process = $null

    try {
        $env:CONTROL_PLANE_API_KEY = $apiKey

        $arguments = (
            'run --profile local-1mcp --profile-dir "{0}" ' +
            '--health.listen-addr 127.0.0.1:0 ' +
            '--health.url-file "{1}"'
        ) -f $TunnelDir, $TunnelHealthUrlFile

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

    Write-ControllerLog `
        "Tunnel process started. PID=$($process.Id)"

    if (-not (Wait-TunnelReady -TimeoutSeconds 45)) {
        $tail = Get-TunnelErrorTail
        Stop-Tunnel

        if ([string]::IsNullOrWhiteSpace($tail)) {
            throw "Tunnel did not become ready within 45 seconds."
        }

        throw "Tunnel did not become ready within 45 seconds. $tail"
    }

    Write-ControllerLog `
        "Tunnel ready. PID=$($process.Id)"
}


function Stop-Tunnel {
    $processes = @(Get-TunnelProcesses)

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

    Remove-Item `
        -LiteralPath $TunnelHealthUrlFile `
        -Force `
        -ErrorAction SilentlyContinue
}


function Stop-ChatProfile {
    $output = @(& $StopChatScript 2>&1)

    foreach ($line in $output) {
        Write-ControllerLog "profile-stop: $line"
    }
}


function Start-Platform {
    Initialize-LocalDirectories

    try {
        $status = Start-ChatProfile
        $expectedProfile = [string]$status.active_profile

        Start-Tunnel

        if (-not (Test-TunnelReady)) {
            throw "Tunnel readiness was lost before platform startup completed."
        }

        $finalStatus = Get-ChatProfileStatus

        if (
            -not (
                Test-ChatProfileReady `
                    -Status $finalStatus `
                    -ProfileName $expectedProfile
            )
        ) {
            throw "MCP readiness was lost before platform startup completed."
        }

        $status = $finalStatus
    }
    catch {
        $startupError = $_

        try {
            Stop-Tunnel
        }
        catch {
            Write-ControllerLog `
                -Level "WARN" `
                -Message (
                    "Tunnel rollback failed: {0}" -f `
                    $_.Exception.Message
                )
        }

        try {
            Stop-ChatProfile
        }
        catch {
            Write-ControllerLog `
                -Level "WARN" `
                -Message (
                    "Chat profile rollback failed: {0}" -f `
                    $_.Exception.Message
                )
        }

        throw $startupError
    }

    $active = [string]$status.active_profile

    Write-ControllerLog `
        "Platform started. ActiveProfile=$active"

    Write-Host "CHAT_PLATFORM_STATUS=running"
    Write-Host "ACTIVE_PROFILE=$active"
    Write-Host "MCP_READY=True"
    Write-Host "TUNNEL_RUNNING=True"
    Write-Host "TUNNEL_READY=True"

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
    $mcpReady = $false

    if (
        $chat.active_count -eq 1 -and
        -not [string]::IsNullOrWhiteSpace(
            [string]$chat.active_profile
        )
    ) {
        $mcpReady = Test-ChatProfileReady `
            -Status $chat `
            -ProfileName ([string]$chat.active_profile)
    }

    $tunnelRunning = Test-TunnelRunning
    $tunnelReady = $false

    if ($tunnelRunning) {
        $tunnelReady = Test-TunnelReady
    }

    return [pscustomobject]@{
        tunnel_running = $tunnelRunning
        tunnel_ready = $tunnelReady
        mcp_ready = $mcpReady
        active_profile = $chat.active_profile
        active_count = $chat.active_count
        conflict = [bool]$chat.conflict
        local_root = $LocalRoot
        settings = Get-Settings
    }
}


function Set-PlatformProfile {
    if ([string]::IsNullOrWhiteSpace($Profile)) {
        throw "-Profile is required for SetProfile."
    }

    $state = Get-ChatProfileStatus

    if ($state.active_count -gt 0) {
        throw "Stop the platform before changing its default profile."
    }

    $settings = Get-Settings
    $settings.profile = $Profile

    if ($Profile -in @("files-readonly", "semantic", "adaptive")) {
        if ([string]::IsNullOrWhiteSpace($FilesRoot)) {
            throw "-FilesRoot is required for $Profile."
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

    if ($Profile -in @("files-readonly", "semantic", "adaptive")) {
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
                $state.mcp_ready -and
                $state.tunnel_ready -and
                $state.active_count -eq 1
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
