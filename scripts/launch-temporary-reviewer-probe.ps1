param(
    [ValidateSet('pass142', 'stale140', 'findings146', 'privatebundle140', 'exact')]
    [string]$Control = 'pass142',
    [string]$TargetPrNumber = '',
    [string]$TargetBaseSha = '',
    [string]$TargetHeadSha = '',
    [string]$TargetSkillVersion = '1.1',
    [ValidateRange(1024, 65535)]
    [int]$Port = 3077,
    [ValidateRange(60, 7200)]
    [int]$TimeoutSeconds = 3000,
    [switch]$NoLaunch
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$ExperimentRoot = Join-Path $RepoRoot 'experiments\chatgpt-temporary-reviewer'
$CollectorPath = Join-Path $ExperimentRoot 'collector.py'
$BundleBuilderPath = Join-Path $ExperimentRoot 'build_private_bundle.py'
$ManifestPath = Join-Path $ExperimentRoot 'manifest.json'
foreach ($requiredPath in @($CollectorPath, $BundleBuilderPath, $ManifestPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Temporary reviewer experiment file is missing: $requiredPath"
    }
}
if ($Port -ne 3077) {
    throw 'This experiment extension is intentionally pinned to loopback port 3077.'
}

$controls = @{
    pass142 = [ordered]@{
        PrNumber = 142
        BaseSha = '8318a592848cad66bb6d8e56b10b04b646bc9137'
        HeadSha = '858dcb7dd065717ea0d59b1e7b931b13a844f8d4'
        SkillVersion = '1.1'
        Focus = 'affected automatic-review fixed-procedure/state/privacy/provenance paths, focused tests, hosted CI and relevant GitHub evidence'
    }
    stale140 = [ordered]@{
        PrNumber = 140
        BaseSha = 'b10a5fa3122bb6c76c12d37d67911b88e5e1ce28'
        HeadSha = '7077ecb8496ee89530cbe5efaa1b2112e7be330f'
        SkillVersion = '1.0'
        Focus = 'affected Stage Research, reviewer authority, local-result publication/reconciliation, persistence, recovery, concurrency, identity, security and acceptance paths, focused tests, hosted CI and relevant GitHub evidence'
    }
    findings146 = [ordered]@{
        PrNumber = 146
        BaseSha = 'b10a5fa3122bb6c76c12d37d67911b88e5e1ce28'
        HeadSha = '7077ecb8496ee89530cbe5efaa1b2112e7be330f'
        SkillVersion = '1.0'
        Focus = 'affected Stage Research, reviewer authority, local-result publication/reconciliation, persistence, recovery, concurrency, identity, security and acceptance paths, focused tests, hosted CI and relevant GitHub evidence'
    }
    privatebundle140 = [ordered]@{
        PrNumber = 0
        BaseSha = 'b10a5fa3122bb6c76c12d37d67911b88e5e1ce28'
        HeadSha = '7077ecb8496ee89530cbe5efaa1b2112e7be330f'
        SkillVersion = '1.0'
        Focus = 'bundle-only private repository semantic control'
    }
}

if ($Control -eq 'exact') {
    if ($TargetPrNumber -notmatch '^\d+$') {
        throw 'Control=exact requires -TargetPrNumber as decimal digits.'
    }
    if ($TargetBaseSha -notmatch '^[0-9a-f]{40}$') {
        throw 'Control=exact requires -TargetBaseSha as exactly 40 lowercase hex characters.'
    }
    if ($TargetHeadSha -notmatch '^[0-9a-f]{40}$') {
        throw 'Control=exact requires -TargetHeadSha as exactly 40 lowercase hex characters.'
    }
    if ($TargetSkillVersion -notin @('1.0', '1.1')) {
        throw 'Control=exact requires -TargetSkillVersion 1.0 or 1.1.'
    }
    $target = [ordered]@{
        PrNumber = [int]$TargetPrNumber
        BaseSha = $TargetBaseSha
        HeadSha = $TargetHeadSha
        SkillVersion = $TargetSkillVersion
        Focus = 'affected experiment-only browser delivery, Temporary Chat qualification evidence, result capture, local collector boundaries, exact identity, failure handling, tests, hosted CI and relevant GitHub evidence'
    }
}
else {
    $target = $controls[$Control]
}

$bundleMode = $Control -eq 'privatebundle140'
$runId = 'tmprev-' + [Guid]::NewGuid().ToString('N')
$tokenBytes = [byte[]]::new(32)
[System.Security.Cryptography.RandomNumberGenerator]::Fill($tokenBytes)
$collectorToken = -join ($tokenBytes | ForEach-Object { $_.ToString('x2') })
$bundleNonceBytes = [byte[]]::new(32)
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bundleNonceBytes)
$bundleNonce = -join ($bundleNonceBytes | ForEach-Object { $_.ToString('x2') })
$completionMarker = "CAP_TEMP_REVIEW_COMPLETE=$runId"

