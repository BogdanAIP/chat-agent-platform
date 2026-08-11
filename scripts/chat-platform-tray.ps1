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
$ControllerLog = Join-Path $LocalRoot "logs\controller.log"

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

    $graphics.Clear(
        [System.Drawing.Color]::Transparent
    )

    $brush = New-Object System.Drawing.SolidBrush($Color)

    $border = New-Object System.Drawing.Pen(
        [System.Drawing.Color]::White,
        2
    )

    $graphics.FillEllipse(
        $brush,
        3,
        3,
        26,
        26
    )

    $graphics.DrawEllipse(
        $border,
        3,
        3,
        26,
        26
    )

    $handle = $bitmap.GetHicon()

    try {
        $temporary = [System.Drawing.Icon]::FromHandle($handle)
        $icon = $temporary.Clone()
    }
    finally {
        [ChatPlatformNativeIcon]::DestroyIcon($handle) |
            Out-Null

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

    return (
        Get-Content `
            -LiteralPath $SettingsFile `
            -Raw |
        ConvertFrom-Json
    )
}


function Get-TunnelRunning {
    $processes = @(
        Get-CimInstance Win32_Process `
            -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -eq "tunnel-client.exe" -and
            $_.CommandLine -match "local-1mcp"
        }
    )

    return ($processes.Count -gt 0)
}


function Get-McpState {
    $settings = Get-Settings
    $profile = [string]$settings.profile

    $pidFile = Join-Path `
        $RepoRoot `
        "runtime\chat-profiles\$profile\server.pid"

    if (-not (Test-Path $pidFile)) {
        return [pscustomobject]@{
            running = $false
            healthy = $false
            profile = $profile
        }
    }

    try {
        $state = (
            Get-Content `
                -LiteralPath $pidFile `
                -Raw |
            ConvertFrom-Json
        )

        $process = Get-Process `
            -Id $state.pid `
            -ErrorAction Stop
    }
    catch {
        return [pscustomobject]@{
            running = $false
            healthy = $false
            profile = $profile
        }
    }

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

        default {
            $null
        }
    }

    $healthy = $false

    if ($healthServer) {
        try {
            $uri = (
                "http://127.0.0.1:3050/health/mcp/{0}" -f `
                $healthServer
            )

            $response = Invoke-WebRequest `
                -Uri $uri `
                -Method Get `
                -TimeoutSec 1 `
                -ErrorAction Stop

            $healthy = ($response.StatusCode -eq 200)
        }
        catch {
            $healthy = $false
        }
    }

    return [pscustomobject]@{
        running = $true
        healthy = $healthy
        profile = $profile
    }
}


function Get-PlatformVisualState {
    $mcp = Get-McpState
    $tunnel = Get-TunnelRunning

    if (
        -not $mcp.running -and
        -not $tunnel
    ) {
        return [pscustomobject]@{
            mode = "off"
            profile = $mcp.profile
            tunnel = $false
            mcp = $false
            healthy = $false
        }
    }

    if (
        $mcp.running -and
        $mcp.healthy -and
        $tunnel
    ) {
        return [pscustomobject]@{
            mode = "on"
            profile = $mcp.profile
            tunnel = $true
            mcp = $true
            healthy = $true
        }
    }

    return [pscustomobject]@{
        mode = "partial"
        profile = $mcp.profile
        tunnel = $tunnel
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
        [ValidateSet(
            "off",
            "partial",
            "busy",
            "on"
        )]
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
        Set-VisualState `
            -Mode busy `
            -Profile ""

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
            $notify.BalloonTipTitle = `
                "Chat Agent Platform"

            $notify.BalloonTipText = `
                "Система запущена частично."
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

    Set-VisualState `
        -Mode busy `
        -Profile ""

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
                    $notify.BalloonTipText = `
                        $reason.Message
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
