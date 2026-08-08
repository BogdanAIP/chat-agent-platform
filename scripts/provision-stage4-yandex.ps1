param(
    [string]$ProjectId = 'demo',
    [string]$FunctionId,
    [string]$FunctionName = 'agent-platform-relay',
    [string]$ServiceAccountName = 'agent-platform-relay',
    [string]$BucketName,
    [switch]$AdoptExistingBucket,
    [switch]$SkipBuild,
    [switch]$LeaveRelayOn
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$deployScript = Join-Path $PSScriptRoot 'deploy-stage4-yandex.ps1'
$binary = Join-Path $repoRoot 'target/release/agent-platform.exe'
$evidencePath = Join-Path $repoRoot 'runtime/stage4-yandex-acceptance.json'

if (-not (Test-Path -LiteralPath $deployScript -PathType Leaf)) {
    throw "Stage 4 deployment script is missing: $deployScript"
}
if (-not (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) -or -not (Get-Command Get-Clipboard -ErrorAction SilentlyContinue)) {
    throw 'Windows clipboard commands are required for one-time GPT Actions bearer-token handoff.'
}

$deployArgs = @{
    ProjectId = $ProjectId
    FunctionName = $FunctionName
    ServiceAccountName = $ServiceAccountName
    CopyActionTokenToClipboard = $true
}
if (-not [string]::IsNullOrWhiteSpace($FunctionId)) { $deployArgs.FunctionId = $FunctionId }
if (-not [string]::IsNullOrWhiteSpace($BucketName)) { $deployArgs.BucketName = $BucketName }
if ($AdoptExistingBucket) { $deployArgs.AdoptExistingBucket = $true }
if ($SkipBuild) { $deployArgs.SkipBuild = $true }

Write-Host '[Stage 4] Provisioning/updating Yandex relay...'
$deployOutput = (& $deployScript @deployArgs | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Stage 4 Yandex deployment failed.' }
try { $deployment = $deployOutput | ConvertFrom-Json }
catch { throw "Stage 4 deployment did not return valid JSON: $deployOutput" }
if ($deployment.status -ne 'success') { throw "Stage 4 deployment returned status $($deployment.status)" }
$functionUrl = [string]$deployment.function_url
if ([string]::IsNullOrWhiteSpace($functionUrl)) { throw 'Deployment result does not contain function_url.' }
if (-not (Test-Path -LiteralPath $binary -PathType Leaf)) { throw "agent-platform binary is missing: $binary" }

$remoteToken = (Get-Clipboard -Raw).Trim()
if ($remoteToken.Length -lt 24) {
    throw 'GPT Actions bearer token was not found in the clipboard after deployment.'
}

$relayStarted = $false
$roundTripPassed = $false
$localPingResult = $null
$selfTestResult = $null
try {
    Write-Host '[Stage 4] Enabling local relay for the real round trip...'
    $startText = (& $binary --repo-root $repoRoot relay start --project-id $ProjectId | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw "relay start failed: $startText" }
    $start = $startText | ConvertFrom-Json
    if ($start.status -notin @('started','starting','already_running')) {
        throw "Unexpected relay start status: $($start.status)"
    }
    $relayStarted = $true

    Write-Host '[Stage 4] Waiting for Yandex heartbeat...'
    $online = $false
    for ($attempt = 0; $attempt -lt 45; $attempt++) {
        try {
            $health = Invoke-RestMethod -Method Get -Uri $functionUrl -TimeoutSec 10
            if ($health.status -eq 'ok' -and $health.agent_online) {
                $online = $true
                break
            }
        }
        catch {
            if ($attempt -eq 44) { throw }
        }
        Start-Sleep -Seconds 1
    }
    if (-not $online) { throw 'Yandex gateway did not observe the local relay heartbeat.' }

    $headers = @{ Authorization = "Bearer $remoteToken" }
    Write-Host '[Stage 4] Calling local_ping through the real public Yandex URL...'
    $pingBody = @{ action = 'local_ping'; message = 'Stage 4 real Yandex acceptance' } | ConvertTo-Json -Compress
    $localPingResult = Invoke-RestMethod -Method Post -Uri $functionUrl -Headers $headers -ContentType 'application/json' -Body $pingBody -TimeoutSec 45
    if ($localPingResult.status -ne 'success' -or -not $localPingResult.result.pong -or -not $localPingResult.result.executed_locally) {
        throw 'Real Yandex -> local_ping round trip did not return a validated local success.'
    }

    Write-Host '[Stage 4] Calling runtime_self_test through the real public Yandex URL...'
    $selfBody = @{ action = 'runtime_self_test' } | ConvertTo-Json -Compress
    $selfTestResult = Invoke-RestMethod -Method Post -Uri $functionUrl -Headers $headers -ContentType 'application/json' -Body $selfBody -TimeoutSec 45
    if ($selfTestResult.status -ne 'success' -or $selfTestResult.result.status -ne 'success' -or $selfTestResult.result.result.ping -ne 'pong') {
        throw 'Real Yandex -> runtime_self_test round trip did not return a validated local success.'
    }
    $roundTripPassed = $true
}
finally {
    $remoteToken = $null
    if ($relayStarted -and -not $LeaveRelayOn) {
        Write-Host '[Stage 4] Switching the local relay back off...'
        try {
            $stopText = (& $binary --repo-root $repoRoot relay stop --project-id $ProjectId | Out-String).Trim()
            if ($LASTEXITCODE -ne 0) { throw "relay stop failed: $stopText" }
            $stop = $stopText | ConvertFrom-Json
            if ($stop.status -notin @('stopped','stopping')) { throw "Unexpected relay stop status: $($stop.status)" }
        }
        catch {
            if ($roundTripPassed) { throw }
            Write-Warning "Relay cleanup after failed acceptance also failed: $($_.Exception.Message)"
        }
    }
}

if (-not $roundTripPassed) { throw 'Stage 4 real Yandex acceptance did not complete.' }

$finalHealth = Invoke-RestMethod -Method Get -Uri $functionUrl -TimeoutSec 10
if (-not $LeaveRelayOn -and $finalHealth.agent_online) {
    for ($attempt = 0; $attempt -lt 10 -and $finalHealth.agent_online; $attempt++) {
        Start-Sleep -Milliseconds 500
        $finalHealth = Invoke-RestMethod -Method Get -Uri $functionUrl -TimeoutSec 10
    }
}
if (-not $LeaveRelayOn -and $finalHealth.agent_online) {
    throw 'Relay stop completed locally but Yandex still reports the agent online.'
}

$evidence = [ordered]@{
    contract_version = 'stage4-yandex-acceptance-v1'
    status = 'success'
    verified_at = [DateTimeOffset]::UtcNow.ToString('o')
    project_id = $ProjectId
    function_id = [string]$deployment.function_id
    function_url = $functionUrl
    bucket = [string]$deployment.bucket
    service_account_id = [string]$deployment.service_account_id
    bucket_runtime_role = [string]$deployment.bucket_runtime_role
    local_ping = [ordered]@{
        pong = [bool]$localPingResult.result.pong
        executed_locally = [bool]$localPingResult.result.executed_locally
    }
    runtime_self_test = [ordered]@{
        status = [string]$selfTestResult.result.status
        ping = [string]$selfTestResult.result.result.ping
        controlled_write_read = [string]$selfTestResult.result.result.controlled_write_read
        cleanup = [string]$selfTestResult.result.result.cleanup
    }
    relay_left_enabled = [bool]$LeaveRelayOn
    remote_bearer_returned = $false
    agent_token_returned = $false
}
$directory = Split-Path -Parent $evidencePath
New-Item -ItemType Directory -Path $directory -Force | Out-Null
$evidence | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $evidencePath -Encoding utf8
$evidence | ConvertTo-Json -Depth 8
