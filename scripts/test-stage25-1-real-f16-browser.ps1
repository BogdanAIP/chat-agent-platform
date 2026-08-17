[CmdletBinding()]
param(
    [string]$ResultPath,
    [double]$EmergencyRamFloorGB = 0.30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SemanticRoot = Join-Path $RepoRoot 'runtime\semantic-projection'
$Harness = Join-Path $SemanticRoot 'tests\target-real-f16-browser-acceptance.mjs'
$RuntimeController = Join-Path $PSScriptRoot 'local-vision-runtime.ps1'
$RuntimeHelper = Join-Path $PSScriptRoot 'semantic-projection-runtime.ps1'
$Python = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage25\python-vision-venv\Scripts\python.exe'

if ([string]$env:CHAT_VISION_RUNTIME_TEST_MODE -eq '1') {
    throw 'Real F16 acceptance refuses CHAT_VISION_RUNTIME_TEST_MODE=1.'
}
if ($EmergencyRamFloorGB -lt 0.20 -or $EmergencyRamFloorGB -gt 1.00) {
    throw 'EmergencyRamFloorGB must be between 0.20 and 1.00.'
}
foreach ($required in @($Harness, $RuntimeController, $RuntimeHelper, $Python)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Required Stage 25.1 target-acceptance file is missing: $required"
    }
}

$node = (Get-Command node -ErrorAction Stop).Source
$head = (& git -C $RepoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($head)) {
    throw 'Could not resolve current Git HEAD.'
}

$chromeRunningBefore = [bool](Get-Process chrome -ErrorAction SilentlyContinue)
if (-not $chromeRunningBefore) {
    throw 'Target acceptance requires the user Chrome workload to remain open.'
}

Write-Host "`n===== STAGE 25.1 REAL F16 SAME-SESSION ACCEPTANCE =====" -ForegroundColor Cyan
Write-Host "HEAD=$head"
Write-Host "CHROME_RUNNING_BEFORE=$chromeRunningBefore"

. $RuntimeHelper
$entry = Get-SemanticProjectionEntryPath -RepoRoot $RepoRoot -EnsureDependencies
Write-Host "SEMANTIC_ENTRY=$entry"

$pillowVersion = (& $Python -c "import PIL; print(PIL.__version__)" 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Could not import Pillow from the reviewed Stage 25 vision environment: $pillowVersion"
}
if ($pillowVersion -ne '12.3.0') {
    throw "Reviewed vision Python environment requires Pillow 12.3.0; got $pillowVersion"
}
Write-Host "PILLOW_VERSION=$pillowVersion"

$doctorText = & $RuntimeController -Action Doctor | Out-String
if ($LASTEXITCODE -ne 0) {
    throw "Vision runtime Doctor failed:`n$doctorText"
}
$doctor = $doctorText | ConvertFrom-Json
if (-not [bool]$doctor.admission_ready) {
    throw "Vision runtime Doctor rejected current memory admission: physical=$($doctor.physical_free_gb) GB virtual=$($doctor.virtual_free_gb) GB."
}
Write-Host "VISION_RUNTIME_PROFILE=$([string]$doctor.profile)"
Write-Host "VISION_RUNTIME_ADMISSION_READY=$([bool]$doctor.admission_ready)"
Write-Host "VISION_RUNTIME_DOCTOR_PHYSICAL_GB=$([double]$doctor.physical_free_gb)"
Write-Host "VISION_RUNTIME_DOCTOR_VIRTUAL_GB=$([double]$doctor.virtual_free_gb)"

$statusBefore = ((& $RuntimeController -Action Status | Out-String) | ConvertFrom-Json)
if ([bool]$statusBefore.running) {
    Write-Host 'Stopping the currently owned vision runtime before cold-start acceptance.' -ForegroundColor Yellow
    $null = (& $RuntimeController -Action Stop | Out-String)
}

