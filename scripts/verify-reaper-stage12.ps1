param(
    [string]$ProjectId = 'demo',
    [switch]$SkipBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$binary = Join-Path $repoRoot 'target/release/agent-platform.exe'
$acceptanceRoot = Join-Path $repoRoot ('runtime/acceptance/stage12-' + [guid]::NewGuid().ToString('N'))
$fixture = Join-Path $acceptanceRoot 'stage12-fixture.wav'
$evidencePath = Join-Path $repoRoot 'runtime/stage12-acceptance.json'

function Invoke-AgentJson {
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments,
        [Parameter(Mandatory)]
        [string]$Context
    )

    $text = (& $binary @Arguments | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "$Context failed with exit code $LASTEXITCODE"
    }
    if ([string]::IsNullOrWhiteSpace($text)) {
        throw "$Context returned no JSON"
    }
    try {
        return $text | ConvertFrom-Json
    }
    catch {
        throw "$Context returned invalid JSON: $text"
    }
}

New-Item -ItemType Directory -Path $acceptanceRoot -Force | Out-Null
Push-Location $repoRoot
try {
    if (-not $SkipBuild) {
        & cargo build --workspace --release
        if ($LASTEXITCODE -ne 0) { throw 'release build failed' }
    }
    if (-not (Test-Path -LiteralPath $binary -PathType Leaf)) {
        throw "release binary not found: $binary"
    }
    if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
        throw 'ffmpeg is unavailable on PATH'
    }

    $probe = Invoke-AgentJson -Context 'REAPER probe' -Arguments @(
        '--repo-root', $repoRoot,
        'reaper-probe'
    )
    if ($probe.status -ne 'available') {
        throw "REAPER probe did not report available status: $($probe.status)"
    }

    & ffmpeg -y -hide_banner -loglevel error -f lavfi -i 'sine=frequency=997:sample_rate=48000:duration=2' -ac 2 $fixture
    if ($LASTEXITCODE -ne 0) { throw 'FFmpeg fixture generation failed' }
    if (-not (Test-Path -LiteralPath $fixture -PathType Leaf)) {
        throw 'FFmpeg did not create the Stage 12 fixture WAV'
    }

    $render = Invoke-AgentJson -Context 'REAPER E2E render' -Arguments @(
        '--repo-root', $repoRoot,
        'reaper-render',
        '--project-id', $ProjectId,
        '--file', $fixture,
        '--track-name', 'Stage 12 Acceptance',
        '--marker-name', 'Acceptance',
        '--marker-seconds', '0.5',
        '--render-sample-rate-hz', '48000',
        '--data-class', 'project'
    )
    if ($render.status -ne 'success') {
        throw "REAPER E2E did not return success: $($render.status)"
    }

    $projectArtifactId = [string]$render.result.project_artifact.artifact_id
    $projectSha256 = [string]$render.result.project_artifact.sha256
    $renderArtifactId = [string]$render.result.render_artifact.artifact_id
    $renderSha256 = [string]$render.result.render_artifact.sha256
    if ([string]::IsNullOrWhiteSpace($projectArtifactId) -or [string]::IsNullOrWhiteSpace($renderArtifactId)) {
        throw 'REAPER E2E did not return both project and render artifact IDs'
    }

    $inspection = Invoke-AgentJson -Context 'render artifact inspection' -Arguments @(
        '--repo-root', $repoRoot,
        'inspect-artifact',
        '--project-id', $ProjectId,
        '--artifact-id', $renderArtifactId
    )
    if ($inspection.status -ne 'success') {
        throw "render artifact inspection did not return success: $($inspection.status)"
    }
    if ([int]$inspection.result.sample_rate_hz -ne 48000) {
        throw "render sample rate mismatch: $($inspection.result.sample_rate_hz)"
    }
    if ([double]$inspection.result.duration_seconds -le 0) {
        throw 'render duration must be positive'
    }

    $diagnose = Invoke-AgentJson -Context 'project diagnose' -Arguments @(
        '--repo-root', $repoRoot,
        'diagnose',
        '--project-id', $ProjectId
    )
    $manifestPath = Join-Path ([string]$diagnose.artifact_root) 'manifest.json'
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw "artifact manifest not found: $manifestPath"
    }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json -AsHashtable
    if (-not $manifest.ContainsKey($projectArtifactId)) {
        throw "project artifact is not registered: $projectArtifactId"
    }
    if (-not $manifest.ContainsKey($renderArtifactId)) {
        throw "render artifact is not registered: $renderArtifactId"
    }
    if ([string]$manifest[$projectArtifactId].sha256 -ne $projectSha256) {
        throw 'project artifact SHA-256 does not match the manifest'
    }
    if ([string]$manifest[$renderArtifactId].sha256 -ne $renderSha256) {
        throw 'render artifact SHA-256 does not match the manifest'
    }

    $evidence = [ordered]@{
        contract_version = 'stage12-acceptance-v1'
        status = 'success'
        verified_at = (Get-Date).ToUniversalTime().ToString('o')
        project_id = $ProjectId
        execution_path = [string]$probe.execution_path
        reaper_executable = [string]$probe.executable
        source = [ordered]@{
            generated_fixture = '997 Hz stereo WAV, 48 kHz, 2 s'
        }
        project_artifact = [ordered]@{
            artifact_id = $projectArtifactId
            sha256 = $projectSha256
        }
        render_artifact = [ordered]@{
            artifact_id = $renderArtifactId
            sha256 = $renderSha256
            sample_rate_hz = [int]$inspection.result.sample_rate_hz
            duration_seconds = [double]$inspection.result.duration_seconds
            integrated_lufs = $inspection.result.integrated_lufs
            true_peak_dbtp = $inspection.result.true_peak_dbtp
        }
    }
    $evidenceJson = $evidence | ConvertTo-Json -Depth 8
    New-Item -ItemType Directory -Path (Split-Path $evidencePath -Parent) -Force | Out-Null
    Set-Content -LiteralPath $evidencePath -Value $evidenceJson -Encoding utf8
    $evidenceJson
}
finally {
    Pop-Location
    if (Test-Path -LiteralPath $acceptanceRoot) {
        Remove-Item -LiteralPath $acceptanceRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
