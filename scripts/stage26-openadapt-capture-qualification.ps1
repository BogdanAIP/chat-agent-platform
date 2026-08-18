[CmdletBinding()]
param(
    [string]$OutputRoot = (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage26\capture-qualification'),
    [int]$InteractionTimeoutSeconds = 240,
    [switch]$KeepEnvironment
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Flag {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [AllowNull()]$Value
    )
    $rendered = if ($null -eq $Value) { '<null>' } else { [string]$Value }
    Write-Host ("{0}={1}" -f $Name, $rendered)
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList,
        [Parameter(Mandatory = $true)][string]$Label
    )
    & $FilePath @ArgumentList
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "$Label failed with exit code $exitCode"
    }
}

function Assert-FileSha256 {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Expected,
        [Parameter(Mandatory = $true)][string]$Label
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label is missing: $Path"
    }
    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    $expectedLower = $Expected.ToLowerInvariant()
    if ($actual -ne $expectedLower) {
        throw "$Label SHA256 mismatch: expected $expectedLower, got $actual"
    }
}

function Start-ExactProcess {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList
    )
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $FilePath
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $false
    foreach ($arg in $ArgumentList) {
        [void]$psi.ArgumentList.Add([string]$arg)
    }
    $process = [System.Diagnostics.Process]::Start($psi)
    if ($null -eq $process) {
        throw "Failed to start qualification-owned process: $FilePath"
    }
    return $process
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$lockPath = Join-Path $repoRoot 'config\stage26-openadapt-lock.json'
$driverPath = Join-Path $PSScriptRoot 'stage26-openadapt-capture-driver.py'
$fixturePath = Join-Path $PSScriptRoot 'stage26-windows-capture-fixture.ps1'

foreach ($required in @($lockPath, $driverPath, $fixturePath)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required Stage 26.1B asset is missing: $required"
    }
}

$lock = Get-Content -LiteralPath $lockPath -Raw -Encoding utf8 | ConvertFrom-Json
if ([int]$lock.schema_version -ne 1) {
    throw "Unsupported OpenAdapt lock schema: $($lock.schema_version)"
}
$flow = $lock.upstreams.openadapt_flow
$capture = $lock.upstreams.openadapt_capture
$desktop = $lock.upstreams.openadapt_desktop
$ffmpegAsset = $lock.qualification_assets.ffmpeg_windows_x86_64
$requiredPython = [string]$lock.python.required_major_minor

if ($null -eq $ffmpegAsset) {
    throw 'Pinned Windows FFmpeg qualification asset is missing from the OpenAdapt lock.'
}
if ([string]$ffmpegAsset.source_commit -ne [string]$desktop.commit) {
    throw 'FFmpeg qualification asset source commit drifted from the pinned OpenAdapt Desktop manifest.'
}
foreach ($shaField in @('archive_sha256', 'ffmpeg_sha256', 'ffprobe_sha256')) {
    if (-not ([string]$ffmpegAsset.$shaField -match '^[0-9a-f]{64}$')) {
        throw "Invalid FFmpeg qualification SHA field: $shaField"
    }
}

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$runDir = Join-Path $OutputRoot "capture-$timestamp"
$venvDir = Join-Path $runDir 'venv'
$ffmpegArchivePath = Join-Path $runDir 'openadapt-ffmpeg-runtime.zip'
$ffmpegRoot = Join-Path $runDir 'ffmpeg-runtime'
$fixtureStatePath = Join-Path $runDir 'fixture-state.json'
$donePath = Join-Path $runDir 'fixture-done.txt'
$recorderReadyPath = Join-Path $runDir 'recorder-ready.txt'
$closePath = Join-Path $runDir 'fixture-close.txt'
$driverResultPath = Join-Path $runDir 'driver-result.json'
$resultPath = Join-Path $runDir 'result.json'
$pinProbePath = Join-Path $runDir 'pin-probe.py'
$windowTitle = "Chat Agent Platform Stage 26.1B Capture Fixture $timestamp"

