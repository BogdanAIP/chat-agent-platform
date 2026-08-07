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
        python_oracle = if ($SkipPythonOracle) { 'skipped' } else { 'tests,parity' }
        release = if ($SkipRelease) { 'skipped' } else { 'built' }
    } | ConvertTo-Json
}
finally {
    Pop-Location
}