$OutputRoot = Join-Path $env:LOCALAPPDATA "ChatAgentPlatform\experiments\temporary-reviewer\$runId"
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$resultPath = Join-Path $OutputRoot 'result.json'
$progressPath = Join-Path $OutputRoot 'progress.json'
$stdoutPath = Join-Path $OutputRoot 'collector.stdout.log'
$stderrPath = Join-Path $OutputRoot 'collector.stderr.log'
$bundlePath = Join-Path $OutputRoot 'private-review-bundle.txt'

$python = (Get-Command 'python.exe' -ErrorAction SilentlyContinue)
if ($null -eq $python) {
    $python = (Get-Command 'python' -ErrorAction Stop)
}

$bundleSha256 = ''
$bundleBytes = 0
if ($bundleMode) {
    & $python.Source $BundleBuilderPath `
        --repo-root $RepoRoot `
        --base-sha $target.BaseSha `
        --head-sha $target.HeadSha `
        --bundle-nonce $bundleNonce `
        --output $bundlePath
    if ($LASTEXITCODE -ne 0) {
        throw "Private review bundle builder failed with exit code $LASTEXITCODE."
    }
    $bundleSha256 = (Get-FileHash -LiteralPath $bundlePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $bundleBytes = (Get-Item -LiteralPath $bundlePath).Length
}

if ($bundleMode) {
    $prompt = @"
CAP_TEMP_REVIEW_RUN_ID=$runId

PRIVATE_BUNDLE_CONTROL_V1

This is a non-authoritative physical quality experiment that models a PRIVATE repository.
A read-only evidence bundle will be injected into this same message automatically before Send.

Use ONLY that injected REVIEW_EVIDENCE_BUNDLE_V1. Do not use built-in web search, GitHub, apps/plugins, APIs, or any external repository/source. Do not ask the user for more evidence. The bundle was generated from local immutable Git objects and contains the accepted BASE review policy, applicable target skills, changed-file inventory and exact BASE..HEAD diff. For this experiment, treat the bundle manifest identity as frozen; do not require a live PR lookup.

Perform the strongest independent semantic/adversarial review supported by the bundled code-review policy. Search for concrete correctness, security, recovery, concurrency, identity, authority and acceptance defects introduced by the exact bundled diff. Falsify candidate findings before reporting them. Do not infer the expected answer from this instruction.

Return exactly this experiment header followed by supported finding bodies when applicable:
PRIVATE_BUNDLE_REVIEW_RESULT_V1
bundle_nonce=<copy the exact bundle_nonce from REVIEW_EVIDENCE_BUNDLE_V1>
evidence_source=bundle_only
external_web_used=no|yes
status=PASS|FINDINGS|ABSTAIN
reported_findings=<count>

If you used any external web/repository source for any reason, set external_web_used=yes. If the bundle is insufficient, return ABSTAIN rather than using web.

When the review is completely finished, append exactly this line as the final line of your final response:
$completionMarker
Do not emit that completion line before the final result is complete.
"@
}
else {
    $prompt = @"
CAP_TEMP_REVIEW_RUN_ID=$runId

REVIEW_REQUEST_V1
repository=BogdanAIP/chat-agent-platform
pr_number=$($target.PrNumber)
base_sha=$($target.BaseSha)
head_sha=$($target.HeadSha)
review_skill=code-review
review_skill_version=$($target.SkillVersion)

Perform the repository's .agents/skills/code-review/SKILL.md independent semantic review exactly as governed by BASE_SHA.

This is an automated physical qualification probe of a fresh ordinary Temporary Chat. Remain read-only. Use only the built-in web/repository-reading capabilities available in this chat. Do not use ChatGPT Work, Codex, apps/plugins, APIs, or ask the user to paste repository evidence.

Independently resolve the live PR identity, governing BASE AGENTS.md and code-review v$($target.SkillVersion), applicable target skills from HEAD_SHA, the exact BASE_SHA..HEAD_SHA diff, $($target.Focus).

Do not ask follow-up questions. If required evidence cannot be obtained with the capabilities available in this chat, return a truthful REVIEW_RESULT_V1 with status=ABSTAIN and explain the blocking condition. Otherwise return the required REVIEW_RESULT_V1 and only concrete findings that survive the skill's falsification requirements. Do not edit the repository or PR.

When the review is completely finished, append exactly this line as the final line of your final response:
$completionMarker
Do not emit that completion line in progress updates or before the final REVIEW_RESULT_V1 is complete.
"@
}
$prompt = $prompt.Trim()

function Encode-QueryValue([string]$Value) {
    return [Uri]::EscapeDataString($Value)
}

function Normalize-ReviewText([string]$Value) {
    if ($null -eq $Value) { return '' }
    return (($Value -replace '\\_', '_') -replace "`r`n?", "`n")
}

