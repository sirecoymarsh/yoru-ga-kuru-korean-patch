[CmdletBinding()]
param(
    [switch]$Commit,
    [string]$SourceRoot = 'C:\Users\CadriacLord\Documents\Codex\2026-07-31\new-chat',
    [string]$ProjectRoot = 'P:\AI\Codex\game_localization\YoruGaKuru_Remastered_KO_Project'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedSourceRoot = [IO.Path]::GetFullPath('C:\Users\CadriacLord\Documents\Codex\2026-07-31\new-chat').TrimEnd('\')
$expectedProjectRoot = [IO.Path]::GetFullPath('P:\AI\Codex\game_localization\YoruGaKuru_Remastered_KO_Project').TrimEnd('\')
$originalGameRoot = [IO.Path]::GetFullPath('P:\GAME\Compacted Files\[Ryuugames] RY-r119676\夜が来る！-Square of the MOON- Remastered').TrimEnd('\')
$packageRelative = 'staging\release\YoruGaKuru_Remastered_KO_KOFC04'
$releaseRelative = 'release\YoruGaKuru_Remastered_KO_KOFC04'

function Resolve-ExactRoot {
    param([string]$Actual, [string]$Expected, [string]$Label)
    $resolved = [IO.Path]::GetFullPath($Actual).TrimEnd('\')
    if (-not $resolved.Equals($Expected, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing unexpected $Label root: $resolved"
    }
    return $resolved
}

function Get-SafeChild {
    param([string]$Root, [string]$Relative, [string]$Label)
    if ([IO.Path]::IsPathRooted($Relative)) { throw "$Label must be relative: $Relative" }
    $full = [IO.Path]::GetFullPath((Join-Path $Root $Relative))
    if (-not $full.StartsWith($Root.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes its root: $Relative"
    }
    return $full
}

function Assert-NoReparseAncestor {
    param([string]$Root, [string]$Path, [string]$Label)
    $rootPrefix = $Root.TrimEnd('\') + '\'
    $current = Split-Path -Parent $Path
    while ($current -and ($current.Equals($Root, [StringComparison]::OrdinalIgnoreCase) -or $current.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase))) {
        if (Test-Path -LiteralPath $current -PathType Container) {
            $item = Get-Item -LiteralPath $current -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "$Label traverses a reparse point: $current"
            }
        }
        if ($current.Equals($Root, [StringComparison]::OrdinalIgnoreCase)) { break }
        $current = Split-Path -Parent $current
    }
}

function Read-JsonFile {
    param([string]$Path)
    try { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json }
    catch { throw "Invalid JSON: $Path`n$($_.Exception.Message)" }
}

function Copy-VerifiedFile {
    param([string]$Source, [string]$Destination, [string]$ExpectedHash, [long]$ExpectedSize)
    Assert-NoReparseAncestor -Root $script:resolvedProjectRoot -Path $Destination -Label 'destination'
    $parent = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Assert-NoReparseAncestor -Root $script:resolvedProjectRoot -Path $Destination -Label 'created destination'

    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        $existingHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()
        $existingSize = (Get-Item -LiteralPath $Destination).Length
        if ($existingHash -eq $ExpectedHash -and $existingSize -eq $ExpectedSize) { return 'unchanged' }
    } elseif (Test-Path -LiteralPath $Destination) {
        throw "Destination exists but is not a file: $Destination"
    }

    $temporary = "$Destination.$PID.$([Guid]::NewGuid().ToString('N')).tmp"
    Copy-Item -LiteralPath $Source -Destination $temporary
    $temporaryHash = (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash.ToLowerInvariant()
    $temporarySize = (Get-Item -LiteralPath $temporary).Length
    if ($temporaryHash -ne $ExpectedHash -or $temporarySize -ne $ExpectedSize) {
        Remove-Item -LiteralPath $temporary -Force
        throw "Temporary copy verification failed: $Destination"
    }
    if (Test-Path -LiteralPath $Destination -PathType Leaf) { Remove-Item -LiteralPath $Destination -Force }
    Move-Item -LiteralPath $temporary -Destination $Destination
    $finalHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($finalHash -ne $ExpectedHash -or (Get-Item -LiteralPath $Destination).Length -ne $ExpectedSize) {
        throw "Post-copy verification failed: $Destination"
    }
    return 'copied'
}

$resolvedSourceRoot = Resolve-ExactRoot -Actual $SourceRoot -Expected $expectedSourceRoot -Label 'source'
$script:resolvedProjectRoot = Resolve-ExactRoot -Actual $ProjectRoot -Expected $expectedProjectRoot -Label 'project'
if (-not (Test-Path -LiteralPath $resolvedSourceRoot -PathType Container)) { throw "Source root not found: $resolvedSourceRoot" }
if (-not (Test-Path -LiteralPath $script:resolvedProjectRoot -PathType Container)) { throw "Project root not found: $script:resolvedProjectRoot" }
if ($script:resolvedProjectRoot.Equals($originalGameRoot, [StringComparison]::OrdinalIgnoreCase) -or $script:resolvedProjectRoot.StartsWith($originalGameRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Project root resolves inside the original game; refusing writes.'
}
if (((Get-Item -LiteralPath $script:resolvedProjectRoot -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Project root is a reparse point; refusing ambiguous writes.'
}

$projectJsonPath = Get-SafeChild -Root $script:resolvedProjectRoot -Relative 'project.json' -Label 'project metadata'
$languageJsonPath = Get-SafeChild -Root $script:resolvedProjectRoot -Relative 'language_contract.json' -Label 'language contract'
$project = Read-JsonFile $projectJsonPath
$null = Read-JsonFile $languageJsonPath
if (-not ([string]$project.game_root).Equals($originalGameRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'project.json identifies an unexpected game root.' }
if ([bool]$project.live_install_approved -or [bool]$project.original_game_modified) { throw 'Project metadata claims a live install or source modification.' }

$staticQaPath = Get-SafeChild -Root $resolvedSourceRoot -Relative 'staging\manifests\final_static_qa_KOFC04.json' -Label 'static QA'
$completionPath = Get-SafeChild -Root $resolvedSourceRoot -Relative 'staging\manifests\completion_audit_KOFC04.json' -Label 'completion audit'
$finalLanguagePath = Get-SafeChild -Root $resolvedSourceRoot -Relative 'staging\manifests\language_contract_final_KOFC04.json' -Label 'final language contract'
$fixturePath = Get-SafeChild -Root $resolvedSourceRoot -Relative 'staging\manifests\release_fixture_tests.json' -Label 'fixture tests'
$packageRoot = Get-SafeChild -Root $resolvedSourceRoot -Relative $packageRelative -Label 'release package'
$installManifestPath = Join-Path $packageRoot 'manifest\install_manifest.json'

$staticQa = Read-JsonFile $staticQaPath
$completion = Read-JsonFile $completionPath
$fixture = Read-JsonFile $fixturePath
$finalLanguage = Read-JsonFile $finalLanguagePath
$installManifest = Read-JsonFile $installManifestPath
if ([string]$staticQa.status -ne 'PASS' -or [int]$staticQa.original_game.hash_or_size_mismatch_count -ne 0 -or [bool]$staticQa.original_game.modified) { throw 'Final static QA is not safe to sync.' }
$allowedCompletionStatuses = @('STATIC_PASS_RUNTIME_CONFIRMATION_PENDING', 'PASS')
if ($allowedCompletionStatuses -notcontains [string]$completion.status -or @($completion.static_failure_ids).Count -ne 0) { throw 'Completion audit is not in an allowed final-sync state.' }
if ([string]$fixture.status -ne 'PASS') { throw 'Release fixture tests did not pass.' }
if ([string]$installManifest.build_tag -ne 'KOFC04' -or [int]$installManifest.file_count -ne 63) { throw 'Unexpected install manifest.' }
if ([string]$finalLanguage.translation_provider -ne 'Codex internal model' -or [string]$finalLanguage.source_language -ne 'ja-JP') { throw 'Unexpected final language contract.' }

$copyPlan = [Collections.Generic.List[object]]::new()
$packageFiles = Get-ChildItem -LiteralPath $packageRoot -Recurse -File
foreach ($file in $packageFiles) {
    $relativeInPackage = $file.FullName.Substring($packageRoot.Length).TrimStart('\')
    $destinationRelative = Join-Path $releaseRelative $relativeInPackage
    $copyPlan.Add([pscustomobject]@{
        Source = $file.FullName
        Destination = Get-SafeChild -Root $script:resolvedProjectRoot -Relative $destinationRelative -Label 'release destination'
        DestinationRelative = $destinationRelative.Replace('\', '/')
        Size = $file.Length
        Sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    })
}

$evidenceCopies = @(
    @('staging\manifests\completion_audit_KOFC04.json', 'audit\final\completion_audit_KOFC04.json'),
    @('staging\manifests\runtime_smoke_KOFC04.json', 'audit\final\runtime_smoke_KOFC04.json'),
    @('staging\manifests\wallpaper_runtime_audit_KOFC04.json', 'audit\final\wallpaper_runtime_audit_KOFC04.json'),
    @('staging\manifests\language_contract_final_KOFC04.json', 'audit\final\language_contract_final_KOFC04.json'),
    @('staging\manifests\config_and_pact_runtime_audit.json', 'audit\final\config_and_pact_runtime_audit.json'),
    @('staging\manifests\final_static_qa_KOFC04.json', 'audit\final\final_static_qa_KOFC04.json'),
    @('staging\manifests\final_candidate_KOFC04.json', 'audit\final\final_candidate_KOFC04.json'),
    @('staging\manifests\release_fixture_tests.json', 'audit\final\release_fixture_tests.json'),
    @('staging\validation\latest_ui_fix_sheet_post.png', 'evidence\final\latest_ui_fix_sheet_post.png'),
    @('work\sync_final_release_to_project.ps1', 'adapter\scripts\sync_final_release_to_project.ps1')
)
foreach ($pair in $evidenceCopies) {
    $source = Get-SafeChild -Root $resolvedSourceRoot -Relative $pair[0] -Label 'evidence source'
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing evidence source: $source" }
    $item = Get-Item -LiteralPath $source
    $copyPlan.Add([pscustomobject]@{
        Source = $source
        Destination = Get-SafeChild -Root $script:resolvedProjectRoot -Relative $pair[1] -Label 'evidence destination'
        DestinationRelative = $pair[1].Replace('\', '/')
        Size = $item.Length
        Sha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    })
}

$releaseDestinationRoot = Get-SafeChild -Root $script:resolvedProjectRoot -Relative $releaseRelative -Label 'release destination root'
if (Test-Path -LiteralPath $releaseDestinationRoot -PathType Container) {
    $expected = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($item in $copyPlan | Where-Object { $_.Destination.StartsWith($releaseDestinationRoot + '\', [StringComparison]::OrdinalIgnoreCase) }) { $null = $expected.Add($item.Destination) }
    foreach ($existing in Get-ChildItem -LiteralPath $releaseDestinationRoot -Recurse -File) {
        if (-not $expected.Contains($existing.FullName)) { throw "Unknown file already exists in final release destination: $($existing.FullName)" }
    }
}

$planSummary = [pscustomobject]@{
    mode = if ($Commit) { 'commit' } else { 'dry-run' }
    source_root = $resolvedSourceRoot
    project_root = $script:resolvedProjectRoot
    original_game_root = $originalGameRoot
    original_game_modified = $false
    file_count = $copyPlan.Count
    total_bytes = ($copyPlan | Measure-Object -Property Size -Sum).Sum
    release_destination = $releaseDestinationRoot
}
if (-not $Commit) { $planSummary | ConvertTo-Json -Depth 4; exit 0 }

$resultRows = [Collections.Generic.List[object]]::new()
foreach ($item in $copyPlan) {
    $action = Copy-VerifiedFile -Source $item.Source -Destination $item.Destination -ExpectedHash $item.Sha256 -ExpectedSize $item.Size
    $resultRows.Add([pscustomobject]@{ path = $item.DestinationRelative; size = $item.Size; sha256 = $item.Sha256; action = $action })
}

$auditFinalRoot = Get-SafeChild -Root $script:resolvedProjectRoot -Relative 'audit\final' -Label 'final audit root'
New-Item -ItemType Directory -Force -Path $auditFinalRoot | Out-Null
$pilotProjectBackup = Join-Path $auditFinalRoot 'project_before_final_sync.json'
$pilotLanguageBackup = Join-Path $auditFinalRoot 'language_contract_before_final_sync.json'
if (-not (Test-Path -LiteralPath $pilotProjectBackup)) { Copy-Item -LiteralPath $projectJsonPath -Destination $pilotProjectBackup }
if (-not (Test-Path -LiteralPath $pilotLanguageBackup)) { Copy-Item -LiteralPath $languageJsonPath -Destination $pilotLanguageBackup }

$project.status = [string]$completion.status
$project.requested_delivery = 'reversible_staged_korean_release'
$project.patched_game_dir = $null
$project.launch_this_exe = $null
$project.delivery_basis = 'KOFC04 reversible release package synced; live original installation remains unapproved.'
$project.live_install_approved = $false
$project.original_game_modified = $false
$project.runtime_assets_generated = $true
$runtimeConfirmationPending = ([string]$completion.status -ne 'PASS')
$project.stage_gate = if ($runtimeConfirmationPending) {
    'Await final user runtime confirmation for the per-save in-game AddArea wallpaper.'
} else {
    'All static, package, and runtime confirmation gates passed.'
}
$project.last_updated_utc = [DateTime]::UtcNow.ToString('o')
$releaseMetadata = [pscustomobject]@{
    build_tag = 'KOFC04'
    package = ($releaseRelative.Replace('\', '/'))
    completion_audit = 'audit/final/completion_audit_KOFC04.json'
    install_manifest_sha256 = (Get-FileHash -LiteralPath $installManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    payload_file_count = 63
    runtime_confirmation_pending = $runtimeConfirmationPending
}
$project | Add-Member -NotePropertyName release -NotePropertyValue $releaseMetadata -Force

$projectTemporary = "$projectJsonPath.$PID.tmp"
$languageTemporary = "$languageJsonPath.$PID.tmp"
$project | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $projectTemporary -Encoding UTF8
$finalLanguage | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $languageTemporary -Encoding UTF8
if (Test-Path -LiteralPath $projectJsonPath) { Remove-Item -LiteralPath $projectJsonPath -Force }
Move-Item -LiteralPath $projectTemporary -Destination $projectJsonPath
if (Test-Path -LiteralPath $languageJsonPath) { Remove-Item -LiteralPath $languageJsonPath -Force }
Move-Item -LiteralPath $languageTemporary -Destination $languageJsonPath

$syncManifestPath = Join-Path $auditFinalRoot 'final_sync_KOFC04.json'
$syncDocument = [pscustomobject]@{
    schema = 'yorugakuru.final-project-sync.v1'
    synced_at = [DateTime]::UtcNow.ToString('o')
    status = 'PASS'
    build_tag = 'KOFC04'
    project_root = $script:resolvedProjectRoot
    original_game_root = $originalGameRoot
    original_game_modified = $false
    live_install_performed = $false
    completion_status = [string]$completion.status
    copied_file_count = @($resultRows | Where-Object { $_.action -eq 'copied' }).Count
    unchanged_file_count = @($resultRows | Where-Object { $_.action -eq 'unchanged' }).Count
    total_file_count = $resultRows.Count
    files = $resultRows
}
$syncDocument | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $syncManifestPath -Encoding UTF8

foreach ($item in $resultRows) {
    $path = Get-SafeChild -Root $script:resolvedProjectRoot -Relative ($item.path.Replace('/', '\')) -Label 'post-sync artifact'
    if ((Get-Item -LiteralPath $path).Length -ne [long]$item.size -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne [string]$item.sha256) {
        throw "Final post-sync verification failed: $($item.path)"
    }
}

[pscustomobject]@{
    status = 'PASS'
    project_root = $script:resolvedProjectRoot
    release_destination = $releaseDestinationRoot
    total_file_count = $resultRows.Count
    copied_file_count = $syncDocument.copied_file_count
    unchanged_file_count = $syncDocument.unchanged_file_count
    original_game_modified = $false
    live_install_performed = $false
    sync_manifest = $syncManifestPath
} | ConvertTo-Json -Depth 4
