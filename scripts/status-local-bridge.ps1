param(
    [int]$Port = 3050,
    [string]$ConfigPath = (Join-Path $PSScriptRoot '..\runtime\mcp.json')
)

$pkg = '@1mcp/agent@0.34.4'
$config = (Resolve-Path $ConfigPath).Path
& npx.cmd -y $pkg serve --config $config --status
$supervisor = $LASTEXITCODE

$health = "http://127.0.0.1:$Port/health/mcp/sequential-thinking"
try {
    $result = Invoke-RestMethod -Method Get -Uri $health -TimeoutSec 5
    $state = [string]$result.state
}
catch {
    $state = 'unreachable'
}

[ordered]@{
    supervisor_exit_code = $supervisor
    sequential_thinking = $state
    mcp_url = "http://127.0.0.1:$Port/mcp"
} | ConvertTo-Json

if ($supervisor -eq 0 -and $state -eq 'ready') { exit 0 }
exit 1
