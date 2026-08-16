[CmdletBinding()]
param(
    [ValidateSet('Start', 'Stop', 'Toggle', 'Status')]
    [string]$Action = 'Status',

    [ValidateSet('semantic', 'semantic-direct')]
    [string]$Profile,

    [string]$FilesRoot,

    [switch]$NoNotify
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$LocalRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
$AppRoot = Join-Path $LocalRoot 'app'
$AppScriptsDir = Join-Path $AppRoot 'scripts'
$StateDir = Join-Path $LocalRoot 'state'
$LogDir = Join-Path $LocalRoot 'logs'
$BinDir = Join-Path $LocalRoot 'bin'
$TunnelDir = Join-Path $LocalRoot 'tunnel'

$SemanticRuntimeHelper = Join-Path $AppScriptsDir 'semantic-projection-runtime.ps1'
$TunnelExe = Join-Path $BinDir 'tunnel-client.exe'
$BaselineTunnelProfile = Join-Path $TunnelDir 'local-1mcp.yaml'
$SecretFile = Join-Path $LocalRoot 'secrets\control-plane-api-key.dpapi'
$MainSettingsFile = Join-Path $StateDir 'settings.json'
$DirectStateFile = Join-Path $StateDir 'semantic-direct.json'
$HealthUrlFile = Join-Path $StateDir 'semantic-direct-health.url'
$StdoutLog = Join-Path $LogDir 'semantic-direct-tunnel-stdout.log'
$StderrLog = Join-Path $LogDir 'semantic-direct-tunnel-stderr.log'
$McpPort = 3050

function Initialize-Directories {
    foreach ($path in @($StateDir, $LogDir)) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
    }
}

function Get-EffectiveProfileName {
    if (-not [string]::IsNullOrWhiteSpace($Profile)) {
        return [string]$Profile
    }

    if (Test-Path -LiteralPath $MainSettingsFile -PathType Leaf) {
        try {
            $settings = Get-Content -LiteralPath $MainSettingsFile -Raw | ConvertFrom-Json
            if (
                $null -ne $settings.PSObject.Properties['profile'] -and
                [string]$settings.profile -in @('semantic', 'semantic-direct')
            ) {
                return [string]$settings.profile
            }
        }
        catch {
            # Keep the controller independently inspectable even if shared
            # settings are temporarily unavailable or malformed.
        }
    }

    # `semantic-direct` remains a compatibility/diagnostic alias for the
    # Stage 24.1 implementation. The public manager promotes `semantic` by
    # passing or persisting that profile explicitly.
    return 'semantic-direct'
}

function Get-ConfiguredFilesRoot {
    if (-not [string]::IsNullOrWhiteSpace($FilesRoot)) {
        if (-not (Test-Path -LiteralPath $FilesRoot -PathType Container)) {
            throw "FilesRoot must be an existing directory: $FilesRoot"
        }
        return (Resolve-Path -LiteralPath $FilesRoot).Path
    }

    if (Test-Path -LiteralPath $DirectStateFile -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $DirectStateFile -Raw | ConvertFrom-Json
            if (
                $null -ne $state.PSObject.Properties['files_root'] -and
                -not [string]::IsNullOrWhiteSpace([string]$state.files_root) -and
                (Test-Path -LiteralPath ([string]$state.files_root) -PathType Container)
            ) {
                return (Resolve-Path -LiteralPath ([string]$state.files_root)).Path
            }
        }
        catch {
            # Fall through to shared settings.
        }
    }

    if (Test-Path -LiteralPath $MainSettingsFile -PathType Leaf) {
        $settings = Get-Content -LiteralPath $MainSettingsFile -Raw | ConvertFrom-Json
        if (
            $null -ne $settings.PSObject.Properties['files_root'] -and
            -not [string]::IsNullOrWhiteSpace([string]$settings.files_root) -and
            (Test-Path -LiteralPath ([string]$settings.files_root) -PathType Container)
        ) {
            return (Resolve-Path -LiteralPath ([string]$settings.files_root)).Path
        }
    }

    throw 'Direct semantic transport requires FilesRoot. Configure the semantic profile first.'
}

