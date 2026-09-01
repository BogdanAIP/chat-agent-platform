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
$stablePkg = '@1mcp/agent@0.34.4'
$adaptivePkg = '@1mcp/agent@0.35.0-beta.3'
$pkg = $stablePkg
$startBridge = Join-Path $PSScriptRoot 'start-local-bridge.ps1'
$adaptiveShim = Join-Path $repoRoot 'runtime\1mcp-adaptive-shim'

$referenceConfig = Join-Path $repoRoot 'runtime\mcp.json'
$filesConfig = Join-Path $repoRoot 'runtime\chat-profiles\files-readonly\mcp.json'
$browserConfig = Join-Path $repoRoot 'runtime\chat-profiles\browser-isolated\mcp.json'
$adaptiveConfig = Join-Path $repoRoot 'runtime\chat-profiles\adaptive\mcp.json'

$definitions = @{
    'files-readonly' = @{
        Config = $filesConfig
        Package = $stablePkg
        HealthServer = 'filesystem'
        RuntimeReadyOnly = $false
        EnableLazyLoading = $false
        DisableAsyncLoading = $false
        InternalTools = ''
    }
    'browser-isolated' = @{
        Config = $browserConfig
        Package = $stablePkg
        HealthServer = 'playwright'
        RuntimeReadyOnly = $false
        EnableLazyLoading = $false
        DisableAsyncLoading = $false
        InternalTools = ''
    }
    'adaptive' = @{
        Config = $adaptiveConfig
        Package = $adaptivePkg
        HealthServer = ''
        RuntimeReadyOnly = $true
        EnableLazyLoading = $true
        DisableAsyncLoading = $true
        InternalTools = 'list,status,enable,disable,reload'
        LauncherExecutable = '1mcp-adaptive'
    }
}

function New-AdaptiveLauncherPackage {
    if (-not (Test-Path -LiteralPath $adaptiveShim -PathType Container)) {
        throw "Adaptive compatibility package is missing: $adaptiveShim"
    }

    $manifestPath = Join-Path $adaptiveShim 'package.json'
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ([string]$manifest.dependencies.'@1mcp/agent' -ne '0.35.0-beta.3') {
        throw 'Adaptive compatibility package must pin @1mcp/agent 0.35.0-beta.3 exactly.'
    }

    $sourceFiles = @(Get-ChildItem -LiteralPath $adaptiveShim -Recurse -File | Sort-Object FullName)
    if ($sourceFiles.Count -eq 0) {
        throw "Adaptive compatibility package contains no source files: $adaptiveShim"
    }
    $fingerprintInput = ($sourceFiles | ForEach-Object {
        $relative = $_.FullName.Substring($adaptiveShim.Length).TrimStart('\', '/')
        "$relative`0$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)"
    }) -join "`n"
    $fingerprintBytes = [System.Text.Encoding]::UTF8.GetBytes($fingerprintInput)
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        $fingerprintHash = $sha256.ComputeHash($fingerprintBytes)
    }
    finally {
        $sha256.Dispose()
    }
    $fingerprint = (($fingerprintHash | ForEach-Object { $_.ToString('x2') }) -join '').Substring(0, 16)

    $cacheDir = Join-Path ([System.IO.Path]::GetTempPath()) "chat-agent-platform\adaptive-shim\$fingerprint"
    New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
    $packageBaseName = ([string]$manifest.name).TrimStart('@').Replace('/', '-')
    $packagePath = Join-Path $cacheDir "$packageBaseName-$($manifest.version).tgz"
    if (-not (Test-Path -LiteralPath $packagePath -PathType Leaf)) {
        $npmName = if ($IsWindows) { 'npm.cmd' } else { 'npm' }
        $npm = (Get-Command $npmName -ErrorAction Stop).Source
        $stagingDir = Join-Path $cacheDir ('.pack-' + [guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $stagingDir | Out-Null
        try {
            $stagedPackage = Join-Path $stagingDir (Split-Path -Leaf $packagePath)
            $packOutput = & $npm pack $adaptiveShim --pack-destination $stagingDir --silent 2>&1 | Out-String
            if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $stagedPackage -PathType Leaf)) {
                throw "Could not prepare adaptive compatibility package.`n$packOutput"
            }
            try {
                [System.IO.File]::Move($stagedPackage, $packagePath)
            }
            catch {
                # A concurrent launcher may have atomically populated the same
                # content-addressed cache entry first.
                if (-not (Test-Path -LiteralPath $packagePath -PathType Leaf)) {
                    throw
                }
            }
        }
        finally {
            if (Test-Path -LiteralPath $stagingDir -PathType Container) {
                [System.IO.Directory]::Delete($stagingDir, $true)
            }
        }
    }

    return $packagePath
}

function Stop-KnownRuntime {
    param(
        [Parameter(Mandatory)] [string]$ConfigPath,
        [Parameter(Mandatory)] [string]$Package
    )

    if (-not (Test-Path -LiteralPath $ConfigPath)) { return }
    & npx.cmd -y $Package serve --config $ConfigPath --stop *> $null
    $stopCode = $LASTEXITCODE
    if ($stopCode -notin @(0, 3, 7)) {
        throw "Unable to stop 1MCP Runtime Scope for $ConfigPath (exit $stopCode)."
    }
}

