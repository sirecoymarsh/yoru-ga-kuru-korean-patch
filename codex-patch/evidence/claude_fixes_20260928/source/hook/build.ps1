param(
    [string]$ProxyMap = 'P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830_compat_v2\build\results_v2_fnl_proxy_map_compat.json',
    [string]$ExpectedProxyMapSha256 = '396c44773a4d7f064ad8558b62e351babbd4181cd777ed678e751e0287bdd12e',
    [ValidateSet('diagnostic', 'release')]
    [string]$BuildProfile = 'diagnostic',
    [string]$Python = 'C:\Users\CadriacLord\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Build = Join-Path $Root $(if ($BuildProfile -eq 'diagnostic') { 'build' } else { 'build_release' })
$Generated = Join-Path $Root 'hangul_proxy_table.generated.h'
$VsWhere = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'

New-Item -ItemType Directory -Force -Path $Build | Out-Null

$ActualProxyMapSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $ProxyMap).Hash.ToLowerInvariant()
$PinnedProxyMapSha256 = $ExpectedProxyMapSha256.Trim().ToLowerInvariant()
if ($ActualProxyMapSha256 -ne $PinnedProxyMapSha256) {
    throw "Proxy-map SHA256 mismatch: expected $PinnedProxyMapSha256, actual $ActualProxyMapSha256"
}

$GeneratorOutput = & $Python (Join-Path $Root 'generate_proxy_table.py') `
    --proxy-map $ProxyMap --output $Generated
if ($LASTEXITCODE -ne 0) { throw 'Proxy-table generation failed' }
$GeneratorOutput | Write-Output
$GeneratorResult = $GeneratorOutput | Select-Object -Last 1 | ConvertFrom-Json
if (-not $GeneratorResult.hangul_rows -or $GeneratorResult.hangul_rows -lt 1) {
    throw 'Generator did not report a positive Hangul row count'
}

$VsRoot = & $VsWhere -latest -products * `
    -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
    -property installationPath
if (-not $VsRoot) { throw 'Visual Studio C++ Build Tools not found' }
$VsDevCmd = Join-Path $VsRoot 'Common7\Tools\VsDevCmd.bat'

$Log = Join-Path $Build 'build.log'
$env:HANGUL_EXPECTED_ROWS = [string]$GeneratorResult.hangul_rows
$env:IME_HOOK_BUILD_DIR = $Build
$env:IME_HOOK_DIAGNOSTICS = if ($BuildProfile -eq 'diagnostic') { '1' } else { '0' }
& cmd.exe /d /c (Join-Path $Root 'build_x86.cmd') 2>&1 | Tee-Object -FilePath $Log
$BuildExitCode = $LASTEXITCODE
Remove-Item Env:HANGUL_EXPECTED_ROWS -ErrorAction SilentlyContinue
Remove-Item Env:IME_HOOK_BUILD_DIR -ErrorAction SilentlyContinue
Remove-Item Env:IME_HOOK_DIAGNOSTICS -ErrorAction SilentlyContinue
if ($BuildExitCode -ne 0) { throw "x86 build failed with exit code $BuildExitCode" }

function Get-ArtifactRecord([string]$Path) {
    $Item = Get-Item -LiteralPath $Path
    [ordered]@{
        path = $Item.FullName
        bytes = $Item.Length
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $Item.FullName).Hash.ToLowerInvariant()
    }
}

$Dll = Join-Path $Build 'winmm.dll'
$Harness = Join-Path $Build 'unit_harness.exe'
$ManifestPath = Join-Path $Build 'build_manifest.json'
$Manifest = [ordered]@{
    schema = 'nightremaster_hangul_ime_hook_build_v1'
    build_profile = $BuildProfile
    diagnostics_enabled = ($BuildProfile -eq 'diagnostic')
    expected_proxy_map_sha256 = $PinnedProxyMapSha256
    row_count = [int]$GeneratorResult.hangul_rows
    target_executable_fingerprint = [ordered]@{
        image_base = '0x00400000'
        pe_timestamp = '0x65F707F0'
        size_of_image = '0x00508000'
        wndproc_va = '0x007321F0'
        wndproc_prefix_hex = '83ec0853568b742418578b7c242481fe'
    }
    artifacts = [ordered]@{
        proxy_map = Get-ArtifactRecord $ProxyMap
        generated_header = Get-ArtifactRecord $Generated
        proxy_source = Get-ArtifactRecord (Join-Path $Root 'winmm_proxy.cpp')
        export_definition = Get-ArtifactRecord (Join-Path $Root 'winmm_proxy.def')
        harness_source = Get-ArtifactRecord (Join-Path $Root 'unit_harness.cpp')
        generator_source = Get-ArtifactRecord (Join-Path $Root 'generate_proxy_table.py')
        dll = Get-ArtifactRecord $Dll
        harness = Get-ArtifactRecord $Harness
        build_log = Get-ArtifactRecord $Log
    }
}
$Manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ManifestPath -Encoding utf8NoBOM

$Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Dll).Hash.ToLowerInvariant()
[pscustomobject]@{
    dll = $Dll
    sha256 = $Hash
    architecture = 'x86'
    profile = $BuildProfile
    row_count = [int]$GeneratorResult.hangul_rows
    manifest = $ManifestPath
    manifest_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $ManifestPath).Hash.ToLowerInvariant()
} | ConvertTo-Json
