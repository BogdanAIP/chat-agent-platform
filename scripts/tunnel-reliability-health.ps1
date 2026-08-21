Set-StrictMode -Version Latest

$script:TunnelPollFreshnessSeconds = 120

function ConvertTo-RemoteTunnelStatus {
    param(
        [Nullable[int]]$StatusCode,
        [string]$InvocationError,
        [bool]$Succeeded = $false
    )

    if ($Succeeded) {
        return 'ready'
    }

    if ($null -ne $StatusCode) {
        switch ([int]$StatusCode) {
            404 { return 'resource_missing' }
            401 { return 'unauthorized' }
            403 { return 'forbidden' }
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($InvocationError)) {
        return 'disconnected'
    }

    return 'unknown'
}

function Get-TunnelEndToEndHealth {
    param(
        [ValidateRange(0, 100)]
        [int]$TunnelProcessCount,
        [bool]$HealthzOk,
        [bool]$ReadyzOk,
        [bool]$ControlPlanePollOk,
        [Nullable[double]]$ControlPlanePollAgeSeconds,
        [ValidateSet('ready', 'resource_missing', 'unauthorized', 'forbidden', 'disconnected', 'unknown')]
        [string]$RemoteStatus,
        [bool]$Conflict = $false
    )

    $pollFresh = (
        $ControlPlanePollOk -and
        $null -ne $ControlPlanePollAgeSeconds -and
        [double]$ControlPlanePollAgeSeconds -ge 0 -and
        [double]$ControlPlanePollAgeSeconds -le $script:TunnelPollFreshnessSeconds
    )

    $localTunnelReady = (
        -not $Conflict -and
        $TunnelProcessCount -eq 1 -and
        $HealthzOk
    )
    $mcpReady = ($localTunnelReady -and $ReadyzOk)
    $openAiReady = ($RemoteStatus -eq 'ready' -and $pollFresh)

    $code = 'READY'
    $recoverable = $false

    if ($RemoteStatus -eq 'resource_missing') {
        $code = 'REMOTE_TUNNEL_RESOURCE_MISSING'
    }
    elseif ($RemoteStatus -eq 'unauthorized') {
        $code = 'REMOTE_TUNNEL_UNAUTHORIZED'
    }
    elseif ($RemoteStatus -eq 'forbidden') {
        $code = 'REMOTE_TUNNEL_FORBIDDEN'
    }
    elseif ($Conflict -or $TunnelProcessCount -gt 1) {
        $code = 'LOCAL_RUNTIME_CONFLICT'
    }
    elseif ($TunnelProcessCount -eq 0) {
        $code = 'LOCAL_TUNNEL_NOT_RUNNING'
        $recoverable = $true
    }
    elseif (-not $HealthzOk) {
        $code = 'LOCAL_TUNNEL_NOT_READY'
        $recoverable = $true
    }
    elseif (-not $ReadyzOk) {
        $code = 'LOCAL_MCP_UNAVAILABLE'
        $recoverable = $true
    }
    elseif ($RemoteStatus -in @('disconnected', 'unknown') -or -not $pollFresh) {
        $code = 'REMOTE_TUNNEL_DISCONNECTED'
        $recoverable = $true
    }

    return [pscustomobject]@{
        code = $code
        recoverable = $recoverable
        mcp_ready = $mcpReady
        tunnel_local_ready = $localTunnelReady
        openai_ready = $openAiReady
        remote_status = $RemoteStatus
        control_plane_poll_fresh = $pollFresh
        poll_freshness_seconds = $script:TunnelPollFreshnessSeconds
    }
}
