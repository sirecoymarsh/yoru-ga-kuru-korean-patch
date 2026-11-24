@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64
if errorlevel 1 exit /b 1
cd /d "%~dp0"
cl /nologo /std:c++17 /utf-8 /W4 /WX /O2 /GS- /GR- /MT /LD /DUNICODE /D_UNICODE /DIME_HOOK_DIAGNOSTICS=0 winmm_proxy.cpp /Fo"P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\claude_fixes_20260928\hook_build\winmm.obj" /link /OUT:"P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\claude_fixes_20260928\hook_build\winmm.dll" /DEF:winmm_proxy.def user32.lib imm32.lib kernel32.lib shell32.lib ole32.lib uuid.lib
if errorlevel 1 exit /b 2
cl /nologo /std:c++17 /utf-8 /W4 /WX /O2 /EHsc /MT /DUNICODE /D_UNICODE unit_harness.cpp /Fo"P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\claude_fixes_20260928\hook_build\unit.obj" /Fe"P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\claude_fixes_20260928\hook_build\unit_harness.exe" user32.lib kernel32.lib
if errorlevel 1 exit /b 3
cl /nologo /std:c++17 /utf-8 /W4 /WX /O2 /EHsc /MT /DUNICODE /D_UNICODE maintenance_harness_20260928.cpp /Fo"P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\claude_fixes_20260928\hook_build\maintenance.obj" /Fe"P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\claude_fixes_20260928\hook_build\maintenance_harness.exe" user32.lib kernel32.lib
if errorlevel 1 exit /b 4
dumpbin /exports "P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\claude_fixes_20260928\hook_build\winmm.dll" > "P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\claude_fixes_20260928\hook_build\exports.txt"
dumpbin /imports "P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\claude_fixes_20260928\hook_build\winmm.dll" > "P:\AI\Codex\projects\YoruGaKuru_KR_asset_opening_20260908\staging\claude_fixes_20260928\hook_build\imports.txt"
