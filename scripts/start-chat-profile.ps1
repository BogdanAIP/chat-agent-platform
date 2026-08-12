param(
    [Parameter(Mandatory)]
    [ValidateSet('files-readonly', 'browser-isolated', 'adaptive')]
    [string]$Profile,
    [string]$FilesRoot,
    [int]$Port = 3050,
    [ValidateRange(30, 600)]
    [int]$ReadyTimeoutSeconds = 180
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pkg = '@1mcp/agent@0.34.4'
$startBridge = Join-Path $PSScriptRoot 'start-local-bridge.ps1'

$referenceConfig = Join-Path $repoRoot 'runtime\mcp.json'
$filesConfig = Join-Path $repoRoot 'runtime\chat-profiles\files-readonly\mcp.json'
$browserConfig = Join-Path $repoRoot 'runtime\chat-profiles\browser-isolated\mcp.json'
$adaptiveConfig = Join-Path $repoRoot 'runtime\chat-profiles\adaptive\mcp.json'

$definitions = @{
    'files-readonly' = @{
        Config = $filesConfig
        HealthServer = 'filesystem'
        RuntimeReadyOnly = $false
        EnableLazyLoading = $false
        DisableAsyncLoading = $false
        InternalTools = ''
    }
    'browser-isolated' = @{
        Config = $browserConfig
        HealthServer = 'playwright'
        RuntimeReadyOnly = $false
        EnableLazyLoading = $false
        DisableAsyncLoading = $false
        InternalTools = ''
    }
    'adaptive' = @{
        Config = $adaptiveConfig
        HealthServer = ''
        RuntimeReadyOnly = $true
        EnableLazyLoading = $true
        DisableAsyncLoading = $true
        InternalTools = 'list,status,enable,disable,reload'
    }
}

function Stop-KnownRuntime {
    param([Parameter(Mandatory)] [string]$ConfigPath)

    if (-not (Test-Path -LiteralPath $ConfigPath)) { return }
    & npx.cmd -y $pkg serve --config $ConfigPath --stop *> $null
    $stopCode = $LASTEXITCODE
    if ($stopCode -notin @(0, 3, 7)) {
        throw "Unable to stop 1MCP Runtime Scope for $ConfigPath (exit $stopCode)."
    }
}

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

function Get-InventoryToolNames {
    param(
        [Parameter(Mandatory)] [string]$ServerName,
        [Parameter(Mandatory)] [string]$BaseUrl
    )

    $inventoryText = & npx.cmd -y $pkg inspect $ServerName --url $BaseUrl --format json --all 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect '$ServerName'.`n$inventoryText"
    }

    try {
        $inventory = $inventoryText | ConvertFrom-Json
    }
    catch {
        throw "1MCP inspect returned non-JSON output for '$ServerName'.`n$inventoryText"
    }

    if ([string]$inventory.kind -ne 'server' -or [string]$inventory.server -ne $ServerName) {
        throw "Unexpected 1MCP inspect payload for '$ServerName'."
    }

    return @($inventory.tools | ForEach-Object { [string]$_.tool })
}

function Assert-AdaptiveConfigContract {
    param([Parameter(Mandatory)] [string]$ConfigPath)

    $configObject = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
    foreach ($serverName in @('filesystem', 'playwright')) {
        $server = $configObject.mcpServers.$serverName
        if ($null -eq $server) {
            throw "Adaptive profile is missing backend '$serverName'."
        }
        if (-not [bool]$server.disabled) {
            throw "Adaptive backend '$serverName' must start disabled for task-driven activation."
        }
    }

    $filesystemDisabled = @($configObject.mcpServers.filesystem.disabledTools)
    foreach ($forbidden in @('create_directory', 'write_file', 'edit_file', 'move_file')) {
        if ($filesystemDisabled -notcontains $forbidden) {
            throw "Adaptive filesystem backend must keep '$forbidden' disabled."
        }
    }

    $browserDisabled = @($configObject.mcpServers.playwright.disabledTools)
    foreach ($forbidden in @('browser_run_code_unsafe', 'browser_evaluate', 'browser_file_upload', 'browser_network_request')) {
        if ($browserDisabled -notcontains $forbidden) {
            throw "Adaptive browser backend must keep '$forbidden' disabled."
        }
    }
}

