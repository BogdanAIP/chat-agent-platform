$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$stablePkg = '@1mcp/agent@0.34.4'
$adaptivePkg = '@1mcp/agent@0.35.0-beta.3'
$runtimeHelper = Join-Path $PSScriptRoot 'semantic-projection-runtime.ps1'

. $runtimeHelper

$runtimes = @(
    @{ Config = (Join-Path $repoRoot 'runtime\mcp.json'); Package = $stablePkg },
    @{ Config = (Join-Path $repoRoot 'runtime\chat-profiles\files-readonly\mcp.json'); Package = $stablePkg },
    @{ Config = (Join-Path $repoRoot 'runtime\chat-profiles\browser-isolated\mcp.json'); Package = $stablePkg },
    @{ Config = (Join-Path $repoRoot 'runtime\chat-profiles\semantic\mcp.json'); Package = $stablePkg },
    @{ Config = (Join-Path $repoRoot 'runtime\chat-profiles\adaptive\mcp.json'); Package = $adaptivePkg }
)

$hadEntry = Test-Path Env:CHAT_SEMANTIC_PROJECTION_ENTRY
$oldEntry = if ($hadEntry) { $env:CHAT_SEMANTIC_PROJECTION_ENTRY } else { $null }
$hadFilesRoot = Test-Path Env:CHAT_LOCAL_FILES_ROOT
$oldFilesRoot = if ($hadFilesRoot) { $env:CHAT_LOCAL_FILES_ROOT } else { $null }

try {
    if (-not $hadEntry) {
        $env:CHAT_SEMANTIC_PROJECTION_ENTRY = Get-SemanticProjectionEntryPath -RepoRoot $repoRoot
    }
    if (-not $hadFilesRoot) {
        # `serve --stop` never starts the backend; this non-broad placeholder
        # only satisfies config interpolation for the semantic Runtime Scope.
        $env:CHAT_LOCAL_FILES_ROOT = $repoRoot
    }

    foreach ($runtime in $runtimes) {
        $config = [string]$runtime.Config
        if (-not (Test-Path -LiteralPath $config)) { continue }

        & npx.cmd -y ([string]$runtime.Package) serve --config $config --stop *> $null
        $stopCode = $LASTEXITCODE
        if ($stopCode -notin @(0, 3, 7)) {
            throw "Unable to stop 1MCP Runtime Scope for $config (exit $stopCode)."
        }
    }
}
finally {
    if ($hadEntry) {
        $env:CHAT_SEMANTIC_PROJECTION_ENTRY = $oldEntry
    }
    else {
        Remove-Item Env:CHAT_SEMANTIC_PROJECTION_ENTRY -ErrorAction SilentlyContinue
    }

    if ($hadFilesRoot) {
        $env:CHAT_LOCAL_FILES_ROOT = $oldFilesRoot
    }
    else {
        Remove-Item Env:CHAT_LOCAL_FILES_ROOT -ErrorAction SilentlyContinue
    }
}

Write-Host 'CHAT_PROFILE_STATUS=stopped' -ForegroundColor Green
