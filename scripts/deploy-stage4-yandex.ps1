param(
    [string]$ProjectId = 'demo',
    [string]$FunctionId,
    [string]$FunctionName = 'agent-platform-relay',
    [string]$ServiceAccountName = 'agent-platform-relay',
    [string]$BucketName,
    [string]$Runtime = 'python312',
    [switch]$AdoptExistingBucket,
    [switch]$SkipBuild,
    [switch]$StartRelay
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$functionSource = Join-Path $repoRoot 'gateway/yandex_function'
$binary = Join-Path $repoRoot 'target/release/agent-platform.exe'
$explicitBucket = -not [string]::IsNullOrWhiteSpace($BucketName)

function Invoke-YcJson {
    param(
        [Parameter(Mandatory)] [string[]]$Arguments,
        [Parameter(Mandatory)] [string]$Context
    )
    $text = (& yc @Arguments --format json 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw "$Context failed: $text" }
    if ([string]::IsNullOrWhiteSpace($text)) { return $null }
    try { return $text | ConvertFrom-Json }
    catch { throw "$Context returned invalid JSON: $text" }
}

function Invoke-Yc {
    param(
        [Parameter(Mandatory)] [string[]]$Arguments,
        [Parameter(Mandatory)] [string]$Context
    )
    $text = (& yc @Arguments 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw "$Context failed: $text" }
    return $text
}

function New-UrlSafeToken {
    param([int]$Bytes = 36)
    $buffer = [byte[]]::new($Bytes)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($buffer)
    return [Convert]::ToBase64String($buffer).TrimEnd('=').Replace('+', '-').Replace('/', '_')
}

function Get-IamToken {
    $token = (& yc iam create-token 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($token)) {
        throw 'Unable to create a temporary Yandex IAM token. Run `yc init` first.'
    }
    return $token
}

function Get-BucketApi {
    param([Parameter(Mandatory)] [string]$Name)
    $iam = Get-IamToken
    try {
        return Invoke-RestMethod -Method Get -Uri ('https://storage.api.cloud.yandex.net/storage/v1/buckets/' + [uri]::EscapeDataString($Name)) -Headers @{ Authorization = "Bearer $iam" }
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
        $bindings = Invoke-RestMethod -Method Get -Uri $listUri -Headers $headers
        $exists = @($bindings.accessBindings) | Where-Object {
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
                $bindings = Invoke-RestMethod -Method Get -Uri $listUri -Headers $headers
                $exists = @($bindings.accessBindings) | Where-Object {
                    $_.roleId -eq 'storage.uploader' -and $_.subject.type -eq 'serviceAccount' -and $_.subject.id -eq $ServiceAccountId
                }
                if ($exists) { break }
            }
            if (-not $exists) { throw 'storage.uploader binding was not observed after update' }
        }
    }
    finally { $iam = $null }
}

if (-not (Get-Command yc -ErrorAction SilentlyContinue)) {
    throw 'Yandex Cloud CLI (`yc`) is not installed or not on PATH.'
}
if (-not (Test-Path -LiteralPath (Join-Path $functionSource 'index.py') -PathType Leaf)) {
    throw "Yandex function source is missing: $functionSource"
}

$folderId = (& yc config get folder-id 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($folderId)) {
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

Write-Host '[4/7] Creating a new function version...'
$agentToken = New-UrlSafeToken
$environment = "AGENT_TOKEN=$agentToken,PROJECT_ID=$ProjectId"
$versionArgs = @(
    'serverless','function','version','create',
    '--function-id',$FunctionId,
    '--runtime',$Runtime,
    '--entrypoint','index.handler',
    '--memory','128MB',
    '--execution-timeout','70s',
    '--concurrency','1',
    '--service-account-id',$serviceAccountId,
    '--source-path',$functionSource,
    '--mount',"type=object-storage,mount-point=relay,bucket=$BucketName,mode=rw",
    '--environment',$environment
)
$version = Invoke-YcJson -Context 'function version create' -Arguments $versionArgs
if (-not $version.id) { throw 'Function version was not created.' }
Invoke-Yc -Context 'allow unauthenticated function invocation' -Arguments @('serverless','function','allow-unauthenticated-invoke','--id',$FunctionId) | Out-Null
$functionUrl = "https://functions.yandexcloud.net/$FunctionId"

Write-Host '[5/7] Building local agent-platform...'
Push-Location $repoRoot
try {
    if (-not $SkipBuild) {
        & cargo build --workspace --release
        if ($LASTEXITCODE -ne 0) { throw 'release build failed' }
    }
}
finally { Pop-Location }
if (-not (Test-Path -LiteralPath $binary -PathType Leaf)) { throw "release binary not found: $binary" }

Write-Host '[6/7] Storing relay token locally and saving endpoint...'
$env:AGENT_PLATFORM_RELAY_TOKEN = $agentToken
try {
    $configureText = (& $binary --repo-root $repoRoot relay configure --project-id $ProjectId --endpoint $functionUrl | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'local relay configure failed' }
    $configured = $configureText | ConvertFrom-Json
    if ($configured.status -ne 'configured') { throw "local relay configure returned status $($configured.status)" }
}
finally {
    Remove-Item Env:AGENT_PLATFORM_RELAY_TOKEN -ErrorAction SilentlyContinue
    $agentToken = $null
    $environment = $null
}

Write-Host '[7/7] Verifying public gateway health...'
$health = Invoke-RestMethod -Method Get -Uri $functionUrl -TimeoutSec 20
if ($health.status -ne 'ok') { throw 'Yandex relay health endpoint did not return status=ok' }

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
    function_url = $functionUrl
    function_version_id = [string]$version.id
    bucket = $BucketName
    service_account_id = $serviceAccountId
    bucket_runtime_role = 'storage.uploader'
    lifecycle_managed = $manageLifecycle
    project_id = $ProjectId
    local_configured = $true
    relay_enabled = [bool]$StartRelay
}
if ($start) { $result.relay = $start.relay }
$result | ConvertTo-Json -Depth 8
