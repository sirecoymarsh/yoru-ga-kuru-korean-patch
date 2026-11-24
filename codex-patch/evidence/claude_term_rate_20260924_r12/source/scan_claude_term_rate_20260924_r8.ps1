$ErrorActionPreference='Stop'
$root='P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\claude_term_rate_20260924_r8'
$target=Join-Path $root 'scan_payload'
if (Test-Path -LiteralPath $target) { throw 'Inspect existing scan payload instead of overwriting it.' }
New-Item -ItemType Directory -Path $target | Out-Null
$files=@('NightRemaster.ain','NightRemasterPact.afa','NightRemasterEX.ex')
$hashes=@{}
foreach($n in $files) {
    Copy-Item -LiteralPath (Join-Path $root $n) -Destination (Join-Path $target $n)
    $hashes[$n]=(Get-FileHash -LiteralPath (Join-Path $target $n) -Algorithm SHA256).Hash.ToLower()
}
$started=(Get-Date).ToString('o')
$status=Get-MpComputerStatus
$before=@(Get-MpThreatDetection | Where-Object { ($_.Resources -join '|').IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0 })
Start-MpScan -ScanType CustomScan -ScanPath $target
$after=@(Get-MpThreatDetection | Where-Object { ($_.Resources -join '|').IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0 })
foreach($n in $files) {
    if ((Get-FileHash -LiteralPath (Join-Path $target $n) -Algorithm SHA256).Hash.ToLower() -ne $hashes[$n]) { throw "Scanned bytes changed: $n" }
}
$r=[ordered]@{status='SCANNED_NO_TARGET_DETECTIONS';started=$started;ended=(Get-Date).ToString('o');target=$target;files=$hashes;engine=$status.AMEngineVersion;platform=$status.AMProductVersion;signatures=$status.AntivirusSignatureVersion;antivirusEnabled=$status.AntivirusEnabled;before=@($before | Select-Object DetectionID,ThreatID,InitialDetectionTime,Resources);after=@($after | Select-Object DetectionID,ThreatID,InitialDetectionTime,Resources)}
if ($after.Count -gt 0) { $r.status='TARGET_DETECTION_PRESENT' }
$json=$r | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText((Join-Path $root 'scan_report.json'),$json,(New-Object Text.UTF8Encoding($false)))
$json
if ($after.Count -gt 0) { throw 'Detected target must not be published.' }