function Resolve-TunnelId {
    if (-not (Test-Path -LiteralPath $BaselineTunnelProfile -PathType Leaf)) {
        throw "Accepted tunnel profile is missing: $BaselineTunnelProfile"
    }

    $raw = Get-Content -LiteralPath $BaselineTunnelProfile -Raw
    $matches = @(
        [regex]::Matches($raw, 'tunnel_[0-9a-f]{32}') |
            ForEach-Object { $_.Value } |
            Select-Object -Unique
    )

    if ($matches.Count -ne 1) {
        throw 'Could not resolve exactly one tunnel id from the accepted local-1mcp profile.'
    }

    return [string]$matches[0]
}

function Get-DecryptedApiKey {
    if (-not (Test-Path -LiteralPath $SecretFile -PathType Leaf)) {
        throw "Accepted DPAPI tunnel key is missing: $SecretFile"
    }

    $encoded = (Get-Content -LiteralPath $SecretFile -Raw).Trim()
    $protectedBytes = [Convert]::FromBase64String($encoded)

    try {
        $plainBytes = [Security.Cryptography.ProtectedData]::Unprotect(
            $protectedBytes,
            $null,
            [Security.Cryptography.DataProtectionScope]::CurrentUser
        )

        try {
            return [Text.Encoding]::UTF8.GetString($plainBytes)
        }
        finally {
            [Array]::Clear($plainBytes, 0, $plainBytes.Length)
        }
    }
    finally {
        [Array]::Clear($protectedBytes, 0, $protectedBytes.Length)
    }
}

function ConvertTo-McpCommandPart {
    param([Parameter(Mandatory)] [string]$Value)

    if ($Value -match '^[A-Za-z0-9_/:=.,@%+-]+$') {
        return $Value
    }
    if ($Value.Contains("'")) {
        throw "Direct semantic MCP command path contains an unsupported apostrophe: $Value"
    }
    return "'$Value'"
}

function Quote-ProcessArgument {
    param([Parameter(Mandatory)] [string]$Value)

    if ($Value.Contains('"')) {
        throw "Direct semantic process argument contains an unsupported double quote: $Value"
    }
    if ($Value -notmatch '\s') {
        return $Value
    }
    return '"' + $Value + '"'
}

function Get-SemanticEntry {
    if (-not (Test-Path -LiteralPath $SemanticRuntimeHelper -PathType Leaf)) {
        throw "Installed semantic runtime helper is missing: $SemanticRuntimeHelper"
    }

    . $SemanticRuntimeHelper
    return Get-SemanticProjectionEntryPath -RepoRoot $AppRoot -EnsureDependencies
}

function Get-PortListeners {
    if ($null -eq (Get-Command 'Get-NetTCPConnection' -ErrorAction SilentlyContinue)) {
        return @()
    }

    return @(
        Get-NetTCPConnection -LocalPort $McpPort -State Listen -ErrorAction SilentlyContinue
    )
}

function Get-DirectTunnelProcesses {
    if (-not (Test-Path -LiteralPath $TunnelExe -PathType Leaf)) {
        return @()
    }

    $expectedExe = [System.IO.Path]::GetFullPath($TunnelExe)
    $healthPattern = [regex]::Escape($HealthUrlFile)

    return @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                if ($_.Name -ne 'tunnel-client.exe') {
                    return $false
                }

                $actualExe = [string]$_.ExecutablePath
                $commandLine = [string]$_.CommandLine
                if (
                    [string]::IsNullOrWhiteSpace($actualExe) -or
                    [string]::IsNullOrWhiteSpace($commandLine)
                ) {
                    return $false
                }

                try {
                    $actualExe = [System.IO.Path]::GetFullPath($actualExe)
                }
                catch {
                    return $false
                }

                return (
                    $actualExe -ieq $expectedExe -and
                    $commandLine -match '(?i)--mcp\.command' -and
                    $commandLine -match $healthPattern
                )
            }
    )
}

function Get-HealthBaseUrl {
    if (-not (Test-Path -LiteralPath $HealthUrlFile -PathType Leaf)) {
        return $null
    }

    try {
        $url = (Get-Content -LiteralPath $HealthUrlFile -Raw).Trim().TrimEnd('/')
        if ($url -notmatch '^https?://127\.0\.0\.1(?::\d+)?$') {
            return $null
        }
        return $url
    }
    catch {
        return $null
    }
}

function Test-DirectReady {
    if (@(Get-DirectTunnelProcesses).Count -ne 1) {
        return $false
    }

    $base = Get-HealthBaseUrl
    if ([string]::IsNullOrWhiteSpace($base)) {
        return $false
    }

    try {
        $response = Invoke-WebRequest -Uri "$base/readyz" -Method Get -TimeoutSec 2 -ErrorAction Stop
        return ($response.StatusCode -eq 200)
    }
    catch {
        return $false
    }
}

