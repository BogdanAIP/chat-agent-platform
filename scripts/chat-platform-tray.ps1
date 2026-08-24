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
$ControllerLog = Join-Path $LocalRoot "logs\controller.log"
$SupervisorTaskName = "Chat Agent Platform Transport Supervisor"
$AutomaticSnapshotFreshnessSeconds = 2100

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

function Get-SettingsProjection {
    $settings = Read-JsonFile -Path $SettingsFile
    $profile = [string](Get-PropertyValue -Object $settings -Name "profile" -DefaultValue "reference")
    $filesRoot = [string](Get-PropertyValue -Object $settings -Name "files_root" -DefaultValue "")

    return [pscustomobject]@{
        profile = $profile
        files_root = $filesRoot
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

    $settings = Get-SettingsProjection
    $running = ($Action -eq "Start")
    $desiredState = if ($running) { "running" } else { "stopped" }

    Write-AtomicJson -Path $ManualStatusFile -Value ([ordered]@{
        schema_version = 1
        source = "manual_user_action"
        desired_state = $desiredState
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
        $running = $false
        $mcpReady = $false
        $tunnelReady = $false
        $healthCode = if ($DesiredState -eq "stopped") { "STOPPED" } else { "MANUAL_STATE_UNVERIFIED" }
        $profile = [string]$settings.profile
    }
    else {
        $running = [bool](Get-PropertyValue -Object $Snapshot -Name "runtime_ready" -DefaultValue $false)
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
        runtime_ready = $running
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

    $snapshot = if ($operationMode -eq "manual") {
        Read-JsonFile -Path $ManualStatusFile
    }
    else {
        Read-JsonFile -Path $SupervisorStateFile
    }

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
            health_code = if ($operationMode -eq "manual") { "MANUAL_STATE_UNVERIFIED" } else { "SUPERVISOR_STATE_UNAVAILABLE" }
            files_root = [string]$settings.files_root
            error = if ($operationMode -eq "manual") { "Ручное состояние ещё не подтверждено." } else { "Supervisor state is unavailable." }
        }
    }

    if ($operationMode -eq "automatic") {
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
                error = "Supervisor state is stale or has no valid observed_at timestamp."
            }
        }
    }

    $snapshotDesired = [string](Get-PropertyValue -Object $snapshot -Name "desired_state" -DefaultValue $desiredState)
    if (
        $operationMode -eq "manual" -and
        $desiredState -in @("running", "stopped") -and
        $snapshotDesired -ne $desiredState
    ) {
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
            error = "Ручное состояние изменилось и ещё не подтверждено."
        }
    }

    $supervisorState = [string](Get-PropertyValue -Object $snapshot -Name "supervisor_state" -DefaultValue "manual")
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
        operation_mode = $operationMode
        profile = $profile
        expected_tool_count = $toolCount
        desired_state = $desiredState
        supervisor_state = $supervisorState
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
$detailsItem = New-Object System.Windows.Forms.ToolStripMenuItem
$detailsItem.Enabled = $false
$workspaceItem = New-Object System.Windows.Forms.ToolStripMenuItem
$workspaceItem.Enabled = $false
$workspaceItem.Visible = $false

$modeLabelItem = New-Object System.Windows.Forms.ToolStripMenuItem
$modeLabelItem.Text = "Режим"
$modeLabelItem.Enabled = $false
$manualModeItem = New-Object System.Windows.Forms.ToolStripMenuItem
$manualModeItem.Text = "Ручной"
$automaticModeItem = New-Object System.Windows.Forms.ToolStripMenuItem
$automaticModeItem.Text = "Автоматический (проверка раз в 30 минут)"

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
[void]$menu.Items.Add($modeLabelItem)
[void]$menu.Items.Add($manualModeItem)
[void]$menu.Items.Add($automaticModeItem)
[void]$menu.Items.Add((New-Object System.Windows.Forms.ToolStripSeparator))
[void]$menu.Items.Add($toggleItem)
[void]$menu.Items.Add($startItem)
[void]$menu.Items.Add($stopItem)
[void]$menu.Items.Add((New-Object System.Windows.Forms.ToolStripSeparator))
[void]$menu.Items.Add($logItem)
[void]$menu.Items.Add($exitItem)
$notify.ContextMenuStrip = $menu

$script:OperationJob = $null
$script:OperationAction = $null
$script:LastState = $null

$operationTimer = New-Object System.Windows.Forms.Timer
$operationTimer.Interval = 250

