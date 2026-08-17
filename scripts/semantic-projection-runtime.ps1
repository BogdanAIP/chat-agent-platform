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
    $launcherPath = Join-Path $projectionRoot 'bin\semantic-projection-launcher.mjs'

    foreach ($required in @($manifestPath, $corePath)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "Semantic projection source is missing: $required"
        }
    }

    # Standalone installed-layout tests historically copied only the core entry.
    # Recreate the reviewed launcher if that old copy list omitted it. Normal
    # source/bootstrap layouts already contain the checked-in launcher.
    if (-not (Test-Path -LiteralPath $launcherPath -PathType Leaf)) {
        $launcherTemplate = @'
#!/usr/bin/env node

const tunnelOnlyCredentialKeys = [
  'CONTROL_PLANE_API_KEY',
  'OPENAI_API_KEY'
];

for (const key of tunnelOnlyCredentialKeys) {
  delete process.env[key];
}

if (process.argv.includes('--verify-credential-scrub')) {
  for (const key of tunnelOnlyCredentialKeys) {
    if (Object.prototype.hasOwnProperty.call(process.env, key)) {
      console.error(`semantic launcher failed to scrub ${key}`);
      process.exit(1);
    }
  }
  console.log('SEMANTIC_TUNNEL_CREDENTIAL_SCRUB=PASS');
  process.exit(0);
}

await import('./semantic-projection.mjs');
'@
        Set-Content -LiteralPath $launcherPath -Value $launcherTemplate -Encoding utf8 -NoNewline
    }

    $launcherSource = Get-Content -LiteralPath $launcherPath -Raw
    $controlDelete = $launcherSource.IndexOf("delete process.env[key]", [StringComparison]::Ordinal)
    $controlName = $launcherSource.IndexOf("'CONTROL_PLANE_API_KEY'", [StringComparison]::Ordinal)
    $openAiName = $launcherSource.IndexOf("'OPENAI_API_KEY'", [StringComparison]::Ordinal)
    $coreImport = $launcherSource.IndexOf("await import('./semantic-projection.mjs')", [StringComparison]::Ordinal)
    if (
        $controlDelete -lt 0 -or
        $controlName -lt 0 -or
        $openAiName -lt 0 -or
        $coreImport -lt 0 -or
        $controlDelete -gt $coreImport
    ) {
        throw 'Semantic projection credential-scrub launcher failed its runtime contract.'
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
    $expectedFiles = @('bin/semantic-projection-launcher.mjs', 'bin/semantic-projection.mjs')
    if (
        $packageFiles.Count -ne $expectedFiles.Count -or
        (($packageFiles | Sort-Object) -join "`n") -ne (($expectedFiles | Sort-Object) -join "`n")
    ) {
        throw 'Semantic projection package file allowlist drifted.'
    }

    if (Test-Path -LiteralPath $lockPath -PathType Leaf) {
        $lock = Get-Content -LiteralPath $lockPath -Raw | ConvertFrom-Json
        if ([int]$lock.lockfileVersion -ne 3) {
            throw 'Semantic projection package-lock must use lockfileVersion 3.'
        }
        $rootPackage = $lock.packages.''
        foreach ($dependencyName in $expectedDependencies.Keys) {
            if ([string]$rootPackage.dependencies.$dependencyName -ne [string]$expectedDependencies[$dependencyName]) {
                throw "Semantic projection lockfile root dependency drifted: $dependencyName"
            }
        }
    }

    if (-not $EnsureDependencies) {
        return [System.IO.Path]::GetFullPath($launcherPath)
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
    }

    if (-not (Test-DependenciesReady)) {
        throw 'Semantic projection dependencies failed exact-version verification after install.'
    }

    return [System.IO.Path]::GetFullPath($launcherPath)
}
