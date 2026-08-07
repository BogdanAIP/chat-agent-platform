param(
    [switch]$SkipPythonOracle,
    [switch]$SkipRelease
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $repoRoot
try {
    & cargo fmt --all -- --check
    if ($LASTEXITCODE -ne 0) { throw 'cargo fmt failed' }

    & cargo clippy --workspace --all-targets -- -D warnings
    if ($LASTEXITCODE -ne 0) { throw 'cargo clippy failed' }

    & cargo test --workspace
    if ($LASTEXITCODE -ne 0) { throw 'cargo test failed' }

    $tokens = $null
    $parseErrors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        (Join-Path $PSScriptRoot 'verify-reaper-stage12.ps1'),
        [ref]$tokens,
        [ref]$parseErrors
    ) | Out-Null
    if ($parseErrors.Count -ne 0) {
        $details = ($parseErrors | ForEach-Object Message) -join '; '
        throw "Stage 12 REAPER acceptance script has PowerShell syntax errors: $details"
    }

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
        powershell = 'stage12-acceptance-syntax'
        python_oracle = if ($SkipPythonOracle) { 'skipped' } else { 'tests,parity' }
        release = if ($SkipRelease) { 'skipped' } else { 'built' }
    } | ConvertTo-Json
}
finally {
    Pop-Location
}
