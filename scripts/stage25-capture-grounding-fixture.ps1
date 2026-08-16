param(
    [string]$OutputRoot
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

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

foreach ($candidate in @(
    (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'),
    (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'),
    (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe'),
    (Join-Path $env:LOCALAPPDATA 'Google\Chrome\Application\chrome.exe')
)) {
    if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
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
$profileRoot = Join-Path $OutputRoot 'browser-profile'
$dumpPath = Join-Path $OutputRoot 'fixture-dom.html'
$geometryPath = Join-Path $OutputRoot 'fixture-geometry.json'
$screenshotPath = Join-Path $OutputRoot 'fixture.png'
$stderrPath = Join-Path $OutputRoot 'browser.stderr.log'

Remove-Item -LiteralPath $profileRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $dumpPath,$geometryPath,$screenshotPath,$stderrPath -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $profileRoot | Out-Null

$commonArgs = @(
    '--headless=new',
    '--disable-gpu',
    '--disable-extensions',
    '--disable-background-networking',
    '--no-first-run',
    '--no-default-browser-check',
    '--hide-scrollbars',
    '--force-device-scale-factor=1',
    '--window-size=1280,720',
    "--user-data-dir=$profileRoot"
)

Write-Host "`n===== STAGE 25 BROWSER FIXTURE =====" -ForegroundColor Cyan
Write-Host "BROWSER=$browser"
Write-Host "FIXTURE=$fixturePath"
Write-Host "OUTPUT_ROOT=$OutputRoot"

$dumpOutput = & $browser @commonArgs '--dump-dom' $fixtureUri 2> $stderrPath
if ($LASTEXITCODE -ne 0) {
    if (Test-Path -LiteralPath $stderrPath) {
        Get-Content -LiteralPath $stderrPath -Tail 80
    }
    throw "Browser --dump-dom failed with exit code $LASTEXITCODE"
}

$dumpText = ($dumpOutput -join "`n")
Set-Content -LiteralPath $dumpPath -Value $dumpText -Encoding utf8

$match = [regex]::Match(
    $dumpText,
    '<pre\s+id="stage25-fixture-export"[^>]*>(.*?)</pre>',
    [System.Text.RegularExpressions.RegexOptions]::Singleline
)
if (-not $match.Success) {
    throw 'Rendered fixture geometry export was not found in browser DOM output.'
}

$geometryJson = [System.Net.WebUtility]::HtmlDecode($match.Groups[1].Value).Trim()
$actual = $geometryJson | ConvertFrom-Json
$spec = Get-Content -LiteralPath $casesPath -Raw -Encoding utf8 | ConvertFrom-Json

$actual | ConvertTo-Json -Depth 8 |
    Set-Content -LiteralPath $geometryPath -Encoding utf8

$expectedWidth = [double]$spec.viewport.width
$expectedHeight = [double]$spec.viewport.height
$actualWidth = [double]$actual.viewport.width
$actualHeight = [double]$actual.viewport.height

Write-Host "VIEWPORT_EXPECTED=${expectedWidth}x${expectedHeight}"
Write-Host "VIEWPORT_ACTUAL=${actualWidth}x${actualHeight}"

if ([math]::Abs($actualWidth - $expectedWidth) -gt 0.01 -or
    [math]::Abs($actualHeight - $expectedHeight) -gt 0.01) {
    throw 'Rendered browser viewport does not match fixture metadata.'
}

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
    $property = $actual.targets.PSObject.Properties[$targetId]
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

& $browser @commonArgs '--run-all-compositor-stages-before-draw' "--screenshot=$screenshotPath" $fixtureUri 2>> $stderrPath | Out-Null
if ($LASTEXITCODE -ne 0) {
    if (Test-Path -LiteralPath $stderrPath) {
        Get-Content -LiteralPath $stderrPath -Tail 80
    }
    throw "Browser screenshot capture failed with exit code $LASTEXITCODE"
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

if ($pngWidth -ne [int]$expectedWidth -or $pngHeight -ne [int]$expectedHeight) {
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
