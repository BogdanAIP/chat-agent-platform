[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Add-Type @"
using System;
using System.Runtime.InteropServices;

public static class ChatPlatformNativeIcon
{
    [DllImport("user32.dll")]
    public static extern bool DestroyIcon(IntPtr handle);
}
"@

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ControllerPath = Join-Path $PSScriptRoot "chat-platform-controller.ps1"

$LocalRoot = Join-Path $env:LOCALAPPDATA "ChatAgentPlatform"
$SettingsFile = Join-Path $LocalRoot "state\settings.json"
$TunnelHealthUrlFile = Join-Path $LocalRoot "state\tunnel-health.url"
$ControllerLog = Join-Path $LocalRoot "logs\controller.log"
$TunnelExe = Join-Path $LocalRoot "bin\tunnel-client.exe"
$TunnelDir = Join-Path $LocalRoot "tunnel"

$createdNew = $false

$mutex = New-Object System.Threading.Mutex(
    $true,
    "Local\ChatAgentPlatformTray",
    [ref]$createdNew
)

if (-not $createdNew) {
    exit 0
}


function New-StatusIcon {
    param(
        [Parameter(Mandatory)]
        [System.Drawing.Color]$Color
    )

    $bitmap = New-Object System.Drawing.Bitmap 32, 32
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = `
        [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias

    $graphics.Clear([System.Drawing.Color]::Transparent)

    $brush = New-Object System.Drawing.SolidBrush($Color)
    $border = New-Object System.Drawing.Pen(
        [System.Drawing.Color]::White,
        2
    )

    $graphics.FillEllipse($brush, 3, 3, 26, 26)
    $graphics.DrawEllipse($border, 3, 3, 26, 26)

    $handle = $bitmap.GetHicon()

    try {
        $temporary = [System.Drawing.Icon]::FromHandle($handle)
        $icon = $temporary.Clone()
    }
    finally {
        [ChatPlatformNativeIcon]::DestroyIcon($handle) | Out-Null
        $graphics.Dispose()
        $brush.Dispose()
        $border.Dispose()
        $bitmap.Dispose()
    }

    return $icon
}


$script:RedIcon = New-StatusIcon `
    ([System.Drawing.Color]::Crimson)
$script:YellowIcon = New-StatusIcon `
    ([System.Drawing.Color]::Goldenrod)
$script:GreenIcon = New-StatusIcon `
    ([System.Drawing.Color]::LimeGreen)


function Get-Settings {
    if (-not (Test-Path $SettingsFile)) {
        return [pscustomobject]@{
            profile = "reference"
            files_root = $null
        }
    }

    try {
        return (
            Get-Content `
                -LiteralPath $SettingsFile `
                -Raw `
                -ErrorAction Stop |
            ConvertFrom-Json `
                -ErrorAction Stop
        )
    }
    catch {
        return [pscustomobject]@{
            profile = "reference"
            files_root = $null
        }
    }
}


function Get-TunnelProcesses {
    if (-not (Test-Path $TunnelExe)) {
        return @()
    }

    $expectedExe = [System.IO.Path]::GetFullPath($TunnelExe)
    $profileDirPattern = ('(?i)--profile-dir\s+"?' + [regex]::Escape($TunnelDir))

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
                $commandLine -match '(?i)--profile\s+"?local-1mcp"?' -and
                $commandLine -match $profileDirPattern
            )
        }
    )
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


function Get-TunnelState {
    $running = (@(Get-TunnelProcesses).Count -gt 0)
    $ready = $false

    if ($running) {
        $baseUrl = Get-TunnelHealthBaseUrl

        if (-not [string]::IsNullOrWhiteSpace($baseUrl)) {
            try {
                $response = Invoke-WebRequest `
                    -Uri "$baseUrl/readyz" `
                    -Method Get `
                    -TimeoutSec 1 `
                    -ErrorAction Stop

                $ready = ($response.StatusCode -eq 200)
            }
            catch {
                $ready = $false
            }
        }
    }

    return [pscustomobject]@{
        running = $running
        ready = $ready
    }
}


