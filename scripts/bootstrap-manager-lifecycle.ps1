Set-StrictMode -Version Latest

function Invoke-ChatManagerStatusCapture {
    param([Parameter(Mandatory)] [string]$CommandPath)
    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    $output = @(
        & $pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $CommandPath -Action Status -NoNotify 2>&1
    )
    return [pscustomobject]@{ exit_code = $LASTEXITCODE; output = $output }
}

function Invoke-ChatManagerAction {
    param(
        [Parameter(Mandatory)] [string]$CommandPath,
        [Parameter(Mandatory)] [ValidateSet('Start', 'Stop')] [string]$Action,
        [ValidateSet('reference', 'files-readonly', 'browser-isolated', 'semantic', 'semantic-direct', 'adaptive')]
        [string]$Profile
    )

    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pwsh
    $startInfo.UseShellExecute = $false
    foreach ($argument in @('-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $CommandPath, '-Action', $Action, '-NoNotify')) {
        $startInfo.ArgumentList.Add([string]$argument)
    }
    if (-not [string]::IsNullOrWhiteSpace($Profile)) {
        $startInfo.ArgumentList.Add('-Profile')
        $startInfo.ArgumentList.Add($Profile)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    try {
        if (-not $process.Start()) {
            throw "Failed to start manager action $Action."
        }
        $process.WaitForExit()
        return $process.ExitCode
    }
    finally {
        $process.Dispose()
    }
}

function Install-ChatManager {
    param([Parameter(Mandatory)] [string]$CommandPath)
    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    & $pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File $CommandPath -Action Install -NoNotify
    if ($LASTEXITCODE -ne 0) {
        throw "Manager installation failed with exit code $LASTEXITCODE."
    }
}

function Invoke-ChatBootstrapSmokeTest {
    param([Parameter(Mandatory)] [string]$CommandPath)

    Write-Host 'Starting reference MCP + Secure MCP Tunnel for bootstrap smoke test...' -ForegroundColor Yellow
    $startSucceeded = $false
    try {
        $startExit = Invoke-ChatManagerAction -CommandPath $CommandPath -Action Start -Profile reference
        if ($startExit -ne 0) {
            throw "Manager start failed during bootstrap smoke test with exit code $startExit."
        }
        $startSucceeded = $true

        $statusResult = Invoke-ChatManagerStatusCapture -CommandPath $CommandPath
        if ($statusResult.exit_code -ne 0) {
            throw "Manager status failed during bootstrap smoke test: $($statusResult.output -join ' ')"
        }
        $status = $statusResult.output | Out-String | ConvertFrom-Json
        if ([string]$status.active_profile -ne 'reference') {
            throw "Bootstrap smoke test started unexpected profile '$($status.active_profile)' instead of reference."
        }
        if (-not [bool]$status.mcp_ready) { throw 'Bootstrap smoke test: reference MCP is not ready.' }
        if (-not [bool]$status.tunnel_ready) { throw 'Bootstrap smoke test: Secure MCP Tunnel is not ready.' }
        if ([int]$status.active_count -ne 1) { throw 'Bootstrap smoke test: expected exactly one active MCP profile.' }

        Write-Host 'BOOTSTRAP_SMOKE_PROFILE=reference'
        Write-Host 'BOOTSTRAP_SMOKE_TEST=passed' -ForegroundColor Green
    }
    finally {
        if ($startSucceeded) {
            $stopExit = Invoke-ChatManagerAction -CommandPath $CommandPath -Action Stop
            if ($stopExit -ne 0) { Write-Warning "Bootstrap cleanup stop returned exit code $stopExit." }
        }
        else {
            try { $null = Invoke-ChatManagerAction -CommandPath $CommandPath -Action Stop }
            catch { Write-Warning "Bootstrap cleanup could not invoke Stop: $($_.Exception.Message)" }
        }
    }
}
