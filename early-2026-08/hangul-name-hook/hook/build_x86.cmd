@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64
if errorlevel 1 exit /b %errorlevel%
cd /d "%~dp0"
if not defined IME_HOOK_BUILD_DIR exit /b 30
if not defined IME_HOOK_DIAGNOSTICS exit /b 32
if not exist "%IME_HOOK_BUILD_DIR%" mkdir "%IME_HOOK_BUILD_DIR%"
cl.exe /nologo /std:c++17 /W4 /WX /O2 /GS- /GR- /MT /LD /DUNICODE /D_UNICODE /DIME_HOOK_DIAGNOSTICS=%IME_HOOK_DIAGNOSTICS% winmm_proxy.cpp /Fo"%IME_HOOK_BUILD_DIR%\winmm_proxy.obj" /Fd"%IME_HOOK_BUILD_DIR%\winmm_proxy.pdb" /link /OUT:"%IME_HOOK_BUILD_DIR%\winmm.dll" /PDB:"%IME_HOOK_BUILD_DIR%\winmm_proxy.pdb" /IMPLIB:"%IME_HOOK_BUILD_DIR%\winmm_proxy.lib" /DEF:winmm_proxy.def user32.lib imm32.lib kernel32.lib
if errorlevel 1 exit /b %errorlevel%
cl.exe /nologo /std:c++17 /W4 /WX /O2 /EHsc /MT /DUNICODE /D_UNICODE unit_harness.cpp /Fo"%IME_HOOK_BUILD_DIR%\unit_harness.obj" /Fd"%IME_HOOK_BUILD_DIR%\unit_harness.pdb" /link /OUT:"%IME_HOOK_BUILD_DIR%\unit_harness.exe" /PDB:"%IME_HOOK_BUILD_DIR%\unit_harness.pdb" user32.lib kernel32.lib
if errorlevel 1 exit /b %errorlevel%
if not defined HANGUL_EXPECTED_ROWS exit /b 31
"%IME_HOOK_BUILD_DIR%\unit_harness.exe" "%IME_HOOK_BUILD_DIR%\winmm.dll" "%HANGUL_EXPECTED_ROWS%"
if errorlevel 1 exit /b %errorlevel%
dumpbin.exe /headers /exports "%IME_HOOK_BUILD_DIR%\winmm.dll"
if errorlevel 1 exit /b %errorlevel%
dumpbin.exe /imports "%IME_HOOK_BUILD_DIR%\winmm.dll"
exit /b %errorlevel%
