param(
    [string]$OutputRoot
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-Stage25Browser {
    param(
        [Parameter(Mandatory = $true)][string]$BrowserPath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds
    )

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $BrowserPath
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    foreach ($argument in $Arguments) {
        [void]$startInfo.ArgumentList.Add($argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo

    try {
        if (-not $process.Start()) {
            throw 'Browser process did not start.'
        }

        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()

        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            try { $process.Kill($true) } catch {}
            throw "Browser process timed out after $TimeoutSeconds seconds."
        }

        return [pscustomobject]@{
            ExitCode = $process.ExitCode
            Stdout = $stdoutTask.GetAwaiter().GetResult()
            Stderr = $stderrTask.GetAwaiter().GetResult()
        }
    }
    finally {
        $process.Dispose()
    }
}

function Get-CommonBrowserArguments {
    param(
        [Parameter(Mandatory = $true)][string]$ProfileRoot,
        [Parameter(Mandatory = $true)][int]$WindowWidth,
        [Parameter(Mandatory = $true)][int]$WindowHeight
    )

    return @(
        '--headless=new',
        '--disable-gpu',
        '--disable-extensions',
        '--disable-background-networking',
        '--no-first-run',
        '--no-default-browser-check',
        '--hide-scrollbars',
        '--force-device-scale-factor=1',
        "--window-size=$WindowWidth,$WindowHeight",
        "--user-data-dir=$ProfileRoot"
    )
}

function Get-RenderedFixture {
    param(
        [Parameter(Mandatory = $true)][string]$BrowserPath,
        [Parameter(Mandatory = $true)][string]$FixtureUri,
        [Parameter(Mandatory = $true)][string]$ProfileRoot,
        [Parameter(Mandatory = $true)][int]$WindowWidth,
        [Parameter(Mandatory = $true)][int]$WindowHeight
    )

    Remove-Item -LiteralPath $ProfileRoot -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $ProfileRoot | Out-Null

    $arguments = @(
        (Get-CommonBrowserArguments `
            -ProfileRoot $ProfileRoot `
            -WindowWidth $WindowWidth `
            -WindowHeight $WindowHeight)
    ) + @('--dump-dom', $FixtureUri)

    $result = Invoke-Stage25Browser `
        -BrowserPath $BrowserPath `
        -Arguments $arguments `
        -TimeoutSeconds 60

    if ($result.ExitCode -ne 0) {
        if (-not [string]::IsNullOrWhiteSpace($result.Stderr)) {
            Write-Host $result.Stderr
        }
        throw "Browser --dump-dom failed with exit code $($result.ExitCode)"
    }

    $dumpText = [string]$result.Stdout
    $match = [regex]::Match(
        $dumpText,
        '<pre[^>]*\bid="stage25-fixture-export"[^>]*>(.*?)</pre>',
        [System.Text.RegularExpressions.RegexOptions]::Singleline
    )
    if (-not $match.Success) {
        throw 'Rendered fixture geometry export was not found in browser DOM output.'
    }

    $geometryJson = [System.Net.WebUtility]::HtmlDecode($match.Groups[1].Value).Trim()
    $actual = $geometryJson | ConvertFrom-Json

    return [pscustomobject]@{
        DumpText = $dumpText
        Actual = $actual
        Stderr = [string]$result.Stderr
        WindowWidth = $WindowWidth
        WindowHeight = $WindowHeight
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$fixturePath = Join-Path $repoRoot 'tests\fixtures\stage25_grounding_fixture.html'
$casesPath = Join-Path $repoRoot 'tests\fixtures\stage25_grounding_cases.json'

if (-not (Test-Path -LiteralPath $fixturePath -PathType Leaf)) {
    throw "Fixture HTML is missing: $fixturePath"
}
if (-not (Test-Path -LiteralPath $casesPath -PathType Leaf)) {
    throw "Fixture metadata is missing: $casesPath"
}

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\stage25\runtime\grounding-fixture'
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$OutputRoot = (Resolve-Path -LiteralPath $OutputRoot).Path

$browserCandidates = [System.Collections.Generic.List[string]]::new()
foreach ($commandName in @('msedge.exe', 'chrome.exe')) {
    $command = Get-Command $commandName -ErrorAction SilentlyContinue
    if ($command -and $command.Source) {
        $browserCandidates.Add([string]$command.Source)
    }
}

$standardCandidates = @()
if (-not [string]::IsNullOrWhiteSpace(${env:ProgramFiles(x86)})) {
    $standardCandidates += Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'
    $standardCandidates += Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe'
}
if (-not [string]::IsNullOrWhiteSpace($env:ProgramFiles)) {
    $standardCandidates += Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'
    $standardCandidates += Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'
}
if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    $standardCandidates += Join-Path $env:LOCALAPPDATA 'Google\Chrome\Application\chrome.exe'
}

foreach ($candidate in $standardCandidates) {
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        $browserCandidates.Add($candidate)
    }
}

$browser = $browserCandidates |
    Select-Object -Unique |
    Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
    Select-Object -First 1

if (-not $browser) {
    throw 'No supported Chromium browser (Edge/Chrome) was found.'
}

$fixtureUri = [System.Uri]::new($fixturePath).AbsoluteUri
$dumpProfileRoot = Join-Path $OutputRoot 'browser-profile-dump'
$screenshotProfileRoot = Join-Path $OutputRoot 'browser-profile-screenshot'
$dumpPath = Join-Path $OutputRoot 'fixture-dom.html'
$geometryPath = Join-Path $OutputRoot 'fixture-geometry.json'
$screenshotPath = Join-Path $OutputRoot 'fixture.png'
$stderrPath = Join-Path $OutputRoot 'browser.stderr.log'

Remove-Item -LiteralPath $dumpPath,$geometryPath,$screenshotPath,$stderrPath -Force -ErrorAction SilentlyContinue

$spec = Get-Content -LiteralPath $casesPath -Raw -Encoding utf8 | ConvertFrom-Json
$expectedWidth = [int]$spec.viewport.width
$expectedHeight = [int]$spec.viewport.height

Write-Host "`n===== STAGE 25 BROWSER FIXTURE =====" -ForegroundColor Cyan
Write-Host "BROWSER=$browser"
Write-Host "FIXTURE=$fixturePath"
Write-Host "OUTPUT_ROOT=$OutputRoot"

# Chromium on Windows may interpret --window-size as outer-window dimensions,
# even in new headless mode. Probe once, measure the decoration delta, then
# calibrate so window.innerWidth/innerHeight match the benchmark viewport.
$windowWidth = $expectedWidth
$windowHeight = $expectedHeight
$rendered = Get-RenderedFixture `
    -BrowserPath $browser `
    -FixtureUri $fixtureUri `
    -ProfileRoot $dumpProfileRoot `
    -WindowWidth $windowWidth `
    -WindowHeight $windowHeight

$actualWidth = [int]$rendered.Actual.viewport.width
$actualHeight = [int]$rendered.Actual.viewport.height
Write-Host "VIEWPORT_PROBE=${actualWidth}x${actualHeight}"

if ($actualWidth -ne $expectedWidth -or $actualHeight -ne $expectedHeight) {
    $widthDelta = $windowWidth - $actualWidth
    $heightDelta = $windowHeight - $actualHeight
    $windowWidth = $expectedWidth + $widthDelta
    $windowHeight = $expectedHeight + $heightDelta

    if ($windowWidth -le 0 -or $windowHeight -le 0 -or
        $windowWidth -gt 4096 -or $windowHeight -gt 4096) {
        throw "Unsafe calibrated Chromium window size ${windowWidth}x${windowHeight}."
    }

    Write-Host "VIEWPORT_CALIBRATED_WINDOW=${windowWidth}x${windowHeight}"
    $rendered = Get-RenderedFixture `
        -BrowserPath $browser `
        -FixtureUri $fixtureUri `
        -ProfileRoot $dumpProfileRoot `
        -WindowWidth $windowWidth `
        -WindowHeight $windowHeight

    $actualWidth = [int]$rendered.Actual.viewport.width
    $actualHeight = [int]$rendered.Actual.viewport.height
}

Write-Host "VIEWPORT_EXPECTED=${expectedWidth}x${expectedHeight}"
Write-Host "VIEWPORT_ACTUAL=${actualWidth}x${actualHeight}"

if ($actualWidth -ne $expectedWidth -or $actualHeight -ne $expectedHeight) {
    throw 'Rendered browser viewport does not match fixture metadata after calibration.'
}

Set-Content -LiteralPath $dumpPath -Value $rendered.DumpText -Encoding utf8
$rendered.Actual | ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath $geometryPath -Encoding utf8
Set-Content -LiteralPath $stderrPath -Value $rendered.Stderr -Encoding utf8

$tolerance = 0.01
$verifiedCount = 0

foreach ($case in @($spec.cases)) {
    if ($null -eq $case.target_id) {
        if ($null -ne $case.bbox) {
            throw "Absent target case '$($case.id)' unexpectedly contains a bbox."
        }
        Write-Host "CASE=$($case.id) TARGET_ABSENT=True"
        continue
    }

    $targetId = [string]$case.target_id
    $property = $rendered.Actual.targets.PSObject.Properties[$targetId]
    if ($null -eq $property) {
        throw "Rendered browser output is missing target '$targetId'."
    }

    $rect = $property.Value
    $expected = @($case.bbox | ForEach-Object { [double]$_ })
    if ($expected.Count -ne 4) {
        throw "Case '$($case.id)' must contain four bbox coordinates."
    }

    $observed = @(
        [double]$rect.x,
        [double]$rect.y,
        [double]$rect.x + [double]$rect.width,
        [double]$rect.y + [double]$rect.height
    )

    $matchBox = $true
    for ($i = 0; $i -lt 4; $i++) {
        if ([math]::Abs($expected[$i] - $observed[$i]) -gt $tolerance) {
            $matchBox = $false
        }
    }

    Write-Host "CASE=$($case.id)"
    Write-Host "TARGET_ID=$targetId"
    Write-Host "EXPECTED_BBOX=$($expected -join ',')"
    Write-Host "OBSERVED_BBOX=$($observed -join ',')"
    Write-Host "BBOX_MATCH=$matchBox"

    if (-not $matchBox) {
        throw "Browser geometry drifted for case '$($case.id)'."
    }
    $verifiedCount++
}

Remove-Item -LiteralPath $screenshotProfileRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $screenshotProfileRoot | Out-Null

$screenshotArguments = @(
    (Get-CommonBrowserArguments `
        -ProfileRoot $screenshotProfileRoot `
        -WindowWidth $windowWidth `
        -WindowHeight $windowHeight)
) + @(
    '--run-all-compositor-stages-before-draw',
    "--screenshot=$screenshotPath",
    $fixtureUri
)

$screenshotResult = Invoke-Stage25Browser `
    -BrowserPath $browser `
    -Arguments $screenshotArguments `
    -TimeoutSeconds 60

if (-not [string]::IsNullOrWhiteSpace($screenshotResult.Stderr)) {
    Add-Content -LiteralPath $stderrPath -Value $screenshotResult.Stderr -Encoding utf8
}

if ($screenshotResult.ExitCode -ne 0) {
    if (-not [string]::IsNullOrWhiteSpace($screenshotResult.Stderr)) {
        Write-Host $screenshotResult.Stderr
    }
    throw "Browser screenshot capture failed with exit code $($screenshotResult.ExitCode)"
}

if (-not (Test-Path -LiteralPath $screenshotPath -PathType Leaf)) {
    throw 'Browser did not create the fixture screenshot.'
}

$png = [System.IO.File]::ReadAllBytes($screenshotPath)
if ($png.Length -lt 24) {
    throw 'Fixture screenshot is too small to be a valid PNG.'
}
$pngSignature = @(137,80,78,71,13,10,26,10)
for ($i = 0; $i -lt $pngSignature.Count; $i++) {
    if ([int]$png[$i] -ne $pngSignature[$i]) {
        throw 'Fixture screenshot does not have a valid PNG signature.'
    }
}

$pngWidth = ([int]$png[16] -shl 24) -bor ([int]$png[17] -shl 16) -bor ([int]$png[18] -shl 8) -bor [int]$png[19]
$pngHeight = ([int]$png[20] -shl 24) -bor ([int]$png[21] -shl 16) -bor ([int]$png[22] -shl 8) -bor [int]$png[23]

Write-Host "SCREENSHOT_RAW_SIZE=${pngWidth}x${pngHeight}"
if ($pngWidth -ne $expectedWidth -or $pngHeight -ne $expectedHeight) {
    throw "Screenshot dimensions are ${pngWidth}x${pngHeight}, expected ${expectedWidth}x${expectedHeight}."
}

$hash = (Get-FileHash -LiteralPath $screenshotPath -Algorithm SHA256).Hash.ToLowerInvariant()

Write-Host "`n===== FIXTURE CAPTURE RESULT =====" -ForegroundColor Green
Write-Host "VERIFIED_TARGET_COUNT=$verifiedCount"
Write-Host "SCREENSHOT=$screenshotPath"
Write-Host "SCREENSHOT_BYTES=$($png.Length)"
Write-Host "SCREENSHOT_SIZE=${pngWidth}x${pngHeight}"
Write-Host "SCREENSHOT_SHA256=$hash"
Write-Host 'STAGE25_GROUNDING_FIXTURE_BROWSER=PASS'
