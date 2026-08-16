[CmdletBinding()]
param(
    [ValidateSet("Install", "Start", "Stop", "Toggle", "Status", "SetProfile")]
    [string]$Action = "Status",

    [ValidateSet("reference", "files-readonly", "browser-isolated", "semantic", "semantic-direct", "adaptive")]
    [string]$Profile,

    [string]$FilesRoot,

    [switch]$NoNotify
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$LocalRoot = Join-Path $env:LOCALAPPDATA "ChatAgentPlatform"
$StateDir = Join-Path $LocalRoot "state"
$OwnerFile = Join-Path $StateDir "manager-owner.json"
$SettingsFile = Join-Path $StateDir "settings.json"
$BaselineControllerPath = Join-Path $PSScriptRoot "chat-platform-controller.ps1"
$SourceDirectControllerPath = Join-Path $PSScriptRoot "semantic-direct-controller.ps1"
$InstalledDirectControllerPath = Join-Path $LocalRoot "app\scripts\semantic-direct-controller.ps1"
$TunnelExe = Join-Path $LocalRoot "bin\tunnel-client.exe"
$DirectHealthUrlFile = Join-Path $StateDir "semantic-direct-health.url"
$McpPort = 3050
$MutexName = "Local\ChatAgentPlatformControllerOperation"
$MutexTimeoutMilliseconds = 30000
$script:LastControllerExitCode = 1

$SupportedProfiles = @(
    "reference",
    "files-readonly",
    "browser-isolated",
    "semantic",
    "semantic-direct",
    "adaptive"
)
$FilesRootProfiles = @(
    "files-readonly",
    "semantic",
    "semantic-direct",
    "adaptive"
)

if (-not (Test-Path -LiteralPath $BaselineControllerPath -PathType Leaf)) {
    throw "Internal controller is missing: $BaselineControllerPath"
}

function Test-SamePath {
    param(
        [string]$Left,
        [string]$Right
    )

    if (
        [string]::IsNullOrWhiteSpace($Left) -or
        [string]::IsNullOrWhiteSpace($Right)
    ) {
        return $false
    }

    try {
        $leftFull = [System.IO.Path]::GetFullPath($Left).TrimEnd('\')
        $rightFull = [System.IO.Path]::GetFullPath($Right).TrimEnd('\')
        return ($leftFull -ieq $rightFull)
    }
    catch {
        return $false
    }
}

function Initialize-ManagerStateDirectory {
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
}

function Get-SharedSettings {
    Initialize-ManagerStateDirectory

    if (-not (Test-Path -LiteralPath $SettingsFile -PathType Leaf)) {
        return [pscustomobject]@{
            profile = "reference"
            files_root = $null
            tunnel_profile = "local-1mcp"
        }
    }

    try {
        $settings = Get-Content -LiteralPath $SettingsFile -Raw | ConvertFrom-Json
    }
    catch {
        throw "Shared manager settings are invalid: $($_.Exception.Message)"
    }

    if (
        $null -eq $settings.PSObject.Properties["profile"] -or
        $SupportedProfiles -notcontains [string]$settings.profile
    ) {
        throw "Shared manager settings contain an unsupported profile."
    }

    $filesRoot = if ($null -ne $settings.PSObject.Properties["files_root"]) {
        $settings.files_root
    }
    else {
        $null
    }

    $tunnelProfile = if ($null -ne $settings.PSObject.Properties["tunnel_profile"]) {
        [string]$settings.tunnel_profile
    }
    else {
        if ([string]$settings.profile -eq "semantic-direct") {
            "direct-stdio"
        }
        else {
            "local-1mcp"
        }
    }

    return [pscustomobject]@{
        profile = [string]$settings.profile
        files_root = $filesRoot
        tunnel_profile = $tunnelProfile
    }
}

function Save-SharedSettings {
    param(
        [Parameter(Mandatory)]
        $Settings
    )

    Initialize-ManagerStateDirectory

    $temporary = "$SettingsFile.new"
    $Settings |
        ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath $temporary -Encoding utf8
    Move-Item -LiteralPath $temporary -Destination $SettingsFile -Force
}

function Get-RequestedProfile {
    if (-not [string]::IsNullOrWhiteSpace($Profile)) {
        return $Profile
    }

    return [string](Get-SharedSettings).profile
}

function Install-DirectControllerIfNeeded {
    if (-not (Test-Path -LiteralPath $SourceDirectControllerPath -PathType Leaf)) {
        return $false
    }

    if (Test-SamePath -Left $SourceDirectControllerPath -Right $InstalledDirectControllerPath) {
        return $false
    }

    $installedDir = Split-Path -Parent $InstalledDirectControllerPath
    New-Item -ItemType Directory -Force -Path $installedDir | Out-Null

    $sourceHash = (Get-FileHash -LiteralPath $SourceDirectControllerPath -Algorithm SHA256).Hash
    if (Test-Path -LiteralPath $InstalledDirectControllerPath -PathType Leaf) {
        $installedHash = (Get-FileHash -LiteralPath $InstalledDirectControllerPath -Algorithm SHA256).Hash
        if ($installedHash -eq $sourceHash) {
            return $false
        }
    }

    $temporary = "$InstalledDirectControllerPath.new"
    Copy-Item -LiteralPath $SourceDirectControllerPath -Destination $temporary -Force
    $copyHash = (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash
    if ($copyHash -ne $sourceHash) {
        Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
        throw 'semantic-direct controller installation verification failed.'
    }

    Move-Item -LiteralPath $temporary -Destination $InstalledDirectControllerPath -Force
    return $true
}

function Get-DirectControllerPath {
    if (Test-Path -LiteralPath $SourceDirectControllerPath -PathType Leaf) {
        $null = Install-DirectControllerIfNeeded
    }

    if (Test-Path -LiteralPath $InstalledDirectControllerPath -PathType Leaf) {
        return [System.IO.Path]::GetFullPath($InstalledDirectControllerPath)
    }

    if (Test-Path -LiteralPath $SourceDirectControllerPath -PathType Leaf) {
        return [System.IO.Path]::GetFullPath($SourceDirectControllerPath)
    }

    throw (
        "semantic-direct controller is unavailable. Expected either {0} or {1}." -f `
            $InstalledDirectControllerPath,
            $SourceDirectControllerPath
    )
}

$TargetProfile = Get-RequestedProfile
$ControllerPath = if ($Action -eq "Install") {
    [System.IO.Path]::GetFullPath($BaselineControllerPath)
}
elseif ($TargetProfile -eq "semantic-direct") {
    Get-DirectControllerPath
}
else {
    [System.IO.Path]::GetFullPath($BaselineControllerPath)
}

function Test-DirectControllerPath {
    param([Parameter(Mandatory)] [string]$Path)

    return (
        (Test-SamePath -Left $Path -Right $SourceDirectControllerPath) -or
        (Test-SamePath -Left $Path -Right $InstalledDirectControllerPath)
    )
}

function Get-ManagerOwner {
    if (-not (Test-Path -LiteralPath $OwnerFile -PathType Leaf)) {
        return $null
    }

    try {
        $owner = Get-Content -LiteralPath $OwnerFile -Raw | ConvertFrom-Json
        if (
            $null -eq $owner.PSObject.Properties["controller_path"] -or
            [string]::IsNullOrWhiteSpace([string]$owner.controller_path)
        ) {
            throw "manager-owner.json is missing controller_path."
        }
        return $owner
    }
    catch {
        throw "Shared manager ownership state is invalid: $($_.Exception.Message)"
    }
}

function Get-OwnerControllerPathForSave {
    if ($TargetProfile -eq "semantic-direct") {
        if (Test-Path -LiteralPath $InstalledDirectControllerPath -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($InstalledDirectControllerPath)
        }
    }

    return [System.IO.Path]::GetFullPath($ControllerPath)
}

function Save-ManagerOwner {
    Initialize-ManagerStateDirectory

    $payload = [ordered]@{
        schema_version = 1
        controller_path = Get-OwnerControllerPathForSave
        command_path = [System.IO.Path]::GetFullPath($PSCommandPath)
        repo_root = [System.IO.Path]::GetFullPath($RepoRoot)
        started_at = (Get-Date).ToUniversalTime().ToString("o")
    }

    $temporary = "$OwnerFile.new"
    $payload |
        ConvertTo-Json -Depth 4 |
        Set-Content -LiteralPath $temporary -Encoding utf8

    Move-Item -LiteralPath $temporary -Destination $OwnerFile -Force
}

function Remove-ManagerOwner {
    Remove-Item -LiteralPath $OwnerFile -Force -ErrorAction SilentlyContinue
}

function Get-McpPortListeners {
    if ($null -eq (Get-Command "Get-NetTCPConnection" -ErrorAction SilentlyContinue)) {
        return @()
    }

    return @(
        Get-NetTCPConnection `
            -LocalPort $McpPort `
            -State Listen `
            -ErrorAction SilentlyContinue
    )
}

function Get-McpPortDiagnostic {
    $lines = [System.Collections.Generic.List[string]]::new()

    foreach ($listener in @(Get-McpPortListeners)) {
        $pidValue = [int]$listener.OwningProcess
        $process = Get-CimInstance `
            Win32_Process `
            -Filter "ProcessId=$pidValue" `
            -ErrorAction SilentlyContinue

        if ($null -eq $process) {
            $lines.Add("PID=$pidValue")
        }
        else {
            $diagnosticLine = (
                "PID={0}; Name={1}; CommandLine={2}" -f `
                    $pidValue,
                    [string]$process.Name,
                    [string]$process.CommandLine
            )
            $lines.Add($diagnosticLine)
        }
    }

    return ($lines -join " | ")
}

function Get-DirectTunnelProcesses {
    if (-not (Test-Path -LiteralPath $TunnelExe -PathType Leaf)) {
        return @()
    }

    $expectedExe = [System.IO.Path]::GetFullPath($TunnelExe)
    $healthPattern = [regex]::Escape($DirectHealthUrlFile)

    return @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                if ($_.Name -ne "tunnel-client.exe") {
                    return $false
                }

                $actualExe = [string]$_.ExecutablePath
                $commandLine = [string]$_.CommandLine

                if (
                    [string]::IsNullOrWhiteSpace($actualExe) -or
                    [string]::IsNullOrWhiteSpace($commandLine)
                ) {
                    return $false
                }

                try {
                    $actualExe = [System.IO.Path]::GetFullPath($actualExe)
                }
                catch {
                    return $false
                }

                return (
                    $actualExe -ieq $expectedExe -and
                    $commandLine -match '(?i)--mcp\.command' -and
                    $commandLine -match $healthPattern
                )
            }
    )
}

