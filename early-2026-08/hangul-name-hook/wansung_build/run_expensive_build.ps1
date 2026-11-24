param(
    [string]$ProjectDir = 'P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830_compat_v2',
    [string]$Python = 'P:\AI\forge\venv\Scripts\python.exe'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$env:PYTHONUTF8 = '1'

$ArtifactDir = $PSScriptRoot
$OutputDir = Join-Path $ArtifactDir 'build_output'
$Scripts = Join-Path $ProjectDir 'scripts'
$Inputs = Join-Path $ProjectDir 'inputs'

$PristineFnl = Join-Path $Inputs 'NightRemasterFont_original.fnl'
$CurrentFnl = Join-Path $ProjectDir 'outputs\NightRemasterFont.fnl'
$CurrentMap = Join-Path $ProjectDir 'build\results_v2_fnl_proxy_map_compat.json'
$Capacity = Join-Path $Inputs 'proxy_capacity_alice_cp932.json'
$Translation = Join-Path $ArtifactDir 'wansung_2350_reviewed_translation.json'
$ExpectedExtension = Join-Path $ArtifactDir 'wansung_expected_extension_assignments.json'
$OutputFnl = Join-Path $OutputDir 'NightRemasterFont_wansung2350.fnl'
$OutputMap = Join-Path $OutputDir 'fnl_proxy_map_wansung2350.json'
$OutputManifest = Join-Path $OutputDir 'fnl_wansung2350_build_manifest.json'
$OutputPreview = Join-Path $OutputDir 'fnl_wansung2350_preview.png'

function Assert-Sha256 {
    param([string]$Path, [string]$Expected)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing input: $Path" }
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
    if ($actual -ne $Expected.ToLowerInvariant()) {
        throw "SHA-256 mismatch: $Path`nexpected $Expected`nactual   $actual"
    }
}

Assert-Sha256 $PristineFnl '1942bfe1cd75690421aea94018c08071324a7ab7b34a2b32f1c1321ad1991591'
Assert-Sha256 $CurrentFnl '21bd7b3c6efab1ceff4a6ccb23037991c31d121381a708bafa7d9f43a549fa08'
Assert-Sha256 $CurrentMap '396c44773a4d7f064ad8558b62e351babbd4181cd777ed678e751e0287bdd12e'
Assert-Sha256 $Capacity 'b8efb147fb27f20e32252176e43c76145e49b931eefb977c4ce8e66866f89a21'

& $Python (Join-Path $ArtifactDir 'validate_wansung_fixture.py') `
    --current-map $CurrentMap `
    --proxy-capacity $Capacity `
    --translation $Translation `
    --expected-extension $ExpectedExtension
if ($LASTEXITCODE -ne 0) { throw "Fixture validation failed: $LASTEXITCODE" }

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# This is the intentionally expensive command. All P-drive inputs are read-only;
# every output path is under this local artifact directory.
& $Python (Join-Path $Scripts 'build_compatible_fnl_proxy_patch.py') `
    --builder-script (Join-Path $Scripts 'build_fnl_proxy_patch.py') `
    --pristine-fnl $PristineFnl `
    --compatibility-base-fnl $CurrentFnl `
    --base-proxy-map $CurrentMap `
    --translation-json $Translation `
    --proxy-capacity $Capacity `
    --output-fnl $OutputFnl `
    --map-output $OutputMap `
    --manifest-output $OutputManifest `
    --preview-output $OutputPreview `
    --expected-pristine-sha256 '1942bfe1cd75690421aea94018c08071324a7ab7b34a2b32f1c1321ad1991591' `
    --expected-base-sha256 '21bd7b3c6efab1ceff4a6ccb23037991c31d121381a708bafa7d9f43a549fa08'
if ($LASTEXITCODE -ne 0) { throw "FNL build failed: $LASTEXITCODE" }

& $Python (Join-Path $ArtifactDir 'validate_wansung_union.py') `
    --current-map $CurrentMap `
    --union-map $OutputMap `
    --expected-extension $ExpectedExtension `
    --builder-script (Join-Path $Scripts 'build_fnl_proxy_patch.py') `
    --base-fnl $CurrentFnl `
    --output-fnl $OutputFnl
if ($LASTEXITCODE -ne 0) { throw "Union validation failed: $LASTEXITCODE" }

Write-Host "PASS: Wansung FNL/map built and validated under $OutputDir"
