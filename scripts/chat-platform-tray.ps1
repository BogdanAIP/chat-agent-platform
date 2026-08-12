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

$CommandPath = Join-Path $PSScriptRoot "chat-platform.ps1"
$LocalRoot = Join-Path $env:LOCALAPPDATA "ChatAgentPlatform"
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


function Invoke-ControllerStatus {
    $pwsh = (
        Get-Command `
            "pwsh.exe" `
            -ErrorAction Stop
    ).Source

    $output = @(
        & $pwsh `
            -NoLogo `
            -NoProfile `
            -ExecutionPolicy Bypass `
            -File $CommandPath `
            -Action Status `
            -NoNotify `
            2>&1
    )

    if ($LASTEXITCODE -ne 0) {
        throw (
            "Manager status failed with exit code {0}: {1}" -f `
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
            "Manager status returned invalid JSON: {0}" -f `
            (($output | Out-String).Trim())
        )
    }
}


function Get-PlatformVisualState {
    try {
        $state = Invoke-ControllerStatus
    }
    catch {
        return [pscustomobject]@{
            mode = "partial"
            profile = "unknown"
            tunnel_running = $false
            tunnel_ready = $false
            mcp_ready = $false
            active_count = 0
            error = $_.Exception.Message
        }
    }

    $activeCount = [int]$state.active_count
    $profile = [string]$state.active_profile

    if ([string]::IsNullOrWhiteSpace($profile)) {
        if ($activeCount -gt 1) {
            $profile = "multiple"
        }
        elseif (
            $null -ne $state.settings -and
            -not [string]::IsNullOrWhiteSpace(
                [string]$state.settings.profile
            )
        ) {
            $profile = [string]$state.settings.profile
        }
        else {
            $profile = "reference"
        }
    }

    if (
        $activeCount -eq 0 -and
        -not [bool]$state.tunnel_running
    ) {
        $mode = "off"
    }
    elseif (
        $activeCount -eq 1 -and
        [bool]$state.mcp_ready -and
        [bool]$state.tunnel_ready
    ) {
        $mode = "on"
    }
    else {
        $mode = "partial"
    }

    return [pscustomobject]@{
        mode = $mode
        profile = $profile
        tunnel_running = [bool]$state.tunnel_running
        tunnel_ready = [bool]$state.tunnel_ready
        mcp_ready = [bool]$state.mcp_ready
        active_count = $activeCount
        error = $null
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
$script:LastState = $null


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
            $statusItem.Text = "🟡 Частично — $Profile"
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

    $script:LastState = $state
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
            if (-not [string]::IsNullOrWhiteSpace($state.error)) {
                $notify.BalloonTipText = $state.error
            }
            else {
                $notify.BalloonTipText = (
                    "Система запущена частично. MCP ready={0}; " +
                    "Tunnel ready={1}; profiles={2}."
                ) -f `
                    $state.mcp_ready,
                    $state.tunnel_ready,
                    $state.active_count
            }
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
        -ArgumentList $CommandPath, $Action `
        -ScriptBlock {
            param(
                $CommandPath,
                $Action
            )

            $ErrorActionPreference = "Stop"
            $pwsh = (
                Get-Command `
                    "pwsh.exe" `
                    -ErrorAction Stop
            ).Source

            $output = @(
                & $pwsh `
                    -NoLogo `
                    -NoProfile `
                    -ExecutionPolicy Bypass `
                    -File $CommandPath `
                    -Action $Action `
                    -NoNotify `
                    2>&1
            )

            if ($LASTEXITCODE -ne 0) {
                throw (
                    "Manager action {0} failed: {1}" -f `
                    $Action,
                    (($output | Out-String).Trim())
                )
            }
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

            try {
                Receive-Job `
                    $script:OperationJob `
                    -ErrorAction Stop |
                    Out-Null
            }
            catch {
                $failed = $true
                if ($null -eq $reason) {
                    $reason = $_.Exception
                }
            }

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