function Get-ProfilePidFile {
    param(
        [Parameter(Mandatory)]
        [ValidateSet("reference", "files-readonly", "browser-isolated")]
        [string]$ProfileName
    )

    if ($ProfileName -eq "reference") {
        return (
            Join-Path `
                $RepoRoot `
                "runtime\server.pid"
        )
    }

    return (
        Join-Path `
            $RepoRoot `
            "runtime\chat-profiles\$ProfileName\server.pid"
    )
}


function Test-ProfileProcessRunning {
    param(
        [Parameter(Mandatory)]
        [string]$PidFile
    )

    if (-not (Test-Path $PidFile)) {
        return $false
    }

    try {
        $state = (
            Get-Content `
                -LiteralPath $PidFile `
                -Raw `
                -ErrorAction Stop |
            ConvertFrom-Json `
                -ErrorAction Stop
        )

        [int]$pidValue = 0

        if (
            $null -eq $state.pid -or
            -not [int]::TryParse(
                [string]$state.pid,
                [ref]$pidValue
            )
        ) {
            return $false
        }

        $process = Get-Process `
            -Id $pidValue `
            -ErrorAction Stop

        return (-not $process.HasExited)
    }
    catch {
        return $false
    }
}


function Get-McpState {
    $profiles = @(
        "reference",
        "files-readonly",
        "browser-isolated"
    )

    $runningProfiles = @()

    foreach ($name in $profiles) {
        $pidFile = Get-ProfilePidFile -ProfileName $name

        if (Test-ProfileProcessRunning -PidFile $pidFile) {
            $runningProfiles += $name
        }
    }

    $runningProfiles = @($runningProfiles)
    $settings = Get-Settings

    if ($runningProfiles.Count -ne 1) {
        $displayProfile = [string]$settings.profile

        if ($runningProfiles.Count -gt 1) {
            $displayProfile = "multiple"
        }

        return [pscustomobject]@{
            running = ($runningProfiles.Count -gt 0)
            healthy = $false
            profile = $displayProfile
            active_count = $runningProfiles.Count
        }
    }

    $profile = [string]$runningProfiles[0]

    $healthServer = switch ($profile) {
        "reference" {
            "sequential-thinking"
        }
        "files-readonly" {
            "filesystem"
        }
        "browser-isolated" {
            "playwright"
        }
    }

    $healthy = $false

    try {
        $uri = (
            "http://127.0.0.1:3050/health/mcp/{0}" -f `
            $healthServer
        )

        $response = Invoke-RestMethod `
            -Uri $uri `
            -Method Get `
            -TimeoutSec 1 `
            -ErrorAction Stop

        $healthy = ([string]$response.state -eq "ready")
    }
    catch {
        $healthy = $false
    }

    return [pscustomobject]@{
        running = $true
        healthy = $healthy
        profile = $profile
        active_count = 1
    }
}


function Get-PlatformVisualState {
    $mcp = Get-McpState
    $tunnel = Get-TunnelState

    if (
        -not $mcp.running -and
        -not $tunnel.running
    ) {
        return [pscustomobject]@{
            mode = "off"
            profile = $mcp.profile
            tunnel_running = $false
            tunnel_ready = $false
            mcp = $false
            healthy = $false
        }
    }

    if (
        $mcp.active_count -eq 1 -and
        $mcp.running -and
        $mcp.healthy -and
        $tunnel.ready
    ) {
        return [pscustomobject]@{
            mode = "on"
            profile = $mcp.profile
            tunnel_running = $true
            tunnel_ready = $true
            mcp = $true
            healthy = $true
        }
    }

    return [pscustomobject]@{
        mode = "partial"
        profile = $mcp.profile
        tunnel_running = $tunnel.running
        tunnel_ready = $tunnel.ready
        mcp = $mcp.running
        healthy = $mcp.healthy
    }
}


$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Visible = $true

$menu = New-Object System.Windows.Forms.ContextMenuStrip

$statusItem = New-Object System.Windows.Forms.ToolStripMenuItem
$statusItem.Enabled = $false

$toggleItem = New-Object System.Windows.Forms.ToolStripMenuItem
$toggleItem.Text = "Переключить ВКЛ / ВЫКЛ"

$startItem = New-Object System.Windows.Forms.ToolStripMenuItem
$startItem.Text = "Включить"

$stopItem = New-Object System.Windows.Forms.ToolStripMenuItem
$stopItem.Text = "Выключить"

$logItem = New-Object System.Windows.Forms.ToolStripMenuItem
$logItem.Text = "Открыть журнал"

$exitItem = New-Object System.Windows.Forms.ToolStripMenuItem
$exitItem.Text = "Закрыть индикатор"

[void]$menu.Items.Add($statusItem)
[void]$menu.Items.Add(
    (New-Object System.Windows.Forms.ToolStripSeparator)
)
[void]$menu.Items.Add($toggleItem)
[void]$menu.Items.Add($startItem)
[void]$menu.Items.Add($stopItem)
[void]$menu.Items.Add(
    (New-Object System.Windows.Forms.ToolStripSeparator)
)
[void]$menu.Items.Add($logItem)
[void]$menu.Items.Add($exitItem)

$notify.ContextMenuStrip = $menu

$script:OperationJob = $null
$script:LastMode = $null


function Set-VisualState {
    param(
        [Parameter(Mandatory)]
        [ValidateSet("off", "partial", "busy", "on")]
        [string]$Mode,

        [string]$Profile
    )

    switch ($Mode) {
        "on" {
            $notify.Icon = $script:GreenIcon
            $notify.Text = "Chat Agent Platform — ВКЛ"
            $statusItem.Text = "🟢 Включено — $Profile"
            $startItem.Enabled = $false
            $stopItem.Enabled = $true
        }

        "off" {
            $notify.Icon = $script:RedIcon
            $notify.Text = "Chat Agent Platform — ВЫКЛ"
            $statusItem.Text = "🔴 Выключено"
            $startItem.Enabled = $true
            $stopItem.Enabled = $false
        }

        "busy" {
            $notify.Icon = $script:YellowIcon
            $notify.Text = "Chat Agent Platform — переключение"
            $statusItem.Text = "🟡 Переключение..."
            $startItem.Enabled = $false
            $stopItem.Enabled = $false
        }

        default {
            $notify.Icon = $script:YellowIcon
            $notify.Text = "Chat Agent Platform — частично"
            $statusItem.Text = "🟡 Частично запущено"
            $startItem.Enabled = $true
            $stopItem.Enabled = $true
        }
    }
}


function Refresh-VisualState {
    if (
        $null -ne $script:OperationJob -and
        $script:OperationJob.State -eq "Running"
    ) {
        Set-VisualState -Mode busy -Profile ""
        return
    }

    $state = Get-PlatformVisualState
    Set-VisualState `
        -Mode $state.mode `
        -Profile $state.profile

    $script:LastMode = $state.mode
}


function Show-StateBalloon {
    $state = Get-PlatformVisualState

    switch ($state.mode) {
        "on" {
            $notify.BalloonTipTitle = `
                "Chat Agent Platform — ВКЛ"
            $notify.BalloonTipText = `
                "Профиль $($state.profile) полностью готов."
        }

        "off" {
            $notify.BalloonTipTitle = `
                "Chat Agent Platform — ВЫКЛ"
            $notify.BalloonTipText = `
                "Туннель и локальный MCP остановлены."
        }

        default {
            $notify.BalloonTipTitle = "Chat Agent Platform"
            $notify.BalloonTipText = (
                "Система запущена частично. MCP ready={0}; " +
                "Tunnel ready={1}."
            ) -f $state.healthy, $state.tunnel_ready
        }
    }

    $notify.ShowBalloonTip(2500)
}


function Start-ControllerOperation {
    param(
        [Parameter(Mandatory)]
        [ValidateSet("Start", "Stop")]
        [string]$Action
    )

    if (
        $null -ne $script:OperationJob -and
        $script:OperationJob.State -eq "Running"
    ) {
        return
    }

    if ($null -ne $script:OperationJob) {
        Remove-Job `
            $script:OperationJob `
            -Force `
            -ErrorAction SilentlyContinue

        $script:OperationJob = $null
    }

    Set-VisualState -Mode busy -Profile ""

    $script:OperationJob = Start-Job `
        -ArgumentList $ControllerPath, $Action `
        -ScriptBlock {
            param(
                $ControllerPath,
                $Action
            )

            $ErrorActionPreference = "Stop"

            & $ControllerPath `
                -Action $Action `
                -NoNotify
        }
}


function Toggle-Platform {
    $state = Get-PlatformVisualState

    if ($state.mode -eq "off") {
        Start-ControllerOperation -Action Start
    }
    else {
        Start-ControllerOperation -Action Stop
    }
}


$toggleHandler = {
    Toggle-Platform
}

$notify.add_DoubleClick($toggleHandler)
$toggleItem.add_Click($toggleHandler)

$startItem.add_Click({
    Start-ControllerOperation -Action Start
})

$stopItem.add_Click({
    Start-ControllerOperation -Action Stop
})

$logItem.add_Click({
    if (Test-Path $ControllerLog) {
        Start-Process `
            -FilePath "notepad.exe" `
            -ArgumentList "`"$ControllerLog`""
    }
})

$exitItem.add_Click({
    $notify.Visible = $false
    $notify.Dispose()

    $timer.Stop()
    $timer.Dispose()

    if ($null -ne $script:OperationJob) {
        Remove-Job `
            $script:OperationJob `
            -Force `
            -ErrorAction SilentlyContinue
    }

    $script:RedIcon.Dispose()
    $script:YellowIcon.Dispose()
    $script:GreenIcon.Dispose()

    $mutex.ReleaseMutex()
    $mutex.Dispose()

    [System.Windows.Forms.Application]::Exit()
})


$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 2000

$timer.add_Tick({
    if ($null -ne $script:OperationJob) {
        if (
            $script:OperationJob.State -in @(
                "Completed",
                "Failed",
                "Stopped"
            )
        ) {
            $failed = (
                $script:OperationJob.State -ne "Completed"
            )

            $reason = $null

            if ($failed) {
                $reason = `
                    $script:OperationJob.ChildJobs[0].JobStateInfo.Reason
            }

            Receive-Job `
                $script:OperationJob `
                -ErrorAction SilentlyContinue |
                Out-Null

            Remove-Job `
                $script:OperationJob `
                -Force `
                -ErrorAction SilentlyContinue

            $script:OperationJob = $null

            Refresh-VisualState

            if ($failed) {
                $notify.BalloonTipTitle = `
                    "Chat Agent Platform — ошибка"

                if ($reason) {
                    $notify.BalloonTipText = $reason.Message
                }
                else {
                    $notify.BalloonTipText = `
                        "Операция завершилась с ошибкой."
                }

                $notify.ShowBalloonTip(3500)
            }
            else {
                Show-StateBalloon
            }

            return
        }
    }

    Refresh-VisualState
})

Refresh-VisualState
$timer.Start()

$notify.BalloonTipTitle = "Chat Agent Platform"
$notify.BalloonTipText = `
    "Индикатор запущен. Двойной клик — ВКЛ/ВЫКЛ."
$notify.ShowBalloonTip(2500)

[System.Windows.Forms.Application]::Run()
