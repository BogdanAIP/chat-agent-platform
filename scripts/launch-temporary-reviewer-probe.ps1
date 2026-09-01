param(
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
$ManifestPath = Join-Path $ExperimentRoot 'manifest.json'
if (-not (Test-Path -LiteralPath $CollectorPath -PathType Leaf)) {
    throw "Temporary reviewer collector is missing: $CollectorPath"
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Temporary reviewer extension manifest is missing: $ManifestPath"
}
if ($Port -ne 3077) {
    throw 'This experiment extension is intentionally pinned to loopback port 3077.'
}

$runId = 'tmprev-' + [Guid]::NewGuid().ToString('N')
$tokenBytes = [byte[]]::new(32)
[System.Security.Cryptography.RandomNumberGenerator]::Fill($tokenBytes)
$collectorToken = -join ($tokenBytes | ForEach-Object { $_.ToString('x2') })

$OutputRoot = Join-Path $env:LOCALAPPDATA "ChatAgentPlatform\experiments\temporary-reviewer\$runId"
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$resultPath = Join-Path $OutputRoot 'result.json'
$progressPath = Join-Path $OutputRoot 'progress.json'
$stdoutPath = Join-Path $OutputRoot 'collector.stdout.log'
$stderrPath = Join-Path $OutputRoot 'collector.stderr.log'

$prompt = @"
CAP_TEMP_REVIEW_RUN_ID=$runId

REVIEW_REQUEST_V1
repository=BogdanAIP/chat-agent-platform
pr_number=142
base_sha=8318a592848cad66bb6d8e56b10b04b646bc9137
head_sha=858dcb7dd065717ea0d59b1e7b931b13a844f8d4
review_skill=code-review
review_skill_version=1.1

Perform the repository's .agents/skills/code-review/SKILL.md independent semantic review exactly as governed by BASE_SHA.

This is an automated physical qualification probe of a fresh ordinary Temporary Chat. Remain read-only. Use only the built-in web/repository-reading capabilities available in this chat. Do not use ChatGPT Work, Codex, apps/plugins, APIs, or ask the user to paste repository evidence.

Independently resolve the live PR identity, governing BASE AGENTS.md and code-review v1.1, applicable target skills from HEAD_SHA, the exact BASE_SHA..HEAD_SHA diff, affected automatic-review fixed-procedure/state/privacy/provenance paths, focused tests, hosted CI and relevant GitHub evidence.

Do not ask follow-up questions. If required evidence cannot be obtained with the capabilities available in this chat, return a truthful REVIEW_RESULT_V1 with status=ABSTAIN and explain the blocking condition. Otherwise return the required REVIEW_RESULT_V1 and only concrete findings that survive the skill's falsification requirements. Do not edit the repository or PR.
"@
$prompt = $prompt.Trim()

function Encode-QueryValue([string]$Value) {
    return [Uri]::EscapeDataString($Value)
}

$url = 'https://chatgpt.com/?temporary-chat=true' +
    '&cap_temp_review=1' +
    '&cap_run_id=' + (Encode-QueryValue $runId) +
    '&cap_collector_token=' + (Encode-QueryValue $collectorToken) +
    '&prompt=' + (Encode-QueryValue $prompt)

Write-Host "TEMP_REVIEW_RUN_ID=$runId" -ForegroundColor Cyan
Write-Host "TEMP_REVIEW_EXTENSION_PATH=$ExperimentRoot"
Write-Host "TEMP_REVIEW_OUTPUT_DIR=$OutputRoot"

if ($NoLaunch) {
    Write-Host 'TEMP_REVIEW_NO_LAUNCH=True'
    Write-Host "TEMP_REVIEW_URL=$url"
    return
}

$python = (Get-Command 'python.exe' -ErrorAction SilentlyContinue)
if ($null -eq $python) {
    $python = (Get-Command 'python' -ErrorAction Stop)
}

$collectorArgs = @(
    $CollectorPath,
    '--run-id', $runId,
    '--token', $collectorToken,
    '--output-dir', $OutputRoot,
    '--port', [string]$Port,
    '--timeout-seconds', [string]$TimeoutSeconds
)
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
            $statusMatch = [regex]::Match([string]$result.result_text, '(?m)^status=(PASS|FINDINGS|ABSTAIN|STALE)$')
            $reviewStatus = if ($statusMatch.Success) { $statusMatch.Groups[1].Value } else { 'UNSTRUCTURED' }
            Write-Host "TEMP_REVIEW_CAPTURE=$($result.capture_kind)" -ForegroundColor Green
            Write-Host "TEMP_REVIEW_STATUS=$reviewStatus" -ForegroundColor Green
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
