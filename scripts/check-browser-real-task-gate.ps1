[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$QualificationRoot,
  [string]$ExpectedHead = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

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

function Test-InstalledAssetMatch {
  param(
    [Parameter(Mandatory = $true)][string]$SourcePath,
    [Parameter(Mandatory = $true)][string]$InstalledPath
  )
  if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) { return $false }
  if (-not (Test-Path -LiteralPath $InstalledPath -PathType Leaf)) { return $false }
  return (Get-Sha256 -Path $SourcePath) -ceq (Get-Sha256 -Path $InstalledPath)
}

$QualificationRoot = (Resolve-Path -LiteralPath $QualificationRoot).Path
$manifestPath = Join-Path $QualificationRoot 'gate-manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
  throw "Gate manifest missing: $manifestPath"
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding utf8 | ConvertFrom-Json
$fixturePid = [int]$manifest.fixture_pid
$cleanupPass = $false

try {
  if ($ExpectedHead -and [string]$manifest.exact_head -ne $ExpectedHead) {
    throw "EXACT_HEAD_MISMATCH expected=$ExpectedHead actual=$($manifest.exact_head)"
  }
  if (-not $ExpectedHead) { $ExpectedHead = [string]$manifest.exact_head }

  $sourceRoot = (Resolve-Path -LiteralPath ([string]$manifest.source_root)).Path
  $fixtureRoot = [string]$manifest.fixture_root
  $workspaceRoot = [string]$manifest.workspace_root
  $sourceProvenancePath = [string]$manifest.source_provenance_path
  $installedProvenancePath = [string]$manifest.installed_runtime_provenance_path
  $frozenCheckerPath = [string]$manifest.frozen_checker_path
  $frozenProvenancePath = [string]$manifest.frozen_provenance_gate_path
  if (-not $fixtureRoot -or -not (Test-Path -LiteralPath $fixtureRoot -PathType Container)) { throw 'Fixture root missing or invalid.' }
  if (-not $workspaceRoot -or -not (Test-Path -LiteralPath $workspaceRoot -PathType Container)) { throw 'Workspace root missing or invalid.' }
  foreach ($path in @($sourceProvenancePath, $installedProvenancePath, $frozenCheckerPath, $frozenProvenancePath)) {
    if (-not $path -or -not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required provenance evidence/code missing: $path" }
  }

  $fixtureFull = [System.IO.Path]::GetFullPath($fixtureRoot).TrimEnd('\')
  $workspaceFull = [System.IO.Path]::GetFullPath($workspaceRoot).TrimEnd('\')
  $qualificationFull = [System.IO.Path]::GetFullPath($QualificationRoot).TrimEnd('\')
  if ($fixtureFull.StartsWith($workspaceFull + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Fixture evidence must not live inside the Chat workspace root.'
  }
  foreach ($path in @($sourceProvenancePath, $installedProvenancePath, $frozenCheckerPath, $frozenProvenancePath, $manifestPath, $PSCommandPath)) {
    $full = [System.IO.Path]::GetFullPath($path)
    if ($full.StartsWith($workspaceFull + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
      throw "Independent Browser L3 evidence/code must not live inside the Chat workspace: $path"
    }
    if (-not $full.StartsWith($qualificationFull + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
      throw "Independent Browser L3 evidence/code escaped qualification root: $path"
    }
  }
  if ([System.IO.Path]::GetFullPath($frozenCheckerPath) -cne [System.IO.Path]::GetFullPath($PSCommandPath)) {
    throw 'Finish Gate must execute the checker path frozen by preparation.'
  }

  $currentCheckerHash = Get-Sha256 -Path $PSCommandPath
  $currentProvenanceHash = Get-Sha256 -Path $frozenProvenancePath
  if ($currentCheckerHash -cne [string]$manifest.frozen_checker_sha256) { throw 'Frozen Browser Finish Gate checker hash drifted.' }
  if ($currentProvenanceHash -cne [string]$manifest.frozen_provenance_gate_sha256) { throw 'Frozen Source Provenance Gate hash drifted.' }

  $initialSource = Get-Content -LiteralPath $sourceProvenancePath -Raw -Encoding utf8 | ConvertFrom-Json
  $initialInstalled = Get-Content -LiteralPath $installedProvenancePath -Raw -Encoding utf8 | ConvertFrom-Json
  if (
    [string]$initialSource.status -ne 'pass' -or
    [string]$initialSource.actual_head -ne $ExpectedHead -or
    -not [bool]$initialSource.working_tree_clean -or
    -not [bool]$initialSource.tracked_diff_empty -or
    -not [bool]$initialSource.untracked_empty -or
    -not [bool]$initialInstalled.all_match -or
    [string]$initialInstalled.exact_head -ne $ExpectedHead -or
    [string]$initialInstalled.playwright_mcp_version -ne '0.0.78' -or
    -not [string]$initialInstalled.playwright_mcp_lock_integrity -or
    -not [string]$initialInstalled.playwright_mcp_directory_sha256
  ) {
    throw 'Initial Browser L3 provenance evidence was not a clean exact-head PASS.'
  }

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
  $recheckPath = Join-Path $QualificationRoot 'finish-provenance-revalidation.json'
  $python = (Get-Command python.exe -ErrorAction Stop).Source
  $provenanceArgs = @(
    $frozenProvenancePath,
    '--repo-root', $sourceRoot,
    '--expected-head', $ExpectedHead,
    '--output', $recheckPath
  )
  foreach ($asset in $criticalAssets) { $provenanceArgs += @('--asset', $asset) }
  $provenanceArgs += @('--lockfile', 'runtime/semantic-projection/package-lock.json')
  & $python @provenanceArgs
  if ($LASTEXITCODE -ne 0) { throw 'Browser L3 source provenance revalidation failed.' }
  $recheck = Get-Content -LiteralPath $recheckPath -Raw -Encoding utf8 | ConvertFrom-Json
  if (
    [string]$recheck.status -ne 'pass' -or
    [string]$recheck.actual_head -ne $ExpectedHead -or
    -not [bool]$recheck.working_tree_clean -or
    -not [bool]$recheck.tracked_diff_empty -or
    -not [bool]$recheck.untracked_empty
  ) {
    throw 'Browser L3 source provenance revalidation did not PASS.'
  }

  $appRoot = [string]$initialInstalled.installed_root
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
  foreach ($mapping in $installedMappings) {
    $sourcePath = Join-Path $sourceRoot ([string]$mapping[0])
    $installedPath = Join-Path $appRoot ([string]$mapping[1])
    if (-not (Test-InstalledAssetMatch -SourcePath $sourcePath -InstalledPath $installedPath)) {
      throw "Installed Browser L3 runtime byte drift: $([string]$mapping[0])"
    }
  }

  $sourceLockPath = Join-Path $sourceRoot 'runtime\semantic-projection\package-lock.json'
  $sourceLock = Get-Content -LiteralPath $sourceLockPath -Raw -Encoding utf8 | ConvertFrom-Json -AsHashtable
  $playwrightLockRecord = $sourceLock['packages']['node_modules/@playwright/mcp']
  $playwrightLockIntegrity = [string]$playwrightLockRecord['integrity']
  if (-not $playwrightLockIntegrity -or $playwrightLockIntegrity -cne [string]$initialInstalled.playwright_mcp_lock_integrity) {
    throw 'Source lock integrity for @playwright/mcp drifted during Browser L3 run.'
  }
  $playwrightManifest = Join-Path $appRoot 'runtime\semantic-projection\node_modules\@playwright\mcp\package.json'
  if (-not (Test-Path -LiteralPath $playwrightManifest -PathType Leaf)) { throw 'Installed @playwright/mcp manifest is missing during revalidation.' }
  $playwrightRoot = Split-Path -Parent $playwrightManifest
  $playwrightVersion = [string](Get-Content -LiteralPath $playwrightManifest -Raw -Encoding utf8 | ConvertFrom-Json).version
  if ($playwrightVersion -ne '0.0.78') { throw "Installed @playwright/mcp version drifted during revalidation: $playwrightVersion" }
  $playwrightDirectoryHash = Get-DirectoryDigest -Root $playwrightRoot
  if ($playwrightDirectoryHash -cne [string]$initialInstalled.playwright_mcp_directory_sha256) {
    throw 'Installed @playwright/mcp package bytes drifted during Browser L3 run.'
  }

  $fixtureProcess = Get-Process -Id $fixturePid -ErrorAction SilentlyContinue
  if ($null -eq $fixtureProcess -or $fixtureProcess.HasExited) { throw 'Browser L3 fixture process was not live at Finish Gate proof time.' }
  $fixtureProcess.Refresh()
  if ($fixtureProcess.ProcessName -cne [string]$manifest.fixture_process_name) { throw 'Browser L3 fixture process identity drifted.' }
  if ($fixtureProcess.StartTime.ToUniversalTime().Ticks -ne [long]$manifest.fixture_process_start_time_ticks) { throw 'Browser L3 fixture process generation drifted.' }

  $finishPath = Join-Path $fixtureRoot 'finish-gate.json'
  $statePath = Join-Path $fixtureRoot 'server-state.json'
  $auditPath = Join-Path $fixtureRoot 'audit.jsonl'
  $seedPath = Join-Path $fixtureRoot 'fixture-seed.json'
  foreach ($path in @($finishPath, $statePath, $seedPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required gate evidence missing: $path" }
  }

  $finish = Get-Content -LiteralPath $finishPath -Raw -Encoding utf8 | ConvertFrom-Json
  $state = Get-Content -LiteralPath $statePath -Raw -Encoding utf8 | ConvertFrom-Json
  $seed = Get-Content -LiteralPath $seedPath -Raw -Encoding utf8 | ConvertFrom-Json

  $requiredChecks = @(
    'target_exists',
    'address_exact',
    'status_exact',
    'comment_exact',
    'old_address_absent_in_target',
    'decoys_unchanged',
    'only_target_ever_mutated'
  )
  if ([string]$finish.status -ne 'done') { throw "FINISH_GATE_NOT_DONE status=$($finish.status)" }
  foreach ($name in $requiredChecks) {
    $property = $finish.checks.PSObject.Properties[$name]
    if ($null -eq $property -or -not [bool]$property.Value) { throw "FINISH_CHECK_FAILED=$name" }
  }

  $targetId = [string]$seed.target_id
  if ([string]$finish.target_id -ne $targetId) { throw 'Finish Gate target identity drifted.' }
  if ([int]$finish.save_count -ne 1) { throw "Browser L3 requires exactly one persisted save; observed=$($finish.save_count)" }

  $mutated = @($finish.mutated_ids)
  if ($mutated.Count -ne 1 -or [string]$mutated[0] -ne $targetId) { throw "UNEXPECTED_MUTATION_SET=$($mutated -join ',')" }

  $target = @($state.cases | Where-Object { [string]$_.id -eq $targetId })
  if ($target.Count -ne 1) { throw 'Target case missing or duplicated in final server state.' }
  if ([string]$target[0].address -ne [string]$seed.expected.address) { throw 'Final address mismatch.' }
  if ([string]$target[0].status -ne [string]$seed.expected.status) { throw 'Final status mismatch.' }
  if ([string]$target[0].comment -ne [string]$seed.expected.comment) { throw 'Final comment mismatch.' }

  $auditCount = 0
  if (Test-Path -LiteralPath $auditPath -PathType Leaf) {
    foreach ($line in Get-Content -LiteralPath $auditPath) {
      if (-not $line.Trim()) { continue }
      $entry = $line | ConvertFrom-Json
      $auditCount += 1
      if ([string]$entry.id -ne $targetId) { throw "AUDIT_WRONG_TARGET_MUTATION=$($entry.id)" }
    }
  }
  if ($auditCount -ne 1) { throw "Browser L3 requires exactly one audit mutation; observed=$auditCount" }

  Write-Host '===== STAGE 26.3B BROWSER REAL-TASK PROVENANCE FINISH GATE ====='
  Write-Host "EXACT_HEAD=$ExpectedHead"
  Write-Host 'SOURCE_PROVENANCE_GATE=PASS'
  Write-Host 'INSTALLED_RUNTIME_PROVENANCE=PASS'
  Write-Host 'PLAYWRIGHT_MCP_PROVENANCE=PASS'
  Write-Host 'FROZEN_FINISH_GATE_CODE=PASS'
  Write-Host 'SOURCE_PROVENANCE_REVALIDATED=PASS'
  Write-Host 'INSTALLED_RUNTIME_REVALIDATED=PASS'
  Write-Host 'PROVENANCE_REVALIDATION=PASS'
  Write-Host 'EVIDENCE_OUTSIDE_CHAT_WORKSPACE=True'
  Write-Host 'TARGET_FINAL_STATE=True'
  Write-Host 'DECOYS_UNCHANGED=True'
  Write-Host 'ONLY_TARGET_EVER_MUTATED=True'
  Write-Host 'FIXTURE_PROCESS_WAS_LIVE=True'
  Write-Host "TARGET_CASE=$targetId"
  Write-Host 'SAVE_COUNT=1'
  Write-Host 'AUDIT_COUNT=1'
  Write-Host 'EXTERNAL_FINISH_GATE=DONE'
  Write-Host 'NON_TARGET_MUTATION=none'
  Write-Host 'STAGE26_3B_BROWSER_REAL_TASK_GATE=PASS'
}
finally {
  if ($fixturePid -gt 0) {
    $live = Get-Process -Id $fixturePid -ErrorAction SilentlyContinue
    if ($null -ne $live) {
      Stop-Process -Id $fixturePid -Force -ErrorAction SilentlyContinue
      try { Wait-Process -Id $fixturePid -Timeout 5 -ErrorAction SilentlyContinue } catch { }
    }
    $stillLive = Get-Process -Id $fixturePid -ErrorAction SilentlyContinue
    $cleanupPass = $null -eq $stillLive
  }
  Write-Host "FIXTURE_CLEANUP_PASS=$cleanupPass"
}
if (-not $cleanupPass) { throw 'Browser L3 fixture cleanup failed.' }
