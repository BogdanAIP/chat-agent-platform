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
        $code = [int]$StatusCode
        switch ($code) {
            401 { return 'unauthorized' }
            403 { return 'forbidden' }
            404 { return 'resource_missing' }
            429 { return 'rate_limited' }
        }
        if ($code -ge 500 -and $code -le 599) {
            return 'service_unavailable'
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($InvocationError)) {
        return 'unavailable'
    }

    return 'unknown'
}

function Get-TunnelEndToEndHealth {
    param(
        [ValidateRange(0, 100)]
        [int]$TunnelProcessCount,

        [ValidateRange(0, 100)]
        [int]$SemanticProcessCount,

        [bool]$HealthzOk,
        [bool]$ReadyzOk,
        [bool]$ControlPlanePollOk,
        [Nullable[double]]$ControlPlanePollAgeSeconds,

        [ValidateSet(
            'ready',
            'resource_missing',
            'unauthorized',
            'forbidden',
            'rate_limited',
            'service_unavailable',
            'unavailable',
            'unknown'
        )]
        [string]$RemoteStatus,

        [bool]$Conflict = $false
    )

    $pollFresh = (
        $ControlPlanePollOk -and
        $null -ne $ControlPlanePollAgeSeconds -and
        [double]$ControlPlanePollAgeSeconds -ge 0 -and
        [double]$ControlPlanePollAgeSeconds -le $script:TunnelPollFreshnessSeconds
    )

    $tunnelLocalReady = (
        -not $Conflict -and
        $TunnelProcessCount -eq 1 -and
        $HealthzOk
    )
    $semanticProcessReady = (
        -not $Conflict -and
        $SemanticProcessCount -eq 1
    )
    $mcpReady = (
        $tunnelLocalReady -and
        $semanticProcessReady -and
        $ReadyzOk
    )
    $runtimeReady = ($mcpReady -and $pollFresh)
    $openAiControlReady = ($RemoteStatus -eq 'ready' -and $pollFresh)

    $code = 'READY'
    $recoveryAction = 'none'

    # Conclusive remote authorization/resource failures outrank local restart
    # symptoms. Restarting the local daemon cannot repair them.
    if ($RemoteStatus -eq 'resource_missing') {
        $code = 'REMOTE_TUNNEL_RESOURCE_MISSING'
        $recoveryAction = 'blocked'
    }
    elseif ($RemoteStatus -eq 'unauthorized') {
        $code = 'REMOTE_TUNNEL_UNAUTHORIZED'
        $recoveryAction = 'blocked'
    }
    elseif ($RemoteStatus -eq 'forbidden') {
        $code = 'REMOTE_TUNNEL_FORBIDDEN'
        $recoveryAction = 'blocked'
    }
    elseif ($Conflict -or $TunnelProcessCount -gt 1 -or $SemanticProcessCount -gt 1) {
        $code = 'LOCAL_RUNTIME_CONFLICT'
        $recoveryAction = 'blocked'
    }
    elseif ($TunnelProcessCount -eq 0) {
        $code = 'LOCAL_TUNNEL_NOT_RUNNING'
        $recoveryAction = 'restart_runtime'
    }
    elseif (-not $HealthzOk) {
        $code = 'LOCAL_TUNNEL_NOT_HEALTHY'
        $recoveryAction = 'restart_runtime'
    }
    elseif ($SemanticProcessCount -eq 0) {
        $code = 'LOCAL_MCP_PROCESS_MISSING'
        $recoveryAction = 'restart_runtime'
    }
    elseif ($RemoteStatus -in @('rate_limited', 'service_unavailable', 'unavailable')) {
        # A live local daemon must not be churned just because the metadata
        # endpoint is temporarily unavailable. If its poll loop is also stale,
        # wait/re-probe first; a later observation may promote a local restart.
        $code = if ($RemoteStatus -eq 'rate_limited') {
            'REMOTE_METADATA_RATE_LIMITED'
        }
        else {
            'REMOTE_METADATA_UNAVAILABLE'
        }
        $recoveryAction = 'wait_and_probe'
    }
    elseif (-not $pollFresh) {
        $code = 'REMOTE_TUNNEL_DISCONNECTED'
        $recoveryAction = 'restart_runtime'
    }
    elseif (-not $ReadyzOk) {
        $code = 'LOCAL_MCP_UNAVAILABLE'
        $recoveryAction = 'restart_runtime'
    }
    elseif ($RemoteStatus -eq 'unknown') {
        $code = 'REMOTE_METADATA_UNKNOWN'
        $recoveryAction = 'wait_and_probe'
    }

    return [pscustomobject]@{
        code = $code
        recovery_action = $recoveryAction
        recoverable = ($recoveryAction -in @('restart_runtime', 'wait_and_probe'))
        runtime_ready = $runtimeReady
        mcp_ready = $mcpReady
        semantic_process_ready = $semanticProcessReady
        tunnel_local_ready = $tunnelLocalReady
        openai_control_ready = $openAiControlReady
        remote_status = $RemoteStatus
        control_plane_poll_fresh = $pollFresh
        poll_freshness_seconds = $script:TunnelPollFreshnessSeconds
    }
}
