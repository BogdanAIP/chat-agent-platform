[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$QualificationRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Test-CaseEqual {
    param([Parameter(Mandatory = $true)]$Left, [Parameter(Mandatory = $true)]$Right)
    if ([string]$Left.id -cne [string]$Right.id) { return $false }
    if ([string]$Left.client -cne [string]$Right.client) { return $false }
    if ([string]$Left.status -cne [string]$Right.status) { return $false }
    $leftNotes = @($Left.notes | ForEach-Object { [string]$_ })
    $rightNotes = @($Right.notes | ForEach-Object { [string]$_ })
    if ($leftNotes.Count -ne $rightNotes.Count) { return $false }
    for ($i = 0; $i -lt $leftNotes.Count; $i += 1) {
        if ($leftNotes[$i] -cne $rightNotes[$i]) { return $false }
    }
    return $true
}

function Get-UniqueCase {
    param([Parameter(Mandatory = $true)]$Cases, [Parameter(Mandatory = $true)][string]$CaseId)
    $matches = @($Cases | Where-Object { [string]$_.id -ceq $CaseId })
    if ($matches.Count -ne 1) { throw "Expected exactly one case '$CaseId', found $($matches.Count)." }
    return $matches[0]
}

function Test-IsOutsideWorkspace {
    param([Parameter(Mandatory = $true)][string]$Workspace, [Parameter(Mandatory = $true)][string]$EvidenceRoot)
    $workspaceFull = [System.IO.Path]::GetFullPath($Workspace).TrimEnd('\') + '\'
    $evidenceFull = [System.IO.Path]::GetFullPath($EvidenceRoot).TrimEnd('\') + '\'
    return -not $evidenceFull.StartsWith($workspaceFull, [System.StringComparison]::OrdinalIgnoreCase)
}

$QualificationRoot = [System.IO.Path]::GetFullPath($QualificationRoot)
$manifestPath = Join-Path $QualificationRoot 'gate-manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Gate manifest is missing: $manifestPath"
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding utf8 | ConvertFrom-Json
$resultPath = Join-Path $QualificationRoot 'finish-gate-result.json'

$result = [ordered]@{
    schema_version = 1
    exact_head = [string]$manifest.exact_head
    run_id = [string]$manifest.run_id
    target_case = [string]$manifest.target_case
    source_provenance_pass = $false
    installed_runtime_provenance_pass = $false
    runtime_attestation_pass = $false
    evidence_outside_chat_workspace = $false
    target_final_state_pass = $false
    decoys_unchanged = $false
    only_target_ever_mutated = $false
    audit_target_save_exactly_once = $false
    audit_before_matches_seed = $false
    audit_after_matches_final = $false
    fixture_process_was_live = $false
    fixture_killed = $false
    fixture_cleanup_pass = $false
    active_session_cleanup_pass = $false
    finish_gate = 'not_done'
    error = $null
}

$fixtureProcess = $null
try {
    $workspaceRoot = [string]$manifest.workspace_root
    $fixtureRoot = [string]$manifest.fixture_root
    $seedPath = [string]$manifest.seed_path
    $statePath = [string]$manifest.state_path
    $auditPath = [string]$manifest.audit_path
    $sourceProvenancePath = [string]$manifest.source_provenance_path
    $installedProvenancePath = [string]$manifest.installed_runtime_provenance_path
    $runtimeAttestationPath = [string]$manifest.runtime_attestation_path

    $result.evidence_outside_chat_workspace = [bool](
        (Test-IsOutsideWorkspace -Workspace $workspaceRoot -EvidenceRoot $fixtureRoot) -and
        (Test-IsOutsideWorkspace -Workspace $workspaceRoot -EvidenceRoot (Split-Path -Parent $sourceProvenancePath))
    )
    if (-not $result.evidence_outside_chat_workspace) {
        throw 'Independent fixture/provenance evidence must not live inside the Chat workspace.'
    }

    $sourceProvenance = Get-Content -LiteralPath $sourceProvenancePath -Raw -Encoding utf8 | ConvertFrom-Json
    $result.source_provenance_pass = [bool](
        [string]$sourceProvenance.status -eq 'pass' -and
        [string]$sourceProvenance.expected_head -eq [string]$manifest.exact_head -and
        [string]$sourceProvenance.actual_head -eq [string]$manifest.exact_head -and
        [bool]$sourceProvenance.working_tree_clean -and
        [bool]$sourceProvenance.tracked_diff_empty -and
        [bool]$sourceProvenance.untracked_empty
    )

    $installed = Get-Content -LiteralPath $installedProvenancePath -Raw -Encoding utf8 | ConvertFrom-Json
    $result.installed_runtime_provenance_pass = [bool](
        [string]$installed.exact_head -eq [string]$manifest.exact_head -and
        [bool]$installed.all_match -and
        @($installed.assets).Count -ge 8 -and
        @($installed.assets | Where-Object { -not [bool]$_.match }).Count -eq 0
    )

    $runtime = Get-Content -LiteralPath $runtimeAttestationPath -Raw -Encoding utf8 | ConvertFrom-Json
    $result.runtime_attestation_pass = [bool](
        [string]$runtime.status -eq 'pass' -and
        [bool]$runtime.version_match -and
        [string]$runtime.win_agent_server_sha256 -match '^[0-9a-f]{64}$'
    )

    $seed = Get-Content -LiteralPath $seedPath -Raw -Encoding utf8 | ConvertFrom-Json
    $state = Get-Content -LiteralPath $statePath -Raw -Encoding utf8 | ConvertFrom-Json
    if ([string]$seed.run_id -ne [string]$manifest.run_id -or [string]$state.run_id -ne [string]$manifest.run_id) {
        throw 'Run identity mismatch across manifest/seed/final state.'
    }

    $targetId = [string]$manifest.target_case
    $expectedStatus = [string]$manifest.expected_status
    $expectedNote = [string]$manifest.expected_note
    $seedTarget = Get-UniqueCase -Cases $seed.cases -CaseId $targetId
    $finalTarget = Get-UniqueCase -Cases $state.cases -CaseId $targetId
    $seedTargetNotes = @($seedTarget.notes | ForEach-Object { [string]$_ })
    $finalTargetNotes = @($finalTarget.notes | ForEach-Object { [string]$_ })

    $prefixMatches = $true
    if ($finalTargetNotes.Count -ne ($seedTargetNotes.Count + 1)) {
        $prefixMatches = $false
    }
    else {
        for ($i = 0; $i -lt $seedTargetNotes.Count; $i += 1) {
            if ($finalTargetNotes[$i] -cne $seedTargetNotes[$i]) { $prefixMatches = $false; break }
        }
    }
    $result.target_final_state_pass = [bool](
        [string]$finalTarget.id -ceq [string]$seedTarget.id -and
        [string]$finalTarget.client -ceq [string]$seedTarget.client -and
        [string]$finalTarget.status -ceq $expectedStatus -and
        $prefixMatches -and
        $finalTargetNotes[-1] -ceq $expectedNote -and
        [int]$state.save_count -eq 1
    )

    $decoysPass = $true
    foreach ($seedCase in @($seed.cases)) {
        if ([string]$seedCase.id -ceq $targetId) { continue }
        $finalCase = Get-UniqueCase -Cases $state.cases -CaseId ([string]$seedCase.id)
        if (-not (Test-CaseEqual -Left $seedCase -Right $finalCase)) {
            $decoysPass = $false
            break
        }
    }
    $result.decoys_unchanged = $decoysPass

    $auditEvents = @()
    if (Test-Path -LiteralPath $auditPath -PathType Leaf) {
        foreach ($line in @(Get-Content -LiteralPath $auditPath -Encoding utf8)) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            $auditEvents += @($line | ConvertFrom-Json)
        }
    }
    $result.only_target_ever_mutated = [bool](
        $auditEvents.Count -gt 0 -and
        @($auditEvents | Where-Object { [string]$_.case_id -cne $targetId }).Count -eq 0
    )
    $result.audit_target_save_exactly_once = [bool](
        $auditEvents.Count -eq 1 -and
        [string]$auditEvents[0].event -eq 'case_saved' -and
        [int]$auditEvents[0].save_index -eq 1 -and
        [string]$auditEvents[0].case_id -ceq $targetId
    )
    if ($auditEvents.Count -eq 1) {
        $result.audit_before_matches_seed = Test-CaseEqual -Left $auditEvents[0].before -Right $seedTarget
        $result.audit_after_matches_final = Test-CaseEqual -Left $auditEvents[0].after -Right $finalTarget
    }

    try {
        $fixtureProcess = Get-Process -Id ([int]$manifest.fixture_pid) -ErrorAction Stop
        $result.fixture_process_was_live = -not $fixtureProcess.HasExited
    }
    catch {
        $result.fixture_process_was_live = $false
    }

    $done = [bool](
        $result.source_provenance_pass -and
        $result.installed_runtime_provenance_pass -and
        $result.runtime_attestation_pass -and
        $result.evidence_outside_chat_workspace -and
        $result.target_final_state_pass -and
        $result.decoys_unchanged -and
        $result.only_target_ever_mutated -and
        $result.audit_target_save_exactly_once -and
        $result.audit_before_matches_seed -and
        $result.audit_after_matches_final
    )
    $result.finish_gate = if ($done) { 'done' } else { 'not_done' }
}
catch {
    $result.error = $_.Exception.Message
}
finally {
    try {
        Set-Content -LiteralPath ([string]$manifest.close_path) -Value 'CLOSE' -Encoding ascii -ErrorAction SilentlyContinue
    }
    catch {}

    if ($null -eq $fixtureProcess) {
        try { $fixtureProcess = Get-Process -Id ([int]$manifest.fixture_pid) -ErrorAction Stop } catch {}
    }
    if ($null -ne $fixtureProcess) {
        try {
            if (-not $fixtureProcess.HasExited) {
                [void]$fixtureProcess.WaitForExit(5000)
                $fixtureProcess.Refresh()
            }
            if (-not $fixtureProcess.HasExited) {
                $fixtureProcess.Kill($true)
                $result.fixture_killed = $true
                [void]$fixtureProcess.WaitForExit(5000)
            }
            $result.fixture_cleanup_pass = $fixtureProcess.HasExited -and -not $result.fixture_killed
        }
        catch {
            $result.fixture_cleanup_pass = $false
        }
    }
    else {
        $result.fixture_cleanup_pass = $true
    }

    try {
        $activeSessionPath = [string]$manifest.active_session_path
        if (Test-Path -LiteralPath $activeSessionPath -PathType Leaf) {
            $active = Get-Content -LiteralPath $activeSessionPath -Raw -Encoding utf8 | ConvertFrom-Json
            if ([string]$active.run_id -ceq [string]$manifest.run_id) {
                Remove-Item -LiteralPath $activeSessionPath -Force
            }
        }
        $result.active_session_cleanup_pass = -not (Test-Path -LiteralPath $activeSessionPath -PathType Leaf)
    }
    catch {
        $result.active_session_cleanup_pass = $false
    }

    $result | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $resultPath -Encoding utf8
}

$accepted = [bool](
    $result.finish_gate -eq 'done' -and
    $result.fixture_cleanup_pass -and
    $result.active_session_cleanup_pass -and
    $null -eq $result.error
)

Write-Host '===== STAGE 26.3B WINDOWS APPLICATION L3 FINISH GATE ====='
Write-Host "RESULT_PATH=$resultPath"
Write-Host "EXACT_HEAD=$($result.exact_head)"
Write-Host "RUN_ID=$($result.run_id)"
Write-Host "TARGET_CASE=$($result.target_case)"
Write-Host "SOURCE_PROVENANCE_GATE=$(if ($result.source_provenance_pass) { 'PASS' } else { 'FAIL' })"
Write-Host "INSTALLED_RUNTIME_PROVENANCE=$(if ($result.installed_runtime_provenance_pass) { 'PASS' } else { 'FAIL' })"
Write-Host "WINDOWS_RUNTIME_ATTESTATION=$(if ($result.runtime_attestation_pass) { 'PASS' } else { 'FAIL' })"
Write-Host "EVIDENCE_OUTSIDE_CHAT_WORKSPACE=$($result.evidence_outside_chat_workspace)"
Write-Host "TARGET_FINAL_STATE=$($result.target_final_state_pass)"
Write-Host "DECOYS_UNCHANGED=$($result.decoys_unchanged)"
Write-Host "ONLY_TARGET_EVER_MUTATED=$($result.only_target_ever_mutated)"
Write-Host "AUDIT_TARGET_SAVE_EXACTLY_ONCE=$($result.audit_target_save_exactly_once)"
Write-Host "AUDIT_BEFORE_MATCHES_SEED=$($result.audit_before_matches_seed)"
Write-Host "AUDIT_AFTER_MATCHES_FINAL=$($result.audit_after_matches_final)"
Write-Host "EXTERNAL_FINISH_GATE=$($result.finish_gate.ToUpperInvariant())"
Write-Host "FIXTURE_KILLED=$($result.fixture_killed)"
Write-Host "FIXTURE_CLEANUP_PASS=$($result.fixture_cleanup_pass)"
Write-Host "ACTIVE_SESSION_CLEANUP_PASS=$($result.active_session_cleanup_pass)"
Write-Host "ERROR=$($result.error)"
Write-Host "STAGE26_3B_WINDOWS_APPLICATION_L3=$(if ($accepted) { 'PASS' } else { 'FAIL' })"

if (-not $accepted) { exit 1 }
exit 0
