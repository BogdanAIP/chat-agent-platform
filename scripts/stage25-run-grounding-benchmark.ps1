param(
    [string]$OutputRoot,
    [int]$Port = 3066,
    [int]$ContextSize = 1024,
    [ValidateSet('direct', 'mark-grid', 'both')][string]$Method = 'both',
    [string[]]$CaseId = @(),
    [int]$RequestTimeoutSeconds = 120,
    [double]$MinStartRamGB = 1.50,
    [double]$MinRunRamGB = 0.50,
    [double]$MinRunVirtualGB = 1.50
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$modelDir = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage25\models\LFM2.5-VL-3B-GGUF'
$modelPath = Join-Path $modelDir 'LFM2.5-VL-3B-Q4_K_M.gguf'
$mmprojPath = Join-Path $modelDir 'mmproj-LFM2.5-VL-3B-Q8_0.gguf'
$expectedModelSha = '83c18dfba02c75769cdd63f73e37c343400e82d434ff1b14bcc1cb02fcf2f5f2'
$expectedMmprojSha = '8ba27050dc88737db66b856d3b74e0e6cf54bee35fa4d9d9808f69ee556bbd43'

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $OutputRoot = Join-Path $env:LOCALAPPDATA "ChatAgentPlatform\stage25\runtime\grounding-benchmark-$stamp"
}
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$OutputRoot = (Resolve-Path -LiteralPath $OutputRoot).Path

if ($Port -lt 1 -or $Port -gt 65535) { throw 'Port must be between 1 and 65535.' }
if ($ContextSize -lt 512 -or $ContextSize -gt 8192) { throw 'ContextSize must be between 512 and 8192.' }
if ($RequestTimeoutSeconds -lt 30 -or $RequestTimeoutSeconds -gt 300) { throw 'RequestTimeoutSeconds must be between 30 and 300.' }
if ($MinStartRamGB -lt 0.5 -or $MinStartRamGB -gt 8.0) { throw 'MinStartRamGB must be between 0.5 and 8.0.' }
if ($MinRunRamGB -lt 0.25 -or $MinRunRamGB -gt $MinStartRamGB) { throw 'MinRunRamGB must be between 0.25 and MinStartRamGB.' }
if ($MinRunVirtualGB -lt 1.0 -or $MinRunVirtualGB -gt 8.0) { throw 'MinRunVirtualGB must be between 1.0 and 8.0.' }
if (($Method -eq 'mark-grid' -or $Method -eq 'both') -and $ContextSize -lt 3072) {
    throw 'Mark-Grid requires ContextSize >= 3072: the first target run measured second-pass prompts up to 2463 tokens.'
}
if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    throw "Port $Port is already in use."
}

$preOs = Get-CimInstance Win32_OperatingSystem
$preRamGB = ($preOs.FreePhysicalMemory * 1KB) / 1GB
$preVirtualGB = ($preOs.FreeVirtualMemory * 1KB) / 1GB
Write-Host "`n===== PRE-RUN MEMORY =====" -ForegroundColor Cyan
Write-Host "RAM_FREE_GB=$([math]::Round($preRamGB,2))"
Write-Host "VIRTUAL_FREE_GB=$([math]::Round($preVirtualGB,2))"
Write-Host "MIN_START_RAM_GB=$MinStartRamGB"
Write-Host "MIN_RUN_RAM_GB=$MinRunRamGB"
Write-Host "MIN_RUN_VIRTUAL_GB=$MinRunVirtualGB"
if ($preRamGB -lt $MinStartRamGB) {
    throw "Not enough physical RAM to start safely: $([math]::Round($preRamGB,2)) GB free."
}
if ($preVirtualGB -lt 3.0) {
    throw "Not enough virtual memory to start safely: $([math]::Round($preVirtualGB,2)) GB free."
}

foreach ($path in @($modelPath, $mmprojPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required verified model artifact is missing: $path"
    }
}

