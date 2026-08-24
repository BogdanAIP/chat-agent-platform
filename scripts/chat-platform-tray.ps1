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
$ControllerLog = Join-Path $LocalRoot "logs\controller.log"
$DesiredStateFile = Join-Path $LocalRoot "state\desired-state.json"
$QualificationHandoffState = Join-Path $LocalRoot "state\stage26-3a-procedure-supervised-handoff.json"
$QualificationDirectState = Join-Path $LocalRoot "state\stage26-3a-procedure-direct.json"
$QualificationHealthUrlFile = Join-Path $LocalRoot "state\stage26-3a-procedure-direct-health.url"

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

$script:RedIcon = New-StatusIcon ([System.Drawing.Color]::Crimson)
$script:YellowIcon = New-StatusIcon ([System.Drawing.Color]::Goldenrod)
$script:GreenIcon = New-StatusIcon ([System.Drawing.Color]::LimeGreen)
$script:BlueIcon = New-StatusIcon ([System.Drawing.Color]::DodgerBlue)

function Invoke-ControllerStatus {
    $pwsh = (Get-Command "pwsh.exe" -ErrorAction Stop).Source
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
        return ($output | Out-String | ConvertFrom-Json -ErrorAction Stop)
    }
    catch {
        throw "Manager status returned invalid JSON: $(($output | Out-String).Trim())"
    }
}

