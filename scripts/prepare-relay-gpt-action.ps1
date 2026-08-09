param(
    [Parameter(Mandatory)]
    [string]$RelayUrl,
    [switch]$DesktopCopy
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$uri = $null
if (-not [Uri]::TryCreate($RelayUrl.Trim(), [UriKind]::Absolute, [ref]$uri)) {
    throw 'RelayUrl must be an absolute HTTPS URL.'
}
if ($uri.Scheme -ne 'https') {
    throw 'RelayUrl must use HTTPS.'
}
if (-not [string]::IsNullOrWhiteSpace($uri.Query) -or -not [string]::IsNullOrWhiteSpace($uri.Fragment)) {
    throw 'RelayUrl must not contain a query string or fragment.'
}
if ($uri.AbsolutePath -ne '/') {
    throw 'RelayUrl must be an HTTPS origin without an additional path.'
}

$origin = $uri.GetLeftPart([UriPartial]::Authority).TrimEnd('/')
$healthUrl = "$origin/healthz"
$health = Invoke-RestMethod -Method Get -Uri $healthUrl -TimeoutSec 20
if ($health.status -ne 'ok' -or $health.contract_version -ne 'relay-server-v1') {
    throw 'Rust relay public health check did not return relay-server-v1 status=ok.'
}

$templatePath = Join-Path $repoRoot 'gateway/actions-openapi-relay.template.json'
if (-not (Test-Path -LiteralPath $templatePath -PathType Leaf)) {
    throw "Rust relay GPT Actions template is missing: $templatePath"
}
$template = Get-Content -LiteralPath $templatePath -Raw -Encoding utf8
if ($template -notmatch '__RELAY_URL__') {
    throw 'Rust relay GPT Actions template does not contain __RELAY_URL__.'
}

$schemaText = $template.Replace('__RELAY_URL__', $origin)
$schema = $schemaText | ConvertFrom-Json
if ($schema.openapi -notin @('3.1.0', '3.1.1')) {
    throw 'GPT Actions OpenAPI must be 3.1.0 or 3.1.1.'
}
if ($null -eq $schema.components.schemas) {
    throw 'GPT Actions OpenAPI is missing components.schemas.'
}
if ($schema.paths.'/'.post.operationId -ne 'runLocalAgentTool') {
    throw 'GPT Action operationId mismatch.'
}
$security = $schema.components.securitySchemes.mcpToken
if ($security.type -ne 'apiKey' -or $security.in -ne 'header' -or $security.name -ne 'X-MCP-Token') {
    throw 'GPT Actions OpenAPI must use X-MCP-Token custom-header authentication.'
}

$outputDirectory = Join-Path $repoRoot 'runtime/relay'
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
$outputPath = Join-Path $outputDirectory 'actions-openapi-relay.json'
$schemaText | Set-Content -LiteralPath $outputPath -Encoding utf8

$desktopPath = $null
if ($DesktopCopy) {
    $desktop = [Environment]::GetFolderPath('Desktop')
    if ([string]::IsNullOrWhiteSpace($desktop)) {
        throw 'Desktop path is unavailable.'
    }
    $desktopPath = Join-Path $desktop 'AgentPlatform-GPT-Action-Schema.json'
    $schemaText | Set-Content -LiteralPath $desktopPath -Encoding utf8
}

[ordered]@{
    contract_version = 'relay-gpt-action-prepare-v1'
    status = 'success'
    transport = 'rust-relay-server'
    relay_url = $origin
    public_health = [string]$health.status
    gpt_path = '/'
    auth_header = 'X-MCP-Token'
    actions_openapi = $outputPath
    desktop_copy = $desktopPath
} | ConvertTo-Json -Depth 5
