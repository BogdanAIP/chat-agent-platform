Set-StrictMode -Version Latest

function Get-SemanticProjectionEntryPath {
    param(
        [Parameter(Mandatory)]
        [string]$RepoRoot,

        [switch]$EnsureDependencies
    )

    $projectionRoot = Join-Path $RepoRoot 'runtime\semantic-projection'
    $manifestPath = Join-Path $projectionRoot 'package.json'
    $lockPath = Join-Path $projectionRoot 'package-lock.json'
    $corePath = Join-Path $projectionRoot 'bin\semantic-projection.mjs'
    $controlPlaneProjectionPath = Join-Path $projectionRoot 'bin\semantic-control-plane-projection.mjs'
    $launcherPath = Join-Path $projectionRoot 'bin\semantic-projection-launcher.mjs'
    $controlPlaneCliPath = Join-Path $RepoRoot 'runtime\control_plane\cli.py'
    $controlPlaneProcedurePath = Join-Path $RepoRoot 'runtime\control_plane\verified_workspace_artifact.py'
    $lockMarkerPath = Join-Path $projectionRoot 'node_modules\.chat-agent-platform-lock.sha256'

    foreach ($required in @(
        $manifestPath,
        $corePath,
        $controlPlaneProjectionPath,
        $controlPlaneCliPath,
        $controlPlaneProcedurePath
    )) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "Semantic six-tool runtime source is missing: $required"
        }
    }

    if (-not (Test-Path -LiteralPath $launcherPath -PathType Leaf)) {
        throw "Reviewed semantic launcher is missing: $launcherPath"
    }

    $launcherSource = Get-Content -LiteralPath $launcherPath -Raw
    $controlDelete = $launcherSource.IndexOf("delete process.env[key]", [StringComparison]::Ordinal)
    $controlName = $launcherSource.IndexOf("'CONTROL_PLANE_API_KEY'", [StringComparison]::Ordinal)
    $openAiName = $launcherSource.IndexOf("'OPENAI_API_KEY'", [StringComparison]::Ordinal)
    $openAiAdminName = $launcherSource.IndexOf("'OPENAI_ADMIN_KEY'", [StringComparison]::Ordinal)
    $semanticEntryMarker = $launcherSource.IndexOf("path.join(launcherDir, 'semantic-control-plane-projection.mjs')", [StringComparison]::Ordinal)
    $childSpawn = $launcherSource.IndexOf("spawn(process.execPath, [semanticEntry]", [StringComparison]::Ordinal)
    $legacyAliases = @(
        'semantic-projection_1mcp_workspace_read',
        'semantic-projection_1mcp_workspace_write',
        'semantic-projection_1mcp_web_open',
        'semantic-projection_1mcp_web_observe',
        'semantic-projection_1mcp_web_interact',
        'semantic-projection_1mcp_procedure_run'
    )
    $legacyAliasContractOk = $true
    foreach ($legacyAlias in $legacyAliases) {
        if ($launcherSource.IndexOf("'$legacyAlias'", [StringComparison]::Ordinal) -lt 0) {
            $legacyAliasContractOk = $false
            break
        }
    }
    if (
        $controlDelete -lt 0 -or
        $controlName -lt 0 -or
        $openAiName -lt 0 -or
        $openAiAdminName -lt 0 -or
        $semanticEntryMarker -lt 0 -or
        $childSpawn -lt 0 -or
        -not $legacyAliasContractOk -or
        $controlDelete -gt $childSpawn -or
        $semanticEntryMarker -gt $childSpawn
    ) {
        throw 'Semantic six-tool credential-scrub compatibility launcher failed its runtime contract.'
    }

    $controlPlaneSource = Get-Content -LiteralPath $controlPlaneProjectionPath -Raw
    $publicTools = @(
        'workspace_read',
        'workspace_write',
        'web_open',
        'web_observe',
        'web_interact',
        'procedure_run'
    )
    foreach ($toolName in $publicTools) {
        if ($controlPlaneSource.IndexOf("server.registerTool('$toolName'", [StringComparison]::Ordinal) -lt 0) {
            throw "Canonical semantic six-tool projection is missing '$toolName'."
        }
    }
    if ([regex]::Matches($controlPlaneSource, 'server\.registerTool\(').Count -ne 6) {
        throw 'Canonical semantic projection must register exactly six public tools.'
    }

    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $expectedDependencies = [ordered]@{
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
        throw 'Semantic projection manifest failed its runtime contract.'
    }

    foreach ($dependencyName in $expectedDependencies.Keys) {
        if ([string]$manifest.dependencies.$dependencyName -ne [string]$expectedDependencies[$dependencyName]) {
            throw "Semantic projection dependency pin drifted: $dependencyName"
        }
    }

    $packageFiles = @($manifest.files | ForEach-Object { [string]$_ })
    $expectedFiles = @(
        'bin/semantic-projection-launcher.mjs',
        'bin/semantic-control-plane-projection.mjs',
        'bin/semantic-projection.mjs',
        'lib/semantic-vision-click-router.mjs',
        'lib/visual-grounding-bridge.mjs',
        'lib/runtime-backed-bridge-grounder.mjs',
        'lib/runtime-backed-visual-grounder.mjs'
    )
    if (
        $packageFiles.Count -ne $expectedFiles.Count -or
        (($packageFiles | Sort-Object) -join "`n") -ne (($expectedFiles | Sort-Object) -join "`n")
    ) {
        throw 'Semantic projection package file allowlist drifted.'
    }

    foreach ($relativeSource in $expectedFiles) {
        $sourcePath = Join-Path $projectionRoot ($relativeSource -replace '/', '\')
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
            throw "Semantic projection reviewed source file is missing: $sourcePath"
        }
    }

    $lockSha256 = $null
    if (Test-Path -LiteralPath $lockPath -PathType Leaf) {
        $lock = Get-Content -LiteralPath $lockPath -Raw | ConvertFrom-Json -AsHashtable
        if ([int]$lock['lockfileVersion'] -ne 3) {
            throw 'Semantic projection package-lock must use lockfileVersion 3.'
        }
        $rootPackage = $lock['packages']['']
        foreach ($dependencyName in $expectedDependencies.Keys) {
            if ([string]$rootPackage['dependencies'][$dependencyName] -ne [string]$expectedDependencies[$dependencyName]) {
                throw "Semantic projection lockfile root dependency drifted: $dependencyName"
            }
        }
        $lockSha256 = (Get-FileHash -LiteralPath $lockPath -Algorithm SHA256).Hash.ToLowerInvariant()
    }

    if (-not $EnsureDependencies) {
        return [System.IO.Path]::GetFullPath($launcherPath)
    }

    $nodeName = if ($IsWindows) { 'node.exe' } else { 'node' }
    $npmName = if ($IsWindows) { 'npm.cmd' } else { 'npm' }
    $null = Get-Command $nodeName -ErrorAction Stop
    $null = Get-Command 'python' -ErrorAction Stop
    $npm = (Get-Command $npmName -ErrorAction Stop).Source

    function Test-DependenciesReady {
        foreach ($dependencyName in $expectedDependencies.Keys) {
            $dependencyManifest = Join-Path `
                $projectionRoot `
                ('node_modules\' + ($dependencyName -replace '/', '\') + '\package.json')

            if (-not (Test-Path -LiteralPath $dependencyManifest -PathType Leaf)) {
                return $false
            }

            try {
                $installed = Get-Content -LiteralPath $dependencyManifest -Raw | ConvertFrom-Json
            }
            catch {
                return $false
            }

            if ([string]$installed.version -ne [string]$expectedDependencies[$dependencyName]) {
                return $false
            }
        }

        if ($null -ne $lockSha256) {
            if (-not (Test-Path -LiteralPath $lockMarkerPath -PathType Leaf)) {
                return $false
            }
            try {
                $appliedLockSha256 = (Get-Content -LiteralPath $lockMarkerPath -Raw -Encoding utf8).Trim().ToLowerInvariant()
            }
            catch {
                return $false
            }
            if ($appliedLockSha256 -ne $lockSha256) {
                return $false
            }
        }

        return $true
    }

    if (-not (Test-DependenciesReady)) {
        if (-not (Test-Path -LiteralPath $lockPath -PathType Leaf)) {
            throw 'Semantic projection dependencies are absent and package-lock.json is missing; refusing unlocked installation.'
        }

        Push-Location $projectionRoot
        try {
            $installOutput = @(
                & $npm ci `
                    --ignore-scripts `
                    --no-audit `
                    --no-fund `
                    2>&1
            )

            if ($LASTEXITCODE -ne 0) {
                throw "Could not install locked semantic projection dependencies with npm ci.`n$($installOutput -join "`n")"
            }
        }
        finally {
            Pop-Location
        }

        Set-Content -LiteralPath $lockMarkerPath -Value $lockSha256 -Encoding utf8 -NoNewline
    }

    if (-not (Test-DependenciesReady)) {
        throw 'Semantic projection dependencies failed exact-version and lock-hash verification after install.'
    }

    return [System.IO.Path]::GetFullPath($launcherPath)
}
