param(
    [string]$ProjectId = 'demo',
    [string]$FunctionId,
    [string]$FunctionName = 'agent-platform-relay',
    [string]$GatewayName = 'agent-platform-relay-gateway',
    [string]$ServiceAccountName = 'agent-platform-relay',
    [string]$BucketName,
    [string]$Runtime = 'python312',
    [switch]$AdoptExistingBucket,
    [switch]$RotateTokens,
    [switch]$SkipBuild,
    [switch]$CopyActionTokenToClipboard,
    [switch]$StartRelay
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$functionSource = Join-Path $repoRoot 'gateway/yandex_function'
$openApiTemplate = Join-Path $repoRoot 'gateway/actions-openapi.template.json'
$gatewayTemplate = Join-Path $repoRoot 'gateway/yandex-apigateway.template.json'
$openApiOutput = Join-Path $repoRoot 'runtime/relay/actions-openapi.json'
$gatewaySpecOutput = Join-Path $repoRoot 'runtime/relay/yandex-apigateway.json'
$binary = Join-Path $repoRoot 'target/release/agent-platform.exe'
$explicitBucket = -not [string]::IsNullOrWhiteSpace($BucketName)

function Invoke-YcJson {
    param(
        [Parameter(Mandatory)] [string[]]$Arguments,
        [Parameter(Mandatory)] [string]$Context
    )
    $stderrPath = [IO.Path]::GetTempFileName()
    try {
        $text = (& yc @Arguments --format json 2> $stderrPath | Out-String).Trim()
        $exitCode = $LASTEXITCODE
        $stderrText = (Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue | Out-String).Trim()
        if ($exitCode -ne 0) {
            $details = @($text, $stderrText) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
            throw "$Context failed: $($details -join [Environment]::NewLine)"
        }
        if ([string]::IsNullOrWhiteSpace($text)) { return $null }
        try { return $text | ConvertFrom-Json }
        catch { throw "$Context returned invalid JSON: $text" }
    }
    finally { Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue }
}

function Invoke-Yc {
    param(
        [Parameter(Mandatory)] [string[]]$Arguments,
        [Parameter(Mandatory)] [string]$Context
    )
    $stderrPath = [IO.Path]::GetTempFileName()
    try {
        $text = (& yc @Arguments 2> $stderrPath | Out-String).Trim()
        $exitCode = $LASTEXITCODE
        $stderrText = (Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue | Out-String).Trim()
        if ($exitCode -ne 0) {
            $details = @($text, $stderrText) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
            throw "$Context failed: $($details -join [Environment]::NewLine)"
        }
        return $text
    }
    finally { Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue }
}

function New-UrlSafeToken {
    param([int]$Bytes = 36)
    $buffer = [byte[]]::new($Bytes)
    try {
        [System.Security.Cryptography.RandomNumberGenerator]::Fill($buffer)
        return [Convert]::ToBase64String($buffer).TrimEnd('=').Replace('+', '-').Replace('/', '_')
    }
    finally {
        [Array]::Clear($buffer, 0, $buffer.Length)
    }
}

function Get-IamToken {
    $stderrPath = [IO.Path]::GetTempFileName()
    try {
        $token = (& yc iam create-token 2> $stderrPath | Out-String).Trim()
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0 -or [string]::IsNullOrWhiteSpace($token)) {
            throw 'Unable to create a temporary Yandex IAM token. Run `yc init` first.'
        }
        return $token
    }
    finally { Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue }
}

function Invoke-ReadOnlyRestWithRetry {
    param(
        [Parameter(Mandatory)] [string]$Uri,
        [Parameter(Mandatory)] [hashtable]$Headers,
        [int]$Attempts = 5
    )
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try { return Invoke-RestMethod -Method Get -Uri $Uri -Headers $Headers -TimeoutSec 30 }
        catch {
            if ($attempt -eq $Attempts) { throw }
            Start-Sleep -Seconds ([Math]::Min($attempt * 2, 8))
        }
    }
}

function Get-BucketApi {
    param([Parameter(Mandatory)] [string]$Name)
    $iam = Get-IamToken
    try {
        return Invoke-ReadOnlyRestWithRetry -Uri ('https://storage.api.cloud.yandex.net/storage/v1/buckets/' + [uri]::EscapeDataString($Name)) -Headers @{ Authorization = "Bearer $iam" }
    }
    finally { $iam = $null }
}