New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$chromeBefore = @(Get-Process chrome -ErrorAction SilentlyContinue).Count
$fixtureProcess = $null
$fixtureKilled = $false
$driverExit = $null
$driverResult = $null

$result = [ordered]@{
    schema_version = 1
    created_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    project_head = $null
    required_python = $requiredPython
    python_version = $null
    flow_expected_commit = [string]$flow.commit
    flow_installed_commit = $null
    flow_installed_version = $null
    capture_expected_commit = [string]$capture.commit
    capture_installed_commit = $null
    capture_installed_version = $null
    ffmpeg_source_commit = [string]$ffmpegAsset.source_commit
    ffmpeg_runtime_version = [string]$ffmpegAsset.runtime_version
    ffmpeg_archive_sha256 = [string]$ffmpegAsset.archive_sha256
    ffmpeg_binary_sha256 = [string]$ffmpegAsset.ffmpeg_sha256
    ffprobe_binary_sha256 = [string]$ffmpegAsset.ffprobe_sha256
    ffmpeg_runtime_pass = $false
    ffmpeg_version_line = $null
    ffprobe_version_line = $null
    window_title = $windowTitle
    fixture_pid = $null
    fixture_killed = $false
    fixture_cleanup_pass = $false
    driver_exit_code = $null
    driver_pass = $false
    driver_error = $null
    driver_traceback = $null
    raw_capture_dir = $null
    recording_dir = $null
    bundle_dir = $null
    raw_action_count = $null
    raw_action_types = $null
    raw_structural_action_count = $null
    foreign_structural_window_count = $null
    flow_event_kinds = $null
    structural_event_count = $null
    video_evidence_pass = $null
    window_scope_pass = $null
    foreign_structural_window_pass = $null
    required_kinds_pass = $null
    expected_text_pass = $null
    expected_key_pass = $null
    uia_evidence_pass = $null
    fixture_sequence_pass = $null
    compile_pass = $null
    compiled_step_count = $null
    compiled_structural_count = $null
    compiled_surface = $null
    surface_contract_pass = $null
    native_windows_replay_claimed = $null
    replay_execution = $null
    bounded_replay_refusal = $null
    raw_artifact_containment_pass = $false
    chrome_process_count_before = $chromeBefore
    chrome_process_count_after = $null
    chrome_survival_pass = $false
    environment_kept = [bool]$KeepEnvironment
    result_dir = $runDir
    error = $null
}

try {
    $projectHead = (& git.exe -C $repoRoot rev-parse HEAD 2>$null | Select-Object -Last 1).Trim()
    $result.project_head = $projectHead

    $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -eq $pyLauncher) {
        throw 'Windows Python launcher py.exe is required.'
    }
    $pythonProbe = & $pyLauncher.Source "-$requiredPython" -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python $requiredPython is not available through py.exe."
    }
    $pythonVersion = (($pythonProbe | Select-Object -Last 1) -as [string]).Trim()
    if (-not $pythonVersion.StartsWith("$requiredPython.")) {
        throw "Resolved Python $pythonVersion does not match $requiredPython.x"
    }
    $result.python_version = $pythonVersion

    Invoke-Checked -FilePath $pyLauncher.Source -ArgumentList @("-$requiredPython", '-m', 'venv', $venvDir) -Label 'Create Stage 26.1B venv'
    $pythonExe = Join-Path $venvDir 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
        throw "Qualification venv Python was not created: $pythonExe"
    }

    $captureSpec = "openadapt-capture @ git+https://github.com/$($capture.repository).git@$($capture.commit)"
    $flowSpec = "openadapt-flow[windows] @ git+https://github.com/$($flow.repository).git@$($flow.commit)"

    Invoke-Checked -FilePath $pythonExe -ArgumentList @(
        '-m', 'pip', 'install', '--disable-pip-version-check', '--no-input', $captureSpec
    ) -Label 'Install pinned openadapt-capture'
    Invoke-Checked -FilePath $pythonExe -ArgumentList @(
        '-m', 'pip', 'install', '--disable-pip-version-check', '--no-input', $flowSpec
    ) -Label 'Install pinned openadapt-flow[windows]'

    $pinProbe = @'
