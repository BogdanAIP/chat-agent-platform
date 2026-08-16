[CmdletBinding()]
param(
    [string]$FilesRoot,
    [string]$TunnelExe,
    [ValidateRange(5, 120)]
    [int]$ReadyTimeoutSeconds = 45,
    [switch]$KeepArtifacts
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtimeHelper = Join-Path $PSScriptRoot 'semantic-projection-runtime.ps1'
$directTest = Join-Path $repoRoot 'runtime\semantic-projection\tests\direct-tunnel-acceptance.mjs'

function ConvertTo-McpCommandPart {
    param([Parameter(Mandatory)] [string]$Value)

    # Match the official tunnel-client wrapper convention: values containing
    # spaces or Windows path separators are shell-quoted before being passed as
    # one --mcp-command string. The target paths are project/runtime paths and
    # are not expected to contain an apostrophe; reject that rare case rather
    # than generating ambiguous command text.
    if ($Value -match '^[A-Za-z0-9_/:=.,@%+-]+$') {
        return $Value
    }
    if ($Value.Contains("'")) {
        throw "Direct semantic MCP command path contains an unsupported apostrophe: $Value"
    }
    return "'$Value'"
}

function Get-ExitedProcessDiagnostic {
    param(
        [Parameter(Mandatory)] $Process,
        [Parameter(Mandatory)] $StdoutTask,
        [Parameter(Mandatory)] $StderrTask
    )

    $stdout = ($StdoutTask.GetAwaiter().GetResult() | Out-String).Trim()
    $stderr = ($StderrTask.GetAwaiter().GetResult() | Out-String).Trim()
    return (
        "exit_code={0}`n--- tunnel stdout ---`n{1}`n--- tunnel stderr ---`n{2}" -f
        $Process.ExitCode,
        $stdout,
        $stderr
    )
}

if (-not (Test-Path -LiteralPath $runtimeHelper -PathType Leaf)) {
    throw "Semantic runtime helper is missing: $runtimeHelper"
}
if (-not (Test-Path -LiteralPath $directTest -PathType Leaf)) {
    throw "Direct tunnel acceptance test is missing: $directTest"
}

if ([string]::IsNullOrWhiteSpace($TunnelExe)) {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\bin\tunnel-client.exe'),
        (Join-Path $repoRoot 'runtime\openai-tunnel-client\tunnel-client.exe')
    )
    $TunnelExe = @($candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1)
    if ($TunnelExe.Count -eq 1) {
        $TunnelExe = [string]$TunnelExe[0]
    }
    else {
        $TunnelExe = $null
    }
}

if ([string]::IsNullOrWhiteSpace($TunnelExe) -or -not (Test-Path -LiteralPath $TunnelExe -PathType Leaf)) {
    throw 'Official tunnel-client.exe was not found. Pass -TunnelExe or install Chat Agent Platform first.'
}
$TunnelExe = (Resolve-Path -LiteralPath $TunnelExe).Path

$node = (Get-Command node.exe -ErrorAction Stop).Source

. $runtimeHelper
$semanticEntry = Get-SemanticProjectionEntryPath -RepoRoot $repoRoot -EnsureDependencies