function Ensure-BucketUploaderRole {
    param(
        [Parameter(Mandatory)] [string]$ResourceId,
        [Parameter(Mandatory)] [string]$ServiceAccountId
    )
    $iam = Get-IamToken
    try {
        $headers = @{ Authorization = "Bearer $iam"; 'Content-Type' = 'application/json' }
        $listUri = "https://storage.api.cloud.yandex.net/storage/v1/buckets/$ResourceId`:listAccessBindings"
        $bindings = Invoke-ReadOnlyRestWithRetry -Uri $listUri -Headers $headers
        $bindingItems = if ($null -eq $bindings.PSObject.Properties['accessBindings']) { @() } else { @($bindings.accessBindings) }
        $exists = $bindingItems | Where-Object {
            $_.roleId -eq 'storage.uploader' -and $_.subject.type -eq 'serviceAccount' -and $_.subject.id -eq $ServiceAccountId
        }
        if (-not $exists) {
            $body = @{
                accessBindingDeltas = @(@{
                    action = 'ADD'
                    accessBinding = @{
                        roleId = 'storage.uploader'
                        subject = @{ type = 'serviceAccount'; id = $ServiceAccountId }
                    }
                })
            } | ConvertTo-Json -Depth 8 -Compress
            $updateUri = "https://storage.api.cloud.yandex.net/storage/v1/buckets/$ResourceId`:updateAccessBindings"
            Invoke-RestMethod -Method Patch -Uri $updateUri -Headers $headers -Body $body | Out-Null
            for ($attempt = 0; $attempt -lt 20; $attempt++) {
                Start-Sleep -Milliseconds 500
                $bindings = Invoke-ReadOnlyRestWithRetry -Uri $listUri -Headers $headers
                $bindingItems = if ($null -eq $bindings.PSObject.Properties['accessBindings']) { @() } else { @($bindings.accessBindings) }
                $exists = $bindingItems | Where-Object {
                    $_.roleId -eq 'storage.uploader' -and $_.subject.type -eq 'serviceAccount' -and $_.subject.id -eq $ServiceAccountId
                }
                if ($exists) { break }
            }
            if (-not $exists) { throw 'storage.uploader binding was not observed after update' }
        }
    }
    finally { $iam = $null }
}

function Write-GeneratedOpenApi {
    param([Parameter(Mandatory)] [string]$GatewayUrl)
    if (-not (Test-Path -LiteralPath $openApiTemplate -PathType Leaf)) {
        throw "GPT Actions OpenAPI template is missing: $openApiTemplate"
    }
    $template = Get-Content -LiteralPath $openApiTemplate -Raw -Encoding utf8
    if ($template -notmatch '__GATEWAY_URL__') {
        throw 'GPT Actions OpenAPI template does not contain __GATEWAY_URL__ placeholder.'
    }
    $generated = $template.Replace('__GATEWAY_URL__', $GatewayUrl)
    $directory = Split-Path -Parent $openApiOutput
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    $generated | Set-Content -LiteralPath $openApiOutput -Encoding utf8
    try { Get-Content -LiteralPath $openApiOutput -Raw -Encoding utf8 | ConvertFrom-Json | Out-Null }
    catch { throw "Generated GPT Actions OpenAPI is invalid JSON: $($_.Exception.Message)" }
}

function Write-GeneratedGatewaySpec {
    param([Parameter(Mandatory)] [string]$CloudFunctionId)
    if (-not (Test-Path -LiteralPath $gatewayTemplate -PathType Leaf)) {
        throw "Yandex API Gateway template is missing: $gatewayTemplate"
    }
    $template = Get-Content -LiteralPath $gatewayTemplate -Raw -Encoding utf8
    if ($template -notmatch '__FUNCTION_ID__') {
        throw 'Yandex API Gateway template does not contain __FUNCTION_ID__ placeholder.'
    }
    $generated = $template.Replace('__FUNCTION_ID__', $CloudFunctionId)
    $directory = Split-Path -Parent $gatewaySpecOutput
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
    $generated | Set-Content -LiteralPath $gatewaySpecOutput -Encoding utf8
    try { Get-Content -LiteralPath $gatewaySpecOutput -Raw -Encoding utf8 | ConvertFrom-Json | Out-Null }
    catch { throw "Generated Yandex API Gateway specification is invalid JSON: $($_.Exception.Message)" }
}

