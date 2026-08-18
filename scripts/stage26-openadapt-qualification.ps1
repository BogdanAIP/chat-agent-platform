[CmdletBinding()]
param(
    [switch]$RunTutorial,
    [switch]$KeepEnvironment,
    [string]$OutputRoot = (Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage26\openadapt-qualification')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Flag {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [AllowNull()]$Value
    )
    $rendered = if ($null -eq $Value) { '<null>' } else { [string]$Value }
    Write-Host ("{0}={1}" -f $Name, $rendered)
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList,
        [Parameter(Mandatory = $true)][string]$Label
    )

    & $FilePath @ArgumentList
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "$Label failed with exit code $exitCode"
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$lockPath = Join-Path $repoRoot 'config\stage26-openadapt-lock.json'
if (-not (Test-Path -LiteralPath $lockPath -PathType Leaf)) {
    throw "Stage 26 OpenAdapt lock not found: $lockPath"
}

$lock = Get-Content -LiteralPath $lockPath -Raw -Encoding utf8 | ConvertFrom-Json
if ([int]$lock.schema_version -ne 1) {
    throw "Unsupported Stage 26 OpenAdapt lock schema: $($lock.schema_version)"
}

$flow = $lock.upstreams.openadapt_flow
$capture = $lock.upstreams.openadapt_capture
$requiredPython = [string]$lock.python.required_major_minor

foreach ($entry in @($flow, $capture)) {
    if ([string]::IsNullOrWhiteSpace([string]$entry.repository) -or
        [string]::IsNullOrWhiteSpace([string]$entry.commit) -or
        [string]::IsNullOrWhiteSpace([string]$entry.declared_version)) {
        throw 'OpenAdapt qualification lock contains an incomplete upstream entry.'
    }
    if ([string]$entry.license -ne 'MIT') {
        throw "Unexpected upstream license in qualification lock: $($entry.repository) = $($entry.license)"
    }
    if (-not ([string]$entry.commit -match '^[0-9a-f]{40}$')) {
        throw "Invalid pinned commit for $($entry.repository): $($entry.commit)"
    }
}

$timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$runDir = Join-Path $OutputRoot "qualification-$timestamp"
$venvDir = Join-Path $runDir 'venv'
$probePath = Join-Path $runDir 'probe.py'
$probeResultPath = Join-Path $runDir 'probe-result.json'
$probeErrorPath = Join-Path $runDir 'probe-error.log'
$resultPath = Join-Path $runDir 'result.json'
$tutorialDir = Join-Path $runDir 'tutorial'
$tutorialLog = Join-Path $runDir 'tutorial.log'
$playwrightBrowsers = Join-Path $runDir 'playwright-browsers'

New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$chromeBefore = @(Get-Process chrome -ErrorAction SilentlyContinue).Count
$projectHead = $null
$gitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
if ($null -ne $gitCommand) {
    try {
        $projectHead = (& $gitCommand.Source -C $repoRoot rev-parse HEAD 2>$null | Select-Object -Last 1).Trim()
    }
    catch {
        $projectHead = $null
    }
}

$result = [ordered]@{
    schema_version = 1
    created_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    project_head = $projectHead
    expected_project_base_main = [string]$lock.project_base_main
    lock_path = $lockPath
    required_python = $requiredPython
    python_version = $null
    flow_repository = [string]$flow.repository
    flow_expected_commit = [string]$flow.commit
    flow_expected_version = [string]$flow.declared_version
    flow_installed_commit = $null
    flow_installed_version = $null
    capture_repository = [string]$capture.repository
    capture_expected_commit = [string]$capture.commit
    capture_expected_version = [string]$capture.declared_version
    capture_installed_commit = $null
    capture_installed_version = $null
    symbols = $null
    phase_b_pass = $false
    tutorial_requested = [bool]$RunTutorial
    tutorial_exit_code = $null
    tutorial_verified_marker = $null
    phase_c_tutorial_pass = $null
    chrome_process_count_before = $chromeBefore
    chrome_process_count_after = $null
    environment_kept = [bool]$KeepEnvironment
    result_dir = $runDir
    probe_error = $null
    error = $null
}

