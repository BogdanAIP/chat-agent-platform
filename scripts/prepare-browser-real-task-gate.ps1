[CmdletBinding()]
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

function Get-Sha256 {
  param([Parameter(Mandatory = $true)][string]$Path)
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-DirectoryDigest {
  param([Parameter(Mandatory = $true)][string]$Root)
  $resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
  $entries = @(
    Get-ChildItem -LiteralPath $resolvedRoot -Recurse -File |
      Sort-Object FullName |
      ForEach-Object {
        $relative = [System.IO.Path]::GetRelativePath($resolvedRoot, $_.FullName).Replace('\', '/')
        "$relative`0$(Get-Sha256 -Path $_.FullName)"
      }
  )
  if ($entries.Count -eq 0) { throw "Cannot hash empty installed directory: $resolvedRoot" }
  $payload = [System.Text.Encoding]::UTF8.GetBytes(($entries -join "`n"))
  return [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($payload)).ToLowerInvariant()
}

function Get-InstalledAssetRecord {
  param(
    [Parameter(Mandatory = $true)][string]$SourcePath,
    [Parameter(Mandatory = $true)][string]$InstalledPath,
    [Parameter(Mandatory = $true)][string]$Name
  )
  if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) { throw "Source asset missing: $SourcePath" }
  if (-not (Test-Path -LiteralPath $InstalledPath -PathType Leaf)) { throw "Installed asset missing: $InstalledPath" }
  $sourceHash = Get-Sha256 -Path $SourcePath
  $installedHash = Get-Sha256 -Path $InstalledPath
  return [ordered]@{
    name = $Name
    source = $SourcePath
    installed = $InstalledPath
    source_sha256 = $sourceHash
    installed_sha256 = $installedHash
    match = ($sourceHash -ceq $installedHash)
  }
}

$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path
$actualHead = (& git.exe -C $SourceRoot rev-parse HEAD 2>$null | Select-Object -Last 1).Trim()
if ($LASTEXITCODE -ne 0 -or -not $actualHead) { throw 'Unable to resolve source HEAD.' }
if ($ExpectedHead -and $actualHead -ne $ExpectedHead) {
  throw "EXACT_HEAD_MISMATCH expected=$ExpectedHead actual=$actualHead"
}
if (-not $ExpectedHead) { $ExpectedHead = $actualHead }

$node = (Get-Command node.exe -ErrorAction Stop).Source
$python = (Get-Command python.exe -ErrorAction Stop).Source
$pwsh = (Get-Command pwsh.exe -ErrorAction Stop).Source
$localRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
$appRoot = Join-Path $localRoot 'app'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$nonce = ([guid]::NewGuid().ToString('N').Substring(0, 8)).ToUpperInvariant()
$qualificationRoot = Join-Path $localRoot "stage26\stage26-3b-browser-real-task-$stamp-$nonce"
$workspaceRoot = Join-Path $qualificationRoot 'workspace'
$fixtureRoot = Join-Path $qualificationRoot 'fixture-state'
$frozenGateRoot = Join-Path $qualificationRoot 'frozen-gate'
New-Item -ItemType Directory -Force -Path $workspaceRoot, $fixtureRoot, $frozenGateRoot | Out-Null

$sourceProvenancePath = Join-Path $qualificationRoot 'source-provenance.json'
$installedProvenancePath = Join-Path $qualificationRoot 'installed-runtime-provenance.json'
$sourceProvenanceGate = Join-Path $SourceRoot 'scripts\source-provenance-gate.py'
$checkerScript = Join-Path $SourceRoot 'scripts\check-browser-real-task-gate.ps1'

$criticalAssets = @(
  'runtime/semantic-projection/bin/semantic-projection-launcher.mjs',
  'runtime/semantic-projection/bin/semantic-control-plane-projection.mjs',
  'runtime/semantic-projection/bin/semantic-projection.mjs',
  'runtime/semantic-projection/lib/browser-verification-bridge.mjs',
  'runtime/semantic-projection/lib/semantic-vision-click-router.mjs',
  'runtime/semantic-projection/lib/visual-grounding-bridge.mjs',
  'runtime/semantic-projection/lib/runtime-backed-bridge-grounder.mjs',
  'runtime/semantic-projection/lib/runtime-backed-visual-grounder.mjs',
  'runtime/semantic-projection/package.json',
  'runtime/control_plane/browser_observation.py',
  'runtime/control_plane/browser_transition.py',
  'runtime/control_plane/browser_transition_cli.py',
  'runtime/control_plane/verification.py',
  'runtime/chat-profiles/semantic/mcp.json',
  'scripts/bootstrap-chat-platform.ps1',
  'scripts/bootstrap-manager-runtime.ps1',
  'scripts/chat-platform.ps1',
  'scripts/semantic-direct-controller.ps1',
  'scripts/source-provenance-gate.py',
  'scripts/prepare-browser-real-task-gate.ps1',
  'scripts/check-browser-real-task-gate.ps1',
  'tests/fixtures/browser_real_task_server.mjs'
)
$provenanceArgs = @(
  $sourceProvenanceGate,
  '--repo-root', $SourceRoot,
  '--expected-head', $ExpectedHead,
  '--output', $sourceProvenancePath
)
foreach ($asset in $criticalAssets) { $provenanceArgs += @('--asset', $asset) }
$provenanceArgs += @('--lockfile', 'runtime/semantic-projection/package-lock.json')

& $python @provenanceArgs
if ($LASTEXITCODE -ne 0) { throw 'Source Provenance Gate failed before Browser L3 preparation.' }
$sourceProvenance = Get-Content -LiteralPath $sourceProvenancePath -Raw -Encoding utf8 | ConvertFrom-Json
if (
  [string]$sourceProvenance.status -ne 'pass' -or
  [string]$sourceProvenance.actual_head -ne $ExpectedHead -or
  -not [bool]$sourceProvenance.working_tree_clean -or
  -not [bool]$sourceProvenance.tracked_diff_empty -or
  -not [bool]$sourceProvenance.untracked_empty
) {
  throw 'Source Provenance Gate did not produce a clean exact-head PASS.'
}

if (-not $SkipBootstrap) {
  $bootstrap = Join-Path $SourceRoot 'scripts\bootstrap-chat-platform.ps1'
  & $pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $bootstrap
  if ($LASTEXITCODE -ne 0) { throw "bootstrap-chat-platform failed: $LASTEXITCODE" }
}

$installedMappings = @(
  @('runtime\semantic-projection\bin\semantic-projection-launcher.mjs', 'runtime\semantic-projection\bin\semantic-projection-launcher.mjs'),
  @('runtime\semantic-projection\bin\semantic-control-plane-projection.mjs', 'runtime\semantic-projection\bin\semantic-control-plane-projection.mjs'),
  @('runtime\semantic-projection\bin\semantic-projection.mjs', 'runtime\semantic-projection\bin\semantic-projection.mjs'),
  @('runtime\semantic-projection\lib\browser-verification-bridge.mjs', 'runtime\semantic-projection\lib\browser-verification-bridge.mjs'),
  @('runtime\semantic-projection\lib\semantic-vision-click-router.mjs', 'runtime\semantic-projection\lib\semantic-vision-click-router.mjs'),
  @('runtime\semantic-projection\lib\visual-grounding-bridge.mjs', 'runtime\semantic-projection\lib\visual-grounding-bridge.mjs'),
  @('runtime\semantic-projection\lib\runtime-backed-bridge-grounder.mjs', 'runtime\semantic-projection\lib\runtime-backed-bridge-grounder.mjs'),
  @('runtime\semantic-projection\lib\runtime-backed-visual-grounder.mjs', 'runtime\semantic-projection\lib\runtime-backed-visual-grounder.mjs'),
  @('runtime\semantic-projection\package.json', 'runtime\semantic-projection\package.json'),
  @('runtime\semantic-projection\package-lock.json', 'runtime\semantic-projection\package-lock.json'),
  @('runtime\control_plane\browser_observation.py', 'runtime\control_plane\browser_observation.py'),
  @('runtime\control_plane\browser_transition.py', 'runtime\control_plane\browser_transition.py'),
  @('runtime\control_plane\browser_transition_cli.py', 'runtime\control_plane\browser_transition_cli.py'),
  @('runtime\control_plane\verification.py', 'runtime\control_plane\verification.py'),
  @('runtime\chat-profiles\semantic\mcp.json', 'runtime\chat-profiles\semantic\mcp.json'),
  @('scripts\chat-platform.ps1', 'scripts\chat-platform.ps1'),
  @('scripts\semantic-direct-controller.ps1', 'scripts\semantic-direct-controller.ps1')
)
$installedRecords = @()
foreach ($mapping in $installedMappings) {
  $sourcePath = Join-Path $SourceRoot ([string]$mapping[0])
  $installedPath = Join-Path $appRoot ([string]$mapping[1])
  $installedRecords += @(Get-InstalledAssetRecord -SourcePath $sourcePath -InstalledPath $installedPath -Name (([string]$mapping[0]).Replace('\', '/')))
}
$allInstalledMatch = @($installedRecords | Where-Object { -not [bool]$_.match }).Count -eq 0
$sourceLockPath = Join-Path $SourceRoot 'runtime\semantic-projection\package-lock.json'
$sourceLock = Get-Content -LiteralPath $sourceLockPath -Raw -Encoding utf8 | ConvertFrom-Json -AsHashtable
$playwrightLockRecord = $sourceLock['packages']['node_modules/@playwright/mcp']
$playwrightLockIntegrity = [string]$playwrightLockRecord['integrity']
if (-not $playwrightLockIntegrity) { throw 'Source package-lock is missing @playwright/mcp integrity.' }
$playwrightManifest = Join-Path $appRoot 'runtime\semantic-projection\node_modules\@playwright\mcp\package.json'
if (-not (Test-Path -LiteralPath $playwrightManifest -PathType Leaf)) { throw 'Installed @playwright/mcp manifest is missing.' }
$playwrightRoot = Split-Path -Parent $playwrightManifest
$playwrightVersion = [string](Get-Content -LiteralPath $playwrightManifest -Raw -Encoding utf8 | ConvertFrom-Json).version
if ($playwrightVersion -ne '0.0.78') { throw "Installed @playwright/mcp version drifted: $playwrightVersion" }
$playwrightDirectoryHash = Get-DirectoryDigest -Root $playwrightRoot
$installedEvidence = [ordered]@{
  schema_version = 2
  exact_head = $ExpectedHead
  source_root = $SourceRoot
  installed_root = $appRoot
  all_match = $allInstalledMatch
  playwright_mcp_version = $playwrightVersion
  playwright_mcp_lock_integrity = $playwrightLockIntegrity
  playwright_mcp_directory_sha256 = $playwrightDirectoryHash
  node_version = (& $node --version).Trim()
  assets = $installedRecords
  captured_at = (Get-Date).ToUniversalTime().ToString('o')
}
Write-Utf8NoBom -Path $installedProvenancePath -Content (($installedEvidence | ConvertTo-Json -Depth 8) + "`n")
if (-not $allInstalledMatch) { throw 'Installed AppRoot bytes do not match the frozen Browser L3 source head.' }

$frozenCheckerPath = Join-Path $frozenGateRoot 'check-browser-real-task-gate.ps1'
$frozenProvenancePath = Join-Path $frozenGateRoot 'source-provenance-gate.py'
Copy-Item -LiteralPath $checkerScript -Destination $frozenCheckerPath -Force
Copy-Item -LiteralPath $sourceProvenanceGate -Destination $frozenProvenancePath -Force
$checkerSourceHash = Get-Sha256 -Path $checkerScript
$frozenCheckerHash = Get-Sha256 -Path $frozenCheckerPath
$provenanceSourceHash = Get-Sha256 -Path $sourceProvenanceGate
$frozenProvenanceHash = Get-Sha256 -Path $frozenProvenancePath
if ($checkerSourceHash -cne $frozenCheckerHash -or $provenanceSourceHash -cne $frozenProvenanceHash) {
  throw 'Frozen Browser L3 checker/provenance bytes do not match the exact-head source.'
}

$platform = Join-Path $appRoot 'scripts\chat-platform.ps1'
& $pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $platform -Action SetProfile -Profile semantic -FilesRoot $workspaceRoot -NoNotify
if ($LASTEXITCODE -ne 0) { throw "SetProfile failed: $LASTEXITCODE" }
& $pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $platform -Action Start -NoNotify
if ($LASTEXITCODE -ne 0) { throw "Platform Start failed: $LASTEXITCODE" }

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

try {
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

  $process.Refresh()
  $manifest = [ordered]@{
    schema_version = 3
    exact_head = $ExpectedHead
    source_root = $SourceRoot
    qualification_root = $qualificationRoot
    workspace_root = $workspaceRoot
    fixture_root = $fixtureRoot
    challenge_file = $challengePath
    start_url = [string]$ready.url
    target_case = $targetId
    fixture_pid = $process.Id
    fixture_process_name = $process.ProcessName
    fixture_process_start_time_ticks = $process.StartTime.ToUniversalTime().Ticks
    source_provenance_path = $sourceProvenancePath
    installed_runtime_provenance_path = $installedProvenancePath
    frozen_checker_path = $frozenCheckerPath
    frozen_provenance_gate_path = $frozenProvenancePath
    frozen_checker_sha256 = $frozenCheckerHash
    frozen_provenance_gate_sha256 = $frozenProvenanceHash
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
  Write-Host 'SOURCE_PROVENANCE_GATE=PASS'
  Write-Host 'INSTALLED_RUNTIME_PROVENANCE=PASS'
  Write-Host "PLAYWRIGHT_MCP_INSTALLED_VERSION=$playwrightVersion"
  Write-Host "PLAYWRIGHT_MCP_DIRECTORY_SHA256=$playwrightDirectoryHash"
  Write-Host 'FROZEN_FINISH_GATE=PASS'
  Write-Host 'INITIAL_FINISH_GATE=NOT_DONE'
  Write-Host "CHECK_COMMAND=& '$frozenCheckerPath' -QualificationRoot '$qualificationRoot' -ExpectedHead '$ExpectedHead'"
  Write-Host 'NOTE=fixture-state is outside the Chat workspace; provenance evidence and frozen Finish Gate are outside the Chat workspace; audit is outside the Chat workspace.'
}
catch {
  if ($null -ne $process -and -not $process.HasExited) {
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
  }
  throw
}
