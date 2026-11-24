param([Parameter(Mandatory=$true)][string]$Candidate, [Parameter(Mandatory=$true)][string]$Target, [Parameter(Mandatory=$true)][string]$Out)
# Claude Opus 5.5 (2026-09-27) r19: Defender custom scan of a COPY of the candidate payload (copy of scan_calendar_r18.ps1).
# ASCII only (Windows PowerShell 5.1 reads a BOM-less .ps1 as ANSI); every path comes in as a parameter.
$ErrorActionPreference='Stop'
if (Test-Path -LiteralPath $Target) { throw 'Inspect existing scan payload instead of overwriting it.' }
New-Item -ItemType Directory -Path $Target | Out-Null
# r19 payload: the AIN and the help-menu chart (keys use '/', as in the manifest)
$files=@('NightRemaster.ain','Manual/chart/yoru_flowchart_v2.html')
$hashes=@{}
foreach($n in $files) {
    $rel=$n.Replace('/','\')
    $dest=Join-Path $Target $rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
    Copy-Item -LiteralPath (Join-Path $Candidate $rel) -Destination $dest
    $hashes[$n]=(Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash.ToLower()
}
$started=(Get-Date).ToString('o')
$status=Get-MpComputerStatus
$before=@(Get-MpThreatDetection | Where-Object { ($_.Resources -join '|').IndexOf($Target,[StringComparison]::OrdinalIgnoreCase) -ge 0 })
Start-MpScan -ScanType CustomScan -ScanPath $Target
$after=@(Get-MpThreatDetection | Where-Object { ($_.Resources -join '|').IndexOf($Target,[StringComparison]::OrdinalIgnoreCase) -ge 0 })
foreach($n in $files) {
    if ((Get-FileHash -LiteralPath (Join-Path $Target $n.Replace('/','\')) -Algorithm SHA256).Hash.ToLower() -ne $hashes[$n]) { throw "Scanned bytes changed: $n" }
}
$r=[ordered]@{status='SCANNED_NO_TARGET_DETECTIONS';started=$started;ended=(Get-Date).ToString('o');target=$Target;files=$hashes;engine=$status.AMEngineVersion;platform=$status.AMProductVersion;signatures=$status.AntivirusSignatureVersion;antivirusEnabled=$status.AntivirusEnabled;before=@($before | Select-Object DetectionID,ThreatID,InitialDetectionTime,Resources);after=@($after | Select-Object DetectionID,ThreatID,InitialDetectionTime,Resources)}
if ($after.Count -gt 0) { $r.status='TARGET_DETECTION_PRESENT' }
$json=$r | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText($Out,$json,(New-Object Text.UTF8Encoding($false)))
$json
if ($after.Count -gt 0) { throw 'Detected target must not be published.' }
