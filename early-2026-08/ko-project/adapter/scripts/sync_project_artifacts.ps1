[CmdletBinding()]
param(
    [string]$WorkRoot = 'C:\Users\CadriacLord\Documents\Codex\2026-07-31\new-chat\work',
    [string]$ProjectRoot = 'P:\AI\Codex\game_localization\YoruGaKuru_Remastered_KO_Project'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$expectedWorkRoot = [System.IO.Path]::GetFullPath(
    'C:\Users\CadriacLord\Documents\Codex\2026-07-31\new-chat\work'
).TrimEnd('\')
$expectedProjectRoot = [System.IO.Path]::GetFullPath(
    'P:\AI\Codex\game_localization\YoruGaKuru_Remastered_KO_Project'
).TrimEnd('\')
$forbiddenGameRoot = [System.IO.Path]::GetFullPath(
    'P:\GAME\Compacted Files\[Ryuugames] RY-r119676\夜が来る！-Square of the MOON- Remastered'
).TrimEnd('\')

function Assert-ExactRoot {
    param(
        [Parameter(Mandatory = $true)][string]$Actual,
        [Parameter(Mandatory = $true)][string]$Expected,
        [Parameter(Mandatory = $true)][string]$Label
    )
    try {
        $normalized = [System.IO.Path]::GetFullPath($Actual).TrimEnd('\')
    }
    catch {
        throw "Invalid $Label root path <$Actual>: $($_.Exception.Message)"
    }
    if (-not $normalized.Equals($Expected, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing unexpected $Label root: $normalized"
    }
    return $normalized
}

function Get-SafeChildPath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [Parameter(Mandatory = $true)][string]$Label
    )
    if ([System.IO.Path]::IsPathRooted($RelativePath)) {
        throw "$Label must be relative: $RelativePath"
    }
    try {
        $joinedPath = Join-Path $Root $RelativePath
        $fullPath = [System.IO.Path]::GetFullPath($joinedPath)
    }
    catch {
        throw "Invalid $Label path <$RelativePath> under <$Root>: $($_.Exception.Message)"
    }
    $prefix = $Root.TrimEnd('\') + '\'
    if (-not $fullPath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes its root: $RelativePath"
    }
    return $fullPath
}

function Assert-NoReparseAncestor {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$ChildPath,
        [Parameter(Mandatory = $true)][string]$Label
    )
    $rootPrefix = $Root.TrimEnd('\') + '\'
    $current = Split-Path -Parent $ChildPath
    while ($current -and
        ($current.Equals($Root, [System.StringComparison]::OrdinalIgnoreCase) -or
         $current.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase))) {
        if (Test-Path -LiteralPath $current -PathType Container) {
            $item = Get-Item -LiteralPath $current -Force
            if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "$Label traverses a reparse point: $current"
            }
        }
        if ($current.Equals($Root, [System.StringComparison]::OrdinalIgnoreCase)) {
            break
        }
        $current = Split-Path -Parent $current
    }
}

$resolvedWorkRoot = Assert-ExactRoot -Actual $WorkRoot -Expected $expectedWorkRoot -Label 'work'
$resolvedProjectRoot = Assert-ExactRoot -Actual $ProjectRoot -Expected $expectedProjectRoot -Label 'project'

if ($resolvedProjectRoot.Equals($forbiddenGameRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
    $resolvedProjectRoot.StartsWith(
        $forbiddenGameRoot + '\',
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
    throw 'The project root resolves inside the original game. Refusing all writes.'
}
if (-not (Test-Path -LiteralPath $resolvedWorkRoot -PathType Container)) {
    throw "Work root was not found: $resolvedWorkRoot"
}
if (-not (Test-Path -LiteralPath $resolvedProjectRoot -PathType Container)) {
    throw "Project root was not found: $resolvedProjectRoot"
}
$projectRootItem = Get-Item -LiteralPath $resolvedProjectRoot -Force
if (($projectRootItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw "Project root is a reparse point; refusing ambiguous writes: $resolvedProjectRoot"
}

$projectMetadataPath = Get-SafeChildPath -Root $resolvedProjectRoot -RelativePath 'project.json' -Label 'project metadata'
$languageContractPath = Get-SafeChildPath -Root $resolvedProjectRoot -RelativePath 'language_contract.json' -Label 'language contract'
if (-not (Test-Path -LiteralPath $projectMetadataPath -PathType Leaf)) {
    throw "Existing project metadata was not found: $projectMetadataPath"
}
if (-not (Test-Path -LiteralPath $languageContractPath -PathType Leaf)) {
    throw "Existing language contract was not found: $languageContractPath"
}

$projectMetadata = Get-Content -LiteralPath $projectMetadataPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not ([string]$projectMetadata.game_root).Equals(
        $forbiddenGameRoot,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
    throw 'project.json does not identify the expected read-only original game root.'
}
if ([string]$projectMetadata.game_root_policy -ne 'read_only_until_explicit_install' -or
    [bool]$projectMetadata.live_install_approved) {
    throw 'project.json does not preserve the required read-only/no-live-install policy.'
}

$node = 'C:\Program Files\nodejs\node.exe'
if (-not (Test-Path -LiteralPath $node -PathType Leaf)) {
    throw "Node.js executable was not found: $node"
}

$directories = @(
    'adapter\scripts',
    'audit',
    'catalog',
    'evidence\font',
    'glossary',
    'packets',
    'packets\drafts',
    'packets\reviews',
    'staging\pilot\proxy'
)

$copies = @(
    @('glossary.tsv', 'glossary\glossary.tsv'),
    @('style_guide.md', 'glossary\style_guide.md'),

    @('pilot_e00001_part01.json', 'packets\pilot_e00001_part01.json'),
    @('pilot_e00001_part02.json', 'packets\pilot_e00001_part02.json'),
    @('pilot_e00001_part03.json', 'packets\pilot_e00001_part03.json'),
    @('pilot_e00001_part04.json', 'packets\pilot_e00001_part04.json'),
    @('result_pilot_e00001_part01.json', 'packets\drafts\result_pilot_e00001_part01.json'),
    @('result_pilot_e00001_part02.json', 'packets\drafts\result_pilot_e00001_part02.json'),
    @('result_pilot_e00001_part03.json', 'packets\drafts\result_pilot_e00001_part03.json'),
    @('result_pilot_e00001_part04.json', 'packets\drafts\result_pilot_e00001_part04.json'),
    @('crossreview_pilot_e00001_part01.json', 'packets\reviews\crossreview_pilot_e00001_part01.json'),
    @('crossreview_pilot_e00001_part02.json', 'packets\reviews\crossreview_pilot_e00001_part02.json'),
    @('crossreview_pilot_e00001_part03.json', 'packets\reviews\crossreview_pilot_e00001_part03.json'),
    @('crossreview_pilot_e00001_part04.json', 'packets\reviews\crossreview_pilot_e00001_part04.json'),

    @('pilot_translation_map.json', 'catalog\pilot_translation_map.json'),
    @('ain_message_packet_plan.json', 'catalog\ain_message_packet_plan.json'),
    @('ain_string_triage_plan.json', 'catalog\ain_string_triage_plan.json'),
    @('pe_surface_catalog_reviewed.json', 'catalog\pe_surface_catalog_reviewed.json'),

    @('language_qa_pilot.json', 'audit\language_qa_pilot.json'),
    @('translation_map_validator_pilot.json', 'audit\translation_map_validator_pilot.json'),
    @('ain_proxy_validation_pilot.json', 'audit\ain_proxy_validation_pilot.json'),
    @('fnl_proxy_map_validation_pilot.json', 'audit\fnl_proxy_map_validation_pilot.json'),
    @('pilot_bundle_validation.json', 'audit\pilot_bundle_validation.json'),
    @('pe_surface_catalog_validation.json', 'audit\pe_surface_catalog_validation.json'),
    @('original_integrity_recheck.json', 'audit\original_integrity_recheck.json'),
    @('ain_roundtrip_audit.json', 'audit\ain_roundtrip_audit.json'),
    @('pact_archive_roundtrip_audit.json', 'audit\pact_archive_roundtrip_audit.json'),
    @('ex_roundtrip_audit.json', 'audit\ex_roundtrip_audit.json'),
    @('surface_inventory_populated.json', 'audit\surface_inventory.json'),
    @('audit.json', 'audit\audit.json'),
    @('discovery_report_ko.md', 'audit\discovery_report_ko.md'),

    @('pilot_proxy_map_reviewed.json', 'staging\pilot\proxy\pilot_proxy_map.json'),
    @('pilot_proxy_preview_reviewed.png', 'evidence\font\pilot_proxy_preview.png'),

    @('analyze_discovery.py', 'adapter\scripts\analyze_discovery.py'),
    @('analyze_fnl.py', 'adapter\scripts\analyze_fnl.py'),
    @('analyze_proxy_capacity.py', 'adapter\scripts\analyze_proxy_capacity.py'),
    @('build_ain_packet.mjs', 'adapter\scripts\build_ain_packet.mjs'),
    @('build_ain_proxy_text.py', 'adapter\scripts\build_ain_proxy_text.py'),
    @('build_fnl_proxy_patch.py', 'adapter\scripts\build_fnl_proxy_patch.py'),
    @('extract_fnl_samples.py', 'adapter\scripts\extract_fnl_samples.py'),
    @('freeze_translation_map.py', 'adapter\scripts\freeze_translation_map.py'),
    @('plan_ain_translation.py', 'adapter\scripts\plan_ain_translation.py'),
    @('pe_resource_audit.ps1', 'adapter\scripts\pe_resource_audit.ps1'),
    @('verify_original_inventory.mjs', 'adapter\scripts\verify_original_inventory.mjs'),
    @('update_project_metadata.mjs', 'adapter\scripts\update_project_metadata.mjs'),
    @('generate_artifact_index.mjs', 'adapter\scripts\generate_artifact_index.mjs'),
    @('sync_project_artifacts.ps1', 'adapter\scripts\sync_project_artifacts.ps1')
)

$requiredExistingProjectArtifacts = @(
    'project.json',
    'language_contract.json',
    'semantic_allowlist.json',
    'adapter\contract.json',
    'audit\original_inventory.json',
    'audit\ain_text_summary.json',
    'audit\ex_string_summary.json',
    'audit\archive_list_summary.json',
    'audit\fnl_audit.json',
    'audit\proxy_capacity.json',
    'audit\fnl_dump_scope.json',
    'audit\archive_lists\NightRemasterCG.afa.list.txt',
    'audit\archive_lists\NightRemasterPact.afa.list.txt',
    'audit\archive_lists\NightRemasterSound.afa.list.txt',
    'audit\archive_lists\NightRemasterVoice.afa.list.txt'
)

$allowedDestinationPrefixes = @(
    'adapter\scripts\',
    'audit\',
    'catalog\',
    'evidence\font\',
    'glossary\',
    'packets\',
    'staging\pilot\proxy\'
)
$forbiddenRuntimeExtensions = @(
    '.afa', '.ain', '.apeg', '.dcf', '.dll', '.ex', '.exe', '.fnl',
    '.ogg', '.pactex', '.pcf', '.qnt'
)

# Complete the entire read-only preflight before creating a directory or copying a file.
foreach ($relativeDirectory in $directories) {
    $directoryPath = Get-SafeChildPath -Root $resolvedProjectRoot -RelativePath $relativeDirectory -Label 'destination directory'
    Assert-NoReparseAncestor -Root $resolvedProjectRoot -ChildPath $directoryPath -Label 'destination directory'
}
foreach ($relativePath in $requiredExistingProjectArtifacts) {
    $requiredPath = Get-SafeChildPath -Root $resolvedProjectRoot -RelativePath $relativePath -Label 'required project artifact'
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Required existing project artifact is missing: $requiredPath"
    }
}

$destinationSet = [System.Collections.Generic.HashSet[string]]::new(
    [System.StringComparer]::OrdinalIgnoreCase
)
$copyPlan = @()
foreach ($copy in $copies) {
    if ($copy.Count -ne 2) {
        throw 'Invalid copy manifest entry.'
    }
    $sourceRelative = [string]$copy[0]
    $destinationRelative = [string]$copy[1]
    $source = Get-SafeChildPath -Root $resolvedWorkRoot -RelativePath $sourceRelative -Label 'source artifact'
    $destination = Get-SafeChildPath -Root $resolvedProjectRoot -RelativePath $destinationRelative -Label 'destination artifact'
    Assert-NoReparseAncestor -Root $resolvedProjectRoot -ChildPath $destination -Label 'destination artifact'

    $allowed = $false
    foreach ($prefix in $allowedDestinationPrefixes) {
        if ($destinationRelative.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            $allowed = $true
            break
        }
    }
    if (-not $allowed) {
        throw "Destination is outside the non-runtime artifact allowlist: $destinationRelative"
    }
    if ($forbiddenRuntimeExtensions -contains [System.IO.Path]::GetExtension($destinationRelative).ToLowerInvariant()) {
        throw "Runtime asset extension is forbidden in this sync: $destinationRelative"
    }
    if (-not $destinationSet.Add($destination)) {
        throw "Duplicate destination in copy manifest: $destinationRelative"
    }
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Required source artifact is missing: $source"
    }

    if ([System.IO.Path]::GetExtension($source).Equals('.json', [System.StringComparison]::OrdinalIgnoreCase)) {
        try {
            $null = Get-Content -LiteralPath $source -Raw -Encoding UTF8 | ConvertFrom-Json
        }
        catch {
            throw "Required JSON artifact is invalid: $source`n$($_.Exception.Message)"
        }
    }

    $sourceItem = Get-Item -LiteralPath $source
    $copyPlan += [pscustomobject]@{
        source = $source
        destination = $destination
        destination_relative = $destinationRelative
        size = $sourceItem.Length
        sha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    }
}

function Read-WorkJson {
    param([Parameter(Mandatory = $true)][string]$FileName)
    $jsonPath = Get-SafeChildPath -Root $resolvedWorkRoot -RelativePath $FileName -Label 'validation artifact'
    return Get-Content -LiteralPath $jsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
}

# Cross-check the frozen non-runtime bundle and its recorded hashes before any P: write.
$pilotMapPath = Get-SafeChildPath -Root $resolvedWorkRoot -RelativePath 'pilot_translation_map.json' -Label 'pilot translation map'
$proxyMapPath = Get-SafeChildPath -Root $resolvedWorkRoot -RelativePath 'pilot_proxy_map_reviewed.json' -Label 'reviewed proxy map'
$previewPath = Get-SafeChildPath -Root $resolvedWorkRoot -RelativePath 'pilot_proxy_preview_reviewed.png' -Label 'reviewed proxy preview'
$peCatalogPath = Get-SafeChildPath -Root $resolvedWorkRoot -RelativePath 'pe_surface_catalog_reviewed.json' -Label 'reviewed PE surface catalog'
$pilotMapHash = (Get-FileHash -LiteralPath $pilotMapPath -Algorithm SHA256).Hash.ToLowerInvariant()
$proxyMapHash = (Get-FileHash -LiteralPath $proxyMapPath -Algorithm SHA256).Hash.ToLowerInvariant()
$previewHash = (Get-FileHash -LiteralPath $previewPath -Algorithm SHA256).Hash.ToLowerInvariant()
$peCatalogHash = (Get-FileHash -LiteralPath $peCatalogPath -Algorithm SHA256).Hash.ToLowerInvariant()

$translationValidator = Read-WorkJson -FileName 'translation_map_validator_pilot.json'
$ainProxyValidation = Read-WorkJson -FileName 'ain_proxy_validation_pilot.json'
$fnlProxyValidation = Read-WorkJson -FileName 'fnl_proxy_map_validation_pilot.json'
$integrityRecheck = Read-WorkJson -FileName 'original_integrity_recheck.json'
$pilotBundle = Read-WorkJson -FileName 'pilot_bundle_validation.json'
$peCatalogValidation = Read-WorkJson -FileName 'pe_surface_catalog_validation.json'

if ([string]$translationValidator.translation_map.sha256 -ne $pilotMapHash -or
    [int]$translationValidator.result.errors -ne 0 -or
    [int]$translationValidator.result.warnings -ne 0) {
    throw 'Translation-map validator does not match the frozen map or reports issues.'
}
if ([string]$ainProxyValidation.translation_map.sha256 -ne $pilotMapHash -or
    [string]$ainProxyValidation.proxy_map.sha256 -ne $proxyMapHash -or
    [bool]$ainProxyValidation.output_written -or
    [int]$ainProxyValidation.missing_stable_id_count -ne 0 -or
    [int]$ainProxyValidation.source_mismatch_count -ne 0 -or
    [int]$ainProxyValidation.proxy_coverage_error_count -ne 0 -or
    [int]$ainProxyValidation.cp932_encoding_error_count -ne 0) {
    throw 'AIN validate-only report is inconsistent or claims a runtime output.'
}
if ([string]$fnlProxyValidation.proxy_map.sha256 -ne $proxyMapHash -or
    [string]$fnlProxyValidation.preview.sha256 -ne $previewHash -or
    [bool]$fnlProxyValidation.output_fnl_created -or
    [bool]$fnlProxyValidation.original_fnl_modified -or
    [bool]$fnlProxyValidation.structural_patch_verification_performed) {
    throw 'FNL map-only report is inconsistent or claims a runtime patch.'
}

$originalInventoryPath = Get-SafeChildPath -Root $resolvedProjectRoot -RelativePath 'audit\original_inventory.json' -Label 'original inventory'
$originalInventoryHash = (Get-FileHash -LiteralPath $originalInventoryPath -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not ([string]$integrityRecheck.game_root).Equals(
        $forbiddenGameRoot,
        [System.StringComparison]::OrdinalIgnoreCase
    ) -or
    [string]$integrityRecheck.inventory.sha256 -ne $originalInventoryHash -or
    [int]$integrityRecheck.missing_count -ne 0 -or
    [int]$integrityRecheck.unexpected_count -ne 0 -or
    [int]$integrityRecheck.hash_or_size_mismatch_count -ne 0 -or
    [bool]$integrityRecheck.original_game_modified) {
    throw 'Original-integrity recheck is missing, stale, or reports a source change.'
}
if ([string]$pilotBundle.translation.map_sha256 -ne $pilotMapHash -or
    [bool]$pilotBundle.language_contract.replacement_slot_approved -or
    [int]$pilotBundle.staged_runtime_asset_count -ne 0 -or
    [bool]$pilotBundle.runtime_assets_generated -or
    [bool]$pilotBundle.release_ready) {
    throw 'Pilot bundle is inconsistent with the required pre-approval non-runtime state.'
}
if ([string]$peCatalogValidation.catalog.sha256 -ne $peCatalogHash -or
    [int]$peCatalogValidation.duplicate_composite_identity_count -ne 0 -or
    [int]$peCatalogValidation.empty_target_count -ne 0 -or
    [int]$peCatalogValidation.protected_token_error_count -ne 0 -or
    [int]$peCatalogValidation.hardcoded_cp932_offset_match_error_count -ne 0 -or
    [int]$peCatalogValidation.baseline_hash_error_count -ne 0 -or
    [bool]$peCatalogValidation.runtime_files_modified) {
    throw 'PE surface catalog validation is inconsistent or reports unsafe changes.'
}

# Parse-check every copied Node program before any P: write.
foreach ($nodeItem in @($copyPlan | Where-Object {
            [System.IO.Path]::GetExtension($_.source).Equals(
                '.mjs',
                [System.StringComparison]::OrdinalIgnoreCase
            )
        })) {
    & $node --check $nodeItem.source
    if ($LASTEXITCODE -ne 0) {
        throw "Node syntax check failed for $($nodeItem.source) with exit code $LASTEXITCODE"
    }
}

# All checks above are read-only. Writes begin here and remain inside the exact project root.
foreach ($relativeDirectory in $directories) {
    $destinationDirectory = Get-SafeChildPath -Root $resolvedProjectRoot -RelativePath $relativeDirectory -Label 'destination directory'
    New-Item -ItemType Directory -Force -Path $destinationDirectory | Out-Null
    Assert-NoReparseAncestor -Root $resolvedProjectRoot -ChildPath (Join-Path $destinationDirectory '_probe_') -Label 'created destination directory'
}

$copied = [System.Collections.Generic.List[object]]::new()
foreach ($item in $copyPlan) {
    $temporaryDestination = "$($item.destination).$PID.$([System.Guid]::NewGuid().ToString('N')).tmp"
    Copy-Item -LiteralPath $item.source -Destination $temporaryDestination
    $temporaryHash = (Get-FileHash -LiteralPath $temporaryDestination -Algorithm SHA256).Hash
    $temporarySize = (Get-Item -LiteralPath $temporaryDestination).Length
    if ($temporaryHash -ne $item.sha256 -or $temporarySize -ne $item.size) {
        Remove-Item -LiteralPath $temporaryDestination -Force
        throw "Temporary copy verification failed: $($item.destination_relative)"
    }
    if (Test-Path -LiteralPath $item.destination) {
        if (-not (Test-Path -LiteralPath $item.destination -PathType Leaf)) {
            Remove-Item -LiteralPath $temporaryDestination -Force
            throw "Destination exists but is not a file: $($item.destination_relative)"
        }
        # Unlink first rather than overwriting through a possible hard link or file reparse point.
        Remove-Item -LiteralPath $item.destination -Force
    }
    Move-Item -LiteralPath $temporaryDestination -Destination $item.destination
    $sourceHashAfterCopy = (Get-FileHash -LiteralPath $item.source -Algorithm SHA256).Hash
    $destinationHash = (Get-FileHash -LiteralPath $item.destination -Algorithm SHA256).Hash
    if ($sourceHashAfterCopy -ne $item.sha256) {
        throw "Source changed during sync: $($item.source)"
    }
    if ($destinationHash -ne $item.sha256) {
        throw "Post-copy SHA-256 mismatch: $($item.destination_relative)"
    }
    if ((Get-Item -LiteralPath $item.destination).Length -ne $item.size) {
        throw "Post-copy size mismatch: $($item.destination_relative)"
    }
    $copied.Add([pscustomobject]@{
        path = $item.destination_relative.Replace('\', '/')
        size = $item.size
        sha256 = $destinationHash.ToLowerInvariant()
    })
}

$metadataUpdater = Get-SafeChildPath -Root $resolvedProjectRoot -RelativePath 'adapter\scripts\update_project_metadata.mjs' -Label 'metadata updater'
$indexGenerator = Get-SafeChildPath -Root $resolvedProjectRoot -RelativePath 'adapter\scripts\generate_artifact_index.mjs' -Label 'index generator'

# Metadata must be final before the index hashes project.json and language_contract.json.
& $node $metadataUpdater $resolvedProjectRoot --non-runtime-sync
if ($LASTEXITCODE -ne 0) {
    throw "Project metadata update failed with exit code $LASTEXITCODE"
}
& $node $indexGenerator $resolvedProjectRoot --non-runtime-sync
if ($LASTEXITCODE -ne 0) {
    throw "Artifact index generation failed with exit code $LASTEXITCODE"
}

$artifactIndexPath = Get-SafeChildPath -Root $resolvedProjectRoot -RelativePath 'audit\artifact_index.json' -Label 'artifact index'
$artifactIndex = Get-Content -LiteralPath $artifactIndexPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ([bool]$artifactIndex.original_game_modified -or [bool]$artifactIndex.runtime_assets_generated) {
    throw 'Generated artifact index contains an unsafe modification claim.'
}
if (@($artifactIndex.entries | Where-Object { $_.path -eq 'audit/artifact_index.json' }).Count -ne 0) {
    throw 'Artifact index must not hash itself.'
}
if (@($artifactIndex.entries | Where-Object { $_.path -eq 'adapter/scripts/sync_project_artifacts.ps1' }).Count -ne 1) {
    throw 'Artifact index omitted the sync script.'
}
foreach ($entry in $artifactIndex.entries) {
    $entryPath = Get-SafeChildPath -Root $resolvedProjectRoot -RelativePath ([string]$entry.path) -Label 'indexed artifact'
    $actualHash = (Get-FileHash -LiteralPath $entryPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $actualSize = (Get-Item -LiteralPath $entryPath).Length
    if ($actualHash -ne [string]$entry.sha256 -or $actualSize -ne [long]$entry.size) {
        throw "Artifact index verification failed: $($entry.path)"
    }
}

[pscustomobject]@{
    project_root = $resolvedProjectRoot
    copied_file_count = $copied.Count
    copied_total_bytes = ($copied | Measure-Object -Property size -Sum).Sum
    original_game_root = $forbiddenGameRoot
    original_game_modified = $false
    runtime_assets_generated = $false
    artifact_index = 'audit/artifact_index.json'
    artifact_index_sha256 = (Get-FileHash -LiteralPath $artifactIndexPath -Algorithm SHA256).Hash.ToLowerInvariant()
    files = $copied
} | ConvertTo-Json -Depth 6
