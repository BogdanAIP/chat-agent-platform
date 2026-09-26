[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{40}$')]
    [string]$ExpectedHead,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9a-fA-F]{40}$')]
    [string]$BaseSha,

    [Parameter(Mandatory = $true)]
    [ValidateRange(1, 2147483647)]
    [int]$PrNumber,

    [string]$Repository = 'BogdanAIP/chat-agent-platform',

    [ValidatePattern('^[0-9]+\.[0-9]+$')]
    [string]$ReviewSkillVersion = '1.1',

    [ValidateRange(60, 7200)]
    [int]$TimeoutSeconds = 1800
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$ExpectedHead = $ExpectedHead.ToLowerInvariant()
$BaseSha = $BaseSha.ToLowerInvariant()

$git = Get-Command git.exe -ErrorAction SilentlyContinue
if ($null -eq $git) { $git = Get-Command git -ErrorAction Stop }
$python = Get-Command python.exe -ErrorAction SilentlyContinue
if ($null -eq $python) { $python = Get-Command python -ErrorAction Stop }
$pwsh = Get-Command pwsh.exe -ErrorAction Stop

$actualHead = (& $git.Source -C $RepoRoot rev-parse HEAD).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or $actualHead -cne $ExpectedHead) {
    throw "EXACT_HEAD_MISMATCH expected=$ExpectedHead actual=$actualHead"
}
$dirty = (& $git.Source -C $RepoRoot status --porcelain=v1 --untracked-files=all) -join [Environment]::NewLine
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect qualification source state.' }
if (-not [string]::IsNullOrWhiteSpace($dirty)) {
    throw 'Qualification source must be clean before reviewer task preparation.'
}

if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    throw 'LOCALAPPDATA is required for automatic reviewer qualification.'
}
$qualificationId = '{0}-pr{1}-{2}' -f $ExpectedHead.Substring(0, 12), $PrNumber, ([guid]::NewGuid().ToString('N').Substring(0, 8))
$qualificationRoot = Join-Path $env:LOCALAPPDATA "ChatAgentPlatform\state\automatic-reviewer-qualification\$qualificationId"
$reviewerStateRoot = Join-Path $qualificationRoot 'review-state'
$outputDir = Join-Path $qualificationRoot 'adapter'
New-Item -ItemType Directory -Force -Path $reviewerStateRoot, $outputDir | Out-Null

$adapter = Join-Path $RepoRoot 'scripts\automatic-reviewer-qualification.py'
$launcher = Join-Path $RepoRoot 'scripts\launch-chatgpt-temporary-worker.ps1'
foreach ($required in @($adapter, $launcher)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Qualification asset is missing: $required"
    }
}

$identityArgs = @(
    '--repository', $Repository,
    '--pr-number', [string]$PrNumber,
    '--base-sha', $BaseSha,
    '--head-sha', $ExpectedHead,
    '--review-skill', 'code-review',
    '--review-skill-version', $ReviewSkillVersion,
    '--reviewer-state-root', $reviewerStateRoot
)

$prepareRaw = & $python.Source $adapter prepare @identityArgs --output-dir $outputDir
if ($LASTEXITCODE -ne 0) {
    throw "Reviewer qualification prepare failed: $($prepareRaw | Out-String)"
}
$prepare = $prepareRaw | Out-String | ConvertFrom-Json
if (
    [string]$prepare.worker_kind -cne 'code-review' -or
    [string]$prepare.worker_profile -cne 'fresh_readonly_worker_v1' -or
    [string]$prepare.result_contract_id -cne 'review_result_v1'
) {
    throw 'Reviewer qualification identity drifted from the accepted contract.'
}
if ([string]$prepare.task_sha256 -notmatch '^[0-9a-f]{64}$') {
    throw 'Reviewer qualification task digest is invalid.'
}

Write-Host "CAP_REVIEW_QUALIFICATION_ROOT=$qualificationRoot" -ForegroundColor Cyan
Write-Host "CAP_REVIEW_TASK_SHA256=$($prepare.task_sha256)"
Write-Host 'CAP_REVIEW_TEMPORARY_MODE=reviewer-only'
Write-Host 'CAP_REVIEW_MANUAL_SEND_REQUIRED=False'

$launcherArgs = @(
    '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass',
    '-File', $launcher,
    '-TaskFile', [string]$prepare.task_file,
    '-ExpectedHead', $ExpectedHead,
    '-ParentTaskId', [string]$prepare.parent_task_id,
    '-SubgoalId', [string]$prepare.subgoal_id,
    '-WorkerKind', [string]$prepare.worker_kind,
    '-ResultContractId', [string]$prepare.result_contract_id,
    '-ReviewerIdentityFile', [string]$prepare.reviewer_identity_file,
    '-ReviewerStateRoot', $reviewerStateRoot,
    '-TimeoutSeconds', [string]$TimeoutSeconds
)
& $pwsh.Source @launcherArgs
if ($LASTEXITCODE -ne 0) {
    throw "Generic Temporary reviewer qualification failed with exit code $LASTEXITCODE."
}

$settleRaw = & $python.Source $adapter settle @identityArgs
if ($LASTEXITCODE -ne 0) {
    throw "Reviewer result settlement failed: $($settleRaw | Out-String)"
}
$settled = $settleRaw | Out-String | ConvertFrom-Json
if (
    [string]$settled.status -notin @('recorded', 'already_recorded') -or
    [string]$settled.result_state -cne 'automatic-result-recorded' -or
    [string]$settled.result_source -cne 'automatic'
) {
    throw "Reviewer result did not close automatically: $($settled | ConvertTo-Json -Compress -Depth 8)"
}
if ([string]$settled.result -notmatch '(?m)^REVIEW_RESULT_V1\s*$') {
    throw 'Reviewer result settlement did not retain a valid REVIEW_RESULT_V1 payload.'
}

$finalHead = (& $git.Source -C $RepoRoot rev-parse HEAD).Trim().ToLowerInvariant()
$finalDirty = (& $git.Source -C $RepoRoot status --porcelain=v1 --untracked-files=all) -join [Environment]::NewLine
if (
    $LASTEXITCODE -ne 0 -or
    $finalHead -cne $ExpectedHead -or
    -not [string]::IsNullOrWhiteSpace($finalDirty)
) {
    throw 'Qualification source changed before final reviewer settlement.'
}

Write-Host 'CAP_AUTOMATIC_REVIEWER_QUALIFICATION=PASS' -ForegroundColor Green
Write-Host "CAP_AUTOMATIC_REVIEWER_RESULT_STATE=$($settled.result_state)"
Write-Host "CAP_AUTOMATIC_REVIEWER_RESULT_SOURCE=$($settled.result_source)"
Write-Host "CAP_AUTOMATIC_REVIEWER_EXACT_HEAD=$ExpectedHead"
