[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$controller = Join-Path $PSScriptRoot 'local-vision-runtime.ps1'
$fakeServer = Join-Path $repoRoot 'tests\fixtures\fake_llama_server.py'
$python = (Get-Command python -ErrorAction Stop).Source
$tempRoot = Join-Path $env:RUNNER_TEMP ('stage25-1-vision-runtime-' + [Guid]::NewGuid().ToString('N'))
$modelRoot = Join-Path $tempRoot 'models'
$artifactDir = Join-Path $modelRoot 'fixture-model'
$stateRoot = Join-Path $tempRoot 'state'
$configPath = Join-Path $tempRoot 'runtime.json'
$modelPath = Join-Path $artifactDir 'model.gguf'
$mmprojPath = Join-Path $artifactDir 'mmproj.gguf'
$port = 31868

New-Item -ItemType Directory -Force -Path $artifactDir, $stateRoot | Out-Null
[IO.File]::WriteAllBytes($modelPath, [Text.Encoding]::UTF8.GetBytes('FAKE_MODEL_STAGE25_1'))
[IO.File]::WriteAllBytes($mmprojPath, [Text.Encoding]::UTF8.GetBytes('FAKE_MMPROJ_STAGE25_1'))

$modelItem = Get-Item -LiteralPath $modelPath
$mmprojItem = Get-Item -LiteralPath $mmprojPath
$modelSha = (Get-FileHash -LiteralPath $modelPath -Algorithm SHA256).Hash.ToLowerInvariant()
$mmprojSha = (Get-FileHash -LiteralPath $mmprojPath -Algorithm SHA256).Hash.ToLowerInvariant()

$config = [ordered]@{
    schema_version = 1
    profile = 'test-fixture'
    runtime = [ordered]@{
        command = $python
        command_prefix = @($fakeServer)
        required_version_markers = @('build 10448', 'ad1de39e0')
        host = '127.0.0.1'
        port = $port
        ready_timeout_seconds = 20
    }
    artifacts = [ordered]@{
        directory = 'fixture-model'
        model = [ordered]@{
            file = 'model.gguf'
            bytes = [int64]$modelItem.Length
            sha256 = $modelSha
        }
        mmproj = [ordered]@{
            file = 'mmproj.gguf'
            bytes = [int64]$mmprojItem.Length
            sha256 = $mmprojSha
        }
    }
    memory = [ordered]@{
        min_start_physical_gb = 0.01
        min_start_virtual_gb = 0.01
        min_run_physical_gb = 0.01
        min_run_virtual_gb = 0.01
    }
    idle_ttl_seconds = 3
    watchdog_interval_seconds = 1
    server_args = @()
}
$config | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $configPath -Encoding utf8

function Invoke-VisionRuntime {
    param(
        [Parameter(Mandatory)][string]$Action,
        [switch]$NoWatchdog
    )
    $parameters = @{
        Action = $Action
        ConfigPath = $configPath
        ModelRoot = $modelRoot
        StateRoot = $stateRoot
    }
    if ($NoWatchdog) { $parameters.NoWatchdog = $true }
    $text = & $controller @parameters 2>&1 | Out-String
    return ($text | ConvertFrom-Json)
}

function Wait-Status {
    param(
        [Parameter(Mandatory)][bool]$Running,
        [int]$TimeoutSeconds = 10
    )
    $deadline = [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
    $status = $null
    do {
        $status = Invoke-VisionRuntime -Action Status
        if ([bool]$status.running -eq $Running) { return $status }
        Start-Sleep -Milliseconds 250
    } while ([DateTimeOffset]::UtcNow -lt $deadline)
    throw "Timed out waiting for running=$Running. Last status: $($status | ConvertTo-Json -Compress)"
}

$oldTestMode = $env:CHAT_VISION_RUNTIME_TEST_MODE
$foreign = $null
try {
    $env:CHAT_VISION_RUNTIME_TEST_MODE = '1'

    Write-Host '===== DOCTOR ====='
    $doctor = Invoke-VisionRuntime -Action Doctor
    if (-not [bool]$doctor.admission_ready) { throw 'Fake runtime doctor should be admission-ready.' }
    if ([string]$doctor.model_sha256 -ne $modelSha) { throw 'Doctor model SHA mismatch.' }
    if ([string]$doctor.mmproj_sha256 -ne $mmprojSha) { throw 'Doctor mmproj SHA mismatch.' }
    if ([string]$doctor.host -ne '127.0.0.1' -or [int]$doctor.port -ne $port) { throw 'Doctor loopback binding drifted.' }
    Write-Host 'VISION_RUNTIME_DOCTOR=PASS'

    Write-Host '===== START / IDEMPOTENT START ====='
    $first = Invoke-VisionRuntime -Action Start
    if (-not [bool]$first.running -or -not [bool]$first.ready -or [bool]$first.conflict) {
        throw "Runtime did not start cleanly: $($first | ConvertTo-Json -Compress)"
    }
    $firstPid = [int]$first.pid
    $second = Invoke-VisionRuntime -Action Start
    if ([int]$second.pid -ne $firstPid) { throw 'Repeated Start must reuse the healthy owned process.' }
    Write-Host 'VISION_RUNTIME_IDEMPOTENT_START=PASS'

    Write-Host '===== TOUCH + IDLE TTL ====='
    Start-Sleep -Seconds 2
    $touched = Invoke-VisionRuntime -Action Touch
    if (-not [bool]$touched.running) { throw 'Touch unexpectedly stopped the runtime.' }
    Start-Sleep -Seconds 2
    $stillRunning = Invoke-VisionRuntime -Action Status
    if (-not [bool]$stillRunning.running) { throw 'Watchdog ignored Touch and unloaded too early.' }
    $stoppedByTtl = Wait-Status -Running $false -TimeoutSeconds 8
    if ([string]$stoppedByTtl.state -ne 'stopped') { throw 'TTL cleanup did not reach stopped state.' }
    if ($null -ne (Get-Process -Id $firstPid -ErrorAction SilentlyContinue)) { throw 'TTL cleanup left the owned fake server alive.' }
    Write-Host 'VISION_RUNTIME_IDLE_TTL=PASS'

    Write-Host '===== EXPLICIT STOP ====='
    $startedAgain = Invoke-VisionRuntime -Action Start
    $stopPid = [int]$startedAgain.pid
    $stopped = Invoke-VisionRuntime -Action Stop
    if ([bool]$stopped.running -or [bool]$stopped.ready) { throw 'Explicit Stop did not report stopped.' }
    if ($null -ne (Get-Process -Id $stopPid -ErrorAction SilentlyContinue)) { throw 'Explicit Stop left the owned process alive.' }
    Write-Host 'VISION_RUNTIME_EXPLICIT_STOP=PASS'

    Write-Host '===== ARTIFACT TAMPER ====='
    Add-Content -LiteralPath $modelPath -Value 'tamper' -NoNewline
    $artifactRejected = $false
    try {
        $null = Invoke-VisionRuntime -Action Doctor
    }
    catch {
        $artifactRejected = ($_.Exception.Message -match 'byte-size mismatch|SHA256 mismatch')
    }
    if (-not $artifactRejected) { throw 'Tampered model artifact was not rejected.' }
    [IO.File]::WriteAllBytes($modelPath, [Text.Encoding]::UTF8.GetBytes('FAKE_MODEL_STAGE25_1'))
    Write-Host 'VISION_RUNTIME_ARTIFACT_TAMPER=PASS'

    Write-Host '===== FOREIGN PORT FAIL CLOSED ====='
    $foreign = Start-Process `
        -FilePath $python `
        -ArgumentList @($fakeServer, '-m', $modelPath, '--mmproj', $mmprojPath, '--host', '127.0.0.1', '--port', [string]$port) `
        -WindowStyle Hidden `
        -PassThru
    $foreignReady = $false
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 100
        try {
            $health = Invoke-WebRequest -Uri "http://127.0.0.1:$port/health" -TimeoutSec 1 -SkipHttpErrorCheck
            if ($health.StatusCode -eq 200) { $foreignReady = $true; break }
        }
        catch {}
    }
    if (-not $foreignReady) { throw 'Foreign fake listener did not start.' }
    $foreignRejected = $false
    try {
        $null = Invoke-VisionRuntime -Action Start
    }
    catch {
        $foreignRejected = ($_.Exception.Message -match 'occupied by an unowned listener')
    }
    if (-not $foreignRejected) { throw 'Controller did not fail closed on an unowned port listener.' }
    if ($foreign.HasExited) { throw 'Controller must not kill the foreign listener.' }
    Stop-Process -Id $foreign.Id -Force
    $foreign.WaitForExit()
    $foreign = $null
    Write-Host 'VISION_RUNTIME_FOREIGN_PORT=PASS'

    Write-Host '===== OWNERSHIP MISMATCH FAIL CLOSED ====='
    $owned = Invoke-VisionRuntime -Action Start -NoWatchdog
    $ownedPid = [int]$owned.pid
    $statePath = Join-Path $stateRoot 'state.json'
    $state = Get-Content -LiteralPath $statePath -Raw -Encoding utf8 | ConvertFrom-Json
    $realExecutable = [string]$state.runtime_executable
    $state.runtime_executable = Join-Path $tempRoot 'not-the-owned-runtime.exe'
    $state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statePath -Encoding utf8

    $ownershipRejected = $false
    try {
        $null = Invoke-VisionRuntime -Action Stop
    }
    catch {
        $ownershipRejected = ($_.Exception.Message -match 'ownership mismatch')
    }
    if (-not $ownershipRejected) { throw 'Ownership mismatch did not fail closed.' }
    if ($null -eq (Get-Process -Id $ownedPid -ErrorAction SilentlyContinue)) { throw 'Ownership mismatch path killed an unverified live process.' }

    $state = Get-Content -LiteralPath $statePath -Raw -Encoding utf8 | ConvertFrom-Json
    $state.runtime_executable = $realExecutable
    $state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statePath -Encoding utf8
    $null = Invoke-VisionRuntime -Action Stop
    if ($null -ne (Get-Process -Id $ownedPid -ErrorAction SilentlyContinue)) { throw 'Restored owned process did not stop.' }
    Write-Host 'VISION_RUNTIME_OWNERSHIP_FAIL_CLOSED=PASS'

    Write-Host 'VISION_RUNTIME_ACCEPTANCE=PASS'
}
finally {
    if ($null -ne $foreign -and -not $foreign.HasExited) {
        Stop-Process -Id $foreign.Id -Force -ErrorAction SilentlyContinue
    }
    try { $null = Invoke-VisionRuntime -Action Stop } catch {}
    if ($null -eq $oldTestMode) { Remove-Item Env:CHAT_VISION_RUNTIME_TEST_MODE -ErrorAction SilentlyContinue }
    else { $env:CHAT_VISION_RUNTIME_TEST_MODE = $oldTestMode }
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}