function Save-DirectState {
    param(
        [Parameter(Mandatory)] [int]$ProcessId,
        [Parameter(Mandatory)] [string]$Root,
        [Parameter(Mandatory)] [string]$TunnelId,
        [Parameter(Mandatory)] [string]$SemanticEntry
    )

    [ordered]@{
        schema_version = 3
        pid = $ProcessId
        profile = Get-EffectiveProfileName
        files_root = $Root
        tunnel_id = $TunnelId
        semantic_entry = $SemanticEntry
        owner = 'chat-platform-manager'
        started_at = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $DirectStateFile -Encoding utf8
}

function Stop-DirectRuntime {
    foreach ($process in @(Get-DirectTunnelProcesses)) {
        Stop-Process -Id ([int]$process.ProcessId) -Force -ErrorAction SilentlyContinue
    }

    for ($i = 0; $i -lt 30; $i++) {
        if (@(Get-DirectTunnelProcesses).Count -eq 0) {
            break
        }
        Start-Sleep -Milliseconds 200
    }

    if (Test-Path -LiteralPath $DirectStateFile -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $DirectStateFile -Raw | ConvertFrom-Json
            if (
                $null -ne $state.PSObject.Properties['semantic_entry'] -and
                -not [string]::IsNullOrWhiteSpace([string]$state.semantic_entry)
            ) {
                $entryPattern = [regex]::Escape([string]$state.semantic_entry)
                Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
                    Where-Object {
                        $_.Name -eq 'node.exe' -and
                        [string]$_.CommandLine -match $entryPattern
                    } |
                    ForEach-Object {
                        Stop-Process -Id ([int]$_.ProcessId) -Force -ErrorAction SilentlyContinue
                    }
            }
        }
        catch {
            # Tunnel parent ownership is authoritative; child cleanup is best effort.
        }
    }

    Remove-Item -LiteralPath $HealthUrlFile -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $DirectStateFile -Force -ErrorAction SilentlyContinue
}

function Start-DirectRuntime {
    Initialize-Directories
    $profileName = Get-EffectiveProfileName

    if (Test-DirectReady) {
        Write-Host 'SEMANTIC_DIRECT_STATUS=ready'
        Write-Host 'SEMANTIC_DIRECT_1MCP_USED=False'
        Write-Host "SEMANTIC_PROFILE=$profileName"
        return
    }

    if (
        @(Get-DirectTunnelProcesses).Count -gt 0 -or
        (Test-Path -LiteralPath $DirectStateFile -PathType Leaf) -or
        (Test-Path -LiteralPath $HealthUrlFile -PathType Leaf)
    ) {
        Stop-DirectRuntime
    }

    $listeners = @(Get-PortListeners)
    if ($listeners.Count -gt 0) {
        throw "Local MCP port $McpPort is occupied. Refusing direct semantic startup until the 1MCP-backed runtime is stopped."
    }

    if (-not (Test-Path -LiteralPath $TunnelExe -PathType Leaf)) {
        throw "Installed official tunnel-client is missing: $TunnelExe"
    }

    $root = Get-ConfiguredFilesRoot
    $tunnelId = Resolve-TunnelId
    $semanticEntry = Get-SemanticEntry
    $node = (Get-Command 'node.exe' -ErrorAction Stop).Source
    $mcpCommand = @(
        ConvertTo-McpCommandPart -Value $node
        ConvertTo-McpCommandPart -Value $semanticEntry
    ) -join ' '

    Remove-Item $HealthUrlFile, $StdoutLog, $StderrLog -Force -ErrorAction SilentlyContinue

    $apiKey = Get-DecryptedApiKey
    $process = $null
    $oldKey = $env:CONTROL_PLANE_API_KEY
    $oldRoot = $env:CHAT_LOCAL_FILES_ROOT

    try {
        $env:CONTROL_PLANE_API_KEY = $apiKey
        $env:CHAT_LOCAL_FILES_ROOT = $root

        $argumentLine = @(
            'run',
            '--control-plane.tunnel-id',
            $tunnelId,
            '--mcp.command',
            (Quote-ProcessArgument -Value $mcpCommand),
            '--health.listen-addr',
            '127.0.0.1:0',
            '--health.url-file',
            (Quote-ProcessArgument -Value $HealthUrlFile)
        ) -join ' '

        $process = Start-Process `
            -FilePath $TunnelExe `
            -ArgumentList $argumentLine `
            -WindowStyle Hidden `
            -RedirectStandardOutput $StdoutLog `
            -RedirectStandardError $StderrLog `
            -PassThru
    }
    finally {
        if ($null -eq $oldKey) {
            Remove-Item Env:CONTROL_PLANE_API_KEY -ErrorAction SilentlyContinue
        }
        else {
            $env:CONTROL_PLANE_API_KEY = $oldKey
        }

        if ($null -eq $oldRoot) {
            Remove-Item Env:CHAT_LOCAL_FILES_ROOT -ErrorAction SilentlyContinue
        }
        else {
            $env:CHAT_LOCAL_FILES_ROOT = $oldRoot
        }

        $apiKey = $null
    }

    Save-DirectState `
        -ProcessId $process.Id `
        -Root $root `
        -TunnelId $tunnelId `
        -SemanticEntry $semanticEntry

    $ready = $false
    for ($i = 0; $i -lt 180; $i++) {
        if ($process.HasExited) {
            break
        }
        if (Test-DirectReady) {
            $ready = $true
            break
        }
        Start-Sleep -Milliseconds 250
    }

    if (-not $ready) {
        $stderrTail = if (Test-Path -LiteralPath $StderrLog) {
            (Get-Content -LiteralPath $StderrLog -Tail 40 | Out-String).Trim()
        }
        else {
            ''
        }

        Stop-DirectRuntime
        throw "Direct semantic tunnel did not become ready within 45 seconds. $stderrTail"
    }

    Write-Host 'SEMANTIC_DIRECT_STATUS=ready'
    Write-Host 'SEMANTIC_DIRECT_1MCP_USED=False'
    Write-Host "SEMANTIC_PROFILE=$profileName"
    Write-Host "SEMANTIC_DIRECT_FILES_ROOT=$root"
    Write-Host "SEMANTIC_DIRECT_TUNNEL_PID=$($process.Id)"
}

