Set-StrictMode -Version Latest

function Get-ChatTunnelArchitecture {
    $arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
    switch ($arch) {
        'x64' { return 'amd64' }
        'arm64' { return 'arm64' }
        default { throw "Unsupported Windows architecture for tunnel-client: $arch" }
    }
}

function Get-ChatOfficialTunnelRelease {
    param(
        [Parameter(Mandatory)] [string]$AcceptedVersion,
        [Parameter(Mandatory)] [string]$ReleaseApi
    )

    $headers = @{
        Accept = 'application/vnd.github+json'
        'User-Agent' = 'chat-agent-platform-bootstrap'
        'X-GitHub-Api-Version' = '2022-11-28'
    }
    $release = Invoke-RestMethod -Method Get -Uri $ReleaseApi -Headers $headers -TimeoutSec 30

    if ([bool]$release.draft -or [bool]$release.prerelease) {
        throw 'Accepted tunnel-client release is not a stable published release.'
    }
    $tag = [string]$release.tag_name
    if ($tag -ne $AcceptedVersion) {
        throw "Expected tunnel-client $AcceptedVersion, got $tag."
    }

    $arch = Get-ChatTunnelArchitecture
    $assetName = "tunnel-client-$tag-windows-$arch.zip"
    $asset = @($release.assets | Where-Object { [string]$_.name -eq $assetName })
    $sumAsset = @($release.assets | Where-Object { [string]$_.name -eq 'SHA256SUMS.txt' })
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

function Get-ChatExpectedChecksum {
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

function Get-ChatExactTunnelProcesses {
    param([Parameter(Mandatory)] [string]$TunnelExe)

    if (-not (Test-Path -LiteralPath $TunnelExe -PathType Leaf)) {
        return @()
    }

    $expected = [System.IO.Path]::GetFullPath($TunnelExe)
    return @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                if ($_.Name -ne 'tunnel-client.exe') { return $false }
                $actual = [string]$_.ExecutablePath
                if ([string]::IsNullOrWhiteSpace($actual)) { return $false }
                try { $actual = [System.IO.Path]::GetFullPath($actual) } catch { return $false }
                return ($actual -ieq $expected)
            }
    )
}

function Test-ChatVerifiedInstalledTunnelClient {
    param(
        [Parameter(Mandatory)] [string]$TunnelExe,
        [Parameter(Mandatory)] [string]$InstallMetadata,
        [Parameter(Mandatory)] [string]$AcceptedVersion,
        [Parameter(Mandatory)] [hashtable]$AcceptedArchiveSha256
    )

    if (
        -not (Test-Path -LiteralPath $TunnelExe -PathType Leaf) -or
        -not (Test-Path -LiteralPath $InstallMetadata -PathType Leaf)
    ) {
        return $false
    }

    try {
        $metadata = Get-Content -LiteralPath $InstallMetadata -Raw | ConvertFrom-Json
        $arch = Get-ChatTunnelArchitecture
        $expectedArchive = [string]$AcceptedArchiveSha256[$arch]
        $expectedAsset = "tunnel-client-$AcceptedVersion-windows-$arch.zip"

        if ([string]::IsNullOrWhiteSpace($expectedArchive)) { return $false }
        if ([int]$metadata.schema_version -ne 1) { return $false }
        if ([string]$metadata.version -ne $AcceptedVersion) { return $false }
        if ([string]$metadata.asset -ne $expectedAsset) { return $false }
        if ([string]$metadata.archive_sha256 -ne $expectedArchive) { return $false }

        $recordedBinaryHash = ([string]$metadata.binary_sha256).ToLowerInvariant()
        if ($recordedBinaryHash -notmatch '^[0-9a-f]{64}$') { return $false }
        $actualBinaryHash = (Get-FileHash -LiteralPath $TunnelExe -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualBinaryHash -ne $recordedBinaryHash) { return $false }

        $help = @(& $TunnelExe help quickstart 2>&1)
        if ($LASTEXITCODE -ne 0) { return $false }

        Write-Host 'TUNNEL_BINARY_SOURCE=verified-local-install'
        Write-Host "OFFICIAL_TUNNEL_RELEASE=$AcceptedVersion"
        Write-Host "TUNNEL_ARCHIVE_SHA256=$expectedArchive"
        Write-Host "TUNNEL_BINARY_SHA256=$actualBinaryHash"
        Write-Host 'TUNNEL_BINARY_VERIFIED=True' -ForegroundColor Green
        return $true
    }
    catch {
        return $false
    }
}

