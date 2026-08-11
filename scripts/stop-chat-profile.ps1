$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pkg = '@1mcp/agent@0.34.4'

$configs = @(
    (Join-Path $repoRoot 'runtime\mcp.json'),
    (Join-Path $repoRoot 'runtime\chat-profiles\files-readonly\mcp.json'),
    (Join-Path $repoRoot 'runtime\chat-profiles\browser-isolated\mcp.json')
)

foreach ($config in $configs) {
    if (-not (Test-Path -LiteralPath $config)) { continue }
    & npx.cmd -y $pkg serve --config $config --stop *> $null
    $stopCode = $LASTEXITCODE
    if ($stopCode -notin @(0, 3, 7)) {
        throw "Unable to stop 1MCP Runtime Scope for $config (exit $stopCode)."
    }
}

Write-Host 'CHAT_PROFILE_STATUS=stopped' -ForegroundColor Green
