param(
    [Parameter(Mandatory)]
    [string]$PublicUrl,

    [string]$OutputPath = 'runtime/ingress/actions-openapi-gpt.json',

    [switch]$SkipHealthCheck
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$uri = $null
if (-not [Uri]::TryCreate($PublicUrl, [UriKind]::Absolute, [ref]$uri)) {
    throw 'PublicUrl must be an absolute HTTPS URL.'
}
if ($uri.Scheme -ne 'https') {
    throw 'PublicUrl must use HTTPS.'
}
if (-not [string]::IsNullOrEmpty($uri.Query) -or -not [string]::IsNullOrEmpty($uri.Fragment)) {
    throw 'PublicUrl must not contain a query string or fragment.'
}

$basePath = $uri.AbsolutePath.TrimEnd('/')
if ($basePath -ne '') {
    throw 'PublicUrl must be the public base URL without an endpoint path.'
}
$baseUrl = $PublicUrl.TrimEnd('/')

$templatePath = Join-Path $repoRoot 'gateway/actions-openapi-gpt.template.json'
if (-not (Test-Path -LiteralPath $templatePath -PathType Leaf)) {
    throw "GPT Actions template is missing: $templatePath"
}

if (-not $SkipHealthCheck) {
    $health = Invoke-RestMethod -Method Get -Uri "$baseUrl/healthz" -TimeoutSec 20
    if ($health.status -ne 'ok') {
        throw 'Direct ingress public health check did not return status=ok.'
    }
    if ($health.contract_version -ne 'local-ingress-v1') {
        throw "Unexpected direct ingress contract version: $($health.contract_version)"
    }
}

$template = Get-Content -LiteralPath $templatePath -Raw -Encoding utf8
if ($template -notmatch '__GATEWAY_URL__') {
    throw 'GPT Actions template does not contain __GATEWAY_URL__.'
}

$actionsText = $template.Replace('__GATEWAY_URL__', $baseUrl)
$actions = $actionsText | ConvertFrom-Json

if ($actions.openapi -notin @('3.1.0', '3.1.1')) {
    throw 'GPT Actions OpenAPI must be 3.1.0 or 3.1.1.'
}
if ($actions.servers.Count -ne 1 -or [string]$actions.servers[0].url -ne $baseUrl) {
    throw 'GPT Actions OpenAPI server URL mismatch.'
}
if ($actions.paths.'/gpt'.post.operationId -ne 'runLocalAgentTool') {
    throw 'GPT Action operationId mismatch.'
}
$security = $actions.components.securitySchemes.mcpToken
if ($security.type -ne 'apiKey' -or $security.in -ne 'header' -or $security.name -ne 'X-MCP-Token') {
    throw 'GPT Actions OpenAPI must use X-MCP-Token custom-header authentication.'
}

$resolvedOutput = if ([IO.Path]::IsPathRooted($OutputPath)) {
    $OutputPath
}
else {
    Join-Path $repoRoot $OutputPath
}
$outputDirectory = Split-Path -Parent $resolvedOutput
if (-not [string]::IsNullOrWhiteSpace($outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}
$actionsText | Set-Content -LiteralPath $resolvedOutput -Encoding utf8

[ordered]@{
    contract_version = 'direct-gpt-action-prepare-v1'
    status = 'success'
    public_url = $baseUrl
    health_checked = -not [bool]$SkipHealthCheck
    health_url = "$baseUrl/healthz"
    gpt_url = "$baseUrl/gpt"
    auth_header = 'X-MCP-Token'
    actions_openapi = $resolvedOutput
    clipboard_modified = $false
} | ConvertTo-Json -Depth 4
