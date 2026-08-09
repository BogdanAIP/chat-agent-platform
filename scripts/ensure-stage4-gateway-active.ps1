param(
    [string]$GatewayId,
    [string]$EvidencePath = 'runtime/stage4-yandex-acceptance.json',
    [int]$Attempts = 60,
    [switch]$CopyOpenApiToClipboard
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

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
        return $text | ConvertFrom-Json
    }
    finally {
        Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue
    }
}

if (-not (Get-Command yc -ErrorAction SilentlyContinue)) {
    throw 'Yandex Cloud CLI (`yc`) is not installed or not on PATH.'
}

if ([string]::IsNullOrWhiteSpace($GatewayId)) {
    $resolvedEvidence = if ([IO.Path]::IsPathRooted($EvidencePath)) {
        $EvidencePath
    }
    else {
        Join-Path $repoRoot $EvidencePath
    }
    if (-not (Test-Path -LiteralPath $resolvedEvidence -PathType Leaf)) {
        throw "Stage 4 acceptance evidence is missing: $resolvedEvidence"
    }
    $evidence = Get-Content -LiteralPath $resolvedEvidence -Raw -Encoding utf8 | ConvertFrom-Json
    $GatewayId = [string]$evidence.gateway_id
}

if ([string]::IsNullOrWhiteSpace($GatewayId)) {
    throw 'Yandex API Gateway ID is missing. Pass -GatewayId or regenerate Stage 4 acceptance evidence.'
}

$gateway = Invoke-YcJson -Context 'API Gateway get' -Arguments @('serverless','api-gateway','get','--id',$GatewayId)
$initialStatus = [string]$gateway.status

if ($initialStatus -eq 'STOPPED') {
    Write-Host "Yandex API Gateway $GatewayId is STOPPED; resuming it..."
    & yc serverless api-gateway resume --id $GatewayId | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw 'Yandex API Gateway resume failed.'
    }
}
elseif ($initialStatus -eq 'ERROR') {
    throw 'Yandex API Gateway is in ERROR state; refusing to hide the cloud-side failure.'
}

for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
    $gateway = Invoke-YcJson -Context 'API Gateway get' -Arguments @('serverless','api-gateway','get','--id',$GatewayId)
    $status = [string]$gateway.status
    Write-Host "[$attempt/$Attempts] API Gateway status=$status"

    if ($status -eq 'ACTIVE') { break }
    if ($status -eq 'ERROR') {
        throw 'Yandex API Gateway entered ERROR state while waiting for ACTIVE.'
    }
    if ($attempt -eq $Attempts) {
        throw "Yandex API Gateway did not become ACTIVE; final status=$status"
    }
    Start-Sleep -Seconds 2
}

$domain = [string]$gateway.domain
if ([string]::IsNullOrWhiteSpace($domain)) {
    throw 'Yandex API Gateway ACTIVE response does not contain a domain.'
}
$gatewayUrl = "https://$domain"

$health = Invoke-RestMethod -Method Get -Uri $gatewayUrl -TimeoutSec 20
if ($health.status -ne 'ok') {
    throw 'Yandex API Gateway is ACTIVE but relay public health did not return status=ok.'
}

$openApiPath = Join-Path $repoRoot 'runtime/relay/actions-openapi.json'
if ($CopyOpenApiToClipboard) {
    if (-not (Get-Command Set-Clipboard -ErrorAction SilentlyContinue)) {
        throw 'Set-Clipboard is unavailable.'
    }
    if (-not (Test-Path -LiteralPath $openApiPath -PathType Leaf)) {
        throw "Generated GPT Actions OpenAPI is missing: $openApiPath"
    }
    $openApiText = Get-Content -LiteralPath $openApiPath -Raw -Encoding utf8
    $openApi = $openApiText | ConvertFrom-Json
    if ($openApi.openapi -notin @('3.1.0','3.1.1')) {
        throw "Generated GPT Actions schema has unsupported OpenAPI version: $($openApi.openapi)"
    }
    if ([string]$openApi.servers[0].url -ne $gatewayUrl) {
        throw "Generated GPT Actions schema points to $($openApi.servers[0].url), expected $gatewayUrl"
    }
    if ($null -eq $openApi.components.schemas) {
        throw 'Generated GPT Actions schema is missing components.schemas.'
    }
    Set-Clipboard -Value $openApiText
}

[ordered]@{
    contract_version = 'stage4-gateway-recovery-v1'
    status = 'success'
    gateway_id = $GatewayId
    initial_status = $initialStatus
    final_status = [string]$gateway.status
    gateway_url = $gatewayUrl
    public_health = [string]$health.status
    actions_openapi_copied_to_clipboard = [bool]$CopyOpenApiToClipboard
} | ConvertTo-Json -Depth 6