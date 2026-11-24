$ErrorActionPreference='Stop'
$root='P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\name_particles_20260917'
$target=Join-Path $root 'scan_copy'
New-Item -ItemType Directory -Path $target -Force | Out-Null
$name='NightRemaster.ain'
$source=Join-Path (Join-Path $root 'output') $name
Copy-Item -LiteralPath $source -Destination (Join-Path $target $name)
$hash=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLower()
$started=(Get-Date).ToString('o')
$status=Get-MpComputerStatus
$before=@(Get-MpThreatDetection | Where-Object { ($_.Resources -join '|').IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0 })
Start-MpScan -ScanType CustomScan -ScanPath $target
$after=@(Get-MpThreatDetection | Where-Object { ($_.Resources -join '|').IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0 })
if ((Get-FileHash -LiteralPath (Join-Path $target $name) -Algorithm SHA256).Hash.ToLower() -ne $hash) { throw 'Scanned bytes changed' }
$r=[ordered]@{completed=$true;status='SCANNED_NO_TARGET_DETECTIONS';started=$started;ended=(Get-Date).ToString('o');target=$target;files=@{ 'NightRemaster.ain'=$hash };engine=$status.AMEngineVersion;platform=$status.AMProductVersion;signatures=$status.AntivirusSignatureVersion;antivirusEnabled=$status.AntivirusEnabled;before=@($before | Select-Object DetectionID,ThreatID,Resources);after=@($after | Select-Object DetectionID,ThreatID,Resources)}
if ($after.Count -gt 0) { $r.status='TARGET_DETECTION_PRESENT' }
$json=$r | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText((Join-Path $root 'defender_scan.json'),$json,(New-Object Text.UTF8Encoding($false)))
$json
if ($after.Count -gt 0) { throw 'Detected target must not be published' }
