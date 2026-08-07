param(
    [string]$MediaPath
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$generated = $false
$placeholder = $null

if (-not $MediaPath) {
    $placeholder = [System.IO.Path]::GetTempFileName()
    $MediaPath = "$placeholder.wav"
    Remove-Item -LiteralPath $placeholder
    $generated = $true
    & ffmpeg -hide_banner -loglevel error -f lavfi -i 'sine=frequency=440:sample_rate=48000:duration=1.25' -ac 2 $MediaPath
    if ($LASTEXITCODE -ne 0) { throw 'FFmpeg could not create the parity fixture' }
}

try {
    $pythonJson = & python -m agent_platform inspect --project-id demo --file $MediaPath
    if ($LASTEXITCODE -ne 0) { throw 'Python oracle failed' }
    $rustJson = & cargo run --quiet --manifest-path (Join-Path $repoRoot 'Cargo.toml') -- --repo-root $repoRoot inspect --project-id demo --file $MediaPath
    if ($LASTEXITCODE -ne 0) { throw 'Rust core failed' }

    $python = $pythonJson | ConvertFrom-Json
    $rust = $rustJson | ConvertFrom-Json
    $checks = [ordered]@{
        status = $python.status -eq $rust.status
        sample_rate_hz = $python.result.sample_rate_hz -eq $rust.result.sample_rate_hz
        channels = $python.result.channels -eq $rust.result.channels
        codec = $python.result.codec -eq $rust.result.codec
        duration_tolerance = [Math]::Abs($python.result.duration_seconds - $rust.result.duration_seconds) -le 0.001
        lufs_tolerance = [Math]::Abs($python.result.integrated_lufs - $rust.result.integrated_lufs) -le 0.1
        true_peak_tolerance = [Math]::Abs($python.result.true_peak_dbtp - $rust.result.true_peak_dbtp) -le 0.1
        rust_validated = $rust.provenance.validated -eq $true
    }
    $failed = @($checks.GetEnumerator() | Where-Object { -not $_.Value })
    $summary = [ordered]@{
        status = if ($failed.Count -eq 0) { 'success' } else { 'error' }
        media = (Resolve-Path -LiteralPath $MediaPath).Path
        checks = $checks
        python = $python.result
        rust = $rust.result
    }
    $summary | ConvertTo-Json -Depth 6
    if ($failed.Count -ne 0) {
        throw "Parity checks failed: $($failed.Name -join ', ')"
    }
}
finally {
    if ($generated -and (Test-Path -LiteralPath $MediaPath)) {
        Remove-Item -LiteralPath $MediaPath
    }
}
