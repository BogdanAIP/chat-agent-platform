param(
  [Parameter(Mandatory = $true)]
  [string]$QualificationRoot,
  [string]$ExpectedHead = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$QualificationRoot = (Resolve-Path -LiteralPath $QualificationRoot).Path
$manifestPath = Join-Path $QualificationRoot 'gate-manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
  throw "Gate manifest missing: $manifestPath"
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($ExpectedHead -and [string]$manifest.exact_head -ne $ExpectedHead) {
  throw "EXACT_HEAD_MISMATCH expected=$ExpectedHead actual=$($manifest.exact_head)"
}

$fixtureRoot = [string]$manifest.fixture_root
$workspaceRoot = [string]$manifest.workspace_root
if (-not $fixtureRoot -or -not (Test-Path -LiteralPath $fixtureRoot -PathType Container)) {
  throw 'Fixture root missing or invalid.'
}
if (-not $workspaceRoot -or -not (Test-Path -LiteralPath $workspaceRoot -PathType Container)) {
  throw 'Workspace root missing or invalid.'
}

$fixtureFull = [System.IO.Path]::GetFullPath($fixtureRoot).TrimEnd('\')
$workspaceFull = [System.IO.Path]::GetFullPath($workspaceRoot).TrimEnd('\')
if ($fixtureFull.StartsWith($workspaceFull + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
  throw 'Fixture evidence must not live inside the Chat workspace root.'
}

$finishPath = Join-Path $fixtureRoot 'finish-gate.json'
$statePath = Join-Path $fixtureRoot 'server-state.json'
$auditPath = Join-Path $fixtureRoot 'audit.jsonl'
$seedPath = Join-Path $fixtureRoot 'fixture-seed.json'
foreach ($path in @($finishPath, $statePath, $seedPath)) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required gate evidence missing: $path" }
}

$finish = Get-Content -LiteralPath $finishPath -Raw | ConvertFrom-Json
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
$seed = Get-Content -LiteralPath $seedPath -Raw | ConvertFrom-Json

$requiredChecks = @(
  'target_exists',
  'address_exact',
  'status_exact',
  'comment_exact',
  'old_address_absent_in_target',
  'decoys_unchanged',
  'only_target_ever_mutated'
)

if ([string]$finish.status -ne 'done') {
  throw "FINISH_GATE_NOT_DONE status=$($finish.status)"
}
foreach ($name in $requiredChecks) {
  $property = $finish.checks.PSObject.Properties[$name]
  if ($null -eq $property -or -not [bool]$property.Value) {
    throw "FINISH_CHECK_FAILED=$name"
  }
}

$targetId = [string]$seed.target_id
if ([string]$finish.target_id -ne $targetId) { throw 'Finish Gate target identity drifted.' }
if ([int]$finish.save_count -lt 1) { throw 'No persisted save was observed.' }

$mutated = @($finish.mutated_ids)
if ($mutated.Count -ne 1 -or [string]$mutated[0] -ne $targetId) {
  throw "UNEXPECTED_MUTATION_SET=$($mutated -join ',')"
}

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
    if ([string]$entry.id -ne $targetId) {
      throw "AUDIT_WRONG_TARGET_MUTATION=$($entry.id)"
    }
  }
}
if ($auditCount -lt 1) { throw 'Audit contains no persisted mutation.' }

Write-Host 'STAGE26_3B_BROWSER_REAL_TASK_GATE=PASS'
Write-Host "EXACT_HEAD=$($manifest.exact_head)"
Write-Host "QUALIFICATION_ROOT=$QualificationRoot"
Write-Host "TARGET_CASE=$targetId"
Write-Host "SAVE_COUNT=$($finish.save_count)"
Write-Host "AUDIT_COUNT=$auditCount"
Write-Host 'FINISH_GATE=done'
Write-Host 'NON_TARGET_MUTATION=none'