Write-Host "`n===== VERIFY MODEL ARTIFACTS =====" -ForegroundColor Cyan
$modelSha = (Get-FileHash -LiteralPath $modelPath -Algorithm SHA256).Hash.ToLowerInvariant()
$mmprojSha = (Get-FileHash -LiteralPath $mmprojPath -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host "MODEL_SHA256=$modelSha"
Write-Host "MMPROJ_SHA256=$mmprojSha"
if ($modelSha -ne $expectedModelSha) { throw 'Main model SHA256 mismatch.' }
if ($mmprojSha -ne $expectedMmprojSha) { throw 'mmproj SHA256 mismatch.' }
Write-Host 'MODEL_ARTIFACTS_VERIFIED=True'

$llamaServer = Get-Command llama-server -ErrorAction Stop
$systemPython = Get-Command python -ErrorAction Stop

# Keep the renderer dependency out of the user's global Python installation.
$venvRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage25\python-vision-venv'
$venvPython = Join-Path $venvRoot 'Scripts\python.exe'
$requirementsPath = Join-Path $repoRoot 'requirements-stage25-vision.txt'

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    Write-Host "`n===== CREATE STAGE 25 PYTHON VENV =====" -ForegroundColor Cyan
    & $systemPython.Source -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) { throw 'Could not create Stage 25 Python venv.' }
}

$installedPillow = & $venvPython -c "import PIL; print(PIL.__version__)" 2>$null
if ($LASTEXITCODE -ne 0 -or ([string]$installedPillow).Trim() -ne '12.3.0') {
    Write-Host "`n===== INSTALL PINNED STAGE 25 RENDERER DEPENDENCY =====" -ForegroundColor Cyan
    & $venvPython -m pip install --disable-pip-version-check --no-input -r $requirementsPath
    if ($LASTEXITCODE -ne 0) { throw 'Could not install pinned Stage 25 renderer dependency.' }
}
Write-Host "PILLOW_VERSION=$((& $venvPython -c 'import PIL; print(PIL.__version__)').Trim())"

$fixtureRoot = Join-Path $OutputRoot 'fixture'
& (Join-Path $PSScriptRoot 'stage25-capture-grounding-fixture.ps1') -OutputRoot $fixtureRoot
if ($LASTEXITCODE -ne 0) { throw 'Grounding fixture capture failed.' }

$screenshotPath = Join-Path $fixtureRoot 'fixture.png'
$casesPath = Join-Path $repoRoot 'tests\fixtures\stage25_grounding_cases.json'
$resultPath = Join-Path $OutputRoot 'grounding-results.json'
$artifactDir = Join-Path $OutputRoot 'mark-grid-artifacts'
$serverStdout = Join-Path $OutputRoot 'llama-server.stdout.log'
$serverStderr = Join-Path $OutputRoot 'llama-server.stderr.log'
$clientStdout = Join-Path $OutputRoot 'benchmark-client.stdout.log'
$clientStderr = Join-Path $OutputRoot 'benchmark-client.stderr.log'

$serverArgs = @(
    '-m', $modelPath,
    '--mmproj', $mmprojPath,
    '--device', 'none',
    '--gpu-layers', '0',
    '--no-mmproj-offload',
    '--no-op-offload',
    '--threads', '8',
    '--threads-batch', '8',
    '--fit', 'off',
    '--ctx-size', "$ContextSize",
    '--batch-size', '128',
    '--ubatch-size', '64',
    '--cache-type-k', 'q8_0',
    '--cache-type-v', 'q8_0',
    '--host', '127.0.0.1',
    '--port', "$Port",
    '--parallel', '1',
    '--no-ui',
    '--offline'
)

$serverProc = $null
$clientProc = $null

