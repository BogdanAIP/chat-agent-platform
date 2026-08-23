Set-StrictMode -Version Latest

function Get-ChatPlatformDesiredStatePath {
    if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        throw 'LOCALAPPDATA is unavailable.'
    }
    return (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\state\desired-state.json')
}

function Write-ChatPlatformDesiredState {
    param(
        [Parameter(Mandatory)]
        [ValidateSet('running', 'stopped')]
        [string]$DesiredState,

        [ValidateSet('user_action', 'legacy_migration', 'qualification')]
        [string]$Source = 'user_action'
    )

    $path = Get-ChatPlatformDesiredStatePath
    $parent = Split-Path -Parent $path
    New-Item -ItemType Directory -Force -Path $parent | Out-Null

    $payload = [ordered]@{
        schema_version = 1
        desired_state = $DesiredState
        source = $Source
        updated_at = (Get-Date).ToUniversalTime().ToString('o')
    }

    $temporary = "$path.new-$PID"
    try {
        $payload | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $temporary -Encoding utf8
        Move-Item -LiteralPath $temporary -Destination $path -Force
    }
    finally {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
    }

    return [pscustomobject]$payload
}

function Read-ChatPlatformDesiredState {
    param(
        [string]$LegacyOwnerFile,
        [switch]$MigrateLegacyOwner
    )

    $path = Get-ChatPlatformDesiredStatePath
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
            if (
                $null -eq $state.PSObject.Properties['desired_state'] -or
                [string]$state.desired_state -notin @('running', 'stopped')
            ) {
                throw 'desired_state missing or unsupported'
            }
            return [pscustomobject]@{
                desired_state = [string]$state.desired_state
                source = if ($null -ne $state.PSObject.Properties['source']) { [string]$state.source } else { 'unknown' }
                updated_at = if ($null -ne $state.PSObject.Properties['updated_at']) { [string]$state.updated_at } else { $null }
                path = $path
                migrated = $false
            }
        }
        catch {
            throw 'desired-state.json is invalid.'
        }
    }

    if ($MigrateLegacyOwner) {
        if ([string]::IsNullOrWhiteSpace($LegacyOwnerFile)) {
            throw 'LegacyOwnerFile is required for desired-state migration.'
        }
        $legacyDesired = if (Test-Path -LiteralPath $LegacyOwnerFile -PathType Leaf) { 'running' } else { 'stopped' }
        $saved = Write-ChatPlatformDesiredState -DesiredState $legacyDesired -Source 'legacy_migration'
        return [pscustomobject]@{
            desired_state = [string]$saved.desired_state
            source = [string]$saved.source
            updated_at = [string]$saved.updated_at
            path = $path
            migrated = $true
        }
    }

    return $null
}
