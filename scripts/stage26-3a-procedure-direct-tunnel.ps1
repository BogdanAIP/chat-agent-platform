[CmdletBinding()]
param(
    [ValidateSet('Start', 'Stop', 'Status')]
    [string]$Action = 'Status',

    [string]$FilesRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    throw 'LOCALAPPDATA is unavailable.'
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$localRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform'
$stateDir = Join-Path $localRoot 'state'
$logDir = Join-Path $localRoot 'logs'
$binDir = Join-Path $localRoot 'bin'
$tunnelDir = Join-Path $localRoot 'tunnel'
$secretFile = Join-Path $localRoot 'secrets\control-plane-api-key.dpapi'
$tunnelExe = Join-Path $binDir 'tunnel-client.exe'
$baselineTunnelProfile = Join-Path $tunnelDir 'local-1mcp.yaml'
$qualificationEntry = Join-Path $repoRoot 'runtime\semantic-projection\bin\procedure-qualification-projection.mjs'
$runtimeHelper = Join-Path $PSScriptRoot 'semantic-projection-runtime.ps1'
$stopProfiles = Join-Path $PSScriptRoot 'stop-chat-profile.ps1'
$qualificationState = Join-Path $stateDir 'stage26-3a-procedure-direct.json'
$healthUrlFile = Join-Path $stateDir 'stage26-3a-procedure-direct-health.url'
$stdoutLog = Join-Path $logDir 'stage26-3a-procedure-direct-stdout.log'
$stderrLog = Join-Path $logDir 'stage26-3a-procedure-direct-stderr.log'
$procedureStateRoot = Join-Path $localRoot 'stage26\procedure-state'
$qualificationAdmission = 'stage26-3a-qualification'

function Initialize-Directories {
    foreach ($path in @($stateDir, $logDir, $procedureStateRoot)) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
    }
}

