param(
    [string]$EvidencePath = 'runtime/stage4-yandex-acceptance.json',
    [switch]$CopyOpenApiToClipboard
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

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
$functionId = [string]$evidence.function_id
if ([string]::IsNullOrWhiteSpace($functionId)) {
    throw 'Stage 4 evidence does not contain function_id.'
}

$functionUrl = "https://functions.yandexcloud.net/$functionId"
$actionsTemplatePath = Join-Path $repoRoot 'gateway/actions-openapi-gpt.template.json'
$actionsOutputPath = Join-Path $repoRoot 'runtime/relay/actions-openapi-gpt.json'

$health = Invoke-RestMethod -Method Get -Uri $functionUrl -TimeoutSec 20
if ($health.status -ne 'ok') {
    throw 'Direct public Function health failed.'
}

$actionsTemplate = Get-Content -LiteralPath $actionsTemplatePath -Raw -Encoding utf8
if ($actionsTemplate -notmatch '__FUNCTION_URL__') {
    throw 'GPT Actions template does not contain __FUNCTION_URL__.'
}
$actionsText = $actionsTemplate.Replace('__FUNCTION_URL__', $functionUrl)
$actions = $actionsText | ConvertFrom-Json

if ($actions.openapi -notin @('3.1.0','3.1.1')) {
    throw 'GPT Actions OpenAPI must be 3.1.0 or 3.1.1.'
}
if ($null -eq $actions.components.schemas) {
    throw 'GPT Actions OpenAPI is missing components.schemas.'
}
if ($actions.paths.'/'.post.operationId -ne 'runLocalAgentTool') {
    throw 'GPT Action operationId mismatch.'
}
if ([string]$actions.servers[0].url -ne $functionUrl) {
    throw 'GPT Actions OpenAPI does not point to the direct Function URL.'
}
$security = $actions.components.securitySchemes.mcpToken
if ($security.type -ne 'apiKey' -or $security.in -ne 'header' -or $security.name -ne 'X-MCP-Token') {
    throw 'GPT Actions OpenAPI must use X-MCP-Token custom-header authentication.'
}

$actionsText | Set-Content -LiteralPath $actionsOutputPath -Encoding utf8

if ($CopyOpenApiToClipboard) {
    Set-Clipboard -Value $actionsText
}

[ordered]@{
    contract_version = 'stage4-gpt-direct-function-prepare-v1'
    status = 'success'
    function_id = $functionId
    function_url = $functionUrl
    public_health = [string]$health.status
    gpt_path = '/'
    auth_header = 'X-MCP-Token'
    api_gateway_used = $false
    actions_openapi = $actionsOutputPath
    actions_openapi_copied_to_clipboard = [bool]$CopyOpenApiToClipboard
} | ConvertTo-Json -Depth 6
