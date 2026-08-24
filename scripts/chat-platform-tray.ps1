[CmdletBinding()]
param(
    [switch]$NoConsoleHost
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($IsWindows -and -not $NoConsoleHost) {
    $pwsh = (Get-Command "pwsh.exe" -ErrorAction Stop).Source
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pwsh
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true

    foreach ($argument in @(
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $PSCommandPath,
        "-NoConsoleHost"
    )) {
        $startInfo.ArgumentList.Add([string]$argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) {
            throw "Failed to relaunch tray without a console host."
        }
    }
    finally {
        $process.Dispose()
    }

    exit 0
}

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
$StateDir = Join-Path $LocalRoot "state"
$SupervisorStateFile = Join-Path $StateDir "supervisor.json"
$DesiredStateFile = Join-Path $StateDir "desired-state.json"
$SettingsFile = Join-Path $StateDir "settings.json"
$ControllerLog = Join-Path $LocalRoot "logs\controller.log"
$SupervisorSnapshotFreshnessSeconds = 45

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
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.Clear([System.Drawing.Color]::Transparent)

    $brush = New-Object System.Drawing.SolidBrush($Color)
    $border = New-Object System.Drawing.Pen([System.Drawing.Color]::White, 2)
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

function Read-JsonFile {
    param([Parameter(Mandatory)] [string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return $null
    }

    try {
        return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        return $null
    }
}

function Get-PropertyValue {
    param(
        $Object,
        [Parameter(Mandatory)] [string]$Name,
        $DefaultValue = $null
    )

    if ($null -eq $Object) {
        return $DefaultValue
    }

    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) {
        return $DefaultValue
    }

    return $property.Value
}

function Get-SupervisorSnapshotAgeSeconds {
    param([Parameter(Mandatory)] $Snapshot)

    $observedAt = Get-PropertyValue -Object $Snapshot -Name "observed_at"
    if ($null -eq $observedAt) {
        return $null
    }

    try {
        if ($observedAt -is [datetimeoffset]) {
            $observed = ([datetimeoffset]$observedAt).ToUniversalTime()
        }
        elseif ($observedAt -is [datetime]) {
            $date = [datetime]$observedAt
            if ($date.Kind -eq [DateTimeKind]::Unspecified) {
                $date = [datetime]::SpecifyKind($date, [DateTimeKind]::Utc)
            }
            else {
                $date = $date.ToUniversalTime()
            }
            $observed = [datetimeoffset]$date
        }
        else {
            $text = [string]$observedAt
            if ([string]::IsNullOrWhiteSpace($text)) {
                return $null
            }
            $observed = [datetimeoffset]::Parse(
                $text,
                [Globalization.CultureInfo]::InvariantCulture,
                [Globalization.DateTimeStyles]::RoundtripKind
            ).ToUniversalTime()
        }

        return [math]::Max(
            0,
            ([datetimeoffset]::UtcNow - $observed).TotalSeconds
        )
    }
    catch {
        return $null
    }
}

function Get-PlatformVisualState {
    # The tray is a projection only. The supervisor owns expensive health
    # observation and atomically publishes supervisor.json. Polling the manager
    # from this 2-second UI timer used to create nested pwsh.exe processes and
    # repeat WMI/transport probes continuously.
    $snapshot = Read-JsonFile -Path $SupervisorStateFile
    $desired = Read-JsonFile -Path $DesiredStateFile
    $settings = Read-JsonFile -Path $SettingsFile

    $desiredState = [string](Get-PropertyValue -Object $desired -Name "desired_state" -DefaultValue "")
    if ([string]::IsNullOrWhiteSpace($desiredState)) {
        $desiredState = [string](Get-PropertyValue -Object $snapshot -Name "desired_state" -DefaultValue "unknown")
    }

    $profile = [string](Get-PropertyValue -Object $snapshot -Name "profile" -DefaultValue "")
    if ([string]::IsNullOrWhiteSpace($profile)) {
        $profile = [string](Get-PropertyValue -Object $settings -Name "profile" -DefaultValue "reference")
    }

    $filesRoot = [string](Get-PropertyValue -Object $settings -Name "files_root" -DefaultValue "")
    $toolCount = if ($profile -in @("semantic", "semantic-direct")) { 6 } else { $null }

    if ($null -eq $snapshot) {
        return [pscustomobject]@{
            mode = "partial"
            profile = $profile
            expected_tool_count = $toolCount
            desired_state = $desiredState
            runtime_ready = $false
            mcp_ready = $false
            tunnel_ready = $false
            health_code = "SUPERVISOR_STATE_UNAVAILABLE"
            files_root = $filesRoot
            error = "Supervisor state is unavailable."
        }
    }

    $age = Get-SupervisorSnapshotAgeSeconds -Snapshot $snapshot
    if ($null -eq $age -or $age -gt $SupervisorSnapshotFreshnessSeconds) {
        return [pscustomobject]@{
            mode = "partial"
            profile = $profile
            expected_tool_count = $toolCount
            desired_state = $desiredState
            runtime_ready = $false
            mcp_ready = $false
            tunnel_ready = $false
            health_code = "SUPERVISOR_STATE_STALE"
            files_root = $filesRoot
            error = "Supervisor state is stale or has no valid observed_at timestamp."
        }
    }

    $supervisorState = [string](Get-PropertyValue -Object $snapshot -Name "supervisor_state" -DefaultValue "unknown")
    $healthCode = [string](Get-PropertyValue -Object $snapshot -Name "health_code" -DefaultValue "UNKNOWN")
    $runtimeReady = [bool](Get-PropertyValue -Object $snapshot -Name "runtime_ready" -DefaultValue $false)
    $mcpReady = [bool](Get-PropertyValue -Object $snapshot -Name "mcp_ready" -DefaultValue $false)
    $tunnelReady = [bool](Get-PropertyValue -Object $snapshot -Name "tunnel_local_ready" -DefaultValue $false)

    if ($desiredState -eq "stopped") {
        $mode = "off"
    }
    elseif ($runtimeReady -and $mcpReady -and $tunnelReady) {
        $mode = "on"
    }
    else {
        $mode = "partial"
    }

    return [pscustomobject]@{
        mode = $mode
        profile = $profile
        expected_tool_count = $toolCount
        desired_state = $desiredState
        supervisor_state = $supervisorState
        runtime_ready = $runtimeReady
        mcp_ready = $mcpReady
        tunnel_ready = $tunnelReady
        health_code = $healthCode
        files_root = $filesRoot
        error = $null
    }
}

$script:RedIcon = New-StatusIcon ([System.Drawing.Color]::Crimson)
$script:YellowIcon = New-StatusIcon ([System.Drawing.Color]::Goldenrod)
$script:GreenIcon = New-StatusIcon ([System.Drawing.Color]::LimeGreen)

$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Visible = $true
$menu = New-Object System.Windows.Forms.ContextMenuStrip

$statusItem = New-Object System.Windows.Forms.ToolStripMenuItem
$statusItem.Enabled = $false
$detailsItem = New-Object System.Windows.Forms.ToolStripMenuItem
$detailsItem.Enabled = $false
$workspaceItem = New-Object System.Windows.Forms.ToolStripMenuItem
$workspaceItem.Enabled = $false
$workspaceItem.Visible = $false

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
[void]$menu.Items.Add($detailsItem)
[void]$menu.Items.Add($workspaceItem)
[void]$menu.Items.Add((New-Object System.Windows.Forms.ToolStripSeparator))
[void]$menu.Items.Add($toggleItem)
[void]$menu.Items.Add($startItem)
[void]$menu.Items.Add($stopItem)
[void]$menu.Items.Add((New-Object System.Windows.Forms.ToolStripSeparator))
[void]$menu.Items.Add($logItem)
[void]$menu.Items.Add($exitItem)
$notify.ContextMenuStrip = $menu

$script:OperationJob = $null
$script:LastState = $null

function Set-VisualState {
    param(
        [Parameter(Mandatory)]
        [psobject]$State
    )

    $workspaceItem.Visible = $false

    switch ([string]$State.mode) {
        "on" {
            $notify.Icon = $script:GreenIcon
            $notify.Text = "Chat Agent Platform - READY"
            $statusItem.Text = "🟢 Готово - $($State.profile)"
            if ($null -ne $State.expected_tool_count) {
                $detailsItem.Text = "MCP READY | Tunnel READY | $($State.expected_tool_count) tools"
            }
            else {
                $detailsItem.Text = "MCP READY | Tunnel READY"
            }
            if (-not [string]::IsNullOrWhiteSpace([string]$State.files_root)) {
                $workspaceItem.Text = "Workspace: $($State.files_root)"
                $workspaceItem.Visible = $true
            }
            $toggleItem.Enabled = $true
            $startItem.Enabled = $false
            $stopItem.Enabled = $true
        }

        "off" {
            $notify.Icon = $script:RedIcon
            $notify.Text = "Chat Agent Platform - OFF"
            $statusItem.Text = "🔴 Выключено"
            $detailsItem.Text = "MCP stopped | Tunnel stopped"
            $toggleItem.Enabled = $true
            $startItem.Enabled = $true
            $stopItem.Enabled = $false
        }

        "busy" {
            $notify.Icon = $script:YellowIcon
            $notify.Text = "Chat Agent Platform - switching"
            $statusItem.Text = "🟡 Переключение..."
            $detailsItem.Text = "Ожидание подтверждённого состояния"
            $toggleItem.Enabled = $false
            $startItem.Enabled = $false
            $stopItem.Enabled = $false
        }

        default {
            $notify.Icon = $script:YellowIcon
            $notify.Text = "Chat Agent Platform - PARTIAL"
            $statusItem.Text = "🟡 Частично - $($State.profile)"
            if (-not [string]::IsNullOrWhiteSpace([string]$State.error)) {
                $detailsItem.Text = [string]$State.error
            }
            else {
                $detailsItem.Text = "Health=$($State.health_code) | MCP=$($State.mcp_ready) | Tunnel=$($State.tunnel_ready)"
            }
            $toggleItem.Enabled = ([string]$State.desired_state -in @("running", "stopped"))
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
        Set-VisualState -State ([pscustomobject]@{
            mode = "busy"
            profile = ""
        })
        return
    }

    $state = Get-PlatformVisualState
    Set-VisualState -State $state
    $script:LastState = $state
}

function Show-StateBalloon {
    $state = Get-PlatformVisualState

    switch ([string]$state.mode) {
        "on" {
            $notify.BalloonTipTitle = "Chat Agent Platform - READY"
            if ($null -ne $state.expected_tool_count) {
                $notify.BalloonTipText = "Профиль $($state.profile) готов. MCP READY. Tunnel READY. $($state.expected_tool_count) tools."
            }
            else {
                $notify.BalloonTipText = "Профиль $($state.profile) полностью готов."
            }
        }
        "off" {
            $notify.BalloonTipTitle = "Chat Agent Platform - ВЫКЛ"
            $notify.BalloonTipText = "Туннель и локальный MCP остановлены."
        }
        default {
            $notify.BalloonTipTitle = "Chat Agent Platform"
            if (-not [string]::IsNullOrWhiteSpace([string]$state.error)) {
                $notify.BalloonTipText = [string]$state.error
            }
            else {
                $notify.BalloonTipText = "Система запущена частично. Health=$($state.health_code); MCP=$($state.mcp_ready); Tunnel=$($state.tunnel_ready)."
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
        Remove-Job $script:OperationJob -Force -ErrorAction SilentlyContinue
        $script:OperationJob = $null
    }

    Set-VisualState -State ([pscustomobject]@{
        mode = "busy"
        profile = ""
    })

    $script:OperationJob = Start-Job `
        -ArgumentList $CommandPath, $Action `
        -ScriptBlock {
            param($CommandPath, $Action)
            $ErrorActionPreference = "Stop"
            $pwsh = (Get-Command "pwsh.exe" -ErrorAction Stop).Source
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
                throw "Manager action $Action failed: $(($output | Out-String).Trim())"
            }
        }
}

function Toggle-Platform {
    $state = Get-PlatformVisualState
    if ([string]$state.desired_state -eq "stopped") {
        Start-ControllerOperation -Action Start
        return
    }
    if ([string]$state.desired_state -eq "running") {
        Start-ControllerOperation -Action Stop
        return
    }

    $notify.BalloonTipTitle = "Chat Agent Platform"
    $notify.BalloonTipText = "Не удалось определить желаемое состояние. Используйте Включить или Выключить."
    $notify.ShowBalloonTip(3000)
}

$toggleHandler = { Toggle-Platform }
$notify.add_DoubleClick($toggleHandler)
$toggleItem.add_Click($toggleHandler)
$startItem.add_Click({ Start-ControllerOperation -Action Start })
$stopItem.add_Click({ Start-ControllerOperation -Action Stop })

$logItem.add_Click({
    if (Test-Path -LiteralPath $ControllerLog -PathType Leaf) {
        Start-Process -FilePath "notepad.exe" -ArgumentList "`"$ControllerLog`""
    }
})

$exitItem.add_Click({
    $notify.Visible = $false
    $notify.Dispose()
    $timer.Stop()
    $timer.Dispose()

    if ($null -ne $script:OperationJob) {
        Remove-Job $script:OperationJob -Force -ErrorAction SilentlyContinue
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
        if ($script:OperationJob.State -in @("Completed", "Failed", "Stopped")) {
            $failed = ($script:OperationJob.State -ne "Completed")
            $reason = $null

            if ($failed) {
                $reason = $script:OperationJob.ChildJobs[0].JobStateInfo.Reason
            }

            try {
                Receive-Job $script:OperationJob -ErrorAction Stop | Out-Null
            }
            catch {
                $failed = $true
                if ($null -eq $reason) {
                    $reason = $_.Exception
                }
            }

            Remove-Job $script:OperationJob -Force -ErrorAction SilentlyContinue
            $script:OperationJob = $null
            Refresh-VisualState

            if ($failed) {
                $notify.BalloonTipTitle = "Chat Agent Platform - ошибка"
                if ($reason) {
                    $notify.BalloonTipText = $reason.Message
                }
                else {
                    $notify.BalloonTipText = "Операция завершилась с ошибкой."
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
$notify.BalloonTipText = "Индикатор запущен. Зелёный READY для semantic означает единый 6-tool runtime."
$notify.ShowBalloonTip(2500)
[System.Windows.Forms.Application]::Run()