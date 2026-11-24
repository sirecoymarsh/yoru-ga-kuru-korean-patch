[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$Root = [IO.Path]::GetFullPath($PSScriptRoot)
$ManifestPath = Join-Path $Root 'manifest\install_manifest.json'
$PayloadRoot = Join-Path $Root 'payload'
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw 'install manifest missing' }
$Manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$Entries = @($Manifest.files)
if ($Manifest.schema -ne 'yorugakuru.ko-patch.install-manifest.v1') { throw 'unsupported manifest schema' }
if ($Entries.Count -ne [int]$Manifest.file_count) { throw 'manifest file count mismatch' }
$actual = @(Get-ChildItem -LiteralPath $PayloadRoot -Recurse -File | ForEach-Object {
    $_.FullName.Substring($PayloadRoot.Length + 1).Replace('\', '/')
} | Sort-Object)
$expected = @($Entries | ForEach-Object { [string]$_.path } | Sort-Object)
if (($actual -join "`n") -ne ($expected -join "`n")) { throw 'payload file set mismatch' }
foreach ($entry in $Entries) {
    $path = Join-Path $PayloadRoot ([string]$entry.path).Replace('/', '\')
    $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne [string]$entry.patched_sha256) { throw "payload hash mismatch: $($entry.path)" }
    if ((Get-Item -LiteralPath $path).Length -ne [long]$entry.patched_size) { throw "payload size mismatch: $($entry.path)" }
}
Write-Host "패키지 검증 완료: $($Entries.Count)개 파일"