try {
    $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -eq $pyLauncher) {
        throw 'Windows Python launcher py.exe is required for the isolated Python 3.12 qualification environment.'
    }

    $pythonProbe = & $pyLauncher.Source "-$requiredPython" -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python $requiredPython is not available through py.exe. Install Python $requiredPython before running this qualification gate."
    }
    $pythonVersion = (($pythonProbe | Select-Object -Last 1) -as [string]).Trim()
    if (-not $pythonVersion.StartsWith("$requiredPython.")) {
        throw "Resolved Python version $pythonVersion does not match required $requiredPython.x"
    }
    $result.python_version = $pythonVersion

    Invoke-Checked -FilePath $pyLauncher.Source -ArgumentList @("-$requiredPython", '-m', 'venv', $venvDir) -Label 'Create qualification venv'

    $pythonExe = Join-Path $venvDir 'Scripts\python.exe'
    $flowCli = Join-Path $venvDir 'Scripts\openadapt-flow.exe'
    if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
        throw "Qualification Python executable was not created: $pythonExe"
    }

    $captureSpec = "openadapt-capture @ git+https://github.com/$($capture.repository).git@$($capture.commit)"
    if ($RunTutorial) {
        $flowSpec = "openadapt-flow[browser,windows] @ git+https://github.com/$($flow.repository).git@$($flow.commit)"
    }
    else {
        $flowSpec = "openadapt-flow[windows] @ git+https://github.com/$($flow.repository).git@$($flow.commit)"
    }

    Invoke-Checked -FilePath $pythonExe -ArgumentList @(
        '-m', 'pip', 'install', '--disable-pip-version-check', '--no-input', '--no-cache-dir', $captureSpec
    ) -Label 'Install pinned openadapt-capture'

    Invoke-Checked -FilePath $pythonExe -ArgumentList @(
        '-m', 'pip', 'install', '--disable-pip-version-check', '--no-input', '--no-cache-dir', $flowSpec
    ) -Label 'Install pinned openadapt-flow'

    $probe = @'
import json
import sys
from importlib import metadata

from openadapt_flow.ir import ProgramGraph, Workflow
from openadapt_flow.learning.library import SkillLibrary
from openadapt_flow.learning.teach import teach
from openadapt_flow.runtime.grounder import Grounder
from openadapt_flow.desktop_record import record_desktop_capture
from openadapt_flow.backends.windows_backend import WindowsBackend


def direct_url(name: str):
    dist = metadata.distribution(name)
    raw = dist.read_text('direct_url.json')
    if not raw:
        return None
    return json.loads(raw)


def commit_id(name: str):
    data = direct_url(name) or {}
    return (data.get('vcs_info') or {}).get('commit_id')

