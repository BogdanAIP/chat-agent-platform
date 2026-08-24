Set-StrictMode -Version Latest

function Copy-ChatVerifiedFile {
    param(
        [Parameter(Mandatory)] [string]$Source,
        [Parameter(Mandatory)] [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw "Manager source file is missing: $Source"
    }

    $parent = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $temporary = "$Destination.new"
    try {
        Copy-Item -LiteralPath $Source -Destination $temporary -Force
        $sourceHash = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
        $copyHash = (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash
        if ($sourceHash -ne $copyHash) {
            throw "Manager file copy verification failed: $Source"
        }
        Move-Item -LiteralPath $temporary -Destination $Destination -Force
    }
    finally {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
    }
}

function Stop-ChatInstalledManagerForBundleUpdate {
    param([Parameter(Mandatory)] [string]$CommandPath)

    if (-not (Test-Path -LiteralPath $CommandPath -PathType Leaf)) {
        return
    }
    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    & $pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $CommandPath -Action Stop -NoNotify
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not stop the installed manager before updating its runtime bundle.'
    }
}

function Assert-ChatInstalledAdaptiveRuntime {
    param([Parameter(Mandatory)] [string]$AppRuntimeDir)

    $manifestPath = Join-Path $AppRuntimeDir '1mcp-adaptive-shim\package.json'
    $adaptiveConfigPath = Join-Path $AppRuntimeDir 'chat-profiles\adaptive\mcp.json'
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if (
        [string]$manifest.name -ne '@chat-agent-platform/1mcp-adaptive-shim' -or
        [string]$manifest.version -ne '0.1.0' -or
        [string]$manifest.bin.'1mcp-adaptive' -ne 'bin/1mcp-adaptive.mjs' -or
        [string]$manifest.scripts.postinstall -ne 'node scripts/apply-compatibility-patch.mjs' -or
        [string]$manifest.dependencies.'@1mcp/agent' -ne '0.35.0-beta.3' -or
        [string]$manifest.engines.node -ne '>=20'
    ) {
        throw 'Installed adaptive compatibility manifest failed its pinned contract.'
    }

    $expectedPackageFiles = @('bin/1mcp-adaptive.mjs', 'scripts/apply-compatibility-patch.mjs')
    if ((@($manifest.files) -join "`n") -ne ($expectedPackageFiles -join "`n")) {
        throw 'Installed adaptive package file allowlist drifted.'
    }

    $adaptive = Get-Content -LiteralPath $adaptiveConfigPath -Raw | ConvertFrom-Json
    foreach ($name in @('filesystem', 'playwright')) {
        if ($null -eq $adaptive.mcpServers.$name -or -not [bool]$adaptive.mcpServers.$name.disabled) {
            throw "Installed adaptive backend '$name' must exist and start disabled."
        }
    }
    $adaptiveRaw = Get-Content -LiteralPath $adaptiveConfigPath -Raw
    foreach ($pin in @('@modelcontextprotocol/server-filesystem@2026.7.10', '@playwright/mcp@0.0.78')) {
        if ($adaptiveRaw -notmatch [regex]::Escape($pin)) {
            throw "Installed adaptive runtime is missing pin '$pin'."
        }
    }
}

function Assert-ChatInstalledSixToolSemanticRuntime {
    param(
        [Parameter(Mandatory)] [string]$AppRuntimeDir,
        [Parameter(Mandatory)] [string]$AppScriptsDir,
        [Parameter(Mandatory)] [string]$AppConfigDir
    )

    $semanticRoot = Join-Path $AppRuntimeDir 'semantic-projection'
    $controlPlaneRoot = Join-Path $AppRuntimeDir 'control_plane'
    $manifestPath = Join-Path $semanticRoot 'package.json'
    $lockPath = Join-Path $semanticRoot 'package-lock.json'
    $semanticConfigPath = Join-Path $AppRuntimeDir 'chat-profiles\semantic\mcp.json'
    $visionConfigPath = Join-Path $AppConfigDir 'local-vision-runtime.json'

    $expectedPackageFiles = @(
        'bin/semantic-projection-launcher.mjs',
        'bin/semantic-control-plane-projection.mjs',
        'bin/semantic-projection.mjs',
        'lib/semantic-vision-click-router.mjs',
        'lib/visual-grounding-bridge.mjs',
        'lib/runtime-backed-bridge-grounder.mjs',
        'lib/runtime-backed-visual-grounder.mjs'
    )
    $controlPlaneFiles = @('__init__.py', 'cli.py', 'verified_workspace_artifact.py')
    $visionScripts = @(
        'local-vision-runtime.ps1',
        'local-vision-runtime-watchdog.ps1',
        'verify-local-vision-listener.ps1',
        'production-visual-grounder.py'
    )
    $visionPythonFiles = @(
        '__init__.py', 'benchmark.py', 'mark_grid.py', 'native_bbox.py',
        'production_grounder.py', 'production_policy.py', 'provider.py', 'renderer.py'
    )

    $required = [System.Collections.Generic.List[string]]::new()
    foreach ($path in @($manifestPath, $lockPath, $semanticConfigPath, $visionConfigPath)) {
        $required.Add($path)
    }
    foreach ($relative in $expectedPackageFiles) {
        $required.Add((Join-Path $semanticRoot ($relative -replace '/', '\')))
    }
    foreach ($name in $controlPlaneFiles) {
        $required.Add((Join-Path $controlPlaneRoot $name))
    }
    foreach ($name in $visionScripts) {
        $required.Add((Join-Path $AppScriptsDir $name))
    }
    foreach ($name in $visionPythonFiles) {
        $required.Add((Join-Path $AppRuntimeDir "local_vision_adapter\$name"))
    }
    foreach ($path in $required) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Installed semantic/vision/control-plane runtime asset is missing: $path"
        }
    }

    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $pins = [ordered]@{
        '@modelcontextprotocol/client' = '2.0.0'
        '@modelcontextprotocol/server' = '2.0.0'
        '@modelcontextprotocol/server-filesystem' = '2026.7.10'
        '@playwright/mcp' = '0.0.78'
        'zod' = '4.4.3'
    }
    if (
        [string]$manifest.name -ne '@chat-agent-platform/semantic-projection' -or
        [string]$manifest.version -ne '0.1.0' -or
        [string]$manifest.bin.'chat-semantic-projection' -ne 'bin/semantic-projection-launcher.mjs' -or
        [string]$manifest.engines.node -ne '>=20'
    ) {
        throw 'Installed semantic projection manifest failed its pinned contract.'
    }
    foreach ($name in $pins.Keys) {
        if ([string]$manifest.dependencies.$name -ne [string]$pins[$name]) {
            throw "Installed semantic dependency pin drifted: $name"
        }
    }
    if ((@($manifest.files) -join "`n") -ne ($expectedPackageFiles -join "`n")) {
        throw 'Installed semantic package file allowlist drifted.'
    }

    $lock = Get-Content -LiteralPath $lockPath -Raw | ConvertFrom-Json -AsHashtable
    if ([int]$lock['lockfileVersion'] -ne 3) {
        throw 'Installed semantic package-lock must use lockfileVersion 3.'
    }
    $rootPackage = $lock['packages']['']
    foreach ($name in $pins.Keys) {
        if ([string]$rootPackage['dependencies'][$name] -ne [string]$pins[$name]) {
            throw "Installed semantic lockfile dependency pin drifted: $name"
        }
    }

    $launcherSource = Get-Content -LiteralPath (Join-Path $semanticRoot 'bin\semantic-projection-launcher.mjs') -Raw
    $deleteIndex = $launcherSource.IndexOf('delete process.env[key]', [StringComparison]::Ordinal)
    $controlIndex = $launcherSource.IndexOf("'CONTROL_PLANE_API_KEY'", [StringComparison]::Ordinal)
    $openAiIndex = $launcherSource.IndexOf("'OPENAI_API_KEY'", [StringComparison]::Ordinal)
    $adminIndex = $launcherSource.IndexOf("'OPENAI_ADMIN_KEY'", [StringComparison]::Ordinal)
    $entryIndex = $launcherSource.IndexOf("path.join(launcherDir, 'semantic-control-plane-projection.mjs')", [StringComparison]::Ordinal)
    $spawnIndex = $launcherSource.IndexOf('spawn(process.execPath, [semanticEntry]', [StringComparison]::Ordinal)
    if (
        $deleteIndex -lt 0 -or $controlIndex -lt 0 -or $openAiIndex -lt 0 -or $adminIndex -lt 0 -or
        $entryIndex -lt 0 -or $spawnIndex -lt 0 -or $deleteIndex -gt $spawnIndex -or $entryIndex -gt $spawnIndex
    ) {
        throw 'Installed semantic six-tool credential-scrub launcher failed its runtime contract.'
    }

    $publicSource = Get-Content -LiteralPath (Join-Path $semanticRoot 'bin\semantic-control-plane-projection.mjs') -Raw
    foreach ($toolName in @(
        'workspace_read', 'workspace_write', 'web_open', 'web_observe', 'web_interact', 'procedure_run'
    )) {
        if ($publicSource.IndexOf("server.registerTool('$toolName'", [StringComparison]::Ordinal) -lt 0) {
            throw "Installed canonical semantic projection is missing '$toolName'."
        }
    }
    if ([regex]::Matches($publicSource, 'server\.registerTool\(').Count -ne 6) {
        throw 'Installed canonical semantic projection must register exactly six tools.'
    }

    $visionConfig = Get-Content -LiteralPath $visionConfigPath -Raw | ConvertFrom-Json
    if (
        [string]$visionConfig.profile -ne 'lfm25-vl-450m-f16' -or
        [string]$visionConfig.runtime.host -ne '127.0.0.1' -or
        [int]$visionConfig.runtime.port -ne 3068 -or
        [double]$visionConfig.memory.min_start_physical_gb -ne 1.35 -or
        [double]$visionConfig.memory.min_run_physical_gb -ne 0.5
    ) {
        throw 'Installed semantic vision runtime config drifted from the reviewed profile.'
    }

    $semantic = Get-Content -LiteralPath $semanticConfigPath -Raw | ConvertFrom-Json
    $servers = @($semantic.mcpServers.PSObject.Properties.Name)
    if ($servers.Count -ne 1 -or $servers[0] -ne 'semantic-projection') {
        throw 'Installed semantic profile must expose exactly one projection server.'
    }
    $server = $semantic.mcpServers.'semantic-projection'
    if ([string]$server.command -ne 'node') {
        throw 'Installed semantic profile must launch the projection directly with Node.'
    }
    if (@($server.args).Count -ne 1 -or [string]$server.args[0] -ne '${CHAT_SEMANTIC_PROJECTION_ENTRY}') {
        throw 'Installed semantic profile entrypoint contract drifted.'
    }
    if (@($server.tags) -notcontains 'procedure' -or @($server.tags) -notcontains 'control-plane') {
        throw 'Installed semantic profile must permanently expose bounded procedure/control-plane capability.'
    }
}

function Install-ChatManagerBundle {
    param(
        [Parameter(Mandatory)] [string]$RepoRoot,
        [Parameter(Mandatory)] [string]$AppRoot,
        [Parameter(Mandatory)] [string]$AppScriptsDir,
        [Parameter(Mandatory)] [string]$AppRuntimeDir,
        [Parameter(Mandatory)] [string]$AppConfigDir,
        [Parameter(Mandatory)] [string]$AppInstallMetadata,
        [Parameter(Mandatory)] [string]$CommandPath,
        [Parameter(Mandatory)] [string]$ControllerPath,
        [Parameter(Mandatory)] [string]$DirectControllerPath,
        [Parameter(Mandatory)] [string]$TrayPath
    )

    Stop-ChatInstalledManagerForBundleUpdate -CommandPath $CommandPath

    $scriptNames = @(
        'start-local-bridge.ps1',
        'status-local-bridge.ps1',
        'stop-local-bridge.ps1',
        'start-chat-profile.ps1',
        'start-semantic-profile.ps1',
        'semantic-projection-runtime.ps1',
        'status-chat-profile.ps1',
        'stop-chat-profile.ps1',
        'chat-platform-controller.ps1',
        'semantic-direct-controller.ps1',
        'chat-platform.ps1',
        'chat-platform-tray.ps1',
        'local-vision-runtime.ps1',
        'local-vision-runtime-watchdog.ps1',
        'verify-local-vision-listener.ps1',
        'production-visual-grounder.py'
    )
    foreach ($name in $scriptNames) {
        Copy-ChatVerifiedFile -Source (Join-Path $RepoRoot "scripts\$name") -Destination (Join-Path $AppScriptsDir $name)
    }

    $runtimeFiles = @(
        @('runtime\mcp.json', 'runtime\mcp.json'),
        @('runtime\chat-profiles\files-readonly\mcp.json', 'runtime\chat-profiles\files-readonly\mcp.json'),
        @('runtime\chat-profiles\browser-isolated\mcp.json', 'runtime\chat-profiles\browser-isolated\mcp.json'),
        @('runtime\chat-profiles\semantic\mcp.json', 'runtime\chat-profiles\semantic\mcp.json'),
        @('runtime\chat-profiles\adaptive\mcp.json', 'runtime\chat-profiles\adaptive\mcp.json'),
        @('runtime\semantic-projection\package.json', 'runtime\semantic-projection\package.json'),
        @('runtime\semantic-projection\package-lock.json', 'runtime\semantic-projection\package-lock.json'),
        @('runtime\semantic-projection\bin\semantic-projection-launcher.mjs', 'runtime\semantic-projection\bin\semantic-projection-launcher.mjs'),
        @('runtime\semantic-projection\bin\semantic-control-plane-projection.mjs', 'runtime\semantic-projection\bin\semantic-control-plane-projection.mjs'),
        @('runtime\semantic-projection\bin\semantic-projection.mjs', 'runtime\semantic-projection\bin\semantic-projection.mjs'),
        @('runtime\semantic-projection\lib\semantic-vision-click-router.mjs', 'runtime\semantic-projection\lib\semantic-vision-click-router.mjs'),
        @('runtime\semantic-projection\lib\visual-grounding-bridge.mjs', 'runtime\semantic-projection\lib\visual-grounding-bridge.mjs'),
        @('runtime\semantic-projection\lib\runtime-backed-bridge-grounder.mjs', 'runtime\semantic-projection\lib\runtime-backed-bridge-grounder.mjs'),
        @('runtime\semantic-projection\lib\runtime-backed-visual-grounder.mjs', 'runtime\semantic-projection\lib\runtime-backed-visual-grounder.mjs'),
        @('runtime\control_plane\__init__.py', 'runtime\control_plane\__init__.py'),
        @('runtime\control_plane\cli.py', 'runtime\control_plane\cli.py'),
        @('runtime\control_plane\verified_workspace_artifact.py', 'runtime\control_plane\verified_workspace_artifact.py'),
        @('config\local-vision-runtime.json', 'config\local-vision-runtime.json'),
        @('runtime\local_vision_adapter\__init__.py', 'runtime\local_vision_adapter\__init__.py'),
        @('runtime\local_vision_adapter\benchmark.py', 'runtime\local_vision_adapter\benchmark.py'),
        @('runtime\local_vision_adapter\mark_grid.py', 'runtime\local_vision_adapter\mark_grid.py'),
        @('runtime\local_vision_adapter\native_bbox.py', 'runtime\local_vision_adapter\native_bbox.py'),
        @('runtime\local_vision_adapter\production_grounder.py', 'runtime\local_vision_adapter\production_grounder.py'),
        @('runtime\local_vision_adapter\production_policy.py', 'runtime\local_vision_adapter\production_policy.py'),
        @('runtime\local_vision_adapter\provider.py', 'runtime\local_vision_adapter\provider.py'),
        @('runtime\local_vision_adapter\renderer.py', 'runtime\local_vision_adapter\renderer.py'),
        @('runtime\1mcp-adaptive-shim\package.json', 'runtime\1mcp-adaptive-shim\package.json'),
        @('runtime\1mcp-adaptive-shim\bin\1mcp-adaptive.mjs', 'runtime\1mcp-adaptive-shim\bin\1mcp-adaptive.mjs'),
        @('runtime\1mcp-adaptive-shim\scripts\apply-compatibility-patch.mjs', 'runtime\1mcp-adaptive-shim\scripts\apply-compatibility-patch.mjs')
    )

    foreach ($pair in $runtimeFiles) {
        $source = Join-Path $RepoRoot ([string]$pair[0])
        $destination = Join-Path $AppRoot ([string]$pair[1])
        Copy-ChatVerifiedFile -Source $source -Destination $destination
    }

    Assert-ChatInstalledAdaptiveRuntime -AppRuntimeDir $AppRuntimeDir
    Assert-ChatInstalledSixToolSemanticRuntime -AppRuntimeDir $AppRuntimeDir -AppScriptsDir $AppScriptsDir -AppConfigDir $AppConfigDir

    foreach ($installed in @($CommandPath, $ControllerPath, $DirectControllerPath, $TrayPath)) {
        if (-not (Test-Path -LiteralPath $installed -PathType Leaf)) {
            throw "Installed manager script is missing after bundle copy: $installed"
        }
    }

    [ordered]@{
        schema_version = 4
        app_root = $AppRoot
        source_root = $RepoRoot
        semantic_public_tool_count = 6
        installed_at = (Get-Date).ToUniversalTime().ToString('o')
        scripts = $scriptNames
        runtime_configs = @(
            'runtime/mcp.json',
            'runtime/chat-profiles/files-readonly/mcp.json',
            'runtime/chat-profiles/browser-isolated/mcp.json',
            'runtime/chat-profiles/semantic/mcp.json',
            'runtime/chat-profiles/adaptive/mcp.json',
            'config/local-vision-runtime.json'
        )
        runtime_assets = @($runtimeFiles | ForEach-Object { ([string]$_[0]).Replace('\', '/') })
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $AppInstallMetadata -Encoding utf8

    Write-Host "MANAGER_APP_ROOT=$AppRoot"
    Write-Host 'SEMANTIC_PUBLIC_TOOL_COUNT=6'
    Write-Host 'MANAGER_BUNDLE_VERIFIED=True' -ForegroundColor Green
}
