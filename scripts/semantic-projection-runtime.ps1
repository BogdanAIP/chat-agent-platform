Set-StrictMode -Version Latest

function Get-SemanticProjectionEntryPath {
    param(
        [Parameter(Mandatory)]
        [string]$RepoRoot,

        [switch]$EnsureDependencies
    )

    $projectionRoot = Join-Path $RepoRoot 'runtime\semantic-projection'
    $manifestPath = Join-Path $projectionRoot 'package.json'
    $entryPath = Join-Path $projectionRoot 'bin\semantic-projection.mjs'

    foreach ($required in @($manifestPath, $entryPath)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "Semantic projection source is missing: $required"
        }
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
        [string]$manifest.bin.'chat-semantic-projection' -ne 'bin/semantic-projection.mjs' -or
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
    if ($packageFiles.Count -ne 1 -or $packageFiles[0] -ne 'bin/semantic-projection.mjs') {
        throw 'Semantic projection package file allowlist drifted.'
    }

    if (-not $EnsureDependencies) {
        return [System.IO.Path]::GetFullPath($entryPath)
    }

    $nodeName = if ($IsWindows) { 'node.exe' } else { 'node' }
    $npmName = if ($IsWindows) { 'npm.cmd' } else { 'npm' }
    $null = Get-Command $nodeName -ErrorAction Stop
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

        return $true
    }

    if (-not (Test-DependenciesReady)) {
        Push-Location $projectionRoot
        try {
            $installOutput = @(
                & $npm install `
                    --ignore-scripts `
                    --no-audit `
                    --no-fund `
                    --package-lock=false `
                    2>&1
            )

            if ($LASTEXITCODE -ne 0) {
                throw "Could not install semantic projection dependencies.`n$($installOutput -join "`n")"
            }
        }
        finally {
            Pop-Location
        }
    }

    if (-not (Test-DependenciesReady)) {
        throw 'Semantic projection dependencies failed exact-version verification after install.'
    }

    return [System.IO.Path]::GetFullPath($entryPath)
}
