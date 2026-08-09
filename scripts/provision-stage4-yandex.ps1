param(
    [string]$ProjectId = 'demo',
    [string]$FunctionId,
    [string]$FunctionName = 'agent-platform-relay',
    [string]$GatewayName = 'agent-platform-relay-gateway',
    [string]$ServiceAccountName = 'agent-platform-relay',
    [string]$BucketName,
    [switch]$AdoptExistingBucket,
    [switch]$RotateTokens,
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
    GatewayName = $GatewayName
    ServiceAccountName = $ServiceAccountName
    CopyActionTokenToClipboard = $true
}
if (-not [string]::IsNullOrWhiteSpace($FunctionId)) { $deployArgs.FunctionId = $FunctionId }
if (-not [string]::IsNullOrWhiteSpace($BucketName)) { $deployArgs.BucketName = $BucketName }
if ($AdoptExistingBucket) { $deployArgs.AdoptExistingBucket = $true }
if ($RotateTokens) { $deployArgs.RotateTokens = $true }
if ($SkipBuild) { $deployArgs.SkipBuild = $true }

Write-Host '[Stage 4] Provisioning/updating Yandex relay...'
$deployOutput = (& $deployScript @deployArgs | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Stage 4 Yandex deployment failed.' }
try { $deployment = $deployOutput | ConvertFrom-Json }
catch { throw "Stage 4 deployment did not return valid JSON: $deployOutput" }
if ($deployment.status -ne 'success') { throw "Stage 4 deployment returned status $($deployment.status)" }
$functionUrl = [string]$deployment.endpoint_url
if ([string]::IsNullOrWhiteSpace($functionUrl)) { $functionUrl = [string]$deployment.gateway_url }
if ([string]::IsNullOrWhiteSpace($functionUrl)) { $functionUrl = [string]$deployment.function_url }
if ([string]::IsNullOrWhiteSpace($functionUrl)) { throw 'Deployment result does not contain function_url.' }
if (-not (Test-Path -LiteralPath $binary -PathType Leaf)) { throw "agent-platform binary is missing: $binary" }

$remoteToken = (Get-Clipboard -Raw).Trim()
if ($remoteToken.Length -lt 24) {
    throw 'GPT Actions bearer token was not found in the clipboard after deployment.'
}
$headers = @{ Authorization = "Bearer $remoteToken" }

$relayStarted = $false
$roundTripPassed = $false
$localPingResult = $null
$selfTestResult = $null
try {
    Write-Host '[Stage 4] Enabling local relay for the real round trip...'
    # Do not capture this command through a PowerShell native pipeline on Windows:
    # the detached worker can keep the pipeline handle open after the launcher exits.
    $startInfo = [Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $binary
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    foreach ($argument in @('--repo-root',$repoRoot,'relay','start','--project-id',$ProjectId)) {
        [void]$startInfo.ArgumentList.Add($argument)
    }
    $startProcess = [Diagnostics.Process]::Start($startInfo)
    $startProcess.WaitForExit()
    if ($startProcess.ExitCode -ne 0) { throw "relay start failed with exit code $($startProcess.ExitCode)" }
    $relayStarted = $true
    $statusText = (& $binary --repo-root $repoRoot relay status --project-id $ProjectId | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw "relay status failed after start: $statusText" }
    $startedStatus = $statusText | ConvertFrom-Json
    if (-not $startedStatus.enabled) { throw 'Relay worker did not enter the enabled state.' }

    Write-Host '[Stage 4] Waiting for Yandex heartbeat...'
    $online = $false
    for ($attempt = 1; $attempt -le 12; $attempt++) {
        try {
            $health = Invoke-RestMethod -Method Get -Uri $functionUrl -Headers $headers -TimeoutSec 15
            if (
                $health.status -eq 'ok' -and
                $health.remote_auth_configured -and
                $health.project_id -eq $ProjectId -and
                $health.agent_online
            ) {
                $online = $true
                break
            }
        }
        catch {
            if ($attempt -eq 12) { throw }
        }
        if ($attempt -lt 12) { Start-Sleep -Seconds 2 }
    }
    if (-not $online) { throw 'Yandex gateway did not observe the local relay heartbeat.' }

    Write-Host '[Stage 4] Calling local_ping through the real public Yandex URL...'
    $pingBody = @{ action = 'local_ping'; message = 'Stage 4 real Yandex acceptance' } | ConvertTo-Json -Compress
    for ($attempt = 0; $attempt -lt 5; $attempt++) {
        try {
            $localPingResult = Invoke-RestMethod -Method Post -Uri $functionUrl -Headers $headers -ContentType 'application/json' -Body $pingBody -TimeoutSec 150
        }
        catch {
            if ($attempt -eq 4) { throw }
            Start-Sleep -Seconds 3
            continue
        }
        if ($localPingResult.status -eq 'success') { break }
        if ($localPingResult.error.code -ne 'AGENT_OFFLINE') { break }
        Start-Sleep -Seconds 2
    }
    if ($localPingResult.status -ne 'success' -or -not $localPingResult.result.pong -or -not $localPingResult.result.executed_locally) {
        $details = $localPingResult | ConvertTo-Json -Depth 8 -Compress
        throw "Real Yandex -> local_ping round trip did not return a validated local success: $details"
    }

    Write-Host '[Stage 4] Calling runtime_self_test through the real public Yandex URL...'
    $selfBody = @{ action = 'runtime_self_test' } | ConvertTo-Json -Compress
    $selfTestResult = Invoke-RestMethod -Method Post -Uri $functionUrl -Headers $headers -ContentType 'application/json' -Body $selfBody -TimeoutSec 150
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

$finalHealth = Invoke-RestMethod -Method Get -Uri $functionUrl -Headers $headers -TimeoutSec 10
if (-not $LeaveRelayOn -and $finalHealth.agent_online) {
    for ($attempt = 0; $attempt -lt 10 -and $finalHealth.agent_online; $attempt++) {
        Start-Sleep -Milliseconds 500
        $finalHealth = Invoke-RestMethod -Method Get -Uri $functionUrl -Headers $headers -TimeoutSec 10
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
    gateway_id = [string]$deployment.gateway_id
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
