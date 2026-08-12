param(
    [int]$Port = 3050
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$stablePkg = '@1mcp/agent@0.34.4'
$adaptivePkg = '@1mcp/agent@0.35.0-beta.3'

$scopes = @(
    @{ Name = 'reference'; Config = (Join-Path $repoRoot 'runtime\mcp.json'); Package = $stablePkg; Health = 'sequential-thinking'; RuntimeReadyOnly = $false },
    @{ Name = 'files-readonly'; Config = (Join-Path $repoRoot 'runtime\chat-profiles\files-readonly\mcp.json'); Package = $stablePkg; Health = 'filesystem'; RuntimeReadyOnly = $false },
    @{ Name = 'browser-isolated'; Config = (Join-Path $repoRoot 'runtime\chat-profiles\browser-isolated\mcp.json'); Package = $stablePkg; Health = 'playwright'; RuntimeReadyOnly = $false },
    @{ Name = 'adaptive'; Config = (Join-Path $repoRoot 'runtime\chat-profiles\adaptive\mcp.json'); Package = $adaptivePkg; Health = '1mcp-runtime'; RuntimeReadyOnly = $true }
)

$result = @()
foreach ($scope in $scopes) {
    if (-not (Test-Path -LiteralPath $scope.Config)) { continue }

    $statusText = & npx.cmd -y ([string]$scope.Package) serve --config $scope.Config --status 2>&1 | Out-String
    $code = $LASTEXITCODE
    $healthState = 'not-running'

    if ($code -eq 0) {
        try {
            if ([bool]$scope.RuntimeReadyOnly) {
                $health = Invoke-WebRequest -Method Get -Uri "http://127.0.0.1:$Port/health/ready" -TimeoutSec 5
                $healthState = if ($health.StatusCode -eq 200) { 'ready' } else { 'unhealthy' }
            }
            else {
                $health = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:$Port/health/mcp/$($scope.Health)" -TimeoutSec 5
                $healthState = [string]$health.state
            }
        }
        catch {
            $healthState = 'unreachable'
        }
    }

    $result += [ordered]@{
        profile = $scope.Name
        one_mcp = [string]$scope.Package
        supervisor_exit_code = $code
        running = ($code -eq 0)
        health_server = $scope.Health
        health_state = $healthState
    }
}

$active = @($result | Where-Object { $_.running })
$conflict = ($active.Count -gt 1)
$state = if ($conflict) {
    'conflict'
}
elseif ($active.Count -eq 1) {
    'active'
}
else {
    'stopped'
}

[ordered]@{
    mcp_url = "http://127.0.0.1:$Port/mcp"
    state = $state
    conflict = $conflict
    active_count = $active.Count
    active_profile = if ($active.Count -eq 1) { $active[0].profile } else { $null }
    active_one_mcp = if ($active.Count -eq 1) { $active[0].one_mcp } else { $null }
    scopes = $result
} | ConvertTo-Json -Depth 6

# A recognized conflict is machine-readable state, not a transport/protocol failure.
# Lifecycle controllers can now observe active_count > 1 and safely stop/recover it.
exit 0
