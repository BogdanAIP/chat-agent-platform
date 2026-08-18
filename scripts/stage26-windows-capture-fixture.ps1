[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$StatePath,
    [Parameter(Mandatory = $true)][string]$DonePath,
    [Parameter(Mandatory = $true)][string]$RecorderReadyPath,
    [Parameter(Mandatory = $true)][string]$ClosePath,
    [string]$WindowTitle = 'Chat Agent Platform Stage 26.1B Capture Fixture'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

$stateDirectory = Split-Path -Parent $StatePath
New-Item -ItemType Directory -Force -Path $stateDirectory | Out-Null

$state = [ordered]@{
    schema_version = 1
    ready = $false
    recorder_ready = $false
    start_clicked = $false
    text_ok = $false
    enter_pressed = $false
    scroll_seen = $false
    finish_clicked = $false
    text_value = ''
    window_title = $WindowTitle
    fixture_pid = $PID
}

function Save-State {
    $state | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $StatePath -Encoding utf8
}

function Update-Ui {
    if (-not $state.recorder_ready) {
        $statusLabel.Text = 'Подготовка записи… Не нажимайте элементы до появления READY.'
        return
    }

    $parts = @(
        "1 Click=$($state.start_clicked)",
        "2 Text=$($state.text_ok)",
        "3 Enter=$($state.enter_pressed)",
        "4 Scroll=$($state.scroll_seen)"
    )
    $statusLabel.Text = 'READY | ' + ($parts -join ' | ')
    $finishButton.Enabled = [bool](
        $state.start_clicked -and
        $state.text_ok -and
        $state.enter_pressed -and
        $state.scroll_seen
    )
}

function Mark-Scroll {
    if (-not $state.recorder_ready) { return }
    $state.scroll_seen = $true
    Save-State
    Update-Ui
}

$form = New-Object System.Windows.Forms.Form
$form.Text = $WindowTitle
$form.Name = 'Stage26CaptureFixtureWindow'
$form.AccessibleName = 'Stage 26 capture qualification fixture'
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.ClientSize = New-Object System.Drawing.Size(720, 560)
$form.TopMost = $true

$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Location = New-Object System.Drawing.Point(24, 18)
$titleLabel.Size = New-Object System.Drawing.Size(670, 52)
$titleLabel.Font = New-Object System.Drawing.Font('Segoe UI', 14, [System.Drawing.FontStyle]::Bold)
$titleLabel.Text = 'Stage 26.1B — безопасный тест записи действий Windows'
$form.Controls.Add($titleLabel)

$helpLabel = New-Object System.Windows.Forms.Label
$helpLabel.Location = New-Object System.Drawing.Point(24, 72)
$helpLabel.Size = New-Object System.Drawing.Size(670, 70)
$helpLabel.Font = New-Object System.Drawing.Font('Segoe UI', 9)
$helpLabel.Text = "Работайте только в этом окне. Выполните шаги сверху вниз. Никакие рабочие файлы или приложения не используются. После READY: нажмите кнопку, введите CAPTURE_OK, нажмите Enter, прокрутите список колесом мыши и завершите тест."
$form.Controls.Add($helpLabel)

$startButton = New-Object System.Windows.Forms.Button
$startButton.Location = New-Object System.Drawing.Point(24, 150)
$startButton.Size = New-Object System.Drawing.Size(310, 42)
$startButton.Text = '1. Нажмите эту кнопку'
$startButton.Name = 'Stage26StartButton'
$startButton.AccessibleName = 'Stage 26 start button'
$startButton.Enabled = $false
$startButton.Add_Click({
    if (-not $state.recorder_ready) { return }
    $state.start_clicked = $true
    Save-State
    Update-Ui
})
$form.Controls.Add($startButton)

$inputLabel = New-Object System.Windows.Forms.Label
$inputLabel.Location = New-Object System.Drawing.Point(24, 210)
$inputLabel.Size = New-Object System.Drawing.Size(310, 22)
$inputLabel.Text = '2. Введите точно: CAPTURE_OK'
$form.Controls.Add($inputLabel)

$inputBox = New-Object System.Windows.Forms.TextBox
$inputBox.Location = New-Object System.Drawing.Point(24, 235)
$inputBox.Size = New-Object System.Drawing.Size(310, 30)
$inputBox.Name = 'Stage26CaptureInput'
$inputBox.AccessibleName = 'Stage 26 capture input'
$inputBox.Enabled = $false
$inputBox.Add_TextChanged({
    if (-not $state.recorder_ready) { return }
    $state.text_value = $inputBox.Text
    $state.text_ok = ($inputBox.Text -ceq 'CAPTURE_OK')
    Save-State
    Update-Ui
})
$inputBox.Add_KeyDown({
    param($sender, $eventArgs)
    if (-not $state.recorder_ready) { return }
    if ($eventArgs.KeyCode -eq [System.Windows.Forms.Keys]::Enter) {
        $state.enter_pressed = $true
        Save-State
        Update-Ui
        # Move focus without synthesizing any input so the next physical wheel
        # event is delivered to the qualification list deterministically.
        [void]$listBox.Focus()
        $eventArgs.SuppressKeyPress = $true
    }
})
$form.Controls.Add($inputBox)

$enterLabel = New-Object System.Windows.Forms.Label
$enterLabel.Location = New-Object System.Drawing.Point(24, 273)
$enterLabel.Size = New-Object System.Drawing.Size(310, 22)
$enterLabel.Text = '3. В этом поле нажмите Enter'
$form.Controls.Add($enterLabel)

$scrollLabel = New-Object System.Windows.Forms.Label
$scrollLabel.Location = New-Object System.Drawing.Point(370, 150)
$scrollLabel.Size = New-Object System.Drawing.Size(320, 38)
$scrollLabel.Text = '4. После Enter прокрутите список колесом вниз'
$form.Controls.Add($scrollLabel)

$listBox = New-Object System.Windows.Forms.ListBox
$listBox.Location = New-Object System.Drawing.Point(370, 195)
$listBox.Size = New-Object System.Drawing.Size(320, 250)
$listBox.Name = 'Stage26ScrollList'
$listBox.AccessibleName = 'Stage 26 scroll list'
$listBox.Enabled = $false
for ($i = 1; $i -le 60; $i++) {
    [void]$listBox.Items.Add(('Qualification row {0:00}' -f $i))
}
$listBox.Add_MouseWheel({ Mark-Scroll })
$form.Add_MouseWheel({ Mark-Scroll })
$form.Controls.Add($listBox)

$finishButton = New-Object System.Windows.Forms.Button
$finishButton.Location = New-Object System.Drawing.Point(370, 458)
$finishButton.Size = New-Object System.Drawing.Size(320, 44)
$finishButton.Text = '5. Завершить тест'
$finishButton.Name = 'Stage26FinishButton'
$finishButton.AccessibleName = 'Stage 26 finish button'
$finishButton.Enabled = $false
$finishButton.Add_Click({
    if (-not $finishButton.Enabled) { return }
    $state.finish_clicked = $true
    Save-State
    Set-Content -LiteralPath $DonePath -Value 'DONE' -Encoding ascii
    $finishButton.Enabled = $false
    $statusLabel.Text = 'DONE — запись завершается автоматически. Окно можно не трогать.'
})
$form.Controls.Add($finishButton)

$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Location = New-Object System.Drawing.Point(24, 515)
$statusLabel.Size = New-Object System.Drawing.Size(666, 28)
$statusLabel.Font = New-Object System.Drawing.Font('Consolas', 9)
$form.Controls.Add($statusLabel)

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 200
$timer.Add_Tick({
    if (-not $state.recorder_ready -and (Test-Path -LiteralPath $RecorderReadyPath -PathType Leaf)) {
        $state.recorder_ready = $true
        $startButton.Enabled = $true
        $inputBox.Enabled = $true
        $listBox.Enabled = $true
        $form.TopMost = $true
        $form.Activate()
        Save-State
        Update-Ui
    }
    if (Test-Path -LiteralPath $ClosePath -PathType Leaf) {
        $timer.Stop()
        $form.Close()
    }
})

$form.Add_Shown({
    $state.ready = $true
    Save-State
    Update-Ui
    $timer.Start()
})

$form.Add_FormClosing({
    if (-not (Test-Path -LiteralPath $ClosePath -PathType Leaf) -and -not $state.finish_clicked) {
        $state['closed_early'] = $true
        Save-State
    }
})

Save-State
[void]$form.ShowDialog()
$timer.Stop()
$timer.Dispose()
$form.Dispose()
