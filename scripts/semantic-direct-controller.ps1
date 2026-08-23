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
$RemoteProbeCacheFile = Join-Path $StateDir 'semantic-direct-remote-health.json'
$HealthUrlFile = Join-Path $StateDir 'semantic-direct-health.url'
$StdoutLog = Join-Path $LogDir 'semantic-direct-tunnel-stdout.log'
$StderrLog = Join-Path $LogDir 'semantic-direct-tunnel-stderr.log'
$McpPort = 3050

$PollFreshnessSeconds = 120
$RemoteProbeCacheSeconds = 30
$RemoteProbeTimeoutMilliseconds = 8000
$LocalHealthTimeoutMilliseconds = 4000

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
        catch {}
    }

    return 'semantic-direct'
}

function Get-DirectState {
    if (-not (Test-Path -LiteralPath $DirectStateFile -PathType Leaf)) {
        return $null
    }
    try {
        return Get-Content -LiteralPath $DirectStateFile -Raw | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Get-ConfiguredFilesRoot {
    if (-not [string]::IsNullOrWhiteSpace($FilesRoot)) {
        if (-not (Test-Path -LiteralPath $FilesRoot -PathType Container)) {
            throw "FilesRoot must be an existing directory: $FilesRoot"
        }
        return (Resolve-Path -LiteralPath $FilesRoot).Path
    }

    $state = Get-DirectState
    if (
        $null -ne $state -and
        $null -ne $state.PSObject.Properties['files_root'] -and
        -not [string]::IsNullOrWhiteSpace([string]$state.files_root) -and
        (Test-Path -LiteralPath ([string]$state.files_root) -PathType Container)
    ) {
        return (Resolve-Path -LiteralPath ([string]$state.files_root)).Path
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
    $state = Get-DirectState
    if (
        $null -ne $state -and
        $null -ne $state.PSObject.Properties['tunnel_id'] -and
        [string]$state.tunnel_id -match '^tunnel_[0-9a-f]{32}$'
    ) {
        return [string]$state.tunnel_id
    }

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
                try { $actualExe = [System.IO.Path]::GetFullPath($actualExe) }
                catch { return $false }
                return (
                    $actualExe -ieq $expectedExe -and
                    $commandLine -match '(?i)--mcp\.command' -and
                    $commandLine -match $healthPattern
                )
            }
    )
}

function Get-SemanticProcesses {
    $state = Get-DirectState
    if (
        $null -eq $state -or
        $null -eq $state.PSObject.Properties['semantic_entry'] -or
        [string]::IsNullOrWhiteSpace([string]$state.semantic_entry)
    ) {
        return @()
    }

    $entryPattern = [regex]::Escape([string]$state.semantic_entry)
    return @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Name -eq 'node.exe' -and
                -not [string]::IsNullOrWhiteSpace([string]$_.CommandLine) -and
                [string]$_.CommandLine -match $entryPattern
            }
    )
}

function Invoke-BoundedProcess {
    param(
        [Parameter(Mandatory)] [string]$FilePath,
        [Parameter(Mandatory)] [string[]]$Arguments,
        [ValidateRange(100, 60000)] [int]$TimeoutMilliseconds,
        [hashtable]$Environment = @{}
    )

    $info = [System.Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $FilePath
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true

    foreach ($argument in $Arguments) {
        $info.ArgumentList.Add([string]$argument)
    }

    foreach ($key in $Environment.Keys) {
        if ($null -eq $Environment[$key]) {
            $null = $info.Environment.Remove([string]$key)
        }
        else {
            $info.Environment[[string]$key] = [string]$Environment[$key]
        }
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $info

    try {
        if (-not $process.Start()) {
            return [pscustomobject]@{ exit_code = -1; timed_out = $false; stdout = ''; stderr = 'process_start_failed' }
        }

        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutMilliseconds)) {
            try { $process.Kill($true) } catch {}
            $process.WaitForExit()
            return [pscustomobject]@{
                exit_code = -1
                timed_out = $true
                stdout = $stdoutTask.GetAwaiter().GetResult()
                stderr = $stderrTask.GetAwaiter().GetResult()
            }
        }

        $process.WaitForExit()
        return [pscustomobject]@{
            exit_code = $process.ExitCode
            timed_out = $false
            stdout = $stdoutTask.GetAwaiter().GetResult()
            stderr = $stderrTask.GetAwaiter().GetResult()
        }
    }
    finally {
        $process.Dispose()
    }
}

