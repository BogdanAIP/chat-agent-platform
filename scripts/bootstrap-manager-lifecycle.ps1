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
        [string]$Profile,
        [string]$FilesRoot
    )

    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pwsh
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    foreach ($argument in @('-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $CommandPath, '-Action', $Action, '-NoNotify')) {
        $startInfo.ArgumentList.Add([string]$argument)
    }
    if (-not [string]::IsNullOrWhiteSpace($Profile)) {
        $startInfo.ArgumentList.Add('-Profile')
        $startInfo.ArgumentList.Add($Profile)
    }
    if (-not [string]::IsNullOrWhiteSpace($FilesRoot)) {
        $startInfo.ArgumentList.Add('-FilesRoot')
        $startInfo.ArgumentList.Add($FilesRoot)
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

function Save-ChatProtectedApiKeyIfMissing {
    param([Parameter(Mandatory)] [string]$LocalRoot)

    $secretDir = Join-Path $LocalRoot 'secrets'
    $secretFile = Join-Path $secretDir 'control-plane-api-key.dpapi'
    New-Item -ItemType Directory -Force -Path $secretDir | Out-Null

    if (Test-Path -LiteralPath $secretFile -PathType Leaf) {
        Write-Host 'SECRET_SOURCE=existing-dpapi'
        return
    }

    $secure = Read-Host 'Вставь CONTROL_PLANE_API_KEY — ввод скрыт' -AsSecureString
    if ($secure.Length -eq 0) { throw 'API key is empty.' }

    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $plain = $null
    $plainBytes = $null
    $protectedBytes = $null
    try {
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        $plainBytes = [Text.Encoding]::UTF8.GetBytes($plain)
        $protectedBytes = [Security.Cryptography.ProtectedData]::Protect(
            $plainBytes,
            $null,
            [Security.Cryptography.DataProtectionScope]::CurrentUser
        )
        [Convert]::ToBase64String($protectedBytes) |
            Set-Content -LiteralPath $secretFile -Encoding ascii
    }
    finally {
        if ($plainBytes) { [Array]::Clear($plainBytes, 0, $plainBytes.Length) }
        if ($protectedBytes) { [Array]::Clear($protectedBytes, 0, $protectedBytes.Length) }
        $plain = $null
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }

    Write-Host 'SECRET_SOURCE=new-dpapi'
}

function Resolve-ChatBootstrapWorkspace {
    param([Parameter(Mandatory)] [string]$LocalRoot)

    $settingsFile = Join-Path $LocalRoot 'state\settings.json'
    if (Test-Path -LiteralPath $settingsFile -PathType Leaf) {
        try {
            $settings = Get-Content -LiteralPath $settingsFile -Raw | ConvertFrom-Json
            if (
                $null -ne $settings.PSObject.Properties['files_root'] -and
                -not [string]::IsNullOrWhiteSpace([string]$settings.files_root) -and
                (Test-Path -LiteralPath ([string]$settings.files_root) -PathType Container)
            ) {
                return (Resolve-Path -LiteralPath ([string]$settings.files_root).Path
            }
        }
        catch {}
    }

    $workspace = Join-Path $LocalRoot 'workspace'
    New-Item -ItemType Directory -Force -Path $workspace | Out-Null
    return (Resolve-Path -LiteralPath $workspace).Path
}

function Install-ChatSemanticDesktopShortcut {
    param(
        [Parameter(Mandatory)] [string]$AppRoot,
        [Parameter(Mandatory)] [string]$TrayPath
    )

    if (-not (Test-Path -LiteralPath $TrayPath -PathType Leaf)) {
        throw "Installed tray script is missing: $TrayPath"
    }

    $desktop = [Environment]::GetFolderPath('Desktop')
    if ([string]::IsNullOrWhiteSpace($desktop)) {
        Write-Host 'DESKTOP_SHORTCUT=unavailable'
        return
    }

    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    $shortcutPath = Join-Path $desktop 'Chat Agent Platform.lnk'
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $pwsh
    $shortcut.Arguments = '-NoLogo -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f $TrayPath
    $shortcut.WorkingDirectory = $AppRoot
    $shortcut.IconLocation = "${env:SystemRoot}\System32\shell32.dll,44"
    $shortcut.Description = 'Chat Agent Platform — индикатор и ВКЛ/ВЫКЛ'
    $shortcut.Save()
    Write-Host "DESKTOP_SHORTCUT=$shortcutPath"
}

function Initialize-ChatSemanticCore {
    param(
        [Parameter(Mandatory)] [string]$CommandPath,
        [Parameter(Mandatory)] [string]$LocalRoot,
        [Parameter(Mandatory)] [string]$AppRoot,
        [Parameter(Mandatory)] [string]$TrayPath
    )

    Save-ChatProtectedApiKeyIfMissing -LocalRoot $LocalRoot
    $workspace = Resolve-ChatBootstrapWorkspace -LocalRoot $LocalRoot

    $pwsh = (Get-Command 'pwsh.exe' -ErrorAction Stop).Source
    & $pwsh `
        -NoLogo `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $CommandPath `
        -Action SetProfile `
        -Profile semantic `
        -FilesRoot $workspace `
        -NoNotify
    if ($LASTEXITCODE -ne 0) {
        throw "Could not migrate the public manager to canonical semantic/direct-stdio profile (exit $LASTEXITCODE)."
    }

    Install-ChatSemanticDesktopShortcut -AppRoot $AppRoot -TrayPath $TrayPath

    Write-Host 'DEFAULT_PROFILE=semantic'
    Write-Host "DEFAULT_FILES_ROOT=$workspace"
    Write-Host 'DEFAULT_TUNNEL_BINDING=direct-stdio'
    Write-Host 'LEGACY_1MCP_INSTALL_PATH_USED=False'
    return $workspace
}

function Invoke-ChatBootstrapSmokeTest {
    param(
        [Parameter(Mandatory)] [string]$CommandPath,
        [Parameter(Mandatory)] [string]$LocalRoot
    )

    $smokeRoot = Join-Path $LocalRoot 'bootstrap-smoke-workspace'
    New-Item -ItemType Directory -Force -Path $smokeRoot | Out-Null
    Set-Content -LiteralPath (Join-Path $smokeRoot 'bootstrap-smoke.txt') -Value 'CHAT_PLATFORM_SIX_TOOL_SMOKE' -Encoding utf8

    Write-Host 'Starting normal six-tool semantic route for bootstrap smoke test...' -ForegroundColor Yellow
    $startSucceeded = $false
    try {
        $startExit = Invoke-ChatManagerAction `
            -CommandPath $CommandPath `
            -Action Start `
            -Profile semantic `
            -FilesRoot $smokeRoot
        if ($startExit -ne 0) {
            throw "Normal semantic manager start failed during bootstrap smoke test with exit code $startExit."
        }
        $startSucceeded = $true

        $statusResult = Invoke-ChatManagerStatusCapture -CommandPath $CommandPath
        if ($statusResult.exit_code -ne 0) {
            throw "Manager status failed during bootstrap smoke test: $($statusResult.output -join ' ')"
        }
        $status = $statusResult.output | Out-String | ConvertFrom-Json
        if ([string]$status.active_profile -ne 'semantic') {
            throw "Bootstrap smoke test started unexpected profile '$($status.active_profile)' instead of semantic."
        }
        if (-not [bool]$status.mcp_ready) { throw 'Bootstrap smoke test: six-tool semantic MCP is not ready.' }
        if (-not [bool]$status.tunnel_ready) { throw 'Bootstrap smoke test: Secure MCP Tunnel is not ready.' }
        if ([int]$status.active_count -ne 1) { throw 'Bootstrap smoke test: expected exactly one active semantic runtime.' }
        if ([string]$status.tunnel_binding -ne 'direct-stdio') { throw 'Bootstrap smoke test: normal semantic route is not direct-stdio.' }

        Write-Host 'BOOTSTRAP_SMOKE_PROFILE=semantic'
        Write-Host 'BOOTSTRAP_SMOKE_BINDING=direct-stdio'
        Write-Host 'BOOTSTRAP_SMOKE_PUBLIC_TOOL_COUNT=6'
        Write-Host 'BOOTSTRAP_SMOKE_1MCP_REQUIRED=False'
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
        Remove-Item -LiteralPath $smokeRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