function Read-JsonStateFile {
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

function Test-QualificationReady {
    if (-not (Test-Path -LiteralPath $QualificationHealthUrlFile -PathType Leaf)) {
        return $false
    }

    try {
        $base = (Get-Content -LiteralPath $QualificationHealthUrlFile -Raw).Trim().TrimEnd('/')
        if ($base -notmatch '^https?://127\.0\.0\.1(?::\d+)?$') {
            return $false
        }
        $response = Invoke-WebRequest `
            -Uri "$base/readyz" `
            -Method Get `
            -TimeoutSec 2 `
            -ErrorAction Stop
        return ($response.StatusCode -eq 200)
    }
    catch {
        return $false
    }
}

function Get-QualificationVisualState {
    if (-not (Test-Path -LiteralPath $QualificationHandoffState -PathType Leaf)) {
        return $null
    }

    $handoff = Read-JsonStateFile -Path $QualificationHandoffState
    if ($null -eq $handoff) {
        return [pscustomobject]@{
            mode = "partial"
            profile = "procedure-qualification"
            route_owner = "qualification"
            expected_tool_count = 6
            tunnel_running = $false
            tunnel_ready = $false
            mcp_ready = $false
            active_count = 0
            files_root = $null
            tunnel_id = $null
            error = "Qualification handoff receipt is unreadable."
        }
    }

    $direct = Read-JsonStateFile -Path $QualificationDirectState
    $desired = Read-JsonStateFile -Path $DesiredStateFile
    $directReceiptPresent = (
        $null -ne $direct -and
        $null -ne $direct.PSObject.Properties['pid'] -and
        $null -ne $direct.PSObject.Properties['tunnel_id'] -and
        -not [string]::IsNullOrWhiteSpace([string]$direct.tunnel_id)
    )
    $ready = Test-QualificationReady
    $handoffRunning = (
        $null -ne $handoff.PSObject.Properties['phase'] -and
        [string]$handoff.phase -eq "running"
    )
    $normalSuspended = (
        $null -ne $desired -and
        $null -ne $desired.PSObject.Properties['desired_state'] -and
        [string]$desired.desired_state -eq "stopped"
    )
    $fullyReady = ($handoffRunning -and $normalSuspended -and $directReceiptPresent -and $ready)

    return [pscustomobject]@{
        mode = if ($fullyReady) { "qualification" } else { "partial" }
        profile = "procedure-qualification"
        route_owner = "qualification"
        expected_tool_count = 6
        tunnel_running = ($directReceiptPresent -and $ready)
        tunnel_ready = $ready
        mcp_ready = $ready
        active_count = if ($directReceiptPresent -and $ready) { 1 } else { 0 }
        files_root = if ($null -ne $direct) { [string]$direct.files_root } else { [string]$handoff.files_root }
        tunnel_id = if ($null -ne $direct) { [string]$direct.tunnel_id } else { $null }
        error = if ($fullyReady) { $null } else { "Qualification handoff exists but the 6-tool route is not fully ready." }
    }
}

function Get-PlatformVisualState {
    $qualification = Get-QualificationVisualState
    if ($null -ne $qualification) {
        return $qualification
    }

    try {
        $state = Invoke-ControllerStatus
    }
    catch {
        return [pscustomobject]@{
            mode = "partial"
            profile = "unknown"
            route_owner = "platform"
            expected_tool_count = $null
            tunnel_running = $false
            tunnel_ready = $false
            mcp_ready = $false
            active_count = 0
            files_root = $null
            tunnel_id = $null
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
            -not [string]::IsNullOrWhiteSpace([string]$state.settings.profile)
        ) {
            $profile = [string]$state.settings.profile
        }
        else {
            $profile = "reference"
        }
    }

    if ($activeCount -eq 0 -and -not [bool]$state.tunnel_running) {
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
        route_owner = "platform"
        expected_tool_count = if ($profile -eq "semantic") { 5 } else { $null }
        tunnel_running = [bool]$state.tunnel_running
        tunnel_ready = [bool]$state.tunnel_ready
        mcp_ready = [bool]$state.mcp_ready
        active_count = $activeCount
        files_root = $null
        tunnel_id = $null
        error = $null
    }
}

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
        "qualification" {
            $notify.Icon = $script:BlueIcon
            $notify.Text = "Chat Agent Platform - 6 tools READY"
            $statusItem.Text = "🔵 Qualification - 6 tools READY"
            $detailsItem.Text = "MCP READY | Tunnel READY | owner=qualification"
            if (-not [string]::IsNullOrWhiteSpace([string]$State.files_root)) {
                $workspaceItem.Text = "Workspace: $($State.files_root)"
                $workspaceItem.Visible = $true
            }
            $toggleItem.Enabled = $false
            $startItem.Enabled = $false
            $stopItem.Enabled = $false
        }

        "on" {
            $notify.Icon = $script:GreenIcon
            $notify.Text = "Chat Agent Platform - ON"
            $statusItem.Text = "🟢 Включено - $($State.profile)"
            if ($null -ne $State.expected_tool_count) {
                $detailsItem.Text = "MCP READY | Tunnel READY | $($State.expected_tool_count) tools"
            }
            else {
                $detailsItem.Text = "MCP READY | Tunnel READY"
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
                $detailsItem.Text = "MCP=$($State.mcp_ready) | Tunnel=$($State.tunnel_ready)"
            }
            $toggleItem.Enabled = ($State.route_owner -ne "qualification")
            $startItem.Enabled = ($State.route_owner -ne "qualification")
            $stopItem.Enabled = ($State.route_owner -ne "qualification")
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
            route_owner = "platform"
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
        "qualification" {
            $notify.BalloonTipTitle = "Chat Agent Platform - Qualification"
            $notify.BalloonTipText = "6 tools READY. MCP READY. Tunnel READY. Обычное ВКЛ/ВЫКЛ временно заблокировано."
        }
        "on" {
            $notify.BalloonTipTitle = "Chat Agent Platform - ВКЛ"
            $notify.BalloonTipText = "Профиль $($state.profile) полностью готов."
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
                $notify.BalloonTipText = "Система запущена частично. MCP ready=$($state.mcp_ready); Tunnel ready=$($state.tunnel_ready)."
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

    $state = Get-PlatformVisualState
    if ($state.route_owner -eq "qualification") {
        Show-StateBalloon
        return
    }

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
        route_owner = "platform"
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
    if ($state.route_owner -eq "qualification") {
        Show-StateBalloon
        return
    }

    if ($state.mode -eq "off") {
        Start-ControllerOperation -Action Start
    }
    else {
        Start-ControllerOperation -Action Stop
    }
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
    $script:BlueIcon.Dispose()

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
$notify.BalloonTipText = "Индикатор запущен. Синий = Stage 26.3A qualification (6 tools)."
$notify.ShowBalloonTip(2500)
[System.Windows.Forms.Application]::Run()
