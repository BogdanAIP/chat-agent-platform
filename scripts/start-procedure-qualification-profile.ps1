param(
    [Parameter(Mandatory)]
    [string]$FilesRoot,

    [string]$StateRoot,

    [int]$Port = 3050,

    [ValidateRange(30, 600)]
    [int]$ReadyTimeoutSeconds = 120
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$stablePkg = '@1mcp/agent@0.34.4'
$startBridge = Join-Path $PSScriptRoot 'start-local-bridge.ps1'
$stopProfiles = Join-Path $PSScriptRoot 'stop-chat-profile.ps1'
$runtimeHelper = Join-Path $PSScriptRoot 'semantic-projection-runtime.ps1'
$profileConfig = Join-Path $repoRoot 'runtime\chat-profiles\procedure-qualification\mcp.json'
$qualificationEntry = Join-Path $repoRoot 'runtime\semantic-projection\bin\procedure-qualification-projection.mjs'
$qualificationAdmission = 'stage26-3a-qualification'

. $runtimeHelper

function Resolve-SafeFilesRoot {
    param([Parameter(Mandatory)] [string]$Path)

    $item = Get-Item -LiteralPath (Resolve-Path -LiteralPath $Path).Path
    if (-not $item.PSIsContainer) {
        throw "FilesRoot must be an existing directory: $Path"
    }

    $full = [System.IO.Path]::GetFullPath($item.FullName).TrimEnd('\')
    $driveRoot = [System.IO.Path]::GetPathRoot($full).TrimEnd('\')
    if ($full -ieq $driveRoot) {
        throw 'A whole drive cannot be exposed to Chat. Choose one explicit workspace folder.'
    }

    $blockedExact = @(
        $env:SystemRoot,
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)},
        $env:ProgramData,
        $env:USERPROFILE
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object {
        [System.IO.Path]::GetFullPath($_).TrimEnd('\')
    }

    if ($blockedExact | Where-Object { $_ -ieq $full }) {
        throw "Refusing broad/system FilesRoot '$full'. Choose a narrower workspace subfolder."
    }

    return $full
}

function Resolve-StateRoot {
    param([string]$Path)

    $candidate = if (-not [string]::IsNullOrWhiteSpace($Path)) {
        $Path
    }
    else {
        if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
            throw 'LOCALAPPDATA is unavailable; pass -StateRoot explicitly.'
        }
        Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage26\procedure-state'
    }

    $full = [System.IO.Path]::GetFullPath($candidate)
    New-Item -ItemType Directory -Force -Path $full | Out-Null
    return $full.TrimEnd('\')
}

function Get-QualificationToolNames {
    param([Parameter(Mandatory)] [string]$BaseUrl)

    $inventoryText = & npx.cmd -y $stablePkg inspect procedure-qualification-projection --url $BaseUrl --format json --all 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect procedure qualification projection.`n$inventoryText"
    }

    try {
        $inventory = $inventoryText | ConvertFrom-Json
    }
    catch {
        throw "1MCP inspect returned non-JSON qualification projection output.`n$inventoryText"
    }

    if (
        [string]$inventory.kind -ne 'server' -or
        [string]$inventory.server -ne 'procedure-qualification-projection'
    ) {
        throw 'Unexpected 1MCP inspect payload for procedure qualification projection.'
    }

    return @($inventory.tools | ForEach-Object { [string]$_.tool } | Sort-Object)
}

if (-not (Test-Path -LiteralPath $profileConfig -PathType Leaf)) {
    throw "Procedure qualification profile config is missing: $profileConfig"
}
if (-not (Test-Path -LiteralPath $qualificationEntry -PathType Leaf)) {
    throw "Procedure qualification projection is missing: $qualificationEntry"
}

$resolvedRoot = Resolve-SafeFilesRoot -Path $FilesRoot
$resolvedStateRoot = Resolve-StateRoot -Path $StateRoot
$null = Get-SemanticProjectionEntryPath -RepoRoot $repoRoot -EnsureDependencies

$managedEnv = @(
    'CHAT_LOCAL_FILES_ROOT',
    'CHAT_PROCEDURE_STATE_ROOT',
    'CHAT_PROCEDURE_ALLOW_CANDIDATE',
    'CHAT_PROCEDURE_QUALIFICATION_ENTRY'
)
$oldEnv = @{}
foreach ($name in $managedEnv) {
    $oldEnv[$name] = if (Test-Path "Env:$name") { [Environment]::GetEnvironmentVariable($name, 'Process') } else { $null }
}

try {
    $env:CHAT_LOCAL_FILES_ROOT = $resolvedRoot
    $env:CHAT_PROCEDURE_STATE_ROOT = $resolvedStateRoot
    $env:CHAT_PROCEDURE_ALLOW_CANDIDATE = $qualificationAdmission
    $env:CHAT_PROCEDURE_QUALIFICATION_ENTRY = $qualificationEntry

    & $stopProfiles

    Write-Host "FILES_ROOT=$resolvedRoot" -ForegroundColor Yellow
    Write-Host "PROCEDURE_STATE_ROOT=$resolvedStateRoot" -ForegroundColor Yellow
    Write-Host "PROCEDURE_QUALIFICATION_ENTRY=$qualificationEntry" -ForegroundColor DarkGray

    & $startBridge `
        -Port $Port `
        -ConfigPath $profileConfig `
        -OneMcpPackage $stablePkg `
        -HealthServerName 'procedure-qualification-projection' `
        -ReadyTimeoutSeconds $ReadyTimeoutSeconds

    $baseUrl = "http://127.0.0.1:$Port"
    $tools = @(Get-QualificationToolNames -BaseUrl $baseUrl)
    $expected = @(
        'procedure_run',
        'web_interact',
        'web_observe',
        'web_open',
        'workspace_read',
        'workspace_write'
    )

    if (($tools -join "`n") -ne ($expected -join "`n")) {
        throw "Procedure qualification surface drifted. Expected: $($expected -join ', '); actual: $($tools -join ', ')"
    }

    Write-Host 'CHAT_PROFILE_STATUS=ready' -ForegroundColor Green
    Write-Host 'CHAT_PROFILE=procedure-qualification'
    Write-Host "ONE_MCP=$stablePkg"
    Write-Host "MCP_URL=$baseUrl/mcp"
    Write-Host 'SEMANTIC_TOOL_COUNT=5'
    Write-Host 'PROCEDURE_TOOL_COUNT=1'
    Write-Host 'TOTAL_TOOL_COUNT=6'
}
catch {
    & npx.cmd -y $stablePkg serve --config $profileConfig --stop *> $null
    throw
}
finally {
    foreach ($name in $managedEnv) {
        if ($null -eq $oldEnv[$name]) {
            Remove-Item "Env:$name" -ErrorAction SilentlyContinue
        }
        else {
            [Environment]::SetEnvironmentVariable($name, [string]$oldEnv[$name], 'Process')
        }
    }
}
