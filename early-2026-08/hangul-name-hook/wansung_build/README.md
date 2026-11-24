# KS X 1001/Wansung FNL proxy extension fixture

This directory prepares a deterministic extension of the current 1,524-entry
proxy ABI to every Hangul syllable encoded by CP949 bytes `B0A1-C8FE`.

No preparation or validation command writes to the P-drive project. The
expensive FNL build is deliberately not executed during preparation. If
`run_expensive_build.ps1` is run later, it reads P-drive inputs but writes every
output below `build_output/` in this directory.

## Pinned result

- KS X 1001/Wansung syllables: **2,350**
- Already present in current map: **1,506**
- Missing/new assignments: **844**
- Current mapping count: **1,524**
- Expected union mapping count: **2,368**
- Eligible unused proxy candidates before extension: **1,357**
- Remaining eligible headroom: **513**
- Expected forced proxy targets: **0**

The current map contains 18 non-Wansung targets, hence the union is
`2,350 + 18 = 2,368` rather than 2,350.

## Prepared files

- `wansung_2350_reviewed_translation.json`: one reviewed synthetic target that
  enumerates the 2,350 syllables in CP949 byte order.
- `wansung_expected_extension_assignments.json`: the exact 844 deterministic
  assignments expected from `choose_extension_rows()`.
- `wansung_extension_plan.json`: input hashes, sequence hashes, counts and
  capacity calculation.
- `generate_wansung_fixture.py`: deterministic fixture generator.
- `validate_wansung_fixture.py`: independent pre-build set/capacity validator.
- `validate_wansung_union.py`: post-build map ABI/Wansung/FNL preservation
  validator.
- `run_expensive_build.ps1`: hash-bound build command; not run during prep.

## Recreate and validate the small fixture

```powershell
$Python = 'C:\Users\CadriacLord\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$Project = 'P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830_compat_v2'
$Here = 'C:\Users\CadriacLord\OneDrive\문서\ChatGPT\밤이 온다 한국어화\hangul_ime_wansung_agent'

& $Python "$Here\generate_wansung_fixture.py" `
  --current-map "$Project\build\results_v2_fnl_proxy_map_compat.json" `
  --proxy-capacity "$Project\inputs\proxy_capacity_alice_cp932.json" `
  --translation-output "$Here\wansung_2350_reviewed_translation.json" `
  --expected-extension-output "$Here\wansung_expected_extension_assignments.json" `
  --plan-output "$Here\wansung_extension_plan.json"

& $Python "$Here\validate_wansung_fixture.py" `
  --current-map "$Project\build\results_v2_fnl_proxy_map_compat.json" `
  --proxy-capacity "$Project\inputs\proxy_capacity_alice_cp932.json" `
  --translation "$Here\wansung_2350_reviewed_translation.json" `
  --expected-extension "$Here\wansung_expected_extension_assignments.json"
```

## Exact expensive build

The wrapper performs all pinned hash checks, calls the existing compatible FNL
builder with the **current 1,524 map and current 1,524-patched FNL as its base**,
then runs both map and retained-glyph validators:

```powershell
& 'C:\Users\CadriacLord\OneDrive\문서\ChatGPT\밤이 온다 한국어화\hangul_ime_wansung_agent\run_expensive_build.ps1'
```

The core command inputs are:

- builder: `P:\AI\Codex\projects\YoruGaKuru_KR_rebuild_20260830_compat_v2\scripts\build_compatible_fnl_proxy_patch.py`
- builder module: `...\scripts\build_fnl_proxy_patch.py`
- pristine FNL: `...\inputs\NightRemasterFont_original.fnl`, SHA-256
  `1942bfe1cd75690421aea94018c08071324a7ab7b34a2b32f1c1321ad1991591`
- compatibility base FNL: `...\outputs\NightRemasterFont.fnl`, SHA-256
  `21bd7b3c6efab1ceff4a6ccb23037991c31d121381a708bafa7d9f43a549fa08`
- base proxy map: `...\build\results_v2_fnl_proxy_map_compat.json`, SHA-256
  `396c44773a4d7f064ad8558b62e351babbd4181cd777ed678e751e0287bdd12e`
- capacity: `...\inputs\proxy_capacity_alice_cp932.json`, SHA-256
  `b8efb147fb27f20e32252176e43c76145e49b931eefb977c4ce8e66866f89a21`
- translation input: local `wansung_2350_reviewed_translation.json`

Using the current patched FNL/map as the compatibility base is essential. Using
the older 1,404-entry KOFC06 base would re-create the earlier extension instead
of proving that the current 1,524 ABI/pixels are retained unchanged.
