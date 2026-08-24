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
$OperationModeFile = Join-Path $StateDir "operation-mode.json"
$ManualStatusFile = Join-Path $StateDir "manual-status.json"
$ManagerOwnerFile = Join-Path $StateDir "manager-owner.json"
$ControllerLog = Join-Path $LocalRoot "logs\controller.log"
$SupervisorTaskName = "Chat Agent Platform Transport Supervisor"
$AutomaticSnapshotFreshnessSeconds = 2100
$OperationTimeoutSeconds = 120

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

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

function Write-AtomicJson {
    param(
        [Parameter(Mandatory)] [string]$Path,
        [Parameter(Mandatory)] $Value
    )

    $temporary = "$Path.new-$PID"
    try {
        $Value |
            ConvertTo-Json -Depth 8 |
            Set-Content -LiteralPath $temporary -Encoding utf8
        Move-Item -LiteralPath $temporary -Destination $Path -Force
    }
    finally {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
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

function ConvertTo-UtcDateTimeOffset {
    param($Value)

    if ($null -eq $Value) {
        return $null
    }

    try {
        if ($Value -is [datetimeoffset]) {
            return ([datetimeoffset]$Value).ToUniversalTime()
        }
        if ($Value -is [datetime]) {
            $date = [datetime]$Value
            if ($date.Kind -eq [DateTimeKind]::Unspecified) {
                $date = [datetime]::SpecifyKind($date, [DateTimeKind]::Utc)
            }
            else {
                $date = $date.ToUniversalTime()
            }
            return ([datetimeoffset]$date).ToUniversalTime()
        }

        $text = [string]$Value
        if ([string]::IsNullOrWhiteSpace($text)) {
            return $null
        }
        return [datetimeoffset]::Parse(
            $text,
            [Globalization.CultureInfo]::InvariantCulture,
            [Globalization.DateTimeStyles]::RoundtripKind
        ).ToUniversalTime()
    }
    catch {
        return $null
    }
}

function Get-OperationMode {
    $state = Read-JsonFile -Path $OperationModeFile
    $mode = [string](Get-PropertyValue -Object $state -Name "mode" -DefaultValue "automatic")
    if ($mode -notin @("manual", "automatic")) {
        return "automatic"
    }
    return $mode
}

function Save-OperationMode {
    param(
        [Parameter(Mandatory)]
        [ValidateSet("manual", "automatic")]
        [string]$Mode
    )

    Write-AtomicJson -Path $OperationModeFile -Value ([ordered]@{
        schema_version = 1
        mode = $Mode
        updated_at = [datetimeoffset]::UtcNow.ToString("o")
    })
}

function Get-SnapshotAgeSeconds {
    param([Parameter(Mandatory)] $Snapshot)

    $observedAt = Get-PropertyValue -Object $Snapshot -Name "observed_at"
    $observed = ConvertTo-UtcDateTimeOffset -Value $observedAt
    if ($null -eq $observed) {
        return $null
    }

    return [math]::Max(
        0,
        ([datetimeoffset]::UtcNow - $observed).TotalSeconds
    )
}

function Test-ManagerOwnerFromCurrentBoot {
    param($Owner)

    if ($null -eq $Owner) {
        return $false
    }

    $startedAt = ConvertTo-UtcDateTimeOffset -Value (
        Get-PropertyValue -Object $Owner -Name "started_at"
    )
    if ($null -eq $startedAt) {
        return $false
    }

    # Manual mode deliberately performs no periodic WMI/process polling. Use
    # TickCount64 to reject a stale owner receipt left behind by a previous boot.
    $bootUtc = [datetimeoffset]::UtcNow.AddMilliseconds(-[Environment]::TickCount64)
    return (
        $startedAt -ge $bootUtc.AddSeconds(-5) -and
        $startedAt -le [datetimeoffset]::UtcNow.AddMinutes(1)
    )
}

function Get-SettingsProjection {
    $settings = Read-JsonFile -Path $SettingsFile
    return [pscustomobject]@{
        profile = [string](Get-PropertyValue -Object $settings -Name "profile" -DefaultValue "reference")
        files_root = [string](Get-PropertyValue -Object $settings -Name "files_root" -DefaultValue "")
    }
}

function Save-ManualStatusForAction {
    param(
        [Parameter(Mandatory)]
        [ValidateSet("Start", "Stop")]
        [string]$Action
    )

    if ((Get-OperationMode) -ne "manual") {
        return
    }

    $running = ($Action -eq "Start")
    $expectedDesiredState = if ($running) { "running" } else { "stopped" }
    $desired = Read-JsonFile -Path $DesiredStateFile
    $currentDesiredState = [string](
        Get-PropertyValue -Object $desired -Name "desired_state" -DefaultValue "unknown"
    )

    # A lifecycle process can finish after another explicit action has already
    # changed desired-state.json. Never let that stale completion overwrite the
    # newer user intent with a contradictory manual-status receipt.
    if ($currentDesiredState -ne $expectedDesiredState) {
        return
    }

    $settings = Get-SettingsProjection
    Write-AtomicJson -Path $ManualStatusFile -Value ([ordered]@{
        schema_version = 1
        source = "manual_user_action"
        desired_state = $expectedDesiredState
        profile = [string]$settings.profile
        runtime_ready = $running
        mcp_ready = $running
        tunnel_local_ready = $running
        health_code = if ($running) { "READY" } else { "STOPPED" }
        observed_at = [datetimeoffset]::UtcNow.ToString("o")
    })
}

function Save-ManualStatusFromAutomaticSnapshot {
    param(
        $Snapshot,
        [Parameter(Mandatory)] [string]$DesiredState
    )

    $settings = Get-SettingsProjection
    if ($null -eq $Snapshot) {
        $runtimeReady = $false
        $mcpReady = $false
        $tunnelReady = $false
        $healthCode = if ($DesiredState -eq "stopped") { "STOPPED" } else { "MANUAL_STATE_UNVERIFIED" }
        $profile = [string]$settings.profile
    }
    else {
        $runtimeReady = [bool](Get-PropertyValue -Object $Snapshot -Name "runtime_ready" -DefaultValue $false)
        $mcpReady = [bool](Get-PropertyValue -Object $Snapshot -Name "mcp_ready" -DefaultValue $false)
        $tunnelReady = [bool](Get-PropertyValue -Object $Snapshot -Name "tunnel_local_ready" -DefaultValue $false)
        $healthCode = [string](Get-PropertyValue -Object $Snapshot -Name "health_code" -DefaultValue "MANUAL_STATE_UNVERIFIED")
        $profile = [string](Get-PropertyValue -Object $Snapshot -Name "profile" -DefaultValue ([string]$settings.profile))
    }

    Write-AtomicJson -Path $ManualStatusFile -Value ([ordered]@{
        schema_version = 1
        source = "automatic_handoff"
        desired_state = $DesiredState
        profile = $profile
        runtime_ready = $runtimeReady
        mcp_ready = $mcpReady
        tunnel_local_ready = $tunnelReady
        health_code = $healthCode
        observed_at = [datetimeoffset]::UtcNow.ToString("o")
    })
}

function Get-PlatformVisualState {
    $operationMode = Get-OperationMode
    $desired = Read-JsonFile -Path $DesiredStateFile
    $settings = Get-SettingsProjection
    $desiredState = [string](Get-PropertyValue -Object $desired -Name "desired_state" -DefaultValue "unknown")

    if ($operationMode -eq "manual") {
        # Keep the legacy receipt readable for compatibility/diagnostics, but do
        # not make the visible Manual state depend on a tray timer callback.
        $manualSnapshot = Read-JsonFile -Path $ManualStatusFile
        $ownerFilePresent = Test-Path -LiteralPath $ManagerOwnerFile -PathType Leaf
        $owner = Read-JsonFile -Path $ManagerOwnerFile
        $ownerCurrentBoot = ($ownerFilePresent -and (Test-ManagerOwnerFromCurrentBoot -Owner $owner))
        $profile = [string](Get-PropertyValue -Object $manualSnapshot -Name "profile" -DefaultValue ([string]$settings.profile))
        $toolCount = if ($profile -in @("semantic", "semantic-direct")) { 6 } else { $null }

        if ($desiredState -eq "stopped" -and -not $ownerFilePresent) {
            return [pscustomobject]@{
                mode = "off"
                operation_mode = $operationMode
                profile = $profile
                expected_tool_count = $toolCount
                desired_state = $desiredState
                runtime_ready = $false
                mcp_ready = $false
                tunnel_ready = $false
                health_code = "STOPPED"
                files_root = [string]$settings.files_root
                error = $null
            }
        }

        if ($desiredState -eq "running" -and $ownerCurrentBoot) {
            return [pscustomobject]@{
                mode = "on"
                operation_mode = $operationMode
                profile = $profile
                expected_tool_count = $toolCount
                desired_state = $desiredState
                runtime_ready = $true
                mcp_ready = $true
                tunnel_ready = $true
                health_code = "READY"
                files_root = [string]$settings.files_root
                error = $null
            }
        }

        $manualError = if ($desiredState -eq "running" -and $ownerFilePresent -and -not $ownerCurrentBoot) {
            "Ручной запуск не подтверждён в текущем сеансе Windows."
        }
        elseif ($desiredState -eq "running") {
            "Ручной запуск ещё выполняется."
        }
        elseif ($desiredState -eq "stopped" -and $ownerFilePresent) {
            "Ручная остановка ещё выполняется."
        }
        else {
            "Ручное состояние ещё не подтверждено."
        }

        return [pscustomobject]@{
            mode = "partial"
            operation_mode = $operationMode
            profile = $profile
            expected_tool_count = $toolCount
            desired_state = $desiredState
            runtime_ready = $false
            mcp_ready = $false
            tunnel_ready = $false
            health_code = "MANUAL_STATE_UNVERIFIED"
            files_root = [string]$settings.files_root
            error = $manualError
        }
    }

    $snapshot = Read-JsonFile -Path $SupervisorStateFile
    $profile = [string](Get-PropertyValue -Object $snapshot -Name "profile" -DefaultValue ([string]$settings.profile))
    $toolCount = if ($profile -in @("semantic", "semantic-direct")) { 6 } else { $null }

    if ($null -eq $snapshot) {
        return [pscustomobject]@{
            mode = "partial"
            operation_mode = $operationMode
            profile = $profile
            expected_tool_count = $toolCount
            desired_state = $desiredState
            runtime_ready = $false
            mcp_ready = $false
            tunnel_ready = $false
            health_code = "SUPERVISOR_STATE_UNAVAILABLE"
            files_root = [string]$settings.files_root
            error = "Состояние автоматической проверки недоступно."
        }
    }

    $age = Get-SnapshotAgeSeconds -Snapshot $snapshot
    if ($null -eq $age -or $age -gt $AutomaticSnapshotFreshnessSeconds) {
        return [pscustomobject]@{
            mode = "partial"
            operation_mode = $operationMode
            profile = $profile
            expected_tool_count = $toolCount
            desired_state = $desiredState
            runtime_ready = $false
            mcp_ready = $false
            tunnel_ready = $false
            health_code = "SUPERVISOR_STATE_STALE"
            files_root = [string]$settings.files_root
            error = "Данные автоматической проверки устарели."
        }
    }

    $runtimeReady = [bool](Get-PropertyValue -Object $snapshot -Name "runtime_ready" -DefaultValue $false)
    $mcpReady = [bool](Get-PropertyValue -Object $snapshot -Name "mcp_ready" -DefaultValue $false)
    $tunnelReady = [bool](Get-PropertyValue -Object $snapshot -Name "tunnel_local_ready" -DefaultValue $false)
    $healthCode = [string](Get-PropertyValue -Object $snapshot -Name "health_code" -DefaultValue "UNKNOWN")

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
        operation_mode = $operationMode
        profile = $profile
        expected_tool_count = $toolCount
        desired_state = $desiredState
        runtime_ready = $runtimeReady
        mcp_ready = $mcpReady
        tunnel_ready = $tunnelReady
        health_code = $healthCode
        files_root = [string]$settings.files_root
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

$modeMenu = New-Object System.Windows.Forms.ToolStripMenuItem
$modeMenu.Text = "Режим"
$manualModeItem = New-Object System.Windows.Forms.ToolStripMenuItem
$manualModeItem.Text = "Ручной"
$automaticModeItem = New-Object System.Windows.Forms.ToolStripMenuItem
$automaticModeItem.Text = "Автоматический — проверка раз в 30 мин"
[void]$modeMenu.DropDownItems.Add($manualModeItem)
[void]$modeMenu.DropDownItems.Add($automaticModeItem)

$powerItem = New-Object System.Windows.Forms.ToolStripMenuItem

$moreMenu = New-Object System.Windows.Forms.ToolStripMenuItem
$moreMenu.Text = "Дополнительно"
$detailsItem = New-Object System.Windows.Forms.ToolStripMenuItem
$detailsItem.Enabled = $false
$workspaceItem = New-Object System.Windows.Forms.ToolStripMenuItem
$workspaceItem.Enabled = $false
$workspaceItem.Visible = $false
$logItem = New-Object System.Windows.Forms.ToolStripMenuItem
$logItem.Text = "Открыть журнал"
[void]$moreMenu.DropDownItems.Add($detailsItem)
[void]$moreMenu.DropDownItems.Add($workspaceItem)
[void]$moreMenu.DropDownItems.Add((New-Object System.Windows.Forms.ToolStripSeparator))
[void]$moreMenu.DropDownItems.Add($logItem)

$exitItem = New-Object System.Windows.Forms.ToolStripMenuItem
$exitItem.Text = "Закрыть индикатор"

[void]$menu.Items.Add($statusItem)
[void]$menu.Items.Add((New-Object System.Windows.Forms.ToolStripSeparator))
[void]$menu.Items.Add($modeMenu)
[void]$menu.Items.Add($powerItem)
[void]$menu.Items.Add((New-Object System.Windows.Forms.ToolStripSeparator))
[void]$menu.Items.Add($moreMenu)
[void]$menu.Items.Add($exitItem)
$notify.ContextMenuStrip = $menu

# Legacy top-level controls intentionally removed from the visible UI:
# "Переключить ВКЛ / ВЫКЛ", simultaneous "Включить" and "Выключить" entries.

$script:OperationProcess = $null
$script:OperationAction = $null
$script:OperationStartedAt = $null
$script:LastState = $null

$operationTimer = New-Object System.Windows.Forms.Timer
$operationTimer.Interval = 250

function Test-OperationRunning {
    if ($null -eq $script:OperationProcess) {
        return $false
    }
    try {
        return (-not $script:OperationProcess.HasExited)
    }
    catch {
        return $false
    }
}

function Clear-OperationProcess {
    if ($null -ne $script:OperationProcess) {
        try { $script:OperationProcess.Dispose() } catch {}
    }
    $script:OperationProcess = $null
    $script:OperationStartedAt = $null
}

function Set-VisualState {
    param(
        [Parameter(Mandatory)]
        [psobject]$State
    )

    $operationMode = [string](Get-PropertyValue -Object $State -Name "operation_mode" -DefaultValue (Get-OperationMode))
    $manualModeItem.Checked = ($operationMode -eq "manual")
    $automaticModeItem.Checked = ($operationMode -eq "automatic")
    $modeMenu.Text = if ($operationMode -eq "manual") { "Режим: Ручной" } else { "Режим: Автоматический" }

    $workspaceItem.Visible = -not [string]::IsNullOrWhiteSpace([string]$State.files_root)
    if ($workspaceItem.Visible) {
        $workspaceItem.Text = "Рабочая папка: $($State.files_root)"
    }

    switch ([string]$State.mode) {
        "on" {
            $notify.Icon = $script:GreenIcon
            $notify.Text = "Chat Agent Platform - READY"
            $statusItem.Text = "🟢 Chat Agent Platform включён"
            $powerItem.Text = "Выключить"
            $powerItem.Enabled = $true
            if ($null -ne $State.expected_tool_count) {
                $detailsItem.Text = "Состояние: READY · MCP · Tunnel · $($State.expected_tool_count) tools"
            }
            else {
                $detailsItem.Text = "Состояние: READY"
            }
        }

        "off" {
            $notify.Icon = $script:RedIcon
            $notify.Text = "Chat Agent Platform - OFF"
            $statusItem.Text = "🔴 Chat Agent Platform выключен"
            $powerItem.Text = "Включить"
            $powerItem.Enabled = $true
            $detailsItem.Text = "Состояние: выключено"
        }

        "busy" {
            $notify.Icon = $script:YellowIcon
            $notify.Text = "Chat Agent Platform - switching"
            $statusItem.Text = "🟡 Переключение..."
            $powerItem.Text = "Подождите..."
            $powerItem.Enabled = $false
            $detailsItem.Text = "Состояние: выполняется операция"
        }

        default {
            $notify.Icon = $script:YellowIcon
            $notify.Text = "Chat Agent Platform - CHECK"
            $statusItem.Text = "🟡 Chat Agent Platform — требуется проверка"
            if ([string]$State.desired_state -eq "stopped") {
                $powerItem.Text = "Включить"
            }
            else {
                $powerItem.Text = "Выключить"
            }
            $powerItem.Enabled = ([string]$State.desired_state -in @("running", "stopped"))
            if (-not [string]::IsNullOrWhiteSpace([string]$State.error)) {
                $detailsItem.Text = "Состояние: $([string]$State.error)"
            }
            else {
                $detailsItem.Text = "Состояние: $($State.health_code)"
            }
        }
    }
}

function Refresh-VisualState {
    $state = Get-PlatformVisualState

    if (Test-OperationRunning) {
        $targetReached = (
            ($script:OperationAction -eq "Start" -and [string]$state.mode -eq "on") -or
            ($script:OperationAction -eq "Stop" -and [string]$state.mode -eq "off")
        )
        if (-not $targetReached) {
            Set-VisualState -State ([pscustomobject]@{
                mode = "busy"
                operation_mode = Get-OperationMode
                profile = ""
                files_root = ""
            })
            return
        }
    }

    Set-VisualState -State $state
    $script:LastState = $state
}

function Show-StateBalloon {
    $state = Get-PlatformVisualState
    $modeText = if ([string]$state.operation_mode -eq "manual") { "Ручной режим." } else { "Автоматический режим." }

    switch ([string]$state.mode) {
        "on" {
            $notify.BalloonTipTitle = "Chat Agent Platform - READY"
            $notify.BalloonTipText = "$modeText Платформа включена."
        }
        "off" {
            $notify.BalloonTipTitle = "Chat Agent Platform - ВЫКЛ"
            $notify.BalloonTipText = "$modeText Платформа выключена."
        }
        default {
            $notify.BalloonTipTitle = "Chat Agent Platform"
            $notify.BalloonTipText = if (-not [string]::IsNullOrWhiteSpace([string]$state.error)) {
                "$modeText $([string]$state.error)"
            }
            else {
                "$modeText Состояние: $($state.health_code)."
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

    if (Test-OperationRunning) {
        return
    }

    Clear-OperationProcess
    Set-VisualState -State ([pscustomobject]@{
        mode = "busy"
        operation_mode = Get-OperationMode
        profile = ""
        files_root = ""
    })

    $pwsh = (Get-Command "pwsh.exe" -ErrorAction Stop).Source
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pwsh
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $false
    $startInfo.RedirectStandardError = $false
    foreach ($argument in @(
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $CommandPath,
        "-Action", $Action,
        "-NoNotify"
    )) {
        $startInfo.ArgumentList.Add([string]$argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    if (-not $process.Start()) {
        $process.Dispose()
        throw "Не удалось запустить операцию $Action."
    }

    $script:OperationProcess = $process
    $script:OperationAction = $Action
    $script:OperationStartedAt = [datetimeoffset]::UtcNow

    # Runs only while an explicit Start/Stop action is in progress.
    $operationTimer.Start()
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
    $notify.BalloonTipText = "Не удалось определить текущее состояние."
    $notify.ShowBalloonTip(3000)
}

function Set-PlatformOperationMode {
    param(
        [Parameter(Mandatory)]
        [ValidateSet("manual", "automatic")]
        [string]$Mode
    )

    if (Test-OperationRunning) {
        $notify.BalloonTipTitle = "Chat Agent Platform"
        $notify.BalloonTipText = "Дождитесь завершения текущей операции."
        $notify.ShowBalloonTip(2500)
        return
    }

    if ((Get-OperationMode) -eq $Mode) {
        return
    }

    if ($Mode -eq "manual") {
        $snapshot = Read-JsonFile -Path $SupervisorStateFile
        $desired = Read-JsonFile -Path $DesiredStateFile
        $desiredState = [string](Get-PropertyValue -Object $desired -Name "desired_state" -DefaultValue "unknown")

        Save-OperationMode -Mode "manual"
        try {
            $task = Get-ScheduledTask -TaskName $SupervisorTaskName -ErrorAction SilentlyContinue
            if ($null -ne $task -and [string]$task.State -ne "Ready") {
                Stop-ScheduledTask -TaskName $SupervisorTaskName -ErrorAction Stop
            }
        }
        catch {
            Save-OperationMode -Mode "automatic"
            throw
        }

        Save-ManualStatusFromAutomaticSnapshot -Snapshot $snapshot -DesiredState $desiredState
    }
    else {
        Save-OperationMode -Mode "automatic"
        try {
            Get-ScheduledTask -TaskName $SupervisorTaskName -ErrorAction Stop | Out-Null
            Start-ScheduledTask -TaskName $SupervisorTaskName -ErrorAction Stop
        }
        catch {
            Save-OperationMode -Mode "manual"
            throw
        }
    }

    Refresh-VisualState
    $notify.BalloonTipTitle = "Chat Agent Platform"
    $notify.BalloonTipText = if ($Mode -eq "manual") {
        "Ручной режим включён. Фоновый supervisor остановлен."
    }
    else {
        "Автоматический режим включён. Проверка раз в 30 минут."
    }
    $notify.ShowBalloonTip(3000)
}

$operationTimer.add_Tick({
    if ($null -eq $script:OperationProcess) {
        $operationTimer.Stop()
        return
    }

    $timedOut = $false
    if (-not $script:OperationProcess.HasExited) {
        if (
            $null -eq $script:OperationStartedAt -or
            ([datetimeoffset]::UtcNow - $script:OperationStartedAt).TotalSeconds -lt $OperationTimeoutSeconds
        ) {
            return
        }

        $timedOut = $true
        try { $script:OperationProcess.Kill($true) } catch {}
        try { $script:OperationProcess.WaitForExit(5000) | Out-Null } catch {}
    }

    $operationTimer.Stop()
    $exitCode = if ($timedOut) {
        -1
    }
    else {
        try { [int]$script:OperationProcess.ExitCode } catch { -1 }
    }

    $action = [string]$script:OperationAction
    $failed = ($exitCode -ne 0)
    $failureText = if ($timedOut) {
        "Операция превысила $OperationTimeoutSeconds секунд и была остановлена."
    }
    else {
        "Операция завершилась с кодом $exitCode."
    }

    Clear-OperationProcess
    $script:OperationAction = $null

    if (-not $failed -and $action -in @("Start", "Stop")) {
        Save-ManualStatusForAction -Action $action
    }

    Refresh-VisualState
    if ($failed) {
        $notify.BalloonTipTitle = "Chat Agent Platform - ошибка"
        $notify.BalloonTipText = $failureText
        $notify.ShowBalloonTip(4000)
    }
    else {
        Show-StateBalloon
    }
})

$powerItem.add_Click({ Toggle-Platform })
$notify.add_DoubleClick({ Toggle-Platform })
$manualModeItem.add_Click({
    try { Set-PlatformOperationMode -Mode "manual" }
    catch {
        $notify.BalloonTipTitle = "Chat Agent Platform - ошибка"
        $notify.BalloonTipText = $_.Exception.Message
        $notify.ShowBalloonTip(3500)
    }
})
$automaticModeItem.add_Click({
    try { Set-PlatformOperationMode -Mode "automatic" }
    catch {
        $notify.BalloonTipTitle = "Chat Agent Platform - ошибка"
        $notify.BalloonTipText = $_.Exception.Message
        $notify.ShowBalloonTip(3500)
    }
})
$logItem.add_Click({
    if (Test-Path -LiteralPath $ControllerLog -PathType Leaf) {
        Start-Process -FilePath "notepad.exe" -ArgumentList "`"$ControllerLog`""
    }
})

# Idle observation is event-driven. There is no periodic health/status timer.
$uiHost = New-Object System.Windows.Forms.Form
$uiHost.ShowInTaskbar = $false
$uiHost.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedToolWindow
$uiHost.Opacity = 0
$uiHost.Width = 1
$uiHost.Height = 1
$uiHost.Location = New-Object System.Drawing.Point(-32000, -32000)
$null = $uiHost.Handle

$script:WatchedStateNames = @(
    "supervisor.json",
    "desired-state.json",
    "settings.json",
    "operation-mode.json",
    "manual-status.json",
    "manager-owner.json"
)

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $StateDir
$watcher.Filter = "*.json"
$watcher.NotifyFilter = (
    [System.IO.NotifyFilters]::FileName -bor
    [System.IO.NotifyFilters]::LastWrite -bor
    [System.IO.NotifyFilters]::Size
)
$watcher.SynchronizingObject = $uiHost

$stateChangedHandler = {
    param($sender, $eventArgs)
    if ($script:WatchedStateNames -contains [string]$eventArgs.Name) {
        Refresh-VisualState
    }
}
$stateRenamedHandler = {
    param($sender, $eventArgs)
    if (
        $script:WatchedStateNames -contains [string]$eventArgs.Name -or
        $script:WatchedStateNames -contains [string]$eventArgs.OldName
    ) {
        Refresh-VisualState
    }
}

$watcher.add_Changed($stateChangedHandler)
$watcher.add_Created($stateChangedHandler)
$watcher.add_Deleted($stateChangedHandler)
$watcher.add_Renamed($stateRenamedHandler)
$watcher.EnableRaisingEvents = $true

$exitItem.add_Click({
    $notify.Visible = $false
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    $operationTimer.Stop()
    $operationTimer.Dispose()

    if (Test-OperationRunning) {
        try { $script:OperationProcess.Kill($true) } catch {}
    }
    Clear-OperationProcess

    $uiHost.Dispose()
    $notify.Dispose()
    $script:RedIcon.Dispose()
    $script:YellowIcon.Dispose()
    $script:GreenIcon.Dispose()

    $mutex.ReleaseMutex()
    $mutex.Dispose()
    [System.Windows.Forms.Application]::Exit()
})

Refresh-VisualState
$notify.BalloonTipTitle = "Chat Agent Platform"
$notify.BalloonTipText = "Индикатор запущен."
$notify.ShowBalloonTip(2000)
[System.Windows.Forms.Application]::Run()