$ownsWorkspace = [string]::IsNullOrWhiteSpace($FilesRoot)
if ($ownsWorkspace) {
    $workspace = Join-Path ([System.IO.Path]::GetTempPath()) ('chat-direct-semantic-workspace-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $workspace | Out-Null
}
else {
    $workspace = (Resolve-Path -LiteralPath $FilesRoot).Path
    if (-not (Test-Path -LiteralPath $workspace -PathType Container)) {
        throw "FilesRoot must be an existing directory: $workspace"
    }
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('chat-direct-semantic-tunnel-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

$connectionFile = Join-Path $tempRoot 'connection.json'
$healthUrlFile = Join-Path $tempRoot 'health.url'
$mcpCommand = @(
    ConvertTo-McpCommandPart -Value $node
    ConvertTo-McpCommandPart -Value $semanticEntry
) -join ' '
$process = $null
$stdoutTask = $null
$stderrTask = $null
$startupWatch = [System.Diagnostics.Stopwatch]::StartNew()

try {
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $TunnelExe
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.Environment['CHAT_LOCAL_FILES_ROOT'] = $workspace

    foreach ($argument in @(
        'dev',
        'proxy',
        '--mcp-command', $mcpCommand,
        '--listen', '127.0.0.1:0',
        '--health-listen-addr', '127.0.0.1:0',
        '--health-url-file', $healthUrlFile,
        '--url-file', $connectionFile,
        '--readiness-timeout', "${ReadyTimeoutSeconds}s",
        '--response-timeout', "${ReadyTimeoutSeconds}s"
    )) {
        $startInfo.ArgumentList.Add([string]$argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    if (-not $process.Start()) {
        throw 'Could not start tunnel-client dev proxy.'
    }
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()

    $deadline = (Get-Date).AddSeconds($ReadyTimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if ($process.HasExited) {
            $diagnostic = Get-ExitedProcessDiagnostic -Process $process -StdoutTask $stdoutTask -StderrTask $stderrTask
            throw "tunnel-client dev proxy exited before readiness.`n$diagnostic"
        }
        if ((Test-Path -LiteralPath $connectionFile -PathType Leaf) -and (Test-Path -LiteralPath $healthUrlFile -PathType Leaf)) {
            $healthBase = (Get-Content -LiteralPath $healthUrlFile -Raw).Trim().TrimEnd('/')
            if (-not [string]::IsNullOrWhiteSpace($healthBase)) {
                try {
                    $ready = Invoke-WebRequest -Uri "$healthBase/readyz" -Method Get -TimeoutSec 2 -ErrorAction Stop
                    if ($ready.StatusCode -eq 200) {
                        break
                    }
                }
                catch {
                    # Startup is still converging.
                }
            }
        }
        Start-Sleep -Milliseconds 250
    }

    if ($process.HasExited) {
        $diagnostic = Get-ExitedProcessDiagnostic -Process $process -StdoutTask $stdoutTask -StderrTask $stderrTask
        throw "tunnel-client dev proxy exited during readiness.`n$diagnostic"
    }
    if (-not (Test-Path -LiteralPath $connectionFile -PathType Leaf)) {
        throw "Direct tunnel connection metadata was not written within $ReadyTimeoutSeconds seconds. MCP_COMMAND=$mcpCommand"
    }
    if (-not (Test-Path -LiteralPath $healthUrlFile -PathType Leaf)) {
        throw "Direct tunnel health URL was not written within $ReadyTimeoutSeconds seconds."
    }

    $healthBase = (Get-Content -LiteralPath $healthUrlFile -Raw).Trim().TrimEnd('/')
    $readyFinal = Invoke-WebRequest -Uri "$healthBase/readyz" -Method Get -TimeoutSec 3 -ErrorAction Stop
    if ($readyFinal.StatusCode -ne 200) {
        throw "Direct tunnel /readyz returned HTTP $($readyFinal.StatusCode)."
    }

    $connection = Get-Content -LiteralPath $connectionFile -Raw | ConvertFrom-Json
    $mcpUrl = [string]$connection.mcp_url
    if ($mcpUrl -notmatch '^http://127\.0\.0\.1:\d+/') {
        throw "Unexpected local dev-proxy MCP URL: $mcpUrl"
    }

    $startupWatch.Stop()
    $env:DIRECT_TUNNEL_MCP_URL = $mcpUrl
    $env:DIRECT_TUNNEL_WORKSPACE = $workspace

    $acceptanceWatch = [System.Diagnostics.Stopwatch]::StartNew()
    & $node $directTest
    $acceptanceExit = $LASTEXITCODE
    $acceptanceWatch.Stop()

    if ($acceptanceExit -ne 0) {
        throw "Direct semantic tunnel acceptance failed with exit code $acceptanceExit."
    }

    Write-Host "DIRECT_SEMANTIC_TUNNEL_EXE=$TunnelExe"
    Write-Host "DIRECT_SEMANTIC_WORKSPACE=$workspace"
    Write-Host "DIRECT_SEMANTIC_PROXY_URL=$mcpUrl"
    Write-Host "DIRECT_SEMANTIC_STARTUP_MS=$($startupWatch.ElapsedMilliseconds)"
    Write-Host "DIRECT_SEMANTIC_ACCEPTANCE_MS=$($acceptanceWatch.ElapsedMilliseconds)"
    Write-Host 'DIRECT_SEMANTIC_1MCP_USED=False'
    Write-Host 'DIRECT_SEMANTIC_TUNNEL=PASS' -ForegroundColor Green
}
finally {
    Remove-Item Env:DIRECT_TUNNEL_MCP_URL -ErrorAction SilentlyContinue
    Remove-Item Env:DIRECT_TUNNEL_WORKSPACE -ErrorAction SilentlyContinue

    if ($null -ne $process) {
        try {
            if (-not $process.HasExited) {
                $process.Kill($true)
                $process.WaitForExit(10000) | Out-Null
            }
            if ($null -ne $stdoutTask -and $stdoutTask.IsCompleted) {
                $unusedStdout = $stdoutTask.GetAwaiter().GetResult()
            }
            if ($null -ne $stderrTask -and $stderrTask.IsCompleted) {
                $unusedStderr = $stderrTask.GetAwaiter().GetResult()
            }
        }
        catch {
            Write-Warning "Could not stop direct tunnel test process cleanly: $($_.Exception.Message)"
        }
        finally {
            $process.Dispose()
        }
    }

    if (-not $KeepArtifacts) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
        if ($ownsWorkspace) {
            Remove-Item -LiteralPath $workspace -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    else {
        Write-Host "DIRECT_SEMANTIC_ARTIFACTS=$tempRoot"
    }
}
