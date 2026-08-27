Set-StrictMode -Version Latest

function Install-ChatWindowsProcedureBundle {
    param(
        [Parameter(Mandatory)] [string]$RepoRoot,
        [Parameter(Mandatory)] [string]$AppRoot,
        [Parameter(Mandatory)] [string]$StateDir
    )

    $assets = @(
        @('runtime\control_plane\windows_observation.py', 'runtime\control_plane\windows_observation.py'),
        @('runtime\control_plane\windows_transition.py', 'runtime\control_plane\windows_transition.py'),
        @('runtime\control_plane\windows_case_update.py', 'runtime\control_plane\windows_case_update.py'),
        @('runtime\windows\__init__.py', 'runtime\windows\__init__.py'),
        @('runtime\windows\actuation.py', 'runtime\windows\actuation.py'),
        @('runtime\windows\observation.py', 'runtime\windows\observation.py'),
        @('runtime\windows\verifier.py', 'runtime\windows\verifier.py'),
        @('runtime\windows\window_scoped_uia.py', 'runtime\windows\window_scoped_uia.py'),
        @('config\stage26-openadapt-lock.json', 'config\stage26-openadapt-lock.json')
    )

    foreach ($pair in $assets) {
        $source = Join-Path $RepoRoot ([string]$pair[0])
        $destination = Join-Path $AppRoot ([string]$pair[1])
        Copy-ChatVerifiedFile -Source $source -Destination $destination

        $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
        $installedHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($sourceHash -ne $installedHash) {
            throw "Installed Windows procedure asset hash mismatch: $($pair[0])"
        }
    }

    $lockPath = Join-Path $AppRoot 'config\stage26-openadapt-lock.json'
    $lock = Get-Content -LiteralPath $lockPath -Raw -Encoding utf8 | ConvertFrom-Json
    if (
        [int]$lock.schema_version -ne 1 -or
        [string]$lock.python.required_major_minor -ne '3.12' -or
        [string]$lock.upstreams.openadapt_flow.declared_version -ne '1.31.0' -or
        [string]$lock.upstreams.openadapt_flow.commit -notmatch '^[0-9a-f]{40}$'
    ) {
        throw 'Installed Windows procedure OpenAdapt lock failed its exact contract.'
    }

    $metadata = [ordered]@{
        schema_version = 1
        procedure_id = 'windows_case_update_v1'
        source_root = $RepoRoot
        installed_at = (Get-Date).ToUniversalTime().ToString('o')
        openadapt_flow_version = [string]$lock.upstreams.openadapt_flow.declared_version
        assets = @($assets | ForEach-Object { ([string]$_[0]).Replace('\', '/') })
    }
    $metadataPath = Join-Path $StateDir 'windows-procedure-install.json'
    $metadata | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $metadataPath -Encoding utf8

    Write-Host 'WINDOWS_PROCEDURE_ID=windows_case_update_v1'
    Write-Host 'WINDOWS_PROCEDURE_RUNTIME_INSTALLED=True'
    Write-Host "WINDOWS_PROCEDURE_INSTALL_METADATA=$metadataPath"
}