if ([string]::IsNullOrWhiteSpace($ResultPath)) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $resultRoot = Join-Path $env:LOCALAPPDATA "ChatAgentPlatform\stage25\runtime\real-f16-same-session-$stamp"
    New-Item -ItemType Directory -Force -Path $resultRoot | Out-Null
    $ResultPath = Join-Path $resultRoot 'result.json'
}
else {
    $ResultPath = [IO.Path]::GetFullPath($ResultPath)
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $ResultPath) | Out-Null
}

$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $node
$psi.WorkingDirectory = $SemanticRoot
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
# Keep stdout/stderr inherited by this console. Redirecting without draining can
# deadlock a long real-model run once the OS pipe buffer fills.
$psi.RedirectStandardOutput = $false
$psi.RedirectStandardError = $false
[void]$psi.ArgumentList.Add($Harness)
$psi.Environment['STAGE25_1_RESULT_PATH'] = $ResultPath

$clientProc = $null
$minRamGB = [double]::MaxValue
$safetyStop = $false

try {
    Write-Host "`n===== LIVE TARGET HARNESS =====" -ForegroundColor Cyan
    $clientProc = [System.Diagnostics.Process]::Start($psi)
    if ($null -eq $clientProc) {
        throw 'Could not start Stage 25.1 Node target harness.'
    }

    while (-not $clientProc.HasExited) {
        Start-Sleep -Milliseconds 500
        $os = Get-CimInstance Win32_OperatingSystem
        $freeGB = ($os.FreePhysicalMemory * 1KB) / 1GB
        if ($freeGB -lt $minRamGB) {
            $minRamGB = $freeGB
        }
        if ($freeGB -lt $EmergencyRamFloorGB) {
            $safetyStop = $true
            Stop-Process -Id $clientProc.Id -Force -ErrorAction SilentlyContinue
            break
        }
    }

    $clientProc.WaitForExit()

    Write-Host "`n===== RESOURCE SAFETY =====" -ForegroundColor Cyan
    Write-Host "SAFETY_STOP=$safetyStop"
    Write-Host "MIN_RAM_FREE_GB=$([math]::Round($minRamGB, 2))"
    Write-Host "CHROME_STILL_RUNNING=$([bool](Get-Process chrome -ErrorAction SilentlyContinue))"

    if (Test-Path -LiteralPath $ResultPath -PathType Leaf) {
        Write-Host "`n===== EXACT RESULT =====" -ForegroundColor Green
        Get-Content -LiteralPath $ResultPath -Raw -Encoding utf8
    }
    else {
        throw "Target harness did not create result file: $ResultPath"
    }

    if ($safetyStop) {
        throw "Target acceptance stopped because free RAM fell below $EmergencyRamFloorGB GB."
    }
    if ($clientProc.ExitCode -ne 0) {
        throw "Stage 25.1 real F16 target harness failed with exit code $($clientProc.ExitCode)."
    }
}
finally {
    if ($null -ne $clientProc -and -not $clientProc.HasExited) {
        Stop-Process -Id $clientProc.Id -Force -ErrorAction SilentlyContinue
        $clientProc.WaitForExit()
    }

    try {
        $stopText = & $RuntimeController -Action Stop | Out-String
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Vision runtime Stop failed: $stopText"
        }
    }
    catch {
        Write-Warning "Vision runtime Stop failed: $($_.Exception.Message)"
    }

    try {
        $after = ((& $RuntimeController -Action Status | Out-String) | ConvertFrom-Json)
        Write-Host "VISION_RUNTIME_RUNNING_AFTER_TEST=$([bool]$after.running)"
        Write-Host "VISION_RUNTIME_STATE_AFTER_TEST=$([string]$after.state)"
    }
    catch {
        Write-Warning "Could not read final vision runtime status: $($_.Exception.Message)"
    }

    Write-Host "CHROME_RUNNING_AFTER_TEST=$([bool](Get-Process chrome -ErrorAction SilentlyContinue))"
    Write-Host "RESULT_PATH=$ResultPath"
}
