[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$StatePath,
    [Parameter(Mandatory = $true)][string]$RecorderReadyPath,
    [Parameter(Mandatory = $true)][string]$ClosePath,
    [Parameter(Mandatory = $true)][ValidateRange(3, 60)][int]$TotalCycles,
    [string]$WindowTitle = 'Chat Agent Platform Stage 26.1D Hot Runtime Fixture'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$stateDirectory = Split-Path -Parent $StatePath
New-Item -ItemType Directory -Force -Path $stateDirectory | Out-Null

function Get-ExpectedText {
    param([int]$Iteration)
    return ('HOT_{0:00}' -f $Iteration)
}

$state = [ordered]@{
    schema_version = 1
    ready = $false
    recorder_ready = $false
    cycle_ready = $false
    benchmark_done = $false
    current_iteration = 1
    total_cycles = $TotalCycles
    completed_cycles = 0
    expected_text = (Get-ExpectedText -Iteration 1)
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
    $state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $StatePath -Encoding utf8
}

function Update-Ui {
    if (-not $state.recorder_ready) {
        $statusLabel.Text = 'Подготовка benchmark runtime...'
        return
    }
    if ($state.benchmark_done) {
        $statusLabel.Text = "DONE | cycles=$($state.completed_cycles)/$($state.total_cycles)"
        return
    }
    $statusLabel.Text = (
        "HOT {0}/{1} | Start={2} | Text={3} | Enter={4} | Scroll={5}" -f
        $state.current_iteration,
        $state.total_cycles,
        $state.start_clicked,
        $state.text_ok,
        $state.enter_pressed,
        $state.scroll_seen
    )
    $finishButton.Enabled = [bool](
        $state.cycle_ready -and
        $state.start_clicked -and
        $state.text_ok -and
        $state.enter_pressed -and
        $state.scroll_seen
    )
}

function Reset-Cycle {
    $state.cycle_ready = $false
    $state.start_clicked = $false
    $state.text_ok = $false
    $state.enter_pressed = $false
    $state.scroll_seen = $false
    $state.finish_clicked = $false
    $state.text_value = ''
    $state.expected_text = Get-ExpectedText -Iteration ([int]$state.current_iteration)

    $inputBox.Text = ''
    $listBox.ClearSelected()
    if ($listBox.Items.Count -gt 0) { $listBox.TopIndex = 0 }

    $startButton.Enabled = $true
    $inputBox.Enabled = $true
    $listBox.Enabled = $true
    $finishButton.Enabled = $false
    $state.cycle_ready = $true
    Save-State
    Update-Ui
}

function Mark-Scroll {
    if (-not $state.cycle_ready -or -not $state.recorder_ready) { return }
    $state.scroll_seen = $true
    Save-State
    Update-Ui
}

$form = New-Object System.Windows.Forms.Form
$form.Text = $WindowTitle
$form.Name = 'Stage26HotRuntimeFixtureWindow'
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
$titleLabel.Text = 'Stage 26.1D — прогретый Windows executor benchmark'
$form.Controls.Add($titleLabel)

$helpLabel = New-Object System.Windows.Forms.Label
$helpLabel.Location = New-Object System.Drawing.Point(24, 72)
$helpLabel.Size = New-Object System.Drawing.Size(670, 70)
$helpLabel.Font = New-Object System.Drawing.Font('Segoe UI', 9)
$helpLabel.Text = 'Ничего не нажимайте. Один и тот же executor и fixture выполнят несколько циклов без перезапуска между действиями.'
$form.Controls.Add($helpLabel)

$startButton = New-Object System.Windows.Forms.Button
$startButton.Location = New-Object System.Drawing.Point(24, 150)
$startButton.Size = New-Object System.Drawing.Size(310, 42)
$startButton.Text = '1. Benchmark start'
$startButton.Name = 'Stage26StartButton'
$startButton.AccessibleName = 'Stage 26 start button'
$startButton.Enabled = $false
$startButton.Add_Click({
    if (-not $state.cycle_ready -or -not $state.recorder_ready) { return }
    $state.start_clicked = $true
    Save-State
    Update-Ui
})
$form.Controls.Add($startButton)

$inputLabel = New-Object System.Windows.Forms.Label
$inputLabel.Location = New-Object System.Drawing.Point(24, 210)
$inputLabel.Size = New-Object System.Drawing.Size(310, 22)
$inputLabel.Text = '2. Executor types current HOT_nn value'
$form.Controls.Add($inputLabel)

$inputBox = New-Object System.Windows.Forms.TextBox
$inputBox.Location = New-Object System.Drawing.Point(24, 235)
$inputBox.Size = New-Object System.Drawing.Size(310, 30)
$inputBox.Name = 'Stage26CaptureInput'
$inputBox.AccessibleName = 'Stage 26 capture input'
$inputBox.Enabled = $false
$inputBox.Add_TextChanged({
    if (-not $state.cycle_ready -or -not $state.recorder_ready) { return }
    $state.text_value = $inputBox.Text
    $state.text_ok = ($inputBox.Text -ceq [string]$state.expected_text)
    Save-State
    Update-Ui
})
$inputBox.Add_KeyDown({
    param($sender, $eventArgs)
    if (-not $state.cycle_ready -or -not $state.recorder_ready) { return }
    if ($eventArgs.KeyCode -eq [System.Windows.Forms.Keys]::Enter) {
        $state.enter_pressed = $true
        Save-State
        Update-Ui
        [void]$listBox.Focus()
        $eventArgs.SuppressKeyPress = $true
    }
})
$form.Controls.Add($inputBox)

$enterLabel = New-Object System.Windows.Forms.Label
$enterLabel.Location = New-Object System.Drawing.Point(24, 273)
$enterLabel.Size = New-Object System.Drawing.Size(310, 22)
$enterLabel.Text = '3. Guarded Enter'
$form.Controls.Add($enterLabel)

$scrollLabel = New-Object System.Windows.Forms.Label
$scrollLabel.Location = New-Object System.Drawing.Point(370, 150)
$scrollLabel.Size = New-Object System.Drawing.Size(320, 38)
$scrollLabel.Text = '4. Guarded list click + scroll'
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
$finishButton.Text = '5. Finish benchmark cycle'
$finishButton.Name = 'Stage26FinishButton'
$finishButton.AccessibleName = 'Stage 26 finish button'
$finishButton.Enabled = $false
$finishButton.Add_Click({
    if (-not $finishButton.Enabled -or -not $state.cycle_ready) { return }
    $state.finish_clicked = $true
    $state.cycle_ready = $false
    $state.completed_cycles = [int]$state.completed_cycles + 1
    Save-State

    if ([int]$state.completed_cycles -ge [int]$state.total_cycles) {
        $state.benchmark_done = $true
        $startButton.Enabled = $false
        $inputBox.Enabled = $false
        $listBox.Enabled = $false
        $finishButton.Enabled = $false
        Save-State
        Update-Ui
        return
    }

    $state.current_iteration = [int]$state.current_iteration + 1
    Reset-Cycle
})
$form.Controls.Add($finishButton)

$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Location = New-Object System.Drawing.Point(24, 515)
$statusLabel.Size = New-Object System.Drawing.Size(666, 28)
$statusLabel.Font = New-Object System.Drawing.Font('Consolas', 9)
$form.Controls.Add($statusLabel)

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 100
$timer.Add_Tick({
    if (-not $state.recorder_ready -and (Test-Path -LiteralPath $RecorderReadyPath -PathType Leaf)) {
        $state.recorder_ready = $true
        $form.TopMost = $true
        $form.Activate()
        Reset-Cycle
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
    if (-not (Test-Path -LiteralPath $ClosePath -PathType Leaf) -and -not $state.benchmark_done) {
        $state['closed_early'] = $true
        Save-State
    }
})

Save-State
[void]$form.ShowDialog()
$timer.Stop()
$timer.Dispose()
$form.Dispose()