$url = 'https://chatgpt.com/?temporary-chat=true' +
    '&cap_temp_review=1' +
    '&cap_run_id=' + (Encode-QueryValue $runId) +
    '&cap_collector_token=' + (Encode-QueryValue $collectorToken)
if ($bundleMode) {
    $url += '&cap_bundle=1' +
        '&cap_bundle_sha256=' + (Encode-QueryValue $bundleSha256) +
        '&cap_bundle_nonce=' + (Encode-QueryValue $bundleNonce)
}
$url += '&prompt=' + (Encode-QueryValue $prompt)

Write-Host "TEMP_REVIEW_CONTROL=$Control" -ForegroundColor Cyan
if (-not $bundleMode) {
    Write-Host "TEMP_REVIEW_TARGET_PR=$($target.PrNumber)"
}
Write-Host "TEMP_REVIEW_TARGET_BASE=$($target.BaseSha)"
Write-Host "TEMP_REVIEW_TARGET_HEAD=$($target.HeadSha)"
Write-Host "TEMP_REVIEW_RUN_ID=$runId" -ForegroundColor Cyan
Write-Host "TEMP_REVIEW_EXTENSION_PATH=$ExperimentRoot"
Write-Host "TEMP_REVIEW_OUTPUT_DIR=$OutputRoot"
if ($bundleMode) {
    Write-Host 'TEMP_REVIEW_EVIDENCE_MODE=local_git_bundle_only' -ForegroundColor Yellow
    Write-Host "TEMP_REVIEW_BUNDLE_BYTES=$bundleBytes"
    Write-Host "TEMP_REVIEW_BUNDLE_SHA256=$bundleSha256"
}

if ($NoLaunch) {
    Write-Host 'TEMP_REVIEW_NO_LAUNCH=True'
    Write-Host "TEMP_REVIEW_URL=$url"
    return
}

