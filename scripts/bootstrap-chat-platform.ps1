[CmdletBinding()]
param(
    [string]$TunnelId,
    [switch]$ForceTunnelClientUpdate,
    [switch]$ReconfigureTunnelProfile,
    [switch]$SkipSmokeTest,
    [switch]$LaunchTray
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$SourceControllerPath = Join-Path $PSScriptRoot "chat-platform-controller.ps1"
$SourceDirectControllerPath = Join-Path $PSScriptRoot "semantic-direct-controller.ps1"
$SourceCommandPath = Join-Path $PSScriptRoot "chat-platform.ps1"
$SourceTrayPath = Join-Path $PSScriptRoot "chat-platform-tray.ps1"

$LocalRoot = Join-Path $env:LOCALAPPDATA "ChatAgentPlatform"
$AppRoot = Join-Path $LocalRoot "app"
$AppScriptsDir = Join-Path $AppRoot "scripts"
$AppRuntimeDir = Join-Path $AppRoot "runtime"
$BinDir = Join-Path $LocalRoot "bin"
$TunnelDir = Join-Path $LocalRoot "tunnel"
$StateDir = Join-Path $LocalRoot "state"
$TunnelExe = Join-Path $BinDir "tunnel-client.exe"
$TunnelProfile = Join-Path $TunnelDir "local-1mcp.yaml"
$InstallMetadata = Join-Path $StateDir "tunnel-client-install.json"
$AppInstallMetadata = Join-Path $StateDir "manager-install.json"
$CommandPath = Join-Path $AppScriptsDir "chat-platform.ps1"
$ControllerPath = Join-Path $AppScriptsDir "chat-platform-controller.ps1"
$DirectControllerPath = Join-Path $AppScriptsDir "semantic-direct-controller.ps1"
$TrayPath = Join-Path $AppScriptsDir "chat-platform-tray.ps1"

$McpUrl = "http://127.0.0.1:3050/mcp"
$AcceptedTunnelClientVersion = "v0.0.11"
$OfficialReleaseApi = "https://api.github.com/repos/openai/tunnel-client/releases/tags/$AcceptedTunnelClientVersion"
$AcceptedTunnelArchiveSha256 = @{
    amd64 = "eb912c86c6ccde90cda805cb17009507176a656725cf86c36fabe1901a12e29b"
    arm64 = "38f015a720404c8ccd5976a0d6aed18d931899697eaf208548b5eb3d0f6e8592"
}
$OneMcpPackage = "@1mcp/agent@0.34.4"

function Write-Step {
    param([Parameter(Mandatory)] [string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Require-Command {
    param([Parameter(Mandatory)] [string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        throw "Required command is missing: $Name"
    }
    return $command.Source
}

function Assert-WindowsEnvironment {
    if (-not $IsWindows) {
        throw "Chat Agent Platform bootstrap currently supports Windows only."
    }
    if ($PSVersionTable.PSEdition -ne "Core" -or $PSVersionTable.PSVersion.Major -lt 7) {
        throw "PowerShell 7 or newer is required."
    }
    if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        throw "LOCALAPPDATA is unavailable."
    }

    $null = Require-Command "pwsh.exe"
    $node = Require-Command "node.exe"
    $null = Require-Command "npm.cmd"
    $null = Require-Command "npx.cmd"

    $nodeVersion = (& $node --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $nodeVersion -notmatch '^v(?<major>[0-9]+)\.') {
        throw "Could not determine the installed Node.js version: $nodeVersion"
    }
    if ([int]$Matches.major -lt 20) {
        throw "Node.js 20 or newer is required; found $nodeVersion."
    }

    Write-Host "POWERSHELL=$($PSVersionTable.PSVersion)"
    Write-Host "NODE=$(& node.exe --version)"
    Write-Host "NPM=$(& npm.cmd --version)"

    $oneMcpHelp = @(& npx.cmd -y $OneMcpPackage --help 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "Pinned 1MCP dependency failed its startup preflight: $($oneMcpHelp -join ' ')"
    }
    Write-Host "ONE_MCP=$OneMcpPackage"

    foreach ($source in @(
        $SourceControllerPath,
        $SourceDirectControllerPath,
        $SourceCommandPath,
        $SourceTrayPath
    )) {
        if (-not (Test-Path -LiteralPath $source)) {
            throw "Manager source script is missing: $source"
        }
    }
}

function Get-TunnelArchitecture {
    $arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
    switch ($arch) {
        "x64" { return "amd64" }
        "arm64" { return "arm64" }
        default { throw "Unsupported Windows architecture for tunnel-client: $arch" }
    }
}

function Get-OfficialTunnelRelease {
    $headers = @{
        Accept = "application/vnd.github+json"
        "User-Agent" = "chat-agent-platform-bootstrap"
        "X-GitHub-Api-Version" = "2022-11-28"
    }
    $release = Invoke-RestMethod -Method Get -Uri $OfficialReleaseApi -Headers $headers -TimeoutSec 30

    if ([bool]$release.draft -or [bool]$release.prerelease) {
        throw "Accepted tunnel-client release is not a stable published release."
    }
    $tag = [string]$release.tag_name
    if ($tag -ne $AcceptedTunnelClientVersion) {
        throw "Expected tunnel-client $AcceptedTunnelClientVersion, got $tag."
    }

    $arch = Get-TunnelArchitecture
    $assetName = "tunnel-client-$tag-windows-$arch.zip"
    $asset = @($release.assets | Where-Object { [string]$_.name -eq $assetName })
    $sumAsset = @($release.assets | Where-Object { [string]$_.name -eq "SHA256SUMS.txt" })
    if ($asset.Count -ne 1) {
        throw "Official release $tag does not contain exactly one $assetName asset."
    }
    if ($sumAsset.Count -ne 1) {
        throw "Official release $tag does not contain SHA256SUMS.txt."
    }

    $expectedPrefix = "https://github.com/openai/tunnel-client/releases/download/$tag/"
    foreach ($url in @([string]$asset[0].browser_download_url, [string]$sumAsset[0].browser_download_url)) {
        if (-not $url.StartsWith($expectedPrefix, [System.StringComparison]::Ordinal)) {
            throw "Unexpected tunnel-client release asset URL: $url"
        }
    }

    return [pscustomobject]@{
        tag = $tag
        asset_name = $assetName
        asset_url = [string]$asset[0].browser_download_url
        asset_digest = [string]$asset[0].digest
        sums_url = [string]$sumAsset[0].browser_download_url
        release_url = [string]$release.html_url
    }
}

function Get-ExpectedChecksum {
    param(
        [Parameter(Mandatory)] [string]$SumsPath,
        [Parameter(Mandatory)] [string]$AssetName
    )

    $pattern = '^(?<hash>[0-9A-Fa-f]{64})\s+[*]?' + [regex]::Escape($AssetName) + '$'
    foreach ($line in Get-Content -LiteralPath $SumsPath) {
        $trimmed = $line.Trim()
        if ($trimmed -match $pattern) {
            return $Matches.hash.ToLowerInvariant()
        }
    }

    throw "SHA256SUMS.txt does not contain a checksum for $AssetName."
}

function Get-ExactTunnelProcesses {
    if (-not (Test-Path -LiteralPath $TunnelExe)) {
        return @()
    }

    $expected = [System.IO.Path]::GetFullPath($TunnelExe)
    return @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                if ($_.Name -ne "tunnel-client.exe") { return $false }
                $actual = [string]$_.ExecutablePath
                if ([string]::IsNullOrWhiteSpace($actual)) { return $false }
                try { $actual = [System.IO.Path]::GetFullPath($actual) } catch { return $false }
                return ($actual -ieq $expected)
            }
    )
}

function Install-OfficialTunnelClient {
    foreach ($path in @($LocalRoot, $BinDir, $TunnelDir, $StateDir)) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
    }

    $release = Get-OfficialTunnelRelease
    Write-Host "OFFICIAL_TUNNEL_RELEASE=$($release.tag)"
    Write-Host "OFFICIAL_RELEASE_URL=$($release.release_url)"

    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("chat-agent-platform-bootstrap-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

    try {
        $zipPath = Join-Path $tempRoot $release.asset_name
        $sumsPath = Join-Path $tempRoot "SHA256SUMS.txt"
        Invoke-WebRequest -Uri $release.sums_url -OutFile $sumsPath -TimeoutSec 60
        Invoke-WebRequest -Uri $release.asset_url -OutFile $zipPath -TimeoutSec 180

        $publishedChecksum = Get-ExpectedChecksum -SumsPath $sumsPath -AssetName $release.asset_name
        $arch = Get-TunnelArchitecture
        $expected = [string]$AcceptedTunnelArchiveSha256[$arch]
        if ([string]::IsNullOrWhiteSpace($expected)) {
            throw "No reviewed tunnel-client checksum is pinned for architecture $arch."
        }
        if ($publishedChecksum -ne $expected) {
            throw "Official SHA256SUMS.txt disagrees with the reviewed checksum pinned in this repository."
        }

        $actual = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $expected) {
            throw "Official tunnel-client ZIP checksum mismatch. Expected $expected, got $actual."
        }

        if (-not [string]::IsNullOrWhiteSpace($release.asset_digest)) {
            $apiDigest = $release.asset_digest.ToLowerInvariant()
            if ($apiDigest -notmatch '^sha256:[0-9a-f]{64}$') {
                throw "Unexpected GitHub asset digest format: $($release.asset_digest)"
            }
            if ($apiDigest -ne "sha256:$actual") {
                throw "GitHub release asset digest does not match the downloaded ZIP."
            }
        }

        $extractDir = Join-Path $tempRoot "extract"
        Expand-Archive -LiteralPath $zipPath -DestinationPath $extractDir -Force
        $candidates = @(Get-ChildItem -LiteralPath $extractDir -Filter "tunnel-client.exe" -File -Recurse)
        if ($candidates.Count -ne 1) {
            throw "Expected exactly one tunnel-client.exe in the official archive; found $($candidates.Count)."
        }

        $candidate = $candidates[0].FullName
        $help = @(& $candidate help quickstart 2>&1)
        if ($LASTEXITCODE -ne 0) {
            throw "Downloaded tunnel-client failed executable preflight: $($help -join ' ')"
        }

        $candidateHash = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant()
        $needsInstall = $true
        if (Test-Path -LiteralPath $TunnelExe) {
            $installedHash = (Get-FileHash -LiteralPath $TunnelExe -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($installedHash -eq $candidateHash -and -not $ForceTunnelClientUpdate) {
                $needsInstall = $false
            }
        }

        if ($needsInstall) {
            if (@(Get-ExactTunnelProcesses).Count -gt 0) {
                throw "The installed tunnel-client is running. Stop Chat Agent Platform before updating it."
            }

            $newPath = "$TunnelExe.new"
            Copy-Item -LiteralPath $candidate -Destination $newPath -Force
            $newHash = (Get-FileHash -LiteralPath $newPath -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($newHash -ne $candidateHash) {
                Remove-Item -LiteralPath $newPath -Force -ErrorAction SilentlyContinue
                throw "Tunnel binary copy verification failed."
            }
            Move-Item -LiteralPath $newPath -Destination $TunnelExe -Force
        }

        [ordered]@{
            schema_version = 1
            version = $release.tag
            archive_sha256 = $actual
            binary_sha256 = $candidateHash
            asset = $release.asset_name
            source = $release.asset_url
            release = $release.release_url
            verified_at = (Get-Date).ToUniversalTime().ToString("o")
        } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $InstallMetadata -Encoding utf8

        Write-Host "TUNNEL_BINARY=$TunnelExe"
        Write-Host "TUNNEL_ARCHIVE_SHA256=$actual"
        Write-Host "TUNNEL_BINARY_SHA256=$candidateHash"
        Write-Host "TUNNEL_BINARY_VERIFIED=True" -ForegroundColor Green
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Resolve-TunnelId {
    if (-not [string]::IsNullOrWhiteSpace($TunnelId)) {
        $candidate = $TunnelId.Trim()
    }
    elseif (Test-Path -LiteralPath $TunnelProfile) {
        $raw = Get-Content -LiteralPath $TunnelProfile -Raw
        $matches = @(
            [regex]::Matches($raw, 'tunnel_[0-9a-f]{32}') |
                ForEach-Object { $_.Value } |
                Select-Object -Unique
        )

        if ($matches.Count -eq 1) {
            $candidate = [string]$matches[0]
            Write-Host "TUNNEL_ID_SOURCE=existing-profile"
        }
        else {
            $candidate = (Read-Host "Вставь CONTROL_PLANE_TUNNEL_ID (tunnel_ + 32 hex символа)").Trim()
        }
    }
    else {
        $candidate = (Read-Host "Вставь CONTROL_PLANE_TUNNEL_ID (tunnel_ + 32 hex символа)").Trim()
    }

    if ($candidate -notmatch '^tunnel_[0-9a-f]{32}$') {
        throw "TunnelId has invalid format. Expected tunnel_ followed by 32 lowercase hexadecimal characters."
    }

    return $candidate
}

function Test-TunnelProfileContract {
    param(
        [Parameter(Mandatory)] [string]$Path,
        [Parameter(Mandatory)] [string]$ResolvedTunnelId
    )

    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $raw = Get-Content -LiteralPath $Path -Raw

    # Old project-managed profiles could pin log.file to a repository-relative
    # path such as runtime/openai-tunnel-client/local-1mcp.log. That silently
    # tied tunnel startup to whichever current working directory happened to
    # launch the manager. The current official remote-no-auth sample does not
    # need a profile-owned log file, so bootstrap repairs only relative log.file
    # entries by regenerating the profile through official `tunnel-client init`.
    $logBlock = [regex]::Match(
        $raw,
        '(?ms)^\s*log:\s*\r?\n(?<body>(?:[ \t]+[^\r\n]*(?:\r?\n|$))*)'
    )
    if ($logBlock.Success) {
        $logFileMatch = [regex]::Match(
            $logBlock.Groups['body'].Value,
            '(?m)^[ \t]+file:\s*(?<value>[^\r\n#]+)'
        )
        if ($logFileMatch.Success) {
            $logFile = $logFileMatch.Groups['value'].Value.Trim().Trim('"').Trim("'")
            if (-not [System.IO.Path]::IsPathRooted($logFile)) {
                return $false
            }
        }
    }

    return (
        $raw -match [regex]::Escape($ResolvedTunnelId) -and
        $raw -match [regex]::Escape($McpUrl) -and
        $raw -match 'CONTROL_PLANE_API_KEY'
    )
}

function Initialize-OfficialTunnelProfile {
    param([Parameter(Mandatory)] [string]$ResolvedTunnelId)

    New-Item -ItemType Directory -Force -Path $TunnelDir | Out-Null
    $profileValid = Test-TunnelProfileContract -Path $TunnelProfile -ResolvedTunnelId $ResolvedTunnelId

    if (
        -not $ReconfigureTunnelProfile -and
        $profileValid
    ) {
        Write-Host "TUNNEL_PROFILE=$TunnelProfile"
        Write-Host "TUNNEL_PROFILE_SOURCE=existing-validated"
        return
    }

    if ((Test-Path -LiteralPath $TunnelProfile) -and -not $profileValid) {
        Write-Host "TUNNEL_PROFILE_COMPATIBILITY=reconfigure-required"
    }

    if (Test-Path -LiteralPath $TunnelProfile) {
        $backup = "$TunnelProfile.bootstrap-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item -LiteralPath $TunnelProfile -Destination $backup -Force
        Write-Host "TUNNEL_PROFILE_BACKUP=$backup"
    }

    $args = @(
        "init",
        "--sample", "sample_mcp_remote_no_auth",
        "--profile", "local-1mcp",
        "--profile-dir", $TunnelDir,
        "--tunnel-id", $ResolvedTunnelId,
        "--mcp-server-url", $McpUrl,
        "--health-listen-addr", "127.0.0.1:0",
        "--force"
    )

    $output = @(& $TunnelExe @args 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw "Official tunnel-client init failed: $($output -join ' ')"
    }
    if (-not (Test-TunnelProfileContract -Path $TunnelProfile -ResolvedTunnelId $ResolvedTunnelId)) {
        throw "Official tunnel-client created a profile that does not satisfy the local bridge contract."
    }

    Write-Host "TUNNEL_PROFILE=$TunnelProfile"
    Write-Host "TUNNEL_PROFILE_SOURCE=official-tunnel-client-init"
}

function Copy-VerifiedManagerFile {
    param(
        [Parameter(Mandatory)] [string]$Source,
        [Parameter(Mandatory)] [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Manager source file is missing: $Source"
    }

    $parent = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Force -Path $parent | Out-Null

    $temporary = "$Destination.new"
    Copy-Item -LiteralPath $Source -Destination $temporary -Force

    $sourceHash = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
    $copyHash = (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash
    if ($sourceHash -ne $copyHash) {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
        throw "Manager file copy verification failed: $Source"
    }

    Move-Item -LiteralPath $temporary -Destination $Destination -Force
}

function Stop-InstalledManagerForBundleUpdate {
    if (-not (Test-Path -LiteralPath $CommandPath -PathType Leaf)) {
        return
    }

    $pwsh = Require-Command "pwsh.exe"
    & $pwsh `
        -NoLogo `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $CommandPath `
        -Action Stop `
        -NoNotify

    if ($LASTEXITCODE -ne 0) {
        throw "Could not stop the installed manager before updating its runtime bundle."
    }
}

function Assert-InstalledAdaptiveRuntime {
    $manifestPath = Join-Path $AppRuntimeDir "1mcp-adaptive-shim\package.json"
    $adaptiveConfigPath = Join-Path $AppRuntimeDir "chat-profiles\adaptive\mcp.json"

    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if (
        [string]$manifest.name -ne "@chat-agent-platform/1mcp-adaptive-shim" -or
        [string]$manifest.version -ne "0.1.0" -or
        [string]$manifest.bin.'1mcp-adaptive' -ne "bin/1mcp-adaptive.mjs" -or
        [string]$manifest.scripts.postinstall -ne "node scripts/apply-compatibility-patch.mjs" -or
        [string]$manifest.dependencies.'@1mcp/agent' -ne "0.35.0-beta.3" -or
        [string]$manifest.engines.node -ne ">=20"
    ) {
        throw "Installed adaptive compatibility manifest failed its pinned contract."
    }

    $expectedPackageFiles = @(
        "bin/1mcp-adaptive.mjs",
        "scripts/apply-compatibility-patch.mjs"
    )
    if (
        (@($manifest.files) -join "`n") -ne
        ($expectedPackageFiles -join "`n")
    ) {
        throw "Installed adaptive package file allowlist drifted."
    }

    $adaptive = Get-Content -LiteralPath $adaptiveConfigPath -Raw | ConvertFrom-Json
    foreach ($name in @("filesystem", "playwright")) {
        if ($null -eq $adaptive.mcpServers.$name -or -not [bool]$adaptive.mcpServers.$name.disabled) {
            throw "Installed adaptive backend '$name' must exist and start disabled."
        }
    }
    $adaptiveRaw = Get-Content -LiteralPath $adaptiveConfigPath -Raw
    foreach ($pin in @(
        "@modelcontextprotocol/server-filesystem@2026.7.10",
        "@playwright/mcp@0.0.78"
    )) {
        if ($adaptiveRaw -notmatch [regex]::Escape($pin)) {
            throw "Installed adaptive runtime is missing pin '$pin'."
        }
    }
}

function Assert-InstalledSemanticRuntimeSource {
    $manifestPath = Join-Path $AppRuntimeDir "semantic-projection\package.json"
    $lockPath = Join-Path $AppRuntimeDir "semantic-projection\package-lock.json"
    $launcherPath = Join-Path $AppRuntimeDir "semantic-projection\bin\semantic-projection-launcher.mjs"
    $entryPath = Join-Path $AppRuntimeDir "semantic-projection\bin\semantic-projection.mjs"
    $semanticConfigPath = Join-Path $AppRuntimeDir "chat-profiles\semantic\mcp.json"

    foreach ($required in @($manifestPath, $lockPath, $launcherPath, $entryPath, $semanticConfigPath)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "Installed semantic runtime asset is missing: $required"
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
        [string]$manifest.name -ne "@chat-agent-platform/semantic-projection" -or
        [string]$manifest.version -ne "0.1.0" -or
        [string]$manifest.bin.'chat-semantic-projection' -ne "bin/semantic-projection-launcher.mjs" -or
        [string]$manifest.engines.node -ne ">=20"
    ) {
        throw "Installed semantic projection manifest failed its pinned contract."
    }
    foreach ($name in $pins.Keys) {
        if ([string]$manifest.dependencies.$name -ne [string]$pins[$name]) {
            throw "Installed semantic dependency pin drifted: $name"
        }
    }

    $expectedPackageFiles = @(
        "bin/semantic-projection-launcher.mjs",
        "bin/semantic-projection.mjs"
    )
    if (
        (@($manifest.files) -join "`n") -ne
        ($expectedPackageFiles -join "`n")
    ) {
        throw "Installed semantic package file allowlist drifted."
    }

    $lock = Get-Content -LiteralPath $lockPath -Raw | ConvertFrom-Json -AsHashtable
    if ([int]$lock['lockfileVersion'] -ne 3) {
        throw "Installed semantic package-lock must use lockfileVersion 3."
    }
    $rootPackage = $lock['packages']['']
    foreach ($name in $pins.Keys) {
        if ([string]$rootPackage['dependencies'][$name] -ne [string]$pins[$name]) {
            throw "Installed semantic lockfile dependency pin drifted: $name"
        }
    }

    $launcherSource = Get-Content -LiteralPath $launcherPath -Raw
    $deleteIndex = $launcherSource.IndexOf("delete process.env[key]", [StringComparison]::Ordinal)
    $controlIndex = $launcherSource.IndexOf("'CONTROL_PLANE_API_KEY'", [StringComparison]::Ordinal)
    $openAiIndex = $launcherSource.IndexOf("'OPENAI_API_KEY'", [StringComparison]::Ordinal)
    $importIndex = $launcherSource.IndexOf("await import('./semantic-projection.mjs')", [StringComparison]::Ordinal)
    if (
        $deleteIndex -lt 0 -or
        $controlIndex -lt 0 -or
        $openAiIndex -lt 0 -or
        $importIndex -lt 0 -or
        $deleteIndex -gt $importIndex
    ) {
        throw "Installed semantic credential-scrub launcher failed its runtime contract."
    }

    $semantic = Get-Content -LiteralPath $semanticConfigPath -Raw | ConvertFrom-Json
    $servers = @($semantic.mcpServers.PSObject.Properties.Name)
    if ($servers.Count -ne 1 -or $servers[0] -ne 'semantic-projection') {
        throw "Installed semantic profile must expose exactly one projection server."
    }
    $server = $semantic.mcpServers.'semantic-projection'
    if ([string]$server.command -ne 'node') {
        throw "Installed semantic profile must launch the projection directly with Node."
    }
    if (@($server.args).Count -ne 1 -or [string]$server.args[0] -ne '${CHAT_SEMANTIC_PROJECTION_ENTRY}') {
        throw "Installed semantic profile entrypoint contract drifted."
    }
}

function Install-ManagerBundle {
    # The adaptive catalog is mutable while running. Stop the installed
    # manager before replacing the reviewed all-disabled catalog baseline.
    Stop-InstalledManagerForBundleUpdate

    $scriptNames = @(
        "start-local-bridge.ps1",
        "status-local-bridge.ps1",
        "stop-local-bridge.ps1",
        "start-chat-profile.ps1",
        "start-semantic-profile.ps1",
        "semantic-projection-runtime.ps1",
        "status-chat-profile.ps1",
        "stop-chat-profile.ps1",
        "chat-platform-controller.ps1",
        "semantic-direct-controller.ps1",
        "chat-platform.ps1",
        "chat-platform-tray.ps1"
    )

    foreach ($name in $scriptNames) {
        Copy-VerifiedManagerFile `
            -Source (Join-Path $RepoRoot "scripts\$name") `
            -Destination (Join-Path $AppScriptsDir $name)
    }

    $runtimeFiles = @(
        @{
            Source = Join-Path $RepoRoot "runtime\mcp.json"
            Destination = Join-Path $AppRuntimeDir "mcp.json"
        },
        @{
            Source = Join-Path $RepoRoot "runtime\chat-profiles\files-readonly\mcp.json"
            Destination = Join-Path $AppRuntimeDir "chat-profiles\files-readonly\mcp.json"
        },
        @{
            Source = Join-Path $RepoRoot "runtime\chat-profiles\browser-isolated\mcp.json"
            Destination = Join-Path $AppRuntimeDir "chat-profiles\browser-isolated\mcp.json"
        },
        @{
            Source = Join-Path $RepoRoot "runtime\chat-profiles\semantic\mcp.json"
            Destination = Join-Path $AppRuntimeDir "chat-profiles\semantic\mcp.json"
        },
        @{
            Source = Join-Path $RepoRoot "runtime\chat-profiles\adaptive\mcp.json"
            Destination = Join-Path $AppRuntimeDir "chat-profiles\adaptive\mcp.json"
        },
        @{
            Source = Join-Path $RepoRoot "runtime\semantic-projection\package.json"
            Destination = Join-Path $AppRuntimeDir "semantic-projection\package.json"
        },
        @{
            Source = Join-Path $RepoRoot "runtime\semantic-projection\package-lock.json"
            Destination = Join-Path $AppRuntimeDir "semantic-projection\package-lock.json"
        },
        @{
            Source = Join-Path $RepoRoot "runtime\semantic-projection\bin\semantic-projection-launcher.mjs"
            Destination = Join-Path $AppRuntimeDir "semantic-projection\bin\semantic-projection-launcher.mjs"
        },
        @{
            Source = Join-Path $RepoRoot "runtime\semantic-projection\bin\semantic-projection.mjs"
            Destination = Join-Path $AppRuntimeDir "semantic-projection\bin\semantic-projection.mjs"
        },
        @{
            Source = Join-Path $RepoRoot "runtime\1mcp-adaptive-shim\package.json"
            Destination = Join-Path $AppRuntimeDir "1mcp-adaptive-shim\package.json"
        },
        @{
            Source = Join-Path $RepoRoot "runtime\1mcp-adaptive-shim\bin\1mcp-adaptive.mjs"
            Destination = Join-Path $AppRuntimeDir "1mcp-adaptive-shim\bin\1mcp-adaptive.mjs"
        },
        @{
            Source = Join-Path $RepoRoot "runtime\1mcp-adaptive-shim\scripts\apply-compatibility-patch.mjs"
            Destination = Join-Path $AppRuntimeDir "1mcp-adaptive-shim\scripts\apply-compatibility-patch.mjs"
        }
    )

    foreach ($entry in $runtimeFiles) {
        Copy-VerifiedManagerFile `
            -Source ([string]$entry.Source) `
            -Destination ([string]$entry.Destination)
    }

    Assert-InstalledAdaptiveRuntime
    Assert-InstalledSemanticRuntimeSource

    foreach ($installed in @($CommandPath, $ControllerPath, $DirectControllerPath, $TrayPath)) {
        if (-not (Test-Path -LiteralPath $installed)) {
            throw "Installed manager script is missing after bundle copy: $installed"
        }
    }

    [ordered]@{
        schema_version = 3
        app_root = $AppRoot
        source_root = $RepoRoot
        installed_at = (Get-Date).ToUniversalTime().ToString("o")
        scripts = $scriptNames
        runtime_configs = @(
            "runtime/mcp.json",
            "runtime/chat-profiles/files-readonly/mcp.json",
            "runtime/chat-profiles/browser-isolated/mcp.json",
            "runtime/chat-profiles/semantic/mcp.json",
            "runtime/chat-profiles/adaptive/mcp.json"
        )
        runtime_assets = @(
            "runtime/semantic-projection/package.json",
            "runtime/semantic-projection/package-lock.json",
            "runtime/semantic-projection/bin/semantic-projection-launcher.mjs",
            "runtime/semantic-projection/bin/semantic-projection.mjs",
            "runtime/1mcp-adaptive-shim/package.json",
            "runtime/1mcp-adaptive-shim/bin/1mcp-adaptive.mjs",
            "runtime/1mcp-adaptive-shim/scripts/apply-compatibility-patch.mjs"
        )
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $AppInstallMetadata -Encoding utf8

    Write-Host "MANAGER_APP_ROOT=$AppRoot"
    Write-Host "MANAGER_BUNDLE_VERIFIED=True" -ForegroundColor Green
}

function Invoke-ManagerStatusCapture {
    $pwsh = Require-Command "pwsh.exe"
    $output = @(
        & $pwsh `
            -NoLogo `
            -NoProfile `
            -ExecutionPolicy Bypass `
            -File $CommandPath `
            -Action Status `
            -NoNotify `
            2>&1
    )

    return [pscustomobject]@{
        exit_code = $LASTEXITCODE
        output = $output
    }
}

function Invoke-ManagerAction {
    param(
        [Parameter(Mandatory)]
        [ValidateSet("Start", "Stop")]
        [string]$Action,

        [ValidateSet("reference", "files-readonly", "browser-isolated", "semantic", "semantic-direct", "adaptive")]
        [string]$Profile
    )

    $pwsh = Require-Command "pwsh.exe"
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pwsh
    $startInfo.UseShellExecute = $false

    foreach ($argument in @(
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $CommandPath,
        "-Action", $Action,
        "-NoNotify"
    )) {
        $startInfo.ArgumentList.Add([string]$argument)
    }

    if (-not [string]::IsNullOrWhiteSpace($Profile)) {
        $startInfo.ArgumentList.Add("-Profile")
        $startInfo.ArgumentList.Add($Profile)
    }

    # Mutating manager actions can create persistent descendants. Waiting on
    # an exact Process handle avoids PowerShell pipeline EOF being held open by
    # inherited handles from 1MCP or tunnel-client.
    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo

    try {
        if (-not $process.Start()) {
            throw "Failed to start manager action $Action."
        }
        $process.WaitForExit()
        return $process.ExitCode
    }
    finally {
        $process.Dispose()
    }
}

function Install-Manager {
    # Install may ask for CONTROL_PLANE_API_KEY through Read-Host. Keep the
    # child process attached to the console instead of capturing its output so
    # the hidden interactive prompt is always visible to the user.
    $pwsh = Require-Command "pwsh.exe"
    & $pwsh `
        -NoLogo `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $CommandPath `
        -Action Install `
        -NoNotify

    if ($LASTEXITCODE -ne 0) {
        throw "Manager installation failed with exit code $LASTEXITCODE."
    }
}

function Invoke-SmokeTest {
    Write-Host "Starting reference MCP + Secure MCP Tunnel for bootstrap smoke test..." -ForegroundColor Yellow

    $startSucceeded = $false
    try {
        $startExit = Invoke-ManagerAction -Action Start -Profile reference
        if ($startExit -ne 0) {
            throw "Manager start failed during bootstrap smoke test with exit code $startExit."
        }
        $startSucceeded = $true

        $statusResult = Invoke-ManagerStatusCapture
        if ($statusResult.exit_code -ne 0) {
            throw "Manager status failed during bootstrap smoke test: $($statusResult.output -join ' ')"
        }

        $status = $statusResult.output | Out-String | ConvertFrom-Json
        if ([string]$status.active_profile -ne "reference") {
            throw "Bootstrap smoke test started unexpected profile '$($status.active_profile)' instead of reference."
        }
        if (-not [bool]$status.mcp_ready) {
            throw "Bootstrap smoke test: reference MCP is not ready."
        }
        if (-not [bool]$status.tunnel_ready) {
            throw "Bootstrap smoke test: Secure MCP Tunnel is not ready."
        }
        if ([int]$status.active_count -ne 1) {
            throw "Bootstrap smoke test: expected exactly one active MCP profile."
        }

        Write-Host "BOOTSTRAP_SMOKE_PROFILE=reference"
        Write-Host "BOOTSTRAP_SMOKE_TEST=passed" -ForegroundColor Green
    }
    finally {
        if ($startSucceeded) {
            $stopExit = Invoke-ManagerAction -Action Stop
            if ($stopExit -ne 0) {
                Write-Warning "Bootstrap cleanup stop returned exit code $stopExit."
            }
        }
        else {
            # Start performs its own rollback, but a best-effort Stop also
            # clears any pre-existing partial state from an interrupted setup.
            try {
                $null = Invoke-ManagerAction -Action Stop
            }
            catch {
                Write-Warning "Bootstrap cleanup could not invoke Stop: $($_.Exception.Message)"
            }
        }
    }
}

Write-Step "Проверка Windows и зависимостей"
Assert-WindowsEnvironment

Write-Step "Получение и проверка официального OpenAI tunnel-client"
Install-OfficialTunnelClient

Write-Step "Настройка официального tunnel-профиля"
$resolvedTunnelId = Resolve-TunnelId
Initialize-OfficialTunnelProfile -ResolvedTunnelId $resolvedTunnelId

Write-Step "Установка независимой локальной копии manager"
Install-ManagerBundle

Write-Step "Установка manager и защищённого runtime key"
Install-Manager

if (-not $SkipSmokeTest) {
    Write-Step "Проверка полного локального lifecycle"
    Invoke-SmokeTest
}

if ($LaunchTray) {
    Start-Process -FilePath (Require-Command "pwsh.exe") -ArgumentList @(
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-WindowStyle", "Hidden",
        "-File", $TrayPath
    ) | Out-Null
}

Write-Host "`nCHAT_PLATFORM_BOOTSTRAP=OK" -ForegroundColor Green
Write-Host "LOCAL_ROOT=$LocalRoot"
Write-Host "APP_ROOT=$AppRoot"
Write-Host "DEFAULT_MCP_URL=$McpUrl"
Write-Host "PLATFORM_STATE=stopped"
Write-Host "NEXT=Use the desktop shortcut or the installed chat-platform.ps1 command facade."
