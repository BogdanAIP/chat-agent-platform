param(
    [Parameter(Mandatory)]
    [string]$FilesRoot,
    [int]$Port = 3050,
    [ValidateRange(30, 600)]
    [int]$ReadyTimeoutSeconds = 240
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$stablePkg = '@1mcp/agent@0.34.4'
$startBridge = Join-Path $PSScriptRoot 'start-local-bridge.ps1'
$stopProfiles = Join-Path $PSScriptRoot 'stop-chat-profile.ps1'
$packageHelper = Join-Path $PSScriptRoot 'semantic-projection-package.ps1'
$semanticConfig = Join-Path $repoRoot 'runtime\chat-profiles\semantic\mcp.json'

. $packageHelper

function Resolve-SafeFilesRoot {
    param([Parameter(Mandatory)] [string]$Path)

    $item = Get-Item -LiteralPath (Resolve-Path -LiteralPath $Path).Path
    if (-not $item.PSIsContainer) {
        throw "FilesRoot must be an existing directory: $Path"
    }

    $full = [System.IO.Path]::GetFullPath($item.FullName).TrimEnd('\')
    $driveRoot = [System.IO.Path]::GetPathRoot($full).TrimEnd('\')
    if ($full -ieq $driveRoot) {
        throw 'A whole drive cannot be exposed to Chat. Choose one explicit workspace folder.'
    }

    $blockedExact = @(
        $env:SystemRoot,
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)},
        $env:ProgramData,
        $env:USERPROFILE
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object {
        [System.IO.Path]::GetFullPath($_).TrimEnd('\')
    }

    if ($blockedExact | Where-Object { $_ -ieq $full }) {
        throw "Refusing broad/system FilesRoot '$full'. Choose a narrower workspace subfolder."
    }

    return $full
}

function Get-SemanticToolNames {
    param([Parameter(Mandatory)] [string]$BaseUrl)

    $inventoryText = & npx.cmd -y $stablePkg inspect semantic-projection --url $BaseUrl --format json --all 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect semantic projection.`n$inventoryText"
    }

    try {
        $inventory = $inventoryText | ConvertFrom-Json
    }
    catch {
        throw "1MCP inspect returned non-JSON semantic projection output.`n$inventoryText"
    }

    if (
        [string]$inventory.kind -ne 'server' -or
        [string]$inventory.server -ne 'semantic-projection'
    ) {
        throw 'Unexpected 1MCP inspect payload for semantic projection.'
    }

    return @($inventory.tools | ForEach-Object { [string]$_.tool } | Sort-Object)
}

if (-not (Test-Path -LiteralPath $semanticConfig -PathType Leaf)) {
    throw "Semantic profile config is missing: $semanticConfig"
}

$resolvedRoot = Resolve-SafeFilesRoot -Path $FilesRoot
$packagePath = Get-SemanticProjectionPackagePath -RepoRoot $repoRoot -Ensure

$hadFilesRoot = Test-Path Env:CHAT_LOCAL_FILES_ROOT
$oldFilesRoot = if ($hadFilesRoot) { $env:CHAT_LOCAL_FILES_ROOT } else { $null }
$hadPackage = Test-Path Env:CHAT_SEMANTIC_PROJECTION_PACKAGE
$oldPackage = if ($hadPackage) { $env:CHAT_SEMANTIC_PROJECTION_PACKAGE } else { $null }

try {
    $env:CHAT_LOCAL_FILES_ROOT = $resolvedRoot
    $env:CHAT_SEMANTIC_PROJECTION_PACKAGE = $packagePath

    # The shared stop script is the single conflict cleanup path for all
    # already-accepted direct/adaptive Runtime Scopes.
    & $stopProfiles

    Write-Host "FILES_ROOT=$resolvedRoot" -ForegroundColor Yellow
    Write-Host "SEMANTIC_PROJECTION_PACKAGE=$packagePath" -ForegroundColor DarkGray

    & $startBridge `
        -Port $Port `
        -ConfigPath $semanticConfig `
        -OneMcpPackage $stablePkg `
        -HealthServerName 'semantic-projection' `
        -ReadyTimeoutSeconds $ReadyTimeoutSeconds

    $baseUrl = "http://127.0.0.1:$Port"
    $tools = @(Get-SemanticToolNames -BaseUrl $baseUrl)
    $expected = @(
        'web_interact',
        'web_observe',
        'web_open',
        'workspace_read',
        'workspace_write'
    )

    if (($tools -join "`n") -ne ($expected -join "`n")) {
        throw "Semantic profile surface drifted. Expected: $($expected -join ', '); actual: $($tools -join ', ')"
    }

    Write-Host 'CHAT_PROFILE_STATUS=ready' -ForegroundColor Green
    Write-Host 'CHAT_PROFILE=semantic'
    Write-Host "ONE_MCP=$stablePkg"
    Write-Host "MCP_URL=$baseUrl/mcp"
    Write-Host 'SEMANTIC_TOOL_COUNT=5'
}
catch {
    & npx.cmd -y $stablePkg serve --config $semanticConfig --stop *> $null
    throw
}
finally {
    if ($hadFilesRoot) {
        $env:CHAT_LOCAL_FILES_ROOT = $oldFilesRoot
    }
    else {
        Remove-Item Env:CHAT_LOCAL_FILES_ROOT -ErrorAction SilentlyContinue
    }

    if ($hadPackage) {
        $env:CHAT_SEMANTIC_PROJECTION_PACKAGE = $oldPackage
    }
    else {
        Remove-Item Env:CHAT_SEMANTIC_PROJECTION_PACKAGE -ErrorAction SilentlyContinue
    }
}
