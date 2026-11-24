[CmdletBinding()]
param(
    [string]$GameDir = '',
    [string]$BackupRoot = (Join-Path $env:LOCALAPPDATA 'YoruGaKuru_KO_Patch\Backups'),
    [string]$StateRoot = (Join-Path $env:LOCALAPPDATA 'YoruGaKuru_KO_Patch\State')
)

$ErrorActionPreference = 'Stop'
$PackageRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$ManifestPath = Join-Path $PackageRoot 'manifest\install_manifest.json'

function Get-Sha256([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Normalize-Directory([string]$Path) {
    $full = [IO.Path]::GetFullPath($Path)
    $root = [IO.Path]::GetPathRoot($full)
    if ($full.Equals($root, [StringComparison]::OrdinalIgnoreCase)) { return $root }
    return $full.TrimEnd('\')
}

function Test-UnderPath([string]$Child, [string]$Parent) {
    $childFull = Normalize-Directory $Child
    $parentFull = Normalize-Directory $Parent
    if ($childFull.Equals($parentFull, [StringComparison]::OrdinalIgnoreCase)) { return $true }
    $prefix = if ($parentFull.EndsWith('\')) { $parentFull } else { $parentFull + '\' }
    return $childFull.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)
}

function Write-Json([object]$Value, [string]$Path) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $Path) -Force | Out-Null
    $Value | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Assert-NoTargetProcess([string]$TargetExe) {
    $target = [IO.Path]::GetFullPath($TargetExe)
    $matches = @()
    foreach ($process in @(Get-Process -Name 'NightRemaster' -ErrorAction SilentlyContinue)) {
        try {
            if ($process.Path -and ([IO.Path]::GetFullPath($process.Path)).Equals($target, [StringComparison]::OrdinalIgnoreCase)) {
                $matches += $process.Id
            }
        } catch {}
    }
    if ($matches.Count -gt 0) { throw "대상 게임이 실행 중입니다. 먼저 종료하십시오. PID: $($matches -join ', ')" }
}

if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw "install manifest missing: $ManifestPath" }
$ManifestHash = Get-Sha256 $ManifestPath
$Manifest = Get-Content -LiteralPath $ManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$Entries = @($Manifest.files)
if ($Manifest.schema -ne 'yorugakuru.ko-patch.install-manifest.v1') { throw "unsupported manifest schema: $($Manifest.schema)" }
if ($Entries.Count -ne [int]$Manifest.file_count) { throw 'manifest file count mismatch' }

if ([string]::IsNullOrWhiteSpace($GameDir)) {
    $beside = Split-Path -Parent $PackageRoot
    if (Test-Path -LiteralPath (Join-Path $beside 'NightRemaster.exe')) { $GameDir = $beside }
    else { $GameDir = Read-Host '게임 폴더의 전체 경로를 입력하십시오' }
}
$GameDir = Normalize-Directory $GameDir
$BackupRoot = Normalize-Directory $BackupRoot
$StateRoot = Normalize-Directory $StateRoot
if (-not (Test-Path -LiteralPath $GameDir -PathType Container)) { throw "game folder missing: $GameDir" }
if (-not (Test-Path -LiteralPath $BackupRoot -PathType Container)) { throw "backup root missing: $BackupRoot" }
Assert-NoTargetProcess (Join-Path $GameDir 'NightRemaster.exe')

$InstalledPath = Join-Path $StateRoot 'installed.json'
if (-not (Test-Path -LiteralPath $InstalledPath -PathType Leaf)) {
    $alreadyOriginal = $true
    foreach ($entry in $Entries) {
        $path = Join-Path $GameDir ([string]$entry.path).Replace('/', '\')
        if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or (Get-Sha256 $path) -ne [string]$entry.original_sha256) {
            $alreadyOriginal = $false
            break
        }
    }
    if ($alreadyOriginal) { Write-Host '이미 원본 상태입니다.'; return }
    throw "설치 상태 파일이 없습니다: $InstalledPath"
}

$Installed = Get-Content -LiteralPath $InstalledPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not ([IO.Path]::GetFullPath([string]$Installed.game_dir)).Equals($GameDir, [StringComparison]::OrdinalIgnoreCase)) {
    throw '설치 상태의 게임 폴더가 현재 대상과 다릅니다.'
}
if ([string]$Installed.package_manifest_sha256 -ne $ManifestHash) { throw '설치에 사용된 패키지와 현재 패키지가 다릅니다.' }
$BackupDir = Normalize-Directory ([string]$Installed.backup_dir)
if (-not (Test-UnderPath $BackupDir $BackupRoot)) { throw "backup directory escapes BackupRoot: $BackupDir" }
$BackupManifestPath = Join-Path $BackupDir 'backup_manifest.json'
if (-not (Test-Path -LiteralPath $BackupManifestPath -PathType Leaf)) { throw "backup manifest missing: $BackupManifestPath" }
$BackupManifest = Get-Content -LiteralPath $BackupManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$BackupManifest.package_manifest_sha256 -ne $ManifestHash) { throw 'backup/package manifest mismatch' }
if (-not ([IO.Path]::GetFullPath([string]$BackupManifest.game_dir)).Equals($GameDir, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'backup game directory mismatch'
}

$BackupMap = @{}
foreach ($record in @($BackupManifest.files)) { $BackupMap[[string]$record.path] = $record }
foreach ($entry in $Entries) {
    $relative = [string]$entry.path
    if (-not $BackupMap.ContainsKey($relative)) { throw "backup entry missing: $relative" }
    $source = Join-Path $BackupDir ('files\' + $relative.Replace('/', '\'))
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "backup file missing: $relative" }
    if ((Get-Sha256 $source) -ne [string]$entry.original_sha256) { throw "backup hash mismatch: $relative" }
}

$TxnId = [Guid]::NewGuid().ToString('N')
$JournalPath = Join-Path $StateRoot 'restore_in_progress.json'
$Journal = [ordered]@{
    schema = 'yorugakuru.ko-patch.restore-transaction.v1'
    status = 'in_progress'
    started_at = (Get-Date).ToString('o')
    transaction_id = $TxnId
    game_dir = $GameDir
    backup_dir = $BackupDir
    restored_count = 0
}
Write-Json $Journal $JournalPath

foreach ($entry in $Entries) {
    $relative = [string]$entry.path
    $source = Join-Path $BackupDir ('files\' + $relative.Replace('/', '\'))
    $target = Join-Path $GameDir $relative.Replace('/', '\')
    $incoming = "$target.ko_restore_$TxnId"
    Copy-Item -LiteralPath $source -Destination $incoming -Force
    if ((Get-Sha256 $incoming) -ne [string]$entry.original_sha256) { throw "restore incoming hash mismatch: $relative" }
    if (Test-Path -LiteralPath $target) {
        $replaceBackup = "$target.ko_replace_$TxnId"
        [IO.File]::Replace($incoming, $target, $replaceBackup, $true)
        if (Test-Path -LiteralPath $replaceBackup) { Remove-Item -LiteralPath $replaceBackup -Force }
    } else {
        Move-Item -LiteralPath $incoming -Destination $target
    }
    $Journal.restored_count++
    Write-Json $Journal $JournalPath
}

$bad = @()
foreach ($entry in $Entries) {
    $path = Join-Path $GameDir ([string]$entry.path).Replace('/', '\')
    if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or (Get-Sha256 $path) -ne [string]$entry.original_sha256) {
        $bad += [string]$entry.path
    }
}
if ($bad.Count -gt 0) { throw "원본 복원 검증 실패: $($bad -join ', ')" }
$Journal.status = 'restored'
$Journal.completed_at = (Get-Date).ToString('o')
Write-Json $Journal (Join-Path $StateRoot ("restored_{0}.json" -f $TxnId))
Remove-Item -LiteralPath $JournalPath -Force
Remove-Item -LiteralPath $InstalledPath -Force
Write-Host '원본 복원 완료'
Write-Host "백업은 보존했습니다: $BackupDir"
