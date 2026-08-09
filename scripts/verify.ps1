param(
    [switch]$SkipPythonOracle,
    [switch]$SkipRelease
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Assert-PowerShellSyntax {
    param(
        [Parameter(Mandatory)] [string]$Path,
        [Parameter(Mandatory)] [string]$Label
    )
    $tokens = $null
    $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $Path,
        [ref]$tokens,
        [ref]$parseErrors
    ) | Out-Null
    if ($parseErrors.Count -ne 0) {
        $details = ($parseErrors | ForEach-Object Message) -join '; '
        throw "$Label has PowerShell syntax errors: $details"
    }
}

Push-Location $repoRoot
try {
    & cargo fmt --all -- --check
    if ($LASTEXITCODE -ne 0) { throw 'cargo fmt failed' }

    & cargo clippy --workspace --all-targets -- -D warnings
    if ($LASTEXITCODE -ne 0) { throw 'cargo clippy failed' }

    & cargo test --workspace
    if ($LASTEXITCODE -ne 0) { throw 'cargo test failed' }

    Assert-PowerShellSyntax `
        -Path (Join-Path $PSScriptRoot 'verify-reaper-stage12.ps1') `
        -Label 'Stage 12 REAPER acceptance script'
    Assert-PowerShellSyntax `
        -Path (Join-Path $PSScriptRoot 'deploy-stage4-yandex.ps1') `
        -Label 'Stage 4 Yandex deployment script'
    Assert-PowerShellSyntax `
        -Path (Join-Path $PSScriptRoot 'ensure-stage4-gateway-active.ps1') `
        -Label 'Stage 4 Yandex API Gateway recovery script'
    Assert-PowerShellSyntax `
        -Path (Join-Path $PSScriptRoot 'prepare-stage4-gpt-action.ps1') `
        -Label 'Stage 4 GPT Action ingress preparation script'
    Assert-PowerShellSyntax `
        -Path (Join-Path $PSScriptRoot 'prepare-relay-gpt-action.ps1') `
        -Label 'Provider-neutral Rust relay GPT Action preparation script'

    & python -m py_compile (Join-Path $PSScriptRoot 'matchering_adapter.py')
    if ($LASTEXITCODE -ne 0) { throw 'Stage 19 Matchering adapter syntax check failed' }

    if (-not $SkipPythonOracle) {
        & python -m unittest discover -s tests -v
        if ($LASTEXITCODE -ne 0) { throw 'Python oracle tests failed' }
        & (Join-Path $PSScriptRoot 'verify-parity.ps1') | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Rust/Python parity failed' }
    }

    if (-not $SkipRelease) {
        & cargo build --workspace --release
        if ($LASTEXITCODE -ne 0) { throw 'release build failed' }
    }

    [ordered]@{
        status = 'success'
        rust = 'fmt,clippy,tests'
        powershell = 'stage12-acceptance-syntax,stage4-yandex-deploy-syntax,stage4-gateway-recovery-syntax,stage4-gpt-action-prepare-syntax,relay-gpt-action-prepare-syntax'
        python_edge = 'stage19-matchering-adapter-syntax'
        python_oracle = if ($SkipPythonOracle) { 'skipped' } else { 'tests,parity' }
        release = if ($SkipRelease) { 'skipped' } else { 'built' }
    } | ConvertTo-Json
}
finally {
    Pop-Location
}
