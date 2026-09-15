param(
    [ValidateSet('pass142', 'stale140', 'findings146', 'privatebundle140', 'libraryfile140', 'exact')]
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
foreach ($path in @($CollectorPath, $BundleBuilderPath, $ManifestPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Temporary reviewer experiment file is missing: $path"
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
    libraryfile140 = [ordered]@{
        PrNumber = 0
        BaseSha = 'b10a5fa3122bb6c76c12d37d67911b88e5e1ce28'
        HeadSha = '7077ecb8496ee89530cbe5efaa1b2112e7be330f'
        SkillVersion = '1.0'
        Focus = 'ChatGPT Library private repository semantic control'
    }
}

if ($Control -eq 'exact') {
    if ($TargetPrNumber -notmatch '^\d+$') { throw 'Control=exact requires -TargetPrNumber as decimal digits.' }
    if ($TargetBaseSha -notmatch '^[0-9a-f]{40}$') { throw 'Control=exact requires -TargetBaseSha as exactly 40 lowercase hex characters.' }
    if ($TargetHeadSha -notmatch '^[0-9a-f]{40}$') { throw 'Control=exact requires -TargetHeadSha as exactly 40 lowercase hex characters.' }
    if ($TargetSkillVersion -notin @('1.0', '1.1')) { throw 'Control=exact requires -TargetSkillVersion 1.0 or 1.1.' }
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
$libraryMode = $Control -eq 'libraryfile140'
$localEvidenceMode = $bundleMode -or $libraryMode
$runId = 'tmprev-' + [Guid]::NewGuid().ToString('N')

function New-HexToken([int]$Bytes) {
    $buffer = [byte[]]::new($Bytes)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($buffer)
    return -join ($buffer | ForEach-Object { $_.ToString('x2') })
}
function Encode-QueryValue([string]$Value) { return [Uri]::EscapeDataString($Value) }
function Normalize-ReviewText([string]$Value) {
    if ($null -eq $Value) { return '' }
    return (($Value -replace '\\_', '_') -replace "`r`n?", "`n")
}

$collectorToken = New-HexToken 32
$bundleNonce = New-HexToken 32
$completionMarker = "CAP_TEMP_REVIEW_COMPLETE=$runId"
$libraryFilename = "cap-private-review-$runId.txt"
$OutputRoot = Join-Path $env:LOCALAPPDATA "ChatAgentPlatform\experiments\temporary-reviewer\$runId"
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$resultPath = Join-Path $OutputRoot 'result.json'
$progressPath = Join-Path $OutputRoot 'progress.json'
$stdoutPath = Join-Path $OutputRoot 'collector.stdout.log'
$stderrPath = Join-Path $OutputRoot 'collector.stderr.log'
$bundlePath = Join-Path $OutputRoot $libraryFilename

$python = Get-Command 'python.exe' -ErrorAction SilentlyContinue
if ($null -eq $python) { $python = Get-Command 'python' -ErrorAction Stop }

$bundleSha256 = ''
$bundleBytes = 0
if ($localEvidenceMode) {
    & $python.Source $BundleBuilderPath --repo-root $RepoRoot --base-sha $target.BaseSha --head-sha $target.HeadSha --bundle-nonce $bundleNonce --output $bundlePath
    if ($LASTEXITCODE -ne 0) { throw "Private review bundle builder failed with exit code $LASTEXITCODE." }
    $bundleSha256 = (Get-FileHash -LiteralPath $bundlePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $bundleBytes = (Get-Item -LiteralPath $bundlePath).Length
}

if ($bundleMode) {
    $prompt = @"
CAP_TEMP_REVIEW_RUN_ID=$runId

PRIVATE_BUNDLE_CONTROL_V1

This is a non-authoritative physical quality experiment that models a PRIVATE repository. A read-only evidence bundle will be injected into this same message automatically before Send.

Use ONLY that injected REVIEW_EVIDENCE_BUNDLE_V1. Do not use built-in web search, GitHub, apps/plugins, APIs, or any external repository/source. Do not ask the user for more evidence. Treat the bundle manifest identity as frozen; do not require a live PR lookup.

Perform the strongest independent semantic/adversarial review supported by the bundled code-review policy. Search for concrete correctness, security, recovery, concurrency, identity, authority and acceptance defects introduced by the exact bundled diff. Falsify candidate findings before reporting them.

Return exactly this experiment header followed by supported finding bodies when applicable:
PRIVATE_BUNDLE_REVIEW_RESULT_V1
bundle_nonce=<copy the exact bundle_nonce from REVIEW_EVIDENCE_BUNDLE_V1>
evidence_source=bundle_only
external_web_used=no|yes
status=PASS|FINDINGS|ABSTAIN
reported_findings=<count>

If the bundle is insufficient, return ABSTAIN rather than using web.

When the review is completely finished, append exactly this line as the final line of your final response:
$completionMarker
"@
}
elseif ($libraryMode) {
    $prompt = @"
CAP_TEMP_REVIEW_RUN_ID=$runId

LIBRARY_PRIVATE_CONTROL_V1

This is a non-authoritative physical quality experiment that models a PRIVATE repository. A read-only review package named $libraryFilename will be attached automatically from ChatGPT Library before Send.

Treat the attached REVIEW_EVIDENCE_BUNDLE_V1 as the sole source of repository/code truth. Do not use GitHub or web search to locate, reconstruct, or supplement the private repository, and do not search the web for unique identifiers or code snippets copied from the attached package.

You MAY use built-in web search for general public technical documentation or engineering research needed to validate semantics. Keep such searches generic and do not include private repository names, internal identifiers or code snippets.

Treat the package manifest identity as frozen; do not require a live PR lookup. Perform the strongest independent semantic/adversarial review supported by the attached code-review policy. Search for concrete correctness, security, recovery, concurrency, identity, authority and acceptance defects introduced by the exact bundled diff. Falsify candidate findings before reporting them.

Return exactly this experiment header followed by supported finding bodies when applicable:
LIBRARY_PRIVATE_REVIEW_RESULT_V1
evidence_nonce=<copy the exact bundle_nonce from the attached REVIEW_EVIDENCE_BUNDLE_V1>
evidence_source=library_file
external_research_used=no|yes
status=PASS|FINDINGS|ABSTAIN
reported_findings=<count>

If the attached file is missing, unreadable or insufficient for repository/code evidence, return ABSTAIN. Do not replace missing private repository evidence with GitHub/web lookup.

When the review is completely finished, append exactly this line as the final line of your final response:
$completionMarker
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

Do not ask follow-up questions. If required evidence cannot be obtained, return a truthful REVIEW_RESULT_V1 with status=ABSTAIN. Otherwise return only concrete findings that survive the skill's falsification requirements. Do not edit the repository or PR.

When the review is completely finished, append exactly this line as the final line of your final response:
$completionMarker
"@
}
$prompt = $prompt.Trim()

if ($libraryMode) {
    $url = 'https://chatgpt.com/?cap_library_stage=1' +
        '&cap_run_id=' + (Encode-QueryValue $runId) +
        '&cap_collector_token=' + (Encode-QueryValue $collectorToken) +
        '&cap_bundle_sha256=' + (Encode-QueryValue $bundleSha256) +
        '&cap_library_filename=' + (Encode-QueryValue $libraryFilename) +
        '&cap_review_prompt=' + (Encode-QueryValue $prompt)
}
else {
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
}

Write-Host "TEMP_REVIEW_CONTROL=$Control" -ForegroundColor Cyan
if (-not $localEvidenceMode) { Write-Host "TEMP_REVIEW_TARGET_PR=$($target.PrNumber)" }
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
if ($libraryMode) {
    Write-Host 'TEMP_REVIEW_EVIDENCE_MODE=chatgpt_library_file' -ForegroundColor Yellow
    Write-Host "TEMP_REVIEW_LIBRARY_FILENAME=$libraryFilename"
    Write-Host "TEMP_REVIEW_LIBRARY_FILE_BYTES=$bundleBytes"
    Write-Host "TEMP_REVIEW_LIBRARY_FILE_SHA256=$bundleSha256"
    Write-Host 'TEMP_REVIEW_LIBRARY_NONCE_DISCLOSED_TO_PROMPT=False' -ForegroundColor Green
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
if ($localEvidenceMode) { $collectorArgs += @('--bundle-path', $bundlePath) }
$collector = Start-Process -FilePath $python.Source -ArgumentList $collectorArgs -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath

try {
    $health = "http://127.0.0.1:$Port/health"
    $ready = $false
    for ($attempt = 0; $attempt -lt 50; $attempt++) {
        if ($collector.HasExited) { break }
        try {
            $response = Invoke-RestMethod -Method Get -Uri $health -TimeoutSec 2
            if ([string]$response.status -eq 'ready' -and [string]$response.run_id -eq $runId) { $ready = $true; break }
        }
        catch {}
        Start-Sleep -Milliseconds 200
    }
    if (-not $ready) {
        $stderr = if (Test-Path -LiteralPath $stderrPath) { (Get-Content -LiteralPath $stderrPath -Raw).Trim() } else { '' }
        throw "Temporary reviewer collector did not become ready. $stderr"
    }

    Write-Host 'TEMP_REVIEW_COLLECTOR=ready' -ForegroundColor Green
    if ($libraryMode) {
        Write-Host 'TEMP_REVIEW_LAUNCHING=regular-chat-library-stage-then-temporary-chat' -ForegroundColor Cyan
    }
    else {
        Write-Host 'TEMP_REVIEW_LAUNCHING=non-personalized-temporary-chat' -ForegroundColor Cyan
    }
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
                Write-Host "TEMP_REVIEW_BUNDLE_INJECTED=$($result.diagnostics.bundle_injected)"
                Write-Host "TEMP_REVIEW_VISIBLE_WEB_ACTIVITY_COUNT=$(@($result.diagnostics.visible_web_activity).Count)"
            }
            if ($libraryMode) {
                Write-Host "TEMP_REVIEW_LIBRARY_FILE_ATTACHED=$($result.diagnostics.library_file_attached)"
                Write-Host "TEMP_REVIEW_LIBRARY_FILENAME_CAPTURED=$($result.diagnostics.library_filename)"
                Write-Host "TEMP_REVIEW_LIBRARY_VISIBLE_WEB_ACTIVITY_COUNT=$(@($result.diagnostics.visible_web_activity).Count)"
                if ($null -ne $result.diagnostics.identity.external_research_used) {
                    Write-Host "TEMP_REVIEW_EXTERNAL_RESEARCH_USED=$($result.diagnostics.identity.external_research_used)"
                }
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
    if (-not $collector.HasExited) { Stop-Process -Id $collector.Id -Force -ErrorAction SilentlyContinue }
    $collector.Dispose()
}
