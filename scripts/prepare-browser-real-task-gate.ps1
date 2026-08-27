[CmdletBinding()]
param(
  [string]$SourceRoot = (Split-Path -Parent $PSScriptRoot),
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^[0-9a-fA-F]{40}$')]
  [string]$ExpectedHead
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

function Get-NodeModulePath {
  param([Parameter(Mandatory = $true)][string]$Root, [Parameter(Mandatory = $true)][string]$PackageName)
  return Join-Path $Root ("node_modules\" + $PackageName.Replace('/', '\'))
}

function Get-DirectSemanticTransport {
  param([Parameter(Mandatory = $true)][string]$LocalRoot)
  $healthUrlFile = Join-Path $LocalRoot 'state\semantic-direct-health.url'
  $healthPattern = [regex]::Escape($healthUrlFile)
  $matches = @(
    Get-CimInstance Win32_Process -ErrorAction Stop |
      Where-Object {
        [string]$_.Name -ieq 'tunnel-client.exe' -and
        [string]$_.CommandLine -match '(?i)--mcp\.command' -and
        [string]$_.CommandLine -match $healthPattern
      }
  )
  if ($matches.Count -ne 1) { throw "Expected exactly one direct semantic transport process; observed=$($matches.Count)" }
  $process = Get-Process -Id ([int]$matches[0].ProcessId) -ErrorAction Stop
  $process.Refresh()
  return [ordered]@{
    pid = $process.Id
    process_name = $process.ProcessName
    process_start_time_ticks = $process.StartTime.ToUniversalTime().Ticks
    command_line = [string]$matches[0].CommandLine
  }
}

$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path
$ExpectedHead = $ExpectedHead.ToLowerInvariant()
$actualHead = (& git.exe -C $SourceRoot rev-parse HEAD 2>$null | Select-Object -Last 1).Trim().ToLowerInvariant()
if ($LASTEXITCODE -ne 0 -or -not $actualHead) { throw 'Unable to resolve source HEAD.' }
if ($actualHead -cne $ExpectedHead) { throw "EXACT_HEAD_MISMATCH expected=$ExpectedHead actual=$actualHead" }

$node = (Get-Command node.exe -ErrorAction Stop).Source
$npm = (Get-Command npm.cmd -ErrorAction Stop).Source
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
$dependencyReferenceRoot = Join-Path $qualificationRoot 'dependency-reference'
New-Item -ItemType Directory -Force -Path $workspaceRoot, $fixtureRoot, $frozenGateRoot, $dependencyReferenceRoot | Out-Null

$sourceProvenancePath = Join-Path $qualificationRoot 'source-provenance.json'
$installedProvenancePath = Join-Path $qualificationRoot 'installed-runtime-provenance.json'
$sourceProvenanceGate = Join-Path $SourceRoot 'scripts\source-provenance-gate.py'
$checkerScript = Join-Path $SourceRoot 'scripts\check-browser-real-task-gate.ps1'
$guardianScript = Join-Path $SourceRoot 'scripts\stage26-browser-byte-lock-guardian.ps1'

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
) { throw 'Source Provenance Gate did not produce a clean exact-head PASS.' }

$bootstrap = Join-Path $SourceRoot 'scripts\bootstrap-chat-platform.ps1'
& $pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $bootstrap
if ($LASTEXITCODE -ne 0) { throw "bootstrap-chat-platform failed: $LASTEXITCODE" }

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
$installedRecords = @()
foreach ($mapping in $installedMappings) {
  $sourcePath = Join-Path $SourceRoot ([string]$mapping[0])
  $installedPath = Join-Path $appRoot ([string]$mapping[1])
  $installedRecords += @(Get-InstalledAssetRecord -SourcePath $sourcePath -InstalledPath $installedPath -Name (([string]$mapping[0]).Replace('\', '/')))
}
$allInstalledMatch = @($installedRecords | Where-Object { -not [bool]$_.match }).Count -eq 0
if (-not $allInstalledMatch) { throw 'Installed AppRoot bytes do not match the frozen Browser L3 source head.' }

$sourcePackageRoot = Join-Path $SourceRoot 'runtime\semantic-projection'
Copy-Item -LiteralPath (Join-Path $sourcePackageRoot 'package.json') -Destination (Join-Path $dependencyReferenceRoot 'package.json') -Force
Copy-Item -LiteralPath (Join-Path $sourcePackageRoot 'package-lock.json') -Destination (Join-Path $dependencyReferenceRoot 'package-lock.json') -Force
Push-Location $dependencyReferenceRoot
try {
  & $npm ci --ignore-scripts --no-audit --no-fund
  if ($LASTEXITCODE -ne 0) { throw "Fresh npm ci from exact Browser L3 lockfile failed: $LASTEXITCODE" }
}
finally { Pop-Location }

$sourceLockPath = Join-Path $sourcePackageRoot 'package-lock.json'
$sourceLock = Get-Content -LiteralPath $sourceLockPath -Raw -Encoding utf8 | ConvertFrom-Json -AsHashtable
$installedPackageRoot = Join-Path $appRoot 'runtime\semantic-projection'
$dependencyNames = @('@playwright/mcp', 'playwright', 'playwright-core')
$dependencyRecords = @()
foreach ($packageName in $dependencyNames) {
  $lockKey = "node_modules/$packageName"
  $lockRecord = $sourceLock['packages'][$lockKey]
  if ($null -eq $lockRecord) { throw "Source package-lock is missing $packageName." }
  $lockVersion = [string]$lockRecord['version']
  $lockIntegrity = [string]$lockRecord['integrity']
  if (-not $lockVersion -or -not $lockIntegrity) { throw "Source package-lock lacks version/integrity for $packageName." }

  $installedPath = Get-NodeModulePath -Root $installedPackageRoot -PackageName $packageName
  $referencePath = Get-NodeModulePath -Root $dependencyReferenceRoot -PackageName $packageName
  foreach ($path in @($installedPath, $referencePath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Container)) { throw "Dependency package missing: $path" }
  }
  $installedManifest = Get-Content -LiteralPath (Join-Path $installedPath 'package.json') -Raw -Encoding utf8 | ConvertFrom-Json
  $referenceManifest = Get-Content -LiteralPath (Join-Path $referencePath 'package.json') -Raw -Encoding utf8 | ConvertFrom-Json
  $installedDigest = Get-DirectoryDigest -Root $installedPath
  $referenceDigest = Get-DirectoryDigest -Root $referencePath
  $matchesLockMaterialization = (
    [string]$installedManifest.version -ceq $lockVersion -and
    [string]$referenceManifest.version -ceq $lockVersion -and
    $installedDigest -ceq $referenceDigest
  )
  $dependencyRecords += @([ordered]@{
    package = $packageName
    lock_version = $lockVersion
    lock_integrity = $lockIntegrity
    installed_version = [string]$installedManifest.version
    reference_version = [string]$referenceManifest.version
    installed_directory_sha256 = $installedDigest
    reference_directory_sha256 = $referenceDigest
    match = $matchesLockMaterialization
  })
}
$allDependenciesMatch = @($dependencyRecords | Where-Object { -not [bool]$_.match }).Count -eq 0
if (-not $allDependenciesMatch) { throw 'Installed Playwright dependency bytes do not match fresh exact-lock npm-ci materialization.' }

$installedEvidence = [ordered]@{
  schema_version = 3
  exact_head = $ExpectedHead
  source_root = $SourceRoot
  installed_root = $appRoot
  all_match = $allInstalledMatch
  dependencies_match_exact_lock = $allDependenciesMatch
  package_lock_sha256 = Get-Sha256 -Path $sourceLockPath
  npm_version = (& $npm --version).Trim()
  node_version = (& $node --version).Trim()
  dependencies = $dependencyRecords
  assets = $installedRecords
  captured_at = (Get-Date).ToUniversalTime().ToString('o')
}
Write-Utf8NoBom -Path $installedProvenancePath -Content (($installedEvidence | ConvertTo-Json -Depth 8) + "`n")

$frozenCheckerPath = Join-Path $frozenGateRoot 'check-browser-real-task-gate.ps1'
$frozenProvenancePath = Join-Path $frozenGateRoot 'source-provenance-gate.py'
$frozenGuardianPath = Join-Path $frozenGateRoot 'stage26-browser-byte-lock-guardian.ps1'
Copy-Item -LiteralPath $checkerScript -Destination $frozenCheckerPath -Force
Copy-Item -LiteralPath $sourceProvenanceGate -Destination $frozenProvenancePath -Force
Copy-Item -LiteralPath $guardianScript -Destination $frozenGuardianPath -Force
$checkerSourceHash = Get-Sha256 -Path $checkerScript
$frozenCheckerHash = Get-Sha256 -Path $frozenCheckerPath
$provenanceSourceHash = Get-Sha256 -Path $sourceProvenanceGate
$frozenProvenanceHash = Get-Sha256 -Path $frozenProvenancePath
$guardianSourceHash = Get-Sha256 -Path $guardianScript
$frozenGuardianHash = Get-Sha256 -Path $frozenGuardianPath
if (
  $checkerSourceHash -cne $frozenCheckerHash -or
  $provenanceSourceHash -cne $frozenProvenanceHash -or
  $guardianSourceHash -cne $frozenGuardianHash
) { throw 'Frozen Browser L3 checker/provenance/guardian bytes do not match exact-head source.' }

$lockPaths = [System.Collections.Generic.List[string]]::new()
foreach ($asset in $criticalAssets) { $lockPaths.Add((Join-Path $SourceRoot $asset)) }
foreach ($mapping in $installedMappings) { $lockPaths.Add((Join-Path $appRoot ([string]$mapping[1]))) }
foreach ($record in $dependencyRecords) {
  $packageRoot = Get-NodeModulePath -Root $installedPackageRoot -PackageName ([string]$record.package)
  foreach ($file in Get-ChildItem -LiteralPath $packageRoot -Recurse -File) { $lockPaths.Add($file.FullName) }
}
$lockPaths.Add($frozenCheckerPath)
$lockPaths.Add($frozenProvenancePath)
$lockPaths.Add($frozenGuardianPath)
$lockSpecPath = Join-Path $qualificationRoot 'byte-lock-spec.json'
$lockSpec = [ordered]@{
  schema_version = 1
  exact_head = $ExpectedHead
  files = @(
    $lockPaths |
      ForEach-Object { [System.IO.Path]::GetFullPath($_) } |
      Sort-Object -Unique |
      ForEach-Object { [ordered]@{ path = $_; sha256 = Get-Sha256 -Path $_ } }
  )
}
Write-Utf8NoBom -Path $lockSpecPath -Content (($lockSpec | ConvertTo-Json -Depth 6) + "`n")
$guardianReadyPath = Join-Path $qualificationRoot 'byte-lock-ready.json'
$guardianStopPath = Join-Path $qualificationRoot 'byte-lock-stop.txt'
$guardianProcess = Start-Process -FilePath $pwsh -ArgumentList @(
  '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass',
  '-File', $frozenGuardianPath,
  '-SpecPath', $lockSpecPath,
  '-ReadyPath', $guardianReadyPath,
  '-StopPath', $guardianStopPath
) -PassThru -WindowStyle Hidden
$guardianDeadline = (Get-Date).AddSeconds(15)
while (-not (Test-Path -LiteralPath $guardianReadyPath -PathType Leaf)) {
  $guardianProcess.Refresh()
  if ($guardianProcess.HasExited) { throw "Browser byte-lock guardian exited before READY: $($guardianProcess.ExitCode)" }
  if ((Get-Date) -gt $guardianDeadline) { throw 'Browser byte-lock guardian did not become ready.' }
  Start-Sleep -Milliseconds 100
}
$guardianReady = Get-Content -LiteralPath $guardianReadyPath -Raw -Encoding utf8 | ConvertFrom-Json
if ([int]$guardianReady.locked_file_count -ne @($lockSpec.files).Count) { throw 'Browser byte-lock guardian locked-file cardinality mismatch.' }

$process = $null
try {
  $platform = Join-Path $appRoot 'scripts\chat-platform.ps1'
  & $pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $platform -Action SetProfile -Profile semantic -FilesRoot $workspaceRoot -NoNotify
  if ($LASTEXITCODE -ne 0) { throw "SetProfile failed: $LASTEXITCODE" }
  & $pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $platform -Action Start -NoNotify
  if ($LASTEXITCODE -ne 0) { throw "Platform Start failed: $LASTEXITCODE" }

  $transportDeadline = (Get-Date).AddSeconds(15)
  $semanticTransport = $null
  while ($null -eq $semanticTransport) {
    try { $semanticTransport = Get-DirectSemanticTransport -LocalRoot $localRoot } catch {
      if ((Get-Date) -gt $transportDeadline) { throw }
      Start-Sleep -Milliseconds 250
    }
  }

  $targetId = "CASE-$nonce-4821"
  $decoyA = "CASE-$nonce-4827"
  $decoyB = "CASE-$nonce-4812"
  $oldAddress = "10 Old Harbor Road $nonce"
  $newAddress = "18 New Harbor Road $nonce"
  $requiredComment = "Reviewed by agent $nonce"

  $seed = [ordered]@{
    target_id = $targetId
    expected = [ordered]@{ address = $newAddress; status = 'Approved'; comment = $requiredComment }
    cases = @(
      [ordered]@{ id = $targetId; client = 'Marina Volkova'; status = 'Pending'; address = $oldAddress; comment = 'Priority customer' },
      [ordered]@{ id = $decoyA; client = 'Marina Volkova'; status = 'Pending'; address = "44 Pine Street $nonce"; comment = 'Waiting for customer' },
      [ordered]@{ id = $decoyB; client = 'Maria Volkova'; status = 'Approved'; address = "7 Lake Avenue $nonce"; comment = 'Already reviewed' }
    )
  }
  $seedPath = Join-Path $fixtureRoot 'fixture-seed.json'
  Write-Utf8NoBom -Path $seedPath -Content (($seed | ConvertTo-Json -Depth 8) + "`n")

  $serverScript = Join-Path $SourceRoot 'tests\fixtures\browser_real_task_server.mjs'
  $stdout = Join-Path $fixtureRoot 'fixture-stdout.log'
  $stderr = Join-Path $fixtureRoot 'fixture-stderr.log'
  $fixtureGeneration = ([guid]::NewGuid().ToString('N'))
  $gateToken = ([guid]::NewGuid().ToString('N')) + ([guid]::NewGuid().ToString('N'))
  $process = Start-Process -FilePath $node -ArgumentList @(
    $serverScript, '--root', $fixtureRoot, '--port', '0',
    '--gate-token', $gateToken, '--generation', $fixtureGeneration
  ) -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  Set-Content -LiteralPath (Join-Path $fixtureRoot 'fixture.pid') -Value $process.Id -Encoding ascii

  $ready = $null
  for ($i = 0; $i -lt 120; $i += 1) {
    if ($process.HasExited) {
      $err = if (Test-Path -LiteralPath $stderr) { Get-Content -LiteralPath $stderr -Raw } else { '' }
      throw "Fixture server exited before readiness. $err"
    }
    if (Test-Path -LiteralPath $stdout) {
      $line = Get-Content -LiteralPath $stdout | Where-Object { $_ -like 'READY *' } | Select-Object -Last 1
      if ($line) { $ready = ($line.Substring(6) | ConvertFrom-Json); break }
    }
    Start-Sleep -Milliseconds 100
  }
  if (-not $ready -or -not $ready.url -or [string]$ready.generation -cne $fixtureGeneration) { throw 'Fixture server did not report expected READY generation.' }

  $health = Invoke-RestMethod -Uri ($ready.url + 'health') -Method Get -TimeoutSec 5
  if ($health.status -ne 'ok' -or $health.finish -ne 'not_done' -or [bool]$health.frozen -or [string]$health.generation -cne $fixtureGeneration) {
    throw 'Fixture did not start in a clean NOT_DONE unfrozen generation.'
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

  $process.Refresh()
  $manifest = [ordered]@{
    schema_version = 4
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
    fixture_generation = $fixtureGeneration
    gate_token = $gateToken
    semantic_transport_pid = [int]$semanticTransport.pid
    semantic_transport_process_name = [string]$semanticTransport.process_name
    semantic_transport_start_time_ticks = [long]$semanticTransport.process_start_time_ticks
    guardian_pid = [int]$guardianReady.pid
    guardian_process_name = [string]$guardianReady.process_name
    guardian_process_start_time_ticks = [long]$guardianReady.process_start_time_ticks
    guardian_stop_path = $guardianStopPath
    source_provenance_path = $sourceProvenancePath
    installed_runtime_provenance_path = $installedProvenancePath
    frozen_checker_path = $frozenCheckerPath
    frozen_provenance_gate_path = $frozenProvenancePath
    frozen_guardian_path = $frozenGuardianPath
    frozen_checker_sha256 = $frozenCheckerHash
    frozen_provenance_gate_sha256 = $frozenProvenanceHash
    frozen_guardian_sha256 = $frozenGuardianHash
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
  Write-Host "SEMANTIC_TRANSPORT_PID=$([int]$semanticTransport.pid)"
  Write-Host "BYTE_LOCK_GUARDIAN_PID=$([int]$guardianReady.pid)"
  Write-Host 'SOURCE_PROVENANCE_GATE=PASS'
  Write-Host 'INSTALLED_RUNTIME_PROVENANCE=PASS'
  Write-Host 'PLAYWRIGHT_EXACT_LOCK_MATERIALIZATION=PASS'
  Write-Host 'BYTE_LOCK_GUARDIAN=PASS'
  Write-Host 'FROZEN_FINISH_GATE=PASS'
  Write-Host 'INITIAL_FINISH_GATE=NOT_DONE'
  Write-Host "CHECK_COMMAND=& '$frozenCheckerPath' -QualificationRoot '$qualificationRoot' -ExpectedHead '$ExpectedHead'"
  Write-Host 'NOTE=fixture/provenance/frozen-gate evidence is outside Chat workspace; exact source/runtime/dependency bytes are write/delete locked until Finish Gate cleanup.'
}
catch {
  if ($null -ne $process) {
    try {
      $process.Refresh()
      if (-not $process.HasExited) { $process.Kill(); $process.WaitForExit(5000) | Out-Null }
    } catch { }
  }
  try { Write-Utf8NoBom -Path $guardianStopPath -Content "stop`n" } catch { }
  try {
    $guardianProcess.Refresh()
    if (-not $guardianProcess.HasExited) { $guardianProcess.WaitForExit(5000) | Out-Null }
  } catch { }
  throw
}