function Get-DirectTunnelDiagnostic {
    $lines = [System.Collections.Generic.List[string]]::new()

    foreach ($process in @(Get-DirectTunnelProcesses)) {
        $lines.Add(
            "PID={0}; CommandLine={1}" -f `
                [int]$process.ProcessId,
                [string]$process.CommandLine
        )
    }

    return ($lines -join " | ")
}

function Test-AnySharedRuntime {
    return (
        @(Get-McpPortListeners).Count -gt 0 -or
        @(Get-DirectTunnelProcesses).Count -gt 0
    )
}

function Wait-SharedRuntimeFree {
    param(
        [ValidateRange(1, 60)]
        [int]$TimeoutSeconds = 15
    )

    for ($attempt = 0; $attempt -lt $TimeoutSeconds; $attempt++) {
        if (-not (Test-AnySharedRuntime)) {
            return $true
        }
        Start-Sleep -Seconds 1
    }

    return (-not (Test-AnySharedRuntime))
}

function Assert-SharedRuntimeFree {
    $portListeners = @(Get-McpPortListeners)
    $directProcesses = @(Get-DirectTunnelProcesses)

    if ($portListeners.Count -eq 0 -and $directProcesses.Count -eq 0) {
        return
    }

    $details = [System.Collections.Generic.List[string]]::new()
    if ($portListeners.Count -gt 0) {
        $details.Add("port ${McpPort}: $(Get-McpPortDiagnostic)")
    }
    if ($directProcesses.Count -gt 0) {
        $details.Add("semantic-direct: $(Get-DirectTunnelDiagnostic)")
    }

    throw (
        "A shared Chat Agent Platform runtime is already active but no matching " +
        "manager owner is available. Refusing ambiguous startup. " +
        ($details -join " | ")
    )
}

function Get-ControllerArguments {
    param(
        [Parameter(Mandatory)]
        [string]$TargetControllerPath,

        [Parameter(Mandatory)]
        [string]$TargetAction
    )

    $arguments = [System.Collections.Generic.List[string]]::new()

    foreach ($value in @(
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $TargetControllerPath,
        "-Action", $TargetAction
    )) {
        $arguments.Add([string]$value)
    }

    $passProfile = -not [string]::IsNullOrWhiteSpace($Profile)
    if (
        $passProfile -and
        [string]$Profile -eq "semantic-direct" -and
        (Test-DirectControllerPath -Path $TargetControllerPath)
    ) {
        $passProfile = $false
    }

    if ($passProfile) {
        $arguments.Add("-Profile")
        $arguments.Add($Profile)
    }

    if (-not [string]::IsNullOrWhiteSpace($FilesRoot)) {
        $arguments.Add("-FilesRoot")
        $arguments.Add($FilesRoot)
    }

    if ($NoNotify) {
        $arguments.Add("-NoNotify")
    }

    return $arguments
}

function Invoke-ControllerStatusAt {
    param(
        [Parameter(Mandatory)]
        [string]$TargetControllerPath
    )

    $pwsh = (
        Get-Command `
            "pwsh.exe" `
            -ErrorAction Stop
    ).Source

    $arguments = Get-ControllerArguments `
        -TargetControllerPath $TargetControllerPath `
        -TargetAction "Status"

    & $pwsh @arguments
    $script:LastControllerExitCode = $LASTEXITCODE
}

function Get-ControllerStatusObjectAt {
    param(
        [Parameter(Mandatory)]
        [string]$TargetControllerPath
    )

    $pwsh = (
        Get-Command `
            "pwsh.exe" `
            -ErrorAction Stop
    ).Source

    $arguments = Get-ControllerArguments `
        -TargetControllerPath $TargetControllerPath `
        -TargetAction "Status"

    $output = @(& $pwsh @arguments 2>&1)
    if ($LASTEXITCODE -ne 0) {
        throw (
            "Controller status failed with exit code {0}: {1}" -f `
                $LASTEXITCODE,
                (($output | Out-String).Trim())
        )
    }

    try {
        return ($output | Out-String | ConvertFrom-Json -ErrorAction Stop)
    }
    catch {
        throw (
            "Controller status returned invalid JSON: {0}" -f `
                (($output | Out-String).Trim())
        )
    }
}

function Invoke-InternalControllerMutation {
    param(
        [Parameter(Mandatory)]
        [string]$TargetControllerPath,

        [Parameter(Mandatory)]
        [string]$TargetAction
    )

    $pwsh = (
        Get-Command `
            "pwsh.exe" `
            -ErrorAction Stop
    ).Source

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pwsh
    $startInfo.UseShellExecute = $false

    foreach ($argument in (
        Get-ControllerArguments `
            -TargetControllerPath $TargetControllerPath `
            -TargetAction $TargetAction
    )) {
        $startInfo.ArgumentList.Add([string]$argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo

    try {
        if (-not $process.Start()) {
            throw "Failed to start the internal Chat Agent Platform controller."
        }

        $process.WaitForExit()
        $script:LastControllerExitCode = $process.ExitCode
    }
    finally {
        $process.Dispose()
    }
}

function Get-EffectiveOwnerControllerPath {
    $owner = Get-ManagerOwner
    if ($null -eq $owner) {
        return $null
    }

    $ownerController = [string]$owner.controller_path
    if (-not (Test-Path -LiteralPath $ownerController -PathType Leaf)) {
        if (Test-AnySharedRuntime) {
            throw (
                "Shared manager ownership points to a missing controller while " +
                "a managed runtime is still active: $ownerController"
            )
        }

        Remove-ManagerOwner
        return $null
    }

    return [System.IO.Path]::GetFullPath($ownerController)
}

function Stop-ForeignManagerIfNeeded {
    $ownerController = Get-EffectiveOwnerControllerPath
    if (
        [string]::IsNullOrWhiteSpace($ownerController) -or
        (Test-SamePath -Left $ownerController -Right $ControllerPath)
    ) {
        return $false
    }

    Invoke-InternalControllerMutation `
        -TargetControllerPath $ownerController `
        -TargetAction "Stop"

    if ($script:LastControllerExitCode -ne 0) {
        throw (
            "Could not stop the currently owning Chat Agent Platform manager: " +
            $ownerController
        )
    }

    Remove-ManagerOwner

    if (-not (Wait-SharedRuntimeFree -TimeoutSeconds 15)) {
        throw (
            "The previous Chat Agent Platform manager stopped, but a shared " +
            "runtime is still active. Port=$((Get-McpPortDiagnostic)); " +
            "Direct=$((Get-DirectTunnelDiagnostic))"
        )
    }

    return $true
}

function Test-CurrentManagerActive {
    try {
        $status = Get-ControllerStatusObjectAt -TargetControllerPath $ControllerPath
        return (
            [int]$status.active_count -eq 1 -and
            [bool]$status.mcp_ready -and
            [bool]$status.tunnel_ready
        )
    }
    catch {
        return $false
    }
}

function Assert-ProfileCanChange {
    $ownerController = Get-EffectiveOwnerControllerPath

    if (-not [string]::IsNullOrWhiteSpace($ownerController)) {
        $state = Get-ControllerStatusObjectAt -TargetControllerPath $ownerController
        if (
            [bool]$state.tunnel_running -or
            [int]$state.active_count -gt 0
        ) {
            throw "Stop the platform before changing its default profile."
        }

        Remove-ManagerOwner
    }
    elseif (Test-AnySharedRuntime) {
        Assert-SharedRuntimeFree
    }
}

function Set-SharedProfile {
    if ([string]::IsNullOrWhiteSpace($Profile)) {
        throw "-Profile is required for SetProfile."
    }

    Assert-ProfileCanChange

    $settings = Get-SharedSettings
    $resolvedRoot = $settings.files_root

    if ($FilesRootProfiles -contains $Profile) {
        if ([string]::IsNullOrWhiteSpace($FilesRoot)) {
            throw "-FilesRoot is required for $Profile."
        }

        if (-not (Test-Path -LiteralPath $FilesRoot -PathType Container)) {
            throw "FilesRoot must be an existing directory: $FilesRoot"
        }

        $resolvedRoot = (Resolve-Path -LiteralPath $FilesRoot).Path
    }

    $updated = [pscustomobject]@{
        profile = $Profile
        files_root = $resolvedRoot
        tunnel_profile = if ($Profile -eq "semantic-direct") {
            "direct-stdio"
        }
        else {
            "local-1mcp"
        }
    }

    Save-SharedSettings $updated

    Write-Host "DEFAULT_PROFILE=$Profile"
    if ($FilesRootProfiles -contains $Profile) {
        Write-Host "FILES_ROOT=$resolvedRoot"
    }
    Write-Host "TUNNEL_BINDING=$($updated.tunnel_profile)"
}

if ($Action -eq "Status") {
    $ownerController = Get-EffectiveOwnerControllerPath
    if (
        -not [string]::IsNullOrWhiteSpace($ownerController) -and
        -not (Test-SamePath -Left $ownerController -Right $ControllerPath)
    ) {
        Invoke-ControllerStatusAt -TargetControllerPath $ownerController
    }
    else {
        Invoke-ControllerStatusAt -TargetControllerPath $ControllerPath
    }

    exit $script:LastControllerExitCode
}

Initialize-ManagerStateDirectory
$mutex = New-Object System.Threading.Mutex($false, $MutexName)
$acquired = $false
$exitCode = 1

try {
    try {
        $acquired = $mutex.WaitOne($MutexTimeoutMilliseconds)
    }
    catch [System.Threading.AbandonedMutexException] {
        $acquired = $true
    }

    if (-not $acquired) {
        throw (
            "Another Chat Agent Platform lifecycle operation is still running. " +
            "Retry after it finishes."
        )
    }

    if ($Action -eq "SetProfile") {
        Set-SharedProfile
        $exitCode = 0
    }
    else {
        $ownerController = Get-EffectiveOwnerControllerPath
        $foreignOwner = (
            -not [string]::IsNullOrWhiteSpace($ownerController) -and
            -not (Test-SamePath -Left $ownerController -Right $ControllerPath)
        )

        if ($Action -eq "Stop" -and $foreignOwner) {
            Invoke-InternalControllerMutation `
                -TargetControllerPath $ownerController `
                -TargetAction "Stop"
            $exitCode = $script:LastControllerExitCode
            if ($exitCode -eq 0) {
                Remove-ManagerOwner
            }
        }
        elseif ($Action -eq "Toggle" -and $foreignOwner) {
            Invoke-InternalControllerMutation `
                -TargetControllerPath $ownerController `
                -TargetAction "Stop"
            $exitCode = $script:LastControllerExitCode
            if ($exitCode -eq 0) {
                Remove-ManagerOwner
            }
        }
        else {
            if ($Action -eq "Start") {
                if ($foreignOwner) {
                    $null = Stop-ForeignManagerIfNeeded
                }
                else {
                    $ownerIsCurrent = (
                        -not [string]::IsNullOrWhiteSpace($ownerController) -and
                        (Test-SamePath -Left $ownerController -Right $ControllerPath)
                    )

                    if (-not $ownerIsCurrent) {
                        Assert-SharedRuntimeFree
                    }
                    elseif (
                        (Test-AnySharedRuntime) -and
                        -not (Test-CurrentManagerActive)
                    ) {
                        throw (
                            "The current manager owns shared state but does not " +
                            "authoritatively report a ready runtime. Refusing " +
                            "ambiguous startup. Port=$(Get-McpPortDiagnostic); " +
                            "Direct=$(Get-DirectTunnelDiagnostic)"
                        )
                    }
                }
            }

            Invoke-InternalControllerMutation `
                -TargetControllerPath $ControllerPath `
                -TargetAction $Action
            $exitCode = $script:LastControllerExitCode

            if ($exitCode -eq 0) {
                switch ($Action) {
                    "Start" {
                        Save-ManagerOwner
                    }
                    "Stop" {
                        Remove-ManagerOwner
                    }
                    "Toggle" {
                        $effectiveController = Get-OwnerControllerPathForSave
                        $status = Get-ControllerStatusObjectAt `
                            -TargetControllerPath $effectiveController
                        if (
                            [int]$status.active_count -eq 1 -or
                            [bool]$status.tunnel_running
                        ) {
                            Save-ManagerOwner
                        }
                        else {
                            Remove-ManagerOwner
                        }
                    }
                }
            }
        }
    }
}
finally {
    if ($acquired) {
        try {
            $mutex.ReleaseMutex()
        }
        catch {
            # Process/session teardown still closes the handle. Do not hide the
            # result of the lifecycle operation with a release-only error.
        }
    }

    $mutex.Dispose()
}

exit $exitCode
