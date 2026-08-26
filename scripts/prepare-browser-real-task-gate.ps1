param(
  [string]$SourceRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$ExpectedHead = '',
  [switch]$SkipBootstrap
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Write-Utf8NoBom {
  param([string]$Path, [string]$Content)
  [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path
$actualHead = (& git -C $SourceRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or -not $actualHead) { throw 'Unable to resolve source HEAD.' }
if ($ExpectedHead -and $actualHead -ne $ExpectedHead) {
  throw "EXACT_HEAD_MISMATCH expected=$ExpectedHead actual=$actualHead"
}
if (-not $ExpectedHead) { $ExpectedHead = $actualHead }

$node = (Get-Command node -ErrorAction Stop).Source
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$nonce = ([guid]::NewGuid().ToString('N').Substring(0, 8)).ToUpperInvariant()
$qualificationRoot = Join-Path $env:LOCALAPPDATA "ChatAgentPlatform\stage26\stage26-3b-browser-real-task-$stamp-$nonce"
$workspaceRoot = Join-Path $qualificationRoot 'workspace'
$fixtureRoot = Join-Path $qualificationRoot 'fixture-state'
New-Item -ItemType Directory -Force -Path $workspaceRoot, $fixtureRoot | Out-Null

$targetId = "CASE-$nonce-4821"
$decoyA = "CASE-$nonce-4827"
$decoyB = "CASE-$nonce-4812"
$oldAddress = "10 Old Harbor Road $nonce"
$newAddress = "18 New Harbor Road $nonce"
$requiredComment = "Reviewed by agent $nonce"

$seed = [ordered]@{
  target_id = $targetId
  expected = [ordered]@{
    address = $newAddress
    status = 'Approved'
    comment = $requiredComment
  }
  cases = @(
    [ordered]@{ id = $targetId; client = 'Marina Volkova'; status = 'Pending'; address = $oldAddress; comment = 'Priority customer' },
    [ordered]@{ id = $decoyA; client = 'Marina Volkova'; status = 'Pending'; address = "44 Pine Street $nonce"; comment = 'Waiting for customer' },
    [ordered]@{ id = $decoyB; client = 'Maria Volkova'; status = 'Approved'; address = "7 Lake Avenue $nonce"; comment = 'Already reviewed' }
  )
}

$seedPath = Join-Path $fixtureRoot 'fixture-seed.json'
Write-Utf8NoBom -Path $seedPath -Content (($seed | ConvertTo-Json -Depth 8) + "`n")

$serverScript = Join-Path $SourceRoot 'tests\fixtures\browser_real_task_server.mjs'
if (-not (Test-Path -LiteralPath $serverScript -PathType Leaf)) { throw "Fixture server missing: $serverScript" }
$stdout = Join-Path $fixtureRoot 'fixture-stdout.log'
$stderr = Join-Path $fixtureRoot 'fixture-stderr.log'
$process = Start-Process -FilePath $node -ArgumentList @($serverScript, '--root', $fixtureRoot, '--port', '0') -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
Set-Content -LiteralPath (Join-Path $fixtureRoot 'fixture.pid') -Value $process.Id -Encoding ascii

$ready = $null
for ($i = 0; $i -lt 120; $i += 1) {
  if ($process.HasExited) {
    $err = if (Test-Path -LiteralPath $stderr) { Get-Content -LiteralPath $stderr -Raw } else { '' }
    throw "Fixture server exited before readiness. $err"
  }
  if (Test-Path -LiteralPath $stdout) {
    $line = Get-Content -LiteralPath $stdout | Where-Object { $_ -like 'READY *' } | Select-Object -Last 1
    if ($line) {
      $ready = ($line.Substring(6) | ConvertFrom-Json)
      break
    }
  }
  Start-Sleep -Milliseconds 100
}
if (-not $ready -or -not $ready.url) { throw 'Fixture server did not report READY.' }

$health = Invoke-RestMethod -Uri ($ready.url + 'health') -Method Get -TimeoutSec 5
if ($health.status -ne 'ok' -or $health.finish -ne 'not_done') { throw 'Fixture did not start in a clean NOT_DONE state.' }

if (-not $SkipBootstrap) {
  $bootstrap = Join-Path $SourceRoot 'scripts\bootstrap-chat-platform.ps1'
  & pwsh.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $bootstrap
  if ($LASTEXITCODE -ne 0) { throw "bootstrap-chat-platform failed: $LASTEXITCODE" }

  $platform = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\app\scripts\chat-platform.ps1'
  & pwsh.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $platform -Action SetProfile -Profile semantic -FilesRoot $workspaceRoot -NoNotify
  if ($LASTEXITCODE -ne 0) { throw "SetProfile failed: $LASTEXITCODE" }
  & pwsh.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $platform -Action Start -NoNotify
  if ($LASTEXITCODE -ne 0) { throw "Platform Start failed: $LASTEXITCODE" }
}

$task = "In Case Desk, find case $targetId for Marina Volkova. Change its delivery address from '$oldAddress' to '$newAddress', set the status to Approved, replace the comment with '$requiredComment', save the case, and make sure you changed the intended case rather than a similar customer record. Verify the final result before you report completion."
$challenge = @"
STAGE26_3B_BROWSER_REAL_TASK_GATE
EXACT_HEAD=$ExpectedHead
START_URL=$($ready.url)
TARGET_CASE=$targetId
TASK_BEGIN
$task
TASK_END
"@
$challengePath = Join-Path $workspaceRoot 'stage26-3b-browser-real-task.txt'
Write-Utf8NoBom -Path $challengePath -Content ($challenge + "`n")

$manifest = [ordered]@{
  exact_head = $ExpectedHead
  qualification_root = $qualificationRoot
  workspace_root = $workspaceRoot
  fixture_root = $fixtureRoot
  challenge_file = $challengePath
  start_url = [string]$ready.url
  target_case = $targetId
  fixture_pid = $process.Id
}
Write-Utf8NoBom -Path (Join-Path $qualificationRoot 'gate-manifest.json') -Content (($manifest | ConvertTo-Json -Depth 6) + "`n")

Write-Host 'STAGE26_3B_BROWSER_REAL_TASK_PREP=PASS'
Write-Host "EXACT_HEAD=$ExpectedHead"
Write-Host "QUALIFICATION_ROOT=$qualificationRoot"
Write-Host "CHAT_WORKSPACE_ROOT=$workspaceRoot"
Write-Host "START_URL=$($ready.url)"
Write-Host "TARGET_CASE=$targetId"
Write-Host "CHALLENGE_FILE=$challengePath"
Write-Host "FIXTURE_PID=$($process.Id)"
Write-Host 'INITIAL_FINISH_GATE=not_done'
Write-Host 'NOTE=fixture-state is outside the Chat workspace and must be checked externally.'