function Set-VisualState {
    param(
        [Parameter(Mandatory)]
        [psobject]$State
    )

    $operationMode = [string](Get-PropertyValue -Object $State -Name "operation_mode" -DefaultValue (Get-OperationMode))
    $manualModeItem.Checked = ($operationMode -eq "manual")
    $automaticModeItem.Checked = ($operationMode -eq "automatic")
    $workspaceItem.Visible = $false

    $modeText = if ($operationMode -eq "manual") { "Ручной" } else { "Автоматический" }

    switch ([string]$State.mode) {
        "on" {
            $notify.Icon = $script:GreenIcon
            $notify.Text = "Chat Agent Platform - READY"
            $statusItem.Text = "🟢 Готово - $($State.profile)"
            if ($null -ne $State.expected_tool_count) {
                $detailsItem.Text = "$modeText | MCP READY | Tunnel READY | $($State.expected_tool_count) tools"
            }
            else {
                $detailsItem.Text = "$modeText | MCP READY | Tunnel READY"
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
            $detailsItem.Text = "$modeText | MCP stopped | Tunnel stopped"
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
                $detailsItem.Text = "$modeText | $([string]$State.error)"
            }
            else {
                $detailsItem.Text = "$modeText | Health=$($State.health_code) | MCP=$($State.mcp_ready) | Tunnel=$($State.tunnel_ready)"
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
            operation_mode = Get-OperationMode
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
    $modeText = if ([string]$state.operation_mode -eq "manual") { "Ручной режим." } else { "Автоматический режим." }

    switch ([string]$state.mode) {
        "on" {
            $notify.BalloonTipTitle = "Chat Agent Platform - READY"
            $notify.BalloonTipText = "$modeText Профиль $($state.profile) готов. MCP READY. Tunnel READY."
        }
        "off" {
            $notify.BalloonTipTitle = "Chat Agent Platform - ВЫКЛ"
            $notify.BalloonTipText = "$modeText Туннель и локальный MCP остановлены."
        }
        default {
            $notify.BalloonTipTitle = "Chat Agent Platform"
            if (-not [string]::IsNullOrWhiteSpace([string]$state.error)) {
                $notify.BalloonTipText = "$modeText $([string]$state.error)"
            }
            else {
                $notify.BalloonTipText = "$modeText Health=$($state.health_code); MCP=$($state.mcp_ready); Tunnel=$($state.tunnel_ready)."
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
        operation_mode = Get-OperationMode
        profile = ""
    })

    $script:OperationAction = $Action
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

    # This timer exists only while an explicit user Start/Stop operation is in
    # progress. It is stopped during idle operation and is not a health poller.
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
    $notify.BalloonTipText = "Не удалось определить желаемое состояние. Используйте Включить или Выключить."
    $notify.ShowBalloonTip(3000)
}

function Set-PlatformOperationMode {
    param(
        [Parameter(Mandatory)]
        [ValidateSet("manual", "automatic")]
        [string]$Mode
    )

    if (
        $null -ne $script:OperationJob -and
        $script:OperationJob.State -eq "Running"
    ) {
        $notify.BalloonTipTitle = "Chat Agent Platform"
        $notify.BalloonTipText = "Дождитесь завершения текущего включения или выключения."
        $notify.ShowBalloonTip(2500)
        return
    }

    $current = Get-OperationMode
    if ($current -eq $Mode) {
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
            $task = Get-ScheduledTask -TaskName $SupervisorTaskName -ErrorAction Stop
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
        "Автоматический режим включён. Проверка выполняется раз в 30 минут."
    }
    $notify.ShowBalloonTip(3000)
}

$operationTimer.add_Tick({
    if ($null -eq $script:OperationJob) {
        $operationTimer.Stop()
        return
    }

    if ($script:OperationJob.State -notin @("Completed", "Failed", "Stopped")) {
        return
    }

    $operationTimer.Stop()
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

    if (-not $failed -and $script:OperationAction -in @("Start", "Stop")) {
        Save-ManualStatusForAction -Action ([string]$script:OperationAction)
    }
    $script:OperationAction = $null

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
})

$toggleHandler = { Toggle-Platform }
$notify.add_DoubleClick($toggleHandler)
$toggleItem.add_Click($toggleHandler)
$startItem.add_Click({ Start-ControllerOperation -Action Start })
$stopItem.add_Click({ Start-ControllerOperation -Action Stop })
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

# FileSystemWatcher is the idle observation mechanism. Windows wakes the tray
# only when relevant state files change; there is no periodic 2-second refresh.
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
    "manual-status.json"
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

    if ($null -ne $script:OperationJob) {
        Remove-Job $script:OperationJob -Force -ErrorAction SilentlyContinue
    }

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
$notify.BalloonTipText = "Индикатор запущен. Режим можно выбрать в меню значка."
$notify.ShowBalloonTip(2500)
[System.Windows.Forms.Application]::Run()