import json
from importlib import metadata

def info(name):
    dist = metadata.distribution(name)
    direct = json.loads(dist.read_text('direct_url.json') or '{}')
    return {
        'version': metadata.version(name),
        'commit': (direct.get('vcs_info') or {}).get('commit_id'),
    }
print(json.dumps({'flow': info('openadapt-flow'), 'capture': info('openadapt-capture')}))
'@
    Set-Content -LiteralPath $pinProbePath -Value $pinProbe -Encoding utf8
    $pinOutput = & $pythonExe $pinProbePath 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw 'Pinned OpenAdapt direct_url probe failed.'
    }
    $pin = (($pinOutput | Select-Object -Last 1) -as [string]) | ConvertFrom-Json
    $result.flow_installed_commit = [string]$pin.flow.commit
    $result.flow_installed_version = [string]$pin.flow.version
    $result.capture_installed_commit = [string]$pin.capture.commit
    $result.capture_installed_version = [string]$pin.capture.version

    if ($result.flow_installed_commit -ne [string]$flow.commit -or $result.flow_installed_version -ne [string]$flow.declared_version) {
        throw "Flow pin mismatch: $($result.flow_installed_version) / $($result.flow_installed_commit)"
    }
    if ($result.capture_installed_commit -ne [string]$capture.commit -or $result.capture_installed_version -ne [string]$capture.declared_version) {
        throw "Capture pin mismatch: $($result.capture_installed_version) / $($result.capture_installed_commit)"
    }

    Write-Host ''
    Write-Host '===== PROVISION PINNED OPENADAPT FFMPEG =====' -ForegroundColor Cyan
    Invoke-WebRequest -Uri ([string]$ffmpegAsset.url) -OutFile $ffmpegArchivePath
    Assert-FileSha256 -Path $ffmpegArchivePath -Expected ([string]$ffmpegAsset.archive_sha256) -Label 'OpenAdapt FFmpeg archive'
    Expand-Archive -LiteralPath $ffmpegArchivePath -DestinationPath $ffmpegRoot -Force

    $ffmpegExe = Join-Path $ffmpegRoot ([string]$ffmpegAsset.ffmpeg_relative_path)
    $ffprobeExe = Join-Path $ffmpegRoot ([string]$ffmpegAsset.ffprobe_relative_path)
    Assert-FileSha256 -Path $ffmpegExe -Expected ([string]$ffmpegAsset.ffmpeg_sha256) -Label 'OpenAdapt ffmpeg.exe'
    Assert-FileSha256 -Path $ffprobeExe -Expected ([string]$ffmpegAsset.ffprobe_sha256) -Label 'OpenAdapt ffprobe.exe'

    $ffmpegVersionOutput = & $ffmpegExe -version 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Pinned ffmpeg -version probe failed.' }
    $ffprobeVersionOutput = & $ffprobeExe -version 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Pinned ffprobe -version probe failed.' }
    $result.ffmpeg_version_line = [string]($ffmpegVersionOutput | Select-Object -First 1)
    $result.ffprobe_version_line = [string]($ffprobeVersionOutput | Select-Object -First 1)
    if ($result.ffmpeg_version_line -notmatch 'ffmpeg version 8\.1\.2') {
        throw "Unexpected pinned FFmpeg version output: $($result.ffmpeg_version_line)"
    }
    if ($result.ffprobe_version_line -notmatch 'ffprobe version 8\.1\.2') {
        throw "Unexpected pinned FFprobe version output: $($result.ffprobe_version_line)"
    }

    $buildConf = (& $ffmpegExe -hide_banner -buildconf 2>&1 | Out-String)
    foreach ($flag in @('--disable-gpl', '--disable-nonfree', '--disable-version3', '--disable-network')) {
        if ($buildConf -notmatch [regex]::Escape($flag)) {
            throw "Pinned FFmpeg build is missing required property $flag"
        }
    }
    $encoders = (& $ffmpegExe -hide_banner -encoders 2>&1 | Out-String)
    foreach ($encoder in @('mpeg4', 'png')) {
        if ($encoders -notmatch "(?m)^.*\b$([regex]::Escape($encoder))\b") {
            throw "Pinned FFmpeg build is missing required encoder $encoder"
        }
    }
    $muxers = (& $ffmpegExe -hide_banner -muxers 2>&1 | Out-String)
    foreach ($muxer in @('mp4', 'image2pipe')) {
        if ($muxers -notmatch "(?m)^.*\b$([regex]::Escape($muxer))\b") {
            throw "Pinned FFmpeg build is missing required muxer $muxer"
        }
    }
    $result.ffmpeg_runtime_pass = $true

    Write-Host ''
    Write-Host '===== STAGE 26.1B HUMAN INPUT FIXTURE =====' -ForegroundColor Cyan
    Write-Host 'Откроется отдельное тестовое окно. Дождитесь READY внутри окна.' -ForegroundColor Yellow
    Write-Host 'После READY выполните в нём шаги 1→5 и не переключайтесь на другие окна до DONE.' -ForegroundColor Yellow
    Write-Host 'Ввод должен быть физическим: OpenAdapt намеренно отбрасывает injected input.' -ForegroundColor Yellow
    Write-Host 'Обычный Chrome и рабочие приложения тест не закрывает и не использует.' -ForegroundColor Yellow

    $pwshCommand = Get-Command pwsh.exe -ErrorAction Stop
    $fixtureArgs = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-STA',
        '-File', $fixturePath,
        '-StatePath', $fixtureStatePath,
        '-DonePath', $donePath,
        '-RecorderReadyPath', $recorderReadyPath,
        '-ClosePath', $closePath,
        '-WindowTitle', $windowTitle
    )
    $fixtureProcess = Start-ExactProcess -FilePath $pwshCommand.Source -ArgumentList $fixtureArgs
    $result.fixture_pid = $fixtureProcess.Id

    $fixtureDeadline = (Get-Date).AddSeconds(30)
    while (-not (Test-Path -LiteralPath $fixtureStatePath -PathType Leaf)) {
        $fixtureProcess.Refresh()
        if ($fixtureProcess.HasExited) {
            throw "Fixture process exited before creating state (exit $($fixtureProcess.ExitCode))."
        }
        if ((Get-Date) -gt $fixtureDeadline) {
            throw 'Fixture window did not initialize before timeout.'
        }
        Start-Sleep -Milliseconds 200
    }

    $driverArgs = @(
        $driverPath,
        '--run-dir', $runDir,
        '--window-title', $windowTitle,
        '--fixture-state', $fixtureStatePath,
        '--done', $donePath,
        '--recorder-ready', $recorderReadyPath,
        '--ffmpeg', $ffmpegExe,
        '--ffprobe', $ffprobeExe,
        '--timeout-seconds', [string]$InteractionTimeoutSeconds
    )
    & $pythonExe @driverArgs
    $driverExit = $LASTEXITCODE
    $result.driver_exit_code = $driverExit

    if (-not (Test-Path -LiteralPath $driverResultPath -PathType Leaf)) {
        throw "Driver result was not written: $driverResultPath"
    }
    $driverResult = Get-Content -LiteralPath $driverResultPath -Raw -Encoding utf8 | ConvertFrom-Json
    $result.driver_pass = [bool]$driverResult.pass
    $result.driver_error = $driverResult.error
    $result.driver_traceback = $driverResult.traceback

    foreach ($field in @(
        'raw_capture_dir', 'recording_dir', 'bundle_dir',
        'raw_action_count', 'raw_action_types', 'raw_structural_action_count',
        'foreign_structural_window_count', 'flow_event_kinds',
        'structural_event_count', 'video_evidence_pass', 'window_scope_pass',
        'foreign_structural_window_pass', 'required_kinds_pass',
        'expected_text_pass', 'expected_key_pass', 'uia_evidence_pass',
        'fixture_sequence_pass', 'compile_pass', 'compiled_step_count',
        'compiled_structural_count', 'compiled_surface', 'surface_contract_pass',
        'native_windows_replay_claimed', 'replay_execution',
        'bounded_replay_refusal'
    )) {
        $result[$field] = $driverResult.$field
    }

    $containmentRoot = [System.IO.Path]::GetFullPath($runDir).TrimEnd('\') + '\'
    $contained = $true
    foreach ($pathValue in @($driverResult.raw_capture_dir, $driverResult.recording_dir, $driverResult.bundle_dir)) {
        if ([string]::IsNullOrWhiteSpace([string]$pathValue)) {
            $contained = $false
            continue
        }
        $full = [System.IO.Path]::GetFullPath([string]$pathValue)
        if (-not $full.StartsWith($containmentRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            $contained = $false
        }
    }
    $result.raw_artifact_containment_pass = $contained

    if ($driverExit -ne 0 -or -not [bool]$driverResult.pass) {
        $detail = if ($driverResult.error) { [string]$driverResult.error } else { "driver exit $driverExit" }
        throw "Stage 26.1B capture driver failed: $detail"
    }
    if (-not $contained) {
        throw 'Capture/recording/bundle escaped the qualification run directory.'
    }
}
catch {
    $result.error = $_.Exception.Message
}
finally {
    try {
        Set-Content -LiteralPath $closePath -Value 'CLOSE' -Encoding ascii -ErrorAction SilentlyContinue
    }
    catch {}

    if ($null -ne $fixtureProcess) {
        try {
            $fixtureProcess.Refresh()
            if (-not $fixtureProcess.HasExited) {
                [void]$fixtureProcess.WaitForExit(5000)
                $fixtureProcess.Refresh()
            }
            if (-not $fixtureProcess.HasExited) {
                # Kill only the exact qualification-owned fixture PID if its
                # graceful close marker failed. Never enumerate or kill user apps.
                $fixtureProcess.Kill($true)
                $fixtureKilled = $true
                [void]$fixtureProcess.WaitForExit(5000)
            }
        }
        catch {
            if ($null -eq $result.error) {
                $result.error = "Fixture cleanup failed: $($_.Exception.Message)"
            }
        }
    }
    $result.fixture_killed = $fixtureKilled
    $result.fixture_cleanup_pass = -not $fixtureKilled

    if (-not $KeepEnvironment) {
        foreach ($path in @($venvDir, $ffmpegRoot, $ffmpegArchivePath)) {
            if (Test-Path -LiteralPath $path) {
                Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }

    $chromeAfter = @(Get-Process chrome -ErrorAction SilentlyContinue).Count
    $result.chrome_process_count_after = $chromeAfter
    $result.chrome_survival_pass = [bool]($chromeBefore -eq 0 -or $chromeAfter -gt 0)

    $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $resultPath -Encoding utf8
}

Write-Host ''
Write-Host '===== STAGE 26.1B WINDOWS CAPTURE QUALIFICATION =====' -ForegroundColor Cyan
Write-Flag 'RESULT_PATH' $resultPath
Write-Flag 'PYTHON_VERSION' $result.python_version
Write-Flag 'FLOW_INSTALLED_COMMIT' $result.flow_installed_commit
Write-Flag 'FLOW_INSTALLED_VERSION' $result.flow_installed_version
Write-Flag 'CAPTURE_INSTALLED_COMMIT' $result.capture_installed_commit
Write-Flag 'CAPTURE_INSTALLED_VERSION' $result.capture_installed_version
Write-Flag 'FFMPEG_RUNTIME_VERSION' $result.ffmpeg_runtime_version
Write-Flag 'FFMPEG_RUNTIME_PASS' $result.ffmpeg_runtime_pass
Write-Flag 'DRIVER_PASS' $result.driver_pass
Write-Flag 'RAW_ACTION_COUNT' $result.raw_action_count
Write-Flag 'RAW_ACTION_TYPES' ($result.raw_action_types -join ',')
Write-Flag 'RAW_STRUCTURAL_ACTION_COUNT' $result.raw_structural_action_count
Write-Flag 'FOREIGN_STRUCTURAL_WINDOW_COUNT' $result.foreign_structural_window_count
Write-Flag 'FLOW_EVENT_KINDS' ($result.flow_event_kinds -join ',')
Write-Flag 'STRUCTURAL_EVENT_COUNT' $result.structural_event_count
Write-Flag 'VIDEO_EVIDENCE_PASS' $result.video_evidence_pass
Write-Flag 'WINDOW_SCOPE_PASS' $result.window_scope_pass
Write-Flag 'FOREIGN_STRUCTURAL_WINDOW_PASS' $result.foreign_structural_window_pass
Write-Flag 'REQUIRED_KINDS_PASS' $result.required_kinds_pass
Write-Flag 'EXPECTED_TEXT_PASS' $result.expected_text_pass
Write-Flag 'EXPECTED_KEY_PASS' $result.expected_key_pass
Write-Flag 'UIA_EVIDENCE_PASS' $result.uia_evidence_pass
Write-Flag 'FIXTURE_SEQUENCE_PASS' $result.fixture_sequence_pass
Write-Flag 'COMPILE_PASS' $result.compile_pass
Write-Flag 'COMPILED_STEP_COUNT' $result.compiled_step_count
Write-Flag 'COMPILED_STRUCTURAL_COUNT' $result.compiled_structural_count
Write-Flag 'COMPILED_SURFACE' $result.compiled_surface
Write-Flag 'SURFACE_CONTRACT_PASS' $result.surface_contract_pass
Write-Flag 'NATIVE_WINDOWS_REPLAY_CLAIMED' $result.native_windows_replay_claimed
Write-Flag 'REPLAY_EXECUTION' $result.replay_execution
Write-Flag 'BOUNDED_REPLAY_REFUSAL' $result.bounded_replay_refusal
Write-Flag 'RAW_ARTIFACT_CONTAINMENT_PASS' $result.raw_artifact_containment_pass
Write-Flag 'CHROME_PROCESS_COUNT_BEFORE' $result.chrome_process_count_before
Write-Flag 'CHROME_PROCESS_COUNT_AFTER' $result.chrome_process_count_after
Write-Flag 'CHROME_SURVIVAL_PASS' $result.chrome_survival_pass
Write-Flag 'FIXTURE_KILLED' $result.fixture_killed
Write-Flag 'FIXTURE_CLEANUP_PASS' $result.fixture_cleanup_pass
Write-Flag 'DRIVER_ERROR' $result.driver_error
Write-Flag 'ERROR' $result.error

$accepted = [bool](
    $result.ffmpeg_runtime_pass -and
    $result.driver_pass -and
    $result.raw_artifact_containment_pass -and
    $result.chrome_survival_pass -and
    $result.fixture_cleanup_pass -and
    $null -eq $result.error
)
if ($accepted) {
    Write-Flag 'STAGE26_1B_CAPTURE_RESULT' 'PASSED'
    exit 0
}
Write-Flag 'STAGE26_1B_CAPTURE_RESULT' 'FAILED'
exit 1