if (-not (Get-Command yc -ErrorAction SilentlyContinue)) {
    throw 'Yandex Cloud CLI (`yc`) is not installed or not on PATH.'
}
if (-not (Test-Path -LiteralPath (Join-Path $functionSource 'index.py') -PathType Leaf)) {
    throw "Yandex function source is missing: $functionSource"
}
if ($CopyActionTokenToClipboard -and -not (Get-Command Set-Clipboard -ErrorAction SilentlyContinue)) {
    throw 'Set-Clipboard is required when -CopyActionTokenToClipboard is requested.'
}

$folderId = Invoke-Yc -Context 'active folder lookup' -Arguments @('config','get','folder-id')
if ([string]::IsNullOrWhiteSpace($folderId)) {
    throw 'No active Yandex Cloud folder. Run `yc init` or set a folder in the active profile.'
}
if (-not $explicitBucket) {
    $BucketName = ('agent-platform-relay-' + $folderId).ToLowerInvariant()
}
if ($BucketName.Length -gt 63) { throw 'Generated/provided bucket name exceeds 63 characters.' }

Write-Host '[1/7] Resolving service account...'
$accounts = @(Invoke-YcJson -Context 'service-account list' -Arguments @('iam','service-account','list','--folder-id',$folderId))
$serviceAccount = $accounts | Where-Object { $_.name -eq $ServiceAccountName } | Select-Object -First 1
if (-not $serviceAccount) {
    $serviceAccount = Invoke-YcJson -Context 'service-account create' -Arguments @('iam','service-account','create','--name',$ServiceAccountName,'--folder-id',$folderId)
}
$serviceAccountId = [string]$serviceAccount.id
if ([string]::IsNullOrWhiteSpace($serviceAccountId)) { throw 'Service account ID is missing.' }

Write-Host '[2/7] Resolving dedicated Object Storage bucket...'
$buckets = @(Invoke-YcJson -Context 'bucket list' -Arguments @('storage','bucket','list','--folder-id',$folderId))
$bucket = $buckets | Where-Object { $_.name -eq $BucketName } | Select-Object -First 1
$bucketCreated = $false
if (-not $bucket) {
    $bucket = Invoke-YcJson -Context 'bucket create' -Arguments @('storage','bucket','create','--name',$BucketName,'--folder-id',$folderId)
    $bucketCreated = $true
}
$bucketApi = Get-BucketApi -Name $BucketName
$resourceId = [string]$bucketApi.resourceId
if ([string]::IsNullOrWhiteSpace($resourceId)) { throw 'Object Storage bucket resourceId is missing.' }
Ensure-BucketUploaderRole -ResourceId $resourceId -ServiceAccountId $serviceAccountId

$manageLifecycle = $bucketCreated -or -not $explicitBucket -or $AdoptExistingBucket
if ($manageLifecycle) {
    $lifecycleFile = Join-Path ([IO.Path]::GetTempPath()) ('agent-platform-relay-lifecycle-' + [guid]::NewGuid().ToString('N') + '.json')
    try {
        @{ lifecycleRules = @(@{
            id = 'agent-platform-relay-expire-json'
            enabled = $true
            filter = @{ prefix = '' }
            expiration = @{ days = '1' }
        }) } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $lifecycleFile -Encoding utf8
        Invoke-Yc -Context 'bucket lifecycle update' -Arguments @('storage','bucket','update','--name',$BucketName,'--lifecycle-rules-from-file',$lifecycleFile) | Out-Null
    }
    finally { Remove-Item -LiteralPath $lifecycleFile -Force -ErrorAction SilentlyContinue }
}
elseif ($explicitBucket) {
    Write-Warning 'Existing custom bucket lifecycle was left unchanged. Use -AdoptExistingBucket only if this bucket is dedicated to the relay.'
}

