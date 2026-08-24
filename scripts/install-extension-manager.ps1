param(
    [ValidateSet('Install', 'Remove', 'Status')]
    [string]$Action = 'Install'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$LocalRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
$AppRoot = Join-Path $LocalRoot 'app'
$AppRuntimeDir = Join-Path $AppRoot 'runtime'
$AppScriptsDir = Join-Path $AppRoot 'scripts'
$MetadataPath = Join-Path $AppRoot 'extension-manager-install.json'
$BaselineCommand = Join-Path $AppScriptsDir 'chat-platform.ps1'
$ManagerModule = Join-Path $PSScriptRoot 'bootstrap-manager-runtime.ps1'

. $ManagerModule

$assets = @(
    @('runtime\chat-profiles\adaptive\mcp.json', 'runtime\chat-profiles\adaptive\mcp.json'),
    @('runtime\1mcp-adaptive-shim\package.json', 'runtime\1mcp-adaptive-shim\package.json'),
    @('runtime\1mcp-adaptive-shim\bin\1mcp-adaptive.mjs', 'runtime\1mcp-adaptive-shim\bin\1mcp-adaptive.mjs'),
    @('runtime\1mcp-adaptive-shim\scripts\apply-compatibility-patch.mjs', 'runtime\1mcp-adaptive-shim\scripts\apply-compatibility-patch.mjs')
)

function Get-InstalledExtensionState {
    $missing = @()
    foreach ($pair in $assets) {
        $destination = Join-Path $AppRoot ([string]$pair[1])
        if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) {
            $missing += ([string]$pair[1]).Replace('\', '/')
        }
    }

    [ordered]@{
        schema_version = 1
        extension_manager = '1mcp'
        installed = ($missing.Count -eq 0)
        baseline_semantic_dependency = $false
        metadata_present = (Test-Path -LiteralPath $MetadataPath -PathType Leaf)
        missing_assets = $missing
    }
}

if ($Action -eq 'Status') {
    Get-InstalledExtensionState | ConvertTo-Json -Depth 5
    exit 0
}

if ($Action -eq 'Remove') {
    foreach ($pair in $assets) {
        $destination = Join-Path $AppRoot ([string]$pair[1])
        Remove-Item -LiteralPath $destination -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $MetadataPath -Force -ErrorAction SilentlyContinue
    Write-Host 'EXTENSION_MANAGER_INSTALLED=False'
    Write-Host 'BASELINE_SEMANTIC_DEPENDENCY=False'
    exit 0
}

if (-not (Test-Path -LiteralPath $BaselineCommand -PathType Leaf)) {
    throw "Baseline Chat Agent Platform is not installed. Run bootstrap-chat-platform.ps1 first: $BaselineCommand"
}

foreach ($pair in $assets) {
    $source = Join-Path $RepoRoot ([string]$pair[0])
    $destination = Join-Path $AppRoot ([string]$pair[1])
    Copy-ChatVerifiedFile -Source $source -Destination $destination
}

Assert-ChatInstalledAdaptiveRuntime -AppRuntimeDir $AppRuntimeDir

[ordered]@{
    schema_version = 1
    extension_manager = '1mcp'
    role = 'optional-internal-extension-manager'
    baseline_semantic_dependency = $false
    source_root = $RepoRoot
    app_root = $AppRoot
    installed_at = (Get-Date).ToUniversalTime().ToString('o')
    assets = @($assets | ForEach-Object { ([string]$_[0]).Replace('\', '/') })
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $MetadataPath -Encoding utf8

Write-Host 'EXTENSION_MANAGER=1mcp-optional-internal'
Write-Host 'EXTENSION_MANAGER_INSTALLED=True'
Write-Host 'BASELINE_SEMANTIC_DEPENDENCY=False' -ForegroundColor Green