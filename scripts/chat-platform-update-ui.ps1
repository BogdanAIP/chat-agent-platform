[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $IsWindows) {
    throw 'Chat Agent Platform update UI supports Windows only.'
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$LocalRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
$StatePath = Join-Path $LocalRoot 'state\platform-update.json'
$UpdateScript = Join-Path $PSScriptRoot 'chat-platform-update.ps1'
$UpdateLog = Join-Path $LocalRoot 'logs\update.log'

if (-not (Test-Path -LiteralPath $UpdateScript -PathType Leaf)) {
    throw "Updater is missing: $UpdateScript"
}

$form = New-Object System.Windows.Forms.Form
$form.Text = 'Chat Agent Platform — Обновление'
$form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.ClientSize = New-Object System.Drawing.Size(500, 245)

$title = New-Object System.Windows.Forms.Label
$title.Text = 'Обновление Chat Agent Platform'
$title.Font = New-Object System.Drawing.Font('Segoe UI', 13, [System.Drawing.FontStyle]::Bold)
$title.AutoSize = $true
$title.Location = New-Object System.Drawing.Point(20, 18)
$form.Controls.Add($title)

$versionLabel = New-Object System.Windows.Forms.Label
$versionLabel.AutoSize = $false
$versionLabel.Size = New-Object System.Drawing.Size(455, 48)
$versionLabel.Location = New-Object System.Drawing.Point(22, 58)
$versionLabel.Font = New-Object System.Drawing.Font('Segoe UI', 9)
$form.Controls.Add($versionLabel)

$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.AutoSize = $false
$statusLabel.Size = New-Object System.Drawing.Size(455, 48)
$statusLabel.Location = New-Object System.Drawing.Point(22, 105)
$statusLabel.Font = New-Object System.Drawing.Font('Segoe UI', 9)
$form.Controls.Add($statusLabel)

$checkButton = New-Object System.Windows.Forms.Button
$checkButton.Text = 'Проверить обновление'
$checkButton.Size = New-Object System.Drawing.Size(180, 36)
$checkButton.Location = New-Object System.Drawing.Point(22, 169)
$form.Controls.Add($checkButton)

$updateButton = New-Object System.Windows.Forms.Button
$updateButton.Text = 'Обновить'
$updateButton.Size = New-Object System.Drawing.Size(130, 36)
$updateButton.Location = New-Object System.Drawing.Point(212, 169)
$updateButton.Enabled = $false
$form.Controls.Add($updateButton)

$logButton = New-Object System.Windows.Forms.Button
$logButton.Text = 'Журнал'
$logButton.Size = New-Object System.Drawing.Size(105, 36)
$logButton.Location = New-Object System.Drawing.Point(352, 169)
$form.Controls.Add($logButton)

$script:Process = $null
$script:StdoutTask = $null
$script:StderrTask = $null
$script:Action = $null
$script:StartedAt = $null
$OperationTimeoutSeconds = 900

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 250

function Short-Sha {
    param($Value)
    $text = [string]$Value
    if ($text -match '^[0-9a-f]{40}$') {
        return $text.Substring(0, 8)
    }
    return 'неизвестно'
}

function Read-UpdateState {
    if (-not (Test-Path -LiteralPath $StatePath -PathType Leaf)) {
        return $null
    }
    try {
        return Get-Content -LiteralPath $StatePath -Raw -Encoding utf8 | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        return $null
    }
}

function Refresh-UpdateView {
    $state = Read-UpdateState
    if ($null -eq $state) {
        $versionLabel.Text = "Установлено: неизвестно`r`nДоступно: ещё не проверялось"
        $statusLabel.Text = 'Нажмите «Проверить обновление».'
        $updateButton.Enabled = $false
        return
    }

    $installed = Short-Sha $state.installed_commit_sha
    $target = Short-Sha $state.target_commit_sha
    $versionLabel.Text = "Установлено: $installed`r`nДоступно: $target"

    switch ([string]$state.status) {
        'current' {
            $statusLabel.Text = 'Установлена последняя принятая версия main.'
            $updateButton.Enabled = $false
        }
        'update_available' {
            $statusLabel.Text = 'Доступно обновление из принятого main.'
            $updateButton.Text = "Обновить до $target"
            $updateButton.Enabled = $true
        }
        'installing' {
            $statusLabel.Text = 'Обновление выполняется...'
            $updateButton.Enabled = $false
        }
        'blocked' {
            $statusLabel.Text = 'Обновление заблокировано: main не является продолжением установленной версии.'
            $updateButton.Enabled = $false
        }
        'error' {
            $statusLabel.Text = "Ошибка обновления: $([string]$state.last_error)"
            $updateButton.Enabled = $false
        }
        default {
            $statusLabel.Text = 'Состояние версии ещё не определено.'
            $updateButton.Enabled = $false
        }
    }
}

function Set-Busy {
    param([bool]$Busy)
    $checkButton.Enabled = -not $Busy
    if ($Busy) {
        $updateButton.Enabled = $false
    }
    $form.UseWaitCursor = $Busy
}

function Clear-UpdateProcess {
    if ($null -ne $script:Process) {
        try { $script:Process.Dispose() } catch {}
    }
    $script:Process = $null
    $script:StdoutTask = $null
    $script:StderrTask = $null
    $script:Action = $null
    $script:StartedAt = $null
}

function Start-UpdateOperation {
    param([Parameter(Mandatory)] [ValidateSet('Check', 'Update')] [string]$Action)

    if ($null -ne $script:Process) {
        return
    }

    Set-Busy $true
    $statusLabel.Text = if ($Action -eq 'Check') {
        'Проверяю accepted main...'
    }
    else {
        'Обновляю платформу. Не закрывайте это окно...'
    }

    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pwsh
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    foreach ($argument in @(
        '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', $UpdateScript, '-Action', $Action
    )) {
        $startInfo.ArgumentList.Add([string]$argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    if (-not $process.Start()) {
        $process.Dispose()
        Set-Busy $false
        throw "Не удалось запустить $Action."
    }

    $script:Process = $process
    $script:StdoutTask = $process.StandardOutput.ReadToEndAsync()
    $script:StderrTask = $process.StandardError.ReadToEndAsync()
    $script:Action = $Action
    $script:StartedAt = [datetimeoffset]::UtcNow
    $timer.Start()
}

$timer.add_Tick({
    if ($null -eq $script:Process) {
        $timer.Stop()
        return
    }

    if (-not $script:Process.HasExited) {
        if (([datetimeoffset]::UtcNow - $script:StartedAt).TotalSeconds -lt $OperationTimeoutSeconds) {
            return
        }
        try { $script:Process.Kill($true) } catch {}
        try { $script:Process.WaitForExit(5000) | Out-Null } catch {}
    }

    $timer.Stop()
    $exitCode = try { [int]$script:Process.ExitCode } catch { -1 }
    $stdout = try { $script:StdoutTask.GetAwaiter().GetResult().Trim() } catch { '' }
    $stderr = try { $script:StderrTask.GetAwaiter().GetResult().Trim() } catch { '' }
    $action = [string]$script:Action
    $result = $null
    if (-not [string]::IsNullOrWhiteSpace($stdout)) {
        try { $result = $stdout | ConvertFrom-Json -ErrorAction Stop } catch {}
    }

    Clear-UpdateProcess
    Set-Busy $false
    Refresh-UpdateView

    if ($exitCode -eq 0 -and $null -ne $result) {
        if ($action -eq 'Check') {
            if ([string]$result.status -eq 'current') {
                [System.Windows.Forms.MessageBox]::Show(
                    'Установлена последняя принятая версия main.',
                    'Chat Agent Platform',
                    [System.Windows.Forms.MessageBoxButtons]::OK,
                    [System.Windows.Forms.MessageBoxIcon]::Information
                ) | Out-Null
            }
        }
        elseif ([string]$result.status -in @('updated', 'current')) {
            [System.Windows.Forms.MessageBox]::Show(
                "Обновление завершено. Установлено: $(Short-Sha $result.installed_commit_sha).",
                'Chat Agent Platform',
                [System.Windows.Forms.MessageBoxButtons]::OK,
                [System.Windows.Forms.MessageBoxIcon]::Information
            ) | Out-Null
        }
    }
    elseif ($null -ne $result -and [string]$result.status -eq 'blocked') {
        [System.Windows.Forms.MessageBox]::Show(
            'Обновление остановлено: удалённый main не является fast-forward от установленной версии.',
            'Chat Agent Platform — обновление заблокировано',
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Warning
        ) | Out-Null
    }
    else {
        $detail = if ($null -ne $result -and -not [string]::IsNullOrWhiteSpace([string]$result.reason)) {
            [string]$result.reason
        }
        elseif (-not [string]::IsNullOrWhiteSpace($stderr)) {
            $stderr
        }
        else {
            "Операция завершилась с кодом $exitCode."
        }
        [System.Windows.Forms.MessageBox]::Show(
            $detail,
            'Chat Agent Platform — ошибка обновления',
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        ) | Out-Null
    }
})

$checkButton.add_Click({
    try { Start-UpdateOperation -Action Check }
    catch {
        Set-Busy $false
        [System.Windows.Forms.MessageBox]::Show(
            $_.Exception.Message,
            'Chat Agent Platform — ошибка',
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        ) | Out-Null
    }
})

$updateButton.add_Click({
    $answer = [System.Windows.Forms.MessageBox]::Show(
        'Установить последнюю принятую версию main? Работающий runtime будет перезапущен.',
        'Chat Agent Platform — обновление',
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    if ($answer -ne [System.Windows.Forms.DialogResult]::Yes) {
        return
    }
    try { Start-UpdateOperation -Action Update }
    catch {
        Set-Busy $false
        [System.Windows.Forms.MessageBox]::Show(
            $_.Exception.Message,
            'Chat Agent Platform — ошибка',
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        ) | Out-Null
    }
})

$logButton.add_Click({
    if (Test-Path -LiteralPath $UpdateLog -PathType Leaf) {
        Start-Process -FilePath 'notepad.exe' -ArgumentList "`"$UpdateLog`""
    }
})

$form.add_FormClosing({
    if ($null -ne $script:Process -and -not $script:Process.HasExited) {
        $_.Cancel = $true
        [System.Windows.Forms.MessageBox]::Show(
            'Дождитесь завершения текущей операции обновления.',
            'Chat Agent Platform',
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Information
        ) | Out-Null
    }
})

$form.add_FormClosed({
    $timer.Stop()
    $timer.Dispose()
    Clear-UpdateProcess
})

Refresh-UpdateView
[void]$form.ShowDialog()