Write-Host '[3/7] Resolving Cloud Function...'
if (-not [string]::IsNullOrWhiteSpace($FunctionId)) {
    $function = Invoke-YcJson -Context 'function get' -Arguments @('serverless','function','get','--id',$FunctionId)
}
else {
    $functions = @(Invoke-YcJson -Context 'function list' -Arguments @('serverless','function','list','--folder-id',$folderId))
    $function = $functions | Where-Object { $_.name -eq $FunctionName } | Select-Object -First 1
    if (-not $function) {
        $function = Invoke-YcJson -Context 'function create' -Arguments @('serverless','function','create','--name',$FunctionName,'--folder-id',$folderId)
    }
}
$FunctionId = [string]$function.id
if ([string]::IsNullOrWhiteSpace($FunctionId)) { throw 'Cloud Function ID is missing.' }

Write-Host '[4/8] Creating a new function version...'
$agentToken = $null
$remoteToken = $null
if (-not $RotateTokens) {
    $existingVersions = @(Invoke-YcJson -Context 'function version list' -Arguments @('serverless','function','version','list','--function-id',$FunctionId))
    $currentVersion = $existingVersions | Where-Object { @($_.tags) -contains '$latest' } | Select-Object -First 1
    if ($currentVersion -and $null -ne $currentVersion.PSObject.Properties['environment']) {
        $agentToken = [string]$currentVersion.environment.AGENT_TOKEN
        $remoteToken = [string]$currentVersion.environment.MCP_TOKEN
    }
}
if ([string]::IsNullOrWhiteSpace($agentToken)) { $agentToken = New-UrlSafeToken }
if ([string]::IsNullOrWhiteSpace($remoteToken)) { $remoteToken = New-UrlSafeToken }
    $environment = "AGENT_TOKEN=$agentToken,MCP_TOKEN=$remoteToken,PROJECT_ID=$ProjectId,BUCKET_NAME=$BucketName"
$versionArgs = @(
    'serverless','function','version','create',
    '--function-id',$FunctionId,
    '--runtime',$Runtime,
    '--entrypoint','index.handler',
    '--memory','128MB',
    '--execution-timeout','70s',
    '--concurrency','4',
    '--service-account-id',$serviceAccountId,
    '--source-path',$functionSource,
    '--mount',"type=object-storage,mount-point=relay,bucket=$BucketName,mode=rw",
    '--environment',$environment
)
$version = Invoke-YcJson -Context 'function version create' -Arguments $versionArgs
if (-not $version.id) { throw 'Function version was not created.' }
Invoke-Yc -Context 'allow unauthenticated function invocation' -Arguments @('serverless','function','allow-unauthenticated-invoke','--id',$FunctionId) | Out-Null
$directFunctionUrl = "https://functions.yandexcloud.net/$FunctionId"

Write-Host '[5/8] Creating/updating Bearer-compatible API Gateway...'
Write-GeneratedGatewaySpec -CloudFunctionId $FunctionId
$gateways = @(Invoke-YcJson -Context 'API Gateway list' -Arguments @('serverless','api-gateway','list','--folder-id',$folderId))
$gateway = $gateways | Where-Object { $_.name -eq $GatewayName } | Select-Object -First 1
if ($gateway) {
    $gateway = Invoke-YcJson -Context 'API Gateway update' -Arguments @('serverless','api-gateway','update','--id',[string]$gateway.id,'--spec',$gatewaySpecOutput)
}
else {
    $gateway = Invoke-YcJson -Context 'API Gateway create' -Arguments @('serverless','api-gateway','create','--name',$GatewayName,'--folder-id',$folderId,'--spec',$gatewaySpecOutput)
}
$gatewayId = [string]$gateway.id
$gatewayDomain = [string]$gateway.domain
if ([string]::IsNullOrWhiteSpace($gatewayId) -or [string]::IsNullOrWhiteSpace($gatewayDomain)) {
    throw 'Yandex API Gateway result is missing id or domain.'
}
$gatewayUrl = "https://$gatewayDomain"
Write-GeneratedOpenApi -GatewayUrl $gatewayUrl

Write-Host '[6/8] Building local agent-platform...'
Push-Location $repoRoot
try {
    if (-not $SkipBuild) {
        & cargo build --workspace --release
        if ($LASTEXITCODE -ne 0) { throw 'release build failed' }
    }
}
finally { Pop-Location }
if (-not (Test-Path -LiteralPath $binary -PathType Leaf)) { throw "release binary not found: $binary" }