function Resolve-SafeFilesRoot {
    param([Parameter(Mandatory)] [string]$Path)

    $item = Get-Item -LiteralPath (Resolve-Path -LiteralPath $Path).Path
    if (-not $item.PSIsContainer) {
        throw "FilesRoot must be an existing directory: $Path"
    }

    $full = [System.IO.Path]::GetFullPath($item.FullName).TrimEnd('\')
    $driveRoot = [System.IO.Path]::GetPathRoot($full).TrimEnd('\')
    if ($full -ieq $driveRoot) {
        throw 'A whole drive cannot be exposed to the qualification profile.'
    }

    foreach ($blocked in @($env:SystemRoot, $env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:ProgramData, $env:USERPROFILE)) {
        if ([string]::IsNullOrWhiteSpace($blocked)) { continue }
        if ($full -ieq [System.IO.Path]::GetFullPath($blocked).TrimEnd('\')) {
            throw "Refusing broad/system FilesRoot '$full'."
        }
    }

    return $full
}

function Resolve-TunnelId {
    if (-not (Test-Path -LiteralPath $baselineTunnelProfile -PathType Leaf)) {
        throw "Accepted tunnel profile is missing: $baselineTunnelProfile"
    }

    $matches = @(
        [regex]::Matches((Get-Content -LiteralPath $baselineTunnelProfile -Raw), 'tunnel_[0-9a-f]{32}') |
            ForEach-Object { $_.Value } |
            Select-Object -Unique
    )
    if ($matches.Count -ne 1) {
        throw 'Could not resolve exactly one persistent tunnel id from the accepted profile.'
    }
    return [string]$matches[0]
}

function Get-DecryptedApiKey {
    if (-not (Test-Path -LiteralPath $secretFile -PathType Leaf)) {
        throw "Accepted DPAPI tunnel key is missing: $secretFile"
    }
    $protectedBytes = [Convert]::FromBase64String((Get-Content -LiteralPath $secretFile -Raw).Trim())
    try {
        $plainBytes = [Security.Cryptography.ProtectedData]::Unprotect(
            $protectedBytes,
            $null,
            [Security.Cryptography.DataProtectionScope]::CurrentUser
        )
        try { return [Text.Encoding]::UTF8.GetString($plainBytes) }
        finally { [Array]::Clear($plainBytes, 0, $plainBytes.Length) }
    }
    finally {
        [Array]::Clear($protectedBytes, 0, $protectedBytes.Length)
    }
}

function ConvertTo-McpCommandPart {
    param([Parameter(Mandatory)] [string]$Value)
    if ($Value -match '^[A-Za-z0-9_/:=.,@%+-]+$') { return $Value }
    if ($Value.Contains("'")) { throw "Unsupported apostrophe in MCP command path: $Value" }
    return "'$Value'"
}

function Quote-ProcessArgument {
    param([Parameter(Mandatory)] [string]$Value)
    if ($Value.Contains('"')) { throw "Unsupported double quote in process argument: $Value" }
    if ($Value -notmatch '\s') { return $Value }
    return '"' + $Value + '"'
}

function Get-HealthBaseUrl {
    if (-not (Test-Path -LiteralPath $healthUrlFile -PathType Leaf)) { return $null }
    try {
        $url = (Get-Content -LiteralPath $healthUrlFile -Raw).Trim().TrimEnd('/')
        if ($url -notmatch '^https?://127\.0\.0\.1(?::\d+)?$') { return $null }
        return $url
    }
    catch { return $null }
}

function Get-QualificationTunnelProcess {
    if (-not (Test-Path -LiteralPath $qualificationState -PathType Leaf)) { return $null }
    try {
        $state = Get-Content -LiteralPath $qualificationState -Raw | ConvertFrom-Json
        $pidValue = [int]$state.pid
        $process = Get-CimInstance Win32_Process -Filter "ProcessId = $pidValue" -ErrorAction SilentlyContinue
        if ($null -eq $process) { return $null }
        if ([string]$process.Name -ne 'tunnel-client.exe') { return $null }
        if ([string]$process.CommandLine -notmatch [regex]::Escape($healthUrlFile)) { return $null }
        return $process
    }
    catch { return $null }
}

function Get-OwnedQualificationSemanticChildren {
    param([Parameter(Mandatory)] $TunnelProcess)

    $parentPid = [int]$TunnelProcess.ProcessId
    $entryPattern = [regex]::Escape($qualificationEntry)
    return @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Name -eq 'node.exe' -and
                [int]$_.ParentProcessId -eq $parentPid -and
                [string]$_.CommandLine -match $entryPattern
            }
    )
}

function Test-QualificationReady {
    if ($null -eq (Get-QualificationTunnelProcess)) { return $false }
    $base = Get-HealthBaseUrl
    if ([string]::IsNullOrWhiteSpace($base)) { return $false }
    try {
        $response = Invoke-WebRequest -Uri "$base/readyz" -Method Get -TimeoutSec 2 -ErrorAction Stop
        return ($response.StatusCode -eq 200)
    }
    catch { return $false }
}

function Stop-QualificationTunnel {
    $process = Get-QualificationTunnelProcess
    $ownedSemanticChildren = if ($null -ne $process) {
        @(Get-OwnedQualificationSemanticChildren -TunnelProcess $process)
    }
    else {
        @()
    }

    if ($null -ne $process) {
        Stop-Process -Id ([int]$process.ProcessId) -Force -ErrorAction SilentlyContinue
    }

    # Cleanup authority is ancestry-bound. Never terminate arbitrary node.exe
    # processes merely because their command line happens to mention the same
    # qualification entry path.
    foreach ($child in $ownedSemanticChildren) {
        Stop-Process -Id ([int]$child.ProcessId) -Force -ErrorAction SilentlyContinue
    }

    Remove-Item -LiteralPath $healthUrlFile -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $qualificationState -Force -ErrorAction SilentlyContinue
}

function Start-QualificationTunnel {
    Initialize-Directories
    if ([string]::IsNullOrWhiteSpace($FilesRoot)) {
        throw 'Start requires -FilesRoot.'
    }
    if (-not (Test-Path -LiteralPath $tunnelExe -PathType Leaf)) {
        throw "Installed official tunnel-client is missing: $tunnelExe"
    }
    if (-not (Test-Path -LiteralPath $qualificationEntry -PathType Leaf)) {
        throw "Qualification projection is missing: $qualificationEntry"
    }

    $root = Resolve-SafeFilesRoot -Path $FilesRoot
    $tunnelId = Resolve-TunnelId

    . $runtimeHelper
    $null = Get-SemanticProjectionEntryPath -RepoRoot $repoRoot -EnsureDependencies

    # Qualification owns the tunnel route temporarily. Stop accepted local
    # profiles first so the same persistent tunnel id never has two local owners.
    & $stopProfiles
    Stop-QualificationTunnel

    $node = (Get-Command 'node.exe' -ErrorAction Stop).Source
    $mcpCommand = @(
        ConvertTo-McpCommandPart -Value $node
        ConvertTo-McpCommandPart -Value $qualificationEntry
    ) -join ' '

    Remove-Item $healthUrlFile, $stdoutLog, $stderrLog -Force -ErrorAction SilentlyContinue

    $apiKey = Get-DecryptedApiKey
    $old = @{}
    foreach ($name in @('CONTROL_PLANE_API_KEY', 'CHAT_LOCAL_FILES_ROOT', 'CHAT_PROCEDURE_STATE_ROOT', 'CHAT_PROCEDURE_ALLOW_CANDIDATE')) {
        $old[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    }

    $process = $null
    try {
        $env:CONTROL_PLANE_API_KEY = $apiKey
        $env:CHAT_LOCAL_FILES_ROOT = $root
        $env:CHAT_PROCEDURE_STATE_ROOT = $procedureStateRoot
        $env:CHAT_PROCEDURE_ALLOW_CANDIDATE = $qualificationAdmission

        $argumentLine = @(
            'run',
            '--control-plane.tunnel-id',
            $tunnelId,
            '--mcp.command',
            (Quote-ProcessArgument -Value $mcpCommand),
            '--health.listen-addr',
            '127.0.0.1:0',
            '--health.url-file',
            (Quote-ProcessArgument -Value $healthUrlFile)
        ) -join ' '

        $process = Start-Process `
            -FilePath $tunnelExe `
            -ArgumentList $argumentLine `
            -WindowStyle Hidden `
            -RedirectStandardOutput $stdoutLog `
            -RedirectStandardError $stderrLog `
            -PassThru
    }
    finally {
        foreach ($name in $old.Keys) {
            if ($null -eq $old[$name]) { Remove-Item "Env:$name" -ErrorAction SilentlyContinue }
            else { [Environment]::SetEnvironmentVariable($name, [string]$old[$name], 'Process') }
        }
        $apiKey = $null
    }

    [ordered]@{
        schema_version = 1
        pid = $process.Id
        tunnel_id = $tunnelId
        files_root = $root
        procedure_state_root = $procedureStateRoot
        qualification_entry = $qualificationEntry
        started_at = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $qualificationState -Encoding utf8

    $ready = $false
    for ($i = 0; $i -lt 180; $i++) {
        if ($process.HasExited) { break }
        if (Test-QualificationReady) { $ready = $true; break }
        Start-Sleep -Milliseconds 250
    }

    if (-not $ready) {
        $stderrTail = if (Test-Path -LiteralPath $stderrLog) {
            (Get-Content -LiteralPath $stderrLog -Tail 40 | Out-String).Trim()
        }
        else { '' }
        Stop-QualificationTunnel
        throw "Stage 26.3A qualification tunnel did not become ready. $stderrTail"
    }

    Write-Host 'STAGE26_3A_DIRECT_TUNNEL=ready'
    Write-Host "STAGE26_3A_TUNNEL_ID=$tunnelId"
    Write-Host "STAGE26_3A_TUNNEL_PID=$($process.Id)"
    Write-Host "STAGE26_3A_FILES_ROOT=$root"
    Write-Host "STAGE26_3A_PROCEDURE_STATE_ROOT=$procedureStateRoot"
    Write-Host 'STAGE26_3A_EXPECTED_TOOL_COUNT=6'
}

function Get-QualificationStatus {
    $process = Get-QualificationTunnelProcess
    $state = $null
    if (Test-Path -LiteralPath $qualificationState -PathType Leaf) {
        try { $state = Get-Content -LiteralPath $qualificationState -Raw | ConvertFrom-Json } catch {}
    }
    [ordered]@{
        schema_version = 1
        running = ($null -ne $process)
        ready = Test-QualificationReady
        pid = if ($null -ne $process) { [int]$process.ProcessId } else { $null }
        tunnel_id = if ($null -ne $state) { [string]$state.tunnel_id } else { $null }
        files_root = if ($null -ne $state) { [string]$state.files_root } else { $null }
        procedure_state_root = if ($null -ne $state) { [string]$state.procedure_state_root } else { $null }
        qualification_entry = if ($null -ne $state) { [string]$state.qualification_entry } else { $qualificationEntry }
    }
}

Initialize-Directories

switch ($Action) {
    'Start' { Start-QualificationTunnel }
    'Stop' {
        Stop-QualificationTunnel
        Write-Host 'STAGE26_3A_DIRECT_TUNNEL=stopped'
    }
    'Status' { Get-QualificationStatus | ConvertTo-Json -Depth 4 }
}