function Assert-ProfileSurface {
    param(
        [Parameter(Mandatory)] [string]$ProfileName,
        [Parameter(Mandatory)] [string]$BaseUrl
    )

    if ($ProfileName -eq 'adaptive') {
        # The adaptive profile intentionally starts with every backend disabled.
        # Its Chat-facing surface is the stable 1MCP lazy/meta-tool contract and
        # selected lifecycle tools; real Chat acceptance verifies that snapshot.
        return
    }

    if ($ProfileName -eq 'files-readonly') {
        $tools = @(Get-InventoryToolNames -ServerName 'filesystem' -BaseUrl $BaseUrl)
        foreach ($forbidden in @('create_directory', 'write_file', 'edit_file', 'move_file')) {
            if ($tools -contains $forbidden) {
                throw "Files profile unexpectedly exposes '$forbidden'."
            }
        }
        foreach ($required in @('read_text_file', 'list_allowed_directories')) {
            if ($tools -notcontains $required) {
                throw "Files profile is missing '$required'."
            }
        }
        if ($tools | Where-Object { $_ -like 'browser_*' }) {
            throw 'Files profile unexpectedly exposes browser tools.'
        }
        return
    }

    $tools = @(Get-InventoryToolNames -ServerName 'playwright' -BaseUrl $BaseUrl)
    if ($tools -notcontains 'browser_navigate') {
        throw 'Browser profile is missing browser_navigate.'
    }
    foreach ($forbidden in @('browser_run_code_unsafe', 'browser_evaluate', 'browser_file_upload', 'browser_network_request')) {
        if ($tools -contains $forbidden) {
            throw "Browser profile unexpectedly exposes '$forbidden'."
        }
    }
    foreach ($filesystemTool in @('read_text_file', 'write_file', 'list_allowed_directories')) {
        if ($tools -contains $filesystemTool) {
            throw "Browser profile unexpectedly exposes filesystem tool '$filesystemTool'."
        }
    }
}

$selected = $definitions[$Profile]
$selectedConfig = [string]$selected.Config
$healthServer = [string]$selected.HealthServer

# Only one Chat-facing Runtime Scope may own the fixed tunnel target port.
foreach ($config in @($referenceConfig, $filesConfig, $browserConfig, $adaptiveConfig)) {
    Stop-KnownRuntime -ConfigPath $config
}

$hadFilesRoot = Test-Path Env:CHAT_LOCAL_FILES_ROOT
$oldFilesRoot = if ($hadFilesRoot) { $env:CHAT_LOCAL_FILES_ROOT } else { $null }

try {
    if ($Profile -in @('files-readonly', 'adaptive')) {
        if ([string]::IsNullOrWhiteSpace($FilesRoot)) {
            throw "$Profile requires -FilesRoot with one explicit workspace directory."
        }
        $env:CHAT_LOCAL_FILES_ROOT = Resolve-SafeFilesRoot -Path $FilesRoot
        Write-Host "FILES_ROOT=$env:CHAT_LOCAL_FILES_ROOT" -ForegroundColor Yellow
    }
    elseif (-not [string]::IsNullOrWhiteSpace($FilesRoot)) {
        throw '-FilesRoot is only valid for files-readonly or adaptive.'
    }

    if ($Profile -eq 'adaptive') {
        Assert-AdaptiveConfigContract -ConfigPath $selectedConfig
    }

    $bridgeArgs = @{
        Port = $Port
        ConfigPath = $selectedConfig
        ReadyTimeoutSeconds = $ReadyTimeoutSeconds
    }
    if ([bool]$selected.RuntimeReadyOnly) {
        $bridgeArgs.RuntimeReadyOnly = $true
    }
    else {
        $bridgeArgs.HealthServerName = $healthServer
    }
    if ([bool]$selected.EnableLazyLoading) {
        $bridgeArgs.EnableLazyLoading = $true
    }
    if ([bool]$selected.DisableAsyncLoading) {
        $bridgeArgs.DisableAsyncLoading = $true
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$selected.InternalTools)) {
        $bridgeArgs.InternalTools = [string]$selected.InternalTools
    }

    # start-local-bridge.ps1 terminates on failure. Do not inspect $LASTEXITCODE here:
    # it may legitimately retain the supervisor's transient 4/5 status after readiness.
    & $startBridge @bridgeArgs

    $baseUrl = "http://127.0.0.1:$Port"
    Assert-ProfileSurface -ProfileName $Profile -BaseUrl $baseUrl

    Write-Host 'CHAT_PROFILE_STATUS=ready' -ForegroundColor Green
    Write-Host "CHAT_PROFILE=$Profile"
    Write-Host "MCP_URL=$baseUrl/mcp"
}
catch {
    Stop-KnownRuntime -ConfigPath $selectedConfig
    throw
}
finally {
    if ($hadFilesRoot) {
        $env:CHAT_LOCAL_FILES_ROOT = $oldFilesRoot
    }
    else {
        Remove-Item Env:CHAT_LOCAL_FILES_ROOT -ErrorAction SilentlyContinue
    }
}
