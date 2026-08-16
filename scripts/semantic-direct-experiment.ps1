[CmdletBinding()]
param(
    [ValidateSet('Start', 'Stop', 'Toggle', 'Status', 'SetProfile')]
    [string]$Action = 'Status',

    [ValidateSet('reference', 'files-readonly', 'browser-isolated', 'semantic', 'adaptive')]
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

$InstalledScript = Join-Path $AppScriptsDir 'semantic-direct-experiment.ps1'
$MainCommand = Join-Path $AppScriptsDir 'chat-platform.ps1'
$SemanticRuntimeHelper = Join-Path $AppScriptsDir 'semantic-projection-runtime.ps1'
$TunnelExe = Join-Path $BinDir 'tunnel-client.exe'
$BaselineTunnelProfile = Join-Path $TunnelDir 'local-1mcp.yaml'
$SecretFile = Join-Path $LocalRoot 'secrets\control-plane-api-key.dpapi'
$MainSettingsFile = Join-Path $StateDir 'settings.json'
$OwnerFile = Join-Path $StateDir 'manager-owner.json'
$DirectStateFile = Join-Path $StateDir 'semantic-direct.json'
$HealthUrlFile = Join-Path $StateDir 'semantic-direct-health.url'
$StdoutLog = Join-Path $LogDir 'semantic-direct-tunnel-stdout.log'
$StderrLog = Join-Path $LogDir 'semantic-direct-tunnel-stderr.log'
$McpPort = 3050

function Initialize-Directories {
    foreach ($path in @($AppScriptsDir, $StateDir, $LogDir)) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
    }
}

