[CmdletBinding()]
param(
    [string]$TunnelId,
    [switch]$ForceTunnelClientUpdate,
    [switch]$SkipSmokeTest,
    [switch]$LaunchTray
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$TunnelModule = Join-Path $PSScriptRoot 'bootstrap-tunnel-runtime.ps1'
$ManagerModule = Join-Path $PSScriptRoot 'bootstrap-manager-runtime.ps1'
$LifecycleModule = Join-Path $PSScriptRoot 'bootstrap-manager-lifecycle.ps1'

foreach ($module in @($TunnelModule, $ManagerModule, $LifecycleModule)) {
    if (-not (Test-Path -LiteralPath $module -PathType Leaf)) {
        throw "Bootstrap module is missing: $module"
    }
    . $module
}

$LocalRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
$AppRoot = Join-Path $LocalRoot 'app'
$AppScriptsDir = Join-Path $AppRoot 'scripts'
$AppRuntimeDir = Join-Path $AppRoot 'runtime'
$AppConfigDir = Join-Path $AppRoot 'config'
$BinDir = Join-Path $LocalRoot 'bin'
$TunnelDir = Join-Path $LocalRoot 'tunnel'
$StateDir = Join-Path $LocalRoot 'state'
$TunnelExe = Join-Path $BinDir 'tunnel-client.exe'
$TunnelStateFile = Join-Path $StateDir 'tunnel.json'
$LegacyTunnelProfile = Join-Path $TunnelDir 'local-1mcp.yaml'
$InstallMetadata = Join-Path $StateDir 'tunnel-client-install.json'
$AppInstallMetadata = Join-Path $StateDir 'manager-install.json'
$CommandPath = Join-Path $AppScriptsDir 'chat-platform.ps1'
$ControllerPath = Join-Path $AppScriptsDir 'chat-platform-controller.ps1'
$DirectControllerPath = Join-Path $AppScriptsDir 'semantic-direct-controller.ps1'
$TrayPath = Join-Path $AppScriptsDir 'chat-platform-tray.ps1'

$AcceptedTunnelClientVersion = 'v0.0.11'
$OfficialReleaseApi = "https://api.github.com/repos/openai/tunnel-client/releases/tags/$AcceptedTunnelClientVersion"
$AcceptedTunnelArchiveSha256 = @{
    amd64 = 'eb912c86c6ccde90cda805cb17009507176a656725cf86c36fabe1901a12e29b'
    arm64 = '38f015a720404c8ccd5976a0d6aed18d931899697eaf208548b5eb3d0f6e8592'
}

function Write-Step {
    param([Parameter(Mandatory)] [string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Require-Command {
    param([Parameter(Mandatory)] [string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) { throw "Required command is missing: $Name" }
    return $command.Source
}

function Assert-ChatBootstrapEnvironment {
    if (-not $IsWindows) { throw 'Chat Agent Platform bootstrap currently supports Windows only.' }
    if ($PSVersionTable.PSEdition -ne 'Core' -or $PSVersionTable.PSVersion.Major -lt 7) {
        throw 'PowerShell 7 or newer is required.'
    }
    if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { throw 'LOCALAPPDATA is unavailable.' }

    $null = Require-Command 'pwsh.exe'
    $node = Require-Command 'node.exe'
    $null = Require-Command 'npm.cmd'
    $python = Require-Command 'python.exe'

    $nodeVersion = (& $node --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $nodeVersion -notmatch '^v(?<major>[0-9]+)\.') {
        throw "Could not determine the installed Node.js version: $nodeVersion"
    }
    if ([int]$Matches.major -lt 20) { throw "Node.js 20 or newer is required; found $nodeVersion." }

    $pythonVersion = (& $python --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Could not determine the installed Python version: $pythonVersion" }

    foreach ($source in @(
        (Join-Path $PSScriptRoot 'chat-platform-controller.ps1'),
        (Join-Path $PSScriptRoot 'semantic-direct-controller.ps1'),
        (Join-Path $PSScriptRoot 'chat-platform.ps1'),
        (Join-Path $PSScriptRoot 'chat-platform-tray.ps1'),
        (Join-Path $RepoRoot 'runtime\semantic-projection\bin\semantic-control-plane-projection.mjs'),
        (Join-Path $RepoRoot 'runtime\semantic-projection\lib\browser-verification-bridge.mjs'),
        (Join-Path $RepoRoot 'runtime\control_plane\browser_observation.py'),
        (Join-Path $RepoRoot 'runtime\control_plane\browser_transition.py'),
        (Join-Path $RepoRoot 'runtime\control_plane\browser_transition_cli.py'),
        (Join-Path $RepoRoot 'runtime\control_plane\cli.py'),
        (Join-Path $RepoRoot 'runtime\control_plane\file_artifact_observation.py'),
        (Join-Path $RepoRoot 'runtime\control_plane\verification.py'),
        (Join-Path $RepoRoot 'runtime\control_plane\verified_workspace_artifact.py')
    )) {
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
            throw "Required six-tool platform source is missing: $source"
        }
    }

    Write-Host "POWERSHELL=$($PSVersionTable.PSVersion)"
    Write-Host "NODE=$nodeVersion"
    Write-Host "NPM=$(& npm.cmd --version)"
    Write-Host "PYTHON=$pythonVersion"
    Write-Host 'NORMAL_SEMANTIC_1MCP_REQUIRED=False'
    Write-Host 'SEMANTIC_PUBLIC_TOOL_COUNT=6'
}

Write-Step 'Проверка Windows и зависимостей normal semantic runtime'
Assert-ChatBootstrapEnvironment

Write-Step 'Получение и проверка официального OpenAI tunnel-client'
Install-ChatOfficialTunnelClient `
    -LocalRoot $LocalRoot `
    -BinDir $BinDir `
    -TunnelDir $TunnelDir `
    -StateDir $StateDir `
    -TunnelExe $TunnelExe `
    -InstallMetadata $InstallMetadata `
    -AcceptedVersion $AcceptedTunnelClientVersion `
    -ReleaseApi $OfficialReleaseApi `
    -AcceptedArchiveSha256 $AcceptedTunnelArchiveSha256 `
    -ForceUpdate:$ForceTunnelClientUpdate

Write-Step 'Разрешение постоянного tunnel anchor'
$resolvedTunnelId = Resolve-ChatTunnelId `
    -RequestedTunnelId $TunnelId `
    -TunnelStateFile $TunnelStateFile `
    -LegacyTunnelProfile $LegacyTunnelProfile
Write-Host "TUNNEL_ID=$resolvedTunnelId"
Write-Host "TUNNEL_STATE=$TunnelStateFile"
Write-Host 'TUNNEL_ANCHOR_1MCP_REQUIRED=False'

Write-Step 'Установка единого six-tool manager/runtime bundle'
Install-ChatManagerBundle `
    -RepoRoot $RepoRoot `
    -AppRoot $AppRoot `
    -AppScriptsDir $AppScriptsDir `
    -AppRuntimeDir $AppRuntimeDir `
    -AppConfigDir $AppConfigDir `
    -AppInstallMetadata $AppInstallMetadata `
    -CommandPath $CommandPath `
    -ControllerPath $ControllerPath `
    -DirectControllerPath $DirectControllerPath `
    -TrayPath $TrayPath

Write-Step 'Инициализация normal semantic core и защищённого runtime key'
$defaultFilesRoot = Initialize-ChatSemanticCore `
    -CommandPath $CommandPath `
    -LocalRoot $LocalRoot `
    -AppRoot $AppRoot `
    -TrayPath $TrayPath

if (-not $SkipSmokeTest) {
    Write-Step 'Проверка normal six-tool semantic lifecycle'
    Invoke-ChatBootstrapSmokeTest -CommandPath $CommandPath -LocalRoot $LocalRoot
}

if ($LaunchTray) {
    Start-Process -FilePath (Require-Command 'pwsh.exe') -ArgumentList @(
        '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', $TrayPath
    ) | Out-Null
}

Write-Host "`nCHAT_PLATFORM_BOOTSTRAP=OK" -ForegroundColor Green
Write-Host "LOCAL_ROOT=$LocalRoot"
Write-Host "APP_ROOT=$AppRoot"
Write-Host "TUNNEL_STATE=$TunnelStateFile"
Write-Host 'DEFAULT_PROFILE=semantic'
Write-Host "DEFAULT_FILES_ROOT=$defaultFilesRoot"
Write-Host 'SEMANTIC_BINDING=direct-stdio'
Write-Host 'SEMANTIC_PUBLIC_TOOL_COUNT=6'
Write-Host 'EXTENSION_MANAGER=optional-1mcp'
Write-Host 'LEGACY_1MCP_INSTALL_PATH_USED=False'
Write-Host 'PLATFORM_STATE=stopped'
Write-Host 'NEXT=Use the desktop shortcut or the installed chat-platform.ps1 command facade.'
