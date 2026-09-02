Set-StrictMode -Version Latest

$script:CapTrayUpdateProcess = $null
$script:CapTrayUpdateStdoutTask = $null
$script:CapTrayUpdateStderrTask = $null
$script:CapTrayUpdateStartedAt = $null
$script:CapTrayUpdateTimer = $null
$script:CapTrayUpdateItem = $null
$script:CapTrayUpdateNotifyIcon = $null
$script:CapTrayUpdateBusyPredicate = $null
$script:CapTrayUpdateScript = Join-Path $PSScriptRoot 'chat-platform-update.ps1'
$script:CapTrayUpdateTimeoutSeconds = 900

function Test-CapUpdateTrayBusy {
    if ($null -eq $script:CapTrayUpdateProcess) {
        return $false
    }
    try {
        return (-not $script:CapTrayUpdateProcess.HasExited)
    }
    catch {
        return $false
    }
}

function Clear-CapUpdateTrayProcess {
    $updateProcess = $script:CapTrayUpdateProcess
    if (
        $null -ne $updateProcess -and
        $null -ne $script:OperationProcess -and
        [object]::ReferenceEquals($script:OperationProcess, $updateProcess)
    ) {
        $script:OperationProcess = $null
        $script:OperationAction = $null
        $script:OperationStartedAt = $null
    }

    if ($null -ne $updateProcess) {
        try { $updateProcess.Dispose() } catch {}
    }
    $script:CapTrayUpdateProcess = $null
    $script:CapTrayUpdateStdoutTask = $null
    $script:CapTrayUpdateStderrTask = $null
    $script:CapTrayUpdateStartedAt = $null
}

function Show-CapUpdateTrayBalloon {
    param(
        [Parameter(Mandatory)] [string]$Text,
        [string]$Title = 'Chat Agent Platform',
        [int]$Milliseconds = 3500
    )

    if ($null -eq $script:CapTrayUpdateNotifyIcon) {
        return
    }
    $message = $Text.Trim()
    if ($message.Length -gt 220) {
        $message = $message.Substring(0, 217) + '...'
    }
    $script:CapTrayUpdateNotifyIcon.BalloonTipTitle = $Title
    $script:CapTrayUpdateNotifyIcon.BalloonTipText = $message
    $script:CapTrayUpdateNotifyIcon.ShowBalloonTip($Milliseconds)
}

function Get-CapUpdateTrayResult {
    param([string]$Stdout)

    if ([string]::IsNullOrWhiteSpace($Stdout)) {
        return $null
    }
    try {
        return ($Stdout.Trim() | ConvertFrom-Json -ErrorAction Stop)
    }
    catch {
        return $null
    }
}