try {
    Write-Host "`n===== START LLAMA.CPP GROUNDING SERVER =====" -ForegroundColor Cyan
    $loadStart = Get-Date
    $serverProc = Start-Process `
        -FilePath $llamaServer.Source `
        -ArgumentList $serverArgs `
        -RedirectStandardOutput $serverStdout `
        -RedirectStandardError $serverStderr `
        -WindowStyle Hidden `
        -PassThru
    Write-Host "SERVER_PID=$($serverProc.Id)"

    $ready = $false
    for ($i = 0; $i -lt 180; $i++) {
        Start-Sleep -Milliseconds 500
        if ($serverProc.HasExited) {
            if (Test-Path -LiteralPath $serverStderr) { Get-Content -LiteralPath $serverStderr -Tail 120 }
            throw 'llama-server exited while loading.'
        }
        try {
            $health = Invoke-WebRequest `
                -Uri "http://127.0.0.1:$Port/health" `
                -TimeoutSec 2 `
                -SkipHttpErrorCheck
            if ($health.StatusCode -eq 200) {
                $ready = $true
                break
            }
        } catch {}
    }
    if (-not $ready) { throw 'llama-server did not become ready.' }

    $loadSeconds = [math]::Round(((Get-Date) - $loadStart).TotalSeconds, 2)
    Write-Host "SERVER_READY=True"
    Write-Host "LOAD_SECONDS=$loadSeconds"
    Write-Host "CONTEXT_SIZE=$ContextSize"
    Write-Host "METHOD=$Method"
    Write-Host "CASE_IDS=$($CaseId -join ',')"
    Write-Host 'THREADS=8'
    Write-Host 'MAIN_MODEL_DEVICE=CPU'
    Write-Host 'MMPROJ_DEVICE=CPU'

    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $venvPython
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.WorkingDirectory = $repoRoot

    $clientArgs = [System.Collections.Generic.List[string]]::new()
    foreach ($argument in @(
        (Join-Path $repoRoot 'scripts\stage25-grounding-benchmark.py'),
        '--image', $screenshotPath,
        '--cases', $casesPath,
        '--port', "$Port",
        '--method', $Method,
        '--output', $resultPath,
        '--artifacts', $artifactDir,
        '--timeout-seconds', "$RequestTimeoutSeconds"
    )) {
        $clientArgs.Add([string]$argument)
    }
    foreach ($case in $CaseId) {
        if (-not [string]::IsNullOrWhiteSpace($case)) {
            $clientArgs.Add('--case-id')
            $clientArgs.Add($case.Trim())
        }
    }
    foreach ($argument in $clientArgs) {
        [void]$psi.ArgumentList.Add($argument)
    }

    Write-Host "`n===== RUN STAGED GROUNDING PROBE =====" -ForegroundColor Cyan
    $benchmarkStart = Get-Date
    $clientProc = [System.Diagnostics.Process]::Start($psi)

    $minRamGB = [double]::MaxValue
    $minVirtualGB = [double]::MaxValue
    $maxPageMB = 0.0
    $maxWorkingMB = 0.0
    $maxPrivateMB = 0.0
    $safetyStop = $false
    $lastProgress = ''

    while (-not $clientProc.HasExited) {
        Start-Sleep -Milliseconds 500

        $os = Get-CimInstance Win32_OperatingSystem
        $ramGB = ($os.FreePhysicalMemory * 1KB) / 1GB
        $virtualGB = ($os.FreeVirtualMemory * 1KB) / 1GB
        $pageMB = (Get-CimInstance Win32_PageFileUsage | Measure-Object CurrentUsage -Sum).Sum
        $serverNow = Get-Process -Id $serverProc.Id -ErrorAction SilentlyContinue

        if ($serverNow) {
            $workingMB = $serverNow.WorkingSet64 / 1MB
            $privateMB = $serverNow.PrivateMemorySize64 / 1MB
            if ($workingMB -gt $maxWorkingMB) { $maxWorkingMB = $workingMB }
            if ($privateMB -gt $maxPrivateMB) { $maxPrivateMB = $privateMB }
        }
        if ($ramGB -lt $minRamGB) { $minRamGB = $ramGB }
        if ($virtualGB -lt $minVirtualGB) { $minVirtualGB = $virtualGB }
        if ($pageMB -gt $maxPageMB) { $maxPageMB = $pageMB }

        if (Test-Path -LiteralPath $resultPath -PathType Leaf) {
            try {
                $partial = Get-Content -LiteralPath $resultPath -Raw -Encoding utf8 | ConvertFrom-Json
                $progressParts = @()
                foreach ($name in @('direct', 'mark-grid')) {
                    $property = $partial.methods.PSObject.Properties[$name]
                    if ($null -ne $property) {
                        $count = @($property.Value.cases).Count
                        $progressParts += "$name=$count"
                    }
                }
                $progress = $progressParts -join ';'
                if ($progress -and $progress -ne $lastProgress) {
                    Write-Host "PROGRESS=$progress"
                    $lastProgress = $progress
                }
            } catch {}
        }

        if ($ramGB -lt $MinRunRamGB -or $virtualGB -lt $MinRunVirtualGB) {
            $safetyStop = $true
            try { $clientProc.Kill($true) } catch {}
            break
        }
    }

    $clientProc.WaitForExit()
    $clientOut = $clientProc.StandardOutput.ReadToEnd()
    $clientErr = $clientProc.StandardError.ReadToEnd()
    Set-Content -LiteralPath $clientStdout -Value $clientOut -Encoding utf8
    Set-Content -LiteralPath $clientStderr -Value $clientErr -Encoding utf8

    $benchmarkSeconds = [math]::Round(((Get-Date) - $benchmarkStart).TotalSeconds, 2)

    Write-Host $clientOut
    if (-not [string]::IsNullOrWhiteSpace($clientErr)) {
        Write-Host "`n===== BENCHMARK STDERR =====" -ForegroundColor Yellow
        Write-Host $clientErr
    }

    Write-Host "`n===== RESOURCE RESULT =====" -ForegroundColor Cyan
    Write-Host "SAFETY_STOP=$safetyStop"
    Write-Host "BENCHMARK_SECONDS=$benchmarkSeconds"
    Write-Host "MIN_RAM_FREE_GB=$([math]::Round($minRamGB,2))"
    Write-Host "MIN_VIRTUAL_FREE_GB=$([math]::Round($minVirtualGB,2))"
    Write-Host "MAX_PAGEFILE_MB=$([math]::Round($maxPageMB,0))"
    Write-Host "MAX_SERVER_WORKING_SET_MB=$([math]::Round($maxWorkingMB,1))"
    Write-Host "MAX_SERVER_PRIVATE_MB=$([math]::Round($maxPrivateMB,1))"
    Write-Host "CLIENT_EXIT_CODE=$($clientProc.ExitCode)"

    $results = $null
    if (Test-Path -LiteralPath $resultPath -PathType Leaf) {
        try {
            $results = Get-Content -LiteralPath $resultPath -Raw -Encoding utf8 | ConvertFrom-Json
        } catch {
            Write-Host 'PARTIAL_RESULT_READABLE=False'
        }
    }

    if ($null -ne $results) {
        Write-Host "`n===== AVAILABLE CHECKPOINT SUMMARY =====" -ForegroundColor Green
        foreach ($name in @('direct', 'mark-grid')) {
            $property = $results.methods.PSObject.Properties[$name]
            if ($null -ne $property -and $null -ne $property.Value.summary) {
                Write-Host "METHOD=$name"
                $property.Value.summary | ConvertTo-Json -Depth 6
            }
        }
        Write-Host "CHECKPOINT_COMPLETED=$($results.completed)"
        Write-Host "RESULT_JSON=$resultPath"
    }

    if ($safetyStop) { throw 'Grounding probe stopped by the conservative memory safety limit.' }
    if ($clientProc.ExitCode -ne 0) { throw 'Grounding benchmark client failed.' }
    if ($null -eq $results) { throw 'Benchmark result JSON is missing or unreadable.' }
    if (-not [bool]$results.completed) { throw 'Benchmark client exited without a completed checkpoint.' }

    Write-Host "`n===== STAGE 25 TARGET GROUNDING PROBE =====" -ForegroundColor Green
    Write-Host 'STAGE25_LFM25_VL_3B_GROUNDING_RUN=PASS'
}
finally {
    Write-Host "`n===== CLEANUP =====" -ForegroundColor Cyan
    if ($clientProc -and -not $clientProc.HasExited) {
        try { $clientProc.Kill($true) } catch {}
    }
    if ($serverProc -and -not $serverProc.HasExited) {
        Stop-Process -Id $serverProc.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 3
    $serverRunning = $false
    if ($serverProc) {
        $serverRunning = [bool](Get-Process -Id $serverProc.Id -ErrorAction SilentlyContinue)
    }
    Write-Host "SERVER_RUNNING_AFTER_TEST=$serverRunning"
}
