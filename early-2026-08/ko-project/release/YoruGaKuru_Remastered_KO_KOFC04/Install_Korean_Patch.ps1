[CmdletBinding()]
param(
    [string]$GameDir = '',
    [string]$BackupRoot = (Join-Path $env:LOCALAPPDATA 'YoruGaKuru_KO_Patch\Backups'),
    [string]$StateRoot = (Join-Path $env:LOCALAPPDATA 'YoruGaKuru_KO_Patch\State'),
    [int]$TestFailAfterN = 0,
    [int]$TestInterruptAfterN = 0
)

$ErrorActionPreference = 'Stop'
$PackageRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$PayloadRoot = Join-Path $PackageRoot 'payload'
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

function Assert-Outside([string]$Path, [string[]]$ForbiddenRoots, [string]$Label) {
    foreach ($root in $ForbiddenRoots) {
        if ((Test-UnderPath $Path $root) -or (Test-UnderPath $root $Path)) {
            throw "$Label overlaps a protected tree: $Path <-> $root"
        }
    }
}

function Get-RelativePath([string]$Root, [string]$Path) {
    $rootFull = Normalize-Directory $Root
    $pathFull = [IO.Path]::GetFullPath($Path)
    $prefix = if ($rootFull.EndsWith('\')) { $rootFull } else { $rootFull + '\' }
    if (-not $pathFull.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is not below root: $pathFull"
    }
    return $pathFull.Substring($prefix.Length).Replace('\', '/')
}

function Write-Json([object]$Value, [string]$Path) {
    $parent = Split-Path -Parent $Path
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
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
    if ($matches.Count -gt 0) {
        throw "대상 게임이 실행 중입니다. 먼저 종료하십시오. PID: $($matches -join ', ')"
    }
}

function Assert-Payload([object[]]$Entries, [string]$ExpectedManifestHash) {
    if (-not (Test-Path -LiteralPath $PayloadRoot -PathType Container)) { throw 'payload folder is missing' }
    $reparse = @(Get-ChildItem -LiteralPath $PayloadRoot -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
    if ($reparse.Count -gt 0) { throw "payload contains reparse points: $($reparse.FullName -join ', ')" }
    $expected = @($Entries | ForEach-Object { [string]$_.path } | Sort-Object)
    $actual = @(Get-ChildItem -LiteralPath $PayloadRoot -Recurse -File -Force | ForEach-Object { Get-RelativePath $PayloadRoot $_.FullName } | Sort-Object)
    if (($expected -join "`n") -ne ($actual -join "`n")) {
        throw "payload file set mismatch`nexpected=$($expected -join ', ')`nactual=$($actual -join ', ')"
    }
    foreach ($entry in $Entries) {
        $path = Join-Path $PayloadRoot ([string]$entry.path).Replace('/', '\')
        $hash = Get-Sha256 $path
        if ($hash -ne [string]$entry.patched_sha256) { throw "payload hash mismatch: $($entry.path)" }
        if ((Get-Item -LiteralPath $path).Length -ne [long]$entry.patched_size) { throw "payload size mismatch: $($entry.path)" }
    }
    if ((Get-Sha256 $ManifestPath) -ne $ExpectedManifestHash) { throw 'manifest changed during payload verification' }
}

function Get-LiveState([object[]]$Entries, [string]$Root) {
    $states = @()
    foreach ($entry in $Entries) {
        $path = Join-Path $Root ([string]$entry.path).Replace('/', '\')
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            $states += [pscustomobject]@{ path = $entry.path; state = 'missing'; hash = $null }
            continue
        }
        $hash = Get-Sha256 $path
        $state = if ($hash -eq [string]$entry.original_sha256) { 'original' } elseif ($hash -eq [string]$entry.patched_sha256) { 'patched' } else { 'unknown' }
        $states += [pscustomobject]@{ path = $entry.path; state = $state; hash = $hash }
    }
    return @($states)
}

function Restore-FromBackup([object[]]$Entries, [string]$Root, [string]$BackupDir, [string]$TxnId) {
    $backupManifestPath = Join-Path $BackupDir 'backup_manifest.json'
    if (-not (Test-Path -LiteralPath $backupManifestPath -PathType Leaf)) { throw "backup manifest missing: $backupManifestPath" }
    $backupManifest = Get-Content -LiteralPath $backupManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $backupMap = @{}
    foreach ($record in @($backupManifest.files)) { $backupMap[[string]$record.path] = $record }
    foreach ($entry in $Entries) {
        $relative = [string]$entry.path
        if (-not $backupMap.ContainsKey($relative)) { throw "backup entry missing: $relative" }
        $source = Join-Path $BackupDir ('files\' + $relative.Replace('/', '\'))
        if ((Get-Sha256 $source) -ne [string]$entry.original_sha256) { throw "backup hash mismatch: $relative" }
    }
    foreach ($entry in $Entries) {
        $relative = [string]$entry.path
        $source = Join-Path $BackupDir ('files\' + $relative.Replace('/', '\'))
        $target = Join-Path $Root $relative.Replace('/', '\')
        $incoming = "$target.ko_rollback_$TxnId"
        Copy-Item -LiteralPath $source -Destination $incoming -Force
        if ((Get-Sha256 $incoming) -ne [string]$entry.original_sha256) { throw "rollback incoming hash mismatch: $relative" }
        if (Test-Path -LiteralPath $target) {
            $replaceBackup = "$target.ko_replace_$TxnId"
            [IO.File]::Replace($incoming, $target, $replaceBackup, $true)
            if (Test-Path -LiteralPath $replaceBackup) { Remove-Item -LiteralPath $replaceBackup -Force }
        } else {
            Move-Item -LiteralPath $incoming -Destination $target
        }
    }
    $post = Get-LiveState $Entries $Root
    $bad = @($post | Where-Object { $_.state -ne 'original' })
    if ($bad.Count -gt 0) { throw "rollback verification failed: $($bad.path -join ', ')" }
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
Assert-Outside $BackupRoot @($GameDir, $PackageRoot) 'BackupRoot'
Assert-Outside $StateRoot @($GameDir, $PackageRoot, $BackupRoot) 'StateRoot'
Assert-NoTargetProcess (Join-Path $GameDir 'NightRemaster.exe')
Assert-Payload $Entries $ManifestHash
New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
New-Item -ItemType Directory -Path $StateRoot -Force | Out-Null

$JournalPath = Join-Path $StateRoot 'in_progress.json'
if (Test-Path -LiteralPath $JournalPath -PathType Leaf) {
    $old = Get-Content -LiteralPath $JournalPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($old.status -eq 'in_progress') {
        if (-not ([IO.Path]::GetFullPath([string]$old.game_dir)).Equals($GameDir, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'an unfinished transaction belongs to a different game directory'
        }
        $recoverStates = Get-LiveState $Entries $GameDir
        $unknown = @($recoverStates | Where-Object { $_.state -notin @('original', 'patched') })
        if ($unknown.Count -gt 0) { throw "unfinished transaction has unknown live files: $($unknown.path -join ', ')" }
        Restore-FromBackup $Entries $GameDir ([string]$old.backup_dir) ([string]$old.transaction_id)
        $old.status = 'recovered_to_original'
        $old | Add-Member -NotePropertyName recovered_at -NotePropertyValue ((Get-Date).ToString('o')) -Force
        Write-Json $old (Join-Path $StateRoot ("recovered_{0}.json" -f $old.transaction_id))
        Remove-Item -LiteralPath $JournalPath -Force
    }
}

$live = Get-LiveState $Entries $GameDir
$unknownLive = @($live | Where-Object { $_.state -in @('missing', 'unknown') })
if ($unknownLive.Count -gt 0) { throw "지원하지 않는 게임 파일 상태입니다: $($unknownLive.path -join ', ')" }
$originalCount = @($live | Where-Object { $_.state -eq 'original' }).Count
$patchedCount = @($live | Where-Object { $_.state -eq 'patched' }).Count
if ($patchedCount -eq $Entries.Count) {
    Write-Host '이미 동일한 한국어 패치가 설치되어 있습니다.'
    return
}
if ($originalCount -ne $Entries.Count) {
    throw "원본/패치 파일이 섞여 있습니다. 설치를 중단합니다. original=$originalCount patched=$patchedCount"
}

$TxnId = ([Guid]::NewGuid().ToString('N'))
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$BackupDir = Join-Path $BackupRoot ("{0}_{1}" -f $Stamp, $TxnId)
Assert-Outside $BackupDir @($GameDir, $PackageRoot, $StateRoot) 'BackupDir'
New-Item -ItemType Directory -Path (Join-Path $BackupDir 'files') -Force | Out-Null
$backupRecords = @()
foreach ($entry in $Entries) {
    $relative = [string]$entry.path
    $source = Join-Path $GameDir $relative.Replace('/', '\')
    $target = Join-Path $BackupDir ('files\' + $relative.Replace('/', '\'))
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $target
    $hash = Get-Sha256 $target
    if ($hash -ne [string]$entry.original_sha256) { throw "backup verification failed: $relative" }
    $backupRecords += [pscustomobject]@{ path = $relative; size = (Get-Item -LiteralPath $target).Length; sha256 = $hash }
}
$BackupManifest = [ordered]@{
    schema = 'yorugakuru.ko-patch.backup-manifest.v1'
    created_at = (Get-Date).ToString('o')
    transaction_id = $TxnId
    game_dir = $GameDir
    package_manifest_sha256 = $ManifestHash
    file_count = $backupRecords.Count
    files = @($backupRecords)
}
Write-Json $BackupManifest (Join-Path $BackupDir 'backup_manifest.json')

$Journal = [ordered]@{
    schema = 'yorugakuru.ko-patch.transaction.v1'
    status = 'in_progress'
    started_at = (Get-Date).ToString('o')
    transaction_id = $TxnId
    game_dir = $GameDir
    backup_dir = $BackupDir
    package_manifest_sha256 = $ManifestHash
    planned_file_count = $Entries.Count
    replaced_count = 0
}
Write-Json $Journal $JournalPath

try {
    $count = 0
    foreach ($entry in $Entries) {
        $relative = [string]$entry.path
        $source = Join-Path $PayloadRoot $relative.Replace('/', '\')
        $target = Join-Path $GameDir $relative.Replace('/', '\')
        $incoming = "$target.ko_incoming_$TxnId"
        Copy-Item -LiteralPath $source -Destination $incoming -Force
        if ((Get-Sha256 $incoming) -ne [string]$entry.patched_sha256) { throw "incoming hash mismatch: $relative" }
        $replaceBackup = "$target.ko_replace_$TxnId"
        [IO.File]::Replace($incoming, $target, $replaceBackup, $true)
        if (Test-Path -LiteralPath $replaceBackup) { Remove-Item -LiteralPath $replaceBackup -Force }
        $count++
        $Journal.replaced_count = $count
        Write-Json $Journal $JournalPath
        if ($TestInterruptAfterN -gt 0 -and $count -eq $TestInterruptAfterN) { [Environment]::Exit(91) }
        if ($TestFailAfterN -gt 0 -and $count -eq $TestFailAfterN) { throw "intentional fixture failure after $count replacements" }
    }
    $post = Get-LiveState $Entries $GameDir
    $bad = @($post | Where-Object { $_.state -ne 'patched' })
    if ($bad.Count -gt 0) { throw "post-install verification failed: $($bad.path -join ', ')" }
    $Journal.status = 'committed'
    $Journal.completed_at = (Get-Date).ToString('o')
    Write-Json $Journal (Join-Path $StateRoot 'installed.json')
    Remove-Item -LiteralPath $JournalPath -Force
    Write-Host "한국어 패치 설치 완료"
    Write-Host "백업: $BackupDir"
} catch {
    $installError = $_
    try {
        Restore-FromBackup $Entries $GameDir $BackupDir $TxnId
        $Journal.status = 'rolled_back'
        $Journal.rollback_at = (Get-Date).ToString('o')
        $Journal.error = $installError.Exception.Message
        Write-Json $Journal (Join-Path $StateRoot ("rolled_back_{0}.json" -f $TxnId))
        if (Test-Path -LiteralPath $JournalPath) { Remove-Item -LiteralPath $JournalPath -Force }
    } catch {
        $Journal.status = 'rollback_incomplete'
        $Journal.rollback_error = $_.Exception.Message
        $Journal.install_error = $installError.Exception.Message
        Write-Json $Journal $JournalPath
        throw "설치 실패 후 복구도 완료하지 못했습니다. 복구 자료: $BackupDir / $JournalPath"
    }
    throw "설치가 실패하여 원본으로 되돌렸습니다: $($installError.Exception.Message)"
}

