[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$SpecPath,
  [Parameter(Mandatory = $true)]
  [string]$ReadyPath,
  [Parameter(Mandatory = $true)]
  [string]$StopPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Get-StreamSha256 {
  param([Parameter(Mandatory = $true)][System.IO.FileStream]$Stream)
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try {
    $Stream.Position = 0
    $hash = $sha.ComputeHash($Stream)
    $Stream.Position = 0
    return [Convert]::ToHexString($hash).ToLowerInvariant()
  }
  finally {
    $sha.Dispose()
  }
}

$SpecPath = (Resolve-Path -LiteralPath $SpecPath).Path
$spec = Get-Content -LiteralPath $SpecPath -Raw -Encoding utf8 | ConvertFrom-Json
$records = @($spec.files)
if ($records.Count -eq 0) { throw 'Byte-lock spec contains no files.' }

$streams = [System.Collections.Generic.List[System.IO.FileStream]]::new()
try {
  foreach ($record in $records) {
    $path = [System.IO.Path]::GetFullPath([string]$record.path)
    $expected = ([string]$record.sha256).ToLowerInvariant()
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Byte-lock target missing: $path" }

    # FileShare.Read allows the runtime to read the file while preventing any
    # writer/deleter from replacing bytes between provenance verification and
    # the actual Node/PowerShell load. Hashing is performed through the held
    # handle, so the verified bytes are exactly the bytes that remain locked.
    $stream = [System.IO.File]::Open(
      $path,
      [System.IO.FileMode]::Open,
      [System.IO.FileAccess]::Read,
      [System.IO.FileShare]::Read
    )
    $actual = Get-StreamSha256 -Stream $stream
    if ($actual -cne $expected) {
      $stream.Dispose()
      throw "Byte-lock target hash mismatch: $path expected=$expected actual=$actual"
    }
    $streams.Add($stream)
  }

  $readyUtc = (Get-Date).ToUniversalTime()
  $ready = [ordered]@{
    schema_version = 2
    pid = $PID
    process_name = (Get-Process -Id $PID).ProcessName
    process_start_time_ticks = (Get-Process -Id $PID).StartTime.ToUniversalTime().Ticks
    locked_file_count = $streams.Count
    ready_time_ticks = $readyUtc.Ticks
    ready_at = $readyUtc.ToString('o')
  }
  [System.IO.File]::WriteAllText(
    $ReadyPath,
    (($ready | ConvertTo-Json -Depth 4) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
  )

  while (-not (Test-Path -LiteralPath $StopPath -PathType Leaf)) {
    Start-Sleep -Milliseconds 100
  }
}
finally {
  foreach ($stream in $streams) {
    try { $stream.Dispose() } catch { }
  }
}
