# Defender custom scan of one summary-layer candidate (Claude Opus 5.5 (claude-opus-5-5), 2026-09-29).
# The label-particles scan (docs/.../scan_calendar_label_particles_20260929.ps1) with the layer folder as a parameter:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scan_summary_layer.ps1 -Out <layer staging folder>
# Copies candidate\NightRemaster.ain + winmm.dll into candidate\scan_payload_<sha12>, scans the copy, checks the bytes did not change,
# writes candidate\scan_report.json (status SCANNED_NO_TARGET_DETECTIONS; publish_summary_layer.py requires it for these bytes).
param([Parameter(Mandatory=$true)][string]$Out)
$ErrorActionPreference='Stop'
$staging=[IO.Path]::GetFullPath('P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\')
$full=[IO.Path]::GetFullPath($Out)
if (-not $full.StartsWith($staging,[StringComparison]::OrdinalIgnoreCase)) { throw 'The layer folder must be under staging.' }
$root=Join-Path $full 'candidate'
$manifest=Get-Content -LiteralPath (Join-Path $root 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.tool -ne 'calendar_summary_layer_tools_20260929') { throw 'Not a summary-layer build.' }
if ($manifest.dry_run) { throw 'Dry-run candidates are not scanned for install.' }
$suffix=(Get-FileHash -LiteralPath (Join-Path $root 'NightRemaster.ain') -Algorithm SHA256).Hash.ToLower().Substring(0,12)
$target=Join-Path $root ('scan_payload_'+$suffix)
if (Test-Path -LiteralPath $target) { throw 'Inspect existing scan payload instead of overwriting.' }
New-Item -ItemType Directory -Path $target | Out-Null
$files=@('NightRemaster.ain','winmm.dll'); $hashes=@{}
foreach($n in $files) {
    Copy-Item -LiteralPath (Join-Path $root $n) -Destination (Join-Path $target $n)
    $hashes[$n]=(Get-FileHash -LiteralPath (Join-Path $target $n) -Algorithm SHA256).Hash.ToLower()
    if ($hashes[$n] -ne $manifest.files.$n.sha256) { throw "Candidate differs from its manifest: $n" }
}
$started=(Get-Date).ToString('o'); $status=Get-MpComputerStatus
$before=@(Get-MpThreatDetection | Where-Object { ($_.Resources -join '|').IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0 })
Start-MpScan -ScanType CustomScan -ScanPath (Join-Path $target 'winmm.dll')
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