Write-Host '[7/8] Storing local agent token and saving endpoint...'
$env:AGENT_PLATFORM_RELAY_TOKEN = $agentToken
try {
    $configureText = (& $binary --repo-root $repoRoot relay configure --project-id $ProjectId --endpoint $gatewayUrl | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'local relay configure failed' }
    $configured = $configureText | ConvertFrom-Json
    if ($configured.status -ne 'configured') { throw "local relay configure returned status $($configured.status)" }
}
finally {
    Remove-Item Env:AGENT_PLATFORM_RELAY_TOKEN -ErrorAction SilentlyContinue
    $environment = $null
}

Write-Host '[8/8] Verifying public gateway health...'
$publicHealth = Invoke-RestMethod -Method Get -Uri $gatewayUrl -TimeoutSec 20
if ($publicHealth.status -ne 'ok') { throw 'Yandex relay public health endpoint did not return status=ok' }
foreach ($privateField in @('agent_online','project_id','remote_auth_configured')) {
    if ($publicHealth.PSObject.Properties.Name -contains $privateField) {
        throw "Yandex relay public health leaked private field: $privateField"
    }
}
$remoteHeaders = @{ Authorization = "Bearer $remoteToken" }
$agentHeaders = @{ 'X-Agent-Token' = $agentToken }
$agentHealthBody = @{ agent_action = 'health'; project_id = $ProjectId } | ConvertTo-Json -Compress
$health = $null
$consecutiveAuthenticatedHealth = 0
for ($attempt = 0; $attempt -lt 90; $attempt++) {
    try {
        $candidate = Invoke-RestMethod -Method Get -Uri $gatewayUrl -Headers $remoteHeaders -TimeoutSec 20
        $agentCandidate = Invoke-RestMethod -Method Post -Uri $gatewayUrl -Headers $agentHeaders -ContentType 'application/json' -Body $agentHealthBody -TimeoutSec 20
        $candidateFields = @($candidate.PSObject.Properties.Name)
        if (
            $candidate.status -eq 'ok' -and
            $candidateFields -contains 'remote_auth_configured' -and
            $candidate.remote_auth_configured -and
            $candidateFields -contains 'project_id' -and
            $candidate.project_id -eq $ProjectId -and
            $agentCandidate.ok -and
            $agentCandidate.project_id -eq $ProjectId
        ) {
            $health = $candidate
            $consecutiveAuthenticatedHealth++
            if ($consecutiveAuthenticatedHealth -ge 3) { break }
        }
        else { $consecutiveAuthenticatedHealth = 0 }
    }
    catch {
        $consecutiveAuthenticatedHealth = 0
        if ($attempt -eq 89) { throw }
    }
    Start-Sleep -Seconds 2
}
if ($consecutiveAuthenticatedHealth -lt 3) {
    throw 'Yandex relay remote and agent authentication did not converge on the new Function version.'
}
Start-Sleep -Seconds 10
$agentToken = $null
$agentHeaders = $null

if ($CopyActionTokenToClipboard) {
    Set-Clipboard -Value $remoteToken
}

if ($StartRelay) {
    $startText = (& $binary --repo-root $repoRoot relay start --project-id $ProjectId | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'relay start failed' }
    $start = $startText | ConvertFrom-Json
}
else {
    $start = $null
}

$result = [ordered]@{
    contract_version = 'stage4-yandex-deploy-v1'
    status = 'success'
    folder_id = $folderId
    function_id = $FunctionId
    function_url = $directFunctionUrl
    function_version_id = [string]$version.id
    gateway_id = $gatewayId
    gateway_url = $gatewayUrl
    endpoint_url = $gatewayUrl
    bucket = $BucketName
    service_account_id = $serviceAccountId
    bucket_runtime_role = 'storage.uploader'
    lifecycle_managed = $manageLifecycle
    project_id = $ProjectId
    local_configured = $true
    relay_enabled = [bool]$StartRelay
    actions_openapi = $openApiOutput
    remote_auth_configured = $true
    tokens_rotated = [bool]$RotateTokens
    remote_bearer_copied_to_clipboard = [bool]$CopyActionTokenToClipboard
    remote_bearer_returned = $false
    agent_token_returned = $false
}
if ($start) { $result.relay = $start.relay }
$remoteToken = $null
$result | ConvertTo-Json -Depth 8