function Install-ChatOfficialTunnelClient {
    param(
        [Parameter(Mandatory)] [string]$LocalRoot,
        [Parameter(Mandatory)] [string]$BinDir,
        [Parameter(Mandatory)] [string]$TunnelDir,
        [Parameter(Mandatory)] [string]$StateDir,
        [Parameter(Mandatory)] [string]$TunnelExe,
        [Parameter(Mandatory)] [string]$InstallMetadata,
        [Parameter(Mandatory)] [string]$AcceptedVersion,
        [Parameter(Mandatory)] [string]$ReleaseApi,
        [Parameter(Mandatory)] [hashtable]$AcceptedArchiveSha256,
        [switch]$ForceUpdate
    )

    foreach ($path in @($LocalRoot, $BinDir, $TunnelDir, $StateDir)) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
    }

    if (
        -not $ForceUpdate -and
        (Test-ChatVerifiedInstalledTunnelClient `
            -TunnelExe $TunnelExe `
            -InstallMetadata $InstallMetadata `
            -AcceptedVersion $AcceptedVersion `
            -AcceptedArchiveSha256 $AcceptedArchiveSha256)
    ) {
        Write-Host 'TUNNEL_NETWORK_FETCH_REQUIRED=False'
        return
    }

    Write-Host 'TUNNEL_NETWORK_FETCH_REQUIRED=True'
    $release = Get-ChatOfficialTunnelRelease -AcceptedVersion $AcceptedVersion -ReleaseApi $ReleaseApi
    Write-Host "OFFICIAL_TUNNEL_RELEASE=$($release.tag)"
    Write-Host "OFFICIAL_RELEASE_URL=$($release.release_url)"

    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("chat-agent-platform-bootstrap-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

    try {
        $zipPath = Join-Path $tempRoot $release.asset_name
        $sumsPath = Join-Path $tempRoot 'SHA256SUMS.txt'
        Invoke-WebRequest -Uri $release.sums_url -OutFile $sumsPath -TimeoutSec 60
        Invoke-WebRequest -Uri $release.asset_url -OutFile $zipPath -TimeoutSec 180

        $publishedChecksum = Get-ChatExpectedChecksum -SumsPath $sumsPath -AssetName $release.asset_name
        $arch = Get-ChatTunnelArchitecture
        $expected = [string]$AcceptedArchiveSha256[$arch]
        if ([string]::IsNullOrWhiteSpace($expected)) {
            throw "No reviewed tunnel-client checksum is pinned for architecture $arch."
        }
        if ($publishedChecksum -ne $expected) {
            throw 'Official SHA256SUMS.txt disagrees with the reviewed checksum pinned in this repository.'
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
                throw 'GitHub release asset digest does not match the downloaded ZIP.'
            }
        }

        $extractDir = Join-Path $tempRoot 'extract'
        Expand-Archive -LiteralPath $zipPath -DestinationPath $extractDir -Force
        $candidates = @(Get-ChildItem -LiteralPath $extractDir -Filter 'tunnel-client.exe' -File -Recurse)
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
        if (Test-Path -LiteralPath $TunnelExe -PathType Leaf) {
            $installedHash = (Get-FileHash -LiteralPath $TunnelExe -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($installedHash -eq $candidateHash -and -not $ForceUpdate) {
                $needsInstall = $false
            }
        }

        if ($needsInstall) {
            if (@(Get-ChatExactTunnelProcesses -TunnelExe $TunnelExe).Count -gt 0) {
                throw 'The installed tunnel-client is running. Stop Chat Agent Platform before updating it.'
            }
            $newPath = "$TunnelExe.new"
            Copy-Item -LiteralPath $candidate -Destination $newPath -Force
            $newHash = (Get-FileHash -LiteralPath $newPath -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($newHash -ne $candidateHash) {
                Remove-Item -LiteralPath $newPath -Force -ErrorAction SilentlyContinue
                throw 'Tunnel binary copy verification failed.'
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
            verified_at = (Get-Date).ToUniversalTime().ToString('o')
        } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $InstallMetadata -Encoding utf8

        Write-Host "TUNNEL_BINARY=$TunnelExe"
        Write-Host "TUNNEL_ARCHIVE_SHA256=$actual"
        Write-Host "TUNNEL_BINARY_SHA256=$candidateHash"
        Write-Host 'TUNNEL_BINARY_VERIFIED=True' -ForegroundColor Green
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Read-ChatTunnelState {
    param([Parameter(Mandatory)] [string]$TunnelStateFile)

    if (-not (Test-Path -LiteralPath $TunnelStateFile -PathType Leaf)) {
        return $null
    }

    try {
        $state = Get-Content -LiteralPath $TunnelStateFile -Raw | ConvertFrom-Json
    }
    catch {
        throw "Persistent tunnel state is invalid JSON: $($_.Exception.Message)"
    }

    if (
        $null -eq $state.PSObject.Properties['tunnel_id'] -or
        [string]$state.tunnel_id -notmatch '^tunnel_[0-9a-f]{32}$'
    ) {
        throw 'Persistent tunnel state does not contain a valid tunnel_id.'
    }

    return $state
}

function Save-ChatTunnelState {
    param(
        [Parameter(Mandatory)] [string]$TunnelStateFile,
        [Parameter(Mandatory)] [string]$TunnelId,
        [Parameter(Mandatory)] [ValidateSet('explicit', 'existing-state', 'legacy-profile-migration')]
        [string]$Source
    )

    if ($TunnelId -notmatch '^tunnel_[0-9a-f]{32}$') {
        throw 'TunnelId has invalid format. Expected tunnel_ followed by 32 lowercase hexadecimal characters.'
    }

    $parent = Split-Path -Parent $TunnelStateFile
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $temporary = "$TunnelStateFile.new"
    [ordered]@{
        schema_version = 1
        tunnel_id = $TunnelId
        source = $Source
        updated_at = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $temporary -Encoding utf8
    Move-Item -LiteralPath $temporary -Destination $TunnelStateFile -Force
}

function Get-ChatTunnelIdFromLegacyProfile {
    param([string]$LegacyTunnelProfile)

    if (
        [string]::IsNullOrWhiteSpace($LegacyTunnelProfile) -or
        -not (Test-Path -LiteralPath $LegacyTunnelProfile -PathType Leaf)
    ) {
        return $null
    }

    $raw = Get-Content -LiteralPath $LegacyTunnelProfile -Raw
    $matches = @(
        [regex]::Matches($raw, 'tunnel_[0-9a-f]{32}') |
            ForEach-Object { $_.Value } |
            Select-Object -Unique
    )
    if ($matches.Count -eq 1) {
        return [string]$matches[0]
    }
    if ($matches.Count -gt 1) {
        throw 'Legacy tunnel profile contains more than one tunnel id; refusing ambiguous migration.'
    }
    return $null
}

function Resolve-ChatTunnelId {
    param(
        [string]$RequestedTunnelId,
        [Parameter(Mandatory)] [string]$TunnelStateFile,
        [string]$LegacyTunnelProfile
    )

    if (-not [string]::IsNullOrWhiteSpace($RequestedTunnelId)) {
        $candidate = $RequestedTunnelId.Trim()
        if ($candidate -notmatch '^tunnel_[0-9a-f]{32}$') {
            throw 'TunnelId has invalid format. Expected tunnel_ followed by 32 lowercase hexadecimal characters.'
        }
        Save-ChatTunnelState -TunnelStateFile $TunnelStateFile -TunnelId $candidate -Source explicit
        Write-Host 'TUNNEL_ID_SOURCE=explicit'
        return $candidate
    }

    $state = Read-ChatTunnelState -TunnelStateFile $TunnelStateFile
    if ($null -ne $state) {
        $candidate = [string]$state.tunnel_id
        Write-Host 'TUNNEL_ID_SOURCE=state/tunnel.json'
        return $candidate
    }

    $legacy = Get-ChatTunnelIdFromLegacyProfile -LegacyTunnelProfile $LegacyTunnelProfile
    if (-not [string]::IsNullOrWhiteSpace($legacy)) {
        Save-ChatTunnelState -TunnelStateFile $TunnelStateFile -TunnelId $legacy -Source legacy-profile-migration
        Write-Host 'TUNNEL_ID_SOURCE=legacy-profile-migration'
        return $legacy
    }

    $candidate = (Read-Host 'Вставь CONTROL_PLANE_TUNNEL_ID (tunnel_ + 32 hex символа)').Trim()
    if ($candidate -notmatch '^tunnel_[0-9a-f]{32}$') {
        throw 'TunnelId has invalid format. Expected tunnel_ followed by 32 lowercase hexadecimal characters.'
    }
    Save-ChatTunnelState -TunnelStateFile $TunnelStateFile -TunnelId $candidate -Source explicit
    Write-Host 'TUNNEL_ID_SOURCE=interactive-explicit'
    return $candidate
}

# Optional compatibility helper for the internal 1MCP Extension Manager path.
# The normal six-tool semantic bootstrap does not call this function.
function Test-ChatTunnelProfileContract {
    param(
        [Parameter(Mandatory)] [string]$Path,
        [Parameter(Mandatory)] [string]$ResolvedTunnelId,
        [Parameter(Mandatory)] [string]$McpUrl
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    $raw = Get-Content -LiteralPath $Path -Raw

    $logBlock = [regex]::Match($raw, '(?ms)^\s*log:\s*\r?\n(?<body>(?:[ \t]+[^\r\n]*(?:\r?\n|$))*)')
    if ($logBlock.Success) {
        $logFileMatch = [regex]::Match($logBlock.Groups['body'].Value, '(?m)^[ \t]+file:\s*(?<value>[^\r\n#]+)')
        if ($logFileMatch.Success) {
            $logFile = $logFileMatch.Groups['value'].Value.Trim().Trim('"').Trim("'")
            if (-not [System.IO.Path]::IsPathRooted($logFile)) { return $false }
        }
    }

    $expectedApiKey = '${CONTROL_PLANE_API_KEY}'
    if ($raw -notmatch [regex]::Escape("tunnel-id: $ResolvedTunnelId")) { return $false }
    if ($raw -notmatch [regex]::Escape("api-key: $expectedApiKey")) { return $false }
    if ($raw -notmatch [regex]::Escape("mcp-server-url: $McpUrl")) { return $false }
    return $true
}

function Initialize-ChatExtensionManagerTunnelProfile {
    param(
        [Parameter(Mandatory)] [string]$TunnelExe,
        [Parameter(Mandatory)] [string]$TunnelDir,
        [Parameter(Mandatory)] [string]$ProfileName,
        [Parameter(Mandatory)] [string]$TunnelId,
        [Parameter(Mandatory)] [string]$McpUrl
    )

    $profilePath = Join-Path $TunnelDir "$ProfileName.yaml"
    if (Test-ChatTunnelProfileContract -Path $profilePath -ResolvedTunnelId $TunnelId -McpUrl $McpUrl) {
        Write-Host 'EXTENSION_TUNNEL_PROFILE_SOURCE=existing-valid'
        return $profilePath
    }

    if (@(Get-ChatExactTunnelProcesses -TunnelExe $TunnelExe).Count -gt 0) {
        throw 'Cannot replace an invalid Extension Manager tunnel profile while tunnel-client is running.'
    }

    if (Test-Path -LiteralPath $profilePath -PathType Leaf) {
        $backup = "$profilePath.bak-$(Get-Date -Format yyyyMMddHHmmss)"
        Move-Item -LiteralPath $profilePath -Destination $backup -Force
        Write-Host "EXTENSION_TUNNEL_PROFILE_BACKUP=$backup"
    }

    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("chat-agent-platform-extension-profile-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
    try {
        $template = Join-Path $tempRoot "$ProfileName.yaml"
        & $TunnelExe init sample_mcp_remote_no_auth --profile-dir $tempRoot --non-interactive --force *> $null
        if ($LASTEXITCODE -ne 0) {
            throw 'tunnel-client init failed while creating Extension Manager profile.'
        }
        if (-not (Test-Path -LiteralPath $template -PathType Leaf)) {
            throw "tunnel-client init did not create expected template: $template"
        }
        $raw = Get-Content -LiteralPath $template -Raw
        $raw = [regex]::Replace($raw, '(?m)^\s*tunnel-id:\s*.*$', "tunnel-id: $TunnelId")
        $raw = [regex]::Replace($raw, '(?m)^\s*api-key:\s*.*$', "api-key: `${CONTROL_PLANE_API_KEY}")
        $raw = [regex]::Replace($raw, '(?m)^\s*mcp-server-url:\s*.*$', "mcp-server-url: $McpUrl")
        $raw = [regex]::Replace($raw, '(?m)^\s*log-level:\s*.*$', 'log-level: info')
        $raw = [regex]::Replace($raw, '(?m)^\s*format:\s*.*$', '  format: text')
        $logPath = Join-Path $TunnelDir "$ProfileName.log"
        $raw = [regex]::Replace($raw, '(?m)^\s*file:\s*.*$', "  file: $logPath")
        $raw | Set-Content -LiteralPath $profilePath -Encoding utf8
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }

    if (-not (Test-ChatTunnelProfileContract -Path $profilePath -ResolvedTunnelId $TunnelId -McpUrl $McpUrl)) {
        throw 'Generated Extension Manager tunnel profile failed validation.'
    }

    Write-Host 'EXTENSION_TUNNEL_PROFILE_SOURCE=generated'
    return $profilePath
}
