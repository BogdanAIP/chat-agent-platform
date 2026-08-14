Set-StrictMode -Version Latest

function Get-SemanticProjectionPackagePath {
    param(
        [Parameter(Mandatory)]
        [string]$RepoRoot,

        [switch]$Ensure
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
    if (
        [string]$manifest.name -ne '@chat-agent-platform/semantic-projection' -or
        [string]$manifest.version -ne '0.1.0' -or
        [string]$manifest.bin.'chat-semantic-projection' -ne 'bin/semantic-projection.mjs' -or
        [string]$manifest.dependencies.'@modelcontextprotocol/client' -ne '2.0.0' -or
        [string]$manifest.dependencies.'@modelcontextprotocol/server' -ne '2.0.0' -or
        [string]$manifest.dependencies.zod -ne '4.4.3' -or
        [string]$manifest.engines.node -ne '>=20'
    ) {
        throw 'Semantic projection manifest failed its pinned runtime contract.'
    }

    $packageFiles = @($manifest.files | ForEach-Object { [string]$_ })
    if (
        $packageFiles.Count -ne 1 -or
        $packageFiles[0] -ne 'bin/semantic-projection.mjs'
    ) {
        throw 'Semantic projection package file allowlist drifted.'
    }

    $fingerprintParts = foreach ($relative in @(
        'package.json',
        'bin\semantic-projection.mjs'
    )) {
        $source = Join-Path $projectionRoot $relative
        $hash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
        "$relative`0$hash"
    }

    $fingerprintBytes = [System.Text.Encoding]::UTF8.GetBytes(
        ($fingerprintParts -join "`n")
    )
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
        $fingerprintHash = $sha256.ComputeHash($fingerprintBytes)
    }
    finally {
        $sha256.Dispose()
    }

    $fingerprint = (
        ($fingerprintHash | ForEach-Object { $_.ToString('x2') }) -join ''
    ).Substring(0, 16)

    $cacheDir = Join-Path (
        [System.IO.Path]::GetTempPath()
    ) "chat-agent-platform\semantic-projection\$fingerprint"
    $packagePath = Join-Path $cacheDir 'semantic-projection-0.1.0.tgz'

    if (-not $Ensure) {
        return $packagePath
    }

    if (Test-Path -LiteralPath $packagePath -PathType Leaf) {
        return $packagePath
    }

    New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
    $npmName = if ($IsWindows) { 'npm.cmd' } else { 'npm' }
    $npm = (Get-Command $npmName -ErrorAction Stop).Source
    $stagingDir = Join-Path $cacheDir ('.pack-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $stagingDir | Out-Null

    try {
        $packOutput = @(
            & $npm pack $projectionRoot --pack-destination $stagingDir --silent 2>&1
        )
        if ($LASTEXITCODE -ne 0) {
            throw "Could not prepare semantic projection package.`n$($packOutput -join "`n")"
        }

        $packedNames = @(
            $packOutput |
                ForEach-Object { ([string]$_).Trim() } |
                Where-Object { $_ -like '*.tgz' }
        )
        if ($packedNames.Count -ne 1) {
            throw "npm pack returned an unexpected semantic package result: $($packOutput -join ' ')"
        }

        $stagedPackage = Join-Path $stagingDir (Split-Path -Leaf $packedNames[0])
        if (-not (Test-Path -LiteralPath $stagedPackage -PathType Leaf)) {
            throw "Packed semantic projection archive is missing: $stagedPackage"
        }

        try {
            [System.IO.File]::Move($stagedPackage, $packagePath)
        }
        catch {
            # Another concurrent launcher may have populated the same
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

    return $packagePath
}
