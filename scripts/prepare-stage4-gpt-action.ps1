param(
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
if ($CopyOpenApiToClipboard -and -not (Get-Command Set-Clipboard -ErrorAction SilentlyContinue)) {
    throw 'Set-Clipboard is unavailable.'
}

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
$gatewayId = [string]$evidence.gateway_id
$functionId = [string]$evidence.function_id
if ([string]::IsNullOrWhiteSpace($gatewayId)) { throw 'Stage 4 evidence does not contain gateway_id.' }
if ([string]::IsNullOrWhiteSpace($functionId)) { throw 'Stage 4 evidence does not contain function_id.' }

$gatewayTemplatePath = Join-Path $repoRoot 'gateway/yandex-apigateway.template.json'
$actionsTemplatePath = Join-Path $repoRoot 'gateway/actions-openapi-gpt.template.json'
$gatewayOutputPath = Join-Path $repoRoot 'runtime/relay/yandex-apigateway.json'
$actionsOutputPath = Join-Path $repoRoot 'runtime/relay/actions-openapi-gpt.json'

$gatewayTemplate = Get-Content -LiteralPath $gatewayTemplatePath -Raw -Encoding utf8
if ($gatewayTemplate -notmatch '__FUNCTION_ID__') {
    throw 'Yandex API Gateway template does not contain __FUNCTION_ID__.'
}
$gatewaySpec = $gatewayTemplate.Replace('__FUNCTION_ID__', $functionId)
$gatewaySpec | Set-Content -LiteralPath $gatewayOutputPath -Encoding utf8
$parsedGatewaySpec = $gatewaySpec | ConvertFrom-Json

$gptRoute = $parsedGatewaySpec.paths.'/gpt'.post.'x-yc-apigateway-integration'
if ($gptRoute.type -ne 'http') { throw 'GPT ingress must use Yandex HTTP integration.' }
if ($gptRoute.headers.'X-MCP-Token' -ne '{X-MCP-Token}') {
    throw 'GPT ingress does not forward the explicit X-MCP-Token parameter.'
}
if ($null -ne $gptRoute.headers.PSObject.Properties['X-Request-Id']) {
    throw 'GPT ingress must not forward X-Request-Id.'
}
if ($null -ne $gptRoute.headers.PSObject.Properties['*']) {
    throw 'GPT ingress must not wildcard-forward original headers.'
}

$gateway = Invoke-YcJson -Context 'API Gateway update' -Arguments @(
    'serverless','api-gateway','update','--id',$gatewayId,'--spec',$gatewayOutputPath
)

for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
    $gateway = Invoke-YcJson -Context 'API Gateway get' -Arguments @(
        'serverless','api-gateway','get','--id',$gatewayId
    )
    $status = [string]$gateway.status
    Write-Host "[$attempt/$Attempts] API Gateway status=$status"
    if ($status -eq 'ACTIVE') { break }
    if ($status -eq 'ERROR') { throw 'Yandex API Gateway entered ERROR after GPT ingress update.' }
    if ($attempt -eq $Attempts) { throw "Yandex API Gateway did not become ACTIVE; final status=$status" }
    Start-Sleep -Seconds 2
}

$domain = [string]$gateway.domain
if ([string]::IsNullOrWhiteSpace($domain)) { throw 'Yandex API Gateway does not contain a domain.' }
$gatewayUrl = "https://$domain"

$health = Invoke-RestMethod -Method Get -Uri $gatewayUrl -TimeoutSec 20
if ($health.status -ne 'ok') { throw 'Gateway public health failed after GPT ingress update.' }

$actionsTemplate = Get-Content -LiteralPath $actionsTemplatePath -Raw -Encoding utf8
if ($actionsTemplate -notmatch '__GATEWAY_URL__') {
    throw 'GPT Actions template does not contain __GATEWAY_URL__.'
}
$actionsText = $actionsTemplate.Replace('__GATEWAY_URL__', $gatewayUrl)
$actions = $actionsText | ConvertFrom-Json
if ($actions.openapi -notin @('3.1.0','3.1.1')) { throw 'GPT Actions OpenAPI must be 3.1.0 or 3.1.1.' }
if ($null -eq $actions.components.schemas) { throw 'GPT Actions OpenAPI is missing components.schemas.' }
if ($actions.paths.'/gpt'.post.operationId -ne 'runLocalAgentTool') { throw 'GPT Action operationId mismatch.' }
$security = $actions.components.securitySchemes.mcpToken
if ($security.type -ne 'apiKey' -or $security.in -ne 'header' -or $security.name -ne 'X-MCP-Token') {
    throw 'GPT Actions OpenAPI must use X-MCP-Token custom-header authentication.'
}
$actionsText | Set-Content -LiteralPath $actionsOutputPath -Encoding utf8

if ($CopyOpenApiToClipboard) {
    Set-Clipboard -Value $actionsText
}

[ordered]@{
    contract_version = 'stage4-gpt-ingress-prepare-v1'
    status = 'success'
    gateway_id = $gatewayId
    gateway_url = $gatewayUrl
    gateway_status = [string]$gateway.status
    public_health = [string]$health.status
    gpt_path = '/gpt'
    auth_header = 'X-MCP-Token'
    original_headers_forwarded = $false
    actions_openapi = $actionsOutputPath
    actions_openapi_copied_to_clipboard = [bool]$CopyOpenApiToClipboard
} | ConvertTo-Json -Depth 6