function Get-LocalHealthProbe {
    param([object[]]$Processes)

    if (
        $Processes.Count -ne 1 -or
        -not (Test-Path -LiteralPath $TunnelExe -PathType Leaf) -or
        -not (Test-Path -LiteralPath $HealthUrlFile -PathType Leaf)
    ) {
        return [pscustomobject]@{
            healthz_ok = $false
            readyz_ok = $false
            poll_ok = $false
            poll_age_seconds = $null
            process_ok = ($Processes.Count -eq 1)
            error = 'local_health_unavailable'
        }
    }

    $result = Invoke-BoundedProcess `
        -FilePath $TunnelExe `
        -Arguments @(
            'health', '--json', '--url-file', $HealthUrlFile,
            '--pid', [string]$Processes[0].ProcessId,
            '--require-control-plane-poll'
        ) `
        -TimeoutMilliseconds $LocalHealthTimeoutMilliseconds

    if ($result.timed_out -or [string]::IsNullOrWhiteSpace([string]$result.stdout)) {
        return [pscustomobject]@{
            healthz_ok = $false
            readyz_ok = $false
            poll_ok = $false
            poll_age_seconds = $null
            process_ok = $true
            error = if ($result.timed_out) { 'local_health_timeout' } else { 'local_health_empty' }
        }
    }

    try { $report = [string]$result.stdout | ConvertFrom-Json }
    catch {
        return [pscustomobject]@{
            healthz_ok = $false
            readyz_ok = $false
            poll_ok = $false
            poll_age_seconds = $null
            process_ok = $true
            error = 'local_health_invalid_json'
        }
    }

    $pollOk = $false
    $pollAge = $null
    if ($null -ne $report.PSObject.Properties['control_plane_poll'] -and $null -ne $report.control_plane_poll) {
        $pollOk = [bool]$report.control_plane_poll.ok
        if ($pollOk -and [double]$report.control_plane_poll.value -gt 0) {
            $nowUnix = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
            $pollAge = [math]::Max(0, $nowUnix - [double]$report.control_plane_poll.value)
        }
    }

    return [pscustomobject]@{
        healthz_ok = [bool]$report.healthz.ok
        readyz_ok = [bool]$report.readyz.ok
        poll_ok = $pollOk
        poll_age_seconds = $pollAge
        process_ok = if ($null -ne $report.process) { [bool]$report.process.running } else { $true }
        error = $null
    }
}

function ConvertTo-RemoteTunnelStatus {
    param(
        [Nullable[int]]$StatusCode,
        [string]$InvocationError,
        [bool]$Succeeded = $false
    )

    if ($Succeeded) { return 'ready' }
    if ($null -ne $StatusCode) {
        $code = [int]$StatusCode
        switch ($code) {
            401 { return 'unauthorized' }
            403 { return 'forbidden' }
            404 { return 'resource_missing' }
            429 { return 'rate_limited' }
        }
        if ($code -ge 500 -and $code -le 599) { return 'service_unavailable' }
    }
    if (-not [string]::IsNullOrWhiteSpace($InvocationError)) { return 'unavailable' }
    return 'unknown'
}

function Read-RemoteProbeCache {
    param([Parameter(Mandatory)] [string]$TunnelId)

    if (-not (Test-Path -LiteralPath $RemoteProbeCacheFile -PathType Leaf)) { return $null }
    try {
        $cache = Get-Content -LiteralPath $RemoteProbeCacheFile -Raw | ConvertFrom-Json
        if ([string]$cache.tunnel_id -ne $TunnelId) { return $null }
        $checkedAt = [datetime]::Parse([string]$cache.checked_at).ToUniversalTime()
        if (((Get-Date).ToUniversalTime() - $checkedAt).TotalSeconds -gt $RemoteProbeCacheSeconds) { return $null }
        return $cache
    }
    catch { return $null }
}

function Save-RemoteProbeCache {
    param([Parameter(Mandatory)] [string]$TunnelId, [Parameter(Mandatory)] $Probe)

    $temporary = "$RemoteProbeCacheFile.new"
    [ordered]@{
        schema_version = 1
        tunnel_id = $TunnelId
        status = [string]$Probe.status
        status_code = $Probe.status_code
        request_id = $Probe.request_id
        checked_at = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $temporary -Encoding utf8
    Move-Item -LiteralPath $temporary -Destination $RemoteProbeCacheFile -Force
}

function Get-RemoteTunnelProbe {
    param(
        [Parameter(Mandatory)] [string]$TunnelId,
        [switch]$Force
    )

    if (-not $Force) {
        $cached = Read-RemoteProbeCache -TunnelId $TunnelId
        if ($null -ne $cached) {
            return [pscustomobject]@{
                status = [string]$cached.status
                status_code = $cached.status_code
                request_id = [string]$cached.request_id
                cached = $true
                error = $null
            }
        }
    }

    if (-not (Test-Path -LiteralPath $TunnelExe -PathType Leaf)) {
        return [pscustomobject]@{ status = 'unknown'; status_code = $null; request_id = $null; cached = $false; error = 'tunnel_binary_unavailable' }
    }

    $apiKey = $null
    try {
        $apiKey = Get-DecryptedApiKey
        $result = Invoke-BoundedProcess `
            -FilePath $TunnelExe `
            -Arguments @('admin', '--json', 'tunnels', 'get', $TunnelId) `
            -TimeoutMilliseconds $RemoteProbeTimeoutMilliseconds `
            -Environment @{
                CONTROL_PLANE_API_KEY = $apiKey
                OPENAI_API_KEY = $null
                OPENAI_ADMIN_KEY = $null
            }
    }
    catch {
        $probe = [pscustomobject]@{
            status = 'unavailable'
            status_code = $null
            request_id = $null
            cached = $false
            error = 'remote_probe_setup_failed'
        }
        Save-RemoteProbeCache -TunnelId $TunnelId -Probe $probe
        return $probe
    }
    finally {
        $apiKey = $null
    }

    if ($result.timed_out) {
        $probe = [pscustomobject]@{
            status = 'unavailable'
            status_code = $null
            request_id = $null
            cached = $false
            error = 'remote_probe_timeout'
        }
        Save-RemoteProbeCache -TunnelId $TunnelId -Probe $probe
        return $probe
    }

    if ($result.exit_code -eq 0) {
        try {
            $payload = [string]$result.stdout | ConvertFrom-Json
            if ([string]$payload.id -ne $TunnelId) { throw 'tunnel id mismatch' }
        }
        catch {
            $probe = [pscustomobject]@{
                status = 'unknown'
                status_code = $null
                request_id = $null
                cached = $false
                error = 'remote_probe_invalid_success_payload'
            }
            Save-RemoteProbeCache -TunnelId $TunnelId -Probe $probe
            return $probe
        }

        $probe = [pscustomobject]@{
            status = 'ready'
            status_code = 200
            request_id = $null
            cached = $false
            error = $null
        }
        Save-RemoteProbeCache -TunnelId $TunnelId -Probe $probe
        return $probe
    }

    $statusCode = $null
    $requestId = $null
    $message = ([string]$result.stderr).Trim()
    foreach ($candidate in @([string]$result.stdout, [string]$result.stderr)) {
        if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
        try {
            $payload = $candidate | ConvertFrom-Json
            if ($null -ne $payload.error) {
                if ($null -ne $payload.error.PSObject.Properties['status_code']) {
                    $statusCode = [int]$payload.error.status_code
                }
                if ($null -ne $payload.error.PSObject.Properties['request_id']) {
                    $requestId = [string]$payload.error.request_id
                }
                if ($null -ne $payload.error.PSObject.Properties['message']) {
                    $message = [string]$payload.error.message
                }
                break
            }
        }
        catch {}
    }

    $remoteStatus = ConvertTo-RemoteTunnelStatus -StatusCode $statusCode -InvocationError $message
    $probe = [pscustomobject]@{
        status = $remoteStatus
        status_code = $statusCode
        request_id = $requestId
        cached = $false
        error = if ($remoteStatus -eq 'ready') { $null } else { 'remote_probe_failed' }
    }
    Save-RemoteProbeCache -TunnelId $TunnelId -Probe $probe
    return $probe
}

function Get-TunnelEndToEndHealth {
    param(
        [int]$TunnelProcessCount,
        [int]$SemanticProcessCount,
        [bool]$HealthzOk,
        [bool]$ReadyzOk,
        [bool]$ControlPlanePollOk,
        [Nullable[double]]$ControlPlanePollAgeSeconds,
        [Parameter(Mandatory)] [string]$RemoteStatus,
        [bool]$Conflict
    )

    $pollFresh = (
        $ControlPlanePollOk -and
        $null -ne $ControlPlanePollAgeSeconds -and
        [double]$ControlPlanePollAgeSeconds -ge 0 -and
        [double]$ControlPlanePollAgeSeconds -le $PollFreshnessSeconds
    )
    $tunnelLocalReady = (-not $Conflict -and $TunnelProcessCount -eq 1 -and $HealthzOk)
    $semanticProcessReady = (-not $Conflict -and $SemanticProcessCount -eq 1)
    $mcpReady = ($tunnelLocalReady -and $semanticProcessReady -and $ReadyzOk)
    $runtimeReady = ($mcpReady -and $pollFresh)
    $openAiControlReady = ($RemoteStatus -eq 'ready' -and $pollFresh)
    $code = 'READY'
    $recoveryAction = 'none'

    if ($RemoteStatus -eq 'resource_missing') { $code = 'REMOTE_TUNNEL_RESOURCE_MISSING'; $recoveryAction = 'blocked' }
    elseif ($RemoteStatus -eq 'unauthorized') { $code = 'REMOTE_TUNNEL_UNAUTHORIZED'; $recoveryAction = 'blocked' }
    elseif ($RemoteStatus -eq 'forbidden') { $code = 'REMOTE_TUNNEL_FORBIDDEN'; $recoveryAction = 'blocked' }
    elseif ($Conflict -or $TunnelProcessCount -gt 1 -or $SemanticProcessCount -gt 1) { $code = 'LOCAL_RUNTIME_CONFLICT'; $recoveryAction = 'blocked' }
    elseif ($TunnelProcessCount -eq 0) { $code = 'LOCAL_TUNNEL_NOT_RUNNING'; $recoveryAction = 'restart_runtime' }
    elseif (-not $HealthzOk) { $code = 'LOCAL_TUNNEL_NOT_HEALTHY'; $recoveryAction = 'restart_runtime' }
    elseif ($SemanticProcessCount -eq 0) { $code = 'LOCAL_MCP_PROCESS_MISSING'; $recoveryAction = 'restart_runtime' }
    elseif ($RemoteStatus -in @('rate_limited', 'service_unavailable', 'unavailable')) {
        $code = if ($RemoteStatus -eq 'rate_limited') { 'REMOTE_METADATA_RATE_LIMITED' } else { 'REMOTE_METADATA_UNAVAILABLE' }
        $recoveryAction = 'wait_and_probe'
    }
    elseif (-not $pollFresh) { $code = 'REMOTE_TUNNEL_DISCONNECTED'; $recoveryAction = 'restart_runtime' }
    elseif (-not $ReadyzOk) { $code = 'LOCAL_MCP_UNAVAILABLE'; $recoveryAction = 'restart_runtime' }
    elseif ($RemoteStatus -eq 'unknown') { $code = 'REMOTE_METADATA_UNKNOWN'; $recoveryAction = 'wait_and_probe' }

    return [pscustomobject]@{
        code = $code
        recovery_action = $recoveryAction
        recoverable = ($recoveryAction -in @('restart_runtime', 'wait_and_probe'))
        runtime_ready = $runtimeReady
        mcp_ready = $mcpReady
        semantic_process_ready = $semanticProcessReady
        tunnel_local_ready = $tunnelLocalReady
        openai_control_ready = $openAiControlReady
        remote_status = $RemoteStatus
        control_plane_poll_fresh = $pollFresh
    }
}

function Save-DirectState {
    param(
        [int]$ProcessId,
        [Parameter(Mandatory)] [string]$Root,
        [Parameter(Mandatory)] [string]$TunnelId,
        [Parameter(Mandatory)] [string]$SemanticEntry
    )

    $previous = Get-DirectState
    $startedAt = if ($null -ne $previous -and $null -ne $previous.PSObject.Properties['started_at']) {
        [string]$previous.started_at
    }
    else {
        (Get-Date).ToUniversalTime().ToString('o')
    }

    $temporary = "$DirectStateFile.new"
    [ordered]@{
        schema_version = 4
        pid = $ProcessId
        profile = Get-EffectiveProfileName
        files_root = $Root
        tunnel_id = $TunnelId
        semantic_entry = $SemanticEntry
        owner = 'chat-platform-manager'
        started_at = $startedAt
        updated_at = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $temporary -Encoding utf8
    Move-Item -LiteralPath $temporary -Destination $DirectStateFile -Force
}

function Get-DirectStatusObject {
    param([switch]$ForceRemote)

    $processes = @(Get-DirectTunnelProcesses)
    $semanticProcesses = @(Get-SemanticProcesses)
    $running = ($processes.Count -gt 0)
    $portConflict = (@(Get-PortListeners).Count -gt 0)
    $conflict = ($processes.Count -gt 1 -or $semanticProcesses.Count -gt 1 -or $portConflict)
    $profileName = Get-EffectiveProfileName
    $root = $null
    $tunnelId = $null
    $state = Get-DirectState

    if ($null -ne $state) {
        if ($null -ne $state.PSObject.Properties['files_root']) { $root = [string]$state.files_root }
        if ($null -ne $state.PSObject.Properties['tunnel_id']) { $tunnelId = [string]$state.tunnel_id }
        if (
            $null -ne $state.PSObject.Properties['profile'] -and
            [string]$state.profile -in @('semantic', 'semantic-direct')
        ) {
            $profileName = [string]$state.profile
        }
    }

    if ([string]::IsNullOrWhiteSpace($root) -and (Test-Path -LiteralPath $MainSettingsFile -PathType Leaf)) {
        try {
            $settings = Get-Content -LiteralPath $MainSettingsFile -Raw | ConvertFrom-Json
            if ($null -ne $settings.PSObject.Properties['files_root']) { $root = [string]$settings.files_root }
        }
        catch { $conflict = $true }
    }

    if ([string]::IsNullOrWhiteSpace($tunnelId)) {
        try { $tunnelId = Resolve-TunnelId } catch { $tunnelId = $null }
    }

    $local = Get-LocalHealthProbe -Processes $processes
    $remote = if (-not [string]::IsNullOrWhiteSpace($tunnelId)) {
        Get-RemoteTunnelProbe -TunnelId $tunnelId -Force:$ForceRemote
    }
    else {
        [pscustomobject]@{ status = 'unknown'; status_code = $null; request_id = $null; cached = $false; error = 'tunnel_id_unavailable' }
    }

    $health = Get-TunnelEndToEndHealth `
        -TunnelProcessCount $processes.Count `
        -SemanticProcessCount $semanticProcesses.Count `
        -HealthzOk ([bool]$local.healthz_ok) `
        -ReadyzOk ([bool]$local.readyz_ok) `
        -ControlPlanePollOk ([bool]$local.poll_ok) `
        -ControlPlanePollAgeSeconds $local.poll_age_seconds `
        -RemoteStatus ([string]$remote.status) `
        -Conflict $conflict

    return [pscustomobject]@{
        schema_version = 4
        tunnel_running = $running
        tunnel_ready = [bool]$health.tunnel_local_ready
        tunnel_local_ready = [bool]$health.tunnel_local_ready
        mcp_ready = [bool]$health.mcp_ready
        runtime_ready = [bool]$health.runtime_ready
        openai_ready = [bool]$health.openai_control_ready
        active_profile = if ($running) { $profileName } else { $null }
        active_count = if ($running) { 1 } else { 0 }
        conflict = $conflict
        local_root = $LocalRoot
        tunnel_binding = 'direct-stdio'
        tunnel_id = $tunnelId
        tunnel_process_count = $processes.Count
        semantic_process_count = $semanticProcesses.Count
        semantic_process_ready = [bool]$health.semantic_process_ready
        health_code = [string]$health.code
        recovery_action = [string]$health.recovery_action
        recoverable = [bool]$health.recoverable
        remote_tunnel_status = [string]$remote.status
        remote_status_code = $remote.status_code
        remote_probe_cached = [bool]$remote.cached
        control_plane_poll_ok = [bool]$local.poll_ok
        control_plane_poll_age_seconds = $local.poll_age_seconds
        control_plane_poll_fresh = [bool]$health.control_plane_poll_fresh
        settings = [pscustomobject]@{
            profile = $profileName
            files_root = $root
            tunnel_profile = 'direct-stdio'
        }
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

    $state = Get-DirectState
    if (
        $null -ne $state -and
        $null -ne $state.PSObject.Properties['semantic_entry'] -and
        -not [string]::IsNullOrWhiteSpace([string]$state.semantic_entry)
    ) {
        try {
            $entryPattern = [regex]::Escape([string]$state.semantic_entry)
            Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
                Where-Object {
                    $_.Name -eq 'node.exe' -and
                    -not [string]::IsNullOrWhiteSpace([string]$_.CommandLine) -and
                    [string]$_.CommandLine -match $entryPattern
                } |
                ForEach-Object {
                    Stop-Process -Id ([int]$_.ProcessId) -Force -ErrorAction SilentlyContinue
                }
        }
        catch {}
    }

    Remove-Item -LiteralPath $HealthUrlFile -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $DirectStateFile -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $RemoteProbeCacheFile -Force -ErrorAction SilentlyContinue
}

function Assert-RemotePreflightNotBlocked {
    param([Parameter(Mandatory)] [string]$TunnelId)

    $remote = Get-RemoteTunnelProbe -TunnelId $TunnelId -Force
    switch ([string]$remote.status) {
        'resource_missing' { throw 'REMOTE_TUNNEL_RESOURCE_MISSING' }
        'unauthorized' { throw 'REMOTE_TUNNEL_UNAUTHORIZED' }
        'forbidden' { throw 'REMOTE_TUNNEL_FORBIDDEN' }
    }
}

function Start-DirectRuntime {
    Initialize-Directories
    $profileName = Get-EffectiveProfileName

    $existing = Get-DirectStatusObject
    if ([bool]$existing.runtime_ready -and -not [bool]$existing.conflict) {
        Write-Host 'SEMANTIC_DIRECT_STATUS=ready'
        Write-Host 'SEMANTIC_DIRECT_1MCP_USED=False'
        Write-Host "SEMANTIC_PROFILE=$profileName"
        Write-Host "SEMANTIC_DIRECT_HEALTH_CODE=$($existing.health_code)"
        return
    }

    if (
        @(Get-DirectTunnelProcesses).Count -gt 0 -or
        @(Get-SemanticProcesses).Count -gt 0 -or
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
    Save-DirectState -ProcessId 0 -Root $root -TunnelId $tunnelId -SemanticEntry $semanticEntry
    Assert-RemotePreflightNotBlocked -TunnelId $tunnelId

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
            'run', '--control-plane.tunnel-id', $tunnelId,
            '--mcp.command', (Quote-ProcessArgument -Value $mcpCommand),
            '--health.listen-addr', '127.0.0.1:0',
            '--health.url-file', (Quote-ProcessArgument -Value $HealthUrlFile)
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
    $lastStatus = $null
    for ($i = 0; $i -lt 180; $i++) {
        if ($process.HasExited) { break }
        $lastStatus = Get-DirectStatusObject
        if ([bool]$lastStatus.runtime_ready -and -not [bool]$lastStatus.conflict) {
            $ready = $true
            break
        }
        if ([string]$lastStatus.recovery_action -eq 'blocked') { break }
        Start-Sleep -Milliseconds 250
    }

    if (-not $ready) {
        $code = if ($null -ne $lastStatus) { [string]$lastStatus.health_code } else { 'LOCAL_TUNNEL_NOT_HEALTHY' }
        $stderrTail = if (Test-Path -LiteralPath $StderrLog) {
            (Get-Content -LiteralPath $StderrLog -Tail 40 | Out-String).Trim()
        }
        else { '' }
        Stop-DirectRuntime
        throw "Direct semantic tunnel did not become runtime-ready within 45 seconds. health_code=$code $stderrTail"
    }

    Write-Host 'SEMANTIC_DIRECT_STATUS=ready'
    Write-Host 'SEMANTIC_DIRECT_1MCP_USED=False'
    Write-Host "SEMANTIC_PROFILE=$profileName"
    Write-Host "SEMANTIC_DIRECT_FILES_ROOT=$root"
    Write-Host "SEMANTIC_DIRECT_TUNNEL_PID=$($process.Id)"
    Write-Host "SEMANTIC_DIRECT_TUNNEL_ID=$tunnelId"
    Write-Host "SEMANTIC_DIRECT_HEALTH_CODE=$($lastStatus.health_code)"
}

Initialize-Directories

try {
    switch ($Action) {
        'Start' { Start-DirectRuntime }
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
            Get-DirectStatusObject | ConvertTo-Json -Depth 7
        }
    }
}
catch {
    Write-Error $_
    exit 1
}
