[CmdletBinding()]
param(
    [ValidateSet("Install", "Start", "Stop", "Toggle", "Status", "SetProfile")]
    [string]$Action = "Status",

    [ValidateSet("reference", "files-readonly", "browser-isolated", "adaptive")]
    [string]$Profile,

    [string]$FilesRoot,

    [switch]$NoNotify
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ControllerPath = Join-Path $PSScriptRoot "chat-platform-controller.ps1"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$LocalRoot = Join-Path $env:LOCALAPPDATA "ChatAgentPlatform"
$StateDir = Join-Path $LocalRoot "state"
$OwnerFile = Join-Path $StateDir "manager-owner.json"
$McpPort = 3050
$MutexName = "Local\ChatAgentPlatformControllerOperation"
$MutexTimeoutMilliseconds = 30000
$script:LastControllerExitCode = 1

if (-not (Test-Path -LiteralPath $ControllerPath)) {
    throw "Internal controller is missing: $ControllerPath"
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

function Save-ManagerOwner {
    Initialize-ManagerStateDirectory

    $payload = [ordered]@{
        schema_version = 1
        controller_path = [System.IO.Path]::GetFullPath($ControllerPath)
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

function Initialize-ManagerStateDirectory {
    New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
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
            $lines.Add(
                "PID={0}; Name={1}; CommandLine={2}" -f `
                    $pidValue,
                    [string]$process.Name,
                    [string]$process.CommandLine
            )
        }
    }

    return ($lines -join " | ")
}

function Wait-McpPortFree {
    param(
        [ValidateRange(1, 60)]
        [int]$TimeoutSeconds = 15
    )

    for ($attempt = 0; $attempt -lt $TimeoutSeconds; $attempt++) {
        if (@(Get-McpPortListeners).Count -eq 0) {
            return $true
        }
        Start-Sleep -Seconds 1
    }

    return (@(Get-McpPortListeners).Count -eq 0)
}

function Assert-McpPortFree {
    $listeners = @(Get-McpPortListeners)
    if ($listeners.Count -eq 0) {
        return
    }

    $detail = Get-McpPortDiagnostic
    throw (
        "Local MCP port $McpPort is already occupied but no matching active " +
        "manager owner is available. Refusing to accept another process's " +
        "health endpoint. $detail"
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

    if (-not [string]::IsNullOrWhiteSpace($Profile)) {
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

function Invoke-ControllerMutationAt {
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

    # Do not invoke the mutating controller through a PowerShell pipeline.
    # Start/Toggle may spawn long-lived 1MCP/tunnel descendants; if their
    # inherited stdout handle belongs to an outer pipeline, EOF can be held
    # open after the controller itself has completed. Wait on the exact child
    # process handle instead.
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
        if (@(Get-McpPortListeners).Count -gt 0) {
            throw (
                "Shared manager ownership points to a missing controller while " +
                "port $McpPort is still occupied: $ownerController"
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

    Invoke-ControllerMutationAt `
        -TargetControllerPath $ownerController `
        -TargetAction "Stop"

    if ($script:LastControllerExitCode -ne 0) {
        throw (
            "Could not stop the currently owning Chat Agent Platform manager: " +
            $ownerController
        )
    }

    Remove-ManagerOwner

    if (-not (Wait-McpPortFree -TimeoutSeconds 15)) {
        throw (
            "The previous Chat Agent Platform manager stopped, but local MCP " +
            "port $McpPort is still occupied. $(Get-McpPortDiagnostic)"
        )
    }

    return $true
}

function Test-CurrentManagerActive {
    try {
        $status = Get-ControllerStatusObjectAt -TargetControllerPath $ControllerPath
        return (
            [int]$status.active_count -eq 1 -and
            [bool]$status.mcp_ready
        )
    }
    catch {
        return $false
    }
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
        # The previous owner terminated without releasing the mutex. Windows
        # grants ownership to this caller, so lifecycle recovery may continue.
        $acquired = $true
    }

    if (-not $acquired) {
        throw (
            "Another Chat Agent Platform lifecycle operation is still running. " +
            "Retry after it finishes."
        )
    }

    $ownerController = Get-EffectiveOwnerControllerPath
    $foreignOwner = (
        -not [string]::IsNullOrWhiteSpace($ownerController) -and
        -not (Test-SamePath -Left $ownerController -Right $ControllerPath)
    )

    if ($Action -eq "Stop" -and $foreignOwner) {
        Invoke-ControllerMutationAt `
            -TargetControllerPath $ownerController `
            -TargetAction "Stop"
        $exitCode = $script:LastControllerExitCode
        if ($exitCode -eq 0) {
            Remove-ManagerOwner
        }
    }
    elseif ($Action -eq "Toggle" -and $foreignOwner) {
        # A platform owned by another installed/source copy is already on.
        # Toggle therefore means stop that one, not start a second copy.
        Invoke-ControllerMutationAt `
            -TargetControllerPath $ownerController `
            -TargetAction "Stop"
        $exitCode = $script:LastControllerExitCode
        if ($exitCode -eq 0) {
            Remove-ManagerOwner
        }
    }
    elseif ($Action -eq "SetProfile" -and $foreignOwner) {
        # Let the actual owner enforce its active-profile rule against the
        # runtime it can authoritatively observe. Settings live in shared
        # LocalAppData, so successful changes remain global.
        Invoke-ControllerMutationAt `
            -TargetControllerPath $ownerController `
            -TargetAction "SetProfile"
        $exitCode = $script:LastControllerExitCode
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
                    Assert-McpPortFree
                }
                elseif (
                    @(Get-McpPortListeners).Count -gt 0 -and
                    -not (Test-CurrentManagerActive)
                ) {
                    throw (
                        "The current manager owns shared state but does not " +
                        "authoritatively report an active MCP runtime while " +
                        "port $McpPort is occupied. Refusing ambiguous startup. " +
                        "$(Get-McpPortDiagnostic)"
                    )
                }
            }
        }

        Invoke-ControllerMutationAt `
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
                    $status = Get-ControllerStatusObjectAt `
                        -TargetControllerPath $ControllerPath
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