result = {
    'python_version': '.'.join(map(str, sys.version_info[:3])),
    'flow_version': metadata.version('openadapt-flow'),
    'flow_commit': commit_id('openadapt-flow'),
    'capture_version': metadata.version('openadapt-capture'),
    'capture_commit': commit_id('openadapt-capture'),
    'symbols': {
        'Workflow': Workflow.__name__,
        'ProgramGraph': ProgramGraph.__name__,
        'SkillLibrary': SkillLibrary.__name__,
        'teach_callable': callable(teach),
        'Grounder_protocol': Grounder.__name__,
        'record_desktop_capture_callable': callable(record_desktop_capture),
        'WindowsBackend': WindowsBackend.__name__,
    },
}
print(json.dumps(result, sort_keys=True))
'@
    Set-Content -LiteralPath $probePath -Value $probe -Encoding utf8

    $probeOutput = & $pythonExe $probePath 2>&1
    $probeExitCode = $LASTEXITCODE
    if ($probeExitCode -ne 0) {
        $probeOutput | Set-Content -LiteralPath $probeErrorPath -Encoding utf8
        $result.probe_error = (($probeOutput | Select-Object -Last 20) -join "`n")
        throw "OpenAdapt import/direct-url probe failed with exit code $probeExitCode"
    }

    $probeJson = ($probeOutput | Select-Object -Last 1) -as [string]
    $probeResult = $probeJson | ConvertFrom-Json
    $probeJson | Set-Content -LiteralPath $probeResultPath -Encoding utf8

    $result.flow_installed_version = [string]$probeResult.flow_version
    $result.flow_installed_commit = [string]$probeResult.flow_commit
    $result.capture_installed_version = [string]$probeResult.capture_version
    $result.capture_installed_commit = [string]$probeResult.capture_commit
    $result.symbols = $probeResult.symbols

    if ($result.flow_installed_version -ne $result.flow_expected_version) {
        throw "Flow version mismatch: expected $($result.flow_expected_version), got $($result.flow_installed_version)"
    }
    if ($result.flow_installed_commit -ne $result.flow_expected_commit) {
        throw "Flow commit mismatch: expected $($result.flow_expected_commit), got $($result.flow_installed_commit)"
    }
    if ($result.capture_installed_version -ne $result.capture_expected_version) {
        throw "Capture version mismatch: expected $($result.capture_expected_version), got $($result.capture_installed_version)"
    }
    if ($result.capture_installed_commit -ne $result.capture_expected_commit) {
        throw "Capture commit mismatch: expected $($result.capture_expected_commit), got $($result.capture_installed_commit)"
    }

    $result.phase_b_pass = $true

    if ($RunTutorial) {
        New-Item -ItemType Directory -Force -Path $tutorialDir | Out-Null
        $oldBrowsersPath = $env:PLAYWRIGHT_BROWSERS_PATH
        try {
            $env:PLAYWRIGHT_BROWSERS_PATH = $playwrightBrowsers
            Invoke-Checked -FilePath $pythonExe -ArgumentList @('-m', 'playwright', 'install', 'chromium') -Label 'Install isolated Playwright Chromium'

            Push-Location $tutorialDir
            try {
                $tutorialOutput = & $flowCli tutorial 2>&1
                $tutorialExit = $LASTEXITCODE
            }
            finally {
                Pop-Location
            }

            $tutorialOutput | Set-Content -LiteralPath $tutorialLog -Encoding utf8
            $result.tutorial_exit_code = $tutorialExit
            $tutorialText = $tutorialOutput -join "`n"
            $verified = [bool]($tutorialText -match '(?m)\bVERIFIED\b')
            $result.tutorial_verified_marker = $verified
            $result.phase_c_tutorial_pass = [bool]($tutorialExit -eq 0 -and $verified)

            if (-not $result.phase_c_tutorial_pass) {
                throw "OpenAdapt tutorial did not produce an accepted VERIFIED exit-0 result. See $tutorialLog"
            }
        }
        finally {
            if ($null -eq $oldBrowsersPath) {
                Remove-Item Env:PLAYWRIGHT_BROWSERS_PATH -ErrorAction SilentlyContinue
            }
            else {
                $env:PLAYWRIGHT_BROWSERS_PATH = $oldBrowsersPath
            }
        }
    }
}
catch {
    $result.error = $_.Exception.Message
}
finally {
    $result.chrome_process_count_after = @(Get-Process chrome -ErrorAction SilentlyContinue).Count

    if (-not $KeepEnvironment) {
        foreach ($path in @($venvDir, $playwrightBrowsers)) {
            if (Test-Path -LiteralPath $path) {
                Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }

    $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding utf8
}

Write-Host ''
Write-Host '===== STAGE 26.1A OPENADAPT QUALIFICATION =====' -ForegroundColor Cyan
Write-Flag 'RESULT_PATH' $resultPath
Write-Flag 'PYTHON_VERSION' $result.python_version
Write-Flag 'FLOW_EXPECTED_COMMIT' $result.flow_expected_commit
Write-Flag 'FLOW_INSTALLED_COMMIT' $result.flow_installed_commit
Write-Flag 'FLOW_INSTALLED_VERSION' $result.flow_installed_version
Write-Flag 'CAPTURE_EXPECTED_COMMIT' $result.capture_expected_commit
Write-Flag 'CAPTURE_INSTALLED_COMMIT' $result.capture_installed_commit
Write-Flag 'CAPTURE_INSTALLED_VERSION' $result.capture_installed_version
Write-Flag 'PHASE_B_PASS' $result.phase_b_pass
Write-Flag 'TUTORIAL_REQUESTED' $result.tutorial_requested
Write-Flag 'PHASE_C_TUTORIAL_PASS' $result.phase_c_tutorial_pass
Write-Flag 'CHROME_PROCESS_COUNT_BEFORE' $result.chrome_process_count_before
Write-Flag 'CHROME_PROCESS_COUNT_AFTER' $result.chrome_process_count_after
Write-Flag 'PROBE_ERROR' $result.probe_error
Write-Flag 'ERROR' $result.error

$accepted = [bool]$result.phase_b_pass
if ($RunTutorial) {
    $accepted = $accepted -and [bool]$result.phase_c_tutorial_pass
}

if (-not $accepted -or $null -ne $result.error) {
    Write-Flag 'STAGE26_1A_PREFLIGHT_RESULT' 'FAILED'
    exit 1
}

Write-Flag 'STAGE26_1A_PREFLIGHT_RESULT' 'PASSED'
exit 0