function Complete-CapUpdateTrayOperation {
    if ($null -eq $script:CapTrayUpdateProcess) {
        if ($null -ne $script:CapTrayUpdateTimer) {
            $script:CapTrayUpdateTimer.Stop()
        }
        return
    }

    if (-not $script:CapTrayUpdateProcess.HasExited) {
        if (
            $null -ne $script:CapTrayUpdateStartedAt -and
            ([datetimeoffset]::UtcNow - $script:CapTrayUpdateStartedAt).TotalSeconds -lt $script:CapTrayUpdateTimeoutSeconds
        ) {
            return
        }
        try { $script:CapTrayUpdateProcess.Kill($true) } catch {}
        try { $script:CapTrayUpdateProcess.WaitForExit(5000) | Out-Null } catch {}
    }

    if ($null -ne $script:CapTrayUpdateTimer) {
        $script:CapTrayUpdateTimer.Stop()
    }

    $exitCode = try { [int]$script:CapTrayUpdateProcess.ExitCode } catch { -1 }
    $stdout = try { $script:CapTrayUpdateStdoutTask.GetAwaiter().GetResult().Trim() } catch { '' }
    $stderr = try { $script:CapTrayUpdateStderrTask.GetAwaiter().GetResult().Trim() } catch { '' }
    $result = Get-CapUpdateTrayResult -Stdout $stdout

    Clear-CapUpdateTrayProcess
    if ($null -ne $script:CapTrayUpdateItem) {
        $script:CapTrayUpdateItem.Text = 'Обновить'
        $script:CapTrayUpdateItem.Enabled = $true
    }
    if ($null -ne (Get-Command 'Refresh-VisualState' -ErrorAction SilentlyContinue)) {
        Refresh-VisualState
    }

    if ($null -ne $result -and [string]$result.status -eq 'current' -and $exitCode -eq 0) {
        Show-CapUpdateTrayBalloon `
            -Text 'Обновление не требуется. Установлена последняя версия.'
        return
    }

    if ($null -ne $result -and [string]$result.status -eq 'updated' -and $exitCode -eq 0) {
        $sha = [string]$result.installed_commit_sha
        $version = if ($sha -match '^[0-9a-f]{40}$') { $sha.Substring(0, 8) } else { 'последняя' }
        Show-CapUpdateTrayBalloon `
            -Title 'Chat Agent Platform обновлён' `
            -Text "Установлена версия $version."
        return
    }

    if ($null -ne $result -and [string]$result.status -eq 'blocked') {
        Show-CapUpdateTrayBalloon `
            -Title 'Chat Agent Platform — обновление заблокировано' `
            -Text 'Удалённый main не является продолжением установленной версии.' `
            -Milliseconds 5000
        return
    }

    $detail = if (
        $null -ne $result -and
        -not [string]::IsNullOrWhiteSpace([string]$result.reason)
    ) {
        [string]$result.reason
    }
    elseif (-not [string]::IsNullOrWhiteSpace($stderr)) {
        $stderr
    }
    else {
        "Операция обновления завершилась с кодом $exitCode."
    }
    Show-CapUpdateTrayBalloon `
        -Title 'Chat Agent Platform — ошибка обновления' `
        -Text $detail `
        -Milliseconds 5000
}

function Start-CapUpdateTrayOperation {
    if (Test-CapUpdateTrayBusy) {
        Show-CapUpdateTrayBalloon -Text 'Обновление уже выполняется.'
        return
    }

    if (
        $null -ne $script:CapTrayUpdateBusyPredicate -and
        [bool]$script:CapTrayUpdateBusyPredicate.Invoke()
    ) {
        Show-CapUpdateTrayBalloon -Text 'Дождитесь завершения текущей операции платформы.'
        return
    }

    if (-not (Test-Path -LiteralPath $script:CapTrayUpdateScript -PathType Leaf)) {
        Show-CapUpdateTrayBalloon `
            -Title 'Chat Agent Platform — ошибка обновления' `
            -Text 'Установленный updater отсутствует.'
        return
    }

    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pwsh
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    foreach ($argument in @(
        '-NoLogo',
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $script:CapTrayUpdateScript,
        '-Action', 'Update'
    )) {
        $startInfo.ArgumentList.Add([string]$argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) {
            throw 'Не удалось запустить updater.'
        }
    }
    catch {
        $process.Dispose()
        Show-CapUpdateTrayBalloon `
            -Title 'Chat Agent Platform — ошибка обновления' `
            -Text $_.Exception.Message
        return
    }

    $script:CapTrayUpdateProcess = $process
    $script:CapTrayUpdateStdoutTask = $process.StandardOutput.ReadToEndAsync()
    $script:CapTrayUpdateStderrTask = $process.StandardError.ReadToEndAsync()
    $script:CapTrayUpdateStartedAt = [datetimeoffset]::UtcNow

    # Reuse the existing tray lifecycle-busy projection while the updater owns
    # installation. This blocks power-toggle/double-click and mode changes from
    # racing the canonical bootstrap without teaching those handlers updater
    # internals or adding a second visible busy-state mechanism.
    $script:OperationProcess = $process
    $script:OperationAction = 'Update'
    $script:OperationStartedAt = $script:CapTrayUpdateStartedAt

    $script:CapTrayUpdateItem.Text = 'Обновление...'
    $script:CapTrayUpdateItem.Enabled = $false
    Show-CapUpdateTrayBalloon -Text 'Проверяю и при необходимости устанавливаю последнюю версию main.'
    $script:CapTrayUpdateTimer.Start()
    if ($null -ne (Get-Command 'Refresh-VisualState' -ErrorAction SilentlyContinue)) {
        Refresh-VisualState
    }
}

function Register-CapUpdateTrayMenu {
    param(
        [Parameter(Mandatory)]
        [System.Windows.Forms.ToolStripMenuItem]$MoreMenu,

        [Parameter(Mandatory)]
        [System.Windows.Forms.NotifyIcon]$NotifyIcon,

        [scriptblock]$BusyPredicate
    )

    if ($null -ne $script:CapTrayUpdateItem) {
        throw 'Tray update menu is already registered.'
    }

    $script:CapTrayUpdateNotifyIcon = $NotifyIcon
    $script:CapTrayUpdateBusyPredicate = $BusyPredicate
    $script:CapTrayUpdateItem = New-Object System.Windows.Forms.ToolStripMenuItem
    $script:CapTrayUpdateItem.Text = 'Обновить'

    $insertIndex = [math]::Min(3, $MoreMenu.DropDownItems.Count)
    $MoreMenu.DropDownItems.Insert($insertIndex, $script:CapTrayUpdateItem)

    $script:CapTrayUpdateTimer = New-Object System.Windows.Forms.Timer
    $script:CapTrayUpdateTimer.Interval = 250
    $script:CapTrayUpdateTimer.add_Tick({ Complete-CapUpdateTrayOperation })
    $script:CapTrayUpdateItem.add_Click({ Start-CapUpdateTrayOperation })
}

function Stop-CapUpdateTrayMenu {
    if ($null -ne $script:CapTrayUpdateTimer) {
        $script:CapTrayUpdateTimer.Stop()
        $script:CapTrayUpdateTimer.Dispose()
        $script:CapTrayUpdateTimer = $null
    }

    # Never kill an updater merely because the user closes the indicator. The
    # updater owns its own mutex and canonical bootstrap lifecycle and may be in
    # the middle of replacing installed files. The tray exit path blocks while
    # Test-CapUpdateTrayBusy is true, so this is normally reached only idle.
    Clear-CapUpdateTrayProcess
    $script:CapTrayUpdateItem = $null
    $script:CapTrayUpdateNotifyIcon = $null
    $script:CapTrayUpdateBusyPredicate = $null
}