function Resolve-PhysicalDirectoryPath {
    param([Parameter(Mandatory)] [string]$Path)

    $nodeName = if ($IsWindows) { 'node.exe' } else { 'node' }
    $node = (Get-Command $nodeName -ErrorAction Stop).Source
    $realPathScript = "const fs=require('node:fs');process.stdout.write(fs.realpathSync.native(process.argv[1]));"
    $output = @(& $node -e $realPathScript $Path 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "Could not resolve physical FilesRoot '$Path': $($output -join ' ')"
    }
    $physical = ($output -join "`n").Trim()
    if ([string]::IsNullOrWhiteSpace($physical)) {
        throw "Could not resolve physical FilesRoot '$Path'."
    }
    return [System.IO.Path]::GetFullPath($physical).TrimEnd('\', '/')
}

function Test-PathsOverlap {
    param(
        [Parameter(Mandatory)] [string]$Left,
        [Parameter(Mandatory)] [string]$Right
    )

    $leftPath = [System.IO.Path]::GetFullPath($Left).TrimEnd('\', '/')
    $rightPath = [System.IO.Path]::GetFullPath($Right).TrimEnd('\', '/')
    if ($leftPath -ieq $rightPath) {
        return $true
    }

    $separator = [System.IO.Path]::DirectorySeparatorChar
    return (
        $leftPath.StartsWith(
            $rightPath + $separator,
            [StringComparison]::OrdinalIgnoreCase
        ) -or
        $rightPath.StartsWith(
            $leftPath + $separator,
            [StringComparison]::OrdinalIgnoreCase
        )
    )
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

    $physicalFull = Resolve-PhysicalDirectoryPath -Path $full
    if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        $managerRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
        if (Test-Path -LiteralPath $managerRoot -PathType Container) {
            $physicalManagerRoot = Resolve-PhysicalDirectoryPath -Path $managerRoot
        }
        else {
            $physicalManagerRoot = [System.IO.Path]::GetFullPath($managerRoot).TrimEnd('\', '/')
        }
        if (Test-PathsOverlap -Left $physicalFull -Right $physicalManagerRoot) {
            throw "Refusing FilesRoot '$physicalFull' because Chat workspaces must be path-disjoint from manager-owned state '$physicalManagerRoot'."
        }
    }

    return $physicalFull
}

function Get-InventoryToolNames {
    param(
        [Parameter(Mandatory)] [string]$ServerName,
        [Parameter(Mandatory)] [string]$BaseUrl
    )

    $inventoryText = & npx.cmd -y $stablePkg inspect $ServerName --url $BaseUrl --format json --all 2>&1 | Out-String
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

function Reset-AdaptiveCatalogToDisabled {
    param([Parameter(Mandatory)] [string]$ConfigPath)

    $configObject = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
    $changed = $false
    foreach ($serverName in @('filesystem', 'playwright')) {
        $server = $configObject.mcpServers.$serverName
        if ($null -eq $server) {
            throw "Adaptive profile is missing backend '$serverName'."
        }
        if (-not [bool]$server.disabled) {
            $server.disabled = $true
            $changed = $true
        }
    }

    if ($changed) {
        $configObject |
            ConvertTo-Json -Depth 20 |
            Set-Content -LiteralPath $ConfigPath -Encoding utf8
        Write-Host 'ADAPTIVE_CATALOG_RESET=all-disabled' -ForegroundColor DarkGray
    }
}

function Assert-ProfileSurface {
    param(
        [Parameter(Mandatory)] [string]$ProfileName,
        [Parameter(Mandatory)] [string]$BaseUrl
    )

    if ($ProfileName -eq 'adaptive') {
        # The adaptive profile intentionally starts with every backend disabled.
        # The hash-guarded compatibility package refreshes the lazy registry
        # after backend load/unload while preserving this stable Chat surface.
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
$selectedPackage = [string]$selected.Package
$healthServer = [string]$selected.HealthServer

# Only one Chat-facing Runtime Scope may own the fixed tunnel target port.
foreach ($runtime in @(
    @{ Config = $referenceConfig; Package = $stablePkg },
    @{ Config = $filesConfig; Package = $stablePkg },
    @{ Config = $browserConfig; Package = $stablePkg },
    @{ Config = $adaptiveConfig; Package = $adaptivePkg }
)) {
    Stop-KnownRuntime -ConfigPath ([string]$runtime.Config) -Package ([string]$runtime.Package)
}

if ($Profile -eq 'adaptive') {
    # mcp_enable persists its state in mcp.json. Normalize the pre-approved
    # catalog after all Runtime Scopes are stopped so an interrupted prior
    # session cannot make the next manager start fail open or become unusable.
    Reset-AdaptiveCatalogToDisabled -ConfigPath $selectedConfig
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
        OneMcpPackage = $selectedPackage
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
    if ($Profile -eq 'adaptive') {
        $bridgeArgs.OneMcpLauncherPackage = New-AdaptiveLauncherPackage
        $bridgeArgs.OneMcpLauncherExecutable = [string]$selected.LauncherExecutable
    }

    # start-local-bridge.ps1 terminates on failure. Do not inspect $LASTEXITCODE here:
    # it may legitimately retain the supervisor's transient 4/5 status after readiness.
    & $startBridge @bridgeArgs

    $baseUrl = "http://127.0.0.1:$Port"
    Assert-ProfileSurface -ProfileName $Profile -BaseUrl $baseUrl

    Write-Host 'CHAT_PROFILE_STATUS=ready' -ForegroundColor Green
    Write-Host "CHAT_PROFILE=$Profile"
    Write-Host "ONE_MCP=$selectedPackage"
    Write-Host "MCP_URL=$baseUrl/mcp"
}
catch {
    Stop-KnownRuntime -ConfigPath $selectedConfig -Package $selectedPackage
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