$collectorArgs = @(
    $CollectorPath,
    '--run-id', $runId,
    '--token', $collectorToken,
    '--output-dir', $OutputRoot,
    '--port', [string]$Port,
    '--timeout-seconds', [string]$TimeoutSeconds
)
if ($bundleMode) {
    $collectorArgs += @('--bundle-path', $bundlePath)
}
$collector = Start-Process `
    -FilePath $python.Source `
    -ArgumentList $collectorArgs `
    -PassThru `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath

try {
    $health = "http://127.0.0.1:$Port/health"
    $ready = $false
    for ($attempt = 0; $attempt -lt 50; $attempt++) {
        if ($collector.HasExited) { break }
        try {
            $response = Invoke-RestMethod -Method Get -Uri $health -TimeoutSec 2
            if ([string]$response.status -eq 'ready' -and [string]$response.run_id -eq $runId) {
                $ready = $true
                break
            }
        }
        catch {}
        Start-Sleep -Milliseconds 200
    }
    if (-not $ready) {
        $stderr = if (Test-Path -LiteralPath $stderrPath) { (Get-Content -LiteralPath $stderrPath -Raw).Trim() } else { '' }
        throw "Temporary reviewer collector did not become ready. $stderr"
    }

    Write-Host 'TEMP_REVIEW_COLLECTOR=ready' -ForegroundColor Green
    Write-Host 'TEMP_REVIEW_LAUNCHING=non-personalized-temporary-chat' -ForegroundColor Cyan
    Start-Process $url

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path -LiteralPath $resultPath -PathType Leaf) {
            $result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
            $normalized = Normalize-ReviewText ([string]$result.result_text)
            $statusMatch = [regex]::Match($normalized, '(?m)^\s*status\s*=\s*(PASS|FINDINGS|ABSTAIN|STALE)\s*$')
            $reviewStatus = if ([string]$result.capture_kind -eq 'structured' -and $statusMatch.Success) { $statusMatch.Groups[1].Value } else { 'UNSTRUCTURED' }
            Write-Host "TEMP_REVIEW_CAPTURE=$($result.capture_kind)" -ForegroundColor Green
            Write-Host "TEMP_REVIEW_STATUS=$reviewStatus" -ForegroundColor Green
            if ($bundleMode) {
                Write-Host "TEMP_REVIEW_BUNDLE_INJECTED=$($result.diagnostics.bundle_injected)" -ForegroundColor Green
                $webMarkers = @($result.diagnostics.visible_web_activity)
                Write-Host "TEMP_REVIEW_VISIBLE_WEB_ACTIVITY_COUNT=$($webMarkers.Count)" -ForegroundColor $(if ($webMarkers.Count -eq 0) { 'Green' } else { 'Yellow' })
            }
            if ([string]$result.capture_kind -ne 'structured' -and $null -ne $result.diagnostics.identity) {
                Write-Host "TEMP_REVIEW_IDENTITY_DIAGNOSTICS=$($result.diagnostics.identity | ConvertTo-Json -Compress -Depth 8)" -ForegroundColor Yellow
            }
            Write-Host "TEMP_REVIEW_RESULT_PATH=$resultPath" -ForegroundColor Green
            return
        }
        if ($collector.HasExited -and $collector.ExitCode -ne 0) { break }
        Start-Sleep -Seconds 1
    }

    $lastEvent = ''
    if (Test-Path -LiteralPath $progressPath -PathType Leaf) {
        $progress = Get-Content -LiteralPath $progressPath -Raw | ConvertFrom-Json
        if (@($progress.events).Count -gt 0) {
            $last = @($progress.events)[-1]
            $lastEvent = " event=$($last.event) details=$($last.details | ConvertTo-Json -Compress -Depth 6)"
        }
    }
    throw "Temporary reviewer probe ended without a captured result.$lastEvent Output=$OutputRoot"
}
finally {
    if (-not $collector.HasExited) {
        Stop-Process -Id $collector.Id -Force -ErrorAction SilentlyContinue
    }
    $collector.Dispose()
}