function Test-SamePath {
    param([string]$Left, [string]$Right)
    if ([string]::IsNullOrWhiteSpace($Left) -or [string]::IsNullOrWhiteSpace($Right)) {
        return $false
    }
    try {
        return (
            [System.IO.Path]::GetFullPath($Left).TrimEnd('\') -ieq
            [System.IO.Path]::GetFullPath($Right).TrimEnd('\')
        )
    }
    catch {
        return $false
    }
}

function Install-SelfIfNeeded {
    Initialize-Directories
    if (Test-SamePath -Left $PSCommandPath -Right $InstalledScript) {
        return $false
    }

    $temporary = "$InstalledScript.new"
    Copy-Item -LiteralPath $PSCommandPath -Destination $temporary -Force
    $sourceHash = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
    $copyHash = (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash
    if ($sourceHash -ne $copyHash) {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
        throw 'semantic-direct experiment self-install verification failed.'
    }
    Move-Item -LiteralPath $temporary -Destination $InstalledScript -Force
    return $true
}

function Invoke-InstalledSelf {
    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    $arguments = @(
        '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', $InstalledScript,
        '-Action', $Action,
        '-NoNotify'
    )
    if (-not [string]::IsNullOrWhiteSpace($Profile)) {
        $arguments += @('-Profile', $Profile)
    }
    if (-not [string]::IsNullOrWhiteSpace($FilesRoot)) {
        $arguments += @('-FilesRoot', $FilesRoot)
    }
    & $pwsh @arguments
    exit $LASTEXITCODE
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
            # Fall through to the accepted manager settings.
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

    throw 'semantic-direct requires FilesRoot. Pass -FilesRoot or configure the accepted semantic profile first.'
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
                if ($_.Name -ne 'tunnel-client.exe') { return $false }
                $actualExe = [string]$_.ExecutablePath
                $commandLine = [string]$_.CommandLine
                if ([string]::IsNullOrWhiteSpace($actualExe) -or [string]::IsNullOrWhiteSpace($commandLine)) {
                    return $false
                }
                try { $actualExe = [System.IO.Path]::GetFullPath($actualExe) } catch { return $false }
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
        schema_version = 1
        pid = $ProcessId
        files_root = $Root
        tunnel_id = $TunnelId
        semantic_entry = $SemanticEntry
        started_at = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $DirectStateFile -Encoding utf8
}

function Save-ManagerOwner {
    [ordered]@{
        schema_version = 1
        controller_path = [System.IO.Path]::GetFullPath($InstalledScript)
        command_path = [System.IO.Path]::GetFullPath($InstalledScript)
        repo_root = [System.IO.Path]::GetFullPath($AppRoot)
        started_at = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $OwnerFile -Encoding utf8
}

function Remove-ManagerOwnerIfOurs {
    if (-not (Test-Path -LiteralPath $OwnerFile -PathType Leaf)) {
        return
    }
    try {
        $owner = Get-Content -LiteralPath $OwnerFile -Raw | ConvertFrom-Json
        if (Test-SamePath -Left ([string]$owner.controller_path) -Right $InstalledScript) {
            Remove-Item -LiteralPath $OwnerFile -Force -ErrorAction SilentlyContinue
        }
    }
    catch {
        # Do not destroy ownership state that cannot be attributed to this experiment.
    }
}

function Stop-DirectRuntime {
    foreach ($process in @(Get-DirectTunnelProcesses)) {
        Stop-Process -Id ([int]$process.ProcessId) -Force -ErrorAction SilentlyContinue
    }
    for ($i = 0; $i -lt 30; $i++) {
        if (@(Get-DirectTunnelProcesses).Count -eq 0) { break }
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
            # The tunnel parent is authoritative; orphan cleanup is best effort.
        }
    }

    Remove-Item -LiteralPath $HealthUrlFile -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $DirectStateFile -Force -ErrorAction SilentlyContinue
    Remove-ManagerOwnerIfOurs
}

function Invoke-BaselineStop {
    if (-not (Test-Path -LiteralPath $MainCommand -PathType Leaf)) {
        throw "Accepted installed manager command is missing: $MainCommand"
    }
    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    & $pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $MainCommand -Action Stop -NoNotify
    if ($LASTEXITCODE -ne 0) {
        throw "Could not stop the accepted platform before semantic-direct startup. Exit=$LASTEXITCODE"
    }
}

function Start-DirectRuntime {
    Initialize-Directories

    if (Test-DirectReady) {
        Save-ManagerOwner
        Write-Host 'SEMANTIC_DIRECT_STATUS=ready'
        return
    }

    if (@(Get-DirectTunnelProcesses).Count -gt 0) {
        Stop-DirectRuntime
    }

    Invoke-BaselineStop

    $listeners = @(Get-PortListeners)
    if ($listeners.Count -gt 0) {
        throw "Local MCP port $McpPort is still occupied after stopping the accepted manager. Refusing ambiguous direct startup."
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
        if ($null -eq $oldKey) { Remove-Item Env:CONTROL_PLANE_API_KEY -ErrorAction SilentlyContinue }
        else { $env:CONTROL_PLANE_API_KEY = $oldKey }
        if ($null -eq $oldRoot) { Remove-Item Env:CHAT_LOCAL_FILES_ROOT -ErrorAction SilentlyContinue }
        else { $env:CHAT_LOCAL_FILES_ROOT = $oldRoot }
        $apiKey = $null
    }

    Save-DirectState -ProcessId $process.Id -Root $root -TunnelId $tunnelId -SemanticEntry $semanticEntry

    $ready = $false
    for ($i = 0; $i -lt 180; $i++) {
        if ($process.HasExited) { break }
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
        else { '' }
        Stop-DirectRuntime
        throw "semantic-direct tunnel did not become ready within 45 seconds. $stderrTail"
    }

    Save-ManagerOwner
    Write-Host 'SEMANTIC_DIRECT_STATUS=ready'
    Write-Host 'SEMANTIC_DIRECT_1MCP_USED=False'
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

    if (Test-Path -LiteralPath $DirectStateFile -PathType Leaf) {
        try {
            $state = Get-Content -LiteralPath $DirectStateFile -Raw | ConvertFrom-Json
            $root = [string]$state.files_root
        }
        catch {
            $conflict = $true
        }
    }

    return [pscustomobject]@{
        tunnel_running = $running
        tunnel_ready = ($ready -and -not $conflict)
        mcp_ready = ($ready -and -not $conflict)
        active_profile = if ($running) { 'semantic-direct' } else { $null }
        active_count = if ($running) { 1 } else { 0 }
        conflict = $conflict
        local_root = $LocalRoot
        tunnel_binding = 'direct-stdio'
        settings = [pscustomobject]@{
            profile = 'semantic-direct'
            files_root = $root
            tunnel_profile = 'direct-stdio'
        }
    }
}

Initialize-Directories

if (-not (Test-SamePath -Left $PSCommandPath -Right $InstalledScript)) {
    if ($Action -eq 'Start') {
        $null = Install-SelfIfNeeded
        Invoke-InstalledSelf
    }
    elseif (Test-Path -LiteralPath $InstalledScript -PathType Leaf) {
        Invoke-InstalledSelf
    }
}

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
        'SetProfile' {
            if (@(Get-DirectTunnelProcesses).Count -gt 0) {
                throw 'Stop semantic-direct before changing the accepted manager profile.'
            }
            Remove-ManagerOwnerIfOurs
            throw 'semantic-direct experiment is stopped. Retry SetProfile through the normal chat-platform.ps1 manager.'
        }
    }
}
catch {
    Write-Error $_
    exit 1
}