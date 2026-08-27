[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$QualificationRoot,
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^[0-9a-fA-F]{40}$')]
  [string]$ExpectedHead
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Get-Sha256 {
  param([Parameter(Mandatory = $true)][string]$Path)
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-DirectoryDigest {
  param(
    [Parameter(Mandatory = $true)][string]$Root,
    [string[]]$ExcludeRelativePath = @()
  )
  $resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
  $entries = @(
    Get-ChildItem -LiteralPath $resolvedRoot -Recurse -File |
      Sort-Object FullName |
      ForEach-Object {
        $relative = [System.IO.Path]::GetRelativePath($resolvedRoot, $_.FullName).Replace('\', '/')
        if ($ExcludeRelativePath -notcontains $relative) {
          "$relative`0$(Get-Sha256 -Path $_.FullName)"
        }
      }
  )
  if ($entries.Count -eq 0) { throw "Cannot hash empty installed directory: $resolvedRoot" }
  $payload = [System.Text.Encoding]::UTF8.GetBytes(($entries -join "`n"))
  return [Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($payload)).ToLowerInvariant()
}

function Test-InstalledAssetMatch {
  param([Parameter(Mandatory = $true)][string]$SourcePath, [Parameter(Mandatory = $true)][string]$InstalledPath)
  if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) { return $false }
  if (-not (Test-Path -LiteralPath $InstalledPath -PathType Leaf)) { return $false }
  return (Get-Sha256 -Path $SourcePath) -ceq (Get-Sha256 -Path $InstalledPath)
}

function Test-ProcessGeneration {
  param(
    [Parameter(Mandatory = $true)][int]$ProcessId,
    [Parameter(Mandatory = $true)][string]$ProcessName,
    [Parameter(Mandatory = $true)][long]$StartTimeTicks
  )
  $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
  if ($null -eq $process) { return $false }
  try {
    $process.Refresh()
    return (-not $process.HasExited -and $process.ProcessName -ceq $ProcessName -and $process.StartTime.ToUniversalTime().Ticks -eq $StartTimeTicks)
  }
  catch { return $false }
}

function Stop-VerifiedProcessSafely {
  param(
    [Parameter(Mandatory = $true)][int]$ProcessId,
    [Parameter(Mandatory = $true)][string]$ProcessName,
    [Parameter(Mandatory = $true)][long]$StartTimeTicks
  )
  $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
  if ($null -eq $process) { return $true }
  try {
    $process.Refresh()
    if ($process.ProcessName -cne $ProcessName -or $process.StartTime.ToUniversalTime().Ticks -ne $StartTimeTicks) { return $false }
    $process.Kill()
    $process.WaitForExit(5000) | Out-Null
  }
  catch { return $false }
  $after = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
  if ($null -eq $after) { return $true }
  try {
    $after.Refresh()
    return ($after.ProcessName -cne $ProcessName -or $after.StartTime.ToUniversalTime().Ticks -ne $StartTimeTicks)
  }
  catch { return $true }
}

$QualificationRoot = (Resolve-Path -LiteralPath $QualificationRoot).Path
$ExpectedHead = $ExpectedHead.ToLowerInvariant()
$manifestPath = Join-Path $QualificationRoot 'gate-manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw "Gate manifest missing: $manifestPath" }
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding utf8 | ConvertFrom-Json
if ([string]$manifest.exact_head -cne $ExpectedHead) { throw "EXACT_HEAD_MISMATCH expected=$ExpectedHead actual=$($manifest.exact_head)" }

$fixturePid = [int]$manifest.fixture_pid
$guardianPid = [int]$manifest.guardian_pid
$fixtureCleanupPass = $false
$guardianCleanupPass = $false
$validated = $false
$mainError = $null
$targetId = ''
$auditCount = 0

try {
  $sourceRoot = (Resolve-Path -LiteralPath ([string]$manifest.source_root)).Path
  $fixtureRoot = [string]$manifest.fixture_root
  $workspaceRoot = [string]$manifest.workspace_root
  $sourceProvenancePath = [string]$manifest.source_provenance_path
  $installedProvenancePath = [string]$manifest.installed_runtime_provenance_path
  $frozenCheckerPath = [string]$manifest.frozen_checker_path
  $frozenProvenancePath = [string]$manifest.frozen_provenance_gate_path
  $frozenGuardianPath = [string]$manifest.frozen_guardian_path
  foreach ($path in @($fixtureRoot, $workspaceRoot)) {
    if (-not $path -or -not (Test-Path -LiteralPath $path -PathType Container)) { throw "Required Browser L3 directory missing: $path" }
  }
  foreach ($path in @($sourceProvenancePath, $installedProvenancePath, $frozenCheckerPath, $frozenProvenancePath, $frozenGuardianPath)) {
    if (-not $path -or -not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required provenance evidence/code missing: $path" }
  }

  $fixtureFull = [System.IO.Path]::GetFullPath($fixtureRoot).TrimEnd('\')
  $workspaceFull = [System.IO.Path]::GetFullPath($workspaceRoot).TrimEnd('\')
  $qualificationFull = [System.IO.Path]::GetFullPath($QualificationRoot).TrimEnd('\')
  if ($fixtureFull.StartsWith($workspaceFull + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Fixture evidence must not live inside the Chat workspace root.' }
  foreach ($path in @($sourceProvenancePath, $installedProvenancePath, $frozenCheckerPath, $frozenProvenancePath, $frozenGuardianPath, $manifestPath, $PSCommandPath)) {
    $full = [System.IO.Path]::GetFullPath($path)
    if ($full.StartsWith($workspaceFull + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw "Independent Browser L3 evidence/code must not live inside the Chat workspace: $path" }
    if (-not $full.StartsWith($qualificationFull + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw "Independent Browser L3 evidence/code escaped qualification root: $path" }
  }
  if ([System.IO.Path]::GetFullPath($frozenCheckerPath) -cne [System.IO.Path]::GetFullPath($PSCommandPath)) { throw 'Finish Gate must execute the checker path frozen by preparation.' }

  if ((Get-Sha256 -Path $PSCommandPath) -cne [string]$manifest.frozen_checker_sha256) { throw 'Frozen Browser Finish Gate checker hash drifted.' }
  if ((Get-Sha256 -Path $frozenProvenancePath) -cne [string]$manifest.frozen_provenance_gate_sha256) { throw 'Frozen Source Provenance Gate hash drifted.' }
  if ((Get-Sha256 -Path $frozenGuardianPath) -cne [string]$manifest.frozen_guardian_sha256) { throw 'Frozen Browser byte-lock guardian hash drifted.' }

  $initialSource = Get-Content -LiteralPath $sourceProvenancePath -Raw -Encoding utf8 | ConvertFrom-Json
  $initialInstalled = Get-Content -LiteralPath $installedProvenancePath -Raw -Encoding utf8 | ConvertFrom-Json
  $dependencyTree = $initialInstalled.dependency_tree
  if (
    [string]$initialSource.status -ne 'pass' -or
    [string]$initialSource.actual_head -ne $ExpectedHead -or
    -not [bool]$initialSource.working_tree_clean -or
    -not [bool]$initialSource.tracked_diff_empty -or
    -not [bool]$initialSource.untracked_empty -or
    -not [bool]$initialInstalled.all_match -or
    -not [bool]$initialInstalled.dependencies_match_exact_lock -or
    [string]$initialInstalled.exact_head -ne $ExpectedHead -or
    $null -eq $dependencyTree -or
    [string]$dependencyTree.scope -ne 'runtime/semantic-projection/node_modules' -or
    -not [bool]$dependencyTree.match -or
    [int]$dependencyTree.lock_package_count -le 0 -or
    -not [string]$dependencyTree.installed_directory_sha256 -or
    [string]$dependencyTree.installed_directory_sha256 -cne [string]$dependencyTree.reference_directory_sha256
  ) {
    throw 'Initial Browser L3 provenance evidence was not a clean exact-head/full exact-lock dependency-tree PASS.'
  }

  $guardianReadyTimeTicks = [long]$manifest.guardian_ready_time_ticks
  if ($guardianReadyTimeTicks -le 0) { throw 'Browser byte-lock guardian READY timestamp is missing.' }
  if ([long]$manifest.semantic_transport_process_start_time_ticks -lt $guardianReadyTimeTicks) {
    throw 'Direct semantic transport predates verified byte-lock acquisition.'
  }
  if ([long]$manifest.fixture_process_start_time_ticks -lt $guardianReadyTimeTicks) {
    throw 'Browser L3 fixture predates verified byte-lock acquisition.'
  }

  if (-not (Test-ProcessGeneration -ProcessId $guardianPid -ProcessName ([string]$manifest.guardian_process_name) -StartTimeTicks ([long]$manifest.guardian_process_start_time_ticks))) { throw 'Browser byte-lock guardian generation was not live at Finish Gate start.' }
  if (-not (Test-ProcessGeneration -ProcessId ([int]$manifest.semantic_transport_pid) -ProcessName ([string]$manifest.semantic_transport_process_name) -StartTimeTicks ([long]$manifest.semantic_transport_process_start_time_ticks))) { throw 'Direct semantic transport process generation drifted before Finish Gate.' }
  if (-not (Test-ProcessGeneration -ProcessId $fixturePid -ProcessName ([string]$manifest.fixture_process_name) -StartTimeTicks ([long]$manifest.fixture_process_start_time_ticks))) { throw 'Browser L3 fixture process generation was not live at Finish Gate proof time.' }

  $freezeUri = [System.Uri]::new([System.Uri]([string]$manifest.start_url), '__gate/freeze')
  $freezeResponse = Invoke-RestMethod -Uri $freezeUri -Method Post -Headers @{ 'X-Gate-Token' = [string]$manifest.gate_token } -TimeoutSec 5
  if ([string]$freezeResponse.status -ne 'frozen' -or [string]$freezeResponse.generation -cne [string]$manifest.fixture_generation) { throw 'Browser L3 fixture did not enter the expected frozen generation.' }
  $health = Invoke-RestMethod -Uri ([System.Uri]::new([System.Uri]([string]$manifest.start_url), 'health')) -Method Get -TimeoutSec 5
  if (-not [bool]$health.frozen -or [string]$health.generation -cne [string]$manifest.fixture_generation) { throw 'Browser L3 fixture health did not confirm the frozen generation.' }

  if (-not (Test-ProcessGeneration -ProcessId $guardianPid -ProcessName ([string]$manifest.guardian_process_name) -StartTimeTicks ([long]$manifest.guardian_process_start_time_ticks))) { throw 'Browser byte-lock guardian did not remain live through fixture freeze.' }
  if (-not (Test-ProcessGeneration -ProcessId ([int]$manifest.semantic_transport_pid) -ProcessName ([string]$manifest.semantic_transport_process_name) -StartTimeTicks ([long]$manifest.semantic_transport_process_start_time_ticks))) { throw 'Direct semantic transport process generation changed during Browser L3 run.' }

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
    'scripts/semantic-projection-runtime.ps1',
    'scripts/source-provenance-gate.py',
    'scripts/stage26-browser-byte-lock-guardian.ps1',
    'scripts/prepare-browser-real-task-gate.ps1',
    'scripts/check-browser-real-task-gate.ps1',
    'tests/fixtures/browser_real_task_server.mjs'
  )
  $recheckPath = Join-Path $QualificationRoot 'finish-provenance-revalidation.json'
  $python = (Get-Command python.exe -ErrorAction Stop).Source
  $provenanceArgs = @($frozenProvenancePath, '--repo-root', $sourceRoot, '--expected-head', $ExpectedHead, '--output', $recheckPath)
  foreach ($asset in $criticalAssets) { $provenanceArgs += @('--asset', $asset) }
  $provenanceArgs += @('--lockfile', 'runtime/semantic-projection/package-lock.json')
  & $python @provenanceArgs
  if ($LASTEXITCODE -ne 0) { throw 'Browser L3 source provenance revalidation failed.' }
  $recheck = Get-Content -LiteralPath $recheckPath -Raw -Encoding utf8 | ConvertFrom-Json
  if ([string]$recheck.status -ne 'pass' -or [string]$recheck.actual_head -ne $ExpectedHead -or -not [bool]$recheck.working_tree_clean -or -not [bool]$recheck.tracked_diff_empty -or -not [bool]$recheck.untracked_empty) { throw 'Browser L3 source provenance revalidation did not PASS.' }

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
    @('scripts\semantic-direct-controller.ps1', 'scripts\semantic-direct-controller.ps1'),
    @('scripts\semantic-projection-runtime.ps1', 'scripts\semantic-projection-runtime.ps1')
  )
  foreach ($mapping in $installedMappings) {
    if (-not (Test-InstalledAssetMatch -SourcePath (Join-Path $sourceRoot ([string]$mapping[0])) -InstalledPath (Join-Path $appRoot ([string]$mapping[1])))) { throw "Installed Browser L3 runtime byte drift: $([string]$mapping[0])" }
  }

  $sourceLockPath = Join-Path $sourceRoot 'runtime\semantic-projection\package-lock.json'
  $packageLockSha256 = Get-Sha256 -Path $sourceLockPath
  if ($packageLockSha256 -cne [string]$initialInstalled.package_lock_sha256) { throw 'Browser L3 package-lock bytes drifted during run.' }

  $installedNodeModulesRoot = Join-Path $appRoot 'runtime\semantic-projection\node_modules'
  if (-not (Test-Path -LiteralPath $installedNodeModulesRoot -PathType Container)) { throw 'Installed semantic Node dependency tree is missing during revalidation.' }
  $lockMarkerRelativePath = '.chat-agent-platform-lock.sha256'
  $lockMarkerPath = Join-Path $installedNodeModulesRoot $lockMarkerRelativePath
  if (-not (Test-Path -LiteralPath $lockMarkerPath -PathType Leaf)) { throw 'Installed semantic runtime lock marker is missing during revalidation.' }
  $appliedLockSha256 = (Get-Content -LiteralPath $lockMarkerPath -Raw -Encoding utf8).Trim().ToLowerInvariant()
  if ($appliedLockSha256 -cne $packageLockSha256) { throw 'Installed semantic runtime lock marker drifted from the exact package-lock SHA-256.' }

  $installedNodeModulesDigest = Get-DirectoryDigest -Root $installedNodeModulesRoot -ExcludeRelativePath @($lockMarkerRelativePath)
  if ($installedNodeModulesDigest -cne [string]$dependencyTree.installed_directory_sha256) {
    throw 'Installed full semantic Node dependency-tree bytes drifted during Browser L3 run.'
  }
  if ([string]$dependencyTree.reference_directory_sha256 -cne [string]$dependencyTree.installed_directory_sha256) {
    throw 'Initial installed semantic Node dependency tree was not identical to fresh exact-lock npm-ci materialization.'
  }

  if (-not (Test-ProcessGeneration -ProcessId $guardianPid -ProcessName ([string]$manifest.guardian_process_name) -StartTimeTicks ([long]$manifest.guardian_process_start_time_ticks))) { throw 'Browser byte-lock guardian did not remain live through final provenance revalidation.' }

  $snapshotPath = Join-Path $fixtureRoot 'frozen-snapshot.json'
  if (-not (Test-Path -LiteralPath $snapshotPath -PathType Leaf)) { throw 'Frozen Browser L3 atomic snapshot is missing.' }
  $snapshot = Get-Content -LiteralPath $snapshotPath -Raw -Encoding utf8 | ConvertFrom-Json
  if (-not [bool]$snapshot.frozen -or [string]$snapshot.fixture_generation -cne [string]$manifest.fixture_generation) { throw 'Frozen Browser L3 snapshot generation mismatch.' }
  $finish = $snapshot.finish
  $state = $snapshot.state
  $seed = $snapshot.seed
  $audit = @($snapshot.audit)

  foreach ($name in @('target_exists', 'address_exact', 'status_exact', 'comment_exact', 'old_address_absent_in_target', 'decoys_unchanged', 'only_target_ever_mutated')) {
    $property = $finish.checks.PSObject.Properties[$name]
    if ($null -eq $property -or -not [bool]$property.Value) { throw "FINISH_CHECK_FAILED=$name" }
  }
  if ([string]$finish.status -ne 'done') { throw "FINISH_GATE_NOT_DONE status=$($finish.status)" }
  $targetId = [string]$seed.target_id
  if ([string]$finish.target_id -ne $targetId) { throw 'Finish Gate target identity drifted.' }
  if ([int]$finish.save_count -ne 1) { throw "Browser L3 requires exactly one persisted save; observed=$($finish.save_count)" }
  $mutated = @($finish.mutated_ids)
  if ($mutated.Count -ne 1 -or [string]$mutated[0] -ne $targetId) { throw "UNEXPECTED_MUTATION_SET=$($mutated -join ',')" }
  $target = @($state.cases | Where-Object { [string]$_.id -eq $targetId })
  if ($target.Count -ne 1) { throw 'Target case missing or duplicated in final snapshot.' }
  if ([string]$target[0].address -ne [string]$seed.expected.address) { throw 'Final address mismatch.' }
  if ([string]$target[0].status -ne [string]$seed.expected.status) { throw 'Final status mismatch.' }
  if ([string]$target[0].comment -ne [string]$seed.expected.comment) { throw 'Final comment mismatch.' }
  $auditCount = $audit.Count
  if ($auditCount -ne 1) { throw "Browser L3 requires exactly one audit mutation; observed=$auditCount" }
  if ([string]$audit[0].id -ne $targetId -or [string]$audit[0].event -ne 'save') { throw 'Frozen Browser L3 audit mutation does not identify the single target save.' }
  $validated = $true
}
catch { $mainError = $_ }
finally {
  $fixtureCleanupPass = Stop-VerifiedProcessSafely -ProcessId $fixturePid -ProcessName ([string]$manifest.fixture_process_name) -StartTimeTicks ([long]$manifest.fixture_process_start_time_ticks)
  $guardianCurrent = Get-Process -Id $guardianPid -ErrorAction SilentlyContinue
  if ($null -eq $guardianCurrent) {
    $guardianCleanupPass = $true
  }
  elseif (Test-ProcessGeneration -ProcessId $guardianPid -ProcessName ([string]$manifest.guardian_process_name) -StartTimeTicks ([long]$manifest.guardian_process_start_time_ticks)) {
    try {
      [System.IO.File]::WriteAllText([string]$manifest.guardian_stop_path, "stop`n", [System.Text.UTF8Encoding]::new($false))
      $guardianCurrent.Refresh()
      $guardianCurrent.WaitForExit(5000) | Out-Null
    } catch { }
    $guardianCleanupPass = Stop-VerifiedProcessSafely -ProcessId $guardianPid -ProcessName ([string]$manifest.guardian_process_name) -StartTimeTicks ([long]$manifest.guardian_process_start_time_ticks)
  }
  else { $guardianCleanupPass = $false }
  Write-Host "FIXTURE_CLEANUP_PASS=$fixtureCleanupPass"
  Write-Host "BYTE_LOCK_GUARDIAN_CLEANUP_PASS=$guardianCleanupPass"
}

if ($null -ne $mainError) { throw $mainError }
if (-not $fixtureCleanupPass) { throw 'Browser L3 fixture cleanup failed.' }
if (-not $guardianCleanupPass) { throw 'Browser L3 byte-lock guardian cleanup failed.' }
if (-not $validated) { throw 'Browser L3 Finish Gate validation did not complete.' }

Write-Host '===== STAGE 26.3B BROWSER REAL-TASK PROVENANCE FINISH GATE ====='
Write-Host "EXACT_HEAD=$ExpectedHead"
Write-Host 'SOURCE_PROVENANCE_GATE=PASS'
Write-Host 'INSTALLED_RUNTIME_PROVENANCE=PASS'
Write-Host 'NODE_RUNTIME_EXACT_LOCK_MATERIALIZATION=PASS'
Write-Host 'PLAYWRIGHT_EXACT_LOCK_MATERIALIZATION=PASS'
Write-Host 'BYTE_LOCK_GUARDIAN=PASS'
Write-Host 'FROZEN_FINISH_GATE_CODE=PASS'
Write-Host 'SOURCE_PROVENANCE_REVALIDATED=PASS'
Write-Host 'INSTALLED_RUNTIME_REVALIDATED=PASS'
Write-Host 'PROVENANCE_REVALIDATION=PASS'
Write-Host 'ATOMIC_FINAL_SNAPSHOT=PASS'
Write-Host 'SEMANTIC_TRANSPORT_GENERATION=PASS'
Write-Host 'EVIDENCE_OUTSIDE_CHAT_WORKSPACE=True'
Write-Host 'TARGET_FINAL_STATE=True'
Write-Host 'DECOYS_UNCHANGED=True'
Write-Host 'ONLY_TARGET_EVER_MUTATED=True'
Write-Host 'FIXTURE_PROCESS_WAS_LIVE=True'
Write-Host "TARGET_CASE=$targetId"
Write-Host 'SAVE_COUNT=1'
Write-Host "AUDIT_COUNT=$auditCount"
Write-Host 'EXTERNAL_FINISH_GATE=DONE'
Write-Host 'NON_TARGET_MUTATION=none'
Write-Host 'FIXTURE_CLEANUP_PASS=True'
Write-Host 'BYTE_LOCK_GUARDIAN_CLEANUP_PASS=True'
Write-Host 'STAGE26_3B_BROWSER_REAL_TASK_GATE=PASS'
