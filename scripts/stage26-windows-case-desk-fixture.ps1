[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SeedPath,
    [Parameter(Mandatory = $true)][string]$StatePath,
    [Parameter(Mandatory = $true)][string]$AuditPath,
    [Parameter(Mandatory = $true)][string]$ReadyPath,
    [Parameter(Mandatory = $true)][string]$ClosePath,
    [Parameter(Mandatory = $true)][ValidatePattern('^[A-F0-9]{8}$')][string]$RunId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content
    )
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function Append-Utf8NoBom {
    param([Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][string]$Content)
    [System.IO.File]::AppendAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function Get-TextSha256 {
    param([AllowEmptyString()][string]$Text)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes([string]$Text)
    $hash = [System.Security.Cryptography.SHA256]::HashData($bytes)
    return [Convert]::ToHexString($hash).ToLowerInvariant()
}

function Copy-CaseRecord {
    param([Parameter(Mandatory = $true)]$Case)
    return [ordered]@{
        id = [string]$Case.id
        client = [string]$Case.client
        status = [string]$Case.status
        notes = @($Case.notes | ForEach-Object { [string]$_ })
    }
}

$seed = Get-Content -LiteralPath $SeedPath -Raw -Encoding utf8 | ConvertFrom-Json
if ([int]$seed.schema_version -ne 1 -or [string]$seed.run_id -ne $RunId) {
    throw 'Case Desk seed contract mismatch.'
}
$cases = @($seed.cases | ForEach-Object { Copy-CaseRecord -Case $_ })
if ($cases.Count -lt 3 -or $cases.Count -gt 8) {
    throw 'Case Desk requires 3..8 cases.'
}
$caseIds = @($cases | ForEach-Object { [string]$_.id })
if ((@($caseIds | Sort-Object -Unique)).Count -ne $caseIds.Count) {
    throw 'Case Desk case ids must be unique.'
}
foreach ($caseId in $caseIds) {
    if ($caseId -notmatch "^CASE-$RunId-[0-9]{4}$") {
        throw "Case Desk case id is outside the active run: $caseId"
    }
}

$stateDirectory = Split-Path -Parent $StatePath
New-Item -ItemType Directory -Force -Path $stateDirectory | Out-Null
Write-Utf8NoBom -Path $AuditPath -Content ''

$selectedCaseId = $null
$draftStatus = $null
$saveCount = 0
$summaryLabels = @{}

function Get-CaseById {
    param([Parameter(Mandatory = $true)][string]$CaseId)
    $matches = @($cases | Where-Object { [string]$_.id -ceq $CaseId })
    if ($matches.Count -ne 1) { throw "Case id is not unique: $CaseId" }
    return $matches[0]
}

function Get-StateToken {
    $selected = if ($null -eq $selectedCaseId) { 'NONE' } else { [string]$selectedCaseId }
    $status = if ($null -eq $draftStatus) { 'NONE' } else { [string]$draftStatus }
    $noteHash = Get-TextSha256 -Text ([string]$noteBox.Text)
    return "STATE|selected=$selected|draft_status=$status|note_sha256=$noteHash|saved=$saveCount"
}

function Get-CaseSummary {
    param([Parameter(Mandatory = $true)]$Case)
    return "CASESTATE|id=$([string]$Case.id)|status=$([string]$Case.status)|notes=$(@($Case.notes).Count)"
}

function Save-State {
    $state = [ordered]@{
        schema_version = 1
        run_id = $RunId
        fixture_pid = $PID
        ready = [bool]$form.Visible
        selected_case_id = if ($null -eq $selectedCaseId) { $null } else { [string]$selectedCaseId }
        draft_status = if ($null -eq $draftStatus) { $null } else { [string]$draftStatus }
        draft_note_sha256 = Get-TextSha256 -Text ([string]$noteBox.Text)
        save_count = $saveCount
        cases = @($cases | ForEach-Object { Copy-CaseRecord -Case $_ })
        updated_at = (Get-Date).ToUniversalTime().ToString('o')
    }
    Write-Utf8NoBom -Path $StatePath -Content (($state | ConvertTo-Json -Depth 8) + "`n")
}

function Update-StateToken {
    $token = Get-StateToken
    $stateTokenLabel.Text = $token
    $stateTokenLabel.AccessibleName = $token
}

function Update-SelectedDetails {
    if ($null -eq $selectedCaseId) {
        $clientValue.Text = '—'
        $statusValue.Text = '—'
        return
    }
    $case = Get-CaseById -CaseId $selectedCaseId
    $clientValue.Text = [string]$case.client
    $statusValue.Text = [string]$case.status
}

function Update-SaveEnabled {
    $saveButton.Enabled = [bool](
        $null -ne $selectedCaseId -and
        $null -ne $draftStatus -and
        -not [string]::IsNullOrEmpty([string]$noteBox.Text)
    )
}

$form = New-Object System.Windows.Forms.Form
$form.Text = "Case Desk — Windows L3 $RunId"
$form.Name = 'Stage26WindowsCaseDesk'
$form.AccessibleName = "Case Desk $RunId"
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.ClientSize = New-Object System.Drawing.Size(920, 650)
$form.TopMost = $true

$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Location = New-Object System.Drawing.Point(20, 15)
$titleLabel.Size = New-Object System.Drawing.Size(875, 34)
$titleLabel.Font = New-Object System.Drawing.Font('Segoe UI', 15, [System.Drawing.FontStyle]::Bold)
$titleLabel.Text = 'Case Desk — обработка клиентских дел'
$titleLabel.AccessibleName = 'Case Desk heading'
$form.Controls.Add($titleLabel)

$instructionLabel = New-Object System.Windows.Forms.Label
$instructionLabel.Location = New-Object System.Drawing.Point(20, 52)
$instructionLabel.Size = New-Object System.Drawing.Size(875, 42)
$instructionLabel.Text = 'Выберите точное дело, добавьте новую внутреннюю заметку, задайте статус и сохраните. Похожие идентификаторы являются разными делами.'
$instructionLabel.AccessibleName = 'Case Desk instructions'
$form.Controls.Add($instructionLabel)

$caseListLabel = New-Object System.Windows.Forms.Label
$caseListLabel.Location = New-Object System.Drawing.Point(20, 105)
$caseListLabel.Size = New-Object System.Drawing.Size(250, 24)
$caseListLabel.Text = 'Дела'
$caseListLabel.AccessibleName = 'Cases'
$form.Controls.Add($caseListLabel)

$caseList = New-Object System.Windows.Forms.ListBox
$caseList.Location = New-Object System.Drawing.Point(20, 132)
$caseList.Size = New-Object System.Drawing.Size(300, 190)
$caseList.Name = 'Stage26CaseList'
$caseList.AccessibleName = 'Case list'
foreach ($case in $cases) { [void]$caseList.Items.Add([string]$case.id) }
$form.Controls.Add($caseList)

$clientLabel = New-Object System.Windows.Forms.Label
$clientLabel.Location = New-Object System.Drawing.Point(350, 112)
$clientLabel.Size = New-Object System.Drawing.Size(95, 22)
$clientLabel.Text = 'Клиент:'
$form.Controls.Add($clientLabel)

$clientValue = New-Object System.Windows.Forms.Label
$clientValue.Location = New-Object System.Drawing.Point(450, 112)
$clientValue.Size = New-Object System.Drawing.Size(430, 22)
$clientValue.Text = '—'
$clientValue.AccessibleName = 'Selected client'
$form.Controls.Add($clientValue)

$currentStatusLabel = New-Object System.Windows.Forms.Label
$currentStatusLabel.Location = New-Object System.Drawing.Point(350, 142)
$currentStatusLabel.Size = New-Object System.Drawing.Size(95, 22)
$currentStatusLabel.Text = 'Статус:'
$form.Controls.Add($currentStatusLabel)

$statusValue = New-Object System.Windows.Forms.Label
$statusValue.Location = New-Object System.Drawing.Point(450, 142)
$statusValue.Size = New-Object System.Drawing.Size(430, 22)
$statusValue.Text = '—'
$statusValue.AccessibleName = 'Current case status'
$form.Controls.Add($statusValue)

$noteLabel = New-Object System.Windows.Forms.Label
$noteLabel.Location = New-Object System.Drawing.Point(350, 182)
$noteLabel.Size = New-Object System.Drawing.Size(300, 22)
$noteLabel.Text = 'Новая внутренняя заметка'
$form.Controls.Add($noteLabel)

$noteBox = New-Object System.Windows.Forms.TextBox
$noteBox.Location = New-Object System.Drawing.Point(350, 208)
$noteBox.Size = New-Object System.Drawing.Size(530, 30)
$noteBox.Name = 'Stage26NewCaseNote'
$noteBox.AccessibleName = 'New case note'
$noteBox.MaxLength = 512
$form.Controls.Add($noteBox)

$approvedButton = New-Object System.Windows.Forms.Button
$approvedButton.Location = New-Object System.Drawing.Point(350, 258)
$approvedButton.Size = New-Object System.Drawing.Size(250, 42)
$approvedButton.Name = 'Stage26StatusApproved'
$approvedButton.Text = 'Статус: Approved'
$approvedButton.AccessibleName = 'Set status Approved'
$form.Controls.Add($approvedButton)

$reviewButton = New-Object System.Windows.Forms.Button
$reviewButton.Location = New-Object System.Drawing.Point(630, 258)
$reviewButton.Size = New-Object System.Drawing.Size(250, 42)
$reviewButton.Name = 'Stage26StatusNeedsReview'
$reviewButton.Text = 'Статус: Needs Review'
$reviewButton.AccessibleName = 'Set status Needs Review'
$form.Controls.Add($reviewButton)

$saveButton = New-Object System.Windows.Forms.Button
$saveButton.Location = New-Object System.Drawing.Point(350, 316)
$saveButton.Size = New-Object System.Drawing.Size(530, 48)
$saveButton.Name = 'Stage26SaveCase'
$saveButton.Text = 'Сохранить дело'
$saveButton.AccessibleName = 'Save case'
$saveButton.Enabled = $false
$form.Controls.Add($saveButton)

$summaryHeading = New-Object System.Windows.Forms.Label
$summaryHeading.Location = New-Object System.Drawing.Point(20, 345)
$summaryHeading.Size = New-Object System.Drawing.Size(860, 24)
$summaryHeading.Text = 'Проверяемые сводки дел'
$summaryHeading.AccessibleName = 'Case summaries'
$form.Controls.Add($summaryHeading)

$summaryY = 375
foreach ($case in $cases) {
    $summary = Get-CaseSummary -Case $case
    $label = New-Object System.Windows.Forms.Label
    $label.Location = New-Object System.Drawing.Point(20, $summaryY)
    $label.Size = New-Object System.Drawing.Size(860, 22)
    $label.Font = New-Object System.Drawing.Font('Consolas', 9)
    $label.Text = $summary
    $label.AccessibleName = $summary
    $form.Controls.Add($label)
    $summaryLabels[[string]$case.id] = $label
    $summaryY += 25
}

$stateTokenLabel = New-Object System.Windows.Forms.Label
$stateTokenLabel.Location = New-Object System.Drawing.Point(20, 565)
$stateTokenLabel.Size = New-Object System.Drawing.Size(860, 28)
$stateTokenLabel.Font = New-Object System.Drawing.Font('Consolas', 8)
$form.Controls.Add($stateTokenLabel)

$runLabel = New-Object System.Windows.Forms.Label
$runLabel.Location = New-Object System.Drawing.Point(20, 604)
$runLabel.Size = New-Object System.Drawing.Size(860, 22)
$runLabel.Text = "Run $RunId"
$runLabel.AccessibleName = "Run $RunId"
$form.Controls.Add($runLabel)

$caseList.Add_SelectedIndexChanged({
    if ($caseList.SelectedIndex -lt 0) { return }
    $selectedCaseId = [string]$caseList.SelectedItem
    $draftStatus = $null
    $noteBox.Text = ''
    Update-SelectedDetails
    Update-StateToken
    Update-SaveEnabled
    Save-State
})

$noteBox.Add_TextChanged({
    Update-StateToken
    Update-SaveEnabled
    Save-State
})

$approvedButton.Add_Click({
    if ($null -eq $selectedCaseId) { return }
    $draftStatus = 'Approved'
    Update-StateToken
    Update-SaveEnabled
    Save-State
})

$reviewButton.Add_Click({
    if ($null -eq $selectedCaseId) { return }
    $draftStatus = 'Needs Review'
    Update-StateToken
    Update-SaveEnabled
    Save-State
})

$saveButton.Add_Click({
    if (-not $saveButton.Enabled -or $null -eq $selectedCaseId -or $null -eq $draftStatus) { return }
    $case = Get-CaseById -CaseId $selectedCaseId
    $before = Copy-CaseRecord -Case $case

    $case.status = [string]$draftStatus
    $case.notes = @($case.notes) + @([string]$noteBox.Text)
    $saveCount += 1

    $after = Copy-CaseRecord -Case $case
    $event = [ordered]@{
        schema_version = 1
        run_id = $RunId
        event = 'case_saved'
        save_index = $saveCount
        case_id = [string]$selectedCaseId
        before = $before
        after = $after
        saved_at = (Get-Date).ToUniversalTime().ToString('o')
    }
    Append-Utf8NoBom -Path $AuditPath -Content (($event | ConvertTo-Json -Depth 8 -Compress) + "`n")

    $summary = Get-CaseSummary -Case $case
    $summaryLabel = $summaryLabels[[string]$case.id]
    $summaryLabel.Text = $summary
    $summaryLabel.AccessibleName = $summary
    Update-SelectedDetails
    Update-StateToken
    Update-SaveEnabled
    Save-State
})

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 100
$timer.Add_Tick({
    if (Test-Path -LiteralPath $ClosePath -PathType Leaf) {
        $timer.Stop()
        $form.Close()
    }
})

$form.Add_Shown({
    Update-SelectedDetails
    Update-StateToken
    Update-SaveEnabled
    Save-State
    Write-Utf8NoBom -Path $ReadyPath -Content "READY`n"
    $form.TopMost = $true
    $form.Activate()
    $timer.Start()
})

[void][System.Windows.Forms.Application]::Run($form)