function Get-DirectStatusObject {
    $processes = @(Get-DirectTunnelProcesses)
    $running = ($processes.Count -gt 0)
    $ready = if ($running) { Test-DirectReady } else { $false }
    $portConflict = (@(Get-PortListeners).Count -gt 0)
    $conflict = ($processes.Count -gt 1 -or $portConflict)
    $root = $null
    $profileName = Get-EffectiveProfileName

    if (Test-Path -LiteralPath $DirectStateFile -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $DirectStateFile -Raw | ConvertFrom-Json
            $root = [string]$state.files_root
            if (
                $null -ne $state.PSObject.Properties['profile'] -and
                [string]$state.profile -in @('semantic', 'semantic-direct')
            ) {
                $profileName = [string]$state.profile
            }
        }
        catch {
            $conflict = $true
        }
    }

    if (
        [string]::IsNullOrWhiteSpace($root) -and
        (Test-Path -LiteralPath $MainSettingsFile -PathType Leaf)
    ) {
        try {
            $settings = Get-Content -LiteralPath $MainSettingsFile -Raw | ConvertFrom-Json
            if ($null -ne $settings.PSObject.Properties['files_root']) {
                $root = [string]$settings.files_root
            }
        }
        catch {
            $conflict = $true
        }
    }

    return [pscustomobject]@{
        tunnel_running = $running
        tunnel_ready = ($ready -and -not $conflict)
        mcp_ready = ($ready -and -not $conflict)
        active_profile = if ($running) { $profileName } else { $null }
        active_count = if ($running) { 1 } else { 0 }
        conflict = $conflict
        local_root = $LocalRoot
        tunnel_binding = 'direct-stdio'
        settings = [pscustomobject]@{
            profile = $profileName
            files_root = $root
            tunnel_profile = 'direct-stdio'
        }
    }
}

Initialize-Directories

try {
    switch ($Action) {
        'Start' {
            Start-DirectRuntime
        }
        'Stop' {
            Stop-DirectRuntime
            Write-Host 'SEMANTIC_DIRECT_STATUS=stopped'
        }
        'Toggle' {
            if (@(Get-DirectTunnelProcesses).Count -gt 0) {
                Stop-DirectRuntime
                Write-Host 'SEMANTIC_DIRECT_STATUS=stopped'
            }
            else {
                Start-DirectRuntime
            }
        }
        'Status' {
            Get-DirectStatusObject | ConvertTo-Json -Depth 6
        }
    }
}
catch {
    Write-Error $_
    exit 1
}
